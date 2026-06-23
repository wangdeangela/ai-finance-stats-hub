"""Tests for portfolio inference bridge."""

from src.bridge.portfolio_inference import compare_return_baskets, returns_to_long
from src.finance.analysis import daily_returns, run_full_analysis
from src.finance.data_fetch import load_demo_prices


def test_returns_to_long_ai_vs_hedge():
    prices = load_demo_prices()
    returns = daily_returns(prices)
    long_df = returns_to_long(returns, group_mode="ai_vs_hedge")
    groups = set(long_df["group"].unique())
    assert groups == {"AI Supply Chain", "Macro Hedge"}
    assert len(long_df) == returns.notna().sum().sum()


def test_compare_return_baskets_runs():
    results = run_full_analysis(load_demo_prices())
    test_results, assumptions, long_df = compare_return_baskets(
        results["simple_returns"],
        group_mode="ai_vs_hedge",
        output_pdf=None,
    )
    assert "p_value" in test_results
    assert len(long_df) > 0
