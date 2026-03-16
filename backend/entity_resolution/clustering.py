"""
entity_resolution/clustering.py

Transitive closure clustering for entity resolution.

After Fellegi-Sunter classifies pairs as MATCH / NON_MATCH / UNCERTAIN,
this module groups matched pairs into clusters using Union-Find (disjoint sets),
then selects a golden record (canonical representative) per cluster.

Functions:
    transitive_closure(pairs, labels)        -> list[frozenset]
    select_golden_record(cluster, records)   -> str (entity_id or name)
    cluster_entities(pairs, labels, records) -> list[dict]

Classes:
    UnionFind
"""

from typing import List, Dict, Set, Tuple, Optional, Any


# ---------------------------------------------------------------------------
# Union-Find (Disjoint Set Union)
# ---------------------------------------------------------------------------

class UnionFind:
    """
    Disjoint Set Union with path compression and union by rank.

    Supports any hashable element as a node ID.
    Nodes are added lazily on first `find` or `union` call.
    """

    def __init__(self):
        self.parent: Dict[Any, Any] = {}
        self.rank: Dict[Any, int] = {}

    def _make(self, x: Any) -> None:
        """Create a singleton set for x if not already present."""
        if x not in self.parent:
            self.parent[x] = x
            self.rank[x] = 0

    def find(self, x: Any) -> Any:
        """
        Find root of x with path compression.

        Args:
            x: element (auto-created if not present)

        Returns:
            root of the set containing x
        """
        self._make(x)
        if self.parent[x] != x:
            self.parent[x] = self.find(self.parent[x])  # path compression
        return self.parent[x]

    def union(self, x: Any, y: Any) -> None:
        """
        Merge sets containing x and y.

        Uses union by rank to keep trees shallow.
        """
        rx, ry = self.find(x), self.find(y)
        if rx == ry:
            return
        # Union by rank
        if self.rank[rx] < self.rank[ry]:
            rx, ry = ry, rx
        self.parent[ry] = rx
        if self.rank[rx] == self.rank[ry]:
            self.rank[rx] += 1

    def clusters(self) -> List[Set[Any]]:
        """
        Return all clusters as a list of sets.

        Each set contains all elements with the same root.
        Singletons (nodes that were never united) are included.
        """
        from collections import defaultdict
        groups: Dict[Any, Set] = defaultdict(set)
        for node in self.parent:
            root = self.find(node)
            groups[root].add(node)
        return list(groups.values())

    def __len__(self) -> int:
        """Number of distinct elements tracked."""
        return len(self.parent)


# ---------------------------------------------------------------------------
# Transitive Closure
# ---------------------------------------------------------------------------

def transitive_closure(
    pairs: List[Tuple[Any, Any]],
    labels: List[str],
) -> List[frozenset]:
    """
    Group entities into clusters via transitive closure over MATCH pairs.

    Pairs classified as NON_MATCH or UNCERTAIN are ignored.
    Union-Find handles transitivity automatically (A=B, B=C → {A, B, C}).

    Args:
        pairs:  list of (entity_a, entity_b) — same length as labels.
                Each entity can be a str name, int ID, or any hashable.
        labels: list of 'MATCH' / 'NON_MATCH' / 'UNCERTAIN' — same order.

    Returns:
        list of frozenset — each frozenset is one cluster.
        Entities that appear only in NON_MATCH/UNCERTAIN pairs form
        singletons if they appear in at least one pair.

    Example:
        pairs  = [('A','B'), ('B','C'), ('A','D'), ('E','F')]
        labels = ['MATCH',   'MATCH',   'NON_MATCH', 'MATCH']
        → [frozenset({'A','B','C'}), frozenset({'D'}), frozenset({'E','F'})]
        (D is a singleton because its only pair with A was NON_MATCH)
    """
    uf = UnionFind()

    # Register all entities so singletons appear in output
    for a, b in pairs:
        uf._make(a)
        uf._make(b)

    for (a, b), label in zip(pairs, labels):
        if label == 'MATCH':
            uf.union(a, b)

    return [frozenset(c) for c in uf.clusters()]


# ---------------------------------------------------------------------------
# Golden Record Selection
# ---------------------------------------------------------------------------

def select_golden_record(
    cluster: frozenset,
    records: Optional[Dict[Any, dict]] = None,
    prefer_field: str = 'name',
) -> Any:
    """
    Select the canonical (golden) record from a cluster.

    Selection heuristic (in priority order):
      1. If `records` dict is provided, prefer the record with the most
         non-null fields (most complete record).
      2. Among equally complete records, prefer the longest value of
         `prefer_field` (usually the most expanded form of a name).
      3. Fallback: alphabetically smallest entity_id / name.

    Args:
        cluster:      frozenset of entity identifiers.
        records:      optional dict mapping entity_id -> record dict.
                      If None, selection falls back to heuristic 3 only.
        prefer_field: field name used as tiebreaker (default: 'name').

    Returns:
        The selected entity_id (same type as elements in cluster).
    """
    if not cluster:
        raise ValueError("Cannot select golden record from empty cluster")

    if len(cluster) == 1:
        return next(iter(cluster))

    if records is None:
        # Fallback: return lexicographically smallest element
        try:
            return min(cluster, key=lambda x: (str(x).lower(), str(x)))
        except TypeError:
            return min(cluster, key=str)

    def completeness_score(entity_id: Any) -> Tuple[int, int, str]:
        rec = records.get(entity_id, {})
        non_null = sum(1 for v in rec.values() if v is not None and v != '')
        field_len = len(str(rec.get(prefer_field, '')))
        # Negate for max-sort: higher completeness → less negative → selected first
        return (non_null, field_len, str(entity_id))

    return max(cluster, key=completeness_score)


# ---------------------------------------------------------------------------
# High-Level Orchestrator
# ---------------------------------------------------------------------------

def cluster_entities(
    pairs: List[Tuple[Any, Any]],
    labels: List[str],
    records: Optional[Dict[Any, dict]] = None,
    prefer_field: str = 'name',
) -> List[dict]:
    """
    Full pipeline: transitive closure → golden record selection.

    Args:
        pairs:        list of (entity_a, entity_b) candidate pairs.
        labels:       list of 'MATCH'/'NON_MATCH'/'UNCERTAIN' for each pair.
        records:      optional {entity_id: record_dict} for golden selection.
        prefer_field: field name for golden selection tiebreaker.

    Returns:
        list of dicts, one per cluster:
        {
            'golden':   <golden entity_id>,
            'members':  [<entity_id>, ...],  # sorted list
            'size':     int,
        }

    Example:
        pairs  = [('A','B'), ('B','C')]
        labels = ['MATCH', 'MATCH']
        cluster_entities(pairs, labels)
        → [{'golden': 'A', 'members': ['A','B','C'], 'size': 3}]
    """
    clusters = transitive_closure(pairs, labels)
    result = []
    for cluster in clusters:
        golden = select_golden_record(cluster, records=records, prefer_field=prefer_field)
        try:
            members = sorted(cluster, key=str)
        except TypeError:
            members = list(cluster)
        result.append({
            'golden': golden,
            'members': members,
            'size': len(cluster),
        })
    # Sort by cluster size descending for readability
    result.sort(key=lambda x: -x['size'])
    return result
