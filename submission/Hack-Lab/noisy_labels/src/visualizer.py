"""
LabelGuard AI - Visualization & Interactive Plotting Engine
Generates interactive Plotly visualizations for 2D latent projections,
noise transition matrices, suspect distributions, and benchmark comparisons.
"""

from typing import List, Optional
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler


def plot_latent_space(
    X: pd.DataFrame,
    audit_df: pd.DataFrame,
    class_names: List[str],
) -> go.Figure:
    """
    Project feature space down to 2D via PCA and highlight suspected noisy labels.
    """
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(np.nan_to_num(X.to_numpy(), nan=0.0))
    pca = PCA(n_components=2, random_state=42)
    coords = pca.fit_transform(X_scaled)

    var_explained = pca.explained_variance_ratio_ * 100

    plot_df = audit_df.copy()
    plot_df["PCA 1"] = coords[:, 0]
    plot_df["PCA 2"] = coords[:, 1]
    plot_df["Status"] = np.where(plot_df["is_suspect"], "🚨 Suspect Error", "✅ Clean / Trustworthy")

    fig = px.scatter(
        plot_df,
        x="PCA 1",
        y="PCA 2",
        color="Status",
        color_discrete_map={
            "🚨 Suspect Error": "#FF2B2B",
            "✅ Clean / Trustworthy": "#00CC96",
        },
        symbol="Status",
        symbol_map={
            "🚨 Suspect Error": "x",
            "✅ Clean / Trustworthy": "circle",
        },
        hover_data={
            "row_index": True,
            "given_label": True,
            "suggested_label": True,
            "noise_score": ":.3f",
            "prediction_margin": ":.3f",
            "knn_discordance": ":.3f",
            "PCA 1": False,
            "PCA 2": False,
            "Status": False,
        },
        title=f"2D Latent Feature Space (PCA Exp Var: {var_explained[0]:.1f}% + {var_explained[1]:.1f}%)",
    )

    fig.update_traces(marker=dict(size=8, opacity=0.85, line=dict(width=1, color="DarkSlateGrey")))
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(14, 17, 23, 0.95)",
        plot_bgcolor="rgba(14, 17, 23, 0.95)",
        font=dict(family="sans-serif", size=12, color="#E0E0E0"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        margin=dict(l=40, r=40, t=60, b=40),
    )
    return fig


def plot_noise_transition_matrix(
    joint_matrix: np.ndarray,
    class_names: List[str],
) -> go.Figure:
    """
    Heatmap of joint distribution matrix P(observed label, latent true label).
    """
    fig = go.Figure(
        data=go.Heatmap(
            z=np.round(joint_matrix * 100, 2),
            x=[f"Pred: {c}" for c in class_names],
            y=[f"Obs: {c}" for c in class_names],
            colorscale="Viridis",
            text=np.round(joint_matrix * 100, 1),
            texttemplate="%{text}%",
            hoverongaps=False,
            colorbar=dict(title="% of Total"),
        )
    )

    fig.update_layout(
        title="Joint Noise Transition Matrix P(Observed, Latent True)",
        xaxis_title="Latent Model Consensus Label",
        yaxis_title="Dataset Observed Label",
        template="plotly_dark",
        paper_bgcolor="rgba(14, 17, 23, 0.95)",
        plot_bgcolor="rgba(14, 17, 23, 0.95)",
        margin=dict(l=40, r=40, t=60, b=40),
    )
    return fig


def plot_noise_score_distribution(
    audit_df: pd.DataFrame,
    threshold: float = 0.50,
) -> go.Figure:
    """
    Distribution histogram of consensus noise scores.
    """
    fig = px.histogram(
        audit_df,
        x="noise_score",
        nbins=40,
        color="is_suspect",
        color_discrete_map={True: "#FF2B2B", False: "#00CC96"},
        labels={"noise_score": "Consensus Noise Score", "is_suspect": "Suspect Label"},
        title="Consensus Label Noise Score Distribution",
    )

    fig.add_vline(
        x=threshold,
        line_width=2,
        line_dash="dash",
        line_color="#FFAA00",
        annotation_text=f"Threshold ({threshold})",
        annotation_position="top right",
    )

    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(14, 17, 23, 0.95)",
        plot_bgcolor="rgba(14, 17, 23, 0.95)",
        bargap=0.08,
        margin=dict(l=40, r=40, t=60, b=40),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    return fig


def plot_benchmark_comparison(
    metrics_table: pd.DataFrame,
) -> go.Figure:
    """
    Bar chart comparing Noisy Baseline vs LabelGuard Healed performance.
    """
    # Parse numbers from percentage strings
    metrics = metrics_table["Metric"].tolist()
    noisy_vals = [float(x.replace("%", "")) for x in metrics_table["Noisy Baseline"]]
    healed_vals = [float(x.replace("%", "")) for x in metrics_table["LabelGuard Healed"]]

    fig = go.Figure(
        data=[
            go.Bar(
                name="Raw Noisy Baseline",
                x=metrics,
                y=noisy_vals,
                marker_color="#EF553B",
                text=[f"{v:.1f}%" for v in noisy_vals],
                textposition="auto",
            ),
            go.Bar(
                name="LabelGuard Healed",
                x=metrics,
                y=healed_vals,
                marker_color="#00CC96",
                text=[f"{v:.1f}%" for v in healed_vals],
                textposition="auto",
            ),
        ]
    )

    fig.update_layout(
        barmode="group",
        title="Model Generalization on Clean Test Set (Before vs After)",
        yaxis_title="Score (%)",
        yaxis_range=[0, 105],
        template="plotly_dark",
        paper_bgcolor="rgba(14, 17, 23, 0.95)",
        plot_bgcolor="rgba(14, 17, 23, 0.95)",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        margin=dict(l=40, r=40, t=60, b=40),
    )
    return fig


def plot_confusion_matrices(
    cm_noisy: list,
    cm_clean: list,
    class_names: List[str],
) -> Tuple[go.Figure, go.Figure]:
    """
    Dual confusion matrix heatmaps.
    """
    labels = [f"Class {c}" for c in class_names]

    fig_noisy = go.Figure(
        data=go.Heatmap(
            z=cm_noisy,
            x=labels,
            y=labels,
            colorscale="Reds",
            text=cm_noisy,
            texttemplate="%{text}",
        )
    )
    fig_noisy.update_layout(
        title="Noisy Model Test Confusion Matrix",
        xaxis_title="Predicted",
        yaxis_title="Ground Truth",
        template="plotly_dark",
        paper_bgcolor="rgba(14, 17, 23, 0.95)",
        plot_bgcolor="rgba(14, 17, 23, 0.95)",
        margin=dict(l=40, r=40, t=50, b=40),
    )

    fig_clean = go.Figure(
        data=go.Heatmap(
            z=cm_clean,
            x=labels,
            y=labels,
            colorscale="Greens",
            text=cm_clean,
            texttemplate="%{text}",
        )
    )
    fig_clean.update_layout(
        title="Healed Model Test Confusion Matrix",
        xaxis_title="Predicted",
        yaxis_title="Ground Truth",
        template="plotly_dark",
        paper_bgcolor="rgba(14, 17, 23, 0.95)",
        plot_bgcolor="rgba(14, 17, 23, 0.95)",
        margin=dict(l=40, r=40, t=50, b=40),
    )

    return fig_noisy, fig_clean
