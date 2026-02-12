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
        # This guarantees "dextrose" finds "Dextrose Monohydrate"
        keyword_hits = ProductSubCategory.objects.filter(name__icontains=clean_qs)
        for hit in keyword_hits:
            matches[hit.id] = {
                "id": hit.id,
                "name": hit.name,
                "score": 1.0,  # Max score for direct keyword match
                "hs_code": hit.hs_code,
                "method": "keyword"
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
