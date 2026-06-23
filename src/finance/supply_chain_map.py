"""AI industry supply-chain map — UBC coursemap-style interactive graph."""

from __future__ import annotations

from pathlib import Path

import matplotlib
import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import pandas as pd
import plotly.graph_objects as go
from matplotlib.figure import Figure
from matplotlib.lines import Line2D
from matplotlib.patches import Circle

from src.config import (
    IMAGES_DIR,
    SUPPLY_CHAIN_LAYERS,
    SUPPLY_CHAIN_NODE_EDGES,
    SUPPLY_CHAIN_TICKER_EDGES,
    TICKER_LAYER_COLORS,
    TICKER_META,
)

# UBC coursemap-inspired palette (https://ubcmath.github.io/coursemap/)
_UBC_BLUE = "#0055B7"
_UBC_LIGHT = "rgba(0,0,0,0.12)"
_EDGE_DEFAULT_OPACITY = 0.18

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


def _node_catalog() -> dict[str, dict]:
    catalog: dict[str, dict] = {}
    for layer in SUPPLY_CHAIN_LAYERS:
        for node in layer["nodes"]:
            catalog[node["id"]] = {**node, "layer_id": layer["id"], "layer_label": layer["label"], "layer_color": layer["color"]}
    return catalog


def _compute_layout() -> dict[str, tuple[float, float]]:
    """Column = layer index; row = vertical slot within layer (UBC-style grid)."""
    positions: dict[str, tuple[float, float]] = {}
    for layer_idx, layer in enumerate(SUPPLY_CHAIN_LAYERS):
        nodes = layer["nodes"]
        n = len(nodes)
        for row_idx, node in enumerate(nodes):
            y = row_idx - (n - 1) / 2
            positions[node["id"]] = (float(layer_idx), y)
    return positions


def _node_short_label(node: dict) -> str:
    if node.get("bottleneck"):
        return f"★{node['short']}"
    return node["short"]


def _node_hover_text(node: dict) -> str:
    lines = [
        f"<b>{node['name']}</b>",
        f"Layer: {node['layer_label']}",
    ]
    watch = node.get("watch")
    if watch:
        meta = TICKER_META.get(watch, {})
        lines.append(f"Watchlist: <b>{watch}</b> — {meta.get('name', '')}")
        lines.append(meta.get("role", ""))
    if node.get("bottleneck"):
        lines.append("★ Structural bottleneck")
    return "<br>".join(lines)


def _edge_ticker_correlation(
    source: dict,
    target: dict,
    correlation: pd.DataFrame | None,
) -> float | None:
    if correlation is None:
        return None
    src_watch = source.get("watch")
    tgt_watch = target.get("watch")
    if not src_watch or not tgt_watch or src_watch == tgt_watch:
        return None
    if src_watch not in correlation.index or tgt_watch not in correlation.columns:
        return None
    return float(correlation.loc[src_watch, tgt_watch])


def _node_is_highlighted(node: dict, layer_filter: str | None) -> bool:
    if layer_filter and layer_filter != "all" and node["layer_id"] != layer_filter:
        return False
    return bool(node.get("watch"))


def _ordered_sankey_tickers(edges: list[tuple[str, str]] | None = None) -> list[str]:
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


def plot_supply_chain_coursemap(
    correlation: pd.DataFrame | None = None,
    layer_filter: str | None = None,
) -> go.Figure:
    """
    Interactive node-link map inspired by UBC MATH coursemap:
    grid layout, circular nodes, prerequisite-style edges, hover details.
    """
    catalog = _node_catalog()
    layout = _compute_layout()
    layer_filter = layer_filter or "all"

    fig = go.Figure()

    # One segment per edge so width/color can differ (UBC uses uniform faint lines)
    seg_idx = 0
    for src_id, tgt_id in SUPPLY_CHAIN_NODE_EDGES:
        x0, y0 = layout[src_id]
        x1, y1 = layout[tgt_id]
        rho = _edge_ticker_correlation(catalog[src_id], catalog[tgt_id], correlation)
        width = 1.0 + 4.5 * abs(rho) if rho is not None else 1.2
        color = _link_rgba(rho) if rho is not None else f"rgba(0,0,0,{_EDGE_DEFAULT_OPACITY})"
        hover = f"{catalog[src_id]['short']} → {catalog[tgt_id]['short']}"
        if rho is not None:
            hover += f"<br>ρ({catalog[src_id].get('watch')}–{catalog[tgt_id].get('watch')}) = {rho:+.3f}"
        fig.add_trace(
            go.Scatter(
                x=[x0, x1],
                y=[y0, y1],
                mode="lines",
                line=dict(color=color, width=width),
                hoverinfo="text",
                hovertext=hover,
                showlegend=False,
                name=f"edge-{seg_idx}",
            )
        )
        seg_idx += 1

    node_ids = list(catalog.keys())
    xs = [layout[nid][0] for nid in node_ids]
    ys = [layout[nid][1] for nid in node_ids]
    labels = [_node_short_label(catalog[nid]) for nid in node_ids]
    hovers = [_node_hover_text(catalog[nid]) for nid in node_ids]

    marker_sizes: list[float] = []
    marker_colors: list[str] = []
    line_colors: list[str] = []
    line_widths: list[float] = []
    text_colors: list[str] = []
    for nid in node_ids:
        node = catalog[nid]
        highlighted = _node_is_highlighted(node, layer_filter)
        is_bn = node.get("bottleneck", False)
        has_watch = bool(node.get("watch"))

        if highlighted and has_watch:
            marker_sizes.append(34 if is_bn else 30)
            marker_colors.append(_UBC_BLUE)
            line_colors.append(_UBC_BLUE)
            line_widths.append(2.5)
            text_colors.append("white")
        elif has_watch:
            marker_sizes.append(26)
            marker_colors.append("white")
            line_colors.append(_UBC_BLUE)
            line_widths.append(2.0)
            text_colors.append(_UBC_BLUE)
        else:
            marker_sizes.append(22)
            marker_colors.append("white")
            line_colors.append("rgba(0,0,0,0.55)")
            line_widths.append(1.5)
            text_colors.append("rgba(0,0,0,0.75)")

    fig.add_trace(
        go.Scatter(
            x=xs,
            y=ys,
            mode="markers+text",
            text=labels,
            textposition="middle center",
            textfont=dict(size=9, color=text_colors),
            marker=dict(
                size=marker_sizes,
                color=marker_colors,
                line=dict(color=line_colors, width=line_widths),
            ),
            hovertext=hovers,
            hoverinfo="text",
            showlegend=False,
            name="nodes",
        )
    )

    # Layer column headers (like 100/200/300 levels on UBC map)
    for layer_idx, layer in enumerate(SUPPLY_CHAIN_LAYERS):
        fig.add_annotation(
            x=layer_idx,
            y=max(y for nid, (_, y) in layout.items() if catalog[nid]["layer_id"] == layer["id"]) + 1.1,
            text=f"<b>{layer['label']}</b>",
            showarrow=False,
            font=dict(size=10, color=layer["color"]),
            xanchor="center",
        )

    fig.update_layout(
        title=dict(
            text="AI 产业链图谱  ·  Supply Chain Course Map",
            x=0.5,
            xanchor="center",
            font=dict(size=16, color="#0f172a"),
        ),
        xaxis=dict(
            showgrid=False,
            zeroline=False,
            showticklabels=False,
            range=[-0.6, len(SUPPLY_CHAIN_LAYERS) - 0.4],
        ),
        yaxis=dict(
            showgrid=False,
            zeroline=False,
            showticklabels=False,
            scaleanchor="x",
            scaleratio=1,
        ),
        height=560,
        margin=dict(l=20, r=20, t=70, b=40),
        paper_bgcolor="white",
        plot_bgcolor="white",
        hovermode="closest",
    )
    fig.add_annotation(
        text="Hover a node for details  ·  Blue = watchlist  ·  Edge width = |ρ| when tickers linked",
        xref="paper",
        yref="paper",
        x=0.5,
        y=-0.06,
        showarrow=False,
        font=dict(size=10, color="#64748b"),
    )
    return fig


def plot_supply_chain_sankey(
    correlation: pd.DataFrame,
    edges: list[tuple[str, str]] | None = None,
) -> go.Figure:
    weighted = build_correlation_weighted_edges(correlation, edges)
    if weighted.empty:
        raise ValueError("No supply-chain edges could be matched to the correlation matrix.")

    nodes = _ordered_sankey_tickers(edges)
    node_index = {ticker: i for i, ticker in enumerate(nodes)}

    node_labels = [f"{ticker}<br>{TICKER_META[ticker]['name']}" for ticker in nodes]
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


def plot_supply_chain_map(save: bool = True, correlation: pd.DataFrame | None = None) -> Path | Figure:
    """Static PNG export using the same coursemap grid layout as the interactive view."""
    catalog = _node_catalog()
    layout = _compute_layout()
    n_layers = len(SUPPLY_CHAIN_LAYERS)

    fig, ax = plt.subplots(figsize=(14, 9))
    ax.set_aspect("equal")
    ax.axis("off")

    ax.set_title(
        "AI 产业链图谱  ·  AI Industry Supply Chain Map\n"
        "UBC coursemap-style layout  |  ★ bottleneck  |  Blue = watchlist",
        fontsize=14,
        fontweight="bold",
        color="#0f172a",
        pad=16,
    )

    # Edges
    for src_id, tgt_id in SUPPLY_CHAIN_NODE_EDGES:
        x0, y0 = layout[src_id]
        x1, y1 = layout[tgt_id]
        rho = _edge_ticker_correlation(catalog[src_id], catalog[tgt_id], correlation)
        lw = 0.8 + 2.5 * abs(rho) if rho is not None else 0.9
        color = "#059669" if rho and rho >= 0 else "#dc2626" if rho else "#94a3b8"
        alpha = 0.25 + 0.45 * abs(rho) if rho is not None else 0.2
        ax.annotate(
            "",
            xy=(x1, y1),
            xytext=(x0, y0),
            arrowprops=dict(arrowstyle="-|>", color=color, lw=lw, alpha=alpha, shrinkA=12, shrinkB=12),
        )

    # Layer bands
    for layer_idx, layer in enumerate(SUPPLY_CHAIN_LAYERS):
        layer_ys = [layout[n["id"]][1] for n in layer["nodes"]]
        y_min, y_max = min(layer_ys) - 0.85, max(layer_ys) + 0.85
        rect = mpatches.FancyBboxPatch(
            (layer_idx - 0.42, y_min),
            0.84,
            y_max - y_min,
            boxstyle="round,pad=0.02,rounding_size=0.08",
            facecolor=layer["color"],
            edgecolor="none",
            alpha=0.08,
            zorder=0,
        )
        ax.add_patch(rect)
        ax.text(
            layer_idx,
            y_max + 0.35,
            layer["label"],
            ha="center",
            va="bottom",
            fontsize=9,
            fontweight="bold",
            color=layer["color"],
        )

    # Nodes
    for node_id, (x, y) in layout.items():
        node = catalog[node_id]
        watch = node.get("watch")
        is_bn = node.get("bottleneck", False)
        if watch:
            fc = _UBC_BLUE
            ec = _UBC_BLUE
            tc = "white"
            r = 0.38 if is_bn else 0.34
        else:
            fc = "white"
            ec = "#334155"
            tc = "#1e293b"
            r = 0.30
        circle = Circle((x, y), r, facecolor=fc, edgecolor=ec, linewidth=2 if watch else 1.2, zorder=3)
        ax.add_patch(circle)
        ax.text(x, y, _node_short_label(node), ha="center", va="center", fontsize=7, fontweight="bold", color=tc, zorder=4)

    ax.set_xlim(-0.75, n_layers - 0.25)
    y_all = [pos[1] for pos in layout.values()]
    ax.set_ylim(min(y_all) - 1.2, max(y_all) + 1.5)

    legend_items = [
        mpatches.Patch(facecolor=_UBC_BLUE, edgecolor=_UBC_BLUE, label="Watchlist ticker"),
        mpatches.Patch(facecolor="white", edgecolor="#334155", label="Industry node"),
        Line2D([0], [0], color="#94a3b8", linewidth=1.5, label="Process flow"),
    ]
    ax.legend(handles=legend_items, loc="lower center", ncol=3, fontsize=8, framealpha=0.9, bbox_to_anchor=(0.5, -0.02))

    plt.tight_layout()
    if save:
        IMAGES_DIR.mkdir(parents=True, exist_ok=True)
        path = IMAGES_DIR / "ai_supply_chain_map.png"
        fig.savefig(path, dpi=160, bbox_inches="tight", facecolor="white")
        plt.close(fig)
        return path
    return fig
