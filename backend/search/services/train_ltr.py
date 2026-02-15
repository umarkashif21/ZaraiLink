import os
import lightgbm as lgb
import numpy as np
from .ltr_evaluation import evaluate_model

MODEL_PATH = os.path.join(os.path.dirname(__file__), '../models/lgbm_ltr.txt')
os.makedirs(os.path.dirname(MODEL_PATH), exist_ok=True)

class LTRTrainer:
    def train(self):
        print("Building Dataset...")
        from .ltr_dataset_builder import LTRDatasetBuilder
        builder = LTRDatasetBuilder()
        X, y, groups = builder.build_dataset()
        
        print(f"Dataset Built: {len(X)} samples, {len(groups)} queries.")
        
        if len(groups) < 2:
            print("Not enough data to split. Aborting.")
            return

        # Train/Val Split (Group-aware)
        # We must split by GROUPS, not samples, so queries stay intact
        n_queries = len(groups)
        n_train = int(n_queries * 0.8)
        
        # Helper to slice based on groups
        train_groups = groups[:n_train]
        val_groups = groups[n_train:]
        
        n_train_samples = sum(train_groups)
        
        X_train = X[:n_train_samples]
        y_train = y[:n_train_samples]
        
        X_val = X[n_train_samples:]
        y_val = y[n_train_samples:]
        
        print(f"Train Queries: {len(train_groups)}, Val Queries: {len(val_groups)}")
        
        # LightGBM Dataset
        train_data = lgb.Dataset(X_train, label=y_train, group=train_groups)
        val_data = lgb.Dataset(X_val, label=y_val, group=val_groups, reference=train_data)
        
        # Train
        params = {
            'objective': 'lambdarank',
            'metric': 'ndcg',
            'ndcg_eval_at': [5],
            'learning_rate': 0.05,
            'num_leaves': 31,
            'verbose': -1
        }
        
        print("Training LightGBM LambdaRank...")
        callbacks = [
            lgb.early_stopping(stopping_rounds=10),
            lgb.log_evaluation(period=10)
        ]
        model = lgb.train(
            params, 
            train_data, 
            valid_sets=[val_data], 
            num_boost_round=100,
            callbacks=callbacks
        )
        
        # Evaluate
        print("Evaluating Model...")
        metrics = evaluate_model(model, X_val, y_val, val_groups)
        print(f"Validation Metrics: {metrics}")
        
        # Save
        print(f"Saving model to {MODEL_PATH}")
        model.save_model(MODEL_PATH)
        print("Done.")

if __name__ == "__main__":
    import django
    import sys
    
    # Setup Django Environment (since we're running as script)
    # Be careful with paths
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    sys.path.append(base_dir)
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "zarailink.settings") # adjust 'core.settings' if needed
    django.setup()
    
    trainer = LTRTrainer()
    trainer.train()
