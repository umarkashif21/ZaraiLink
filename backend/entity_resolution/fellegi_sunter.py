"""
entity_resolution/fellegi_sunter.py

Fellegi-Sunter EM (Expectation-Maximisation) probabilistic record linkage.

Theory:
  For each comparison field f, we estimate:
    m_f = P(field agrees | records ARE a match)
    u_f = P(field agrees | records are NOT a match)
  Then weight_f = log(m_f / u_f)
  Total score = sum of weights for agreeing fields.
  Score >= MATCH_THRESHOLD   → MATCH
  Score <  NON_MATCH_THRESHOLD → NON_MATCH
  Otherwise                  → UNCERTAIN

EM Algorithm (2-component mixture):
  - Initialize m and u from prior (0.9 / base rate)
  - E-step: compute posterior P(match | agreement vector) for each pair
  - M-step: re-estimate m and u from expected counts
  - Iterate until convergence (delta < tol) or max_iter

Usage:
    from entity_resolution.fellegi_sunter import FellegiSunterEM

    fs = FellegiSunterEM(fields=['name_jw', 'name_jaccard', 'soundex_match'])
    fs.fit(comparison_vectors)          # list of dicts
    labels = fs.predict(comparison_vectors)  # list of 'MATCH'/'NON_MATCH'/'UNCERTAIN'
    scores = fs.score(comparison_vectors)    # list of float
"""

import math
import logging
from typing import List, Dict

logger = logging.getLogger(__name__)

# Default decision thresholds (log-likelihood ratio scale)
DEFAULT_MATCH_THRESHOLD = 2.0
DEFAULT_NON_MATCH_THRESHOLD = -2.0

# Prior probability a random pair is a true match
DEFAULT_PRIOR_MATCH = 0.01


class FellegiSunterEM:
    """
    Two-component mixture EM for Fellegi-Sunter record linkage.

    Each comparison vector is a dict: {field_name: agreement_score}
    where agreement_score is in [0, 1] (continuous or binary).

    For binary fields:  1.0 = agree, 0.0 = disagree.
    For continuous:     values are treated as soft agreement.
    """

    def __init__(
        self,
        fields: List[str],
        match_threshold: float = DEFAULT_MATCH_THRESHOLD,
        non_match_threshold: float = DEFAULT_NON_MATCH_THRESHOLD,
        prior_match: float = DEFAULT_PRIOR_MATCH,
        max_iter: int = 50,
        tol: float = 1e-4,
    ):
        self.fields = fields
        self.match_threshold = match_threshold
        self.non_match_threshold = non_match_threshold
        self.prior_match = prior_match
        self.max_iter = max_iter
        self.tol = tol

        # m[f] = P(agree on f | MATCH),  u[f] = P(agree on f | NON_MATCH)
        self.m: Dict[str, float] = {f: 0.9 for f in fields}
        self.u: Dict[str, float] = {f: 0.1 for f in fields}
        self.fitted = False

    def _log_odds(self, field: str, agree: float) -> float:
        """
        Log-likelihood ratio contribution for one field.
        agree: soft agreement in [0, 1].
        """
        m = self.m[field]
        u = self.u[field]
        eps = 1e-9
        # Soft version: agree * log(m/u) + (1-agree) * log((1-m)/(1-u))
        log_m_u = math.log((m + eps) / (u + eps))
        log_nm_nu = math.log((1 - m + eps) / (1 - u + eps))
        return agree * log_m_u + (1 - agree) * log_nm_nu

    def _total_score(self, vector: dict) -> float:
        """Sum of log-likelihood ratios across all fields."""
        return sum(
            self._log_odds(f, float(vector.get(f, 0.0)))
            for f in self.fields
        )

    def fit(self, vectors: List[dict]) -> 'FellegiSunterEM':
        """
        Fit m and u parameters via EM.

        Args:
            vectors: list of comparison dicts {field: agreement_score}

        Returns:
            self (for chaining)
        """
        if not vectors:
            logger.warning("FellegiSunterEM.fit() called with empty vectors")
            return self

        n = len(vectors)
        lambda_m = self.prior_match  # P(MATCH)

        for iteration in range(self.max_iter):
            old_m = dict(self.m)
            old_u = dict(self.u)

            # E-step: compute posterior P(match | vector) for each pair
            posteriors = []
            for vec in vectors:
                score = self._total_score(vec)
                # Convert log-odds to probability via sigmoid-like formula
                # P(M|x) ∝ lambda_m * prod(m_f^a * (1-m_f)^(1-a))
                # Use log-space for numerical stability
                log_p_match = math.log(lambda_m + 1e-9)
                log_p_nonmatch = math.log(1 - lambda_m + 1e-9)
                for f in self.fields:
                    a = float(vec.get(f, 0.0))
                    log_p_match += a * math.log(self.m[f] + 1e-9) + (1 - a) * math.log(1 - self.m[f] + 1e-9)
                    log_p_nonmatch += a * math.log(self.u[f] + 1e-9) + (1 - a) * math.log(1 - self.u[f] + 1e-9)

                # Normalize
                log_max = max(log_p_match, log_p_nonmatch)
                p_m = math.exp(log_p_match - log_max)
                p_nm = math.exp(log_p_nonmatch - log_max)
                posterior = p_m / (p_m + p_nm)
                posteriors.append(posterior)

            # M-step: re-estimate parameters
            sum_match = sum(posteriors) + 1e-9
            sum_nonmatch = (n - sum(posteriors)) + 1e-9

            for f in self.fields:
                # Expected agreement count among matches / non-matches
                agree_match = sum(
                    float(vec.get(f, 0.0)) * posteriors[i]
                    for i, vec in enumerate(vectors)
                )
                agree_nonmatch = sum(
                    float(vec.get(f, 0.0)) * (1 - posteriors[i])
                    for i, vec in enumerate(vectors)
                )
                self.m[f] = max(0.001, min(0.999, agree_match / sum_match))
                self.u[f] = max(0.001, min(0.999, agree_nonmatch / sum_nonmatch))

            # Update lambda_m
            lambda_m = max(1e-6, min(1 - 1e-6, sum_match / n))

            # Check convergence
            delta = max(
                abs(self.m[f] - old_m[f]) + abs(self.u[f] - old_u[f])
                for f in self.fields
            )
            logger.debug(f"EM iter {iteration + 1}: delta={delta:.6f}, lambda_m={lambda_m:.4f}")
            if delta < self.tol:
                logger.info(f"EM converged after {iteration + 1} iterations")
                break

        self.prior_match = lambda_m
        self.fitted = True
        logger.info(
            f"EM fit complete. m={self.m}, u={self.u}, prior_match={lambda_m:.4f}"
        )
        return self

    def score(self, vectors: List[dict]) -> List[float]:
        """
        Compute log-likelihood ratio score for each comparison vector.

        Higher score = more likely a match.
        """
        return [self._total_score(v) for v in vectors]

    def predict(self, vectors: List[dict]) -> List[str]:
        """
        Classify each comparison vector as MATCH / NON_MATCH / UNCERTAIN.

        Returns:
            list of str: 'MATCH', 'NON_MATCH', or 'UNCERTAIN'
        """
        labels = []
        for score in self.score(vectors):
            if score >= self.match_threshold:
                labels.append('MATCH')
            elif score < self.non_match_threshold:
                labels.append('NON_MATCH')
            else:
                labels.append('UNCERTAIN')
        return labels

    def predict_proba(self, vectors: List[dict]) -> List[float]:
        """
        Return match probability in [0, 1] for each vector.
        Uses sigmoid of the log-likelihood ratio score.
        """
        scores = self.score(vectors)
        return [1 / (1 + math.exp(-s)) for s in scores]

    def fit_predict(self, vectors: List[dict]) -> List[str]:
        """Convenience: fit then predict on the same vectors."""
        self.fit(vectors)
        return self.predict(vectors)

    def summary(self) -> str:
        """Return a human-readable parameter summary."""
        lines = ["FellegiSunterEM parameters:"]
        lines.append(f"  Prior P(match): {self.prior_match:.4f}")
        lines.append(f"  Match threshold: {self.match_threshold}")
        lines.append(f"  Non-match threshold: {self.non_match_threshold}")
        for f in self.fields:
            weight = math.log(self.m[f] / self.u[f]) if self.u[f] > 0 else 0
            lines.append(f"  {f}: m={self.m[f]:.3f}, u={self.u[f]:.3f}, weight={weight:+.3f}")
        return '\n'.join(lines)
