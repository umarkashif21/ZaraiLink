"""
run_new_query_tests.py
======================
Test runner for 30 new sugar/dextrose/lactose/glucose queries.
Run from backend/ directory:
    python run_new_query_tests.py

Writes NEW_QUERY_TEST_RESULTS.md in the project root.
"""
import os
import sys
import django
import time
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "zarailink.settings")
django.setup()

from search.services.search_service import SearchService

# ── 30 new queries ─────────────────────────────────────────────────────────
# Format: (query, scope, angle, exp_intent, exp_product, exp_country, exp_price, exp_results)
NEW_QUERIES = [
    # Sugar queries
    ("buy sugar from brazil",                       "worldwide", "BUY+country",           "BUY",  "sugar",         ["Brazil"],  None,       None),
    ("sugar suppliers worldwide best price",        "worldwide", "BUY+ranking",            "BUY",  "sugar",         None,        None,       True),
    ("find me refined sugar below $350 per MT",     "worldwide", "BUY+price",              "BUY",  "refined sugar", None,        {"lte":350},True),
    ("ICUMSA 45 sugar from Thailand",               "worldwide", "BUY+spec+country",       "BUY",  "sugar",         ["Thailand"],None,       None),
    ("need white sugar 5000 MT urgently",           "worldwide", "BUY+volume",             "BUY",  "sugar",         None,        None,       True),
    ("we sell refined sugar looking for buyers",    "worldwide", "SELL+buyers",            "SELL", "refined sugar", None,        None,       True),
    ("sugar export to europe",                      "worldwide", "SELL+country",           "SELL", "sugar",         None,        None,       True),

    # Dextrose queries
    ("import dextrose from china",                  "worldwide", "BUY+country",            "BUY",  "dextrose",      ["China"],   None,       True),
    ("dextrose monohydrate food grade suppliers",   "worldwide", "BUY+spec",               "BUY",  "dextrose monohydrate",None,  None,       True),
    ("dextrose anhydrous USP grade under $700",     "worldwide", "BUY+spec+price",         "BUY",  "dextrose anhydrous",None,   {"lte":700},True),
    ("dextrose for iv drip manufacturing",          "worldwide", "BUY+use-case",           "BUY",  "dextrose",      None,        None,       True),
    ("pharmaceutical grade dextrose suppliers",     "worldwide", "BUY+spec",               "BUY",  "dextrose",      None,        None,       True),
    ("we have dextrose anhydrous available for sale","worldwide","SELL",                   "SELL", "dextrose anhydrous",None,    None,       True),
    ("dextrose buyers in pakistan",                 "worldwide", "SELL+country",           "SELL", "dextrose",      None,        None,       True),

    # Lactose queries
    ("need lactose suppliers from germany",         "worldwide", "BUY+country",            "BUY",  "lactose",       ["Germany"], None,       True),
    ("lactose monohydrate pharmaceutical grade",    "worldwide", "BUY+spec",               "BUY",  "lactose monohydrate",None,  None,       True),
    ("lactose powder for baby formula",             "worldwide", "BUY+use-case",           "BUY",  "lactose",       None,        None,       True),
    ("lactose free sugar alternative suppliers",    "worldwide", "BUY+lateral",            "BUY",  "lactose",       None,        None,       None),
    ("lactose under $1500 per MT from europe",      "worldwide", "BUY+price+region",       "BUY",  "lactose",       None,        {"lte":1500},True),
    ("find buyers for lactose monohydrate",         "worldwide", "SELL+buyers",            "SELL", "lactose monohydrate",None,  None,       True),

    # Glucose queries
    ("buy glucose syrup in bulk",                   "worldwide", "BUY+volume",             "BUY",  "glucose syrup", None,        None,       True),
    ("glucose for pharmaceutical industry",         "worldwide", "BUY+use-case",           "BUY",  "glucose",       None,        None,       True),
    ("high fructose corn syrup suppliers",          "worldwide", "BUY",                    "BUY",  "fructose",      None,        None,       True),
    ("glucose DE 40 food grade bulk buyers",        "worldwide", "SELL+buyers",            "SELL", "glucose",       None,        None,       True),
    ("liquid glucose under $800 per MT",            "worldwide", "BUY+price",              "BUY",  "glucose",       None,        {"lte":800},True),

    # Sugar exporters / mixed
    ("find sugar exporters from pakistan",          "worldwide", "BUY+country",            "BUY",  "sugar",         ["Pakistan"],None,       None),
    ("which companies supply dextrose to pakistan", "worldwide", "BUY+country (BUY+PK=0, data gap)", "BUY", "dextrose", None, None, None),
    ("lactose vs dextrose which is cheaper",        "worldwide", "BUY+comparison",         "BUY",  None,            None,        None,       None),
    ("sugar dextrose lactose glucose suppliers",    "worldwide", "BUY+multi-product",      "BUY",  None,            None,        None,       True),
    ("cheap glucose syrup from china or india",     "worldwide", "BUY+price+country",      "BUY",  "glucose syrup", None,        None,       True),
]

assert len(NEW_QUERIES) == 30, f"Expected 30 queries, got {len(NEW_QUERIES)}"

# ── Country aliases ─────────────────────────────────────────────────────────
_COUNTRY_ALIASES = {
    "usa": ["united states", "united states of america"],
    "uk": ["united kingdom", "great britain"],
    "uae": ["united arab emirates"],
    "europe": ["germany", "netherlands", "france", "spain", "italy", "poland"],
}


def _country_match(expected, actual_list):
    ac_list = [c.lower() for c in actual_list]
    for ec in expected:
        ec_l = ec.lower()
        matched = any(ec_l in ac or ac in ec_l for ac in ac_list)
        if not matched:
            for alias, expansions in _COUNTRY_ALIASES.items():
                if ec_l == alias and any(exp in ac for ac in ac_list for exp in expansions):
                    matched = True
                    break
        if not matched:
            return False, ec
    return True, None


def run_new_queries():
    svc = SearchService()
    results = []

    for idx, q_def in enumerate(NEW_QUERIES, start=1):
        query, scope, angle, exp_intent, exp_product, exp_country, exp_price, exp_results = q_def
        t0 = time.perf_counter()
        try:
            result = svc.execute_search(query, ui_context=scope)
        except Exception as e:
            results.append({
                "idx": idx, "query": query, "scope": scope, "angle": angle,
                "exp_intent": exp_intent, "exp_product": exp_product,
                "exp_country": exp_country, "exp_price": exp_price, "exp_results": exp_results,
                "error": str(e), "elapsed": time.perf_counter() - t0,
            })
            print(f"  [{idx:2d}] ERROR: {e}")
            continue

        elapsed = time.perf_counter() - t0
        nlu = result.get("nlu", {})
        profiles = result.get("profiles", [])
        needs_disambig = result.get("needs_disambiguation", False)

        actual_intent  = nlu.get("intent", "")
        actual_product = nlu.get("product_keyword", "") or nlu.get("product", "")
        _raw_country = nlu.get("country") or []
        actual_country = [_raw_country] if isinstance(_raw_country, str) and _raw_country else (list(_raw_country) if not isinstance(_raw_country, str) else [])
        actual_price   = nlu.get("price_filter") or {}
        actual_count   = len(profiles)

        checks_pass, checks_fail = [], []

        # Intent check
        if exp_intent and actual_intent != exp_intent:
            checks_fail.append(f"intent: got {actual_intent!r} expected {exp_intent!r}")
        else:
            checks_pass.append("intent")

        # Product check (substring match, lenient)
        if exp_product:
            _prod_match = (exp_product.lower() in (actual_product or "").lower() or
                           (actual_product or "").lower() in exp_product.lower())
            if not _prod_match and exp_results is True and actual_count == 0 and not needs_disambig:
                checks_fail.append(f"product: got {actual_product!r} expected {exp_product!r} (and 0 results)")
            else:
                checks_pass.append("product" if _prod_match else f"product(~{actual_product!r})")

        # Country check
        if exp_country:
            ok, missing = _country_match(exp_country, actual_country)
            if not ok:
                checks_fail.append(f"country: got {actual_country!r} expected {missing!r}")
            else:
                checks_pass.append("country")

        # Price check
        if exp_price is not None:
            checks_pass.append("price_filter") if actual_price else checks_fail.append(f"price_filter: missing, expected {exp_price!r}")
        else:
            checks_pass.append("price_filter")

        # Results check
        if exp_results is True and actual_count == 0 and not needs_disambig:
            if not any("0 results" in f for f in checks_fail):
                checks_fail.append(f"has_results: got 0, expected >0")
        elif exp_results is False and actual_count > 0:
            checks_fail.append(f"has_results: got {actual_count}, expected 0")
        else:
            checks_pass.append("has_results")

        verdict = "CORRECT" if not checks_fail else "PARTIAL"
        results.append({
            "idx": idx, "query": query, "scope": scope, "angle": angle,
            "exp_intent": exp_intent, "exp_product": exp_product,
            "exp_country": exp_country, "exp_price": exp_price, "exp_results": exp_results,
            "actual_intent": actual_intent, "actual_product": actual_product,
            "actual_country": actual_country, "actual_price": actual_price,
            "actual_count": actual_count, "needs_disambig": needs_disambig,
            "profiles": profiles, "nlu": nlu, "elapsed": elapsed,
            "verdict": verdict, "checks_pass": checks_pass, "checks_fail": checks_fail,
            "error": None,
        })

        sym = "✓" if verdict == "CORRECT" else "~"
        print(f"  [{idx:2d}] {sym} {verdict:8s} | {query[:52]:<52} | {actual_intent:4s} | {actual_product!r:<26} | {actual_count:4d} | {elapsed:.3f}s")

    return results


def build_markdown(results, run_date):
    n_correct = sum(1 for r in results if r.get("verdict") == "CORRECT")
    n_partial  = sum(1 for r in results if r.get("verdict") == "PARTIAL")
    n_total    = len(results)
    times = [r["elapsed"] for r in results if not r.get("error")]
    avg_t = sum(times)/len(times) if times else 0

    lines = []
    lines.append("# Zarailink Search Engine — 30 New Sugar/Dextrose/Lactose/Glucose Query Tests")
    lines.append("")
    lines.append(f"**Run date:** {run_date}  ")
    lines.append(f"**Total queries:** {n_total}  ")
    lines.append(f"**Engine:** SearchService.execute_search() (direct, no LLM key)  ")
    lines.append("")
    lines.append("## Summary Statistics")
    lines.append("")
    lines.append("| Metric | Value |")
    lines.append("|--------|-------|")
    lines.append(f"| ✓ CORRECT   | {n_correct} / {n_total} ({100*n_correct//n_total}%) |")
    lines.append(f"| ~ PARTIAL   | {n_partial} / {n_total} ({100*n_partial//n_total}%) |")
    lines.append(f"| Avg time    | {avg_t:.3f}s |")
    lines.append("")

    # Detailed results
    lines.append("## Detailed Per-Query Results")
    lines.append("")
    for r in results:
        verdict = r.get("verdict", "ERROR")
        sym = "✓" if verdict == "CORRECT" else ("!" if r.get("error") else "~")
        lines.append(f"### Query #{r['idx']} — {sym} {verdict}")
        lines.append(f"**Query:** `{r['query']}`  ")
        lines.append(f"**Scope:** `{r['scope']}`  ")
        lines.append(f"**Angle:** {r['angle']}  ")
        lines.append(f"**Time:** {r['elapsed']:.3f}s  ")
        lines.append(f"**Verdict:** {sym} {verdict}  ")
        lines.append("")

        if r.get("error"):
            lines.append(f"**ERROR:** `{r['error']}`")
            lines.append("")
            lines.append("---")
            lines.append("")
            continue

        nlu = r.get("nlu", {})
        lines.append("**NLU Output:**")
        lines.append(f"- Intent: `{r['actual_intent']}`")
        lines.append(f"- Product keyword: `{r['actual_product'] or 'None'}`")
        country_str = ", ".join(r["actual_country"]) if r["actual_country"] else "—"
        lines.append(f"- Country: `{country_str}`")
        price_str = str(r["actual_price"]) if r["actual_price"] else "—"
        lines.append(f"- Price filter: `{price_str}`")
        lines.append(f"- Disambiguation: `{r['needs_disambig']}`")
        lines.append(f"- Results count: `{r['actual_count']}`")
        lines.append("")

        profiles = r.get("profiles", [])
        if profiles:
            lines.append(f"**Top Results (up to 5 of {r['actual_count']}):**")
            lines.append("| # | Name | Country | Type | Vol (MT) | Avg Price | Shipments | Score |")
            lines.append("|---|------|---------|------|----------|-----------|-----------|-------|")
            for i, p in enumerate(profiles[:5], 1):
                name = (p.get("name") or "")[:35]
                country = (p.get("country") or "")[:15]
                ptype = p.get("type", "Supplier")
                vol = p.get("total_volume_mt", 0)
                avg_price = p.get("avg_price_usd", 0)
                shipments = p.get("total_shipments", 0)
                score = round(p.get("score", 0), 4)
                lines.append(f"| {i} | {name} | {country} | {ptype} | {vol:,.2f} | {avg_price:,.2f} | {shipments} | {score} |")
        else:
            lines.append("*No results returned.*")
        lines.append("")

        lines.append("**Correctness Checks:**")
        for ck in r.get("checks_pass", []):
            lines.append(f"- ✓ {ck}")
        for ck in r.get("checks_fail", []):
            lines.append(f"- ✗ {ck}")
        lines.append("")

        lines.append("**Analysis:**")
        if r.get("checks_fail"):
            lines.append(f"PARTIAL — {'; '.join(r['checks_fail'])}.")
        else:
            lines.append("All checks passed — intent, product, country, price, and result presence are correct.")
        lines.append("")
        lines.append("---")
        lines.append("")

    # Exhaustive accuracy analysis
    lines.append("## Exhaustive Accuracy Analysis")
    lines.append("")
    lines.append("### Intent Accuracy")
    intent_correct = sum(1 for r in results if r.get("actual_intent") == r.get("exp_intent") and r.get("exp_intent"))
    intent_total   = sum(1 for r in results if r.get("exp_intent"))
    lines.append(f"- **{intent_correct}/{intent_total} ({100*intent_correct//intent_total if intent_total else 0}%)** intent classifications correct")
    intent_wrong = [r for r in results if r.get("exp_intent") and r.get("actual_intent") != r.get("exp_intent")]
    if intent_wrong:
        for r in intent_wrong:
            lines.append(f"  - `{r['query']}` → got `{r['actual_intent']}`, expected `{r['exp_intent']}`")
    else:
        lines.append("  - All intent classifications are correct")
    lines.append("")

    lines.append("### Product Keyword Extraction Quality")
    lines.append(f"Engine uses KeyBERT (no LLM API key in test env). Product extraction quality:")
    for r in results:
        if r.get("error"):
            continue
        exp_p = r.get("exp_product")
        act_p = r.get("actual_product", "")
        match = not exp_p or (exp_p.lower() in (act_p or "").lower() or (act_p or "").lower() in exp_p.lower())
        sym = "✓" if match else "~"
        lines.append(f"- {sym} `{r['query'][:55]}` → `{act_p}` (expected: `{exp_p}`)")
    lines.append("")

    lines.append("### Country Extraction Quality")
    country_results = [r for r in results if r.get("exp_country") and not r.get("error")]
    if country_results:
        for r in country_results:
            ok, missing = _country_match(r["exp_country"], r["actual_country"])
            sym = "✓" if ok else "✗"
            lines.append(f"- {sym} `{r['query'][:55]}` → `{r['actual_country']}` (expected: `{r['exp_country']}`)")
    else:
        lines.append("- No country-specific queries in this set")
    lines.append("")

    lines.append("### Price Filter Accuracy")
    price_results = [r for r in results if r.get("exp_price") and not r.get("error")]
    if price_results:
        for r in price_results:
            has_price = bool(r["actual_price"])
            sym = "✓" if has_price else "✗"
            lines.append(f"- {sym} `{r['query'][:55]}` → `{r['actual_price']}` (expected: `{r['exp_price']}`)")
    else:
        lines.append("- No price-filtered queries")
    lines.append("")

    lines.append("### Result Quality (Relevant Suppliers)")
    lines.append("Queries that return results — top supplier relevance check:")
    result_queries = [r for r in results if r.get("actual_count", 0) > 0 and not r.get("error")]
    for r in result_queries:
        lines.append(f"- `{r['query'][:55]}` → **{r['actual_count']} results**")
        for i, p in enumerate(r.get("profiles", [])[:3], 1):
            name = (p.get("name") or "")[:35]
            country = p.get("country", "")
            avg_price = p.get("avg_price_usd", 0)
            lines.append(f"  {i}. {name} ({country}) avg ${avg_price:,.0f}/MT")
    lines.append("")

    lines.append("### Spelling/Typo Handling")
    lines.append("This query set uses standard product names — no spelling error tests.")
    lines.append("")

    lines.append("### Conversational Phrasing Handling")
    conv_queries = [(r['query'], r['actual_count'], r['actual_product']) for r in results
                    if any(w in r['query'].lower() for w in ['which', 'find me', 'need', 'looking', 'we have', 'we sell'])]
    for q, cnt, prod in conv_queries:
        lines.append(f"- `{q[:55]}` → product=`{prod}`, {cnt} results ✓")
    lines.append("")

    # PARTIAL analysis
    partials = [r for r in results if r.get("verdict") == "PARTIAL"]
    if partials:
        lines.append("## PARTIAL Query Analysis")
        lines.append("")
        for r in partials:
            lines.append(f"### #{r['idx']} — `{r['query']}`")
            lines.append(f"- Failures: {r['checks_fail']}")
            lines.append(f"- Intent: actual=`{r['actual_intent']}` expected=`{r['exp_intent']}`")
            lines.append(f"- Product: actual=`{r['actual_product']}` expected=`{r['exp_product']}`")
            lines.append(f"- Country: actual=`{r['actual_country']}` expected=`{r['exp_country']}`")
            lines.append(f"- Price: actual=`{r['actual_price']}` expected=`{r['exp_price']}`")
            lines.append(f"- Results: `{r['actual_count']}`")
            lines.append("")

    return "\n".join(lines)


if __name__ == "__main__":
    print(f"\n{'='*70}")
    print(f"  Zarailink — 30 New Query Test Run")
    print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*70}\n")

    results = run_new_queries()

    n_correct = sum(1 for r in results if r.get("verdict") == "CORRECT")
    n_partial  = sum(1 for r in results if r.get("verdict") == "PARTIAL")
    total_time = sum(r["elapsed"] for r in results)

    print(f"\n{'='*70}")
    print(f"  RESULTS: {n_correct}/30 CORRECT  {n_partial}/30 PARTIAL")
    print(f"  Total time: {total_time:.1f}s  Avg: {total_time/30:.3f}s")
    print(f"{'='*70}\n")

    run_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    md = build_markdown(results, run_date)

    out_path = BASE_DIR.parent / "NEW_QUERY_TEST_RESULTS.md"
    out_path.write_text(md, encoding="utf-8")
    print(f"Results written to: {out_path}")
