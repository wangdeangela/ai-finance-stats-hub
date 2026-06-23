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
    page_icon="📊",
    layout="wide",
)

WORKFLOW_STEPS: list[dict[str, str | int]] = [
    {"step": 1, "title": "数据采集", "detail": "yfinance / Demo 收盘价", "module": "sidebar"},
    {"step": 2, "title": "收益计算", "detail": "日收益率 simple_returns", "module": "engine"},
    {"step": 3, "title": "描述性分析", "detail": "图谱 · 相关 · 波动 · JB/ADF", "module": "portfolio"},
    {"step": 4, "title": "分组映射", "detail": "产业链 basket → 长表", "module": "inference"},
    {"step": 5, "title": "假设检验", "detail": "t / Welch / MWU / ANOVA", "module": "inference"},
    {"step": 6, "title": "PDF 报告", "detail": "推断结论与假设说明", "module": "inference"},
]

PAGE_ACTIVE_STEP = {
    "Portfolio Dashboard": 3,
    "Basket Inference": 5,
}


def render_architecture_flow(active_step: int) -> None:
    """Top pipeline rail — numbered steps aligned with the analysis workflow."""
    st.markdown("#### 分析流程")
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


@st.cache_data(show_spinner="步骤② 加载行情并计算日收益率…", ttl=3600)
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
        st.warning(f"实时 yfinance 获取失败：{exc}。已自动切换为 Demo 数据。")
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
        st.info("请在侧边栏开启 **Use demo data**，然后点击 **Clear cache & refresh**。")
        st.stop()

    prices = results["prices"]
    stats = results["stats_loop"]

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Trading days", f"{len(prices)}")
    c2.metric("Watchlist", len(TICKERS))
    c3.metric("Highest volatility", stats["std"].idxmax())
    c4.metric("Data source", "Demo" if effective_demo else "yfinance")

    st.caption("步骤 ③ 描述性分析 — 从产业链结构到收益特征，为后续推断性检验做准备。")

    tab_map, tab_overview, tab_stats, tab_tests, tab_charts = st.tabs(
        ["① 产业链图谱", "② 标的概览", "③ 收益统计", "④ 分布检验", "⑤ 可视化"]
    )

    with tab_map:
        st.markdown("**步骤 ③-A** 产业链结构 + 相关性")
        st.subheader("AI 产业链上下游图谱")

        layer_options = {"全部 All": "all", **{layer["label"]: layer["id"] for layer in SUPPLY_CHAIN_LAYERS}}
        nav_col, map_col = st.columns([0.32, 0.68])
        with nav_col:
            selected_layer = st.selectbox(
                "产业链层级 / Layer",
                options=list(layer_options.keys()),
                index=0,
            )
            layer_filter = layer_options[selected_layer]
            st.markdown("**节点速览**")
            for layer in SUPPLY_CHAIN_LAYERS:
                if layer_filter != "all" and layer["id"] != layer_filter:
                    continue
                for node in layer["nodes"]:
                    watch = node.get("watch")
                    bn = " ★" if node.get("bottleneck") else ""
                    ticker = f" `[{watch}]`" if watch else ""
                    st.markdown(f"- **{node['short']}**{bn}{ticker} — {node['name']}")

        with map_col:
            st.plotly_chart(
                plot_supply_chain_coursemap(results["correlation"], layer_filter=layer_filter),
                use_container_width=True,
            )

        st.markdown("**相关性加权流向图**")
        st.caption(
            "沿产业链逻辑连边的日收益率相关系数 ρ：流带宽度 = |ρ|，"
            "绿色为正相关、红色为负相关（如 SLV 对冲分支）。"
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
                    "correlation": "ρ",
                    "abs_correlation": "|ρ|",
                    "label": "Edge",
                }
            )[["Source", "Target", "ρ", "|ρ|"]],
            use_container_width=True,
            hide_index=True,
        )

        st.markdown("**产业链分层说明**")
        layer_rows = []
        for layer in SUPPLY_CHAIN_LAYERS:
            for node in layer["nodes"]:
                layer_rows.append(
                    {
                        "Layer": layer["label"],
                        "Node": node["name"],
                        "Code": node["short"],
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
        st.markdown("**步骤 ③-B** 标的定义与共变结构")
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
        st.markdown("**步骤 ③-C** 收益水平与月度汇总")
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
        st.markdown("**步骤 ③-D** 分布与平稳性预检（为步骤 ⑤ 假设检验提供依据）")
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
        st.caption("→ 完成预检后，请切换至 **Basket Inference** 进行步骤 ④–⑥。")

    with tab_charts:
        st.markdown("**步骤 ③-E** 时序与相关可视化")
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
    st.caption("步骤 ④ 分组映射 → ⑤ 假设检验 → ⑥ PDF 报告")

    results, _effective_demo = load_analysis(use_demo)
    returns = results["simple_returns"]

    st.markdown("**步骤 ④ 分组映射** — 将日收益率按产业链角色合并为检验组")
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
    st.markdown("**分组预览（pooled daily returns）**")
    st.dataframe(long_preview.groupby("group")["daily_return"].describe().round(6))

    st.markdown("**步骤 ⑤ 假设检验** — 根据组数与分布自动选择 t / Welch / MWU / ANOVA")
    alpha = st.slider("Significance level α", 0.01, 0.10, 0.05, 0.01)

    if st.button("Run basket inference（步骤 ⑤ → ⑥）", type="primary"):
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
            st.markdown("**步骤 ⑥ PDF 报告**")
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
        "7 只 AI 产业链 watchlist：GOOGL · VRT · SLV · AVGO · ASML · TSM · NVDA"
    )

    default_demo = _on_streamlit_cloud()
    with st.sidebar:
        st.header("步骤 ① 数据采集")
        use_demo = st.toggle(
            "Use demo data",
            value=default_demo,
            help="步骤 ①：Demo（推荐云端）或 yfinance 实时行情。",
        )
        if not use_demo:
            st.warning("Live 模式在 Streamlit Cloud 上常被 yfinance 限流，约 20 秒后会自动回退 Demo。")
        st.caption("步骤 ② 收益计算在加载数据后自动执行。")
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
            "*瓶颈股：ASML（EUV）、TSM（代工/CoWoS）、NVDA（GPU）*"
        )

    page = st.radio(
        "分析模块",
        ["Portfolio Dashboard", "Basket Inference"],
        format_func=lambda x: {
            "Portfolio Dashboard": "③ Portfolio Dashboard · 描述性分析",
            "Basket Inference": "④–⑥ Basket Inference · 推断性检验",
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
