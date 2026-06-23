"""Bridge portfolio returns with statistical inference."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

from src.config import AI_CHAIN_TICKERS, HEDGE_TICKERS, REPORTS_DIR, TICKER_META
from src.stats.inference import analyze


def basket_label(ticker: str) -> str:
    """Map ticker to a human-readable basket name for inference."""
    meta = TICKER_META.get(ticker, {})
    basket = meta.get("basket", "other")
    labels = {
        "ai_platform": "AI Platform",
        "ai_infra": "AI Infrastructure",
        "hedge": "Macro Hedge (SLV)",
        "bottleneck_upstream": "Upstream Bottleneck",
        "bottleneck_midstream": "Midstream Bottleneck",
        "bottleneck_downstream": "Downstream Bottleneck",
    }
    return labels.get(basket, basket)


def returns_to_long(returns: pd.DataFrame, group_mode: str = "basket") -> pd.DataFrame:
    """
    Convert wide daily returns to long format for inference.

    group_mode:
      - 'basket': AI chain vs hedge vs bottleneck groupings
      - 'ticker': each symbol as its own group (for ANOVA)
      - 'ai_vs_hedge': collapse to two groups only
    """
    rows: list[dict[str, Any]] = []
    for ticker in returns.columns:
        meta = TICKER_META.get(ticker, {})
        basket = meta.get("basket", "other")
        if group_mode == "ai_vs_hedge":
            if basket == "hedge":
                group = "Macro Hedge"
            else:
                group = "AI Supply Chain"
        elif group_mode == "basket":
            group = basket_label(ticker)
        else:
            group = ticker

        for value in returns[ticker].dropna():
            rows.append({"group": group, "daily_return": float(value), "ticker": ticker})

    return pd.DataFrame(rows)


def compare_return_baskets(
    returns: pd.DataFrame,
    group_mode: str = "ai_vs_hedge",
    alpha: float = 0.05,
    output_pdf: str | None = None,
    report_metadata: dict[str, Any] | None = None,
) -> tuple[dict, dict | None, pd.DataFrame]:
    """
    Run statistical inference on daily returns grouped by basket.
    Returns test results, assumptions, and the long-form input DataFrame.
    """
    long_df = returns_to_long(returns, group_mode=group_mode)
    metadata = report_metadata or {
        "client_name": "AI Supply Chain Portfolio",
        "prepared_by": "AI Finance & Stats Hub",
        "audience": "researcher",
    }
    test_results, assumptions = analyze(
        long_df,
        group_col="group",
        value_col="daily_return",
        alpha=alpha,
        output_pdf=output_pdf,
        report_metadata=metadata,
        verbose=False,
    )
    return test_results, assumptions, long_df


def export_basket_comparison_csv(returns: pd.DataFrame, path: Path | None = None) -> Path:
    """Export long-format returns for external stats CLI."""
    path = path or REPORTS_DIR / "portfolio_returns_long.csv"
    path.parent.mkdir(parents=True, exist_ok=True)
    returns_to_long(returns, group_mode="ai_vs_hedge").to_csv(path, index=False)
    return path
