"""
entity_resolution/similarity.py

Pure-Python string similarity functions for company name matching.
All implementations are from scratch — no jellyfish, rapidfuzz, or difflib.

Functions:
    normalize_company_name(s) -> str
    jaro_winkler(s1, s2)      -> float  [0, 1]
    damerau_levenshtein_normalized(s1, s2) -> float  [0, 1]
    soundex(s)                -> str    (4-char code)
    token_jaccard(s1, s2)     -> float  [0, 1]
"""

import re
import unicodedata


# ---------------------------------------------------------------------------
# Abbreviation expansion table
# ---------------------------------------------------------------------------
_ABBREV = {
    'pvt':   'private',
    'ltd':   'limited',
    '&':     'and',
    'co.':   'company',
    'co':    'company',
    'corp':  'corporation',
    'intl':  'international',
    'mfg':   'manufacturing',
    'inc':   'incorporated',
    'llc':   'limited liability company',
    'plc':   'public limited company',
    'gmbh':  'gesellschaft mit beschrankter haftung',
    'ag':    'aktiengesellschaft',
}

# Soundex digit mapping
_SOUNDEX_TABLE = {
    'b': '1', 'f': '1', 'p': '1', 'v': '1',
    'c': '2', 'g': '2', 'j': '2', 'k': '2', 'q': '2', 's': '2', 'x': '2', 'z': '2',
    'd': '3', 't': '3',
    'l': '4',
    'm': '5', 'n': '5',
    'r': '6',
}
_SOUNDEX_IGNORE = set('aeiouyhw')


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def normalize_company_name(s: str) -> str:
    """
    Normalise a company name for comparison.

    Steps:
      1. Unicode → ASCII
      2. Lowercase
      3. Strip punctuation (. , ( ) / \\ ' " -)
      4. Expand abbreviations
      5. Collapse whitespace
    """
    if not s:
        return ''

    # 1. Unicode → ASCII
    s = unicodedata.normalize('NFKD', s).encode('ascii', 'ignore').decode('ascii')

    # 2. Lowercase
    s = s.lower()

    # 3. Strip punctuation (keep spaces and alphanumerics)
    s = re.sub(r"[.,()\/\\\'\"\-]+", ' ', s)

    # 4. Expand abbreviations — whole-word replacements
    tokens = s.split()
    expanded = []
    for tok in tokens:
        expanded.append(_ABBREV.get(tok, tok))
    s = ' '.join(expanded)

    # 5. Collapse whitespace
    s = re.sub(r'\s+', ' ', s).strip()
    return s


def jaro_winkler(s1: str, s2: str) -> float:
    """
    Jaro-Winkler similarity between two strings.

    Returns float in [0.0, 1.0].
    1.0 = identical, 0.0 = completely dissimilar.

    Algorithm:
      1. Compute Jaro similarity:
         - matching window = floor(max(len(s1), len(s2)) / 2) - 1
         - count matches m (same char within window, not already matched)
         - count transpositions t (matched chars in different order / 2)
         - jaro = (m/|s1| + m/|s2| + (m-t/2)/m) / 3  if m > 0 else 0
      2. Winkler prefix bonus:
         - l = length of common prefix (up to 4)
         - jaro_winkler = jaro + l * p * (1 - jaro),  p = 0.1
    """
    if s1 == s2:
        return 1.0
    if not s1 or not s2:
        return 0.0

    len1, len2 = len(s1), len(s2)
    match_window = max(len1, len2) // 2 - 1
    match_window = max(0, match_window)

    s1_matches = [False] * len1
    s2_matches = [False] * len2

    matches = 0
    transpositions = 0

    # Count matches
    for i in range(len1):
        start = max(0, i - match_window)
        end = min(i + match_window + 1, len2)
        for j in range(start, end):
            if s2_matches[j] or s1[i] != s2[j]:
                continue
            s1_matches[i] = True
            s2_matches[j] = True
            matches += 1
            break

    if matches == 0:
        return 0.0

    # Count transpositions
    k = 0
    for i in range(len1):
        if not s1_matches[i]:
            continue
        while not s2_matches[k]:
            k += 1
        if s1[i] != s2[k]:
            transpositions += 1
        k += 1

    jaro = (matches / len1 + matches / len2 + (matches - transpositions / 2) / matches) / 3

    # Winkler prefix bonus (up to 4 chars, p = 0.1)
    prefix_len = 0
    for i in range(min(4, len1, len2)):
        if s1[i] == s2[i]:
            prefix_len += 1
        else:
            break

    return jaro + prefix_len * 0.1 * (1 - jaro)


def damerau_levenshtein_normalized(s1: str, s2: str) -> float:
    """
    Normalized Damerau-Levenshtein similarity.

    Computes full Damerau-Levenshtein edit distance (allows transpositions),
    then normalizes: similarity = 1 - distance / max(len(s1), len(s2)).

    Returns float in [0.0, 1.0].
    """
    if s1 == s2:
        return 1.0
    if not s1:
        return 0.0
    if not s2:
        return 0.0

    len1, len2 = len(s1), len(s2)

    # DP table: d[i][j] = edit distance between s1[:i] and s2[:j]
    d = [[0] * (len2 + 1) for _ in range(len1 + 1)]

    for i in range(len1 + 1):
        d[i][0] = i
    for j in range(len2 + 1):
        d[0][j] = j

    for i in range(1, len1 + 1):
        for j in range(1, len2 + 1):
            cost = 0 if s1[i - 1] == s2[j - 1] else 1
            d[i][j] = min(
                d[i - 1][j] + 1,        # deletion
                d[i][j - 1] + 1,        # insertion
                d[i - 1][j - 1] + cost, # substitution
            )
            # Transposition
            if i > 1 and j > 1 and s1[i - 1] == s2[j - 2] and s1[i - 2] == s2[j - 1]:
                d[i][j] = min(d[i][j], d[i - 2][j - 2] + cost)

    distance = d[len1][len2]
    max_len = max(len1, len2)
    return 1.0 - distance / max_len


def soundex(s: str) -> str:
    """
    American Soundex code for a string.

    Algorithm:
      1. Keep first letter
      2. Replace consonants with digits (1–6), remove vowels/h/w/y
      3. Remove adjacent duplicate digits
      4. Pad or truncate to 4 characters (letter + 3 digits)

    Returns 4-character code, e.g. "M400" for "Muller".
    """
    if not s:
        return '0000'

    s = s.upper()
    # Keep only ASCII letters
    s = re.sub(r'[^A-Z]', '', s)
    if not s:
        return '0000'

    first_char = s[0]
    code = first_char

    prev_digit = _SOUNDEX_TABLE.get(first_char.lower(), '')

    for ch in s[1:]:
        lower_ch = ch.lower()
        if lower_ch in _SOUNDEX_IGNORE:
            prev_digit = ''  # vowels reset the de-dup check
            continue
        digit = _SOUNDEX_TABLE.get(lower_ch, '')
        if digit and digit != prev_digit:
            code += digit
            if len(code) == 4:
                break
        prev_digit = digit

    # Pad to 4 characters
    code = (code + '000')[:4]
    return code


def token_jaccard(s1: str, s2: str) -> float:
    """
    Token-level Jaccard similarity between two strings.

    Tokenizes on whitespace (after normalization), computes:
        |intersection| / |union|

    Returns float in [0.0, 1.0].
    """
    t1 = set(s1.split())
    t2 = set(s2.split())
    if not t1 and not t2:
        return 1.0
    if not t1 or not t2:
        return 0.0
    intersection = len(t1 & t2)
    union = len(t1 | t2)
    return intersection / union
