"""
sync_search.py - Django Management Command
==========================================
Phase 1: OpenSearch Foundation - Indexes all Transactions into a hybrid
BM25 + kNN (vector) index for use by the ZaraiLink Trade Search Engine.

Usage:
    python manage.py sync_search
    python manage.py sync_search --reset   (drops index first, then rebuilds)
"""

import logging
from django.core.management.base import BaseCommand
from opensearchpy import OpenSearch
from opensearchpy.helpers import bulk
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)

# ===========================================================================
# Constants
# ===========================================================================

OPENSEARCH_HOST = "http://localhost:9200"
INDEX_NAME = "trade_index"
VECTOR_DIM = 384
EMBEDDING_MODEL = "all-MiniLM-L6-v2"
BATCH_SIZE = 500


# ===========================================================================
# Index Definition
# ===========================================================================

INDEX_SETTINGS = {
    "settings": {
        "index": {
            "knn": True
        }
    },
    "mappings": {
        "properties": {
            "product_item_name": {
                "type": "text",
                "analyzer": "standard",
                "fields": {
                    "keyword": {
                        "type": "keyword"
                    }
                }
            },
            "clean_product_name": {
                "type": "text",
                "analyzer": "standard",
                "fields": {
                    "keyword": {
                        "type": "keyword"
                    }
                }
            },
            "sub_category_name": {
                "type": "keyword"
            },
            "hs_code": {
                "type": "keyword"
            },
            "buyer": {
                "type": "text",
                "analyzer": "standard",
                "fields": {
                    "keyword": {
                        "type": "keyword"
                    }
                }
            },
            "seller": {
                "type": "text",
                "analyzer": "standard",
                "fields": {
                    "keyword": {
                        "type": "keyword"
                    }
                }
            },
            "origin_country": {
                "type": "keyword"
            },
            "destination_country": {
                "type": "keyword"
            },
            "trade_type": {
                "type": "keyword"
            },
            "qty_mt": {
                "type": "float"
            },
            "usd_per_mt": {
                "type": "float"
            },
            "reporting_date": {
                "type": "date"
            },
            "combined_vector": {
                "type": "knn_vector",
                "dimension": VECTOR_DIM,
                "method": {
                    "name": "hnsw",
                    "space_type": "l2",
                    "engine": "faiss"
                }
            }
        }
    }
}


# ===========================================================================
# Core Search Function
# ===========================================================================

def hybrid_trade_search(client: OpenSearch, model: SentenceTransformer,
                        query_text: str, trade_type_filter: str = None, top_k: int = 10):
    """
    Execute a Hybrid BM25 + kNN search against the trade_index.

    Args:
        client: OpenSearch Python client instance.
        model:  The loaded SentenceTransformer model.
        query_text:         Natural language query (e.g. "refined sugar from Brazil").
        trade_type_filter:  Optional "IMPORT" or "EXPORT" filter.
        top_k:              Number of results to return.

    Returns:
        List of hit _source dicts with a `_score` key injected.
    """
    # 1. Embed the query
    query_vector = model.encode(query_text).tolist()

    # 2. Build hybrid query
    should_clauses = [
        # BM25 full-text match — clean_product_name gets 9x boost (most signal),
        # product_item_name gets 3x, buyer/seller at 1x.
        {
            "multi_match": {
                "query": query_text,
                "fields": [
                    "clean_product_name^9",  # sub_category name — highest signal
                    "product_item_name^3",   # raw item name — secondary
                    "buyer",
                    "seller"
                ],
                "type": "best_fields"
            }
        },
        # Dense kNN vector search
        {
            "knn": {
                "combined_vector": {
                    "vector": query_vector,
                    "k": top_k
                }
            }
        }
    ]

    query_body = {
        "size": top_k,
        "query": {
            "bool": {
                "should": should_clauses
            }
        }
    }

    # 3. Apply optional trade_type filter
    if trade_type_filter:
        query_body["query"]["bool"]["filter"] = [
            {"term": {"trade_type": trade_type_filter.upper()}}
        ]

    response = client.search(index=INDEX_NAME, body=query_body)

    # 4. Flatten results
    results = []
    for hit in response["hits"]["hits"]:
        doc = hit["_source"]
        doc["_score"] = hit["_score"]
        results.append(doc)

    return results


# ===========================================================================
# Django Management Command
# ===========================================================================

class Command(BaseCommand):
    help = "Sync all Transactions into the OpenSearch hybrid index (trade_index)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--reset",
            action="store_true",
            help="Drop the existing index before rebuilding it.",
        )

    def handle(self, *args, **options):
        # Lazy import to avoid Django app registry issues
        from trade_data.models import Transaction

        self.stdout.write(self.style.MIGRATE_HEADING("=== ZaraiLink: OpenSearch Sync ==="))

        # -----------------------------------------------------------------------
        # 1. Connect to OpenSearch
        # -----------------------------------------------------------------------
        self.stdout.write("Connecting to OpenSearch...")
        client = OpenSearch(hosts=[OPENSEARCH_HOST], timeout=30)

        try:
            info = client.info()
            self.stdout.write(self.style.SUCCESS(
                f"Connected! OpenSearch v{info['version']['number']} | "
                f"Cluster: {info['cluster_name']}"
            ))
        except Exception as e:
            self.stderr.write(self.style.ERROR(
                f"Cannot connect to OpenSearch at {OPENSEARCH_HOST}.\n"
                f"Please ensure the container is running: docker-compose up -d\n"
                f"Error: {e}"
            ))
            return

        # -----------------------------------------------------------------------
        # 2. Create (or reset) the index
        # -----------------------------------------------------------------------
        if options["reset"] and client.indices.exists(index=INDEX_NAME):
            self.stdout.write(f"Dropping existing index '{INDEX_NAME}'...")
            client.indices.delete(index=INDEX_NAME)
            self.stdout.write(self.style.WARNING(f"Index '{INDEX_NAME}' DELETED."))

        if not client.indices.exists(index=INDEX_NAME):
            self.stdout.write(f"Creating index '{INDEX_NAME}' with kNN + BM25 mappings...")
            client.indices.create(index=INDEX_NAME, body=INDEX_SETTINGS)
            self.stdout.write(self.style.SUCCESS(f"Index '{INDEX_NAME}' created."))
        else:
            self.stdout.write(self.style.WARNING(
                f"Index '{INDEX_NAME}' already exists. Appending data. "
                f"Use --reset to rebuild from scratch."
            ))

        # -----------------------------------------------------------------------
        # 3. Load Embedding Model
        # -----------------------------------------------------------------------
        self.stdout.write(f"Loading embedding model: {EMBEDDING_MODEL} ...")
        model = SentenceTransformer(EMBEDDING_MODEL)
        self.stdout.write(self.style.SUCCESS("Embedding model loaded."))

        # -----------------------------------------------------------------------
        # 4. ETL: Fetch, Embed, and Bulk Index
        # -----------------------------------------------------------------------
        self.stdout.write("Fetching transactions from database...")
        # Deep join: product_item -> sub_category to get clean category names
        qs = Transaction.objects.select_related("product_item__sub_category").all()
        total = qs.count()
        self.stdout.write(f"Found {total:,} transactions. Indexing in batches of {BATCH_SIZE}...")

        def generate_actions(queryset):
            """Generator that yields OpenSearch bulk action dicts."""
            for tx in queryset.iterator(chunk_size=BATCH_SIZE):
                item = tx.product_item
                item_description = item.name if item else ""
                # sub_category.name is the clean, canonical product label (e.g. "Refined Sugar")
                sub_category_name = (
                    item.sub_category.name
                    if item and item.sub_category
                    else item_description
                )

                # Structured semantic string: Sub-Category is leading so the AI
                # learns it is the most important concept in the embedding.
                semantic_text = (
                    f"Product: {sub_category_name}. "
                    f"Details: {item_description}. "
                    f"Trade: {tx.trade_type} from {tx.origin_country} to {tx.destination_country}."
                )
                vector = model.encode(semantic_text).tolist()

                yield {
                    "_index": INDEX_NAME,
                    "_id": tx.id,
                    "_source": {
                        "product_item_name": item_description,
                        "clean_product_name": sub_category_name,
                        "sub_category_name": sub_category_name,
                        "hs_code": tx.hs_code,
                        "buyer": tx.buyer,
                        "seller": tx.seller,
                        "origin_country": tx.origin_country,
                        "destination_country": tx.destination_country,
                        "trade_type": tx.trade_type,
                        "qty_mt": float(tx.qty_mt) if tx.qty_mt else 0.0,
                        "usd_per_mt": float(tx.usd_per_mt) if tx.usd_per_mt else None,
                        "reporting_date": str(tx.reporting_date),
                        "combined_vector": vector,
                    }
                }

        success_count, failed_count = bulk(
            client,
            generate_actions(qs),
            chunk_size=BATCH_SIZE,
            raise_on_error=False,
            stats_only=False,
        )

        self.stdout.write(self.style.SUCCESS(
            f"\n✓ Indexed {success_count:,} documents."
        ))
        if failed_count:
            self.stdout.write(self.style.WARNING(f"⚠ {failed_count} documents failed."))

        # -----------------------------------------------------------------------
        # 5. Verification: Run a test search
        # -----------------------------------------------------------------------
        self.stdout.write("\nRunning test search: 'sugar importers from Brazil'...")
        try:
            results = hybrid_trade_search(
                client, model,
                query_text="sugar importers from Brazil",
                trade_type_filter="IMPORT",
                top_k=5
            )
            self.stdout.write(self.style.SUCCESS(f"Test search returned {len(results)} results."))
            for i, r in enumerate(results, 1):
                self.stdout.write(
                    f"  {i}. [{r.get('trade_type')}] {r.get('clean_product_name', r.get('product_item_name'))} | "
                    f"{r.get('origin_country')} → {r.get('destination_country')} | "
                    f"Score: {r.get('_score', 0):.4f}"
                )
        except Exception as e:
            self.stdout.write(self.style.WARNING(f"Test search failed (index may be refreshing): {e}"))

        self.stdout.write(self.style.SUCCESS("\n=== Sync Complete! ==="))
