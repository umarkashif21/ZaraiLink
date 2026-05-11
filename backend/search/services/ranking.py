class SupplierRanker:
    def rank_suppliers(self, suppliers):
        # Weights: volume 0.4, frequency 0.3, recency 0.3.
        if not suppliers:
            return []

        max_vol = max(s['total_volume'] for s in suppliers) or 1
        max_freq = max(s['shipment_count'] for s in suppliers) or 1

        for s in suppliers:
            norm_vol = s['total_volume'] / max_vol
            norm_freq = s['shipment_count'] / max_freq

            recency_score = 1.0  # TODO: derive from last_shipment_date

            score = (norm_vol * 0.4) + (norm_freq * 0.3) + (recency_score * 0.3)

            s['score'] = round(score, 2)

        return sorted(suppliers, key=lambda x: x['score'], reverse=True)

class ComparableFinder:
    def find_comparables(self, current_supplier, subcategory_ids, all_suppliers):
        if not all_suppliers:
            return []

        candidates = [s for s in all_suppliers if s['name'] != current_supplier]

        # Assumes all_suppliers is already ranked by SupplierRanker.
        return candidates[:5]
