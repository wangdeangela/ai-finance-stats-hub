"""Core analysis: returns, rolling metrics, correlation, resampling."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import jarque_bera
from statsmodels.tsa.stattools import adfuller

from src.config import PROCESSED_DIR, ROLLING_LONG, ROLLING_SHORT, TICKERS
from src.finance.utils import cumulative_log_return, log_returns_from_prices, summary_stats, vectorized_summary


def load_prices_wide(path: Path | None = None) -> pd.DataFrame:
    path = path or PROCESSED_DIR / "prices_wide.csv"
    df = pd.read_csv(path, index_col=0, parse_dates=True)
    df.index = pd.to_datetime(df.index)
    return df.sort_index()


def daily_returns(prices: pd.DataFrame) -> pd.DataFrame:
    """Simple daily percentage returns."""
    return prices.pct_change().dropna(how="all")


def rolling_moving_averages(prices: pd.DataFrame) -> pd.DataFrame:
    """Stack 20-day and 60-day moving averages for each ticker."""
    parts = []
    for col in prices.columns:
        ma20 = prices[col].rolling(window=ROLLING_SHORT).mean().rename(f"{col}_MA20")
        ma60 = prices[col].rolling(window=ROLLING_LONG).mean().rename(f"{col}_MA60")
        parts.extend([ma20, ma60])
    return pd.concat(parts, axis=1)


def rolling_volatility(returns: pd.DataFrame, window: int = ROLLING_SHORT) -> pd.DataFrame:
    """Rolling standard deviation of daily returns."""
    return returns.rolling(window=window).std()


def correlation_matrix(returns: pd.DataFrame) -> pd.DataFrame:
    return returns.corr()


def monthly_mean_returns(returns: pd.DataFrame) -> pd.DataFrame:
    """Group by calendar month and average daily returns."""
    monthly = returns.groupby(returns.index.to_period("M")).mean()
    monthly.index = monthly.index.astype(str)
    return monthly


def resample_monthly_returns(returns: pd.DataFrame) -> pd.DataFrame:
    """Resample to month-end and compound daily returns within each month."""
    compounded = (1 + returns).resample("ME").prod() - 1
    return compounded


def normality_tests(returns: pd.DataFrame) -> pd.DataFrame:
    """Jarque-Bera test on daily simple returns per ticker."""
    rows = []
    for col in returns.columns:
        series = returns[col].dropna()
        stat, p_value = jarque_bera(series)
        rows.append(
            {
                "jb_stat": stat,
                "p_value": p_value,
                "reject_normal_5pct": p_value < 0.05,
            }
        )
    return pd.DataFrame(rows, index=returns.columns)


def adf_stationarity_tests(series: pd.DataFrame, kind: str) -> pd.DataFrame:
    """Augmented Dickey-Fuller test per column."""
    rows = []
    for col in series.columns:
        values = series[col].dropna()
        adf_stat, p_value, *_ = adfuller(values, autolag="AIC")
        rows.append(
            {
                "kind": kind,
                "adf_stat": adf_stat,
                "p_value": p_value,
                "stationary_5pct": p_value < 0.05,
            }
        )
    return pd.DataFrame(rows, index=series.columns)


def run_full_analysis(prices: pd.DataFrame | None = None) -> dict:
    """Run all analysis steps and return a dict of results for notebooks/plots."""
    prices = prices if prices is not None else load_prices_wide()
    simple_ret = daily_returns(prices)
    log_ret = log_returns_from_prices(prices).dropna(how="all")

    stats_loop = summary_stats(simple_ret)
    stats_broadcast = vectorized_summary(simple_ret)
    cum_log = cumulative_log_return(log_ret)

    ma = rolling_moving_averages(prices)
    roll_vol = rolling_volatility(simple_ret)
    corr = correlation_matrix(simple_ret)
    monthly_gb = monthly_mean_returns(simple_ret)
    monthly_rs = resample_monthly_returns(simple_ret)
    normality = normality_tests(simple_ret)
    adf_prices = adf_stationarity_tests(prices, kind="price")
    adf_returns = adf_stationarity_tests(simple_ret, kind="return")

    vol_spikes = {}
    for col in roll_vol.columns:
        threshold = roll_vol[col].quantile(0.99)
        spikes = roll_vol[col][roll_vol[col] >= threshold].dropna()
        vol_spikes[col] = spikes

    return {
        "prices": prices,
        "simple_returns": simple_ret,
        "log_returns": log_ret,
        "stats_loop": stats_loop,
        "stats_broadcast": stats_broadcast,
        "cumulative_log_return": cum_log,
        "moving_averages": ma,
        "rolling_volatility": roll_vol,
        "correlation": corr,
        "monthly_groupby": monthly_gb,
        "monthly_resample": monthly_rs,
        "normality_tests": normality,
        "adf_price_tests": adf_prices,
        "adf_return_tests": adf_returns,
        "volatility_spikes": vol_spikes,
    }
