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
                # Parse settings.CACHES['default']['LOCATION']
                # e.g. redis://127.0.0.1:6379/1
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
        
        VECTOR_DIM = 1536 # OpenAI text-embedding-3-small
        INDEX_NAME = "idx:companies"
        
        try:
            r.ft(INDEX_NAME).info()
            # logger.info("Index already exists")
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
        if not r or query_embedding is None:
            return []
            
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
            # doc.id is like "company:123", we want "123"
            return [{'id': doc.id.split(':')[-1], 'score': doc.score, 'name': doc.name} for doc in res.docs]
        except Exception as e:
            logger.error(f"Redis Search failed: {e}")
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

