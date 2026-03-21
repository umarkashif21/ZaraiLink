from django.db import models
from django.conf import settings


class SearchInteractionLog(models.Model):
    """
    Logs every search query for offline analysis, LTR retraining, and A/B testing.

    Written asynchronously (best-effort) after each search response is returned.
    """

    # Who searched
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='search_logs',
        db_index=True,
    )
    session_key = models.CharField(max_length=64, blank=True, default='')

    # What was searched
    query_text = models.TextField()
    query_family = models.SmallIntegerField(null=True, blank=True)
    parsed_intent = models.CharField(max_length=16, blank=True, default='')
    parsed_product = models.CharField(max_length=256, blank=True, default='')
    parsed_country = models.CharField(max_length=128, blank=True, default='')

    # Result metadata
    result_count = models.IntegerField(default=0)
    cache_hit = models.BooleanField(default=False)

    # Performance
    latency_ms = models.FloatField(null=True, blank=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Search Interaction Log'
        verbose_name_plural = 'Search Interaction Logs'
        indexes = [
            models.Index(fields=['created_at', 'query_family']),
        ]

    def __str__(self):
        return f"[F{self.query_family}] {self.query_text[:60]} ({self.result_count} results)"
