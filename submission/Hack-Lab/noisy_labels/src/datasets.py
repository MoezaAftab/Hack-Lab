"""
LabelGuard AI - Dataset Management & Noise Injection Engine
Provides benchmark datasets, custom CSV loading, and controllable label noise simulation.
"""

from typing import Tuple, Optional, Dict, Any
import numpy as np
import pandas as pd
from sklearn.datasets import load_breast_cancer, load_wine, load_digits, make_classification
from sklearn.preprocessing import StandardScaler


def load_benchmark_dataset(name: str) -> Tuple[pd.DataFrame, pd.Series, list]:
    """
    Load a standardized benchmark dataset for noise evaluation.
    
    Returns:
        X (pd.DataFrame): Normalized feature matrix.
        y (pd.Series): Integer class labels.
        class_names (list): Human-readable class names.
    """
    name = name.lower()
    if "cancer" in name:
        data = load_breast_cancer()
        X = pd.DataFrame(data.data, columns=data.feature_names)
        y = pd.Series(data.target, name="target")
        class_names = [str(c) for c in data.target_names]
    elif "wine" in name:
        data = load_wine()
        X = pd.DataFrame(data.data, columns=data.feature_names)
        y = pd.Series(data.target, name="target")
        class_names = [f"Class {c}" for c in data.target_names]
    elif "digits" in name:
        data = load_digits()
        X = pd.DataFrame(data.data, columns=[f"pixel_{i}" for i in range(data.data.shape[1])])
        y = pd.Series(data.target, name="target")
        class_names = [f"Digit {c}" for c in range(10)]
    else:
        # Default synthetic classification dataset
        X_arr, y_arr = make_classification(
            n_samples=1000,
            n_features=12,
            n_informative=8,
            n_redundant=2,
            n_classes=3,
            n_clusters_per_class=1,
            random_state=42,
        )
        X = pd.DataFrame(X_arr, columns=[f"feature_{i+1}" for i in range(12)])
        y = pd.Series(y_arr, name="target")
        class_names = ["Alpha", "Beta", "Gamma"]

    return X, y, class_names


def load_custom_csv(file_buffer, label_col: str) -> Tuple[pd.DataFrame, pd.Series, list]:
    """
    Load a user-uploaded CSV file, encode labels, and impute missing values.
    """
    df = pd.read_csv(file_buffer)
    if label_col not in df.columns:
        raise ValueError(f"Label column '{label_col}' not found in uploaded CSV.")

    y_raw = df[label_col]
    X_raw = df.drop(columns=[label_col])

    # Convert non-numeric features to numeric / dummy variables
    X_numeric = pd.get_dummies(X_raw, drop_first=True)
    X_numeric = X_numeric.fillna(X_numeric.median(numeric_only=True))

    # Encode label to integers 0..K-1
    unique_labels = sorted(y_raw.unique())
    label_to_idx = {val: idx for idx, val in enumerate(unique_labels)}
    y = y_raw.map(label_to_idx).astype(int)
    class_names = [str(val) for val in unique_labels]

    return X_numeric, y, class_names


def inject_noise(
    y: pd.Series,
    noise_rate: float = 0.20,
    noise_type: str = "symmetric",
    random_state: int = 42,
) -> Tuple[pd.Series, np.ndarray, Dict[str, Any]]:
    """
    Inject synthetic label noise into a clean target series.
    
    Args:
        y: Clean target series (0..K-1).
        noise_rate: Fraction of labels to corrupt (0.0 to 0.8).
        noise_type: 'symmetric' (random flip) or 'asymmetric' (class-conditional swap).
        random_state: Seed for reproducibility.
        
    Returns:
        noisy_y (pd.Series): Corrupted labels.
        is_corrupted (np.ndarray): Boolean mask of corrupted indices.
        noise_metadata (dict): Summary statistics of injection.
    """
    rng = np.random.RandomState(random_state)
    n_samples = len(y)
    unique_classes = np.unique(y)
    n_classes = len(unique_classes)
    
    y_clean = y.to_numpy().copy()
    noisy_y = y_clean.copy()
    is_corrupted = np.zeros(n_samples, dtype=bool)

    if noise_rate <= 0.0:
        return pd.Series(noisy_y, name=y.name, index=y.index), is_corrupted, {
            "injected_count": 0,
            "actual_noise_rate": 0.0,
            "noise_type": noise_type,
        }

    # Select candidates to corrupt
    num_to_corrupt = int(round(noise_rate * n_samples))
    corrupt_indices = rng.choice(n_samples, size=num_to_corrupt, replace=False)

    if noise_type == "symmetric":
        for idx in corrupt_indices:
            curr_class = y_clean[idx]
            other_classes = [c for c in unique_classes if c != curr_class]
            if other_classes:
                new_class = rng.choice(other_classes)
                noisy_y[idx] = new_class
                is_corrupted[idx] = True
    elif noise_type == "asymmetric":
        # Realistic annotator confusion: class c flips to (c + 1) % n_classes
        for idx in corrupt_indices:
            curr_class = y_clean[idx]
            new_class = (curr_class + 1) % n_classes
            noisy_y[idx] = new_class
            is_corrupted[idx] = True
    else:
        raise ValueError(f"Unknown noise_type '{noise_type}'. Use 'symmetric' or 'asymmetric'.")

    actual_noise_rate = float(np.mean(noisy_y != y_clean))

    metadata = {
        "injected_count": int(np.sum(is_corrupted)),
        "actual_noise_rate": actual_noise_rate,
        "noise_type": noise_type,
    }

    return pd.Series(noisy_y, name=y.name, index=y.index), is_corrupted, metadata
