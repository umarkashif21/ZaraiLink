"""
backend/search/tests/test_latency_benchmark.py

Phase 7: Latency benchmarks for the full hybrid + CE + GLiNER pipeline.

Measures wall-clock time for:
  - QueryInterpreter.parse()
  - QueryMatcher.match() (BM25 + FAISS hybrid)
  - Combined parse+match latency

Targets (with all pipeline features enabled — GLiNER adds ~180 ms per parse call):
  - parse():  < 300 ms (warm, with GLiNER NER enabled)
  - match():  < 300 ms (warm, BM25 + FAISS hybrid)
  - combined: < 600 ms (warm, p95, full pipeline)

Run (isolated — not in main CI suite):
    cd backend
    pytest search/tests/test_latency_benchmark.py -v -s -m benchmark
"""

import time
import pytest
import statistics


@pytest.fixture(scope='module')
def interpreter():
    import django, os
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'zarailink.settings')
    try:
        django.setup()
    except RuntimeError:
        pass
    from search.services.query_parser import QueryInterpreter
    return QueryInterpreter()


@pytest.fixture(scope='module')
def matcher():
    import django, os
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'zarailink.settings')
    try:
        django.setup()
    except RuntimeError:
        pass
    from search.services.nlp import QueryMatcher
    return QueryMatcher()


BENCHMARK_QUERIES = [
    "find dextrose suppliers",
    "top 5 palm oil exporters",
    "which countries import most sugar",
    "has Nestle purchased palm oil",
    "100 MT lactose monohydrate",
    "Q1 2024 glucose importers",
    "buy cotton from China",
    "find buyers for our wheat",
]

# Warm-up queries (run once before measuring)
WARMUP_QUERIES = [
    "dextrose suppliers",
    "sugar importers",
]


@pytest.mark.benchmark
class TestParseLatency:

    def test_parse_warm_latency_under_300ms(self, interpreter):
        """Warm parse (with GLiNER NER enabled) should complete in < 300 ms (p95)."""
        # warm-up — loads GLiNER model
        for q in WARMUP_QUERIES:
            interpreter.parse(q)

        times = []
        for q in BENCHMARK_QUERIES:
            t0 = time.perf_counter()
            interpreter.parse(q)
            times.append((time.perf_counter() - t0) * 1000)

        p95 = sorted(times)[int(len(times) * 0.95)]
        mean_ms = statistics.mean(times)
        print(f"\nParse latency — mean: {mean_ms:.1f} ms, p95: {p95:.1f} ms")
        print(f"  Per-query: {[f'{t:.1f}' for t in times]}")

        assert p95 < 300.0, f"Parse p95 latency {p95:.1f} ms exceeds 300 ms target"

    def test_parse_all_queries_under_350ms(self, interpreter):
        """Every single parse call should complete in < 350 ms (includes GLiNER)."""
        for q in BENCHMARK_QUERIES:
            t0 = time.perf_counter()
            interpreter.parse(q)
            ms = (time.perf_counter() - t0) * 1000
            assert ms < 350.0, f"parse({q!r}) took {ms:.1f} ms — exceeds 350 ms"


@pytest.mark.benchmark
class TestMatchLatency:

    def test_match_warm_latency_under_300ms(self, matcher, interpreter):
        """Warm match (BM25+FAISS hybrid) should complete in < 300 ms (p95)."""
        # warm-up — triggers FAISS index load
        for q in WARMUP_QUERIES:
            parsed = interpreter.parse(q)
            product = parsed.get('product') or q
            try:
                matcher.match(product)
            except Exception:
                pass

        times = []
        for q in BENCHMARK_QUERIES:
            parsed = interpreter.parse(q)
            product = parsed.get('product') or q
            t0 = time.perf_counter()
            try:
                matcher.match(product)
            except Exception:
                pass
            times.append((time.perf_counter() - t0) * 1000)

        p95 = sorted(times)[int(len(times) * 0.95)]
        mean_ms = statistics.mean(times)
        print(f"\nMatch latency — mean: {mean_ms:.1f} ms, p95: {p95:.1f} ms")
        print(f"  Per-query: {[f'{t:.1f}' for t in times]}")

        assert p95 < 300.0, f"Match p95 latency {p95:.1f} ms exceeds 300 ms target"


@pytest.mark.benchmark
class TestCombinedPipelineLatency:

    def test_combined_warm_latency_under_600ms(self, interpreter, matcher):
        """parse() + match() combined should be < 600 ms (p95) when warm (full pipeline)."""
        # warm-up
        for q in WARMUP_QUERIES:
            parsed = interpreter.parse(q)
            product = parsed.get('product') or q
            try:
                matcher.match(product)
            except Exception:
                pass

        times = []
        for q in BENCHMARK_QUERIES:
            t0 = time.perf_counter()
            parsed = interpreter.parse(q)
            product = parsed.get('product') or q
            try:
                matcher.match(product)
            except Exception:
                pass
            times.append((time.perf_counter() - t0) * 1000)

        p95 = sorted(times)[int(len(times) * 0.95)]
        mean_ms = statistics.mean(times)
        print(f"\nCombined latency — mean: {mean_ms:.1f} ms, p95: {p95:.1f} ms")
        print(f"  Per-query: {[f'{t:.1f}' for t in times]}")

        assert p95 < 600.0, f"Combined p95 latency {p95:.1f} ms exceeds 600 ms target"
