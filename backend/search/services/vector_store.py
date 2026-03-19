import os
import faiss
import numpy as np
import logging
from sentence_transformers import SentenceTransformer
from django.conf import settings

logger = logging.getLogger(__name__)

class FaissVectorStore:
    """
    Modern Dense Semantic Retrieval using FAISS.
    Replaces the manual dot-product math in `nlp.py`.
    """
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(FaissVectorStore, cls).__new__(cls)
            cls._instance._init_store()
        return cls._instance

    def _init_store(self):
        self.index = None
        self.metadata = {'ids': [], 'names': [], 'hs_codes': []}
        self.embedding_model = None
        self.ready = False

    def load_model(self):
        if self.embedding_model is None:
            logger.info("Loading SentenceTransformer for Dense Retrieval...")
            self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        return self.embedding_model

    def build_index(self):
        """
        Builds the FAISS Index from Product Subcategories.
        In production, this should run asynchronously and optionally save/load from disk.
        """
        from trade_data.models import ProductSubCategory
        
        logger.info("Initializing FAISS Index...")
        categories = ProductSubCategory.objects.all()
        
        if not categories.exists():
            logger.warning("No categories to index.")
            return

        texts = []
        self.metadata = {'ids': [], 'names': [], 'hs_codes': []} # Reset

        for cat in categories:
            texts.append(cat.name)
            self.metadata['ids'].append(cat.id)
            self.metadata['names'].append(cat.name)
            self.metadata['hs_codes'].append(cat.hs_code)
            
        model = self.load_model()
        embeddings = model.encode(texts)
        
        # Initialize FAISS Flat L2 Index (exact search, fast enough for ~100k rows)
        dimension = embeddings.shape[1]
        self.index = faiss.IndexFlatL2(dimension)
        
        # FAISS strictly requires float32
        faiss_vectors = np.array(embeddings).astype('float32')
        self.index.add(faiss_vectors)
        
        self.ready = True
        logger.info(f"FAISS index built successfully with {self.index.ntotal} vectors.")

    def search(self, query: str, top_k=10, cache_expand=None):
        """
        Given a query vector, returns top_k candidates via ANN similarity.
        cache_expand is an optional list of expanded semantic terms to boost recall.
        """
        if not self.ready:
            self.build_index()
            
        if not self.index:
            return []

        model = self.load_model()
        
        # Pre-process query with expanded terms
        search_phrases = [query]
        if cache_expand:
            search_phrases.extend(cache_expand[:2]) # Limit to top 2 synonyms to avoid noise

        # Vectorize all phrases
        query_vecs = model.encode(search_phrases).astype('float32')
        
        # Aggregate results across original query and expansions
        results_map = {}
        
        for vec in query_vecs:
            # Reshape for FAISS: (1, d)
            v = vec.reshape(1, -1)
            distances, indices = self.index.search(v, top_k)
            
            for j, idx in enumerate(indices[0]):
                if idx == -1: continue # padding
                
                # Convert L2 distance back to a 0-1 similarity score loosely
                dist = distances[0][j]
                sim = 1.0 / (1.0 + (dist / 10.0)) # Scaled slightly to keep scores reasonable
                
                if sim < 0.4: continue # Drop low relevance
                
                cat_id = self.metadata['ids'][idx]
                
                # Max-pool scores if a subcategory matches multiple expansions
                if cat_id not in results_map or sim > results_map[cat_id]['score']:
                    results_map[cat_id] = {
                        "id": cat_id,
                        "name": self.metadata['names'][idx],
                        "hs_code": self.metadata['hs_codes'][idx],
                        "score": round(float(sim), 3),
                        "method": "semantic_faiss",
                        "matched_variants": []
                    }
                    
        # Sort descending by score
        final_results = list(results_map.values())
        final_results.sort(key=lambda x: x['score'], reverse=True)
        
        # Return top N overall after expansion merge
        return final_results[:top_k]
