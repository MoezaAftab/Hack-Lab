"""
LabelGuard AI - Remediation & Dataset Healing Engine
Applies automated relabeling, outlier pruning, and manual human-in-the-loop overrides.
"""

from typing import Tuple, Dict, Any, Optional
import numpy as np
import pandas as pd


class DatasetHealer:
    """
    Applies data-centric remediation strategies to repair noisy datasets.
    """

    def __init__(
        self,
        relabel_threshold: float = 0.55,
        min_relabel_confidence: float = 0.60,
        prune_unconfident: bool = False,
    ):
        self.relabel_threshold = relabel_threshold
        self.min_relabel_confidence = min_relabel_confidence
        self.prune_unconfident = prune_unconfident

    def heal_dataset(
        self,
        X: pd.DataFrame,
        y: pd.Series,
        audit_df: pd.DataFrame,
        manual_overrides: Optional[Dict[int, int]] = None,
    ) -> Tuple[pd.DataFrame, pd.Series, Dict[str, Any]]:
        """
        Produce a healed (cleaned) dataset using probabilistic relabeling,
        optional pruning of low-confidence ambiguous anomalies, and human overrides.

        Returns:
            X_clean: Cleaned feature DataFrame.
            y_clean: Cleaned integer target Series.
            remediation_summary: Statistics of repairs made.
        """
        y_healed = y.copy()
        mask_keep = np.ones(len(X), dtype=bool)
        relabeled_indices = []
        pruned_indices = []
        manual_applied = 0

        for idx in range(len(X)):
            row = audit_df.iloc[idx]
            noise_score = row["noise_score"]
            sug_prob = row["suggested_label_prob"]
            sug_idx = int(row["suggested_label_idx"])
            given_idx = int(row["given_label_idx"])

            # Check if user provided manual override
            if manual_overrides and idx in manual_overrides:
                y_healed.iloc[idx] = manual_overrides[idx]
                manual_applied += 1
                continue

            # Automated remediation logic
            if noise_score >= self.relabel_threshold:
                if sug_prob >= self.min_relabel_confidence and sug_idx != given_idx:
                    # Confident error -> Auto-relabel to suggested label
                    y_healed.iloc[idx] = sug_idx
                    relabeled_indices.append(idx)
                elif self.prune_unconfident:
                    # Highly noisy but model itself is uncertain -> prune as ambiguous anomaly
                    mask_keep[idx] = False
                    pruned_indices.append(idx)

        X_clean = X.loc[mask_keep].copy()
        y_clean = y_healed.loc[mask_keep].copy()

        summary = {
            "original_samples": len(X),
            "final_samples": len(X_clean),
            "relabeled_count": len(relabeled_indices),
            "pruned_count": len(pruned_indices),
            "manual_overrides_applied": manual_applied,
            "relabeled_indices": relabeled_indices,
            "pruned_indices": pruned_indices,
        }

        return X_clean, y_clean, summary
