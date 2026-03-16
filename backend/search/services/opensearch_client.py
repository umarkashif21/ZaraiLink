"""
search/services/opensearch_client.py

OpenSearch client and index management for scalable trade data search.

Indices:
    zarailink_transactions  — raw transaction records (one doc per Transaction row)
    zarailink_products      — ProductSubCategory catalog

Usage:
    from search.services.opensearch_client import get_os_client, OS_TRANSACTIONS_INDEX

    client = get_os_client()          # singleton
    client.ping()                     # verify connection
"""

import logging
from django.conf import settings

logger = logging.getLogger(__name__)

# ── Index names ───────────────────────────────────────────────────────────────
OS_TRANSACTIONS_INDEX = 'zarailink_transactions'
OS_PRODUCTS_INDEX = 'zarailink_products'

# ── Index mappings ────────────────────────────────────────────────────────────
TRANSACTION_MAPPING = {
    'mappings': {
        'properties': {
            'id': {'type': 'integer'},
            'tx_reference': {'type': 'keyword'},
            'reporting_date': {
                'type': 'date',
                'format': 'yyyy-MM-dd',
            },
            'trade_type': {'type': 'keyword'},
            'hs_code': {'type': 'keyword'},
            'product_item_id': {'type': 'integer'},
            'subcategory_id': {'type': 'integer'},
            'seller': {
                'type': 'text',
                'fields': {
                    'keyword': {
                        'type': 'keyword',
                        'ignore_above': 512,
                    }
                },
            },
            'buyer': {
                'type': 'text',
                'fields': {
                    'keyword': {
                        'type': 'keyword',
                        'ignore_above': 512,
                    }
                },
            },
            'shipping_agent': {'type': 'text'},
            'origin_country': {'type': 'keyword'},
            'destination_country': {'type': 'keyword'},
            'qty_kg': {'type': 'float'},
            'qty_mt': {'type': 'float'},
            'usd_per_kg': {'type': 'float'},
            'usd_per_mt': {'type': 'float'},
            'pkr': {'type': 'float'},
            'usd': {'type': 'float'},
            'shipment_count': {'type': 'integer'},  # always 1 per doc
        }
    },
    'settings': {
        'number_of_shards': 1,
        'number_of_replicas': 1,
    },
}

PRODUCT_MAPPING = {
    'mappings': {
        'properties': {
            'id': {'type': 'integer'},
            'name': {
                'type': 'text',
                'fields': {
                    'keyword': {
                        'type': 'keyword',
                        'ignore_above': 256,
                    }
                },
            },
            'hs_code': {'type': 'keyword'},
        }
    },
    'settings': {
        'number_of_shards': 1,
        'number_of_replicas': 1,
    },
}

# ── Singleton client ──────────────────────────────────────────────────────────
_os_client = None


def get_os_client():
    """
    Return a module-level singleton OpenSearch client.

    Connection parameters are read from Django settings:
        OPENSEARCH_HOST  (default: 'localhost')
        OPENSEARCH_PORT  (default: 9200)
    """
    global _os_client
    if _os_client is not None:
        return _os_client

    try:
        from opensearchpy import OpenSearch  # noqa: F401
    except ImportError as exc:
        raise ImportError(
            "opensearch-py is not installed. "
            "Run: pip install opensearch-py"
        ) from exc

    host = getattr(settings, 'OPENSEARCH_HOST', 'localhost')
    port = int(getattr(settings, 'OPENSEARCH_PORT', 9200))

    _os_client = OpenSearch(
        hosts=[{'host': host, 'port': port}],
        http_compress=True,
        use_ssl=False,
        verify_certs=False,
        ssl_show_warn=False,
    )
    logger.debug("OpenSearch client initialised — %s:%s", host, port)
    return _os_client


# ── Index management ──────────────────────────────────────────────────────────

def create_indices(client):
    """
    Create zarailink_transactions and zarailink_products indices if they do not
    already exist.  Idempotent — safe to call on every startup.
    """
    for index_name, mapping in [
        (OS_TRANSACTIONS_INDEX, TRANSACTION_MAPPING),
        (OS_PRODUCTS_INDEX, PRODUCT_MAPPING),
    ]:
        if not client.indices.exists(index=index_name):
            client.indices.create(index=index_name, body=mapping)
            logger.info("Created OpenSearch index: %s", index_name)
        else:
            logger.debug("OpenSearch index already exists: %s", index_name)


def _tx_to_doc(tx):
    """Convert a Transaction Django model instance to an OpenSearch document."""
    reporting_date = None
    if tx.reporting_date:
        reporting_date = (
            tx.reporting_date.strftime('%Y-%m-%d')
            if hasattr(tx.reporting_date, 'strftime')
            else str(tx.reporting_date)
        )

    return {
        'id': tx.id,
        'tx_reference': tx.tx_reference or '',
        'reporting_date': reporting_date,
        'trade_type': tx.trade_type or '',
        'hs_code': tx.hs_code or '',
        'product_item_id': tx.product_item_id,
        'subcategory_id': tx.product_item.sub_category_id if tx.product_item_id and hasattr(tx, 'product_item') and tx.product_item else None,
        'seller': tx.seller or '',
        'buyer': tx.buyer or '',
        'shipping_agent': tx.shipping_agent or '',
        'origin_country': tx.origin_country or '',
        'destination_country': tx.destination_country or '',
        'qty_kg': float(tx.qty_kg) if tx.qty_kg is not None else None,
        'qty_mt': float(tx.qty_mt) if tx.qty_mt is not None else None,
        'usd_per_kg': float(tx.usd_per_kg) if tx.usd_per_kg is not None else None,
        'usd_per_mt': float(tx.usd_per_mt) if tx.usd_per_mt is not None else None,
        'pkr': float(tx.pkr) if tx.pkr is not None else None,
        'usd': float(tx.usd) if tx.usd is not None else None,
        'shipment_count': 1,
    }


def index_transaction(client, tx):
    """
    Index a single Transaction Django model instance.

    Args:
        client: OpenSearch client returned by get_os_client()
        tx:     A Transaction model instance.

    Returns:
        The OpenSearch response dict.
    """
    doc = _tx_to_doc(tx)
    response = client.index(
        index=OS_TRANSACTIONS_INDEX,
        id=tx.id,
        body=doc,
        refresh=False,
    )
    return response


def bulk_index_transactions(client, transactions, chunk_size=500):
    """
    Bulk-index an iterable of Transaction model instances.

    Args:
        client:       OpenSearch client returned by get_os_client()
        transactions: Iterable of Transaction model instances.
        chunk_size:   Number of documents per bulk request.

    Returns:
        Tuple (indexed_count, error_count).
    """
    from opensearchpy.helpers import bulk, BulkIndexError

    indexed_count = 0
    error_count = 0
    chunk = []

    def _flush(chunk):
        nonlocal indexed_count, error_count
        if not chunk:
            return
        actions = [
            {
                '_op_type': 'index',
                '_index': OS_TRANSACTIONS_INDEX,
                '_id': doc['id'],
                **doc,
            }
            for doc in chunk
        ]
        try:
            success, errors = bulk(client, actions, stats_only=False, raise_on_error=False)
            indexed_count += success
            error_count += len(errors)
            if errors:
                logger.warning("Bulk index errors (%d): first=%s", len(errors), errors[0])
        except BulkIndexError as exc:
            logger.error("BulkIndexError: %s", exc)
            error_count += len(exc.errors)

    for tx in transactions:
        chunk.append(_tx_to_doc(tx))
        if len(chunk) >= chunk_size:
            _flush(chunk)
            chunk = []

    _flush(chunk)
    return indexed_count, error_count


# ── Search helpers ─────────────────────────────────────────────────────────────

def search_suppliers(
    client,
    subcategory_ids,
    intent='BUY',
    country_filter=None,
    date_from=None,
    date_to=None,
    price_ceiling=None,
    price_floor=None,
    size=100,
):
    """
    Aggregate suppliers (or buyers) from the transactions index.

    For BUY intent  → aggregates on seller.keyword (Pakistan imports from world).
    For SELL intent → aggregates on buyer.keyword  (Pakistan exports to world).

    Returns a list of dicts matching SupplierAggregator output format:
        {name, country, total_volume, avg_price, shipment_count, last_shipment_date}

    Args:
        client:          OpenSearch client.
        subcategory_ids: List of ProductSubCategory IDs (integers) to filter on.
        intent:          'BUY' or 'SELL'.
        country_filter:  List of country strings, or None.
        date_from:       ISO date string 'YYYY-MM-DD', or None.
        date_to:         ISO date string 'YYYY-MM-DD', or None.
        price_ceiling:   Max usd_per_mt, or None.
        price_floor:     Min usd_per_mt, or None.
        size:            Max number of aggregation buckets to return.

    Returns:
        list of supplier/buyer dicts.
    """
    # ── Determine group-by field and trade_type filter ────────────────────────
    if intent == 'SELL':
        agg_field = 'buyer.keyword'
        country_agg_field = 'destination_country'
        trade_type = 'EXPORT'
    else:
        agg_field = 'seller.keyword'
        country_agg_field = 'origin_country'
        trade_type = 'IMPORT'

    # ── Build filter clauses ──────────────────────────────────────────────────
    must_filters = [
        {'term': {'trade_type': trade_type}},
    ]

    if subcategory_ids:
        must_filters.append({'terms': {'subcategory_id': list(subcategory_ids)}})

    if country_filter:
        must_filters.append({'terms': {country_agg_field: list(country_filter)}})

    range_filter = {}
    if date_from:
        range_filter['gte'] = date_from
    if date_to:
        range_filter['lte'] = date_to
    if range_filter:
        must_filters.append({'range': {'reporting_date': range_filter}})

    price_range = {}
    if price_floor is not None:
        price_range['gte'] = float(price_floor)
    if price_ceiling is not None:
        price_range['lte'] = float(price_ceiling)
    if price_range:
        must_filters.append({'range': {'usd_per_mt': price_range}})

    # ── Build aggregation query ───────────────────────────────────────────────
    query = {
        'size': 0,  # no raw hits, aggregations only
        'query': {
            'bool': {
                'filter': must_filters,
            }
        },
        'aggs': {
            'by_counterparty': {
                'terms': {
                    'field': agg_field,
                    'size': size,
                    'order': {'total_volume': 'desc'},
                },
                'aggs': {
                    'total_volume': {'sum': {'field': 'qty_mt'}},
                    'avg_price': {'avg': {'field': 'usd_per_mt'}},
                    'last_shipment_date': {'max': {'field': 'reporting_date'}},
                    'shipment_count': {'value_count': {'field': 'id'}},
                    # Most common country for this counterparty
                    'top_country': {
                        'terms': {
                            'field': country_agg_field,
                            'size': 1,
                        }
                    },
                },
            }
        },
    }

    try:
        response = client.search(index=OS_TRANSACTIONS_INDEX, body=query)
    except Exception as exc:
        logger.error("OpenSearch search_suppliers query failed: %s", exc)
        raise

    buckets = response.get('aggregations', {}).get('by_counterparty', {}).get('buckets', [])

    results = []
    for bucket in buckets:
        name = bucket['key']
        total_volume = bucket['total_volume']['value'] or 0.0
        avg_price = bucket['avg_price']['value'] or 0.0
        shipment_count = bucket['shipment_count']['value'] or 0

        # last_shipment_date comes back as a formatted string when format is set
        last_shipment_raw = bucket['last_shipment_date'].get('value_as_string') or \
                            bucket['last_shipment_date'].get('value')
        last_shipment_date = None
        if last_shipment_raw:
            try:
                from datetime import date
                if isinstance(last_shipment_raw, str):
                    last_shipment_date = date.fromisoformat(last_shipment_raw[:10])
                else:
                    # epoch ms
                    import datetime as dt
                    last_shipment_date = dt.datetime.utcfromtimestamp(
                        last_shipment_raw / 1000
                    ).date()
            except Exception:
                last_shipment_date = None

        # Country: pick the most common one for this counterparty
        country_buckets = bucket.get('top_country', {}).get('buckets', [])
        country = country_buckets[0]['key'] if country_buckets else ''

        results.append({
            'name': name,
            'country': country,
            'total_volume': float(total_volume),
            'avg_price': float(avg_price),
            'shipment_count': int(shipment_count),
            'last_shipment_date': last_shipment_date,
            # Extra fields to be consistent with SupplierAggregator output
            'max_shipment_vol': 0.0,
            'avg_shipment_vol': float(total_volume / shipment_count) if shipment_count else 0.0,
            'type': 'Buyer' if intent == 'SELL' else 'Supplier',
            'volume_score': None,
            'volume_fit': 'N/A',
            '_source': 'opensearch',
        })

    return results


def search_products(client, query_text, top_k=10):
    """
    Full-text search over product names and hs_codes in the products index.

    Args:
        client:     OpenSearch client.
        query_text: Free-text query string.
        top_k:      Max results to return.

    Returns:
        List of dicts: {id, name, hs_code, score}
    """
    query = {
        'size': top_k,
        'query': {
            'multi_match': {
                'query': query_text,
                'fields': ['name^2', 'hs_code'],
                'type': 'best_fields',
                'fuzziness': 'AUTO',
            }
        },
    }

    try:
        response = client.search(index=OS_PRODUCTS_INDEX, body=query)
    except Exception as exc:
        logger.error("OpenSearch search_products query failed: %s", exc)
        raise

    hits = response.get('hits', {}).get('hits', [])
    return [
        {
            'id': hit['_source']['id'],
            'name': hit['_source']['name'],
            'hs_code': hit['_source'].get('hs_code', ''),
            'score': hit['_score'],
        }
        for hit in hits
    ]
