import numpy as np
import pandas as pd
import random
from trade_data.models import ProductSubCategory, Transaction
from .aggregation import SupplierAggregator
from .ranking_ltr import FeatureExtractor, FAMILY_WEIGHTS, DEFAULT_WEIGHTS

class LTRDatasetBuilder:
    """
    Builds a synthetic dataset for LTR training from historical transactions.
    """
    def build_dataset(self, limit_per_product=50):
        """
        Generates X (features), y (labels), group (query boundaries).
        """
        subcats = ProductSubCategory.objects.all()
        aggregator = SupplierAggregator()
        extractor = FeatureExtractor()
        
        all_features = []
        all_labels = []
        groups = []
        
        # Cache transaction check to avoid query in loop? 
        # Actually, let's just iterate.
        
        for subcat in subcats:
            # Check if this product has any activity
            has_imports = Transaction.objects.filter(product_item__sub_category=subcat, trade_type='IMPORT').exists()
            has_exports = Transaction.objects.filter(product_item__sub_category=subcat, trade_type='EXPORT').exists()
            
            if not has_imports and not has_exports:
                continue
                
            # Generate Synthetic Queries
            queries = []
            
            # BUY Queries (Search for Supplier) - Valid if IMPORTS exist (for Worldwide) or EXPORTS (for Pakistan)
            # Simplification: BUY + WORLDWIDE -> IMPORT. BUY + PAKISTAN -> EXPORT.
            
            if has_imports:
                # 1. Simple Discovery (Family 1) - Worldwide
                queries.append({
                    "intent": "BUY", "family": 1, "product": subcat.name, "product_id": subcat.id, "scope": "WORLDWIDE"
                })
                # 3. Volume Aware (Family 3)
                queries.append({
                    "intent": "BUY", "family": 3, "product": subcat.name, "product_id": subcat.id, "scope": "WORLDWIDE",
                    "volume_mt": 100 # Arbitrary constraint to trigger feature
                })
                # 4. Price Constrained (Family 4)
                queries.append({
                    "intent": "BUY", "family": 4, "product": subcat.name, "product_id": subcat.id, "scope": "WORLDWIDE",
                    "price_ceiling": 1000 # Arbitrary
                })
            
            if has_exports:
                 # 1. Simple Discovery (Family 1) - Selling to Worldwide (Find Buyer) -> EXPORT
                queries.append({
                    "intent": "SELL", "family": 1, "product": subcat.name, "product_id": subcat.id, "scope": "WORLDWIDE"
                })
                 # Buy from Pakistan (Family 1) -> EXPORT
                queries.append({
                    "intent": "BUY", "family": 1, "product": subcat.name, "product_id": subcat.id, "scope": "PAKISTAN"
                })

            # Process Each Query
            for q in queries:
                # 1. Retrieve Candidates
                # Simulate Parsed Query structure
                parsed_q = {
                    "intent": q["intent"],
                    "product": q["product"],
                    "family": q["family"],
                    "country_filter": q.get("country_filter", []),
                    "price_ceiling": q.get("price_ceiling"),
                    "volume_mt": q.get("volume_mt"),
                    "time_range": q.get("time_range")
                }
                
                # Fetch Raw Candidates
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
                    
                # 2. Extract Features & Heuristic Score
                query_features = []
                heuristic_scores = []
                
                weights = FAMILY_WEIGHTS.get(q["family"], DEFAULT_WEIGHTS)
                
                for cand in candidates:
                    # Enrich candidate with 'volume_fit' etc which are usually done in Retriever
                    # We need to simulate that logic or move it to a shared helper? 
                    # FeatureExtractor expects 'volume_fit' string or score? 
                    # FeatureExtractor logic: v_fit_str = candidate.get('volume_fit', 'N/A')
                    # We need to calculate it here if Aggregator doesn't return it.
                    # Aggregator returns 'max_shipment_vol' but not 'volume_fit' string.
                    # CandidateRetriever adds the string. 
                    # Let's add it here briefly.
                    
                    vol_req = q.get("volume_mt")
                    if vol_req:
                        max_vol = cand.get('max_shipment_vol', 0)
                        total_vol = cand.get('total_volume', 0)
                        if max_vol >= vol_req * 1.2: v_fit = "Strong"
                        elif max_vol >= vol_req: v_fit = "Good"
                        elif total_vol >= vol_req: v_fit = "Partial"
                        else: v_fit = "Low"
                        cand['volume_fit'] = v_fit
                    
                    # Extract
                    feats = extractor.extract(cand, parsed_q)
                    query_features.append(feats)
                    
                    # Heuristic Score
                    feat_dict = dict(zip(FeatureExtractor.FEATURE_NAMES, feats))
                    score = sum(weights.get(k, 0)*v for k,v in feat_dict.items())
                    heuristic_scores.append(score)
                    
                # 3. Generating Labels (Quantile Binning)
                # Sort by score descending
                # We need to know the rank to assign label
                # Or just use pandas qcut?
                
                # Let's use simple percentile logic
                # Scores -> Rank -> Percentile -> Label
                
                # Create DataFrame for easier binning
                df = pd.DataFrame({'score': heuristic_scores})
                
                # Handling ties and small groups
                if len(df) < 5:
                    # Fallback: simple normalization or just skip small groups?
                    # Let's keep them but labels might be coarse
                    pass
                
                try:
                    # qcut might fail if not unique edges. rank(pct=True) is safer.
                    df['pct'] = df['score'].rank(pct=True)
                    
                    def time_to_label(p):
                        if p > 0.8: return 4
                        if p > 0.6: return 3
                        if p > 0.4: return 2
                        if p > 0.2: return 1
                        return 0
                        
                    labels = df['pct'].apply(time_to_label).values.tolist()
                except:
                    # Fallback
                    labels = [0] * len(heuristic_scores)
                
                # Append to main lists
                for f, l in zip(query_features, labels):
                    all_features.append(f)
                    all_labels.append(l)
                    
                groups.append(len(candidates))
                
        return np.array(all_features), np.array(all_labels), np.array(groups)
