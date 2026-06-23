"""Unified Streamlit dashboard: portfolio analytics + statistical inference."""

from __future__ import annotations

import io
import os
from collections.abc import Callable
from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import streamlit as st
from matplotlib.figure import Figure

from src.bridge.portfolio_inference import compare_return_baskets, returns_to_long
from src.config import (
    AI_CHAIN_TICKERS,
    BOTTLENECK_TICKERS,
    HEDGE_TICKERS,
    REPORTS_DIR,
    SUPPLY_CHAIN_LAYERS,
    TICKER_META,
    TICKERS,
)
from src.finance.analysis import run_full_analysis
from src.finance.data_fetch import run_pipeline
from src.finance.plotting import (
    plot_correlation_heatmap,
    plot_cumulative_returns,
    plot_monthly_returns_bar,
    plot_rolling_volatility,
)
from src.finance.supply_chain_map import (
    build_correlation_weighted_edges,
    plot_supply_chain_coursemap,
    plot_supply_chain_sankey,
)

st.set_page_config(
    page_title="AI Finance & Stats Hub",
    page_icon=":bar_chart:",
    layout="wide",
)

WORKFLOW_STEPS: list[dict[str, str | int]] = [
    {"step": 1, "title": "Data collection", "detail": "yfinance / Demo close prices", "module": "sidebar"},
    {"step": 2, "title": "Return calculation", "detail": "Daily simple returns", "module": "engine"},
    {"step": 3, "title": "Descriptive analysis", "detail": "Map, correlation, vol, JB/ADF", "module": "portfolio"},
    {"step": 4, "title": "Group mapping", "detail": "Supply-chain basket to long table", "module": "inference"},
    {"step": 5, "title": "Hypothesis tests", "detail": "t / Welch / MWU / ANOVA", "module": "inference"},
    {"step": 6, "title": "PDF report", "detail": "Inference conclusions & assumptions", "module": "inference"},
]

PAGE_ACTIVE_STEP = {
    "Portfolio Dashboard": 3,
    "Basket Inference": 5,
}


def render_architecture_flow(active_step: int) -> None:
    """Top pipeline rail - numbered steps aligned with the analysis workflow."""
    st.markdown("#### Analysis workflow")
    cols = st.columns(len(WORKFLOW_STEPS))
    for col, item in zip(cols, WORKFLOW_STEPS):
        step_num = int(item["step"])
        is_active = step_num == active_step
        is_done = step_num < active_step
        border = "#2563eb" if is_active else "#cbd5e1"
        bg = "#eff6ff" if is_active else "#f8fafc"
        badge_bg = "#2563eb" if is_active else ("#059669" if is_done else "#94a3b8")
        col.markdown(
            f"""
<div style="border:2px solid {border};border-radius:8px;padding:10px 8px;
background:{bg};text-align:center;min-height:88px;">
  <div style="display:inline-block;background:{badge_bg};color:white;border-radius:50%;
  width:26px;height:26px;line-height:26px;font-weight:700;font-size:13px;">{step_num}</div>
  <div style="font-weight:600;font-size:13px;margin-top:6px;color:#0f172a;">{item["title"]}</div>
  <div style="font-size:11px;color:#64748b;margin-top:4px;">{item["detail"]}</div>
</div>
            """,
            unsafe_allow_html=True,
        )

    st.divider()


def _on_streamlit_cloud() -> bool:
    env = os.environ.get("STREAMLIT_RUNTIME_ENVIRONMENT", "").lower()
    if env in {"cloud", "streamlit-cloud", "community-cloud"}:
        return True
    if os.environ.get("STREAMLIT_SHARING"):
        return True
    if os.environ.get("IS_STREAMLIT_CLOUD", "").lower() in {"1", "true", "yes"}:
        return True
    return os.environ.get("STREAMLIT_SERVER_HEADLESS", "").lower() == "true"


@st.cache_data(show_spinner="Step 2: Loading prices and computing daily returns...", ttl=3600)
def load_prices(use_demo: bool) -> pd.DataFrame:
    return run_pipeline(
        demo=use_demo,
        save=False,
        yfinance_timeout=20.0,
        yfinance_retries=2,
    )


def load_analysis(use_demo: bool) -> tuple[dict, bool]:
    """Return analysis results and whether demo data was used (after fallback)."""
    effective_demo = use_demo
    try:
        prices = load_prices(use_demo)
    except Exception as exc:
        if use_demo:
            raise
        st.warning(f"Live yfinance fetch failed: {exc}. Falling back to demo data.")
        effective_demo = True
        prices = load_prices(True)
    return run_full_analysis(prices), effective_demo


def render_figure(plot_fn: Callable[..., Path | Figure], data: Any) -> None:
    if data is None:
        fig = plot_fn(save=False)
    else:
        fig = plot_fn(data, save=False)
    if not isinstance(fig, Figure):
        st.warning("Chart could not be rendered.")
        return
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=120, bbox_inches="tight")
    plt.close(fig)
    buf.seek(0)
    st.image(buf, use_container_width=True)


def render_portfolio_tab(use_demo: bool) -> None:
    try:
        results, effective_demo = load_analysis(use_demo)
    except Exception as exc:
        st.error(f"Failed to load analysis: {exc}")
        st.info("Enable **Use demo data** in the sidebar, then click **Clear cache & refresh**.")
        st.stop()

    prices = results["prices"]
    stats = results["stats_loop"]

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Trading days", f"{len(prices)}")
    c2.metric("Watchlist", len(TICKERS))
    c3.metric("Highest volatility", stats["std"].idxmax())
    c4.metric("Data source", "Demo" if effective_demo else "yfinance")

    st.caption("Step 3: Descriptive analysis - from supply-chain structure to return features, preparing for inference.")

    tab_map, tab_overview, tab_stats, tab_tests, tab_charts = st.tabs(
        [
            "3A. Supply chain map",
            "3B. Watchlist overview",
            "3C. Return statistics",
            "3D. Distribution tests",
            "3E. Charts",
        ]
    )

    with tab_map:
        st.markdown("**Step 3A** Supply-chain structure + correlation")
        st.subheader("AI supply chain map")

        layer_options = {"All": "all", **{layer["label"]: layer["id"] for layer in SUPPLY_CHAIN_LAYERS}}
        nav_col, map_col = st.columns([0.32, 0.68])
        with nav_col:
            selected_layer = st.selectbox(
                "Supply-chain layer",
                options=list(layer_options.keys()),
                index=0,
            )
            layer_filter = layer_options[selected_layer]
            st.markdown("**Node quick view**")
            for layer in SUPPLY_CHAIN_LAYERS:
                if layer_filter != "all" and layer["id"] != layer_filter:
                    continue
                for node in layer["nodes"]:
                    watch = node.get("watch")
                    bn = " *" if node.get("bottleneck") else ""
                    ticker = f" `[{watch}]`" if watch else ""
                    st.markdown(f"- **{node['short']}**{bn}{ticker} - {node['name']}")

        with map_col:
            st.plotly_chart(
                plot_supply_chain_coursemap(results["correlation"], layer_filter=layer_filter),
                use_container_width=True,
            )

        st.markdown("**Correlation-weighted flow diagram**")
        st.caption(
            "Daily-return correlation rho along supply-chain logical edges: band width = |rho|; "
            "green = positive, red = negative (e.g. SLV hedge branch)."
        )
        st.plotly_chart(
            plot_supply_chain_sankey(results["correlation"]),
            use_container_width=True,
        )
        edge_df = build_correlation_weighted_edges(results["correlation"])
        st.dataframe(
            edge_df.rename(
                columns={
                    "source": "Source",
                    "target": "Target",
                    "correlation": "rho",
                    "abs_correlation": "|rho|",
                    "label": "Edge",
                }
            )[["Source", "Target", "rho", "|rho|"]],
            use_container_width=True,
            hide_index=True,
        )

        st.markdown("**Layer glossary**")
        layer_rows = []
        for layer in SUPPLY_CHAIN_LAYERS:
            for node in layer["nodes"]:
                layer_rows.append(
                    {
                        "Layer": layer["label"],
                        "Node": node["name"],
                        "Code": node["short"],
                        "Watchlist": node.get("watch") or "-",
                        "Bottleneck": "*" if node.get("bottleneck") else "",
                    }
                )
        st.dataframe(pd.DataFrame(layer_rows), use_container_width=True, hide_index=True)

        bn_cols = st.columns(3)
        for col, ticker in zip(bn_cols, BOTTLENECK_TICKERS):
            with col:
                st.markdown(f"**{ticker}** - {TICKER_META[ticker]['name']}")
                st.write(TICKER_META[ticker]["role"])

    with tab_overview:
        st.markdown("**Step 3B** Ticker definitions & co-movement")
        st.subheader("AI supply-chain watchlist")
        glossary = pd.DataFrame(
            [
                {
                    "Ticker": t,
                    "Name": TICKER_META[t]["name"],
                    "Role": TICKER_META[t]["role"],
                }
                for t in TICKERS
            ]
        )
        st.dataframe(glossary, use_container_width=True, hide_index=True)

        st.subheader("Close prices (last 10 rows)")
        st.dataframe(prices.tail(10).round(2), use_container_width=True)

        st.subheader("Daily return correlation")
        st.dataframe(results["correlation"].round(3), use_container_width=True)

        ai = [t for t in AI_CHAIN_TICKERS if t in results["correlation"].columns]
        if ai:
            ai_corr = results["correlation"].loc[ai, ai].values
            upper = ai_corr[np.triu_indices(len(ai), k=1)]
            slv_vals = (
                results["correlation"].loc["SLV", ai].mean()
                if "SLV" in results["correlation"].index
                else float("nan")
            )
            st.write(
                f"AI-chain avg correlation: **{upper.mean():.3f}** | "
                f"SLV vs AI-chain avg: **{slv_vals:.3f}**"
            )

    with tab_stats:
        st.markdown("**Step 3C** Return levels & monthly summary")
        st.subheader("Daily return statistics")
        st.dataframe(stats.round(6), use_container_width=True)
        left, right = st.columns(2)
        with left:
            st.markdown("**Monthly mean daily returns (last 6)**")
            st.dataframe(results["monthly_groupby"].tail(6).round(6), use_container_width=True)
        with right:
            st.markdown("**Month-end compounded returns (last 6)**")
            st.dataframe(results["monthly_resample"].tail(6).round(6), use_container_width=True)

    with tab_tests:
        st.markdown("**Step 3D** Distribution & stationarity pre-checks (inputs for Step 5 hypothesis tests)")
        c1, c2, c3 = st.columns(3)
        with c1:
            st.markdown("**Jarque-Bera normality**")
            st.dataframe(results["normality_tests"].round(4), use_container_width=True)
        with c2:
            st.markdown("**ADF - price level**")
            st.dataframe(results["adf_price_tests"].round(4), use_container_width=True)
        with c3:
            st.markdown("**ADF - daily returns**")
            st.dataframe(results["adf_return_tests"].round(4), use_container_width=True)

        reject = int(results["normality_tests"]["reject_normal_5pct"].sum())
        nonstat = int((~results["adf_price_tests"]["stationary_5pct"]).sum())
        stat = int(results["adf_return_tests"]["stationary_5pct"].sum())
        st.info(
            f"Reject normality {reject}/{len(TICKERS)} | "
            f"Non-stationary prices {nonstat}/{len(TICKERS)} | "
            f"Stationary returns {stat}/{len(TICKERS)}"
        )
        st.caption("-> After pre-checks, switch to **Basket Inference** for Steps 4-6.")

    with tab_charts:
        st.markdown("**Step 3E** Time series & correlation charts")
        st.subheader("Cumulative log returns")
        render_figure(plot_cumulative_returns, results["cumulative_log_return"])
        left, right = st.columns(2)
        with left:
            st.subheader("Correlation heatmap")
            render_figure(plot_correlation_heatmap, results["correlation"])
        with right:
            st.subheader("20-day rolling volatility")
            render_figure(plot_rolling_volatility, results["rolling_volatility"])
        st.subheader("Monthly mean daily returns (last 12 months)")
        render_figure(plot_monthly_returns_bar, results["monthly_groupby"])


def render_basket_inference_tab(use_demo: bool) -> None:
    st.subheader("Basket return inference")
    st.caption("Step 4: Group mapping -> Step 5: Hypothesis tests -> Step 6: PDF report")

    results, _effective_demo = load_analysis(use_demo)
    returns = results["simple_returns"]

    st.markdown("**Step 4: Group mapping** - pool daily returns by supply-chain role for testing")
    mode = st.radio(
        "Grouping mode",
        options=["ai_vs_hedge", "basket", "ticker"],
        format_func=lambda x: {
            "ai_vs_hedge": "AI Supply Chain vs SLV Hedge (2-sample)",
            "basket": "By role basket (ANOVA when 3+ groups)",
            "ticker": "Per ticker (ANOVA across 7 symbols)",
        }[x],
        horizontal=True,
    )
    long_preview = returns_to_long(returns, group_mode=mode)
    st.markdown("**Group preview (pooled daily returns)**")
    st.dataframe(long_preview.groupby("group")["daily_return"].describe().round(6))

    st.markdown("**Step 5: Hypothesis tests** - auto-select t / Welch / MWU / ANOVA by group count and distribution")
    alpha = st.slider("Significance level alpha", 0.01, 0.10, 0.05, 0.01)

    if st.button("Run basket inference (Steps 5-6)", type="primary"):
        pdf_path = REPORTS_DIR / "portfolio_basket_report.pdf"
        pdf_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            test_results, assumptions, _ = compare_return_baskets(
                returns,
                group_mode=mode,
                alpha=alpha,
                output_pdf=str(pdf_path),
                report_metadata={
                    "client_name": "AI Supply Chain Watchlist",
                    "prepared_by": "AI Finance & Stats Hub",
                    "audience": "researcher",
                },
            )
        except Exception as exc:
            st.error(f"Inference failed: {exc}")
            return

        st.success(f"Test: **{test_results.get('test_name', 'N/A')}**")
        st.metric("p-value", f"{test_results.get('p_value', float('nan')):.6f}")
        if "effect_size" in test_results:
            st.metric("Effect size", f"{test_results['effect_size']:.4f}")
        if assumptions:
            st.markdown("**Assumption checks**")
            st.json(
                {
                    "group_a_normality": assumptions["group_a_normality"]["note"],
                    "group_b_normality": assumptions["group_b_normality"]["note"],
                    "variance_equality": assumptions["variance_equality"]["note"],
                    "recommended_test": assumptions["recommended_test"],
                }
            )

        if pdf_path.exists():
            st.markdown("**Step 6: PDF report**")
            st.download_button(
                "Download PDF report",
                data=pdf_path.read_bytes(),
                file_name=pdf_path.name,
                mime="application/pdf",
            )

    st.markdown("**Bottleneck focus**")
    bottleneck_df = pd.DataFrame(
        [
            {"Ticker": t, "Role": TICKER_META[t]["role"]}
            for t in BOTTLENECK_TICKERS
        ]
    )
    st.dataframe(bottleneck_df, hide_index=True, use_container_width=True)


def main() -> None:
    st.title("AI Finance & Statistics Hub")
    st.caption(
        "7-ticker AI supply-chain watchlist: GOOGL, VRT, SLV, AVGO, ASML, TSM, NVDA"
    )

    default_demo = _on_streamlit_cloud()
    with st.sidebar:
        st.header("Step 1: Data collection")
        use_demo = st.toggle(
            "Use demo data",
            value=default_demo,
            help="Step 1: Demo (recommended on cloud) or live yfinance quotes.",
        )
        if not use_demo:
            st.warning(
                "Live mode is often rate-limited on Streamlit Cloud; "
                "falls back to demo after ~20 seconds."
            )
        st.caption("Step 2: Return calculation runs automatically after data loads.")
        if st.button("Clear cache & refresh"):
            st.cache_data.clear()
            st.rerun()
        st.divider()
        st.markdown("**Watchlist baskets**")
        st.write(f"AI chain: {', '.join(AI_CHAIN_TICKERS)}")
        st.write(f"Hedge: {', '.join(HEDGE_TICKERS)}")
        st.write(f"Bottlenecks: {', '.join(BOTTLENECK_TICKERS)}")
        st.divider()
        st.markdown(
            "*Bottlenecks: ASML (EUV), TSM (foundry/CoWoS), NVDA (GPU)*"
        )

    page = st.radio(
        "Analysis module",
        ["Portfolio Dashboard", "Basket Inference"],
        format_func=lambda x: {
            "Portfolio Dashboard": "Step 3: Portfolio Dashboard - Descriptive analysis",
            "Basket Inference": "Steps 4-6: Basket Inference - Statistical inference",
        }[x],
        horizontal=True,
        label_visibility="collapsed",
    )

    render_architecture_flow(PAGE_ACTIVE_STEP[page])

    if page == "Portfolio Dashboard":
        render_portfolio_tab(use_demo)
    else:
        render_basket_inference_tab(use_demo)


main()
