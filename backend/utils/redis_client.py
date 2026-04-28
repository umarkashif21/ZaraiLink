import logging
import numpy as np
from django.conf import settings

logger = logging.getLogger('zarailink')


class RedisClient:

    @classmethod
    def get_connection(cls):
        try:
            import redis
            location = settings.CACHES.get('default', {}).get('LOCATION', 'redis://127.0.0.1:6379/1')
            r = redis.from_url(location)
            r.ping()
            return r
        except Exception as e:
            logger.warning(f'Redis Connection Failed: {e}')
            return None

    @classmethod
    def create_index(cls):
        r = cls.get_connection()
        if r is None:
            return
        try:
            from redis.commands.search.field import VectorField, TextField
            from redis.commands.search.indexDefinition import IndexDefinition, IndexType
            VECTOR_DIM = 1536
            INDEX_NAME = 'idx:companies'
            schema = (
                TextField('name'),
                TextField('description'),
                VectorField('embedding', 'HNSW', {
                    'TYPE': 'FLOAT32',
                    'DIM': VECTOR_DIM,
                    'DISTANCE_METRIC': 'COSINE',
                }),
            )
            definition = IndexDefinition(prefix=['company:'], index_type=IndexType.HASH)
            r.ft(INDEX_NAME).create_index(schema, definition=definition)
            logger.info(f'Created Redis Search Index: {INDEX_NAME}')
        except Exception as e:
            logger.warning(f'Failed to create index: {e}')

    @classmethod
    def index_data(cls, key_prefix, object_id, embedding, metadata=None):
        r = cls.get_connection()
        if r is None:
            return
        try:
            key = f'{key_prefix}:{object_id}'
            mapping = {'embedding': np.array(embedding, dtype=np.float32).tobytes()}
            if metadata:
                mapping.update(metadata)
            r.hset(key, mapping=mapping)
        except Exception as e:
            logger.warning(f'Failed to index data to Redis: {e}')

    @classmethod
    def search(cls, query_embedding, top_k=10):
        r = cls.get_connection()
        if r is None:
            logger.info('AI vector search unavailable (Redis down). Using text search fallback.')
            return cls._inmemory_search(query_embedding, top_k)
        try:
            from redis.commands.search.query import Query
            INDEX_NAME = 'idx:companies'
            query_vec = np.array(query_embedding, dtype=np.float32).tobytes()
            query = (
                Query(f'*=>[KNN {top_k} @embedding $vec AS score]')
                .sort_by('score')
                .return_fields('id', 'score', 'name')
                .paging(0, top_k)
                .dialect(2)
            )
            params = {'vec': query_vec}
            res = r.ft(INDEX_NAME).search(query, query_params=params)
            results = []
            for doc in res.docs:
                results.append({
                    'id': doc.id.split(':')[-1],
                    'score': doc.score,
                    'name': doc.name,
                })
            return results
        except Exception as e:
            logger.warning(f'Redis Search failed, falling back to text search: {e}')
            return cls._inmemory_search(query_embedding, top_k)

    @classmethod
    def _inmemory_search(cls, query_embedding, top_k=10):
        """Fallback in-memory vector search using database embeddings."""
        try:
            from companies.models import CompanyEmbedding, Company
            from sklearn.metrics.pairwise import cosine_similarity
            all_embeddings = list(CompanyEmbedding.objects.values('company_name', 'embedding'))
            if not all_embeddings:
                logger.warning('No company embeddings found in database')
                return []
            names = [e['company_name'] for e in all_embeddings]
            vectors = np.array([e['embedding'] for e in all_embeddings], dtype=np.float32)
            query_vec = np.array(query_embedding, dtype=np.float32).reshape(1, -1)
            similarities = cosine_similarity(query_vec, vectors)[0]
            top_indices = np.argsort(similarities)[::-1][:top_k]
            results = []
            for i in top_indices:
                company_name = names[i]
                try:
                    company = Company.objects.get(name__icontains=company_name)
                    results.append({'id': str(company.id), 'score': float(similarities[i]), 'name': company_name})
                except Exception:
                    results.append({'id': None, 'score': float(similarities[i]), 'name': company_name})
            logger.info(f'In-memory search found {len(results)} results')
            return results
        except Exception as e:
            logger.warning(f'In-memory search failed: {e}')
            return []

    @classmethod
    def get_vector(cls, key_prefix, object_id):
        """Retrieve vector for a specific object to use in recommendations"""
        r = cls.get_connection()
        if r is None:
            return None
        try:
            key = f'{key_prefix}:{object_id}'
            data = r.hget(key, 'embedding')
            if data is None:
                return None
            return np.frombuffer(data, dtype=np.float32)
        except Exception as e:
            logger.warning(f'Failed to get vector: {e}')
            return None
