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
        # Hybrid: keyword ILIKE (precision) + semantic (recall) + fuzzy variant catch.
        clean_qs = self._clean_query(query)
        matches = {}

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

        # ProductItem hits record the specific variant, e.g. "Dextrose Anhydrous"
        # maps to the Dextrose SubCategory parent.
        from trade_data.models import ProductItem
        item_hits = ProductItem.objects.filter(name__icontains=clean_qs).select_related('sub_category')
        for item in item_hits:
            parent = item.sub_category

            if parent.id in matches:
                if "matched_variants" not in matches[parent.id]:
                     matches[parent.id]["matched_variants"] = []

                if item.id not in matches[parent.id]["matched_variants"]:
                    matches[parent.id]["matched_variants"].append(item.id)
                    matches[parent.id]["variant_name"] = item.name
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

        index = self.get_index()
        if index and index.get('embeddings') is not None:
            model = self.get_model()
            query_vec = model.encode([clean_qs])

            scores = cosine_similarity(query_vec, index['embeddings'])[0]

            top_indices = np.argsort(scores)[::-1][:10]

            for idx in top_indices:
                score = float(scores[idx])
                if score < 0.4:
                    continue

                cat_id = index['ids'][idx]

                if cat_id not in matches:
                    matches[cat_id] = {
                        "id": cat_id,
                        "name": index['names'][idx],
                        "score": score,
                        "hs_code": index['hs_codes'][idx],
                        "method": "semantic"
                    }

        # Fuzzy variant catch (handles typos like "MONOYDRATE" -> "Monohydrate").
        try:
            from difflib import SequenceMatcher
            from trade_data.models import ProductItem

            matched_subcat_ids = list(matches.keys())

            if matched_subcat_ids:
                candidate_items = ProductItem.objects.filter(sub_category_id__in=matched_subcat_ids).values('id', 'name', 'sub_category_id')

                for item in candidate_items:
                    parent_id = item['sub_category_id']
                    if item['id'] in matches[parent_id].get('matched_variants', []):
                        continue

                    ratio = SequenceMatcher(None, clean_qs, item['name'].lower()).ratio()

                    if ratio > 0.85:
                        if "matched_variants" not in matches[parent_id]:
                             matches[parent_id]["matched_variants"] = []

                        matches[parent_id]["matched_variants"].append(item['id'])
        except Exception as e:
            print(f"Fuzzy match error: {e}")

        results = list(matches.values())
        results.sort(key=lambda x: x['score'], reverse=True)
        return results

    def _clean_query(self, query):
        stopwords = ["i", "want", "to", "buy", "suppliers", "sell", "who", "sells", "find", "search", "for", "please", "looking"]
        words = query.lower().split()
        clean_words = [w for w in words if w not in stopwords]
        return " ".join(clean_words)
