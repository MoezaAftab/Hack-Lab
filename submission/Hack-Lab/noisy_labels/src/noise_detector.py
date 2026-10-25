"""
LabelGuard AI - Multi-Engine Label Noise Detection & Auditing
Implements Confident Learning, Prediction Margin Anomaly, and Latent k-NN Discordance.
"""

from typing import Dict, Any, Tuple, Optional
import numpy as np
import pandas as pd
from sklearn.model_selection import StratifiedKFold
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.neighbors import NearestNeighbors
from sklearn.preprocessing import StandardScaler


class LabelNoiseAuditor:
    """
    State-of-the-art multi-engine label noise detector and dataset auditor.
    """

    def __init__(
        self,
        n_splits: int = 5,
        base_model_type: str = "rf",
        knn_neighbors: int = 10,
        random_state: int = 42,
    ):
        self.n_splits = n_splits
        self.base_model_type = base_model_type
        self.knn_neighbors = knn_neighbors
        self.random_state = random_state

        self.oof_probs: Optional[np.ndarray] = None
        self.class_thresholds: Optional[np.ndarray] = None
        self.joint_distribution: Optional[np.ndarray] = None
        self.results_df: Optional[pd.DataFrame] = None
        self.classes_: Optional[np.ndarray] = None

    def _get_model(self):
        if self.base_model_type == "lr":
            return LogisticRegression(max_iter=1000, random_state=self.random_state)
        return RandomForestClassifier(
            n_estimators=100,
            max_depth=12,
            min_samples_split=4,
            random_state=self.random_state,
            n_jobs=-1,
        )

    def fit_audit(
        self,
        X: pd.DataFrame,
        y: pd.Series,
        class_names: Optional[list] = None,
    ) -> pd.DataFrame:
        """
        Runs out-of-fold cross validation, computes Confident Learning joint distribution,
        prediction margin anomaly, and k-NN semantic discordance.
        """
        X_arr = np.nan_to_num(X.to_numpy(), nan=0.0)
        y_arr = y.to_numpy().astype(int)
        n_samples = len(y_arr)
        unique_classes = np.sort(np.unique(y_arr))
        n_classes = len(unique_classes)
        self.classes_ = unique_classes

        if class_names is None:
            class_names = [f"Class {c}" for c in unique_classes]

        # -------------------------------------------------------------
        # 1. Out-of-Fold (OOF) Probability Estimation via Stratified K-Fold
        # -------------------------------------------------------------
        oof_probs = np.zeros((n_samples, n_classes), dtype=float)
        skf = StratifiedKFold(
            n_splits=min(self.n_splits, n_samples // n_classes),
            shuffle=True,
            random_state=self.random_state,
        )

        for train_idx, val_idx in skf.split(X_arr, y_arr):
            X_train, y_train = X_arr[train_idx], y_arr[train_idx]
            X_val = X_arr[val_idx]

            model = self._get_model()
            model.fit(X_train, y_train)
            probs = model.predict_proba(X_val)

            # Ensure all classes align
            for col_idx, cls in enumerate(model.classes_):
                c_idx = np.where(unique_classes == cls)[0][0]
                oof_probs[val_idx, c_idx] = probs[:, col_idx]

        self.oof_probs = oof_probs

        # -------------------------------------------------------------
        # 2. Confident Learning: Thresholds & Joint Distribution
        # -------------------------------------------------------------
        # Threshold t_j = average predicted probability for class j on samples labeled j
        class_thresholds = np.zeros(n_classes, dtype=float)
        for j in range(n_classes):
            idx_j = np.where(y_arr == j)[0]
            if len(idx_j) > 0:
                class_thresholds[j] = float(np.mean(oof_probs[idx_j, j]))
            else:
                class_thresholds[j] = 1.0 / n_classes
        self.class_thresholds = class_thresholds

        # Unnormalized confident counting matrix C[i, j]
        # Observed label is i, but predicted probability for j exceeds threshold t_j
        C_matrix = np.zeros((n_classes, n_classes), dtype=int)
        cl_is_error = np.zeros(n_samples, dtype=bool)

        for i in range(n_samples):
            obs = y_arr[i]
            # Classes whose probability exceeds their threshold
            candidate_classes = [
                j for j in range(n_classes) if oof_probs[i, j] >= class_thresholds[j]
            ]
            if candidate_classes:
                # Pick the class with highest probability among candidates
                pred_true = max(candidate_classes, key=lambda c: oof_probs[i, c])
                C_matrix[obs, pred_true] += 1
                if pred_true != obs:
                    cl_is_error[i] = True
            else:
                pred_true = int(np.argmax(oof_probs[i]))
                if pred_true != obs and oof_probs[i, pred_true] > 0.5:
                    cl_is_error[i] = True

        # Normalized Joint Distribution Matrix Q[i, j] = P(given=i, true=j)
        row_sums = C_matrix.sum(axis=1, keepdims=True)
        row_sums[row_sums == 0] = 1
        cond_probs = C_matrix / row_sums
        class_priors = np.array([np.mean(y_arr == c) for c in range(n_classes)])
        Q_matrix = cond_probs * class_priors[:, None]
        if Q_matrix.sum() > 0:
            Q_matrix = Q_matrix / Q_matrix.sum()
        self.joint_distribution = Q_matrix

        # -------------------------------------------------------------
        # 3. Prediction Margin & Self-Confidence Loss Deviation
        # -------------------------------------------------------------
        given_probs = oof_probs[np.arange(n_samples), y_arr]
        suggested_labels = np.argmax(oof_probs, axis=1)
        suggested_probs = np.max(oof_probs, axis=1)

        # Margin: given_prob - max_rival_prob
        rival_probs = np.zeros(n_samples, dtype=float)
        for i in range(n_samples):
            obs = y_arr[i]
            rival_mask = np.ones(n_classes, dtype=bool)
            rival_mask[obs] = False
            rival_probs[i] = np.max(oof_probs[i, rival_mask]) if np.any(rival_mask) else 0.0

        margins = given_probs - rival_probs  # in [-1, 1], negative means rival is higher
        margin_noise_score = np.clip(1.0 - (margins + 1.0) / 2.0, 0.0, 1.0)

        # -------------------------------------------------------------
        # 4. Latent Space k-NN Neighborhood Dissimilarity
        # -------------------------------------------------------------
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X_arr)
        k_val = min(self.knn_neighbors, n_samples - 1)
        knn = NearestNeighbors(n_neighbors=k_val + 1, metric="euclidean", n_jobs=-1)
        knn.fit(X_scaled)
        indices = knn.kneighbors(X_scaled, return_distance=False)

        knn_discordance = np.zeros(n_samples, dtype=float)
        for i in range(n_samples):
            neighbor_indices = indices[i, 1:]  # exclude self
            neighbor_labels = y_arr[neighbor_indices]
            # Fraction of neighbors having a DIFFERENT label than sample's given label
            discordant_count = np.sum(neighbor_labels != y_arr[i])
            knn_discordance[i] = discordant_count / len(neighbor_indices)

        # -------------------------------------------------------------
        # 5. Ensemble Consensus Noise Scoring & Ranking
        # -------------------------------------------------------------
        # Weighted combination:
        # 45% Margin Score + 30% k-NN Discordance + 25% Confident Learning indicator
        cl_numeric = cl_is_error.astype(float)
        consensus_score = (
            0.45 * margin_noise_score
            + 0.30 * knn_discordance
            + 0.25 * cl_numeric
        )
        consensus_score = np.clip(consensus_score, 0.0, 1.0)

        # Assemble comprehensive diagnostics dataframe
        results = pd.DataFrame(
            {
                "row_index": np.arange(n_samples),
                "given_label_idx": y_arr,
                "given_label": [class_names[c] for c in y_arr],
                "suggested_label_idx": suggested_labels,
                "suggested_label": [class_names[c] for c in suggested_labels],
                "given_label_prob": np.round(given_probs, 4),
                "suggested_label_prob": np.round(suggested_probs, 4),
                "prediction_margin": np.round(margins, 4),
                "knn_discordance": np.round(knn_discordance, 4),
                "cl_error_flag": cl_is_error,
                "noise_score": np.round(consensus_score, 4),
            },
            index=X.index,
        )

        results["is_suspect"] = (results["noise_score"] >= 0.50) | (results["cl_error_flag"])
        results = results.sort_values(by="noise_score", ascending=False)
        results["suspect_rank"] = np.arange(1, n_samples + 1)
        self.results_df = results.sort_index()

        return self.results_df

    def get_summary_metrics(self) -> Dict[str, Any]:
        """
        Returns high-level audit summary metrics.
        """
        if self.results_df is None:
            raise ValueError("Auditor has not been fitted yet. Call fit_audit first.")

        df = self.results_df
        total = len(df)
        suspects = int(df["is_suspect"].sum())
        cl_errors = int(df["cl_error_flag"].sum())
        high_discord = int((df["knn_discordance"] >= 0.70).sum())
        avg_score = float(df["noise_score"].mean())

        return {
            "total_samples": total,
            "suspect_count": suspects,
            "suspect_percentage": round((suspects / total) * 100, 2),
            "cl_errors": cl_errors,
            "high_knn_discordance": high_discord,
            "mean_noise_score": round(avg_score, 3),
        }
