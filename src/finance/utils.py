"""Utility functions for financial statistics."""

from __future__ import annotations

import numpy as np
import pandas as pd


def summary_stats(returns: pd.DataFrame) -> pd.DataFrame:
    """Compute mean, std, and variance for each return column using NumPy."""
    values = returns.to_numpy(dtype=float)
    return pd.DataFrame(
        {
            "mean": np.mean(values, axis=0),
            "std": np.std(values, axis=0, ddof=1),
            "var": np.var(values, axis=0, ddof=1),
        },
        index=returns.columns,
    )


def vectorized_summary(returns: pd.DataFrame) -> pd.DataFrame:
    """Same statistics as summary_stats via NumPy broadcasting."""
    arr = returns.to_numpy(dtype=float)
    means = arr.mean(axis=0)
    stds = arr.std(axis=0, ddof=1)
    vars_ = arr.var(axis=0, ddof=1)
    return pd.DataFrame({"mean": means, "std": stds, "var": vars_}, index=returns.columns)


def log_returns_from_prices(prices: pd.DataFrame) -> pd.DataFrame:
    """Compute log returns: ln(P_t / P_{t-1})."""
    ratio = prices / prices.shift(1)
    return np.log(ratio)


def cumulative_log_return(log_ret: pd.DataFrame) -> pd.DataFrame:
    """Cumulative sum of log returns along the time axis."""
    return log_ret.cumsum()
