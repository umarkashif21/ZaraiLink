class SupplierRanker:
    def rank_suppliers(self, suppliers):
        """
        Ranks a list of supplier dictionaries based on:
        - Volume (40%)
        - Shipment Frequency (30%)
        - Recency (30%)
        - Price (Secondary factor, mostly for display ordering if others equal)
        """
        if not suppliers:
            return []
            
        # 1. Determine Max values for normalization
        max_vol = max(s['total_volume'] for s in suppliers) or 1
        max_freq = max(s['shipment_count'] for s in suppliers) or 1
        
        # 2. Score each supplier
        for s in suppliers:
            norm_vol = s['total_volume'] / max_vol
            norm_freq = s['shipment_count'] / max_freq
            
            # Simple recency score (1.0 if this year, 0.8 last year, etc.)
            # For now, just placeholder
            recency_score = 1.0 
            
            # Weighted Score
            # Volume (0.4) + Frequency (0.3) + Recency (0.3)
            score = (norm_vol * 0.4) + (norm_freq * 0.3) + (recency_score * 0.3)
            
            s['score'] = round(score, 2)
            
        # 3. Sort by score descending
        return sorted(suppliers, key=lambda x: x['score'], reverse=True)

class ComparableFinder:
    def find_comparables(self, current_supplier, subcategory_ids, all_suppliers):
        """
        Finds similar suppliers based on volume and product.
        Simple logic:
        1. Filter out current supplier.
        2. Sort by volume (closest to current supplier's volume).
        3. Return top 5.
        """
        if not all_suppliers:
            return []
            
        # Filter out self
        candidates = [s for s in all_suppliers if s['name'] != current_supplier]
        
        # In a real app, we might find suppliers with *similar* volume, 
        # i.e. minimizes abs(s.volume - current.volume)
        # For now, just return top ranked (highest score) as "competitors"
        
        # Assuming 'all_suppliers' are already ranked by SupplierRanker
        return candidates[:5]
