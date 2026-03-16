"""
Entity Resolution models.

CanonicalEntity: a de-duplicated, golden-record company entity.
Each unique company (after merging near-duplicates) gets one CanonicalEntity.
"""

from django.db import models


class CanonicalEntity(models.Model):
    """
    Golden record for a company entity.
    """

    ENTITY_TYPES = [
        ('SELLER', 'Seller'),
        ('BUYER', 'Buyer'),
        ('BOTH', 'Both'),
    ]

    canonical_name = models.CharField(max_length=500, unique=True)
    entity_type = models.CharField(max_length=10, choices=ENTITY_TYPES, default='SELLER')
    country = models.CharField(max_length=100, blank=True)

    # All raw string variants that map to this entity
    raw_names = models.JSONField(default=list)

    # Denormalized stats — refreshed by management command
    shipment_count = models.IntegerField(default=0)
    total_volume_mt = models.FloatField(default=0.0)
    avg_price_usd_mt = models.FloatField(default=0.0)
    last_shipment_date = models.DateField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Canonical Entity'
        verbose_name_plural = 'Canonical Entities'
        ordering = ['-shipment_count']
        indexes = [
            models.Index(fields=['canonical_name']),
            models.Index(fields=['entity_type']),
            models.Index(fields=['country']),
        ]

    def __str__(self):
        return f"{self.canonical_name} ({self.entity_type}, {self.country})"


class EntityMergeLog(models.Model):
    """
    Audit trail for entity resolution decisions.
    Allows human review and correction of automated merges.
    """

    DECISION_CHOICES = [
        ('MATCH', 'Match — same entity'),
        ('NON_MATCH', 'Non-match — different entities'),
        ('UNCERTAIN', 'Uncertain — requires human review'),
    ]

    raw_name_a = models.CharField(max_length=500)
    raw_name_b = models.CharField(max_length=500)
    similarity_score = models.FloatField()
    decision = models.CharField(max_length=15, choices=DECISION_CHOICES)
    canonical_entity = models.ForeignKey(
        CanonicalEntity,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='merge_logs',
    )
    method = models.CharField(max_length=50, default='auto')
    reviewed_by_human = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Entity Merge Log'
        verbose_name_plural = 'Entity Merge Logs'
        indexes = [
            models.Index(fields=['decision']),
            models.Index(fields=['reviewed_by_human']),
        ]

    def __str__(self):
        return f"{self.raw_name_a!r} ↔ {self.raw_name_b!r} → {self.decision} ({self.similarity_score:.2f})"
