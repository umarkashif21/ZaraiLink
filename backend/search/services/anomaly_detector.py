"""
backend/search/services/anomaly_detector.py

Statistical anomaly detection for trade price and volume data (Phase 4-A).

Approach:
  - IsolationForest on (price, volume) feature pairs → detects multi-dimensional outliers
  - Prophet on monthly avg_price time-series → detects price anomalies in context of trends
  - Persisted per subcategory to `search/models/anomaly/{subcat_id}.pkl`

Usage:
    detector = TradeAnomalyDetector()
    detector.fit_price_model(subcategory_id=42)
    score = detector.score_company('Nestle Pakistan', subcategory_id=42)
    # → {'pct_suspicious_transactions': 0.05, 'avg_price_deviation': 12.3}
"""

import os
import pickle
import logging
import datetime
import numpy as np
from typing import Optional

logger = logging.getLogger(__name__)

MODEL_DIR = os.path.join(os.path.dirname(__file__), '../models/anomaly')
MIN_TRANSACTIONS = 5    # min transactions to fit a model
IF_CONTAMINATION = 0.1  # expected fraction of anomalies (10%)


# -----------------------------------------------------------------------
# Singleton
# -----------------------------------------------------------------------
_detector_instance: Optional['TradeAnomalyDetector'] = None


def get_anomaly_detector() -> 'TradeAnomalyDetector':
    global _detector_instance
    if _detector_instance is None:
        _detector_instance = TradeAnomalyDetector()
    return _detector_instance


# -----------------------------------------------------------------------
# TradeAnomalyDetector
# -----------------------------------------------------------------------

class TradeAnomalyDetector:
    """
    Detects price and volume anomalies in trade transactions.

    Two models per subcategory:
      1. IsolationForest on (log_price, log_volume) pairs
      2. Prophet on monthly avg_price time-series (optional, for trend context)
    """

    def __init__(self):
        self._models: dict = {}          # subcategory_id → {'iso': model, 'prophet': model}

    # ------------------------------------------------------------------
    # Model persistence
    # ------------------------------------------------------------------

    def _model_path(self, subcategory_id: int) -> str:
        os.makedirs(MODEL_DIR, exist_ok=True)
        return os.path.join(MODEL_DIR, f'anomaly_{subcategory_id}.pkl')

    def _save_model(self, subcategory_id: int, models: dict):
        path = self._model_path(subcategory_id)
        with open(path, 'wb') as f:
            pickle.dump(models, f)

    def _load_model(self, subcategory_id: int) -> Optional[dict]:
        if subcategory_id in self._models:
            return self._models[subcategory_id]
        path = self._model_path(subcategory_id)
        if os.path.exists(path):
            try:
                with open(path, 'rb') as f:
                    models = pickle.load(f)
                self._models[subcategory_id] = models
                return models
            except Exception as e:
                logger.warning(f"Failed to load anomaly model for subcat {subcategory_id}: {e}")
        return None

    # ------------------------------------------------------------------
    # Model fitting
    # ------------------------------------------------------------------

    def fit_price_model(self, subcategory_id: int, dry_run: bool = False) -> bool:
        """
        Fit IsolationForest and Prophet models for a subcategory.

        Args:
            subcategory_id: ProductSubCategory ID
            dry_run:        If True, do not persist models

        Returns:
            True if model was fit successfully.
        """
        try:
            from django.db import connection
            transactions = self._load_transactions(subcategory_id)
        except Exception as e:
            logger.warning(f"Failed to load transactions for subcat {subcategory_id}: {e}")
            return False

        if len(transactions) < MIN_TRANSACTIONS:
            logger.debug(f"Subcat {subcategory_id}: only {len(transactions)} transactions, skip")
            return False

        models = {}

        # 1. IsolationForest on (log_price, log_volume)
        try:
            from sklearn.ensemble import IsolationForest
            prices = np.array([t['price'] for t in transactions if t['price'] > 0])
            volumes = np.array([t['volume'] for t in transactions if t['price'] > 0])

            if len(prices) >= MIN_TRANSACTIONS:
                X = np.column_stack([np.log1p(prices), np.log1p(volumes)])
                iso = IsolationForest(
                    contamination=IF_CONTAMINATION,
                    random_state=42,
                    n_estimators=100,
                )
                iso.fit(X)
                models['iso'] = iso
                models['iso_price_mean'] = float(np.mean(prices))
                models['iso_price_std'] = float(np.std(prices)) or 1.0
                logger.debug(f"Subcat {subcategory_id}: IsolationForest fit on {len(prices)} samples")
        except Exception as e:
            logger.warning(f"IsolationForest fit failed for subcat {subcategory_id}: {e}")

        # 2. Prophet on monthly price time-series
        try:
            monthly = self._monthly_price_series(transactions)
            if len(monthly) >= 6:  # need at least 6 months
                from prophet import Prophet
                import pandas as pd
                df = pd.DataFrame(monthly, columns=['ds', 'y'])
                prophet_model = Prophet(
                    yearly_seasonality=True,
                    weekly_seasonality=False,
                    daily_seasonality=False,
                    interval_width=0.95,
                    changepoint_prior_scale=0.05,
                )
                # Suppress Prophet output
                import logging as _logging
                _logging.getLogger('prophet').setLevel(_logging.WARNING)
                _logging.getLogger('cmdstanpy').setLevel(_logging.WARNING)
                prophet_model.fit(df)
                models['prophet'] = prophet_model
                logger.debug(f"Subcat {subcategory_id}: Prophet fit on {len(monthly)} months")
        except Exception as e:
            logger.debug(f"Prophet fit skipped for subcat {subcategory_id}: {e}")

        if not models:
            return False

        self._models[subcategory_id] = models
        if not dry_run:
            self._save_model(subcategory_id, models)

        return True

    # ------------------------------------------------------------------
    # Scoring
    # ------------------------------------------------------------------

    def score_transaction(self, transaction: dict) -> dict:
        """
        Score a single transaction for anomalousness.

        Args:
            transaction: dict with 'price' (usd_per_mt), 'volume' (qty_mt),
                         'subcategory_id', 'date' (optional)

        Returns:
            {
                'price_anomaly_score': float [0-1],   # 1 = very anomalous
                'volume_anomaly_score': float [0-1],
                'is_suspicious': bool,
            }
        """
        subcat_id = transaction.get('subcategory_id')
        price = float(transaction.get('price') or 0)
        volume = float(transaction.get('volume') or 0)

        result = {
            'price_anomaly_score': 0.0,
            'volume_anomaly_score': 0.0,
            'is_suspicious': False,
        }

        if not subcat_id or price <= 0:
            return result

        models = self._load_model(subcat_id)
        if not models:
            return result

        # IsolationForest score
        iso = models.get('iso')
        if iso and price > 0 and volume > 0:
            try:
                X = np.array([[np.log1p(price), np.log1p(volume)]])
                prediction = iso.predict(X)[0]   # -1 = anomaly, 1 = normal
                score = iso.score_samples(X)[0]  # lower = more anomalous
                # Normalize to [0, 1]: score_samples returns negative values
                price_anomaly = float(np.clip((-score) / 0.5, 0.0, 1.0))
                result['price_anomaly_score'] = price_anomaly
                result['volume_anomaly_score'] = price_anomaly  # same model
                result['is_suspicious'] = bool(prediction == -1)
            except Exception as e:
                logger.debug(f"IsolationForest score error: {e}")

        return result

    def score_company(self, company_name: str, subcategory_id: int) -> dict:
        """
        Aggregate anomaly scores across all transactions for (company, subcategory).

        Returns:
            {
                'pct_suspicious_transactions': float [0-1],
                'avg_price_deviation': float,    # deviation from subcat mean price (%)
                'n_transactions': int,
            }
        """
        result = {
            'pct_suspicious_transactions': 0.0,
            'avg_price_deviation': 0.0,
            'n_transactions': 0,
        }

        try:
            transactions = self._load_company_transactions(company_name, subcategory_id)
        except Exception as e:
            logger.debug(f"Failed to load company transactions: {e}")
            return result

        if not transactions:
            return result

        models = self._load_model(subcategory_id)

        suspicious_count = 0
        price_deviations = []
        price_mean = models.get('iso_price_mean', 0) if models else 0
        price_std = models.get('iso_price_std', 1) if models else 1

        for txn in transactions:
            score = self.score_transaction({
                'price': txn['price'],
                'volume': txn['volume'],
                'subcategory_id': subcategory_id,
            })
            if score['is_suspicious']:
                suspicious_count += 1
            if price_mean > 0 and txn['price'] > 0:
                deviation = abs(txn['price'] - price_mean) / price_mean * 100
                price_deviations.append(deviation)

        n = len(transactions)
        result['pct_suspicious_transactions'] = suspicious_count / n if n > 0 else 0.0
        result['avg_price_deviation'] = float(np.mean(price_deviations)) if price_deviations else 0.0
        result['n_transactions'] = n
        return result

    # ------------------------------------------------------------------
    # DB helpers
    # ------------------------------------------------------------------

    def _load_transactions(self, subcategory_id: int) -> list:
        """Load price+volume transactions for a subcategory."""
        from trade_data.models import Transaction
        txns = (
            Transaction.objects
            .filter(
                product_item__sub_category_id=subcategory_id,
                usd_per_mt__gt=0,
                qty_mt__gt=0,
            )
            .values('usd_per_mt', 'qty_mt', 'reporting_date')
            .order_by('reporting_date')
        )
        return [
            {
                'price': float(t['usd_per_mt']),
                'volume': float(t['qty_mt']),
                'date': t['reporting_date'],
            }
            for t in txns
        ]

    def _load_company_transactions(self, company_name: str, subcategory_id: int) -> list:
        """Load transactions for (company, subcategory)."""
        from trade_data.models import Transaction
        txns = (
            Transaction.objects
            .filter(
                product_item__sub_category_id=subcategory_id,
                usd_per_mt__gt=0,
                qty_mt__gt=0,
            )
            .filter(
                seller__icontains=company_name[:20]
            )
            .values('usd_per_mt', 'qty_mt', 'reporting_date')
        )
        return [
            {'price': float(t['usd_per_mt']), 'volume': float(t['qty_mt'])}
            for t in txns
        ]

    def _monthly_price_series(self, transactions: list) -> list:
        """Aggregate transactions into monthly (date, avg_price) pairs for Prophet."""
        from collections import defaultdict
        monthly = defaultdict(list)
        for t in transactions:
            date = t['date']
            if date:
                month_key = date.replace(day=1)
                monthly[month_key].append(t['price'])

        result = []
        for month, prices in sorted(monthly.items()):
            result.append((month, float(np.mean(prices))))
        return result

    # ------------------------------------------------------------------
    # Batch fitting
    # ------------------------------------------------------------------

    def fit_all(self, verbose: bool = True) -> dict:
        """Fit models for all subcategories with sufficient data."""
        from trade_data.models import ProductSubCategory
        subcats = ProductSubCategory.objects.all().values_list('id', flat=True)
        results = {'fitted': 0, 'skipped': 0, 'errors': 0}
        for subcat_id in subcats:
            try:
                ok = self.fit_price_model(subcat_id)
                if ok:
                    results['fitted'] += 1
                    if verbose:
                        logger.info(f"  Fitted model for subcat {subcat_id}")
                else:
                    results['skipped'] += 1
            except Exception as e:
                results['errors'] += 1
                logger.warning(f"Error fitting model for subcat {subcat_id}: {e}")
        return results
