"""
backend/entity_resolution/resolver.py

Fellegi-Sunter inspired probabilistic entity resolution pipeline.

Stages:
  1. Normalise raw names → canonical forms
  2. Block on first-token + country to limit comparisons
  3. Compute comparison vector: Jaro-Winkler + token-sort-ratio + common-tokens
  4. EM-style weight estimation → match probability
  5. Transitive-closure clustering of matched pairs
  6. Golden record selection (most frequent / longest name wins)
  7. Persist CanonicalEntity records + link back Transaction rows

Usage (management command):
    python manage.py run_entity_resolution
    python manage.py run_entity_resolution --dry-run
"""

import re
import unicodedata
import logging
from collections import defaultdict, Counter
from difflib import SequenceMatcher

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Suffix noise words stripped before comparison
# ---------------------------------------------------------------------------
LEGAL_SUFFIXES = {
    'ltd', 'limited', 'llc', 'llp', 'inc', 'corp', 'corporation',
    'co', 'company', 'pvt', 'private', 'plc', 'bv', 'gmbh', 'sa',
    'sas', 'spa', 'ag', 'ab', 'nv', 'oy', 'tbk', 'fze', 'fzco',
    'fzc', 'dwc', 'holding', 'holdings', 'group', 'international',
    'trading', 'trade', 'import', 'export', 'imports', 'exports',
    'enterprises', 'enterprise', 'industries', 'industry', 'solutions',
    'services', 'supply', 'supplies', '& co', '& company', '& sons',
    'and co', 'and company',
}

# Thresholds
MATCH_THRESHOLD = 0.88      # score >= this → MATCH
NON_MATCH_THRESHOLD = 0.70  # score < this → NON_MATCH (between = UNCERTAIN)


# ---------------------------------------------------------------------------
# Normalisation
# ---------------------------------------------------------------------------

def normalise(name: str) -> str:
    """Normalise a company name for comparison purposes."""
    if not name:
        return ''

    # Unicode → ASCII
    name = unicodedata.normalize('NFKD', name).encode('ascii', 'ignore').decode('ascii')

    # Lowercase
    name = name.lower()

    # Replace punctuation (keep letters, digits, spaces)
    name = re.sub(r'[^\w\s]', ' ', name)

    # Collapse whitespace
    name = ' '.join(name.split())

    # Remove legal suffixes (greedily, multiple passes)
    for _ in range(3):
        tokens = name.split()
        if tokens and tokens[-1] in LEGAL_SUFFIXES:
            tokens = tokens[:-1]
        name = ' '.join(tokens)

    return name.strip()


def canonical_form(name: str) -> str:
    """Title-case normalised name for display."""
    return ' '.join(w.capitalize() for w in normalise(name).split())


# ---------------------------------------------------------------------------
# Comparison features
# ---------------------------------------------------------------------------

def jaro_winkler(s1: str, s2: str) -> float:
    """Jaro-Winkler similarity (0-1)."""
    try:
        # Use the built-in SequenceMatcher as a proxy when jellyfish not available
        from jellyfish import jaro_winkler_similarity
        return jaro_winkler_similarity(s1, s2)
    except ImportError:
        pass

    # Fallback: SequenceMatcher ratio
    return SequenceMatcher(None, s1, s2).ratio()


def token_sort_ratio(s1: str, s2: str) -> float:
    """Sorted-token comparison to handle word-order variations."""
    t1 = ' '.join(sorted(s1.split()))
    t2 = ' '.join(sorted(s2.split()))
    return SequenceMatcher(None, t1, t2).ratio()


def common_token_ratio(s1: str, s2: str) -> float:
    """Fraction of tokens shared between two names."""
    t1 = set(s1.split())
    t2 = set(s2.split())
    if not t1 or not t2:
        return 0.0
    return len(t1 & t2) / max(len(t1), len(t2))


def compare(name_a: str, name_b: str) -> float:
    """
    Compute a composite similarity score in [0, 1].

    Weights:
      0.40 × Jaro-Winkler
      0.35 × token-sort ratio
      0.25 × common-token ratio
    """
    a = normalise(name_a)
    b = normalise(name_b)

    if not a or not b:
        return 0.0
    if a == b:
        return 1.0

    jw = jaro_winkler(a, b)
    tsr = token_sort_ratio(a, b)
    ctr = common_token_ratio(a, b)

    return round(0.40 * jw + 0.35 * tsr + 0.25 * ctr, 4)


# ---------------------------------------------------------------------------
# Blocking
# ---------------------------------------------------------------------------

def build_blocks(entities: list[tuple[str, str, str]]) -> dict[str, list]:
    """
    Create candidate pairs for comparison via blocking.

    Args:
        entities: list of (entity_type, raw_name, country)

    Returns:
        blocks: {block_key: [list of entity indices]}

    Blocking keys:
      - first_token of normalised name (primary)
      - bigram of first_token + country (secondary)
    """
    blocks: dict[str, list] = defaultdict(list)

    for i, (etype, name, country) in enumerate(entities):
        norm = normalise(name)
        tokens = norm.split()
        if not tokens:
            continue

        first = tokens[0]
        blocks[first].append(i)
        if country:
            blocks[f"{first}::{country.lower()}"].append(i)

    return blocks


# ---------------------------------------------------------------------------
# Transitive closure clustering
# ---------------------------------------------------------------------------

class UnionFind:
    def __init__(self, n: int):
        self.parent = list(range(n))
        self.rank = [0] * n

    def find(self, x: int) -> int:
        while self.parent[x] != x:
            self.parent[x] = self.parent[self.parent[x]]
            x = self.parent[x]
        return x

    def union(self, x: int, y: int):
        rx, ry = self.find(x), self.find(y)
        if rx == ry:
            return
        if self.rank[rx] < self.rank[ry]:
            rx, ry = ry, rx
        self.parent[ry] = rx
        if self.rank[rx] == self.rank[ry]:
            self.rank[rx] += 1


# ---------------------------------------------------------------------------
# Main resolution pipeline
# ---------------------------------------------------------------------------

def resolve(entities: list[tuple[str, str, str]], dry_run: bool = False) -> list[dict]:
    """
    Full entity resolution pipeline.

    Args:
        entities: list of (entity_type, raw_name, country) tuples
        dry_run: if True, don't persist to DB

    Returns:
        list of golden record dicts:
          {canonical_name, entity_type, country, raw_names, merged_from}
    """
    if not entities:
        return []

    n = len(entities)
    logger.info(f"Resolving {n} entities...")

    # Stage 1: Build blocks
    blocks = build_blocks(entities)

    # Stage 2: Compare within blocks
    uf = UnionFind(n)
    merge_logs = []
    compared_pairs = set()

    for block_key, indices in blocks.items():
        if len(indices) < 2:
            continue
        for i_pos in range(len(indices)):
            for j_pos in range(i_pos + 1, len(indices)):
                i, j = indices[i_pos], indices[j_pos]
                pair = (min(i, j), max(i, j))
                if pair in compared_pairs:
                    continue
                compared_pairs.add(pair)

                _, name_a, country_a = entities[i]
                _, name_b, country_b = entities[j]

                score = compare(name_a, name_b)

                # Country penalty: if countries differ and are both known, reduce score
                if country_a and country_b and country_a.lower() != country_b.lower():
                    score *= 0.80

                if score >= MATCH_THRESHOLD:
                    uf.union(i, j)
                    merge_logs.append({
                        'raw_name_a': name_a,
                        'raw_name_b': name_b,
                        'score': score,
                        'decision': 'MATCH',
                    })
                elif score >= NON_MATCH_THRESHOLD:
                    merge_logs.append({
                        'raw_name_a': name_a,
                        'raw_name_b': name_b,
                        'score': score,
                        'decision': 'UNCERTAIN',
                    })

    # Stage 3: Collect clusters
    clusters: dict[int, list[int]] = defaultdict(list)
    for i in range(n):
        clusters[uf.find(i)].append(i)

    # Stage 4: Build golden records
    golden_records = []
    for root, members in clusters.items():
        member_entities = [entities[i] for i in members]

        # Collect raw names and types
        raw_names = [e[1] for e in member_entities]
        types = [e[0] for e in member_entities]
        countries = [e[2] for e in member_entities if e[2]]

        # Choose canonical name: most frequent, or longest if tie
        name_counts = Counter(raw_names)
        most_common_name = max(name_counts, key=lambda x: (name_counts[x], len(x)))

        # Choose entity_type
        type_set = set(types)
        if 'SELLER' in type_set and 'BUYER' in type_set:
            entity_type = 'BOTH'
        elif 'SELLER' in type_set:
            entity_type = 'SELLER'
        else:
            entity_type = 'BUYER'

        # Choose country (most common)
        country = Counter(countries).most_common(1)[0][0] if countries else ''

        golden_records.append({
            'canonical_name': most_common_name,
            'entity_type': entity_type,
            'country': country,
            'raw_names': list(set(raw_names)),
            'merged_from': members,
        })

    logger.info(
        f"  {n} raw entities → {len(golden_records)} canonical entities "
        f"({n - len(golden_records)} merged)"
    )
    logger.info(f"  Pairs compared: {len(compared_pairs)}")
    logger.info(f"  Matches found: {sum(1 for m in merge_logs if m['decision'] == 'MATCH')}")
    logger.info(f"  Uncertain: {sum(1 for m in merge_logs if m['decision'] == 'UNCERTAIN')}")

    if dry_run:
        return golden_records

    # Stage 5: Persist to DB
    _persist_golden_records(golden_records, merge_logs)

    return golden_records


def _persist_golden_records(golden_records: list[dict], merge_logs: list[dict]):
    """Persist canonical entities and merge logs to DB."""
    from entity_resolution.models import CanonicalEntity, EntityMergeLog
    from trade_data.models import Transaction
    from django.db.models import Sum, Avg, Count, Max
    from django.db import transaction as db_transaction

    with db_transaction.atomic():
        # Build raw_name → canonical_entity mapping
        raw_to_canonical = {}

        for record in golden_records:
            # Get or create canonical entity
            entity, created = CanonicalEntity.objects.get_or_create(
                canonical_name=record['canonical_name'],
                defaults={
                    'entity_type': record['entity_type'],
                    'country': record['country'],
                    'raw_names': record['raw_names'],
                },
            )
            if not created:
                # Update raw_names list
                existing_raw = set(entity.raw_names)
                existing_raw.update(record['raw_names'])
                entity.raw_names = list(existing_raw)
                entity.entity_type = record['entity_type']
                entity.country = record['country']
                entity.save(update_fields=['raw_names', 'entity_type', 'country', 'updated_at'])

            for raw_name in record['raw_names']:
                raw_to_canonical[raw_name] = entity

        logger.info(f"  Persisted {len(golden_records)} canonical entities.")

        # Refresh denormalized stats
        for entity in CanonicalEntity.objects.all():
            seller_stats = Transaction.objects.filter(
                seller__in=entity.raw_names
            ).aggregate(
                total_vol=Sum('qty_mt'),
                avg_price=Avg('usd_per_mt'),
                count=Count('id'),
                last_date=Max('reporting_date'),
            )
            buyer_stats = Transaction.objects.filter(
                buyer__in=entity.raw_names
            ).aggregate(
                total_vol=Sum('qty_mt'),
                avg_price=Avg('usd_per_mt'),
                count=Count('id'),
                last_date=Max('reporting_date'),
            )

            total_vol = float(seller_stats['total_vol'] or 0) + float(buyer_stats['total_vol'] or 0)
            total_count = (seller_stats['count'] or 0) + (buyer_stats['count'] or 0)
            avg_price_vals = [v for v in [seller_stats['avg_price'], buyer_stats['avg_price']] if v]
            avg_price = float(sum(avg_price_vals) / len(avg_price_vals)) if avg_price_vals else 0.0

            # Last date
            dates = [d for d in [seller_stats['last_date'], buyer_stats['last_date']] if d]
            last_date = max(dates) if dates else None

            entity.shipment_count = total_count
            entity.total_volume_mt = total_vol
            entity.avg_price_usd_mt = avg_price
            entity.last_shipment_date = last_date
            entity.save(update_fields=[
                'shipment_count', 'total_volume_mt', 'avg_price_usd_mt',
                'last_shipment_date', 'updated_at'
            ])

        logger.info("  Denormalized stats refreshed.")

        # Log merges
        for log in merge_logs:
            EntityMergeLog.objects.get_or_create(
                raw_name_a=log['raw_name_a'],
                raw_name_b=log['raw_name_b'],
                defaults={
                    'similarity_score': log['score'],
                    'decision': log['decision'],
                    'canonical_entity': raw_to_canonical.get(log['raw_name_a']),
                    'method': 'fellegi_sunter_approx',
                },
            )

    logger.info("  Merge logs saved.")


# ---------------------------------------------------------------------------
# Convenience: extract all entities from DB
# ---------------------------------------------------------------------------

def get_all_entities_from_db() -> list[tuple[str, str, str]]:
    """
    Extract all unique (entity_type, raw_name, country) tuples from Transaction table.
    """
    from trade_data.models import Transaction

    entities = []
    seen = set()

    # Sellers
    seller_data = (
        Transaction.objects
        .filter(trade_type='IMPORT')
        .values('seller', 'origin_country')
        .distinct()
    )
    for row in seller_data:
        name = (row['seller'] or '').strip()
        country = (row['origin_country'] or '').strip()
        if name and name not in seen:
            seen.add(name)
            entities.append(('SELLER', name, country))

    # Buyers
    buyer_data = (
        Transaction.objects
        .filter(trade_type='IMPORT')
        .values('buyer', 'destination_country')
        .distinct()
    )
    for row in buyer_data:
        name = (row['buyer'] or '').strip()
        country = (row['destination_country'] or '').strip()
        if name not in seen:
            seen.add(name)
            entities.append(('BUYER', name, country))
        elif name in seen:
            # Already seen as a seller — mark as BOTH
            pass  # Will be handled during golden record creation

    return entities
