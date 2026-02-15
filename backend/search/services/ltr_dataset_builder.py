import numpy as np
import pandas as pd
from trade_data.models import ProductSubCategory, Transaction
from .aggregation import SupplierAggregator
from .ranking_ltr import FeatureExtractor, FAMILY_WEIGHTS, DEFAULT_WEIGHTS


def _percentile_to_label(p):
    """Convert percentile rank to 0-4 relevance label."""
    if p > 0.8: return 4
    if p > 0.6: return 3
    if p > 0.4: return 2
    if p > 0.2: return 1
    return 0


class LTRDatasetBuilder:
    """
    Builds a synthetic dataset for LTR training from historical transactions.
    """
    def build_dataset(self):
        """
        Generates X (features), y (labels), group (query boundaries).
        """
        subcats = ProductSubCategory.objects.all()
        aggregator = SupplierAggregator()
        extractor = FeatureExtractor()

        all_features = []
        all_labels = []
        groups = []

        for subcat in subcats:
            has_imports = Transaction.objects.filter(product_item__sub_category=subcat, trade_type='IMPORT').exists()
            has_exports = Transaction.objects.filter(product_item__sub_category=subcat, trade_type='EXPORT').exists()

            if not has_imports and not has_exports:
                continue

            # Generate Synthetic Queries for all families and intent/scope combos
            queries = []

            if has_imports:
                # BUY + WORLDWIDE (IMPORT data)
                queries.append({
                    "intent": "BUY", "family": 1, "product": subcat.name, "product_id": subcat.id, "scope": "WORLDWIDE"
                })
                queries.append({
                    "intent": "BUY", "family": 2, "product": subcat.name, "product_id": subcat.id, "scope": "WORLDWIDE",
                    "country_filter": ["China"]
                })
                queries.append({
                    "intent": "BUY", "family": 3, "product": subcat.name, "product_id": subcat.id, "scope": "WORLDWIDE",
                    "volume_mt": 100
                })
                queries.append({
                    "intent": "BUY", "family": 4, "product": subcat.name, "product_id": subcat.id, "scope": "WORLDWIDE",
                    "price_ceiling": 1000
                })
                queries.append({
                    "intent": "BUY", "family": 5, "product": subcat.name, "product_id": subcat.id, "scope": "WORLDWIDE",
                    "time_range": "last 6 months"
                })
                queries.append({
                    "intent": "BUY", "family": 6, "product": subcat.name, "product_id": subcat.id, "scope": "WORLDWIDE"
                })
                queries.append({
                    "intent": "BUY", "family": 7, "product": subcat.name, "product_id": subcat.id, "scope": "WORLDWIDE"
                })
                queries.append({
                    "intent": "BUY", "family": 8, "product": subcat.name, "product_id": subcat.id, "scope": "WORLDWIDE"
                })
                # SELL + PAKISTAN (IMPORT data — Pakistani buyers importing locally)
                queries.append({
                    "intent": "SELL", "family": 1, "product": subcat.name, "product_id": subcat.id, "scope": "PAKISTAN"
                })

            if has_exports:
                # SELL + WORLDWIDE (EXPORT data — find foreign buyers)
                queries.append({
                    "intent": "SELL", "family": 1, "product": subcat.name, "product_id": subcat.id, "scope": "WORLDWIDE"
                })
                queries.append({
                    "intent": "SELL", "family": 3, "product": subcat.name, "product_id": subcat.id, "scope": "WORLDWIDE",
                    "volume_mt": 100
                })
                queries.append({
                    "intent": "SELL", "family": 4, "product": subcat.name, "product_id": subcat.id, "scope": "WORLDWIDE",
                    "price_floor": 500
                })
                queries.append({
                    "intent": "SELL", "family": 6, "product": subcat.name, "product_id": subcat.id, "scope": "WORLDWIDE"
                })
                # BUY + PAKISTAN (EXPORT data — Pakistani suppliers)
                queries.append({
                    "intent": "BUY", "family": 1, "product": subcat.name, "product_id": subcat.id, "scope": "PAKISTAN"
                })
                queries.append({
                    "intent": "BUY", "family": 3, "product": subcat.name, "product_id": subcat.id, "scope": "PAKISTAN",
                    "volume_mt": 50
                })

            # Process Each Query
            for q in queries:
                parsed_q = {
                    "intent": q["intent"],
                    "product": q["product"],
                    "family": q["family"],
                    "scope": q.get("scope", "WORLDWIDE"),
                    "country_filter": q.get("country_filter", []),
                    "price_ceiling": q.get("price_ceiling"),
                    "price_floor": q.get("price_floor"),
                    "volume_mt": q.get("volume_mt"),
                    "time_range": q.get("time_range")
                }

                candidates = aggregator.get_suppliers_for_subcategories(
                    [q["product_id"]],
                    intent=q["intent"],
                    scope=q["scope"],
                    country_filter=q.get("country_filter"),
                    price_filter={'ceiling': q.get("price_ceiling"), 'floor': q.get("price_floor")} if q.get("price_ceiling") or q.get("price_floor") else None,
                    volume_filter=q.get("volume_mt")
                )

                if not candidates or len(candidates) < 2:
                    continue

                query_features = []
                heuristic_scores = []

                weights = FAMILY_WEIGHTS.get(q["family"], DEFAULT_WEIGHTS)

                for cand in candidates:
                    # Enrich with volume_fit
                    vol_req = q.get("volume_mt")
                    if vol_req:
                        max_vol = cand.get('max_shipment_vol', 0)
                        total_vol = cand.get('total_volume', 0)
                        if max_vol >= vol_req * 1.2: v_fit = "Strong"
                        elif max_vol >= vol_req: v_fit = "Good"
                        elif total_vol >= vol_req: v_fit = "Partial"
                        else: v_fit = "Low"
                        cand['volume_fit'] = v_fit

                    feats = extractor.extract(cand, parsed_q)
                    query_features.append(feats)

                    feat_dict = dict(zip(FeatureExtractor.FEATURE_NAMES, feats))
                    score = sum(weights.get(k, 0)*v for k,v in feat_dict.items())
                    heuristic_scores.append(score)

                df = pd.DataFrame({'score': heuristic_scores})

                try:
                    df['pct'] = df['score'].rank(pct=True)
                    labels = df['pct'].apply(_percentile_to_label).values.tolist()
                except Exception:
                    labels = [0] * len(heuristic_scores)

                for f, l in zip(query_features, labels):
                    all_features.append(f)
                    all_labels.append(l)

                groups.append(len(candidates))

        return np.array(all_features), np.array(all_labels), np.array(groups)
