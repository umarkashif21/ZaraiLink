import numpy as np
import pandas as pd
import random
from trade_data.models import ProductSubCategory, Transaction
from .aggregation import SupplierAggregator
from .ranking_ltr import FeatureExtractor, FAMILY_WEIGHTS, DEFAULT_WEIGHTS

class LTRDatasetBuilder:
    """Builds synthetic LTR training data from historical transactions."""
    def build_dataset(self, limit_per_product=50):
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

            queries = []

            if has_imports:
                queries.append({
                    "intent": "BUY", "family": 1, "product": subcat.name, "product_id": subcat.id, "scope": "WORLDWIDE"
                })
                queries.append({
                    "intent": "BUY", "family": 3, "product": subcat.name, "product_id": subcat.id, "scope": "WORLDWIDE",
                    "volume_mt": 100
                })
                queries.append({
                    "intent": "BUY", "family": 4, "product": subcat.name, "product_id": subcat.id, "scope": "WORLDWIDE",
                    "price_ceiling": 1000
                })

            if has_exports:
                queries.append({
                    "intent": "SELL", "family": 1, "product": subcat.name, "product_id": subcat.id, "scope": "WORLDWIDE"
                })
                queries.append({
                    "intent": "BUY", "family": 1, "product": subcat.name, "product_id": subcat.id, "scope": "PAKISTAN"
                })

            for q in queries:
                parsed_q = {
                    "intent": q["intent"],
                    "product": q["product"],
                    "family": q["family"],
                    "country_filter": q.get("country_filter", []),
                    "price_ceiling": q.get("price_ceiling"),
                    "volume_mt": q.get("volume_mt"),
                    "time_range": q.get("time_range")
                }
                
                candidates = aggregator.get_suppliers_for_subcategories(
                    [q["product_id"]],
                    intent=q["intent"],
                    scope=q["scope"],
                    country_filter=q.get("country_filter"),
                    price_filter={'ceiling': q.get("price_ceiling")} if q.get("price_ceiling") else None,
                    volume_filter=q.get("volume_mt")
                )
                
                if not candidates or len(candidates) < 2:
                    continue

                query_features = []
                heuristic_scores = []

                weights = FAMILY_WEIGHTS.get(q["family"], DEFAULT_WEIGHTS)

                for cand in candidates:
                    # Aggregator returns 'max_shipment_vol' but not the 'volume_fit'
                    # label. Compute it here so FeatureExtractor can read it.
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
                    # rank(pct=True) handles duplicate-edge issues that break qcut.
                    df['pct'] = df['score'].rank(pct=True)

                    def time_to_label(p):
                        if p > 0.8: return 4
                        if p > 0.6: return 3
                        if p > 0.4: return 2
                        if p > 0.2: return 1
                        return 0

                    labels = df['pct'].apply(time_to_label).values.tolist()
                except:
                    labels = [0] * len(heuristic_scores)

                for f, l in zip(query_features, labels):
                    all_features.append(f)
                    all_labels.append(l)
                    
                groups.append(len(candidates))
                
        return np.array(all_features), np.array(all_labels), np.array(groups)
