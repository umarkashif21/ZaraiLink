"""
entity_resolution/blocking.py

Blocking strategies to reduce O(n²) comparison space.

Functions:
    soundex_blocking(names)           -> dict[str, list[str]]
    first3_blocking(names)            -> dict[str, list[str]]
    sorted_neighborhood(names, W=50)  -> list[tuple[str, str]]

Each function takes a list of (raw_name, entity_id) tuples or just names,
and returns candidate pairs to compare — never the full cross-product.
"""

from entity_resolution.similarity import normalize_company_name, soundex


def soundex_blocking(names: list) -> dict:
    """
    Group company names by their Soundex code.

    Args:
        names: list of str (raw company names), or list of (name, id) tuples.

    Returns:
        dict mapping soundex_code -> list of items (same type as input).

    Example:
        soundex_blocking(["Muller Phipps", "Mueller Phipps", "XYZ Corp"])
        → {"M416": ["Muller Phipps", "Mueller Phipps"], "X261": ["XYZ Corp"]}
    """
    blocks = {}
    for item in names:
        name = item[0] if isinstance(item, (tuple, list)) else item
        normalized = normalize_company_name(name)
        # Take soundex of first token for efficiency
        first_token = normalized.split()[0] if normalized.split() else normalized
        key = soundex(first_token)
        if key not in blocks:
            blocks[key] = []
        blocks[key].append(item)
    return blocks


def first3_blocking(names: list) -> dict:
    """
    Group company names by first 3 characters of normalized name.

    Args:
        names: list of str or list of (name, id) tuples.

    Returns:
        dict mapping first3 -> list of items.
    """
    blocks = {}
    for item in names:
        name = item[0] if isinstance(item, (tuple, list)) else item
        normalized = normalize_company_name(name)
        key = normalized[:3] if len(normalized) >= 3 else normalized.ljust(3, '_')
        if key not in blocks:
            blocks[key] = []
        blocks[key].append(item)
    return blocks


def sorted_neighborhood(names: list, window: int = 50) -> list:
    """
    Sorted Neighborhood Method: sort names alphabetically (after normalization),
    then slide a window of size W over the sorted list and emit all pairs
    within each window position.

    Args:
        names:  list of str or list of (name, id) tuples.
        window: sliding window size (default 50).

    Returns:
        list of (item_a, item_b) candidate pairs — deduplicated.

    Notes:
        - Pairs are deduplicated (canonical order: a < b by position).
        - For n names and window W, produces at most n * (W-1) pairs.
    """
    if not names:
        return []

    # Sort by normalized name
    def sort_key(item):
        name = item[0] if isinstance(item, (tuple, list)) else item
        return normalize_company_name(name)

    sorted_names = sorted(names, key=sort_key)
    n = len(sorted_names)
    pairs = set()

    for i in range(n):
        for j in range(i + 1, min(i + window, n)):
            # Canonical order by index to deduplicate
            pair = (i, j)
            if pair not in pairs:
                pairs.add(pair)

    return [(sorted_names[i], sorted_names[j]) for i, j in sorted(pairs)]


def candidate_pairs_from_blocks(blocks: dict) -> list:
    """
    Generate all candidate pairs within each block.

    Args:
        blocks: dict from any blocking function (key -> list of items).

    Returns:
        list of (item_a, item_b) tuples — deduplicated across blocks.
    """
    seen = set()
    pairs = []

    for key, members in blocks.items():
        n = len(members)
        for i in range(n):
            for j in range(i + 1, n):
                a, b = members[i], members[j]
                # Deduplicate by normalized names
                name_a = a[0] if isinstance(a, (tuple, list)) else a
                name_b = b[0] if isinstance(b, (tuple, list)) else b
                canonical = tuple(sorted([name_a, name_b]))
                if canonical not in seen:
                    seen.add(canonical)
                    pairs.append((a, b))

    return pairs
