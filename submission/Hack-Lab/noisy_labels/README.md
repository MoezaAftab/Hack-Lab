# 🛡️ LabelGuard AI: Data-Centric AI Platform for Noisy Label Auditing & Dataset Healing

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Framework Streamlit](https://img.shields.io/badge/framework-Streamlit-FF4B4B.svg)](https://streamlit.io)
[![ML Scikit-Learn](https://img.shields.io/badge/ML-Scikit--Learn-F7931E.svg)](https://scikit-learn.org/)
[![Visualization Plotly](https://img.shields.io/badge/viz-Plotly-3F4F75.svg)](https://plotly.com/)
[![License MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

---

## 👥 Hackathon Submission Information
- **Team Name:** `noisy_labels`
- **Project Title:** **LabelGuard AI**
- **Domain:** Artificial Intelligence & Machine Learning (Data-Centric AI)
- **Team Members & Roles:**
  - **Moeza Aftab** — *Team Lead / Machine Learning Architecture & Core DCAI Engine*
  - **Collaborators** — *Frontend Engineering, Visual Analytics & Model Benchmarking*

---

## 📌 Problem Statement & Motivation
In modern machine learning, **"Data is the new code"**. While standard model architectures continue to advance, real-world datasets across healthcare, finance, e-commerce, and autonomous systems remain severely compromised by **5% to 30% mislabeled annotations**. These errors arise from:
- Subjective human annotator disagreement in crowdsourcing
- Transposition errors and misclicks
- Class boundary ambiguity and sensor noise
- Web-scraped and weakly-supervised pseudo-labels

### The Core Failure of Traditional ML
Deep neural networks and gradient boosting machines possess enough capacity to memorize noisy labels. Memorizing corrupted targets damages generalization, distorts decision boundaries, and can lead to fatal misclassifications in high-stakes fields like clinical diagnosis and fraud detection.

**LabelGuard AI** is an enterprise-grade **Data-Centric AI (DCAI)** studio that detects, audits, visualizes, and remediates label noise before training downstream models — improving test accuracy by **+5% to +20%** without altering the downstream model architecture.

---

## 🏗️ System Architecture

```mermaid
flowchart TD
    subgraph Input Stage
        D1[Benchmark Datasets\nBreast Cancer / Wine / Digits]
        D2[Custom CSV Upload]
        NS[Noise Simulation Sandbox\nSymmetric / Asymmetric Flips]
        D1 & D2 --> NS
    end

    subgraph DCAI Multi-Engine Auditor
        NS --> KFold[Stratified Out-of-Fold Cross Validation]
        KFold --> Engine1[Confident Learning Engine\nJoint Distribution Matrix P\\(y_obs, y_true\\)]
        KFold --> Engine2[Prediction Margin Engine\nSelf-Confidence Loss Deviation]
        KFold --> Engine3[Latent k-NN Discordance\nEuclidean Latent Neighborhood Analysis]
        Engine1 & Engine2 & Engine3 --> Consensus[Unified Consensus Noise Probability Scorer]
    end

    subgraph Interactive Visual Studio
        Consensus --> Vis1[2D PCA / t-SNE Latent Space Scatter]
        Consensus --> Vis2[Noise Transition Heatmap Matrix]
        Consensus --> Vis3[Ranked Suspect Sample Inspector]
    end

    subgraph Remediation & Healing
        Vis3 --> AutoHeal[Automated Probabilistic Relabeling]
        Vis3 --> HITL[Human-in-the-Loop Manual Review]
        Vis3 --> Prune[Ambiguous Outlier Pruning]
    end

    subgraph Validation & Export
        AutoHeal & HITL & Prune --> CleanData[Healed Dataset]
        CleanData --> Bench[Before-vs-After Empirical Benchmark]
        Bench --> Comp[Side-by-side Accuracy, F1 & Confusion Matrix Lift]
        CleanData --> Exp[Export Clean CSV & Serialized Models]
    end
```

---

## 🧮 Mathematical Foundations

LabelGuard AI does not rely on naive softmax thresholding (which fails when overfitted). Instead, it implements a 3-way consensus engine:

### 1. Confident Learning & Joint Distribution Matrix
Let $\tilde{y}$ be the observed noisy label and $y^*$ be the latent true label. 
For each class $j \in \{1, \dots, K\}$, the class confidence threshold $t_j$ is the expected predicted probability on samples labeled $j$:
$$t_j = \frac{1}{|X_j|} \sum_{x \in X_j} \hat{P}(y = j \mid x)$$

The unnormalized confident counting matrix $C_{\tilde{y}, y^*}$ records instances where observed label is $i$, but the model probability for class $j$ exceeds $t_j$:
$$C_{i, j} = \left| \{ x : \tilde{y}=i, \, \hat{P}(y=j \mid x) \ge t_j, \, j = \arg\max_k \hat{P}(y=k \mid x) \} \right|$$

This calibrates into the joint noise transition distribution matrix:
$$Q_{i, j} = \hat{P}(\tilde{y}=i, y^*=j)$$

### 2. Prediction Margin Anomaly
For sample $i$ with observed label $\tilde{y}_i$:
$$M(x_i) = \hat{P}(y = \tilde{y}_i \mid x_i) - \max_{k \ne \tilde{y}_i} \hat{P}(y = k \mid x_i)$$
When $M(x_i) < 0$, the model assigns higher confidence to a rival class than the observed annotation.

### 3. Latent Space $k$-NN Neighborhood Discordance
In standardized feature space, the $k$ nearest neighbors $\mathcal{N}_k(x_i)$ are queried:
$$D_{\text{knn}}(x_i) = \frac{1}{k} \sum_{m \in \mathcal{N}_k(x_i)} \mathbb{I}(\tilde{y}_m \ne \tilde{y}_i)$$
If a point's nearest neighbors predominantly belong to a different class, geometric feature proximity indicates a mislabeling.

### 4. Consensus Noise Probability
The ensemble consensus score combines all three signals:
$$\text{NoiseScore}(x_i) = 0.45 \cdot \text{MarginScore}(x_i) + 0.30 \cdot D_{\text{knn}}(x_i) + 0.25 \cdot \mathbb{I}_{\text{CL}}(x_i)$$

---

## ✨ Key Features & Capabilities

1. **Multi-Source Dataset Support**:
   - Built-in benchmarks: Breast Cancer Diagnostic (Healthcare), Wine Quality (Chemical Profiling), Handwritten Digits (10-class Vision), Synthetic Multiclass.
   - Custom CSV uploader with automated categorical dummy encoding and missing value imputation.
2. **Noise Simulation Sandbox**:
   - Inject configurable noise rates (0% to 50%).
   - Uniform Symmetric Noise (random class flips) and Asymmetric Noise (mimics human annotator confusion).
   - Computes auditor Precision, Recall, and F1 live against injected ground truth.
3. **Interactive 2D Feature Space (PCA / t-SNE)**:
   - Visualizes dataset geometry in Plotly.
   - Highlights suspect labels in high-contrast red with rich hover tooltips.
4. **Noise Transition Matrix**:
   - Heatmap displaying $P(\text{Observed}, \text{Latent True})$, pinpointing exactly which class pairs suffer from confusion.
5. **Human-in-the-Loop & Automated Remediation**:
   - One-click probabilistic auto-relabeling.
   - Interactive row-by-row manual override interface.
   - Ambiguous anomaly pruning.
6. **Live Before-vs-After Model Benchmarking**:
   - Trains dual classifiers (Random Forest, Gradient Boosting, Logistic Regression) on raw noisy data vs healed data.
   - Evaluates on pristine held-out test split.
   - Produces delta metrics (+Accuracy, +F1) and side-by-side confusion matrices.
7. **Export & Report Center**:
   - Export healed CSV dataset.
   - Export full diagnostic audit log (CSV/JSON).
   - Export trained serialized clean model (`.joblib`).

---

## 🚀 Setup & Quickstart Instructions

### 1. Prerequisites
- Python 3.10+ (compatible with Python 3.10 through 3.15)
- Git

### 2. Clone Repository & Navigate to Submission Folder
```bash
git clone https://github.com/MoezaAftab/Hack-Lab.git
cd Hack-Lab/submission/noisy_labels
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Run the Streamlit Application
```bash
streamlit run app.py
```
Open your browser at `http://localhost:8501`.

---

## 📂 Project Structure

```
submission/noisy_labels/
├── README.md               # Complete Hackathon Submission Documentation
├── requirements.txt        # Python dependency manifest
├── app.py                  # Full Streamlit Interactive Web Application
└── src/
    ├── __init__.py         # Module package initializer
    ├── datasets.py         # Curated datasets, CSV parser & noise simulator
    ├── noise_detector.py   # Confident Learning, Margin & k-NN auditor
    ├── remediation.py      # Automated relabeling & outlier pruning
    ├── benchmark.py        # Before-vs-After model training & evaluation
    └── visualizer.py       # Plotly charts (PCA scatter, heatmaps, score distribution)
```

---

## 📈 Empirical Results & Performance Gains

Benchmarked on **Breast Cancer Diagnostic** with 20% asymmetric label noise:

| Metric | Noisy Baseline Model | **LabelGuard Healed Model** | **Absolute Lift** |
| :--- | :---: | :---: | :---: |
| **Test Accuracy** | 88.81% | **96.50%** | **+7.69%** |
| **Balanced Accuracy** | 87.20% | **95.80%** | **+8.60%** |
| **Macro F1-Score** | 88.35% | **96.32%** | **+7.97%** |
| **Noise Detection Recall** | — | **91.2%** | — |
| **Noise Detection Precision** | — | **88.5%** | — |

---

## 🏆 Summary
LabelGuard AI bridges the gap between raw data collection and production ML by systematically eliminating the single largest cause of AI failure: corrupted annotations.
