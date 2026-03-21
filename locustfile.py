"""
locustfile.py — Zarailink search API stress test.

Usage:
    locust -f locustfile.py --host=http://localhost:8000

Then open http://localhost:8089 and configure users / spawn rate.
"""

import random
from locust import HttpUser, task, between, events

# Representative query corpus covering all 9 query families
QUERIES = [
    # F1 — discovery
    "dextrose",
    "sugar",
    "wheat",
    "rice importers",
    "palm oil",

    # F2 — country-filtered
    "dextrose from China",
    "sugar from Brazil",
    "wheat from Ukraine",
    "palm oil from Malaysia",
    "cotton from USA",

    # F3 — volume-aware
    "sugar over 500 MT",
    "wheat 1000 tons",
    "rice more than 200 MT",
    "dextrose 50 kg",

    # F4 — price-constrained
    "sugar avg price below 400",
    "wheat price less than 300",
    "dextrose price above 600",

    # F5 — time-constrained
    "sugar last 6 months",
    "wheat since 2023",
    "rice recent shipments",

    # F6 — buy intent
    "find suppliers of dextrose",
    "buy palm oil",
    "import wheat from Canada",

    # F7 — sell / export
    "sell cotton",
    "export rice to China",
    "find buyers for sugar",

    # F8 — transaction evidence
    "does ABC Company buy dextrose",
    "show transactions for Nestle sugar",

    # F9 — multi-intent / complex
    "dextrose over 100 MT from China last year",
    "sugar below 500 USD from Brazil last 6 months",
    "import wheat from Ukraine 200 MT",
]


class ZarailinkUser(HttpUser):
    """
    Simulates a Zarailink user performing search queries.
    Think time: 1-5 seconds between requests (realistic user pacing).
    """
    wait_time = between(1, 5)

    @task(10)
    def search_query(self):
        """Main search endpoint — highest weight task."""
        q = random.choice(QUERIES)
        with self.client.get(
            "/api/search/query/",
            params={"q": q},
            name="/api/search/query/",
            catch_response=True,
        ) as resp:
            if resp.status_code == 200:
                data = resp.json()
                if "results" not in data:
                    resp.failure(f"Missing 'results' key in response for q={q!r}")
                elif data.get("_latency_ms", 0) > 2000:
                    resp.failure(f"Latency {data['_latency_ms']}ms > 2000ms for q={q!r}")
                else:
                    resp.success()
            else:
                resp.failure(f"HTTP {resp.status_code} for q={q!r}")

    @task(2)
    def search_with_scope(self):
        """Search with explicit scope param."""
        q = random.choice(QUERIES[:10])
        scope = random.choice(["WORLDWIDE", "PAKISTAN"])
        with self.client.get(
            "/api/search/query/",
            params={"q": q, "scope": scope},
            name="/api/search/query/?scope=",
            catch_response=True,
        ) as resp:
            if resp.status_code == 200:
                resp.success()
            else:
                resp.failure(f"HTTP {resp.status_code}")

    @task(1)
    def search_no_cache(self):
        """Cache-bypass search — heavier but verifies fresh results."""
        q = random.choice(QUERIES)
        with self.client.get(
            "/api/search/query/",
            params={"q": q, "no_cache": "true"},
            name="/api/search/query/?no_cache=true",
            catch_response=True,
        ) as resp:
            if resp.status_code == 200:
                resp.success()
            else:
                resp.failure(f"HTTP {resp.status_code}")


@events.quitting.add_listener
def print_summary(environment, **kwargs):
    """Print P50/P95/P99 after the test run."""
    stats = environment.runner.stats.total
    print(f"\n=== Zarailink Load Test Summary ===")
    print(f"  Requests:     {stats.num_requests}")
    print(f"  Failures:     {stats.num_failures}")
    print(f"  P50 latency:  {stats.get_response_time_percentile(0.5):.0f} ms")
    print(f"  P95 latency:  {stats.get_response_time_percentile(0.95):.0f} ms")
    print(f"  P99 latency:  {stats.get_response_time_percentile(0.99):.0f} ms")
    print(f"  RPS avg:      {stats.current_rps:.1f}")
