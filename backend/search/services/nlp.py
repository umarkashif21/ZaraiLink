import os
import pickle
import numpy as np
from django.conf import settings
from trade_data.models import ProductSubCategory
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

class QueryMatcher:
    _model = None
    _index = None

    @classmethod
    def get_model(cls):
        if cls._model is None:
            # Load model (downloads on first run)
            cls._model = SentenceTransformer('all-MiniLM-L6-v2')
        return cls._model

    @classmethod
    def get_index(cls):
        if cls._index is None:
            index_path = os.path.join(settings.BASE_DIR, 'search_index.pkl')
            if os.path.exists(index_path):
                with open(index_path, 'rb') as f:
                    cls._index = pickle.load(f)
        return cls._index

    def match(self, query):
        """
        Hybrid matching:
        1. Keyword match (High precision for exact substrings like "dextrose")
        2. Semantic match (High recall for synonyms/concepts)
        """
        clean_qs = self._clean_query(query)
        matches = {}

        # 1. Keyword Match (Database ILIKE)
        # Check ProductSubCategory (Broad)
        subcat_hits = ProductSubCategory.objects.filter(name__icontains=clean_qs)
        for hit in subcat_hits:
            matches[hit.id] = {
                "id": hit.id,
                "name": hit.name,
                "score": 1.0, 
                "hs_code": hit.hs_code,
                "method": "keyword_subcat",
                "matched_variants": []
            }
            
        # Check ProductItem (Specific Variant)
        # e.g. "Dextrose Anhydrous" -> matches Item -> maps to Dextrose SubCat
        from trade_data.models import ProductItem
        item_hits = ProductItem.objects.filter(name__icontains=clean_qs).select_related('sub_category')
        for item in item_hits:
            parent = item.sub_category
            # If we already matched the parent (e.g. searching "Dextrose"), we normally keep it.
            # BUT if we matched a SPECIFIC item ("Dextrose Anhydrous"), we want to record that specificity.
            
            if parent.id in matches:
                # Append to existing list of matched variants
                if "matched_variants" not in matches[parent.id]:
                     matches[parent.id]["matched_variants"] = []
                
                if item.id not in matches[parent.id]["matched_variants"]:
                    matches[parent.id]["matched_variants"].append(item.id)
                    matches[parent.id]["variant_name"] = item.name # Update name to last found (display purposes)
            else:
                matches[parent.id] = {
                    "id": parent.id,
                    "name": parent.name,
                    "score": 1.0,
                    "hs_code": parent.hs_code,
                    "method": "keyword_item",
                    "matched_variants": [item.id],
                    "variant_name": item.name
                }

        # 2. Semantic Search (Vector)
        index = self.get_index()
        if index and index.get('embeddings') is not None:
            model = self.get_model()
            query_vec = model.encode([clean_qs])
            
            # Compute cosine similarity
            # shape: (1, embedding_dim) x (num_categories, embedding_dim).T -> (1, num_categories)
            scores = cosine_similarity(query_vec, index['embeddings'])[0]
            
            # Get top N candidates (e.g., top 10)
            top_indices = np.argsort(scores)[::-1][:10]
            
            for idx in top_indices:
                score = float(scores[idx])
                if score < 0.4: # Filter low relevance
                    continue
                    
                cat_id = index['ids'][idx]
                
                # If already found by keyword, keep the 1.0 score, otherwise add
                if cat_id not in matches:
                    matches[cat_id] = {
                        "id": cat_id,
                        "name": index['names'][idx],
                        "score": score,
                        "hs_code": index['hs_codes'][idx],
                        "method": "semantic"
                    }

        # 3. Fuzzy Variant Matching (Catch typos like "MONOYDRATE")
        # For ALL matched subcategories (from keyword or semantic), check their items for near-matches
        try:
            from difflib import SequenceMatcher
            from trade_data.models import ProductItem
            
            # Get all matched subcategory IDs
            matched_subcat_ids = list(matches.keys())
            
            if matched_subcat_ids:
                # Fetch all items for these subcategories
                candidate_items = ProductItem.objects.filter(sub_category_id__in=matched_subcat_ids).values('id', 'name', 'sub_category_id')
                
                for item in candidate_items:
                    # Skip if already matched
                    parent_id = item['sub_category_id']
                    if item['id'] in matches[parent_id].get('matched_variants', []):
                        continue
                        
                    # Calculate similarity
                    # clean_qs is lower, item name to lower
                    ratio = SequenceMatcher(None, clean_qs, item['name'].lower()).ratio()
                    
                    if ratio > 0.85: # Threshold for typos
                        if "matched_variants" not in matches[parent_id]:
                             matches[parent_id]["matched_variants"] = []
                        
                        matches[parent_id]["matched_variants"].append(item['id'])
                        
                        # Only update variant_name if it's the *best* match? 
                        # Or just leave broad name if vaguely matched.
                        # Ideally we want to show the USER what they found.
                        # If query was "Dextrose Monohydrate", and we found "Dextrose Monoydrate", 
                        # we probably implicitly just want to include it in the filter.
        except Exception as e:
            print(f"Fuzzy match error: {e}")

        # Convert to list and sort by score
        results = list(matches.values())
        results.sort(key=lambda x: x['score'], reverse=True)
        return results

    def _clean_query(self, query):
        # Remove common "stop phrases" that confuse search
        stopwords = ["i", "want", "to", "buy", "suppliers", "sell", "who", "sells", "find", "search", "for", "please", "looking"]
        words = query.lower().split()
        clean_words = [w for w in words if w not in stopwords]
        return " ".join(clean_words)
