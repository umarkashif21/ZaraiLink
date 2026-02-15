class ComparableFinder:
    def find_comparables(self, current_supplier, subcategory_ids, all_suppliers):
        """
        Finds similar suppliers based on volume and product.
        1. Filter out current supplier (case-insensitive).
        2. Return top 5 from already-ranked list.
        """
        if not all_suppliers:
            return []

        # Normalize for comparison
        normalized_current = current_supplier.strip().upper()
        candidates = [s for s in all_suppliers if s['name'].strip().upper() != normalized_current]

        return candidates[:5]
