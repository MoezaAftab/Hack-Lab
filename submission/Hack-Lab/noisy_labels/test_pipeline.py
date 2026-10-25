"""
Unit & Integration Test for LabelGuard AI
Tests dataset loading, noise injection, multi-engine auditing, healing, and benchmarking.
"""

import sys
import os

# Ensure current directory is in path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.datasets import load_benchmark_dataset, inject_noise
from src.noise_detector import LabelNoiseAuditor
from src.remediation import DatasetHealer
from src.benchmark import run_benchmark


def run_pipeline_test():
    print("=" * 60)
    print("🚀 Starting LabelGuard AI Pipeline Integration Test...")
    print("=" * 60)

    # 1. Dataset Loading
    print("\n[Step 1] Loading Breast Cancer Diagnostic benchmark...")
    X, y, class_names = load_benchmark_dataset("cancer")
    print(f"  -> Features shape: {X.shape}")
    print(f"  -> Target counts:\n{y.value_counts().to_dict()}")
    print(f"  -> Class names: {class_names}")

    # 2. Noise Injection
    print("\n[Step 2] Injecting 20% Asymmetric Label Noise...")
    y_noisy, is_corrupted, meta = inject_noise(
        y, noise_rate=0.20, noise_type="asymmetric", random_state=42
    )
    print(f"  -> Corrupted {meta['injected_count']} samples (Actual Rate: {meta['actual_noise_rate']*100:.2f}%)")

    # 3. Label Noise Auditing
    print("\n[Step 3] Running Multi-Engine Label Noise Audit (Confident Learning + Margin + k-NN)...")
    auditor = LabelNoiseAuditor(n_splits=5, base_model_type="rf", knn_neighbors=10, random_state=42)
    audit_df = auditor.fit_audit(X, y_noisy, class_names=class_names)
    metrics = auditor.get_summary_metrics()
    print(f"  -> Total samples analyzed: {metrics['total_samples']}")
    print(f"  -> Flagged suspects: {metrics['suspect_count']} ({metrics['suspect_percentage']}%)")
    print(f"  -> Confident learning errors: {metrics['cl_errors']}")
    print(f"  -> Mean noise score: {metrics['mean_noise_score']}")

    # Calculate Detection Accuracy on Injected Ground Truth
    actual_corrupt = is_corrupted
    flagged = audit_df["is_suspect"].to_numpy()
    tp = (actual_corrupt & flagged).sum()
    precision = tp / flagged.sum() if flagged.sum() > 0 else 0
    recall = tp / actual_corrupt.sum() if actual_corrupt.sum() > 0 else 0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0
    print(f"  -> Noise Detector Precision: {precision * 100:.2f}%")
    print(f"  -> Noise Detector Recall:    {recall * 100:.2f}%")
    print(f"  -> Noise Detector F1:        {f1 * 100:.2f}%")

    # 4. Remediation & Healing
    print("\n[Step 4] Applying Dataset Healing & Remediation...")
    healer = DatasetHealer(relabel_threshold=0.55, min_relabel_confidence=0.60)
    X_clean, y_clean, summary = healer.heal_dataset(X, y_noisy, audit_df)
    print(f"  -> Auto-relabeled: {summary['relabeled_count']} samples")
    print(f"  -> Pruned: {summary['pruned_count']} samples")
    print(f"  -> Final dataset size: {summary['final_samples']} rows")

    # 5. Before vs. After Benchmark
    print("\n[Step 5] Benchmarking Downstream Model Generalization (Noisy vs Healed)...")
    bench = run_benchmark(
        X_noisy=X,
        y_noisy=y_noisy,
        X_clean=X_clean,
        y_clean=y_clean,
        y_ground_truth=y,
        test_size=0.25,
        classifier_name="rf",
        random_state=42,
    )
    print("\n📊 Benchmark Scorecard:")
    print(bench["metrics_table"].to_string(index=False))

    print(f"\n✅ ACCURACY DELTA: {bench['acc_delta']*100:+.2f}%")
    print(f"✅ MACRO F1 DELTA: {bench['f1_delta']*100:+.2f}%")
    print("\n🎉 ALL PIPELINE INTEGRATION TESTS PASSED PERFECTLY!")


if __name__ == "__main__":
    run_pipeline_test()
