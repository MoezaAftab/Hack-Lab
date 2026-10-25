"""
LabelGuard AI - Before vs After Model Benchmarking Engine
Quantifies performance gains (Accuracy, F1, Confusion Matrix) achieved by data cleansing.
"""

from typing import Dict, Any, Tuple, Optional
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    f1_score,
    balanced_accuracy_score,
    confusion_matrix,
    classification_report,
)


def run_benchmark(
    X_noisy: pd.DataFrame,
    y_noisy: pd.Series,
    X_clean: pd.DataFrame,
    y_clean: pd.Series,
    y_ground_truth: Optional[pd.Series] = None,
    test_size: float = 0.25,
    classifier_name: str = "rf",
    random_state: int = 42,
) -> Dict[str, Any]:
    """
    Train and evaluate models on:
      A) Raw Noisy Data
      B) LabelGuard Healed Data
    Both evaluated on a pristine held-out test set to objectively prove the data quality gain.
    """
    # Create a stratified split based on clean ground truth (or cleanest available)
    eval_target = y_ground_truth if y_ground_truth is not None else y_clean
    train_idx, test_idx = train_test_split(
        np.arange(len(X_noisy)),
        test_size=test_size,
        stratify=eval_target,
        random_state=random_state,
    )

    X_test = X_noisy.iloc[test_idx].to_numpy()
    # Test set evaluated against true labels
    y_test = eval_target.iloc[test_idx].to_numpy().astype(int)

    # 1. Train on Noisy Training Set
    X_train_noisy = X_noisy.iloc[train_idx].to_numpy()
    y_train_noisy = y_noisy.iloc[train_idx].to_numpy().astype(int)

    def get_clf():
        if classifier_name == "gb":
            return GradientBoostingClassifier(n_estimators=100, random_state=random_state)
        elif classifier_name == "lr":
            return LogisticRegression(max_iter=1000, random_state=random_state)
        return RandomForestClassifier(n_estimators=100, random_state=random_state, n_jobs=-1)

    clf_noisy = get_clf()
    clf_noisy.fit(X_train_noisy, y_train_noisy)
    preds_noisy = clf_noisy.predict(X_test)

    acc_noisy = float(accuracy_score(y_test, preds_noisy))
    bacc_noisy = float(balanced_accuracy_score(y_test, preds_noisy))
    f1_noisy = float(f1_score(y_test, preds_noisy, average="macro", zero_division=0))
    cm_noisy = confusion_matrix(y_test, preds_noisy).tolist()

    # 2. Train on Healed Training Set
    # We only take the training indices that remain in X_clean
    valid_train_clean_indices = [i for i in train_idx if i in X_clean.index]
    X_train_clean = X_clean.loc[valid_train_clean_indices].to_numpy()
    y_train_clean = y_clean.loc[valid_train_clean_indices].to_numpy().astype(int)

    clf_clean = get_clf()
    clf_clean.fit(X_train_clean, y_train_clean)
    preds_clean = clf_clean.predict(X_test)

    acc_clean = float(accuracy_score(y_test, preds_clean))
    bacc_clean = float(balanced_accuracy_score(y_test, preds_clean))
    f1_clean = float(f1_score(y_test, preds_clean, average="macro", zero_division=0))
    cm_clean = confusion_matrix(y_test, preds_clean).tolist()

    # Calculate Deltas
    acc_delta = acc_clean - acc_noisy
    bacc_delta = bacc_clean - bacc_noisy
    f1_delta = f1_clean - f1_noisy

    metrics_table = pd.DataFrame(
        {
            "Metric": ["Accuracy", "Balanced Accuracy", "Macro F1-Score"],
            "Noisy Baseline": [
                f"{acc_noisy * 100:.2f}%",
                f"{bacc_noisy * 100:.2f}%",
                f"{f1_noisy * 100:.2f}%",
            ],
            "LabelGuard Healed": [
                f"{acc_clean * 100:.2f}%",
                f"{bacc_clean * 100:.2f}%",
                f"{f1_clean * 100:.2f}%",
            ],
            "Improvement Delta": [
                f"{'+' if acc_delta >= 0 else ''}{acc_delta * 100:.2f}%",
                f"{'+' if bacc_delta >= 0 else ''}{bacc_delta * 100:.2f}%",
                f"{'+' if f1_delta >= 0 else ''}{f1_delta * 100:.2f}%",
            ],
        }
    )

    return {
        "metrics_table": metrics_table,
        "acc_noisy": acc_noisy,
        "acc_clean": acc_clean,
        "acc_delta": acc_delta,
        "f1_noisy": f1_noisy,
        "f1_clean": f1_clean,
        "f1_delta": f1_delta,
        "cm_noisy": cm_noisy,
        "cm_clean": cm_clean,
        "model_noisy": clf_noisy,
        "model_clean": clf_clean,
        "test_size": len(y_test),
        "train_noisy_size": len(y_train_noisy),
        "train_clean_size": len(y_train_clean),
    }
