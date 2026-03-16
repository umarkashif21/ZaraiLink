"""
backend/training_scripts/generate_embedding_pairs.py

Phase 4-C: Generate (query, positive_document, negative_document) triplets
for fine-tuning nomic-embed-text-v1 on Zarailink trade domain.

Strategy:
  Positive: query → matching subcategory name / product description
  Hard negative: query → near-miss subcategory (same parent category, different product)
  In-batch negatives: handled by the trainer itself

Output: backend/training_data/embedding_pairs.jsonl
Format per line:
  {"query": "...", "positive": "...", "negative": "..."}

  OR (if no hard negative available):
  {"query": "...", "positive": "..."}

Usage:
    cd backend
    python training_scripts/generate_embedding_pairs.py
"""

import os
import sys
import json
import random
import logging

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BACKEND_DIR)

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')

OUTPUT_PATH = os.path.join(BACKEND_DIR, 'training_data', 'embedding_pairs.jsonl')
RANDOM_SEED = 42


# ── Static query → product mapping (no DB needed) ────────────────────────────
# Each entry: query string → canonical product document (as it would appear in
# a nomic-embed search_document: context).

QUERY_POSITIVE_PAIRS = [
    # Dextrose / Glucose
    ("find dextrose suppliers",
     "Dextrose Anhydrous - pharmaceutical grade glucose sugar used in food, pharma, and fermentation industries"),
    ("who sells dextrose anhydrous",
     "Dextrose Anhydrous - pharmaceutical grade glucose sugar used in food, pharma, and fermentation industries"),
    ("dextrose anhydrous importers",
     "Dextrose Anhydrous - pharmaceutical grade glucose sugar used in food, pharma, and fermentation industries"),
    ("source pharmaceutical glucose",
     "Pharmaceutical Glucose - high-purity dextrose monohydrate for IV solutions and drug manufacturing"),
    ("glucose syrup suppliers",
     "Glucose Syrup - liquid sweetener derived from starch hydrolysis, used in confectionery and baking"),
    ("buy glucose syrup from China",
     "Glucose Syrup - liquid sweetener derived from starch hydrolysis, used in confectionery and baking"),

    # Sugar
    ("find sugar importers",
     "White Refined Sugar - sucrose extracted from sugarcane or beet, ICUMSA 45 grade for food industry"),
    ("who imports sugar",
     "White Refined Sugar - sucrose extracted from sugarcane or beet, ICUMSA 45 grade for food industry"),
    ("sugar cane suppliers from Brazil",
     "Raw Cane Sugar - minimally processed sugar from sugarcane, used as feedstock for refineries"),
    ("sucrose exporters worldwide",
     "White Refined Sugar - sucrose extracted from sugarcane or beet, ICUMSA 45 grade for food industry"),

    # Cotton
    ("find cotton suppliers",
     "Raw Cotton - natural textile fiber harvested from cotton bolls, used in yarn and fabric manufacturing"),
    ("buy cotton from China",
     "Raw Cotton - natural textile fiber harvested from cotton bolls, used in yarn and fabric manufacturing"),
    ("find buyers for our cotton",
     "Cotton Fiber - cleaned and ginned cotton staple fiber for spinning mills"),

    # Wheat / Wheat Flour
    ("wheat flour suppliers from India",
     "Wheat Flour - milled wheat grain product used in bakery, pasta, and food processing"),
    ("looking for wheat suppliers",
     "Wheat Grain - whole wheat used for milling, animal feed, and starch extraction"),
    ("import maize starch to Pakistan",
     "Maize Starch (Corn Starch) - extracted from corn kernels, used as thickener in food and pharma"),

    # Lactose
    ("need lactose supplier",
     "Lactose Monohydrate - milk sugar disaccharide used in pharmaceutical excipient and infant formula"),
    ("lactose monohydrate exporters worldwide",
     "Lactose Monohydrate - milk sugar disaccharide used in pharmaceutical excipient and infant formula"),
    ("lactose anhydrous suppliers",
     "Lactose Anhydrous - water-free form of milk sugar used in direct-compression tablet manufacturing"),

    # Palm Oil
    ("palm oil suppliers Malaysia",
     "Crude Palm Oil (CPO) - vegetable oil from oil palm fruit, used in food processing and oleochemicals"),
    ("source refined palm oil",
     "Refined Bleached Deodorized Palm Oil (RBD) - processed palm oil for edible use"),
    ("palm kernel oil exporters",
     "Palm Kernel Oil - oil extracted from palm seed kernel, used in soap and detergent manufacturing"),

    # Citric Acid
    ("citric acid suppliers from Europe",
     "Citric Acid Anhydrous - organic acid used as food preservative, flavoring, and cleaning agent"),
    ("buy citric acid below $1500",
     "Citric Acid Anhydrous - organic acid used as food preservative, flavoring, and cleaning agent"),

    # Starch variants
    ("tapioca starch suppliers",
     "Tapioca Starch - cassava-derived starch used in food thickening and industrial adhesives"),
    ("rice starch exporters",
     "Rice Starch - fine-grain starch from rice, used in cosmetics, baby food, and paper coating"),
    ("potato starch buyers",
     "Potato Starch - starch extracted from potatoes, used in food and industrial applications"),

    # Whey / Casein
    ("buy whey protein concentrate",
     "Whey Protein Concentrate (WPC 80) - dairy by-product protein supplement for sports nutrition"),
    ("casein protein suppliers",
     "Micellar Casein - slow-digesting dairy protein used in nutrition supplements and cheese production"),

    # Gums / Hydrocolloids
    ("xanthan gum suppliers",
     "Xanthan Gum - microbial polysaccharide used as food thickener and stabilizer"),
    ("guar gum from India",
     "Guar Gum - natural galactomannan polysaccharide from guar bean, used in food and drilling fluids"),
    ("carrageenan from Philippines",
     "Carrageenan - seaweed-derived hydrocolloid used as food gelling and thickening agent"),

    # Oils
    ("sunflower oil suppliers",
     "Refined Sunflower Oil - edible vegetable oil from sunflower seeds, used for cooking and frying"),
    ("canola oil importers",
     "Canola Oil - low erucic acid rapeseed oil used for cooking and food processing"),
    ("soy lecithin suppliers",
     "Soy Lecithin - phospholipid emulsifier derived from soybeans, used in food and pharma"),

    # Sodium Chloride
    ("sodium chloride exporters from China",
     "Sodium Chloride (Industrial Salt) - used in chemical production, water treatment, and food processing"),

    # Calcium carbonate
    ("calcium carbonate suppliers from China",
     "Calcium Carbonate - mineral filler and coating pigment used in paper, plastics, and construction"),

    # Sorbitol / Maltodextrin / Pectin
    ("sorbitol suppliers",
     "Sorbitol - sugar alcohol used as humectant, sweetener, and excipient in pharma and food"),
    ("maltodextrin priced under $500",
     "Maltodextrin - partially hydrolyzed starch used as food additive, carrier, and bulking agent"),
    ("pectin suppliers",
     "Pectin - natural polysaccharide from citrus peel used as gelling agent in jams and confectionery"),

    # Vitamin C
    ("vitamin C suppliers",
     "Ascorbic Acid (Vitamin C) - antioxidant used as food preservative and nutritional supplement"),

    # F5 / F6 / F7 / F8 context queries
    ("top 5 dextrose anhydrous suppliers",
     "Dextrose Anhydrous - pharmaceutical grade glucose sugar used in food, pharma, and fermentation industries"),
    ("Q1 2024 palm oil exporters",
     "Crude Palm Oil (CPO) - vegetable oil from oil palm fruit, used in food processing and oleochemicals"),
    ("which countries import most sugar",
     "White Refined Sugar - sucrose extracted from sugarcane or beet, ICUMSA 45 grade for food industry"),
    ("has Nestle purchased palm oil",
     "Crude Palm Oil (CPO) - vegetable oil from oil palm fruit, used in food processing and oleochemicals"),
    ("200 MT lactose monohydrate suppliers",
     "Lactose Monohydrate - milk sugar disaccharide used in pharmaceutical excipient and infant formula"),
]


# ── Product documents for building hard negatives ────────────────────────────
# When a query is about product A, a hard negative is product B (same category).

PRODUCT_DOCUMENTS = [
    "Dextrose Anhydrous - pharmaceutical grade glucose sugar used in food, pharma, and fermentation industries",
    "Pharmaceutical Glucose - high-purity dextrose monohydrate for IV solutions and drug manufacturing",
    "Glucose Syrup - liquid sweetener derived from starch hydrolysis, used in confectionery and baking",
    "White Refined Sugar - sucrose extracted from sugarcane or beet, ICUMSA 45 grade for food industry",
    "Raw Cane Sugar - minimally processed sugar from sugarcane, used as feedstock for refineries",
    "Lactose Monohydrate - milk sugar disaccharide used in pharmaceutical excipient and infant formula",
    "Lactose Anhydrous - water-free form of milk sugar used in direct-compression tablet manufacturing",
    "Crude Palm Oil (CPO) - vegetable oil from oil palm fruit, used in food processing and oleochemicals",
    "Refined Bleached Deodorized Palm Oil (RBD) - processed palm oil for edible use",
    "Palm Kernel Oil - oil extracted from palm seed kernel, used in soap and detergent manufacturing",
    "Citric Acid Anhydrous - organic acid used as food preservative, flavoring, and cleaning agent",
    "Raw Cotton - natural textile fiber harvested from cotton bolls, used in yarn and fabric manufacturing",
    "Wheat Flour - milled wheat grain product used in bakery, pasta, and food processing",
    "Wheat Grain - whole wheat used for milling, animal feed, and starch extraction",
    "Maize Starch (Corn Starch) - extracted from corn kernels, used as thickener in food and pharma",
    "Tapioca Starch - cassava-derived starch used in food thickening and industrial adhesives",
    "Rice Starch - fine-grain starch from rice, used in cosmetics, baby food, and paper coating",
    "Xanthan Gum - microbial polysaccharide used as food thickener and stabilizer",
    "Guar Gum - natural galactomannan polysaccharide from guar bean, used in food and drilling fluids",
    "Refined Sunflower Oil - edible vegetable oil from sunflower seeds, used for cooking and frying",
    "Canola Oil - low erucic acid rapeseed oil used for cooking and food processing",
    "Soy Lecithin - phospholipid emulsifier derived from soybeans, used in food and pharma",
    "Sodium Chloride (Industrial Salt) - used in chemical production, water treatment, and food processing",
    "Calcium Carbonate - mineral filler and coating pigment used in paper, plastics, and construction",
    "Sorbitol - sugar alcohol used as humectant, sweetener, and excipient in pharma and food",
    "Maltodextrin - partially hydrolyzed starch used as food additive, carrier, and bulking agent",
    "Pectin - natural polysaccharide from citrus peel used as gelling agent in jams and confectionery",
    "Whey Protein Concentrate (WPC 80) - dairy by-product protein supplement for sports nutrition",
    "Micellar Casein - slow-digesting dairy protein used in nutrition supplements and cheese production",
    "Carrageenan - seaweed-derived hydrocolloid used as food gelling and thickening agent",
    "Ascorbic Acid (Vitamin C) - antioxidant used as food preservative and nutritional supplement",
]

PRODUCT_DOCS_SET = set(PRODUCT_DOCUMENTS)


def _pick_hard_negative(positive: str, rng: random.Random) -> str:
    """Pick a product document that is NOT the positive."""
    candidates = [d for d in PRODUCT_DOCUMENTS if d != positive]
    return rng.choice(candidates)


def run():
    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    rng = random.Random(RANDOM_SEED)

    pairs = []
    for query, positive in QUERY_POSITIVE_PAIRS:
        neg = _pick_hard_negative(positive, rng)
        pairs.append({
            "query": f"search_query: {query}",
            "positive": f"search_document: {positive}",
            "negative": f"search_document: {neg}",
        })

    with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
        for p in pairs:
            f.write(json.dumps(p, ensure_ascii=False) + '\n')

    logger.info(f"Wrote {len(pairs)} triplets to {OUTPUT_PATH}")
    return pairs


if __name__ == '__main__':
    run()
