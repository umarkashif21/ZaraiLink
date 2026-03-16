"""
entity_resolution/tests/test_entity_resolution.py

Unit tests for all Phase 1 entity resolution modules:
  1-B: similarity.py          (normalize, jaro_winkler, damerau_levenshtein, soundex, token_jaccard)
  1-C: blocking.py            (soundex_blocking, first3_blocking, sorted_neighborhood, candidate_pairs)
  1-D: fellegi_sunter.py      (FellegiSunterEM fit/predict/score/summary)
  1-E: clustering.py          (UnionFind, transitive_closure, select_golden_record, cluster_entities)

Run:
    cd backend
    pytest entity_resolution/tests/test_entity_resolution.py -v
"""

import math
import pytest

# ---------------------------------------------------------------------------
# 1-B: similarity.py
# ---------------------------------------------------------------------------

class TestNormalizeCompanyName:
    from entity_resolution.similarity import normalize_company_name

    def test_lowercase(self):
        from entity_resolution.similarity import normalize_company_name
        assert normalize_company_name("ACME Corp") == "acme corporation"

    def test_expands_ltd(self):
        from entity_resolution.similarity import normalize_company_name
        result = normalize_company_name("Muller Ltd")
        assert "limited" in result

    def test_expands_pvt(self):
        from entity_resolution.similarity import normalize_company_name
        result = normalize_company_name("ABC Pvt Ltd")
        assert "private" in result
        assert "limited" in result

    def test_strips_punctuation(self):
        from entity_resolution.similarity import normalize_company_name
        result = normalize_company_name("A.B.C. (Pakistan) / Intl")
        assert "." not in result
        assert "(" not in result
        assert "/" not in result

    def test_unicode_to_ascii(self):
        from entity_resolution.similarity import normalize_company_name
        result = normalize_company_name("Müller GmbH")
        assert "muller" in result

    def test_ampersand_expansion(self):
        from entity_resolution.similarity import normalize_company_name
        result = normalize_company_name("Smith & Sons")
        assert "and" in result

    def test_empty_string(self):
        from entity_resolution.similarity import normalize_company_name
        assert normalize_company_name("") == ""

    def test_collapses_whitespace(self):
        from entity_resolution.similarity import normalize_company_name
        result = normalize_company_name("  Alpha   Beta  ")
        assert "  " not in result
        assert result == result.strip()


class TestJaroWinkler:
    def test_identical_strings(self):
        from entity_resolution.similarity import jaro_winkler
        assert jaro_winkler("Muller Phipps", "Muller Phipps") == 1.0

    def test_empty_strings(self):
        from entity_resolution.similarity import jaro_winkler
        assert jaro_winkler("", "") == 1.0  # both empty → identical
        assert jaro_winkler("abc", "") == 0.0
        assert jaro_winkler("", "abc") == 0.0

    def test_similar_names(self):
        from entity_resolution.similarity import jaro_winkler
        # "Muller" vs "Mueller" — should be high similarity
        score = jaro_winkler("muller phipps", "mueller phipps")
        assert score > 0.85, f"Expected > 0.85, got {score}"

    def test_dissimilar_names(self):
        from entity_resolution.similarity import jaro_winkler
        score = jaro_winkler("apple", "zebra")
        assert score < 0.7, f"Expected < 0.7, got {score}"

    def test_prefix_bonus(self):
        from entity_resolution.similarity import jaro_winkler
        # Common prefix boosts score
        score_with_prefix = jaro_winkler("abcdef", "abcxyz")
        score_without = jaro_winkler("abcdef", "xyzabc")
        assert score_with_prefix > score_without

    def test_returns_float_in_range(self):
        from entity_resolution.similarity import jaro_winkler
        for s1, s2 in [("foo", "bar"), ("hello", "world"), ("x", "x")]:
            score = jaro_winkler(s1, s2)
            assert 0.0 <= score <= 1.0, f"Out of range [{s1},{s2}]: {score}"


class TestDamerauLevenshtein:
    def test_identical(self):
        from entity_resolution.similarity import damerau_levenshtein_normalized
        assert damerau_levenshtein_normalized("abc", "abc") == 1.0

    def test_empty_strings(self):
        from entity_resolution.similarity import damerau_levenshtein_normalized
        assert damerau_levenshtein_normalized("", "") == 1.0
        assert damerau_levenshtein_normalized("abc", "") == 0.0
        assert damerau_levenshtein_normalized("", "abc") == 0.0

    def test_one_edit(self):
        from entity_resolution.similarity import damerau_levenshtein_normalized
        # "abc" → "abcd": 1 insertion, max_len=4 → similarity = 1 - 1/4 = 0.75
        score = damerau_levenshtein_normalized("abc", "abcd")
        assert abs(score - 0.75) < 0.01

    def test_transposition(self):
        from entity_resolution.similarity import damerau_levenshtein_normalized
        # "ab" → "ba": 1 transposition (Damerau allows this), max_len=2 → 0.5
        score = damerau_levenshtein_normalized("ab", "ba")
        assert score >= 0.5  # Should be better than full substitution

    def test_completely_different(self):
        from entity_resolution.similarity import damerau_levenshtein_normalized
        score = damerau_levenshtein_normalized("abc", "xyz")
        assert score < 0.5

    def test_returns_float_in_range(self):
        from entity_resolution.similarity import damerau_levenshtein_normalized
        for s1, s2 in [("foo", "bar"), ("hello", "hell"), ("x", "y")]:
            score = damerau_levenshtein_normalized(s1, s2)
            assert 0.0 <= score <= 1.0


class TestSoundex:
    def test_muller(self):
        from entity_resolution.similarity import soundex
        # "Muller" and "Mueller" should share same Soundex code
        code_a = soundex("Muller")
        code_b = soundex("Mueller")
        assert code_a == code_b, f"Expected same code, got {code_a} vs {code_b}"

    def test_length_always_4(self):
        from entity_resolution.similarity import soundex
        for name in ["A", "AB", "ABCDEFG", "Smith", "Johnson", "XYZ"]:
            code = soundex(name)
            assert len(code) == 4, f"Length != 4 for {name!r}: {code!r}"

    def test_first_char_preserved(self):
        from entity_resolution.similarity import soundex
        assert soundex("Smith")[0] == "S"
        assert soundex("Robert")[0] == "R"

    def test_empty_string(self):
        from entity_resolution.similarity import soundex
        assert soundex("") == "0000"

    def test_known_codes(self):
        from entity_resolution.similarity import soundex
        # Standard American Soundex values
        assert soundex("Robert") == "R163"
        assert soundex("Rupert") == "R163"  # Same as Robert

    def test_digits_only_zero_to_six(self):
        from entity_resolution.similarity import soundex
        code = soundex("Test")
        assert code[0].isalpha()
        for ch in code[1:]:
            assert ch.isdigit()


class TestTokenJaccard:
    def test_identical(self):
        from entity_resolution.similarity import token_jaccard
        assert token_jaccard("alpha beta", "alpha beta") == 1.0

    def test_disjoint(self):
        from entity_resolution.similarity import token_jaccard
        assert token_jaccard("alpha beta", "gamma delta") == 0.0

    def test_partial_overlap(self):
        from entity_resolution.similarity import token_jaccard
        # "alpha beta" vs "alpha gamma" → intersection=1, union=3 → 1/3
        score = token_jaccard("alpha beta", "alpha gamma")
        assert abs(score - 1/3) < 0.01

    def test_both_empty(self):
        from entity_resolution.similarity import token_jaccard
        assert token_jaccard("", "") == 1.0

    def test_one_empty(self):
        from entity_resolution.similarity import token_jaccard
        assert token_jaccard("alpha", "") == 0.0
        assert token_jaccard("", "beta") == 0.0

    def test_subset(self):
        from entity_resolution.similarity import token_jaccard
        # "alpha" vs "alpha beta" → 1/2
        score = token_jaccard("alpha", "alpha beta")
        assert abs(score - 0.5) < 0.01


# ---------------------------------------------------------------------------
# 1-C: blocking.py
# ---------------------------------------------------------------------------

class TestSoundexBlocking:
    def test_similar_names_same_block(self):
        from entity_resolution.blocking import soundex_blocking
        names = ["Muller Phipps", "Mueller Phipps", "XYZ Corp"]
        blocks = soundex_blocking(names)
        # Muller and Mueller should share a block
        found_together = any(
            "Muller Phipps" in block and "Mueller Phipps" in block
            for block in blocks.values()
        )
        assert found_together, f"Muller/Mueller not in same block. Blocks: {blocks}"

    def test_different_names_different_blocks(self):
        from entity_resolution.blocking import soundex_blocking
        names = ["Alpha Inc", "Zebra Corp"]
        blocks = soundex_blocking(names)
        # They should be in different blocks (A vs Z different first letter)
        for block in blocks.values():
            assert not ("Alpha Inc" in block and "Zebra Corp" in block)

    def test_accepts_tuples(self):
        from entity_resolution.blocking import soundex_blocking
        names = [("Muller Phipps", "id1"), ("Mueller Phipps", "id2")]
        blocks = soundex_blocking(names)
        assert len(blocks) >= 1

    def test_empty_input(self):
        from entity_resolution.blocking import soundex_blocking
        assert soundex_blocking([]) == {}


class TestFirst3Blocking:
    def test_same_prefix_same_block(self):
        from entity_resolution.blocking import first3_blocking
        names = ["Alpha Trading", "Alphabet Corp", "Beta Ltd"]
        blocks = first3_blocking(names)
        alpha_block = blocks.get("alp")
        assert alpha_block is not None
        assert len(alpha_block) == 2  # Alpha Trading + Alphabet Corp

    def test_short_name_padded(self):
        from entity_resolution.blocking import first3_blocking
        names = ["AB Corp"]  # normalized "ab corporation" → "ab " prefix
        blocks = first3_blocking(names)
        assert len(blocks) == 1


class TestSortedNeighborhood:
    def test_window_limits_pairs(self):
        from entity_resolution.blocking import sorted_neighborhood
        names = ["E Corp", "A Corp", "B Corp", "C Corp", "D Corp"]
        pairs = sorted_neighborhood(names, window=2)
        # With window=2, only adjacent pairs in sorted order
        assert len(pairs) <= len(names)

    def test_returns_pairs(self):
        from entity_resolution.blocking import sorted_neighborhood
        names = ["Alpha", "Beta", "Gamma"]
        pairs = sorted_neighborhood(names, window=50)
        assert all(isinstance(p, tuple) and len(p) == 2 for p in pairs)

    def test_empty_input(self):
        from entity_resolution.blocking import sorted_neighborhood
        assert sorted_neighborhood([]) == []

    def test_single_item(self):
        from entity_resolution.blocking import sorted_neighborhood
        assert sorted_neighborhood(["only one"]) == []

    def test_no_duplicate_pairs(self):
        from entity_resolution.blocking import sorted_neighborhood
        names = ["Alpha", "Beta", "Gamma", "Delta"]
        pairs = sorted_neighborhood(names, window=10)
        # Convert to frozensets for dedup check
        seen = set()
        for a, b in pairs:
            key = frozenset([a, b])
            assert key not in seen, f"Duplicate pair: {a}, {b}"
            seen.add(key)

    def test_muller_mueller_in_window(self):
        from entity_resolution.blocking import sorted_neighborhood
        # After normalization "mueller" < "muller" alphabetically
        names = ["Muller Phipps", "Mueller Phipps", "ABC Corp", "XYZ Ltd"]
        pairs = sorted_neighborhood(names, window=3)
        pair_names = {frozenset([str(a), str(b)]) for a, b in pairs}
        assert frozenset(["Muller Phipps", "Mueller Phipps"]) in pair_names


class TestCandidatePairsFromBlocks:
    def test_generates_all_pairs_within_block(self):
        from entity_resolution.blocking import candidate_pairs_from_blocks
        blocks = {"M400": ["Muller", "Mueller", "Miller"]}
        pairs = candidate_pairs_from_blocks(blocks)
        # 3 items → 3 pairs
        assert len(pairs) == 3

    def test_deduplicates_across_blocks(self):
        from entity_resolution.blocking import candidate_pairs_from_blocks
        # Same pair appears in two blocks
        blocks = {
            "M400": ["Muller", "Mueller"],
            "X000": ["Muller", "Mueller"],  # overlap
        }
        pairs = candidate_pairs_from_blocks(blocks)
        assert len(pairs) == 1  # deduplicated

    def test_empty_blocks(self):
        from entity_resolution.blocking import candidate_pairs_from_blocks
        assert candidate_pairs_from_blocks({}) == []


# ---------------------------------------------------------------------------
# 1-D: fellegi_sunter.py
# ---------------------------------------------------------------------------

class TestFellegiSunterEM:
    FIELDS = ['name_jw', 'name_jaccard', 'soundex_match']

    def _make_match_vector(self):
        return {'name_jw': 0.95, 'name_jaccard': 0.9, 'soundex_match': 1.0}

    def _make_nonmatch_vector(self):
        return {'name_jw': 0.1, 'name_jaccard': 0.05, 'soundex_match': 0.0}

    def test_predict_match(self):
        from entity_resolution.fellegi_sunter import FellegiSunterEM
        fs = FellegiSunterEM(fields=self.FIELDS)
        vectors = [self._make_match_vector()] * 50 + [self._make_nonmatch_vector()] * 50
        fs.fit(vectors)
        labels = fs.predict([self._make_match_vector()])
        assert labels[0] == 'MATCH', f"Expected MATCH, got {labels[0]}"

    def test_predict_nonmatch(self):
        from entity_resolution.fellegi_sunter import FellegiSunterEM
        fs = FellegiSunterEM(fields=self.FIELDS)
        vectors = [self._make_match_vector()] * 50 + [self._make_nonmatch_vector()] * 50
        fs.fit(vectors)
        labels = fs.predict([self._make_nonmatch_vector()])
        assert labels[0] == 'NON_MATCH', f"Expected NON_MATCH, got {labels[0]}"

    def test_fit_converges(self):
        from entity_resolution.fellegi_sunter import FellegiSunterEM
        fs = FellegiSunterEM(fields=self.FIELDS, max_iter=50, tol=1e-4)
        vectors = [self._make_match_vector()] * 30 + [self._make_nonmatch_vector()] * 30
        fs.fit(vectors)
        assert fs.fitted

    def test_m_greater_than_u_after_fit(self):
        from entity_resolution.fellegi_sunter import FellegiSunterEM
        fs = FellegiSunterEM(fields=self.FIELDS)
        vectors = [self._make_match_vector()] * 40 + [self._make_nonmatch_vector()] * 40
        fs.fit(vectors)
        for f in self.FIELDS:
            assert fs.m[f] > fs.u[f], (
                f"m[{f}]={fs.m[f]:.3f} should be > u[{f}]={fs.u[f]:.3f}"
            )

    def test_score_returns_float_list(self):
        from entity_resolution.fellegi_sunter import FellegiSunterEM
        fs = FellegiSunterEM(fields=self.FIELDS)
        vectors = [self._make_match_vector(), self._make_nonmatch_vector()]
        scores = fs.score(vectors)
        assert len(scores) == 2
        assert all(isinstance(s, float) for s in scores)

    def test_match_score_higher_than_nonmatch(self):
        from entity_resolution.fellegi_sunter import FellegiSunterEM
        fs = FellegiSunterEM(fields=self.FIELDS)
        vectors = [self._make_match_vector()] * 30 + [self._make_nonmatch_vector()] * 30
        fs.fit(vectors)
        scores = fs.score([self._make_match_vector(), self._make_nonmatch_vector()])
        assert scores[0] > scores[1], f"Match score {scores[0]} not > non-match {scores[1]}"

    def test_predict_proba_in_range(self):
        from entity_resolution.fellegi_sunter import FellegiSunterEM
        fs = FellegiSunterEM(fields=self.FIELDS)
        vectors = [self._make_match_vector(), self._make_nonmatch_vector()]
        probs = fs.predict_proba(vectors)
        assert all(0.0 <= p <= 1.0 for p in probs)

    def test_empty_fit_does_not_crash(self):
        from entity_resolution.fellegi_sunter import FellegiSunterEM
        fs = FellegiSunterEM(fields=self.FIELDS)
        fs.fit([])  # Should log warning, not crash
        assert not fs.fitted

    def test_fit_predict_convenience(self):
        from entity_resolution.fellegi_sunter import FellegiSunterEM
        fs = FellegiSunterEM(fields=self.FIELDS)
        vectors = [self._make_match_vector()] * 20 + [self._make_nonmatch_vector()] * 20
        labels = fs.fit_predict(vectors)
        assert len(labels) == 40
        assert all(l in ('MATCH', 'NON_MATCH', 'UNCERTAIN') for l in labels)

    def test_summary_contains_fields(self):
        from entity_resolution.fellegi_sunter import FellegiSunterEM
        fs = FellegiSunterEM(fields=self.FIELDS)
        summary = fs.summary()
        for f in self.FIELDS:
            assert f in summary


# ---------------------------------------------------------------------------
# 1-E: clustering.py
# ---------------------------------------------------------------------------

class TestUnionFind:
    def test_singleton_cluster(self):
        from entity_resolution.clustering import UnionFind
        uf = UnionFind()
        uf._make("A")
        clusters = uf.clusters()
        assert len(clusters) == 1
        assert {"A"} in clusters

    def test_union_merges_sets(self):
        from entity_resolution.clustering import UnionFind
        uf = UnionFind()
        uf.union("A", "B")
        uf.union("B", "C")
        clusters = uf.clusters()
        assert len(clusters) == 1
        assert clusters[0] == {"A", "B", "C"}

    def test_find_with_path_compression(self):
        from entity_resolution.clustering import UnionFind
        uf = UnionFind()
        uf.union("A", "B")
        uf.union("B", "C")
        uf.union("C", "D")
        # All should have same root
        roots = {uf.find(x) for x in ["A", "B", "C", "D"]}
        assert len(roots) == 1

    def test_disjoint_sets(self):
        from entity_resolution.clustering import UnionFind
        uf = UnionFind()
        uf.union("A", "B")
        uf.union("C", "D")
        clusters = uf.clusters()
        assert len(clusters) == 2

    def test_already_same_set(self):
        from entity_resolution.clustering import UnionFind
        uf = UnionFind()
        uf.union("A", "B")
        uf.union("A", "B")  # Duplicate union — should not crash
        clusters = uf.clusters()
        assert len(clusters) == 1


class TestTransitiveClosure:
    def test_basic_transitivity(self):
        from entity_resolution.clustering import transitive_closure
        pairs = [("A", "B"), ("B", "C")]
        labels = ["MATCH", "MATCH"]
        clusters = transitive_closure(pairs, labels)
        # A, B, C should all be in same cluster
        found = any(frozenset({"A", "B", "C"}) == c for c in clusters)
        assert found, f"Expected {{A,B,C}} cluster, got: {clusters}"

    def test_nonmatch_not_linked(self):
        from entity_resolution.clustering import transitive_closure
        pairs = [("A", "B"), ("B", "C")]
        labels = ["MATCH", "NON_MATCH"]
        clusters = transitive_closure(pairs, labels)
        # A and B in one cluster; C is singleton
        sizes = sorted(len(c) for c in clusters)
        assert sizes == [1, 2], f"Expected [1,2], got {sizes}"

    def test_uncertain_not_linked(self):
        from entity_resolution.clustering import transitive_closure
        pairs = [("A", "B")]
        labels = ["UNCERTAIN"]
        clusters = transitive_closure(pairs, labels)
        assert len(clusters) == 2  # Both singletons

    def test_empty_pairs(self):
        from entity_resolution.clustering import transitive_closure
        clusters = transitive_closure([], [])
        assert clusters == []

    def test_returns_frozensets(self):
        from entity_resolution.clustering import transitive_closure
        pairs = [("A", "B")]
        labels = ["MATCH"]
        clusters = transitive_closure(pairs, labels)
        assert all(isinstance(c, frozenset) for c in clusters)

    def test_large_chain(self):
        from entity_resolution.clustering import transitive_closure
        # A-B-C-D-E all MATCH → one big cluster
        pairs = [("A","B"), ("B","C"), ("C","D"), ("D","E")]
        labels = ["MATCH"] * 4
        clusters = transitive_closure(pairs, labels)
        assert len(clusters) == 1
        assert clusters[0] == frozenset({"A","B","C","D","E"})


class TestSelectGoldenRecord:
    def test_single_member(self):
        from entity_resolution.clustering import select_golden_record
        result = select_golden_record(frozenset({"A"}))
        assert result == "A"

    def test_most_complete_record_wins(self):
        from entity_resolution.clustering import select_golden_record
        cluster = frozenset({"id1", "id2", "id3"})
        records = {
            "id1": {"name": "Alpha", "address": None, "phone": None},
            "id2": {"name": "Alpha Trading Co", "address": "123 St", "phone": "555-1234"},
            "id3": {"name": "Alpha Trading", "address": "123 St", "phone": None},
        }
        golden = select_golden_record(cluster, records=records)
        assert golden == "id2"  # Most non-null fields

    def test_fallback_to_alphabetical(self):
        from entity_resolution.clustering import select_golden_record
        cluster = frozenset({"C", "A", "B"})
        golden = select_golden_record(cluster)
        assert golden == "A"  # Alphabetically smallest

    def test_empty_cluster_raises(self):
        from entity_resolution.clustering import select_golden_record
        with pytest.raises((ValueError, StopIteration)):
            select_golden_record(frozenset())


class TestClusterEntities:
    def test_basic_clustering(self):
        from entity_resolution.clustering import cluster_entities
        pairs = [("A", "B"), ("B", "C"), ("D", "E")]
        labels = ["MATCH", "MATCH", "MATCH"]
        result = cluster_entities(pairs, labels)
        # Should have 2 clusters: {A,B,C} and {D,E}
        sizes = sorted(c['size'] for c in result)
        assert sizes == [2, 3]

    def test_cluster_has_golden_member_fields(self):
        from entity_resolution.clustering import cluster_entities
        pairs = [("A", "B")]
        labels = ["MATCH"]
        result = cluster_entities(pairs, labels)
        assert len(result) == 1
        cluster = result[0]
        assert 'golden' in cluster
        assert 'members' in cluster
        assert 'size' in cluster

    def test_golden_is_member(self):
        from entity_resolution.clustering import cluster_entities
        pairs = [("Alpha", "Beta")]
        labels = ["MATCH"]
        result = cluster_entities(pairs, labels)
        cluster = result[0]
        assert cluster['golden'] in cluster['members']

    def test_sorted_by_size_descending(self):
        from entity_resolution.clustering import cluster_entities
        pairs = [("A","B"), ("B","C"), ("D","E")]
        labels = ["MATCH", "MATCH", "MATCH"]
        result = cluster_entities(pairs, labels)
        sizes = [c['size'] for c in result]
        assert sizes == sorted(sizes, reverse=True)

    def test_nonmatch_creates_singletons(self):
        from entity_resolution.clustering import cluster_entities
        pairs = [("A", "B"), ("C", "D")]
        labels = ["NON_MATCH", "NON_MATCH"]
        result = cluster_entities(pairs, labels)
        # All singletons
        assert all(c['size'] == 1 for c in result)
        assert len(result) == 4

    def test_with_records_uses_completeness(self):
        from entity_resolution.clustering import cluster_entities
        pairs = [("id1", "id2")]
        labels = ["MATCH"]
        records = {
            "id1": {"name": "Short Name", "phone": None},
            "id2": {"name": "Full Company Name Ltd", "phone": "123-4567"},
        }
        result = cluster_entities(pairs, labels, records=records)
        assert result[0]['golden'] == "id2"  # More complete record
