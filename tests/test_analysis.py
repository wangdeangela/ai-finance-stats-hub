"""Tests for analysis module."""

import numpy as np
import pandas as pd

from src.finance.analysis import (
    adf_stationarity_tests,
    correlation_matrix,
    daily_returns,
    normality_tests,
    run_full_analysis,
)
from src.config import TICKERS
from src.finance.data_fetch import load_demo_prices


def test_daily_returns_shape():
    prices = load_demo_prices()
    rets = daily_returns(prices)
    assert rets.shape[1] == len(TICKERS)
    assert len(rets) == len(prices) - 1


def test_correlation_matrix_symmetric_and_unit_diagonal():
    prices = load_demo_prices()
    corr = correlation_matrix(daily_returns(prices))
    assert list(corr.columns) == TICKERS
    assert np.allclose(np.diag(corr), 1.0)
    assert np.allclose(corr, corr.T)


def test_run_full_analysis_keys():
    results = run_full_analysis(load_demo_prices())
    expected = {
        "prices",
        "simple_returns",
        "log_returns",
        "stats_loop",
        "stats_broadcast",
        "cumulative_log_return",
        "moving_averages",
        "rolling_volatility",
        "correlation",
        "monthly_groupby",
        "monthly_resample",
        "normality_tests",
        "adf_price_tests",
        "adf_return_tests",
        "volatility_spikes",
    }
    assert expected <= set(results.keys())
    pd.testing.assert_frame_equal(
        results["stats_loop"],
        results["stats_broadcast"],
        check_names=True,
    )


def test_normality_tests_columns():
    prices = load_demo_prices()
    rets = daily_returns(prices)
    jb = normality_tests(rets)
    assert list(jb.columns) == ["jb_stat", "p_value", "reject_normal_5pct"]
    assert len(jb) == len(TICKERS)
    assert jb["p_value"].between(0, 1).all()
