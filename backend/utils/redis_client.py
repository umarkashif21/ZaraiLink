import redis
from django.conf import settings
import logging
import numpy as np

logger = logging.getLogger('zarailink')

class RedisClient:
    _connection = None

    @classmethod
    def get_connection(cls):
        if cls._connection is None:
            try:
                
                
                cls._connection = redis.Redis.from_url(settings.CACHES['default']['LOCATION'])
                cls._connection.ping()
            except Exception as e:
                logger.error(f"Redis Connection Failed: {e}")
                cls._connection = None
        return cls._connection

    @classmethod
    def create_index(cls):
        r = cls.get_connection()
        if not r: return
        
        from redis.commands.search.field import VectorField, TextField
        from redis.commands.search.indexDefinition import IndexDefinition, IndexType
        
        VECTOR_DIM = 1536 
        INDEX_NAME = "idx:companies"
        
        try:
            r.ft(INDEX_NAME).info()
            
        except:
            schema = (
                TextField("name"),
                TextField("description"),
                VectorField("embedding",
                    "HNSW", {
                        "TYPE": "FLOAT32",
                        "DIM": VECTOR_DIM,
                        "DISTANCE_METRIC": "COSINE"
                    }
                )
            )
            definition = IndexDefinition(prefix=["company:"], index_type=IndexType.HASH)
            try:
                r.ft(INDEX_NAME).create_index(schema, definition=definition)
                logger.info("Created Redis Search Index: idx:companies")
            except Exception as e:
                logger.error(f"Failed to create index: {e}")

    @classmethod
    def index_data(cls, key_prefix, object_id, embedding, metadata=None):
        r = cls.get_connection()
        if not r or embedding is None:
            return

        key = f"{key_prefix}:{object_id}"
        mapping = {
            "embedding": np.array(embedding, dtype=np.float32).tobytes(),
        }
        if metadata:
            mapping.update(metadata)
        
        try:
            r.hset(key, mapping=mapping)
        except Exception as e:
            logger.error(f"Failed to index data to Redis: {e}")

    @classmethod
    def search(cls, query_embedding, top_k=5):
        r = cls.get_connection()
        
        
        if r and query_embedding is not None:
            from redis.commands.search.query import Query
            
            INDEX_NAME = "idx:companies"
            query = (
                Query(f"*=>[KNN {top_k} @embedding $vec AS score]")
                .sort_by("score")
                .return_fields("id", "score", "name")
                .dialect(2)
            )
            params = {"vec": np.array(query_embedding, dtype=np.float32).tobytes()}
            
            try:
                res = r.ft(INDEX_NAME).search(query, params)
                
                return [{'id': doc.id.split(':')[-1], 'score': doc.score, 'name': doc.name} for doc in res.docs]
            except Exception as e:
                logger.warning(f"Redis Search failed, falling back to text search: {e}")
        
        
        
        logger.info("AI vector search unavailable (Redis down). Using text search fallback.")
        return []
    
    @classmethod
    def _inmemory_search(cls, query_embedding, top_k=5):
        """Fallback in-memory vector search using database embeddings."""
        try:
            from trade_data.models import CompanyEmbedding
            from companies.models import Company
            from sklearn.metrics.pairwise import cosine_similarity
            
            
            all_embeddings = list(CompanyEmbedding.objects.all().values('company_name', 'embedding'))
            if not all_embeddings:
                logger.warning("No company embeddings found in database")
                return []
            
            
            names = []
            vectors = []
            for emb in all_embeddings:
                names.append(emb['company_name'])
                vectors.append(emb['embedding'])
            
            vectors = np.array(vectors)
            query_vec = np.array(query_embedding).reshape(1, -1)
            
            
            similarities = cosine_similarity(query_vec, vectors)[0]
            top_indices = np.argsort(similarities)[-top_k:][::-1]
            
            
            results = []
            for i in top_indices:
                company_name = names[i]
                
                company = Company.objects.filter(name__icontains=company_name).first()
                if company:
                    results.append({
                        'id': str(company.id),
                        'score': float(similarities[i]),
                        'name': company_name
                    })
                else:
                    
                    results.append({
                        'id': company_name,  
                        'score': float(similarities[i]),
                        'name': company_name
                    })
            
            logger.info(f"In-memory search found {len(results)} results")
            return results
            
        except Exception as e:
            logger.error(f"In-memory search failed: {e}")
            return []


    @classmethod
    def get_vector(cls, key_prefix, object_id):
        """Retrieve vector for a specific object to use in recommendations"""
        r = cls.get_connection()
        if not r: return None
        
        key = f"{key_prefix}:{object_id}"
        try:
            data = r.hget(key, "embedding")
            if data:
                return np.frombuffer(data, dtype=np.float32)
        except Exception as e:
            logger.error(f"Failed to get vector: {e}")
        return None

