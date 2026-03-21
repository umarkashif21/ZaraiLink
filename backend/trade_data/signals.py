"""
trade_data/signals.py

Post-save signal on Transaction model → invalidates the semantic search cache
so stale results are never served after new trade data lands.
"""

import logging
from django.db.models.signals import post_save
from django.dispatch import receiver

logger = logging.getLogger(__name__)


def _invalidate_search_cache():
    """Clear the semantic cache (best-effort, never raises)."""
    try:
        from search.services.semantic_cache import get_cache
        cache = get_cache()
        cache.flush_all()
        logger.info("Semantic search cache flushed after Transaction post_save")
    except Exception as exc:
        logger.warning(f"Cache invalidation after Transaction save failed (non-fatal): {exc}")


def wire_transaction_signal():
    """
    Lazily import Transaction and connect the post_save signal.
    Called from TradeDataConfig.ready() so that Django's app registry is fully
    loaded before we import any models.
    """
    from trade_data.models import Transaction

    @receiver(post_save, sender=Transaction, weak=False)
    def transaction_post_save(sender, instance, created, **kwargs):
        _invalidate_search_cache()
