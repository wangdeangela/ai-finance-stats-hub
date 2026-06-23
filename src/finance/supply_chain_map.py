"""AI industry upstream/downstream supply-chain map visualization."""

from __future__ import annotations

from pathlib import Path

import matplotlib
import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import pandas as pd
import plotly.graph_objects as go
from matplotlib.figure import Figure
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

from src.config import (
    IMAGES_DIR,
    SUPPLY_CHAIN_LAYERS,
    SUPPLY_CHAIN_TICKER_EDGES,
    TICKER_LAYER_COLORS,
    TICKER_META,
)

# Prefer CJK-capable fonts so Chinese labels render on macOS / Windows
_CJK_FONTS = [
    "PingFang SC",
    "Heiti SC",
    "STHeiti",
    "Microsoft YaHei",
    "SimHei",
    "Arial Unicode MS",
    "Noto Sans CJK SC",
    "DejaVu Sans",
]
matplotlib.rcParams["font.sans-serif"] = _CJK_FONTS
matplotlib.rcParams["axes.unicode_minus"] = False


_CHAIN_POSITION_ORDER = {"upstream": 0, "midstream": 1, "downstream": 2, "hedge": 3}


def _layer_y_positions(n_layers: int, top: float = 0.92, bottom: float = 0.06) -> list[float]:
    step = (top - bottom) / max(n_layers - 1, 1)
    return [top - i * step for i in range(n_layers)]


def _ordered_sankey_tickers(edges: list[tuple[str, str]] | None = None) -> list[str]:
    """Return tickers appearing in supply-chain edges, sorted by chain position."""
    edges = edges or SUPPLY_CHAIN_TICKER_EDGES
    tickers = {t for pair in edges for t in pair}
    return sorted(
        tickers,
        key=lambda t: (_CHAIN_POSITION_ORDER[TICKER_META[t]["chain_position"]], t),
    )


def build_correlation_weighted_edges(
    correlation: pd.DataFrame,
    edges: list[tuple[str, str]] | None = None,
) -> pd.DataFrame:
    """
    Map logical supply-chain edges to signed correlation weights.

    Returns columns: source, target, correlation, abs_correlation, label.
    """
    edges = edges or SUPPLY_CHAIN_TICKER_EDGES
    rows: list[dict[str, object]] = []
    for source, target in edges:
        if source not in correlation.index or target not in correlation.columns:
            continue
        rho = float(correlation.loc[source, target])
        rows.append(
            {
                "source": source,
                "target": target,
                "correlation": rho,
                "abs_correlation": abs(rho),
                "label": f"{source} → {target}: ρ = {rho:+.3f}",
            }
        )
    return pd.DataFrame(rows)


def _link_rgba(correlation: float) -> str:
    alpha = 0.35 + 0.5 * min(abs(correlation), 1.0)
    if correlation >= 0:
        return f"rgba(5, 150, 105, {alpha:.2f})"
    return f"rgba(220, 38, 38, {alpha:.2f})"


def plot_supply_chain_sankey(
    correlation: pd.DataFrame,
    edges: list[tuple[str, str]] | None = None,
) -> go.Figure:
    """
    Sankey diagram along the AI supply chain; link width = |ρ|, color = sign of ρ.
    """
    weighted = build_correlation_weighted_edges(correlation, edges)
    if weighted.empty:
        raise ValueError("No supply-chain edges could be matched to the correlation matrix.")

    nodes = _ordered_sankey_tickers(edges)
    node_index = {ticker: i for i, ticker in enumerate(nodes)}

    node_labels = [
        f"{ticker}<br>{TICKER_META[ticker]['name']}" for ticker in nodes
    ]
    node_colors = [
        TICKER_LAYER_COLORS.get(TICKER_META[ticker]["layer"], "#64748b") for ticker in nodes
    ]

    sources = [node_index[row["source"]] for _, row in weighted.iterrows()]
    targets = [node_index[row["target"]] for _, row in weighted.iterrows()]
    values = weighted["abs_correlation"].tolist()
    link_colors = [_link_rgba(float(r)) for r in weighted["correlation"]]
    hover_labels = weighted["label"].tolist()

    fig = go.Figure(
        data=[
            go.Sankey(
                arrangement="snap",
                node=dict(
                    label=node_labels,
                    color=node_colors,
                    pad=18,
                    thickness=22,
                    line=dict(color="#e2e8f0", width=1),
                ),
                link=dict(
                    source=sources,
                    target=targets,
                    value=values,
                    color=link_colors,
                    customdata=hover_labels,
                    hovertemplate="%{customdata}<br>|ρ| = %{value:.3f}<extra></extra>",
                ),
            )
        ]
    )
    fig.update_layout(
        title=dict(
            text="AI 产业链相关性流向图  ·  Correlation-Weighted Supply Chain",
            x=0.5,
            xanchor="center",
            font=dict(size=16, color="#0f172a"),
        ),
        font=dict(size=11, color="#1e293b"),
        height=520,
        margin=dict(l=24, r=24, t=64, b=24),
        paper_bgcolor="white",
        plot_bgcolor="white",
    )
    fig.add_annotation(
        text="Link width = |ρ| (daily returns)  ·  Green = positive  ·  Red = negative",
        xref="paper",
        yref="paper",
        x=0.5,
        y=-0.02,
        showarrow=False,
        font=dict(size=10, color="#64748b"),
    )
    return fig


def plot_supply_chain_map(save: bool = True) -> Path | Figure:
    """
    Draw a rich AI supply-chain map: layered upstream → application flow,
    watchlist tickers highlighted, bottleneck nodes marked.
    """
    fig, ax = plt.subplots(figsize=(14, 11))
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")

    ax.text(
        0.5,
        0.98,
        "AI 产业链上下游图谱  ·  AI Industry Supply Chain Map",
        ha="center",
        va="top",
        fontsize=16,
        fontweight="bold",
        color="#0f172a",
    )
    ax.text(
        0.5,
        0.955,
        "Watchlist tickers in bold  |  ★ = structural bottleneck  |  Flow: Upstream → Midstream → Infra → Application",
        ha="center",
        va="top",
        fontsize=9,
        color="#64748b",
    )

    y_positions = _layer_y_positions(len(SUPPLY_CHAIN_LAYERS))
    layer_boxes: list[tuple[float, float, float, float]] = []

    for layer, y_center in zip(SUPPLY_CHAIN_LAYERS, y_positions):
        color = layer["color"]
        nodes = layer["nodes"]
        n = len(nodes)
        box_h = 0.11
        box_w = 0.88
        x0, y0 = 0.06, y_center - box_h / 2

        rect = FancyBboxPatch(
            (x0, y0),
            box_w,
            box_h,
            boxstyle="round,pad=0.012,rounding_size=0.015",
            facecolor=color,
            edgecolor="white",
            alpha=0.12,
            linewidth=1.5,
            transform=ax.transAxes,
            zorder=1,
        )
        ax.add_patch(rect)
        layer_boxes.append((x0, y0, box_w, box_h))

        ax.text(
            x0 + 0.02,
            y_center + box_h / 2 - 0.018,
            layer["label"],
            transform=ax.transAxes,
            fontsize=10,
            fontweight="bold",
            color=color,
            va="top",
        )

        cols = min(3, n)
        for i, node in enumerate(nodes):
            row, col = divmod(i, cols)
            cell_w = box_w / cols
            cx = x0 + col * cell_w + cell_w * 0.05
            cy = y_center + box_h / 2 - 0.038 - row * 0.032

            label = node["name"]
            watch = node.get("watch")
            is_bn = node.get("bottleneck", False)

            if watch:
                meta = TICKER_META.get(watch, {})
                suffix = f"  [{watch}]"
                full = label + suffix
                weight = "bold"
                fc = "#fef3c7" if is_bn else "#e0f2fe"
                ec = "#d97706" if is_bn else "#0284c7"
            else:
                full = label
                weight = "normal"
                fc = "#f8fafc"
                ec = "#cbd5e1"

            prefix = "★ " if is_bn else "• "
            ax.text(
                cx,
                cy,
                prefix + full,
                transform=ax.transAxes,
                fontsize=7.5,
                fontweight=weight,
                color="#1e293b",
                va="top",
                bbox=dict(boxstyle="round,pad=0.25", facecolor=fc, edgecolor=ec, alpha=0.95),
            )

    # Vertical flow arrows between layers (skip hedge side branch)
    main_layers = layer_boxes[:4]
    for i in range(len(main_layers) - 1):
        _, y0_a, _, h_a = main_layers[i]
        _, y0_b, _, _ = main_layers[i + 1]
        y_top = y0_a
        y_bot = y0_b + main_layers[i + 1][3]
        arrow = FancyArrowPatch(
            (0.5, y_top),
            (0.5, y_bot + 0.01),
            transform=ax.transAxes,
            arrowstyle="-|>",
            mutation_scale=12,
            color="#94a3b8",
            linewidth=1.8,
            zorder=0,
        )
        ax.add_patch(arrow)

    # Hedge branch arrow from midstream
    ax.annotate(
        "",
        xy=(0.94, layer_boxes[4][1] + layer_boxes[4][3]),
        xytext=(0.94, layer_boxes[1][1]),
        xycoords="axes fraction",
        textcoords="axes fraction",
        arrowprops=dict(arrowstyle="-|>", color="#b45309", lw=1.5, linestyle="dashed"),
    )
    ax.text(
        0.965,
        (layer_boxes[1][1] + layer_boxes[4][1]) / 2,
        "diversify\nbeta",
        transform=ax.transAxes,
        fontsize=7,
        color="#b45309",
        ha="left",
        va="center",
        rotation=-90,
    )

    # Legend
    legend_items = [
        mpatches.Patch(facecolor="#fef3c7", edgecolor="#d97706", label="★ Bottleneck (watchlist)"),
        mpatches.Patch(facecolor="#e0f2fe", edgecolor="#0284c7", label="Watchlist ticker"),
        mpatches.Patch(facecolor="#f8fafc", edgecolor="#cbd5e1", label="Industry node (not tracked)"),
    ]
    ax.legend(
        handles=legend_items,
        loc="lower center",
        ncol=3,
        fontsize=8,
        framealpha=0.9,
        bbox_to_anchor=(0.5, 0.01),
    )

    # Ticker summary strip
    summary = "  |  ".join(
        f"{t} ({TICKER_META[t]['name']})" for t in ["GOOGL", "VRT", "SLV", "AVGO", "ASML", "TSM", "NVDA"]
    )
    ax.text(
        0.5,
        0.035,
        summary,
        ha="center",
        va="bottom",
        fontsize=7,
        color="#475569",
        wrap=True,
    )

    plt.tight_layout()
    if save:
        IMAGES_DIR.mkdir(parents=True, exist_ok=True)
        path = IMAGES_DIR / "ai_supply_chain_map.png"
        fig.savefig(path, dpi=160, bbox_inches="tight", facecolor="white")
        plt.close(fig)
        return path
    return fig
