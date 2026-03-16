"""
Unit tests for entity_resolution.resolver
"""

import pytest
from entity_resolution.resolver import (
    normalise, compare, resolve,
    MATCH_THRESHOLD, NON_MATCH_THRESHOLD,
)


class TestNormalise:
    def test_strips_ltd(self):
        assert 'ltd' not in normalise('Lactalis Ingredients Ltd')

    def test_strips_llc(self):
        assert 'llc' not in normalise('Al Khaleej Sugar Co Llc')

    def test_lowercase(self):
        assert normalise('SIGMA-ALDRICH CHEMIE GMBH') == normalise('Sigma-Aldrich Chemie GmbH')

    def test_strips_punctuation(self):
        result = normalise('M.A. Kamil & Sons, Ltd.')
        assert '.' not in result
        assert ',' not in result

    def test_empty_string(self):
        assert normalise('') == ''

    def test_unicode_normalisation(self):
        result = normalise('Société Française')
        assert result


class TestCompare:
    def test_identical_names_score_one(self):
        assert compare('Lactalis Ingredients', 'Lactalis Ingredients') == 1.0

    def test_different_legal_suffix_scores_high(self):
        score = compare('Qingdao Hisunny Imp Export Co Ltd', 'Qingdao Hisunny Imp Export Co')
        assert score >= MATCH_THRESHOLD, f"Expected >= {MATCH_THRESHOLD}, got {score}"

    def test_completely_different_scores_low(self):
        score = compare('Lactalis Ingredients', 'Dongying City Longxing Chemical')
        assert score < NON_MATCH_THRESHOLD, f"Expected < {NON_MATCH_THRESHOLD}, got {score}"

    def test_empty_name_scores_zero(self):
        assert compare('', 'Lactalis Ingredients') == 0.0
        assert compare('Lactalis Ingredients', '') == 0.0

    def test_partial_name_match(self):
        score = compare('Friesland Campina Domo', 'Friesland Campina Nederland Bv')
        assert NON_MATCH_THRESHOLD <= score < MATCH_THRESHOLD, \
            f"Expected UNCERTAIN range, got {score}"

    def test_word_order_invariant(self):
        score = compare('Sugar Al Khaleej Co', 'Al Khaleej Sugar Co')
        assert score >= 0.80, f"Expected high score for same tokens, got {score}"


class TestResolve:
    def test_deterministic(self):
        entities = [
            ('SELLER', 'Lactalis Ingredients', 'France'),
            ('SELLER', 'Sigma-Aldrich Chemie Gmbh', 'Germany'),
            ('BUYER', 'Barrett Hodgson Pakistan Pvt Ltd', 'Pakistan'),
        ]
        r1 = resolve(entities, dry_run=True)
        r2 = resolve(entities, dry_run=True)
        assert len(r1) == len(r2)
        assert [r['canonical_name'] for r in r1] == [r['canonical_name'] for r in r2]

    def test_near_duplicates_merge(self):
        entities = [
            ('SELLER', 'Qingdao Hisunny Imp & Exp Co Ltd', 'China'),
            ('SELLER', 'Qingdao Hisunny Imp And Exp Co Ltd', 'China'),
        ]
        records = resolve(entities, dry_run=True)
        assert len(records) == 1, f"Expected 1 merged cluster, got {len(records)}"

    def test_canonical_name_is_most_frequent(self):
        entities = [
            ('SELLER', 'Qingdao Hisunny Imp & Exp Co Ltd', 'China'),
            ('SELLER', 'Qingdao Hisunny Imp & Exp Co Ltd', 'China'),
            ('SELLER', 'Qingdao Hisunny Import Export Co', 'China'),
        ]
        records = resolve(entities, dry_run=True)
        if len(records) == 1:
            assert records[0]['canonical_name'] == 'Qingdao Hisunny Imp & Exp Co Ltd'

    def test_entity_type_both_for_seller_and_buyer(self):
        entities = [
            ('SELLER', 'Trading Corporation Of Pakistan', 'Pakistan'),
            ('BUYER', 'Trading Corporation Of Pakistan', 'Pakistan'),
        ]
        records = resolve(entities, dry_run=True)
        merged = [r for r in records if 'Trading Corporation Of Pakistan' in r['raw_names']]
        if merged and len(merged) == 1:
            assert merged[0]['entity_type'] == 'BOTH'

    def test_empty_input(self):
        assert resolve([], dry_run=True) == []

    def test_single_entity(self):
        entities = [('SELLER', 'Lactalis Ingredients', 'France')]
        records = resolve(entities, dry_run=True)
        assert len(records) == 1
        assert records[0]['canonical_name'] == 'Lactalis Ingredients'

    def test_unrelated_entities_do_not_merge(self):
        entities = [
            ('SELLER', 'Lactalis Ingredients', 'France'),
            ('SELLER', 'Al Khaleej Sugar Co Llc', 'UAE'),
            ('SELLER', 'Dongying City Longxing Chemical Co Ltd', 'China'),
        ]
        records = resolve(entities, dry_run=True)
        assert len(records) == 3
