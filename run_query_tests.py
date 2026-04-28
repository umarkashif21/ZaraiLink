#!/usr/bin/env python3
"""
Zarailink Search Engine — Exhaustive 150-Query Test Suite
Runs every query 3 at a time (ThreadPoolExecutor), records timing,
parses the engine's response, evaluates correctness, writes a full report.
"""
import requests, time, json, sys, re
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

BASE_URL = "http://localhost:8000/api/search/"
TIMEOUT  = 45  # seconds per request

# ---------------------------------------------------------------------------
# QUERY REGISTRY
# Each entry is a dict:
#   id, query, scope, group, angle
#   exp_intent  : "BUY" | "SELL" | None  (None = skip intent check)
#   exp_product : str | None              (substring check on product_keyword)
#   exp_country : str | None              (substring check on parsed country)
#   exp_price   : True | False | None     (True = price_filter must be set)
#   exp_results : True | False | None     (True = count>0, False = count==0, None = skip)
# ---------------------------------------------------------------------------
QUERIES = [
    # ── GROUP A — Bare / Minimal ──────────────────────────────────────────
    dict(id=1,  query="sugar",    scope="worldwide", group="A", angle="BARE KEYWORD, default BUY",
         exp_intent="BUY", exp_product="sugar",  exp_country=None, exp_price=False, exp_results=True),
    dict(id=2,  query="dex",      scope="worldwide", group="A", angle="3-CHAR ABBREVIATION, trigram match",
         exp_intent="BUY", exp_product="dex",    exp_country=None, exp_price=False, exp_results=None),
    dict(id=3,  query="1702",     scope="worldwide", group="A", angle="BARE HS CODE, cascade lookup",
         exp_intent="BUY", exp_product=None,     exp_country=None, exp_price=False, exp_results=None),
    dict(id=4,  query="SEAWALL",  scope="worldwide", group="A", angle="COMPANY NAME, transaction fallback",
         exp_intent="BUY", exp_product=None,     exp_country=None, exp_price=False, exp_results=None),
    dict(id=5,  query="s",        scope="worldwide", group="A", angle="SINGLE CHAR, graceful no-match",
         exp_intent="BUY", exp_product=None,     exp_country=None, exp_price=False, exp_results=False),

    # ── GROUP B — Basic BUY Intent ────────────────────────────────────────
    dict(id=6,  query="buy sugar",                         scope="worldwide", group="B", angle="BASIC BUY, single product",
         exp_intent="BUY", exp_product="sugar",        exp_country=None, exp_price=False, exp_results=True),
    dict(id=7,  query="i want to buy dextrose anhydrous",  scope="worldwide", group="B", angle="EXPLICIT BUY, full product name",
         exp_intent="BUY", exp_product="dextrose",     exp_country=None, exp_price=False, exp_results=True),
    dict(id=8,  query="i need basmati rice",               scope="worldwide", group="B", angle="NEED = BUY, common phrasing",
         exp_intent="BUY", exp_product="basmati",      exp_country=None, exp_price=False, exp_results=True),
    dict(id=9,  query="purchase refined sugar",            scope="worldwide", group="B", angle="PURCHASE VERB, BUY intent",
         exp_intent="BUY", exp_product="sugar",        exp_country=None, exp_price=False, exp_results=True),
    dict(id=10, query="looking for wheat",                 scope="worldwide", group="B", angle="LOOKING FOR = BUY, no supplier mention",
         exp_intent="BUY", exp_product="wheat",        exp_country=None, exp_price=False, exp_results=True),
    dict(id=11, query="find me cotton yarn",               scope="worldwide", group="B", angle="FIND ME = BUY, imperative",
         exp_intent="BUY", exp_product="cotton",       exp_country=None, exp_price=False, exp_results=True),
    dict(id=12, query="i am interested in buying palm oil",scope="worldwide", group="B", angle="INTERESTED IN BUYING phrase",
         exp_intent="BUY", exp_product="palm oil",     exp_country=None, exp_price=False, exp_results=True),
    dict(id=13, query="want to get urea fertilizer",       scope="worldwide", group="B", angle="WANT TO GET, casual BUY",
         exp_intent="BUY", exp_product="urea",         exp_country=None, exp_price=False, exp_results=True),

    # ── GROUP C — Basic SELL Intent ───────────────────────────────────────
    dict(id=14, query="sugar for sale",                              scope="worldwide", group="C", angle="FOR SALE phrase = SELL",
         exp_intent="SELL", exp_product="sugar",   exp_country=None, exp_price=False, exp_results=True),
    dict(id=15, query="we are selling wheat",                        scope="worldwide", group="C", angle="WE ARE SELLING = SELL",
         exp_intent="SELL", exp_product="wheat",   exp_country=None, exp_price=False, exp_results=True),
    dict(id=16, query="i have dextrose anhydrous for sale",          scope="worldwide", group="C", angle="I HAVE X FOR SALE = SELL",
         exp_intent="SELL", exp_product="dextrose",exp_country=None, exp_price=False, exp_results=True),
    dict(id=17, query="basmati rice in stock",                       scope="worldwide", group="C", angle="IN STOCK = SELL",
         exp_intent="SELL", exp_product="basmati", exp_country=None, exp_price=False, exp_results=True),
    dict(id=18, query="we export cotton yarn",                       scope="worldwide", group="C", angle="WE EXPORT = SELL",
         exp_intent="SELL", exp_product="cotton",  exp_country=None, exp_price=False, exp_results=True),
    dict(id=19, query="i am a supplier of refined sugar",            scope="worldwide", group="C", angle="I AM A SUPPLIER = SELL",
         exp_intent="SELL", exp_product="sugar",   exp_country=None, exp_price=False, exp_results=True),
    dict(id=20, query="our company produces urea and we want to sell",scope="worldwide", group="C", angle="WE PRODUCE + SELL = SELL",
         exp_intent="SELL", exp_product="urea",    exp_country=None, exp_price=False, exp_results=True),

    # ── GROUP D — Find Suppliers (semantic reversal → BUY) ───────────────
    dict(id=21, query="find suppliers of dextrose anhydrous",  scope="worldwide", group="D", angle="FIND SUPPLIERS = BUY",
         exp_intent="BUY", exp_product="dextrose", exp_country=None, exp_price=False, exp_results=True),
    dict(id=22, query="looking for sellers of refined sugar",  scope="worldwide", group="D", angle="SEMANTIC REVERSAL — sellers = BUY",
         exp_intent="BUY", exp_product="sugar",    exp_country=None, exp_price=False, exp_results=True),
    dict(id=23, query="looking for exporters of basmati rice", scope="worldwide", group="D", angle="EXPORTERS = BUY not SELL",
         exp_intent="BUY", exp_product="basmati",  exp_country=None, exp_price=False, exp_results=True),
    dict(id=24, query="who sells cotton yarn",                 scope="worldwide", group="D", angle="WHO SELLS = BUY",
         exp_intent="BUY", exp_product="cotton",   exp_country=None, exp_price=False, exp_results=True),
    dict(id=25, query="find manufacturers of urea fertilizer", scope="worldwide", group="D", angle="MANUFACTURERS = BUY",
         exp_intent="BUY", exp_product="urea",     exp_country=None, exp_price=False, exp_results=True),

    # ── GROUP E — Find Buyers (SELL hidden in "find buyers") ─────────────
    dict(id=26, query="find buyers for basmati rice",                   scope="worldwide", group="E", angle="FIND BUYERS = SELL",
         exp_intent="SELL", exp_product="basmati", exp_country=None, exp_price=False, exp_results=True),
    dict(id=27, query="looking for importers of cotton yarn",           scope="worldwide", group="E", angle="IMPORTERS = SELL",
         exp_intent="SELL", exp_product="cotton",  exp_country=None, exp_price=False, exp_results=True),
    dict(id=28, query="who buys refined sugar",                         scope="worldwide", group="E", angle="WHO BUYS = SELL",
         exp_intent="SELL", exp_product="sugar",   exp_country=None, exp_price=False, exp_results=True),
    dict(id=29, query="find companies interested in buying our wheat",  scope="worldwide", group="E", angle="OUR PRODUCT = SELL",
         exp_intent="SELL", exp_product="wheat",   exp_country=None, exp_price=False, exp_results=True),

    # ── GROUP F — Price Operator Queries ──────────────────────────────────
    dict(id=30, query="sugar under $500",               scope="worldwide", group="F", angle="WORD LTE operator",
         exp_intent="BUY", exp_product="sugar",  exp_country=None, exp_price=True, exp_results=True),
    dict(id=31, query="wheat above $250",               scope="worldwide", group="F", angle="WORD GTE operator",
         exp_intent="BUY", exp_product="wheat",  exp_country=None, exp_price=True, exp_results=True),
    dict(id=32, query="dextrose anhydrous around $700", scope="worldwide", group="F", angle="RANGE ±15% operator",
         exp_intent="BUY", exp_product="dextrose",exp_country=None, exp_price=True, exp_results=True),
    dict(id=33, query="rice <= $600",                   scope="worldwide", group="F", angle="SYMBOL LTE operator",
         exp_intent="BUY", exp_product="rice",   exp_country=None, exp_price=True, exp_results=True),
    dict(id=34, query="cotton >= $1000",                scope="worldwide", group="F", angle="SYMBOL GTE operator",
         exp_intent="BUY", exp_product="cotton", exp_country=None, exp_price=True, exp_results=True),
    dict(id=35, query="palm oil at most $900",          scope="worldwide", group="F", angle="AT MOST = LTE",
         exp_intent="BUY", exp_product="palm",   exp_country=None, exp_price=True, exp_results=True),
    dict(id=36, query="urea at least $250",             scope="worldwide", group="F", angle="AT LEAST = GTE",
         exp_intent="BUY", exp_product="urea",   exp_country=None, exp_price=True, exp_results=True),
    dict(id=37, query="refined sugar not exceeding $400",scope="worldwide", group="F", angle="NOT EXCEEDING = LTE",
         exp_intent="BUY", exp_product="sugar",  exp_country=None, exp_price=True, exp_results=True),
    dict(id=38, query="wheat starting from $200",       scope="worldwide", group="F", angle="STARTING FROM = GTE",
         exp_intent="BUY", exp_product="wheat",  exp_country=None, exp_price=True, exp_results=True),
    dict(id=39, query="sugar under five hundred dollars",scope="worldwide", group="F", angle="WRITTEN NUMBER, no digit",
         exp_intent="BUY", exp_product="sugar",  exp_country=None, exp_price=True, exp_results=True),
    dict(id=40, query="dextrose approximately $650",    scope="worldwide", group="F", angle="APPROXIMATE = RANGE",
         exp_intent="BUY", exp_product="dextrose",exp_country=None, exp_price=True, exp_results=True),

    # ── GROUP G — Ranking Hint (no price number) ──────────────────────────
    dict(id=41, query="cheap sugar",              scope="worldwide", group="G", angle="RANKING: price_asc, no number",
         exp_intent="BUY", exp_product="sugar",  exp_country=None, exp_price=False, exp_results=True),
    dict(id=42, query="affordable wheat",         scope="worldwide", group="G", angle="RANKING: price_asc synonym",
         exp_intent="BUY", exp_product="wheat",  exp_country=None, exp_price=False, exp_results=True),
    dict(id=43, query="premium dextrose anhydrous",scope="worldwide", group="G", angle="RANKING: price_desc",
         exp_intent="BUY", exp_product="dextrose",exp_country=None, exp_price=False, exp_results=True),
    dict(id=44, query="bulk basmati rice",         scope="worldwide", group="G", angle="RANKING: volume-heavy preset",
         exp_intent="BUY", exp_product="basmati", exp_country=None, exp_price=False, exp_results=True),
    dict(id=45, query="high quality refined sugar",scope="worldwide", group="G", angle="RANKING: price_desc implicit",
         exp_intent="BUY", exp_product="sugar",   exp_country=None, exp_price=False, exp_results=True),
    dict(id=46, query="cheapest cotton yarn",      scope="worldwide", group="G", angle="SUPERLATIVE price_asc",
         exp_intent="BUY", exp_product="cotton",  exp_country=None, exp_price=False, exp_results=True),
    dict(id=47, query="best quality palm oil",     scope="worldwide", group="G", angle="BEST QUALITY = price_desc",
         exp_intent="BUY", exp_product="palm",    exp_country=None, exp_price=False, exp_results=True),

    # ── GROUP H — Country Queries ──────────────────────────────────────────
    dict(id=48, query="sugar from China",         scope="worldwide", group="H", angle="COUNTRY FILTER: China",
         exp_intent="BUY", exp_product="sugar",  exp_country="china",   exp_price=False, exp_results=None),
    dict(id=49, query="wheat from Russia",        scope="worldwide", group="H", angle="COUNTRY FILTER: Russia",
         exp_intent="BUY", exp_product="wheat",  exp_country="russia",  exp_price=False, exp_results=None),
    dict(id=50, query="basmati rice from India",  scope="worldwide", group="H", angle="COUNTRY FILTER: India",
         exp_intent="BUY", exp_product="basmati",exp_country="india",   exp_price=False, exp_results=None),
    dict(id=51, query="palm oil from Malaysia",   scope="worldwide", group="H", angle="COUNTRY FILTER: Malaysia",
         exp_intent="BUY", exp_product="palm",   exp_country="malaysia",exp_price=False, exp_results=None),
    dict(id=52, query="cotton from USA",          scope="worldwide", group="H", angle="COUNTRY FILTER: USA",
         exp_intent="BUY", exp_product="cotton", exp_country="usa",     exp_price=False, exp_results=None),
    dict(id=53, query="soybean from Brazil",      scope="worldwide", group="H", angle="COUNTRY FILTER: Brazil",
         exp_intent="BUY", exp_product="soybean",exp_country="brazil",  exp_price=False, exp_results=None),
    dict(id=54, query="import wheat from Ukraine",scope="worldwide", group="H", angle="IMPORT verb + COUNTRY",
         exp_intent="BUY", exp_product="wheat",  exp_country="ukraine", exp_price=False, exp_results=None),
    dict(id=55, query="Chinese sugar suppliers",  scope="worldwide", group="H", angle="DEMONYM country form",
         exp_intent="BUY", exp_product="sugar",  exp_country="china",   exp_price=False, exp_results=None),

    # ── GROUP I — Combined Multi-Criteria ─────────────────────────────────
    dict(id=56, query="dextrose anhydrous from China under $700",        scope="worldwide", group="I", angle="PRODUCT + COUNTRY + PRICE",
         exp_intent="BUY", exp_product="dextrose", exp_country="china",  exp_price=True, exp_results=None),
    dict(id=57, query="refined sugar from Brazil below $400",            scope="worldwide", group="I", angle="PRODUCT + COUNTRY + LTE",
         exp_intent="BUY", exp_product="sugar",    exp_country="brazil", exp_price=True, exp_results=None),
    dict(id=58, query="basmati rice from India under $600",              scope="worldwide", group="I", angle="PRODUCT + COUNTRY + LTE",
         exp_intent="BUY", exp_product="basmati",  exp_country="india",  exp_price=True, exp_results=None),
    dict(id=59, query="bulk palm oil from Malaysia below $900",          scope="worldwide", group="I", angle="RANKING + COUNTRY + PRICE",
         exp_intent="BUY", exp_product="palm",     exp_country="malaysia",exp_price=True, exp_results=None),
    dict(id=60, query="cheap wheat from Russia",                         scope="worldwide", group="I", angle="RANKING + COUNTRY, no number",
         exp_intent="BUY", exp_product="wheat",    exp_country="russia", exp_price=False, exp_results=None),
    dict(id=61, query="premium cotton yarn from Pakistan above $1000",   scope="worldwide", group="I", angle="RANKING + COUNTRY + GTE",
         exp_intent="BUY", exp_product="cotton",   exp_country="pakistan",exp_price=True, exp_results=None),
    dict(id=62, query="find suppliers of dextrose from China under $700",scope="worldwide", group="I", angle="FIND + COUNTRY + PRICE",
         exp_intent="BUY", exp_product="dextrose", exp_country="china",  exp_price=True, exp_results=None),
    dict(id=63, query="looking for cheap basmati rice from India",       scope="worldwide", group="I", angle="INTENT + RANKING + COUNTRY",
         exp_intent="BUY", exp_product="basmati",  exp_country="india",  exp_price=False, exp_results=None),

    # ── GROUP J — HS Code Queries ──────────────────────────────────────────
    dict(id=64, query="1702.3090",        scope="worldwide", group="J", angle="HS: dotted notation",
         exp_intent="BUY", exp_product=None, exp_country=None, exp_price=False, exp_results=None),
    dict(id=65, query="17021990",         scope="worldwide", group="J", angle="HS: bare digit string",
         exp_intent="BUY", exp_product=None, exp_country=None, exp_price=False, exp_results=None),
    dict(id=66, query="HS code 1701.991", scope="worldwide", group="J", angle="HS: with explicit label",
         exp_intent="BUY", exp_product=None, exp_country=None, exp_price=False, exp_results=None),
    dict(id=67, query="tariff code 1001", scope="worldwide", group="J", angle="HS: tariff code prefix",
         exp_intent="BUY", exp_product=None, exp_country=None, exp_price=False, exp_results=None),
    dict(id=68, query="chapter 17",       scope="worldwide", group="J", angle="HS: chapter-level lookup",
         exp_intent="BUY", exp_product=None, exp_country=None, exp_price=False, exp_results=None),
    dict(id=69, query="1702 30 90",       scope="worldwide", group="J", angle="HS: space-separated",
         exp_intent="BUY", exp_product=None, exp_country=None, exp_price=False, exp_results=None),
    dict(id=70, query="HS 5201",          scope="worldwide", group="J", angle="HS: short label prefix",
         exp_intent="BUY", exp_product=None, exp_country=None, exp_price=False, exp_results=None),
    dict(id=71, query="heading 1701",     scope="worldwide", group="J", angle="HS: heading prefix",
         exp_intent="BUY", exp_product=None, exp_country=None, exp_price=False, exp_results=None),

    # ── GROUP K — Procurement / Formal Language ───────────────────────────
    dict(id=72, query="RFQ for dextrose anhydrous",                            scope="worldwide", group="K", angle="PROCUREMENT acronym",
         exp_intent="BUY", exp_product="dextrose", exp_country=None, exp_price=False, exp_results=True),
    dict(id=73, query="request for quotation refined sugar",                   scope="worldwide", group="K", angle="FORMAL PROCUREMENT phrase",
         exp_intent="BUY", exp_product="sugar",    exp_country=None, exp_price=False, exp_results=True),
    dict(id=74, query="our company requires urea fertilizer",                  scope="worldwide", group="K", angle="COMPANY REQUIRES = BUY",
         exp_intent="BUY", exp_product="urea",     exp_country=None, exp_price=False, exp_results=True),
    dict(id=75, query="we are procuring basmati rice for our operations",      scope="worldwide", group="K", angle="PROCURING verb",
         exp_intent="BUY", exp_product="basmati",  exp_country=None, exp_price=False, exp_results=True),
    dict(id=76, query="sourcing cotton yarn for our textile mill in Faisalabad",scope="worldwide", group="K", angle="SOURCING + LOCAL CITY",
         exp_intent="BUY", exp_product="cotton",   exp_country=None, exp_price=False, exp_results=True),
    dict(id=77, query="tender for wheat supply 5000 MT",                       scope="worldwide", group="K", angle="TENDER + VOLUME",
         exp_intent="BUY", exp_product="wheat",    exp_country=None, exp_price=False, exp_results=True),
    dict(id=78, query="invite quotations for palm oil",                        scope="worldwide", group="K", angle="INVITE QUOTATIONS = BUY",
         exp_intent="BUY", exp_product="palm",     exp_country=None, exp_price=False, exp_results=True),
    dict(id=79, query="seeking quotation for dextrose anhydrous 100 MT",       scope="worldwide", group="K", angle="SEEKING QUOTATION + VOLUME",
         exp_intent="BUY", exp_product="dextrose", exp_country=None, exp_price=False, exp_results=True),

    # ── GROUP L — Volume / Quantity Specific ──────────────────────────────
    dict(id=80, query="sugar 1000 MT",                         scope="worldwide", group="L", angle="BARE PRODUCT + VOLUME",
         exp_intent="BUY", exp_product="sugar",   exp_country=None, exp_price=False, exp_results=True),
    dict(id=81, query="buy 5000 MT wheat",                     scope="worldwide", group="L", angle="BUY + LARGE VOLUME",
         exp_intent="BUY", exp_product="wheat",   exp_country=None, exp_price=False, exp_results=True),
    dict(id=82, query="need 100 MT dextrose anhydrous urgently",scope="worldwide", group="L", angle="NEED + VOLUME + URGENCY",
         exp_intent="BUY", exp_product="dextrose",exp_country=None, exp_price=False, exp_results=True),
    dict(id=83, query="trial shipment basmati rice",            scope="worldwide", group="L", angle="TRIAL SHIPMENT, small qty signal",
         exp_intent="BUY", exp_product="basmati", exp_country=None, exp_price=False, exp_results=True),
    dict(id=84, query="sugar FCL",                             scope="worldwide", group="L", angle="CONTAINER LOAD abbreviation",
         exp_intent="BUY", exp_product="sugar",   exp_country=None, exp_price=False, exp_results=True),
    dict(id=85, query="bulk vessel wheat",                     scope="worldwide", group="L", angle="BULK VESSEL, very large shipment",
         exp_intent="BUY", exp_product="wheat",   exp_country=None, exp_price=False, exp_results=True),
    dict(id=86, query="sample cotton yarn",                    scope="worldwide", group="L", angle="SAMPLE = minimal quantity",
         exp_intent="BUY", exp_product="cotton",  exp_country=None, exp_price=False, exp_results=True),

    # ── GROUP M — Sector / Use-Case ───────────────────────────────────────
    dict(id=87, query="dextrose for pharmaceutical IV",          scope="worldwide", group="M", angle="PHARMA USE-CASE",
         exp_intent="BUY", exp_product="dextrose", exp_country=None, exp_price=False, exp_results=True),
    dict(id=88, query="sugar for confectionery manufacturing",   scope="worldwide", group="M", angle="FOOD INDUSTRY USE-CASE",
         exp_intent="BUY", exp_product="sugar",    exp_country=None, exp_price=False, exp_results=True),
    dict(id=89, query="wheat for flour milling",                 scope="worldwide", group="M", angle="MILLING USE-CASE",
         exp_intent="BUY", exp_product="wheat",    exp_country=None, exp_price=False, exp_results=True),
    dict(id=90, query="palm oil for biodiesel production",       scope="worldwide", group="M", angle="ENERGY USE-CASE",
         exp_intent="BUY", exp_product="palm",     exp_country=None, exp_price=False, exp_results=True),
    dict(id=91, query="cotton for yarn spinning mill",           scope="worldwide", group="M", angle="TEXTILE USE-CASE",
         exp_intent="BUY", exp_product="cotton",   exp_country=None, exp_price=False, exp_results=True),
    dict(id=92, query="urea for agricultural use",               scope="worldwide", group="M", angle="AGRICULTURE USE-CASE",
         exp_intent="BUY", exp_product="urea",     exp_country=None, exp_price=False, exp_results=True),
    dict(id=93, query="soybean for animal feed formulation",     scope="worldwide", group="M", angle="FEED INDUSTRY USE-CASE",
         exp_intent="BUY", exp_product="soybean",  exp_country=None, exp_price=False, exp_results=True),

    # ── GROUP N — Scope / Geography ───────────────────────────────────────
    dict(id=94,  query="local sugar suppliers Pakistan",      scope="pakistan",  group="N", angle="SCOPE: domestic Pakistan explicit",
         exp_intent="BUY", exp_product="sugar",   exp_country=None, exp_price=False, exp_results=None),
    dict(id=95,  query="sugar suppliers in Karachi",          scope="worldwide", group="N", angle="SCOPE: Pakistani city triggers domestic",
         exp_intent="BUY", exp_product="sugar",   exp_country=None, exp_price=False, exp_results=None),
    dict(id=96,  query="import sugar for our Karachi plant",  scope="worldwide", group="N", angle="CITY inside BUY = domestic",
         exp_intent="BUY", exp_product="sugar",   exp_country=None, exp_price=False, exp_results=None),
    dict(id=97,  query="international dextrose suppliers",    scope="worldwide", group="N", angle="SCOPE: worldwide",
         exp_intent="BUY", exp_product="dextrose",exp_country=None, exp_price=False, exp_results=None),
    dict(id=98,  query="global basmati rice suppliers",       scope="worldwide", group="N", angle="SCOPE: worldwide, global synonym",
         exp_intent="BUY", exp_product="basmati", exp_country=None, exp_price=False, exp_results=True),
    dict(id=99,  query="foreign cotton yarn suppliers",       scope="worldwide", group="N", angle="SCOPE: worldwide, foreign synonym",
         exp_intent="BUY", exp_product="cotton",  exp_country=None, exp_price=False, exp_results=None),
    dict(id=100, query="domestic wheat suppliers",            scope="pakistan",  group="N", angle="SCOPE: Pakistan, domestic synonym",
         exp_intent="BUY", exp_product="wheat",   exp_country=None, exp_price=False, exp_results=None),

    # ── GROUP O — Spelling Errors ──────────────────────────────────────────
    dict(id=101, query="suagr",                scope="worldwide", group="O", angle="TYPO: transposed → sugar",
         exp_intent="BUY", exp_product="sugar",   exp_country=None, exp_price=False, exp_results=None),
    dict(id=102, query="whaet",                scope="worldwide", group="O", angle="TYPO: transposed → wheat",
         exp_intent="BUY", exp_product="wheat",   exp_country=None, exp_price=False, exp_results=None),
    dict(id=103, query="dextroze anhydrous",   scope="worldwide", group="O", angle="TYPO: z/s swap → dextrose",
         exp_intent="BUY", exp_product="dextrose",exp_country=None, exp_price=False, exp_results=None),
    dict(id=104, query="basmati rce",          scope="worldwide", group="O", angle="TYPO: missing letter → rice",
         exp_intent="BUY", exp_product="basmati", exp_country=None, exp_price=False, exp_results=None),
    dict(id=105, query="cottan yarn",          scope="worldwide", group="O", angle="TYPO: wrong vowel → cotton",
         exp_intent="BUY", exp_product="cotton",  exp_country=None, exp_price=False, exp_results=None),
    dict(id=106, query="ureea fertilizer",     scope="worldwide", group="O", angle="TYPO: doubled vowel → urea",
         exp_intent="BUY", exp_product="urea",    exp_country=None, exp_price=False, exp_results=None),
    dict(id=107, query="palmm oil",            scope="worldwide", group="O", angle="TYPO: doubled consonant → palm oil",
         exp_intent="BUY", exp_product="palm",    exp_country=None, exp_price=False, exp_results=None),
    dict(id=108, query="soybeen",              scope="worldwide", group="O", angle="TYPO: wrong vowel → soybean",
         exp_intent="BUY", exp_product="soybean", exp_country=None, exp_price=False, exp_results=None),
    dict(id=109, query="refind sugar",         scope="worldwide", group="O", angle="TYPO: wrong suffix → refined",
         exp_intent="BUY", exp_product="sugar",   exp_country=None, exp_price=False, exp_results=None),
    dict(id=110, query="chickpeaz",            scope="worldwide", group="O", angle="TYPO: z/s swap → chickpeas",
         exp_intent="BUY", exp_product="chickpe", exp_country=None, exp_price=False, exp_results=None),
    dict(id=111, query="fructoze syrup",       scope="worldwide", group="O", angle="TYPO: z/s swap → fructose",
         exp_intent="BUY", exp_product="fructose",exp_country=None, exp_price=False, exp_results=None),
    dict(id=112, query="lactos monohydrate",   scope="worldwide", group="O", angle="TYPO: missing e → lactose",
         exp_intent="BUY", exp_product="lactose", exp_country=None, exp_price=False, exp_results=None),

    # ── GROUP P — Broken / Uneducated English ─────────────────────────────
    dict(id=113, query="sugar buying i want",              scope="worldwide", group="P", angle="REVERSED WORD ORDER, BUY",
         exp_intent="BUY", exp_product="sugar",  exp_country=None, exp_price=False, exp_results=True),
    dict(id=114, query="give me wheat cheap",              scope="worldwide", group="P", angle="IMPERATIVE + RANKING, no verb buy",
         exp_intent="BUY", exp_product="wheat",  exp_country=None, exp_price=False, exp_results=True),
    dict(id=115, query="cotton seller find me",            scope="worldwide", group="P", angle="REVERSED, find seller = BUY",
         exp_intent="BUY", exp_product="cotton", exp_country=None, exp_price=False, exp_results=True),
    dict(id=116, query="need sugar 500 ton urgent",        scope="worldwide", group="P", angle="MISSING ARTICLES + VOLUME + URGENCY",
         exp_intent="BUY", exp_product="sugar",  exp_country=None, exp_price=False, exp_results=True),
    dict(id=117, query="where buy dextrose",               scope="worldwide", group="P", angle="MISSING CAN I, bare question",
         exp_intent="BUY", exp_product="dextrose",exp_country=None, exp_price=False, exp_results=True),
    dict(id=118, query="good quality rice give me contact",scope="worldwide", group="P", angle="BROKEN PHRASE, wants supplier",
         exp_intent="BUY", exp_product="rice",   exp_country=None, exp_price=False, exp_results=True),
    dict(id=119, query="1000 ton wheat need",              scope="worldwide", group="P", angle="VOLUME FIRST, verb last",
         exp_intent="BUY", exp_product="wheat",  exp_country=None, exp_price=False, exp_results=True),
    dict(id=120, query="sugar people contact me",          scope="worldwide", group="P", angle="PEOPLE = supplier, informal",
         exp_intent="BUY", exp_product="sugar",  exp_country=None, exp_price=False, exp_results=True),
    dict(id=121, query="which country sugar comes",        scope="worldwide", group="P", angle="WRONG GRAMMAR, origin question",
         exp_intent="BUY", exp_product="sugar",  exp_country=None, exp_price=False, exp_results=True),
    dict(id=122, query="how much cost dextrose",           scope="worldwide", group="P", angle="MISSING VERB, price inquiry = BUY",
         exp_intent="BUY", exp_product="dextrose",exp_country=None, exp_price=False, exp_results=True),

    # ── GROUP Q — Super Creative / Lateral ────────────────────────────────
    dict(id=123, query="sweetener for my factory",             scope="worldwide", group="Q", angle="FUNCTION DESCRIPTION → sugar/dextrose",
         exp_intent="BUY", exp_product=None, exp_country=None, exp_price=False, exp_results=None),
    dict(id=124, query="fermentation feedstock",               scope="worldwide", group="Q", angle="INDUSTRIAL FUNCTION → glucose/molasses",
         exp_intent="BUY", exp_product=None, exp_country=None, exp_price=False, exp_results=None),
    dict(id=125, query="IV fluid ingredient",                  scope="worldwide", group="Q", angle="MEDICAL FUNCTION → dextrose anhydrous",
         exp_intent="BUY", exp_product=None, exp_country=None, exp_price=False, exp_results=None),
    dict(id=126, query="textile raw material",                 scope="worldwide", group="Q", angle="MATERIAL CATEGORY → cotton",
         exp_intent="BUY", exp_product=None, exp_country=None, exp_price=False, exp_results=None),
    dict(id=127, query="biofuel feedstock",                    scope="worldwide", group="Q", angle="ENERGY FUNCTION → molasses/palm oil",
         exp_intent="BUY", exp_product=None, exp_country=None, exp_price=False, exp_results=None),
    dict(id=128, query="bakery raw material bulk",             scope="worldwide", group="Q", angle="FOOD FUNCTION → wheat flour/sugar",
         exp_intent="BUY", exp_product=None, exp_country=None, exp_price=False, exp_results=None),
    dict(id=129, query="animal feed ingredient high protein",  scope="worldwide", group="Q", angle="FEED FUNCTION → soybean meal",
         exp_intent="BUY", exp_product=None, exp_country=None, exp_price=False, exp_results=None),
    dict(id=130, query="crop growth booster nitrogen",         scope="worldwide", group="Q", angle="AGRI FUNCTION → urea fertilizer",
         exp_intent="BUY", exp_product=None, exp_country=None, exp_price=False, exp_results=None),

    # ── GROUP R — Unrelated Language, Correct Final Meaning ──────────────
    dict(id=131, query="white gold of Pakistan",scope="worldwide", group="R", angle="METAPHOR → sugar OR cotton",
         exp_intent="BUY", exp_product=None, exp_country=None, exp_price=False, exp_results=None),
    dict(id=132, query="liquid sunshine",        scope="worldwide", group="R", angle="METAPHOR → sunflower/palm oil",
         exp_intent="BUY", exp_product=None, exp_country=None, exp_price=False, exp_results=None),
    dict(id=133, query="hospital sugar",         scope="worldwide", group="R", angle="NICKNAME → dextrose anhydrous",
         exp_intent="BUY", exp_product=None, exp_country=None, exp_price=False, exp_results=None),
    dict(id=134, query="perfumed rice",          scope="worldwide", group="R", angle="NICKNAME → basmati rice",
         exp_intent="BUY", exp_product="rice",   exp_country=None, exp_price=False, exp_results=None),
    dict(id=135, query="staff of life",          scope="worldwide", group="R", angle="IDIOM → wheat/bread flour",
         exp_intent="BUY", exp_product=None, exp_country=None, exp_price=False, exp_results=None),
    dict(id=136, query="nature's fertilizer",    scope="worldwide", group="R", angle="METAPHOR → urea/organic fertilizer",
         exp_intent="BUY", exp_product=None, exp_country=None, exp_price=False, exp_results=None),

    # ── GROUP S — Conversational / Chatbot Style ──────────────────────────
    dict(id=137, query="hi i need sugar suppliers urgently",                   scope="worldwide", group="S", angle="GREETING + BUY + URGENCY",
         exp_intent="BUY", exp_product="sugar",   exp_country=None, exp_price=False, exp_results=True),
    dict(id=138, query="can you show me top dextrose anhydrous suppliers",     scope="worldwide", group="S", angle="TOP-N + CONVERSATIONAL",
         exp_intent="BUY", exp_product="dextrose",exp_country=None, exp_price=False, exp_results=True),
    dict(id=139, query="who are the biggest wheat exporters from Russia",      scope="worldwide", group="S", angle="QUESTION FORM + COUNTRY",
         exp_intent="BUY", exp_product="wheat",   exp_country="russia", exp_price=False, exp_results=None),
    dict(id=140, query="i am a new buyer looking for basmati rice from India", scope="worldwide", group="S", angle="PERSONA + BUY + COUNTRY",
         exp_intent="BUY", exp_product="basmati", exp_country="india",  exp_price=False, exp_results=None),
    dict(id=141, query="please help me find cotton yarn under $1200",          scope="worldwide", group="S", angle="POLITE REQUEST + PRICE",
         exp_intent="BUY", exp_product="cotton",  exp_country=None, exp_price=True, exp_results=True),

    # ── GROUP T — Advanced / Technical / Multi-Spec ───────────────────────
    dict(id=142, query="dextrose anhydrous 99.5% purity USP grade from China under $700 per MT",
         scope="worldwide", group="T", angle="GRADE+PURITY+COUNTRY+PRICE+UNIT",
         exp_intent="BUY", exp_product="dextrose", exp_country="china",   exp_price=True, exp_results=None),
    dict(id=143, query="white sugar ICUMSA 45 from Brazil FOB below $400",
         scope="worldwide", group="T", angle="GRADE+TRADE TERM+COUNTRY+PRICE",
         exp_intent="BUY", exp_product="sugar",    exp_country="brazil",  exp_price=True, exp_results=None),
    dict(id=144, query="wheat HRW protein 12.5% from USA under $350 per MT",
         scope="worldwide", group="T", angle="VARIETY+SPEC+COUNTRY+PRICE",
         exp_intent="BUY", exp_product="wheat",    exp_country="usa",     exp_price=True, exp_results=None),
    dict(id=145, query="RBD palm oil RSPO certified from Malaysia below $950 per MT",
         scope="worldwide", group="T", angle="GRADE+CERTIFICATION+COUNTRY+PRICE",
         exp_intent="BUY", exp_product="palm",     exp_country="malaysia",exp_price=True, exp_results=None),
    dict(id=146, query="urea granular 46-0-0 prilled from China under $300 bulk vessel",
         scope="worldwide", group="T", angle="GRADE+NPK+FORM+COUNTRY+PRICE+VOL",
         exp_intent="BUY", exp_product="urea",     exp_country="china",   exp_price=True, exp_results=None),

    # ── GROUP U — Ambiguous Intent Edge Cases ─────────────────────────────
    dict(id=147, query="sugar export",                                scope="worldwide", group="U", angle="AMBIGUOUS: export → SELL",
         exp_intent="SELL", exp_product="sugar",  exp_country=None, exp_price=False, exp_results=True),
    dict(id=148, query="we are sugar suppliers looking for buyers",   scope="worldwide", group="U", angle="SELL: we are suppliers + find buyers",
         exp_intent="SELL", exp_product="sugar",  exp_country=None, exp_price=False, exp_results=True),
    dict(id=149, query="find someone who wants to buy our cotton",    scope="worldwide", group="U", angle="SELL: our product + find buyers",
         exp_intent="SELL", exp_product="cotton", exp_country=None, exp_price=False, exp_results=True),
    dict(id=150, query="sugar trade inquiry",                         scope="worldwide", group="U", angle="AMBIGUOUS: defaults to BUY",
         exp_intent="BUY",  exp_product="sugar",  exp_country=None, exp_price=False, exp_results=True),
]


# ---------------------------------------------------------------------------
# EXECUTION
# ---------------------------------------------------------------------------

def run_single_query(q_dict):
    """Run one query against the search API and return (q_dict, elapsed_s, response_json, error)."""
    params = {"q": q_dict["query"], "scope": q_dict["scope"]}
    t0 = time.perf_counter()
    try:
        resp = requests.get(BASE_URL, params=params, timeout=TIMEOUT)
        elapsed = round(time.perf_counter() - t0, 3)
        if resp.status_code == 200:
            return q_dict, elapsed, resp.json(), None
        else:
            return q_dict, elapsed, None, f"HTTP {resp.status_code}: {resp.text[:200]}"
    except Exception as exc:
        elapsed = round(time.perf_counter() - t0, 3)
        return q_dict, elapsed, None, str(exc)


def evaluate_correctness(q, data):
    """
    Returns a dict with per-check booleans and an overall verdict.
    Verdict: CORRECT / PARTIAL / INCORRECT / ERROR / EDGE_CASE
    """
    if data is None:
        return {"verdict": "ERROR", "checks": {}, "notes": "Request failed / timeout"}

    parsed   = data.get("parsed_query", {})
    count    = data.get("count", 0)
    results  = data.get("results", [])
    disam    = data.get("needs_disambiguation", False)

    checks = {}
    notes  = []

    # ── Intent ────────────────────────────────────────────────────────────
    if q["exp_intent"] is not None:
        actual = parsed.get("intent", "")
        checks["intent"] = actual == q["exp_intent"]
        if not checks["intent"]:
            notes.append(f"Intent: expected {q['exp_intent']}, got {actual!r}")

    # ── Product keyword ───────────────────────────────────────────────────
    if q["exp_product"] is not None:
        raw_kw = (parsed.get("product_keyword") or parsed.get("product") or "").lower().strip()
        match  = q["exp_product"].lower() in raw_kw or raw_kw in q["exp_product"].lower()
        # also check product_keyword2
        raw_kw2 = (parsed.get("product_keyword2") or "").lower().strip()
        if not match and raw_kw2:
            match = q["exp_product"].lower() in raw_kw2
        checks["product"] = match
        if not match:
            notes.append(f"Product: expected '{q['exp_product']}', got '{raw_kw}'")

    # ── Country ───────────────────────────────────────────────────────────
    if q["exp_country"] is not None:
        actual_c = (parsed.get("country") or "").lower().strip()
        # also check os_filter for country value
        os_str = json.dumps(parsed.get("os_filter", {})).lower()
        match_c = q["exp_country"].lower() in actual_c or q["exp_country"].lower() in os_str
        checks["country"] = match_c
        if not match_c:
            notes.append(f"Country: expected '{q['exp_country']}', got '{actual_c}'")

    # ── Price filter ──────────────────────────────────────────────────────
    if q["exp_price"] is not None:
        pf = parsed.get("price_filter")
        has_price = pf is not None and pf != {}
        checks["price_filter"] = has_price == q["exp_price"]
        if not checks["price_filter"]:
            if q["exp_price"]:
                notes.append(f"Price filter: expected one, got None ({pf})")
            else:
                notes.append(f"Price filter: expected none, got {pf}")

    # ── Results count ─────────────────────────────────────────────────────
    if q["exp_results"] is not None:
        if q["exp_results"]:
            checks["has_results"] = count > 0
            if not checks["has_results"]:
                notes.append("No results returned (expected some)")
        else:
            checks["has_results"] = count == 0
            if not checks["has_results"]:
                notes.append(f"Expected no results, got {count}")

    # Disambiguation note
    if disam:
        notes.append("Disambiguation triggered")

    # ── Overall verdict ───────────────────────────────────────────────────
    if not checks:
        verdict = "EDGE_CASE"
    elif all(checks.values()):
        verdict = "CORRECT"
    elif checks.get("intent", True) and sum(checks.values()) >= len(checks) * 0.6:
        verdict = "PARTIAL"
    elif not checks.get("intent", True):
        verdict = "INCORRECT"
    else:
        verdict = "PARTIAL"

    return {"verdict": verdict, "checks": checks, "notes": "; ".join(notes) if notes else ""}


def fmt_verdict(v):
    symbols = {"CORRECT": "✓ CORRECT", "PARTIAL": "~ PARTIAL",
               "INCORRECT": "✗ INCORRECT", "ERROR": "! ERROR", "EDGE_CASE": "? EDGE_CASE"}
    return symbols.get(v, v)


# ---------------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------------
def main():
    total = len(QUERIES)
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Starting {total} queries (3 at a time)...\n")

    results_store = []

    # Run 3 at a time
    batch_size = 3
    for batch_start in range(0, total, batch_size):
        batch = QUERIES[batch_start: batch_start + batch_size]
        ids   = [q["id"] for q in batch]
        print(f"  Running queries {ids}...", end=" ", flush=True)

        with ThreadPoolExecutor(max_workers=batch_size) as ex:
            futures = {ex.submit(run_single_query, q): q for q in batch}
            batch_results = {}
            for fut in as_completed(futures):
                qd, elapsed, data, err = fut.result()
                correctness = evaluate_correctness(qd, data)
                batch_results[qd["id"]] = {
                    "query_def":   qd,
                    "elapsed":     elapsed,
                    "response":    data,
                    "error":       err,
                    "correctness": correctness,
                }

        # Print inline result for this batch
        for q in batch:
            r = batch_results[q["id"]]
            v = r["correctness"]["verdict"]
            t = r["elapsed"]
            c = r["response"]["count"] if r["response"] else 0
            print(f"\n    [{q['id']:3d}] {v:12s} | {t:6.3f}s | {c:3d} results | {q['query'][:55]}", flush=True)
            results_store.append(batch_results[q["id"]])

        print()

    # -----------------------------------------------------------------------
    # Write full report
    # -----------------------------------------------------------------------
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    out_lines = []

    out_lines.append(f"# Zarailink Search Engine — Exhaustive 150-Query Test Results")
    out_lines.append(f"\n**Run date:** {now_str}  ")
    out_lines.append(f"**Total queries:** {total}  ")
    out_lines.append(f"**Endpoint:** {BASE_URL}  \n")

    # Summary stats
    verdicts = [r["correctness"]["verdict"] for r in results_store]
    correct   = verdicts.count("CORRECT")
    partial   = verdicts.count("PARTIAL")
    incorrect = verdicts.count("INCORRECT")
    edge      = verdicts.count("EDGE_CASE")
    error     = verdicts.count("ERROR")

    timings = [r["elapsed"] for r in results_store]
    avg_t   = round(sum(timings)/len(timings), 3) if timings else 0
    min_t   = round(min(timings), 3) if timings else 0
    max_t   = round(max(timings), 3) if timings else 0

    out_lines.append("## Summary Statistics\n")
    out_lines.append(f"| Metric | Value |")
    out_lines.append(f"|--------|-------|")
    out_lines.append(f"| ✓ CORRECT   | {correct} / {total} ({100*correct//total}%) |")
    out_lines.append(f"| ~ PARTIAL   | {partial} / {total} ({100*partial//total}%) |")
    out_lines.append(f"| ✗ INCORRECT | {incorrect} / {total} ({100*incorrect//total}%) |")
    out_lines.append(f"| ? EDGE_CASE | {edge} / {total} ({100*edge//total}%) |")
    out_lines.append(f"| ! ERROR     | {error} / {total} ({100*error//total}%) |")
    out_lines.append(f"| Avg response time | {avg_t}s |")
    out_lines.append(f"| Min response time | {min_t}s |")
    out_lines.append(f"| Max response time | {max_t}s |\n")

    # Group-level summary
    out_lines.append("## Group-Level Accuracy\n")
    out_lines.append("| Group | Description | Total | Correct | Partial | Incorrect | Edge/Error |")
    out_lines.append("|-------|-------------|-------|---------|---------|-----------|-----------|")
    groups = {}
    for r in results_store:
        g = r["query_def"]["group"]
        groups.setdefault(g, []).append(r["correctness"]["verdict"])
    group_desc = {
        "A": "Bare/Minimal", "B": "Basic BUY", "C": "Basic SELL",
        "D": "Find Suppliers (semantic reversal)", "E": "Find Buyers",
        "F": "Price Operators", "G": "Ranking Hints",
        "H": "Country Filters", "I": "Combined Multi-Criteria",
        "J": "HS Codes", "K": "Procurement Language",
        "L": "Volume/Quantity", "M": "Sector/Use-Case",
        "N": "Scope/Geography", "O": "Spelling Errors",
        "P": "Broken English", "Q": "Creative/Lateral",
        "R": "Metaphors", "S": "Conversational",
        "T": "Advanced/Technical", "U": "Ambiguous Intent",
    }
    for g in sorted(groups.keys()):
        vs = groups[g]
        n = len(vs)
        c = vs.count("CORRECT")
        p = vs.count("PARTIAL")
        i = vs.count("INCORRECT")
        e = vs.count("EDGE_CASE") + vs.count("ERROR")
        out_lines.append(f"| {g} | {group_desc.get(g,'')} | {n} | {c} | {p} | {i} | {e} |")

    out_lines.append("")

    # Detailed per-query results
    out_lines.append("---\n")
    out_lines.append("## Detailed Per-Query Results\n")

    current_group = None
    for r in results_store:
        qd   = r["query_def"]
        data = r["response"]
        corr = r["correctness"]
        elapsed = r["elapsed"]

        if qd["group"] != current_group:
            current_group = qd["group"]
            out_lines.append(f"\n### Group {current_group} — {group_desc.get(current_group,'')}\n")

        verdict_str = fmt_verdict(corr["verdict"])
        out_lines.append(f"#### Query #{qd['id']} — {verdict_str}")
        out_lines.append(f"**Query:** `{qd['query']}`  ")
        out_lines.append(f"**Scope:** `{qd['scope']}`  ")
        out_lines.append(f"**Angle:** {qd['angle']}  ")
        out_lines.append(f"**Time:** {elapsed}s  ")
        out_lines.append(f"**Verdict:** {verdict_str}  ")

        if r["error"]:
            out_lines.append(f"**Error:** {r['error']}  ")
        elif data:
            parsed  = data.get("parsed_query", {})
            count   = data.get("count", 0)
            snap    = data.get("market_snapshot", {}) or {}
            disam   = data.get("needs_disambiguation", False)

            out_lines.append(f"\n**Engine Parsed:**")
            out_lines.append(f"- Intent: `{parsed.get('intent','—')}`")
            out_lines.append(f"- Product keyword: `{parsed.get('product_keyword','—')}`")
            kw2 = parsed.get('product_keyword2')
            if kw2:
                out_lines.append(f"- Product keyword 2: `{kw2}`")
            out_lines.append(f"- Country: `{parsed.get('country') or '—'}`")
            pf = parsed.get('price_filter')
            out_lines.append(f"- Price filter: `{json.dumps(pf) if pf else '—'}`")
            out_lines.append(f"- Disambiguation: `{disam}`")
            out_lines.append(f"- Results count: `{count}`")
            if snap:
                out_lines.append(f"- Market snapshot: avg_price=`{snap.get('avg_price_global','—')}` top_country=`{snap.get('top_country','—')}`")

            if count > 0:
                results = data.get("results", [])
                show = results[:5]
                out_lines.append(f"\n**Top Results (up to 5 of {count}):**")
                out_lines.append("| # | Name | Country | Type | Vol (MT) | Avg Price | Shipments | Last Date | Score |")
                out_lines.append("|---|------|---------|------|----------|-----------|-----------|-----------|-------|")
                for i, res in enumerate(show, 1):
                    name = (res.get("name") or "")[:35]
                    cty  = res.get("country","")[:15]
                    typ  = res.get("type","")
                    vol  = res.get("total_volume", 0)
                    price= res.get("avg_price", 0)
                    shps = res.get("shipment_count", 0)
                    last = res.get("last_shipment_date","")
                    score= round(res.get("relevance_score", 0), 4)
                    out_lines.append(f"| {i} | {name} | {cty} | {typ} | {vol:,.2f} | {price:,.2f} | {shps} | {last} | {score} |")
            else:
                out_lines.append(f"\n*No results returned.*")

        # Correctness detail
        if corr["checks"]:
            out_lines.append(f"\n**Correctness Checks:**")
            for k, v in corr["checks"].items():
                sym = "✓" if v else "✗"
                out_lines.append(f"- {sym} {k}")
        if corr["notes"]:
            out_lines.append(f"\n**Issues:** {corr['notes']}  ")

        # Analysis
        out_lines.append(f"\n**Analysis:** ", )
        if corr["verdict"] == "CORRECT":
            out_lines.append("Engine handled this correctly — intent, product extraction, and filters all matched expectations.")
        elif corr["verdict"] == "PARTIAL":
            out_lines.append(f"Partially correct. Some expectations met but: {corr['notes'] or 'minor discrepancies'}.")
        elif corr["verdict"] == "INCORRECT":
            out_lines.append(f"Incorrect. Primary failure: {corr['notes']}.")
        elif corr["verdict"] == "EDGE_CASE":
            if data and data.get("count", 0) > 0:
                out_lines.append("Edge case query (no strict expectations) — engine returned results; inspect manually.")
            else:
                out_lines.append("Edge case query (no strict expectations) — engine returned no results, which may or may not be acceptable.")
        elif corr["verdict"] == "ERROR":
            out_lines.append("Request failed entirely.")
        out_lines.append("\n---\n")

    # Final notes
    out_lines.append("## Overall Assessment\n")
    pct_good = round(100 * (correct + partial) / total)
    out_lines.append(f"- **{correct} queries fully correct** ({100*correct//total}%), **{partial} partially correct** ({100*partial//total}%) — {pct_good}% are at minimum partially functional.")
    out_lines.append(f"- **{incorrect} queries incorrect** — intent or primary filter missed.")
    out_lines.append(f"- **{edge} edge-case queries** — no hard expectations (metaphors, creative, HS codes), manual inspection needed.")
    out_lines.append(f"- **{error} errors** — network/timeout issues if any.")
    out_lines.append(f"- **Average response time {avg_t}s** (min {min_t}s, max {max_t}s).")

    report_path = "/home/rolex/Salman Adnan/HU Files/8th Semester/FYP/Zarailink-Code/QUERY_TEST_RESULTS.md"
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("\n".join(out_lines))

    print(f"\n{'='*70}")
    print(f"SUMMARY: {correct} correct | {partial} partial | {incorrect} incorrect | {edge} edge | {error} error")
    print(f"Avg time: {avg_t}s | Min: {min_t}s | Max: {max_t}s")
    print(f"Full report written to: {report_path}")

if __name__ == "__main__":
    main()
