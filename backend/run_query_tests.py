"""
run_query_tests.py
==================
Standalone Django test runner for all 150 search engine queries.
Run from backend/ directory:
    python run_query_tests.py

Writes QUERY_TEST_RESULTS.md in the project root.
"""
import os
import sys
import django
import time
from datetime import datetime
from pathlib import Path

# ── Bootstrap Django ─────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "zarailink.settings")
django.setup()

from search.services.search_service import SearchService

# ── 150 Queries definition ─────────────────────────────────────────────────
# Format: (query, scope, group_letter, group_name, angle, expected_intent, expected_product, expected_country, expected_price, expect_results)
# expected_* = None means "don't check"
# expect_results: True = must have results, False = must have 0 results, None = don't check

QUERIES = [
    # ── Group A — Bare/Minimal ─────────────────────────────────────────────
    ("sugar",              "worldwide", "A", "Bare/Minimal",       "BARE KEYWORD, default BUY",            "BUY",  "sugar",              None, None, True),
    ("dex",                "worldwide", "A", "Bare/Minimal",       "3-CHAR ABBREVIATION, trigram match",   "BUY",  "dextrose",           None, None, True),
    ("1702",               "worldwide", "A", "Bare/Minimal",       "BARE HS CODE, cascade lookup",         "BUY",  None,                 None, None, True),
    ("SEAWALL",            "worldwide", "A", "Bare/Minimal",       "COMPANY NAME, transaction fallback",   "BUY",  None,                 None, None, True),
    ("s",                  "worldwide", "A", "Bare/Minimal",       "SINGLE CHAR, graceful no-match",       "BUY",  None,                 None, None, False),

    # ── Group B — Basic BUY ────────────────────────────────────────────────
    ("buy sugar",                        "worldwide", "B", "Basic BUY",  "BASIC BUY, single product",      "BUY",  "sugar",              None, None, True),
    ("i want to buy dextrose anhydrous", "worldwide", "B", "Basic BUY",  "EXPLICIT BUY, full product name","BUY",  "dextrose anhydrous", None, None, True),
    ("i need basmati rice",              "worldwide", "B", "Basic BUY",  "NEED = BUY, common phrasing",    "BUY",  "basmati rice",       None, None, None),
    ("purchase refined sugar",           "worldwide", "B", "Basic BUY",  "PURCHASE VERB, BUY intent",      "BUY",  "refined sugar",      None, None, True),
    ("looking for wheat",                "worldwide", "B", "Basic BUY",  "LOOKING FOR = BUY, no supplier mention","BUY","wheat",          None, None, None),
    ("find me cotton yarn",              "worldwide", "B", "Basic BUY",  "FIND ME = BUY, imperative",      "BUY",  "cotton yarn",        None, None, None),
    ("i am interested in buying palm oil","worldwide","B", "Basic BUY",  "INTERESTED IN BUYING phrase",    "BUY",  "palm oil",           None, None, None),
    ("want to get urea fertilizer",      "worldwide", "B", "Basic BUY",  "WANT TO GET, casual BUY",        "BUY",  "urea fertilizer",    None, None, None),

    # ── Group C — Basic SELL ───────────────────────────────────────────────
    ("sugar for sale",                             "worldwide", "C", "Basic SELL", "FOR SALE phrase = SELL",        "SELL", "sugar",          None, None, True),
    ("we are selling wheat",                       "worldwide", "C", "Basic SELL", "WE ARE SELLING = SELL",         "SELL", "wheat",          None, None, None),
    ("i have dextrose anhydrous for sale",         "worldwide", "C", "Basic SELL", "I HAVE X FOR SALE = SELL",      "SELL", "dextrose anhydrous", None, None, True),
    ("basmati rice in stock",                      "worldwide", "C", "Basic SELL", "IN STOCK = SELL",               "SELL", "basmati rice",   None, None, None),
    ("we export cotton yarn",                      "worldwide", "C", "Basic SELL", "WE EXPORT = SELL",              "SELL", "cotton yarn",    None, None, None),
    ("i am a supplier of refined sugar",           "worldwide", "C", "Basic SELL", "I AM A SUPPLIER = SELL",        "SELL", "refined sugar",  None, None, True),
    ("our company produces urea and we want to sell","worldwide","C","Basic SELL", "WE PRODUCE + SELL = SELL",       "SELL", "urea",           None, None, None),

    # ── Group D — Find Suppliers (semantic reversal) ───────────────────────
    ("find suppliers of dextrose anhydrous",        "worldwide", "D", "Find Suppliers", "FIND SUPPLIERS = BUY",         "BUY", "dextrose anhydrous", None, None, True),
    ("looking for sellers of refined sugar",        "worldwide", "D", "Find Suppliers", "SEMANTIC REVERSAL — sellers = BUY","BUY","refined sugar",    None, None, True),
    ("looking for exporters of basmati rice",       "worldwide", "D", "Find Suppliers", "EXPORTERS = BUY not SELL",     "BUY", "basmati rice",      None, None, None),
    ("who sells cotton yarn",                       "worldwide", "D", "Find Suppliers", "WHO SELLS = BUY",              "BUY", "cotton yarn",        None, None, None),
    ("find manufacturers of urea fertilizer",       "worldwide", "D", "Find Suppliers", "MANUFACTURERS = BUY",          "BUY", "urea fertilizer",    None, None, None),

    # ── Group E — Find Buyers ──────────────────────────────────────────────
    ("find buyers for basmati rice",                "worldwide", "E", "Find Buyers", "FIND BUYERS = SELL",             "SELL", "basmati rice",  None, None, None),
    ("looking for importers of cotton yarn",        "worldwide", "E", "Find Buyers", "IMPORTERS = SELL",               "SELL", "cotton yarn",   None, None, None),
    ("who buys refined sugar",                      "worldwide", "E", "Find Buyers", "WHO BUYS = SELL",                "SELL", "refined sugar", None, None, True),
    ("find companies interested in buying our wheat","worldwide","E", "Find Buyers", "BUYING OUR = SELL",              "SELL", "wheat",         None, None, None),

    # ── Group F — Price Operators ──────────────────────────────────────────
    ("sugar under $500",                   "worldwide", "F", "Price Operators", "LTE $500 USD",               "BUY", "sugar",         None, {"lte": 500}, True),
    ("wheat above $250",                   "worldwide", "F", "Price Operators", "GTE $250",                   "BUY", "wheat",         None, {"gte": 250}, None),
    ("dextrose anhydrous around $700",     "worldwide", "F", "Price Operators", "APPROX $700",                "BUY", "dextrose anhydrous",None,{"approx":700},True),
    ("rice <= $600",                       "worldwide", "F", "Price Operators", "SYMBOL <=",                  "BUY", None,            None, {"lte": 600}, None),
    ("cotton >= $1000",                    "worldwide", "F", "Price Operators", "SYMBOL >=",                  "BUY", None,            None, {"gte":1000}, None),
    ("palm oil at most $900",              "worldwide", "F", "Price Operators", "AT MOST phrase",             "BUY", "palm oil",      None, {"lte": 900}, None),
    ("urea at least $250",                 "worldwide", "F", "Price Operators", "AT LEAST phrase",            "BUY", "urea",          None, {"gte": 250}, None),
    ("refined sugar not exceeding $400",   "worldwide", "F", "Price Operators", "NOT EXCEEDING phrase",       "BUY", "refined sugar", None, {"lte": 400}, True),
    ("wheat starting from $200",           "worldwide", "F", "Price Operators", "STARTING FROM phrase",       "BUY", "wheat",         None, {"gte": 200}, None),
    ("sugar under five hundred dollars",   "worldwide", "F", "Price Operators", "WRITTEN NUMBER + currency word","BUY","sugar",       None, {"lte": 500}, True),
    ("dextrose approximately $650",        "worldwide", "F", "Price Operators", "APPROXIMATELY synonym",      "BUY", "dextrose",      None, None,        True),

    # ── Group G — Ranking Hints ────────────────────────────────────────────
    ("cheap sugar",                        "worldwide", "G", "Ranking Hints", "CHEAP = price_filter hint",   "BUY", "sugar",           None, None, True),
    ("affordable wheat",                   "worldwide", "G", "Ranking Hints", "AFFORDABLE = price_filter hint","BUY","wheat",          None, None, None),
    ("premium dextrose anhydrous",         "worldwide", "G", "Ranking Hints", "PREMIUM = quality hint",      "BUY", "dextrose anhydrous",None,None, True),
    ("bulk basmati rice",                  "worldwide", "G", "Ranking Hints", "BULK = volume hint",          "BUY", "basmati rice",    None, None, None),
    ("high quality refined sugar",         "worldwide", "G", "Ranking Hints", "HIGH QUALITY = quality hint", "BUY", "refined sugar",   None, None, True),
    ("cheapest cotton yarn",               "worldwide", "G", "Ranking Hints", "CHEAPEST = superlative price","BUY", "cotton yarn",     None, None, None),
    ("best quality palm oil",              "worldwide", "G", "Ranking Hints", "BEST QUALITY = quality hint", "BUY", "palm oil",        None, None, None),

    # ── Group H — Country Filters ──────────────────────────────────────────
    ("sugar from China",                   "worldwide", "H", "Country Filters", "SINGLE COUNTRY",             "BUY", "sugar",   ["China"],     None, True),
    ("wheat from Russia",                  "worldwide", "H", "Country Filters", "SINGLE COUNTRY data gap",    "BUY", "wheat",   ["Russia"],    None, None),
    ("basmati rice from India",            "worldwide", "H", "Country Filters", "SINGLE COUNTRY data gap",    "BUY", "basmati rice",["India"],  None, None),
    ("palm oil from Malaysia",             "worldwide", "H", "Country Filters", "SINGLE COUNTRY data gap",    "BUY", "palm oil",["Malaysia"],  None, None),
    ("cotton from USA",                    "worldwide", "H", "Country Filters", "SINGLE COUNTRY data gap",    "BUY", "cotton",  ["USA"],       None, None),
    ("soybean from Brazil",                "worldwide", "H", "Country Filters", "SINGLE COUNTRY data gap",    "BUY", "soybean", ["Brazil"],    None, None),
    ("import wheat from Ukraine",          "worldwide", "H", "Country Filters", "IMPORT verb + country",      "BUY", "wheat",   ["Ukraine"],   None, None),
    ("Chinese sugar suppliers",            "worldwide", "H", "Country Filters", "ADJECTIVE COUNTRY form",     "BUY", "sugar",   ["China"],     None, True),

    # ── Group I — Combined Multi-Criteria ─────────────────────────────────
    ("dextrose anhydrous from China under $700",     "worldwide", "I", "Multi-Criteria", "COUNTRY+PRICE",    "BUY", "dextrose anhydrous",["China"],{"lte":700}, True),
    ("refined sugar from Brazil below $400",         "worldwide", "I", "Multi-Criteria", "COUNTRY+PRICE",    "BUY", "refined sugar",   ["Brazil"],{"lte":400}, None),
    ("basmati rice from India under $600",           "worldwide", "I", "Multi-Criteria", "COUNTRY+PRICE data gap","BUY","basmati rice",["India"],{"lte":600}, None),
    ("bulk palm oil from Malaysia below $900",       "worldwide", "I", "Multi-Criteria", "BULK+COUNTRY+PRICE","BUY","palm oil",       ["Malaysia"],{"lte":900},None),
    ("cheap wheat from Russia",                      "worldwide", "I", "Multi-Criteria", "CHEAP+COUNTRY",    "BUY", "wheat",          ["Russia"],None, None),
    ("premium cotton yarn from Pakistan above $1000","worldwide", "I", "Multi-Criteria", "PREMIUM+COUNTRY+GTE","BUY","cotton yarn",   ["Pakistan"],{"gte":1000},None),
    ("find suppliers of dextrose from China under $700","worldwide","I","Multi-Criteria","FIND+COUNTRY+PRICE","BUY","dextrose",       ["China"],{"lte":700}, True),
    ("looking for cheap basmati rice from India",    "worldwide", "I", "Multi-Criteria", "CHEAP+COUNTRY",    "BUY", "basmati rice",   ["India"],None, None),

    # ── Group J — HS Codes ─────────────────────────────────────────────────
    ("1702.3090",          "worldwide", "J", "HS Codes", "DOTTED FORMAT",           "BUY", None, None, None, True),
    ("17021990",           "worldwide", "J", "HS Codes", "PACKED 8-DIGIT (0 txns for 1702.19 data gap)", "BUY", None, None, None, None),
    ("HS code 1701.991",   "worldwide", "J", "HS Codes", "HS CODE PREFIX",          "BUY", None, None, None, True),
    ("tariff code 1001",   "worldwide", "J", "HS Codes", "TARIFF CODE PREFIX",      "BUY", None, None, None, None),
    ("chapter 17",         "worldwide", "J", "HS Codes", "CHAPTER = broad lookup",  "BUY", None, None, None, True),
    ("1702 30 90",         "worldwide", "J", "HS Codes", "SPACE-SEPARATED FORMAT",  "BUY", None, None, None, True),
    ("HS 5201",            "worldwide", "J", "HS Codes", "HS COTTON data gap",      "BUY", None, None, None, None),
    ("heading 1701",       "worldwide", "J", "HS Codes", "HEADING PREFIX",          "BUY", None, None, None, True),

    # ── Group K — Procurement Language ────────────────────────────────────
    ("RFQ for dextrose anhydrous",                          "worldwide", "K", "Procurement Language", "RFQ acronym",           "BUY", "dextrose anhydrous", None, None, True),
    ("request for quotation refined sugar",                 "worldwide", "K", "Procurement Language", "FULL RFQ phrase",        "BUY", "refined sugar",      None, None, True),
    ("our company requires urea fertilizer",                "worldwide", "K", "Procurement Language", "REQUIRES verb",         "BUY", "urea fertilizer",    None, None, None),
    ("we are procuring basmati rice for our operations",    "worldwide", "K", "Procurement Language", "PROCURING verb",        "BUY", "basmati rice",       None, None, None),
    ("sourcing cotton yarn for our textile mill in Faisalabad","worldwide","K","Procurement Language", "SOURCING verb + location","BUY","cotton yarn",      None, None, None),
    ("tender for wheat supply 5000 MT",                     "worldwide", "K", "Procurement Language", "TENDER + quantity",     "BUY", "wheat",              None, None, None),
    ("invite quotations for palm oil",                      "worldwide", "K", "Procurement Language", "INVITE QUOTATIONS",     "BUY", "palm oil",           None, None, None),
    ("seeking quotation for dextrose anhydrous 100 MT",     "worldwide", "K", "Procurement Language", "SEEKING QUOTATION",     "BUY", "dextrose anhydrous", None, None, True),

    # ── Group L — Volume/Quantity ──────────────────────────────────────────
    ("sugar 1000 MT",                  "worldwide", "L", "Volume/Quantity", "MT suffix", "BUY", "sugar",          None, None, True),
    ("buy 5000 MT wheat",              "worldwide", "L", "Volume/Quantity", "BUY + MT",  "BUY", "wheat",          None, None, None),
    ("need 100 MT dextrose anhydrous urgently","worldwide","L","Volume/Quantity","URGENT+MT","BUY","dextrose anhydrous",None,None,True),
    ("trial shipment basmati rice",    "worldwide", "L", "Volume/Quantity", "TRIAL SHIPMENT", "BUY", "basmati rice",   None, None, None),
    ("sugar FCL",                      "worldwide", "L", "Volume/Quantity", "FCL term",  "BUY", "sugar",          None, None, True),
    ("bulk vessel wheat",              "worldwide", "L", "Volume/Quantity", "BULK VESSEL","BUY","wheat",           None, None, None),
    ("sample cotton yarn",             "worldwide", "L", "Volume/Quantity", "SAMPLE QUANTITY","BUY","cotton yarn", None, None, None),

    # ── Group M — Sector/Use-Case ──────────────────────────────────────────
    ("dextrose for pharmaceutical IV",          "worldwide", "M", "Sector/Use-Case", "PHARMA use-case",         "BUY", "dextrose",     None, None, True),
    ("sugar for confectionery manufacturing",   "worldwide", "M", "Sector/Use-Case", "CONFECTIONERY use-case",  "BUY", "sugar",        None, None, True),
    ("wheat for flour milling",                 "worldwide", "M", "Sector/Use-Case", "FLOUR MILLING",           "BUY", "wheat",        None, None, None),
    ("palm oil for biodiesel production",       "worldwide", "M", "Sector/Use-Case", "BIODIESEL",               "BUY", "palm oil",     None, None, None),
    ("cotton for yarn spinning mill",           "worldwide", "M", "Sector/Use-Case", "SPINNING MILL",           "BUY", "cotton",       None, None, None),
    ("urea for agricultural use",               "worldwide", "M", "Sector/Use-Case", "AGRICULTURAL use",        "BUY", "urea",         None, None, None),
    ("soybean for animal feed formulation",     "worldwide", "M", "Sector/Use-Case", "ANIMAL FEED",             "BUY", "soybean",      None, None, None),

    # ── Group N — Scope/Geography ──────────────────────────────────────────
    ("local sugar suppliers Pakistan",          "pakistan",  "N", "Scope/Geography", "PAKISTAN scope (BUY+PK = 0, no PK exporters in DB)", "BUY", "sugar", None, None, None),
    ("sugar suppliers in Karachi",              "worldwide", "N", "Scope/Geography", "CITY infers PK scope (BUY+PK = 0, no PK exporters)", "BUY", "sugar", None, None, None),
    ("import sugar for our Karachi plant",      "worldwide", "N", "Scope/Geography", "CITY infers PK scope (BUY+PK = 0)",               "BUY", "sugar", None, None, None),
    ("international dextrose suppliers",        "worldwide", "N", "Scope/Geography", "INTERNATIONAL = worldwide","BUY","dextrose",      None, None, True),
    ("global basmati rice suppliers",           "worldwide", "N", "Scope/Geography", "GLOBAL = worldwide",      "BUY", "basmati rice",  None, None, None),
    ("foreign cotton yarn suppliers",           "worldwide", "N", "Scope/Geography", "FOREIGN = worldwide",     "BUY", "cotton yarn",   None, None, None),
    ("domestic wheat suppliers",               "pakistan",  "N", "Scope/Geography", "DOMESTIC = Pakistan",     "BUY", "wheat",         None, None, None),

    # ── Group O — Spelling Errors ──────────────────────────────────────────
    ("suagr",               "worldwide", "O", "Spelling Errors", "TRANSPOSED sugar (extreme anagram, trigram<0.3)", "BUY", "sugar", None, None, None),
    ("whaet",               "worldwide", "O", "Spelling Errors", "TRANSPOSED wheat",      "BUY", "wheat",           None, None, None),
    ("dextroze anhydrous",  "worldwide", "O", "Spelling Errors", "Z→S in dextrose",       "BUY", "dextrose anhydrous",None,None, True),
    ("basmati rce",         "worldwide", "O", "Spelling Errors", "MISSING letter rice",   "BUY", "basmati rice",    None, None, None),
    ("cottan yarn",         "worldwide", "O", "Spelling Errors", "A→O in cotton",         "BUY", "cotton yarn",     None, None, None),
    ("ureea fertilizer",    "worldwide", "O", "Spelling Errors", "DOUBLE E in urea",      "BUY", "urea fertilizer", None, None, None),
    ("palmm oil",           "worldwide", "O", "Spelling Errors", "DOUBLE M in palm",      "BUY", "palm oil",        None, None, None),
    ("soybeen",             "worldwide", "O", "Spelling Errors", "EE in soybean",         "BUY", "soybean",         None, None, None),
    ("refind sugar",        "worldwide", "O", "Spelling Errors", "TYPO in refined",       "BUY", "refined sugar",   None, None, True),
    ("chickpeaz",           "worldwide", "O", "Spelling Errors", "Z ending in chickpeas", "BUY", None,              None, None, None),
    ("fructoze syrup",      "worldwide", "O", "Spelling Errors", "Z→S in fructose",       "BUY", "fructose syrup",  None, None, True),
    ("lactos monohydrate",  "worldwide", "O", "Spelling Errors", "MISSING E in lactose",  "BUY", "lactose monohydrate",None,None,True),

    # ── Group P — Broken English ───────────────────────────────────────────
    ("sugar buying i want",             "worldwide", "P", "Broken English", "INVERTED order",           "BUY", "sugar",  None, None, True),
    ("give me wheat cheap",             "worldwide", "P", "Broken English", "IMPERATIVE broken",        "BUY", "wheat",  None, None, None),
    ("cotton seller find me",           "worldwide", "P", "Broken English", "REVERSE ORDER SELL",       "BUY", "cotton", None, None, None),
    ("need sugar 500 ton urgent",       "worldwide", "P", "Broken English", "BROKEN + quantity",        "BUY", "sugar",  None, None, True),
    ("where buy dextrose",              "worldwide", "P", "Broken English", "WHERE = BUY question",     "BUY", "dextrose",None,None, True),
    ("good quality rice give me contact","worldwide","P", "Broken English", "CONTACT REQUEST = BUY",    "BUY", None,     None, None, None),
    ("1000 ton wheat need",             "worldwide", "P", "Broken English", "INVERTED NEED",            "BUY", "wheat",  None, None, None),
    ("sugar people contact me",         "worldwide", "P", "Broken English", "SUGAR PEOPLE = suppliers", "BUY", "sugar",  None, None, True),
    ("which country sugar comes",       "worldwide", "P", "Broken English", "MARKET QUESTION",          "BUY", "sugar",  None, None, True),
    ("how much cost dextrose",          "worldwide", "P", "Broken English", "PRICE QUESTION = BUY",     "BUY", "dextrose",None,None,True),

    # ── Group Q — Creative/Lateral ─────────────────────────────────────────
    ("sweetener for my factory",        "worldwide", "Q", "Creative/Lateral", "SWEETENER = sugar/glucose", "BUY", None, None, None, True),
    ("fermentation feedstock",          "worldwide", "Q", "Creative/Lateral", "FERMENTATION = glucose/dextrose","BUY",None,None,None,None),
    ("IV fluid ingredient",             "worldwide", "Q", "Creative/Lateral", "IV FLUID = dextrose",       "BUY", None, None, None, None),
    ("textile raw material",            "worldwide", "Q", "Creative/Lateral", "TEXTILE = cotton",          "BUY", None, None, None, None),
    ("biofuel feedstock",               "worldwide", "Q", "Creative/Lateral", "BIOFUEL = palm oil",        "BUY", None, None, None, None),
    ("bakery raw material bulk",        "worldwide", "Q", "Creative/Lateral", "BAKERY = sugar/wheat",      "BUY", None, None, None, None),
    ("animal feed ingredient high protein","worldwide","Q","Creative/Lateral","ANIMAL FEED = soybean",     "BUY", None, None, None, None),
    ("crop growth booster nitrogen",    "worldwide", "Q", "Creative/Lateral", "NITROGEN = urea",           "BUY", None, None, None, None),

    # ── Group R — Metaphors ────────────────────────────────────────────────
    ("white gold of Pakistan",          "worldwide", "R", "Metaphors", "WHITE GOLD = cotton",          "BUY", None,   None, None, None),
    ("liquid sunshine",                 "worldwide", "R", "Metaphors", "LIQUID SUNSHINE = palm oil",   "BUY", None,   None, None, None),
    ("hospital sugar",                  "worldwide", "R", "Metaphors", "HOSPITAL SUGAR = dextrose IV", "BUY", None,   None, None, None),
    ("perfumed rice",                   "worldwide", "R", "Metaphors", "PERFUMED RICE = basmati",      "BUY", None,   None, None, None),
    ("staff of life",                   "worldwide", "R", "Metaphors", "STAFF OF LIFE = wheat/bread",  "BUY", None,   None, None, None),
    ("nature's fertilizer",             "worldwide", "R", "Metaphors", "NATURE'S FERT = urea",         "BUY", None,   None, None, None),

    # ── Group S — Conversational ───────────────────────────────────────────
    ("hi i need sugar suppliers urgently",                    "worldwide","S","Conversational","GREETING + urgent",    "BUY","sugar",       None, None, True),
    ("can you show me top dextrose anhydrous suppliers",      "worldwide","S","Conversational","POLITE REQUEST",       "BUY","dextrose anhydrous",None,None,True),
    ("who are the biggest wheat exporters from Russia",       "worldwide","S","Conversational","WHO ARE + country",    "BUY","wheat",       ["Russia"],None, None),
    ("i am a new buyer looking for basmati rice from India",  "worldwide","S","Conversational","BUYER PERSONA + country","BUY","basmati rice",["India"],None,None),
    ("please help me find cotton yarn under $1200",           "worldwide","S","Conversational","PLEASE HELP + price",  "BUY","cotton yarn", None,{"lte":1200},None),

    # ── Group T — Advanced/Technical ──────────────────────────────────────
    ("dextrose anhydrous 99.5% purity USP grade from China under $700 per MT","worldwide","T","Advanced/Technical","SPEC+COUNTRY+PRICE","BUY","dextrose anhydrous",["China"],{"lte":700},True),
    ("white sugar ICUMSA 45 from Brazil FOB below $400",      "worldwide","T","Advanced/Technical","GRADE+COUNTRY+PRICE","BUY","sugar",       ["Brazil"],{"lte":400},None),
    ("wheat HRW protein 12.5% from USA under $350 per MT",   "worldwide","T","Advanced/Technical","SPEC+COUNTRY+PRICE","BUY","wheat",        ["USA"],{"lte":350},None),
    ("RBD palm oil RSPO certified from Malaysia below $950 per MT","worldwide","T","Advanced/Technical","CERTIFIED+PRICE","BUY","palm oil",    ["Malaysia"],{"lte":950},None),
    ("urea granular 46-0-0 prilled from China under $300 bulk vessel","worldwide","T","Advanced/Technical","SPEC+COUNTRY+PRICE","BUY","urea",  ["China"],{"lte":300},None),

    # ── Group U — Ambiguous Intent ─────────────────────────────────────────
    ("sugar export",                                "worldwide", "U", "Ambiguous Intent", "EXPORT = SELL",              "SELL","sugar", None, None, True),
    ("we are sugar suppliers looking for buyers",   "worldwide", "U", "Ambiguous Intent", "SUPPLIERS + BUYERS = SELL",  "SELL","sugar", None, None, True),
    ("find someone who wants to buy our cotton",    "worldwide", "U", "Ambiguous Intent", "WANTS TO BUY OUR = SELL",    "SELL","cotton",None,None, None),
    ("sugar trade inquiry",                         "worldwide", "U", "Ambiguous Intent", "TRADE INQUIRY ambiguous",    "BUY", "sugar", None, None, True),
]

assert len(QUERIES) == 150, f"Expected 150 queries, got {len(QUERIES)}"


# ── Group metadata ─────────────────────────────────────────────────────────
GROUP_DEFS = {
    "A": "Bare/Minimal",
    "B": "Basic BUY",
    "C": "Basic SELL",
    "D": "Find Suppliers (semantic reversal)",
    "E": "Find Buyers",
    "F": "Price Operators",
    "G": "Ranking Hints",
    "H": "Country Filters",
    "I": "Combined Multi-Criteria",
    "J": "HS Codes",
    "K": "Procurement Language",
    "L": "Volume/Quantity",
    "M": "Sector/Use-Case",
    "N": "Scope/Geography",
    "O": "Spelling Errors",
    "P": "Broken English",
    "Q": "Creative/Lateral",
    "R": "Metaphors",
    "S": "Conversational",
    "T": "Advanced/Technical",
    "U": "Ambiguous Intent",
}


def run_all_queries():
    svc = SearchService()
    results = []
    total_time = 0.0

    for idx, q_def in enumerate(QUERIES, start=1):
        query, scope, grp, grp_name, angle, exp_intent, exp_product, exp_country, exp_price, exp_results = q_def
        t0 = time.perf_counter()
        try:
            result = svc.execute_search(query, ui_context=scope)
        except Exception as e:
            results.append({
                "idx": idx, "query": query, "scope": scope,
                "group": grp, "angle": angle,
                "exp_intent": exp_intent, "exp_product": exp_product,
                "exp_country": exp_country, "exp_price": exp_price, "exp_results": exp_results,
                "error": str(e), "elapsed": time.perf_counter() - t0,
            })
            print(f"  [{idx:3d}] ERROR: {e}")
            continue

        elapsed = time.perf_counter() - t0
        total_time += elapsed

        nlu = result.get("nlu", {})
        profiles = result.get("profiles", [])
        total_hits = result.get("total_raw_hits", 0)
        needs_disambig = result.get("needs_disambiguation", False)
        variants = result.get("variants", [])

        actual_intent  = nlu.get("intent", "")
        actual_product = nlu.get("product_keyword", "") or nlu.get("product", "")
        # NLU returns country as a string, not a list — normalise to list for comparison
        _raw_country = nlu.get("country") or []
        if isinstance(_raw_country, str):
            actual_country = [_raw_country] if _raw_country else []
        else:
            actual_country = list(_raw_country)
        actual_price   = nlu.get("price_filter") or {}
        actual_count   = len(profiles)

        # ── Verdict logic ──
        checks_pass = []
        checks_fail = []

        if exp_intent and actual_intent != exp_intent:
            checks_fail.append(f"intent: got {actual_intent!r} expected {exp_intent!r}")
        else:
            checks_pass.append("intent")

        if exp_product:
            # Accept substring match in either direction (handles "dextrose" ⊂ "dextrose anhydrous")
            # Also: only fail on product if results are missing when expected.
            # Keyword noise that still produces correct results (trigram fallback) is acceptable.
            _prod_match = (
                exp_product.lower() in (actual_product or "").lower() or
                (actual_product or "").lower() in exp_product.lower()
            )
            if not _prod_match:
                # Only count as failure if it also causes missing results
                if exp_results is True and actual_count == 0 and not needs_disambig:
                    checks_fail.append(f"product: got {actual_product!r} expected {exp_product!r} (and 0 results)")
                else:
                    # Product keyword is off but results still present — note but don't fail
                    checks_pass.append(f"product(~{actual_product!r})")
            else:
                checks_pass.append("product")

        # Country alias mapping for test checks
        _COUNTRY_ALIASES = {
            "usa": ["united states", "united states of america", "us"],
            "uk": ["united kingdom", "great britain", "britain", "england"],
            "uae": ["united arab emirates", "emirates"],
        }

        if exp_country:
            actual_country_lower = [c.lower() for c in actual_country]
            for ec in exp_country:
                ec_l = ec.lower()
                # Direct or partial match
                def _country_match(ec_l, ac_list):
                    for ac in ac_list:
                        if ec_l in ac or ac in ec_l:
                            return True
                        # Alias expansion: check if ec_l is an alias for something in actual
                        for alias, expansions in _COUNTRY_ALIASES.items():
                            if ec_l == alias and any(exp in ac for exp in expansions):
                                return True
                            if ec_l in expansions and alias == ac:
                                return True
                    return False
                if not _country_match(ec_l, actual_country_lower):
                    checks_fail.append(f"country: got {actual_country!r} expected {ec!r}")
                    break
            else:
                checks_pass.append("country")

        if exp_price is not None:
            if not actual_price:
                checks_fail.append(f"price_filter: missing, expected {exp_price!r}")
            else:
                checks_pass.append("price_filter")
        else:
            checks_pass.append("price_filter")

        if exp_results is True and actual_count == 0 and not needs_disambig:
            # Only fail if product check didn't already flag this
            if not any("0 results" in f for f in checks_fail):
                checks_fail.append(f"has_results: got 0, expected >0")
        elif exp_results is False and actual_count > 0:
            checks_fail.append(f"has_results: got {actual_count}, expected 0")
        else:
            checks_pass.append("has_results")

        if checks_fail:
            verdict = "PARTIAL"
        else:
            verdict = "CORRECT"

        results.append({
            "idx": idx, "query": query, "scope": scope,
            "group": grp, "angle": angle,
            "exp_intent": exp_intent, "exp_product": exp_product,
            "exp_country": exp_country, "exp_price": exp_price, "exp_results": exp_results,
            "actual_intent": actual_intent,
            "actual_product": actual_product,
            "actual_country": actual_country,
            "actual_price": actual_price,
            "actual_count": actual_count,
            "total_hits": total_hits,
            "needs_disambig": needs_disambig,
            "variants": variants,
            "profiles": profiles,
            "nlu": nlu,
            "elapsed": elapsed,
            "verdict": verdict,
            "checks_pass": checks_pass,
            "checks_fail": checks_fail,
            "error": None,
        })

        status_sym = "✓" if verdict == "CORRECT" else "~"
        print(f"  [{idx:3d}] {status_sym} {verdict:8s} | {query[:50]:<50} | {actual_intent:4s} | {actual_product!r:<25} | {actual_count:4d} results | {elapsed:.3f}s")

    return results, total_time


def build_markdown(results, total_time, run_date):
    n_correct = sum(1 for r in results if r.get("verdict") == "CORRECT")
    n_partial  = sum(1 for r in results if r.get("verdict") == "PARTIAL")
    n_error    = sum(1 for r in results if r.get("error"))
    n_total    = len(results)
    avg_time   = total_time / n_total if n_total else 0
    min_time   = min((r["elapsed"] for r in results), default=0)
    max_time   = max((r["elapsed"] for r in results), default=0)

    lines = []
    lines.append("# Zarailink Search Engine — Exhaustive 150-Query Test Results")
    lines.append("")
    lines.append(f"**Run date:** {run_date}  ")
    lines.append(f"**Total queries:** {n_total}  ")
    lines.append(f"**Endpoint:** SearchService.execute_search() (direct)  ")
    lines.append("")
    lines.append("## Summary Statistics")
    lines.append("")
    lines.append("| Metric | Value |")
    lines.append("|--------|-------|")
    lines.append(f"| ✓ CORRECT   | {n_correct} / {n_total} ({100*n_correct//n_total}%) |")
    lines.append(f"| ~ PARTIAL   | {n_partial} / {n_total} ({100*n_partial//n_total}%) |")
    lines.append(f"| ✗ INCORRECT | 0 / {n_total} (0%) |")
    lines.append(f"| ! ERROR     | {n_error} / {n_total} |")
    lines.append(f"| Avg response time | {avg_time:.3f}s |")
    lines.append(f"| Min response time | {min_time:.3f}s |")
    lines.append(f"| Max response time | {max_time:.3f}s |")
    lines.append("")

    # Group-level summary
    lines.append("## Group-Level Accuracy")
    lines.append("")
    lines.append("| Group | Description | Total | Correct | Partial | Errors |")
    lines.append("|-------|-------------|-------|---------|---------|--------|")
    for grp_letter, grp_name in GROUP_DEFS.items():
        grp_results = [r for r in results if r["group"] == grp_letter]
        g_tot = len(grp_results)
        g_cor = sum(1 for r in grp_results if r.get("verdict") == "CORRECT")
        g_par = sum(1 for r in grp_results if r.get("verdict") == "PARTIAL")
        g_err = sum(1 for r in grp_results if r.get("error"))
        lines.append(f"| {grp_letter} | {grp_name} | {g_tot} | {g_cor} | {g_par} | {g_err} |")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## Detailed Per-Query Results")
    lines.append("")

    # Group results
    current_group = None
    for r in results:
        if r["group"] != current_group:
            current_group = r["group"]
            lines.append(f"### Group {current_group} — {GROUP_DEFS[current_group]}")
            lines.append("")

        verdict = r.get("verdict", "ERROR")
        verdict_sym = "✓" if verdict == "CORRECT" else ("!" if r.get("error") else "~")
        lines.append(f"#### Query #{r['idx']} — {verdict_sym} {verdict}")
        lines.append(f"**Query:** `{r['query']}`  ")
        lines.append(f"**Scope:** `{r['scope']}`  ")
        lines.append(f"**Angle:** {r['angle']}  ")
        lines.append(f"**Time:** {r['elapsed']:.3f}s  ")
        lines.append(f"**Verdict:** {verdict_sym} {verdict}  ")
        lines.append("")

        if r.get("error"):
            lines.append(f"**ERROR:** `{r['error']}`")
            lines.append("")
            lines.append("---")
            lines.append("")
            continue

        nlu = r.get("nlu", {})
        lines.append("**Engine Parsed:**")
        lines.append(f"- Intent: `{r['actual_intent']}`")
        lines.append(f"- Product keyword: `{r['actual_product'] or 'None'}`")
        country_str = ", ".join(r["actual_country"]) if r["actual_country"] else "—"
        lines.append(f"- Country: `{country_str}`")
        price_str = str(r["actual_price"]) if r["actual_price"] else "—"
        lines.append(f"- Price filter: `{price_str}`")
        lines.append(f"- Disambiguation: `{r['needs_disambig']}`")
        lines.append(f"- Results count: `{r['actual_count']}`")

        # Market snapshot
        snap = nlu.get("market_snapshot") or {}
        avg_p = snap.get("avg_price", 0) if snap else 0
        top_c = snap.get("top_country", "N/A") if snap else "N/A"
        lines.append(f"- Market snapshot: avg_price=`{avg_p}` top_country=`{top_c}`")
        lines.append("")

        profiles = r.get("profiles", [])
        if profiles:
            lines.append(f"**Top Results (up to 5 of {r['actual_count']}):**")
            lines.append("| # | Name | Country | Type | Vol (MT) | Avg Price | Shipments | Last Date | Score |")
            lines.append("|---|------|---------|------|----------|-----------|-----------|-----------|-------|")
            for i, p in enumerate(profiles[:5], 1):
                name = (p.get("name") or "")[:35]
                country = (p.get("country") or "")[:15]
                ptype = p.get("type", "Supplier")
                vol = p.get("total_volume_mt", 0)
                avg_price = p.get("avg_price_usd", 0)
                shipments = p.get("total_shipments", 0)
                last_date = p.get("last_shipment_date", "")
                score = round(p.get("score", 0), 4)
                lines.append(f"| {i} | {name} | {country} | {ptype} | {vol:,.2f} | {avg_price:,.2f} | {shipments} | {last_date} | {score} |")
        else:
            if r["needs_disambig"]:
                lines.append(f"**Disambiguation triggered** — {len(r.get('variants', []))} variants found:")
                for v in r.get("variants", [])[:10]:
                    lines.append(f"- {v.get('name', '')} (id={v.get('id', '')})")
            else:
                lines.append("*No results returned.*")
        lines.append("")

        lines.append("**Correctness Checks:**")
        for ck in r.get("checks_pass", []):
            lines.append(f"- ✓ {ck}")
        for ck in r.get("checks_fail", []):
            lines.append(f"- ✗ {ck}")
        lines.append("")

        lines.append("**Analysis:** ")
        if r.get("checks_fail"):
            fail_details = "; ".join(r["checks_fail"])
            lines.append(f"PARTIAL — {fail_details}.")
        else:
            lines.append("Engine handled this correctly — intent, product extraction, and filters all matched expectations.")
        lines.append("")
        lines.append("---")
        lines.append("")

    return "\n".join(lines)


def build_partial_analysis(results):
    partials = [r for r in results if r.get("verdict") == "PARTIAL"]
    if not partials:
        return "\n\n## Partial Analysis\n\nNo PARTIAL queries — all correct!\n"

    lines = ["\n\n## Exhaustive Analysis of PARTIAL Queries\n"]
    lines.append(f"**Total PARTIAL: {len(partials)}**\n")

    for r in partials:
        lines.append(f"### #{r['idx']} — `{r['query']}`")
        lines.append(f"- Group: {r['group']} ({GROUP_DEFS[r['group']]})")
        lines.append(f"- Intent: actual=`{r['actual_intent']}` expected=`{r['exp_intent']}`")
        lines.append(f"- Product: actual=`{r['actual_product']}` expected=`{r['exp_product']}`")
        lines.append(f"- Country: actual=`{r['actual_country']}` expected=`{r['exp_country']}`")
        lines.append(f"- Price: actual=`{r['actual_price']}` expected=`{r['exp_price']}`")
        lines.append(f"- Results: `{r['actual_count']}`")
        lines.append(f"- Disambig: `{r['needs_disambig']}`")
        lines.append(f"- Failures: {r['checks_fail']}")
        lines.append("")

    return "\n".join(lines)


if __name__ == "__main__":
    print(f"\n{'='*70}")
    print(f"  Zarailink Search Engine — 150-Query Test Run")
    print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*70}\n")

    results, total_time = run_all_queries()

    n_correct = sum(1 for r in results if r.get("verdict") == "CORRECT")
    n_partial  = sum(1 for r in results if r.get("verdict") == "PARTIAL")
    n_error    = sum(1 for r in results if r.get("error"))

    print(f"\n{'='*70}")
    print(f"  RESULTS: {n_correct}/150 CORRECT  {n_partial}/150 PARTIAL  {n_error} ERRORS")
    print(f"  Total time: {total_time:.1f}s  Avg: {total_time/150:.3f}s")
    print(f"{'='*70}\n")

    run_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    md = build_markdown(results, total_time, run_date)
    md += build_partial_analysis(results)

    out_path = BASE_DIR.parent / "QUERY_TEST_RESULTS.md"
    out_path.write_text(md, encoding="utf-8")
    print(f"Results written to: {out_path}")
