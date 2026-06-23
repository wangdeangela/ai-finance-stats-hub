"""Unified Streamlit dashboard: portfolio analytics + statistical inference."""

from __future__ import annotations

import io
import os
import tempfile
from collections.abc import Callable
from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st
from matplotlib.figure import Figure

from src.bridge.portfolio_inference import compare_return_baskets, returns_to_long
from src.config import (
    AI_CHAIN_TICKERS,
    BOTTLENECK_TICKERS,
    DEMO_DATA_DIR,
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
from src.finance.supply_chain_map import plot_supply_chain_map
from src.stats.inference import analyze

st.set_page_config(
    page_title="AI Finance & Stats Hub",
    page_icon="📊",
    layout="wide",
)

SAMPLE_DATASETS = {
    "[Business] Conversion A/B test": "conversion_data.csv",
    "[Business] Revenue A/B test": "revenue_data.csv",
    "[Business] Session duration": "session_data.csv",
    "[Business] Feedback Chi-Square": "feedback_data.csv",
    "[Lab] Cell viability": "biology_cell_viability.csv",
    "[Lab] Enzyme activity ANOVA": "biology_enzyme_anova.csv",
}


def _on_streamlit_cloud() -> bool:
    env = os.environ.get("STREAMLIT_RUNTIME_ENVIRONMENT", "").lower()
    return env in {"cloud", "streamlit-cloud", "community-cloud"} or bool(
        os.environ.get("STREAMLIT_SHARING")
    )


@st.cache_data(show_spinner="Loading prices…", ttl=3600)
def load_prices(use_demo: bool) -> pd.DataFrame:
    return run_pipeline(demo=use_demo, save=False)


def load_analysis(use_demo: bool) -> dict:
    try:
        prices = load_prices(use_demo)
    except Exception as exc:
        if use_demo:
            raise
        st.warning(f"Live yfinance fetch failed: {exc}. Using demo data.")
        prices = load_prices(True)
    return run_full_analysis(prices)


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
        results = load_analysis(use_demo)
    except Exception as exc:
        st.error(f"Failed to load analysis: {exc}")
        st.info("Enable **Use demo data** in the sidebar, then refresh.")
        st.stop()

    prices = results["prices"]
    stats = results["stats_loop"]

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Trading days", f"{len(prices)}")
    c2.metric("Watchlist", len(TICKERS))
    c3.metric("Highest volatility", stats["std"].idxmax())
    c4.metric("Data source", "Demo" if use_demo else "yfinance")

    tab_map, tab_overview, tab_stats, tab_tests, tab_charts = st.tabs(
        ["Supply Chain Map", "Overview", "Returns", "Tests", "Charts"]
    )

    with tab_map:
        st.subheader("AI 产业链上下游图谱")
        st.caption(
            "从硅片/光刻设备 → 芯片设计/代工/封装 → 数据中心基础设施 → 云与大模型应用。"
            "★ 标注为结构性瓶颈节点；彩色高亮为当前 watchlist 标的。"
        )
        render_figure(plot_supply_chain_map, None)

        st.markdown("**产业链分层说明**")
        layer_rows = []
        for layer in SUPPLY_CHAIN_LAYERS:
            for node in layer["nodes"]:
                layer_rows.append(
                    {
                        "Layer": layer["label"],
                        "Node": node["name"],
                        "Watchlist": node.get("watch") or "—",
                        "Bottleneck": "★" if node.get("bottleneck") else "",
                    }
                )
        st.dataframe(pd.DataFrame(layer_rows), use_container_width=True, hide_index=True)

        bn_cols = st.columns(3)
        for col, ticker in zip(bn_cols, BOTTLENECK_TICKERS):
            with col:
                st.markdown(f"**{ticker}** — {TICKER_META[ticker]['name']}")
                st.write(TICKER_META[ticker]["role"])

    with tab_overview:
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
                f"AI-chain avg correlation: **{upper.mean():.3f}** ｜ "
                f"SLV vs AI-chain avg: **{slv_vals:.3f}**"
            )

    with tab_stats:
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
        c1, c2, c3 = st.columns(3)
        with c1:
            st.markdown("**Jarque–Bera normality**")
            st.dataframe(results["normality_tests"].round(4), use_container_width=True)
        with c2:
            st.markdown("**ADF — price level**")
            st.dataframe(results["adf_price_tests"].round(4), use_container_width=True)
        with c3:
            st.markdown("**ADF — daily returns**")
            st.dataframe(results["adf_return_tests"].round(4), use_container_width=True)

        reject = int(results["normality_tests"]["reject_normal_5pct"].sum())
        nonstat = int((~results["adf_price_tests"]["stationary_5pct"]).sum())
        stat = int(results["adf_return_tests"]["stationary_5pct"].sum())
        st.info(
            f"Reject normality {reject}/{len(TICKERS)} ｜ "
            f"Non-stationary prices {nonstat}/{len(TICKERS)} ｜ "
            f"Stationary returns {stat}/{len(TICKERS)}"
        )

    with tab_charts:
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
    st.caption(
        "Combines portfolio analytics with automated assumption checks — "
        "compare AI supply-chain baskets vs macro hedge (SLV), or run ANOVA across tickers."
    )

    results = load_analysis(use_demo)
    returns = results["simple_returns"]

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
    alpha = st.slider("Significance level α", 0.01, 0.10, 0.05, 0.01)

    long_preview = returns_to_long(returns, group_mode=mode)
    st.markdown("**Pooled daily returns (sample)**")
    st.dataframe(long_preview.groupby("group")["daily_return"].describe().round(6))

    if st.button("Run basket inference", type="primary"):
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


def render_ab_stats_tab() -> None:
    st.subheader("A/B & experiment statistical toolkit")
    st.caption("Upload CSV or pick a sample — auto assumption checks → correct test → PDF.")

    source = st.radio("Data source", ["Sample dataset", "Upload CSV"], horizontal=True)
    df: pd.DataFrame | None = None

    if source == "Sample dataset":
        label = st.selectbox("Sample", list(SAMPLE_DATASETS.keys()))
        path = DEMO_DATA_DIR / SAMPLE_DATASETS[label]
        df = pd.read_csv(path)
    else:
        uploaded = st.file_uploader("CSV file", type=["csv"])
        if uploaded:
            df = pd.read_csv(uploaded)

    if df is None:
        st.info("Select or upload data to continue.")
        return

    st.dataframe(df.head(8), use_container_width=True)
    cols = list(df.columns)
    group_col = st.selectbox("Group column", cols, index=cols.index("group") if "group" in cols else 0)
    value_col = st.selectbox(
        "Value column",
        cols,
        index=cols.index("converted") if "converted" in cols else min(1, len(cols) - 1),
    )
    audience = st.selectbox(
        "Report audience",
        ["researcher", "small_business", "fiverr_buyer"],
        format_func=lambda x: {
            "researcher": "Researcher / PhD",
            "small_business": "Small business / marketer",
            "fiverr_buyer": "Fiverr buyer (concise)",
        }[x],
    )

    if st.button("Run A/B analysis", type="primary"):
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
            pdf_path = tmp.name
        try:
            test_results, assumptions = analyze(
                df,
                group_col=group_col,
                value_col=value_col,
                output_pdf=pdf_path,
                report_metadata={"audience": audience},
                verbose=False,
            )
        except Exception as exc:
            st.error(str(exc))
            return

        st.success(f"**{test_results.get('test_name', 'Test')}** — p = {test_results.get('p_value', 0):.6f}")
        if assumptions:
            st.write(f"Recommended route: {assumptions.get('recommended_test', 'N/A')}")

        groups = df.groupby(group_col)[value_col]
        if pd.api.types.is_numeric_dtype(df[value_col]):
            summary = groups.describe()
            fig = px.box(df, x=group_col, y=value_col, title="Group comparison")
            st.plotly_chart(fig, use_container_width=True)
            st.dataframe(summary.round(4))

        st.download_button(
            "Download PDF",
            data=Path(pdf_path).read_bytes(),
            file_name="ab_test_report.pdf",
            mime="application/pdf",
        )


def main() -> None:
    st.title("AI Finance & Statistics Hub")
    st.caption(
        "Portfolio analytics (yfinance) + statistical inference ｜ "
        "GOOGL · VRT · SLV · AVGO · ASML · TSM · NVDA"
    )
    st.markdown(
        "*三大瓶颈股：ASML（EUV 光刻）、TSM（先进代工/CoWoS 封装）、NVDA（AI GPU 算力）。"
        "详见 Portfolio → Supply Chain Map。*"
    )

    default_demo = _on_streamlit_cloud()
    with st.sidebar:
        st.header("Settings")
        use_demo = st.toggle(
            "Use demo data",
            value=default_demo,
            help="Recommended on Streamlit Cloud. Turn off for live yfinance.",
        )
        if not use_demo:
            st.warning("Live mode needs network; may be rate-limited.")
        if st.button("Clear cache & refresh"):
            st.cache_data.clear()
            st.rerun()
        st.divider()
        st.markdown("**Watchlist baskets**")
        st.write(f"AI chain: {', '.join(AI_CHAIN_TICKERS)}")
        st.write(f"Hedge: {', '.join(HEDGE_TICKERS)}")
        st.write(f"Bottlenecks: {', '.join(BOTTLENECK_TICKERS)}")

    page = st.radio(
        "Module",
        ["Portfolio Dashboard", "Basket Inference", "A/B Stats Toolkit"],
        horizontal=True,
        label_visibility="collapsed",
    )

    if page == "Portfolio Dashboard":
        render_portfolio_tab(use_demo)
    elif page == "Basket Inference":
        render_basket_inference_tab(use_demo)
    else:
        render_ab_stats_tab()


main()
