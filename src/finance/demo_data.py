"""Synthetic OHLCV for offline runs when yfinance is rate-limited."""

from __future__ import annotations

import numpy as np
import pandas as pd

from src.config import TICKERS

_PROFILE = {
    "GOOGL": {"start": 175.0, "vol": 0.018, "drift": 0.00035},
    "VRT": {"start": 95.0, "vol": 0.028, "drift": 0.0005},
    "SLV": {"start": 24.0, "vol": 0.022, "drift": 0.00015},
    "AVGO": {"start": 165.0, "vol": 0.025, "drift": 0.00045},
    "ASML": {"start": 880.0, "vol": 0.024, "drift": 0.0004},
    "TSM": {"start": 175.0, "vol": 0.022, "drift": 0.00042},
    "NVDA": {"start": 120.0, "vol": 0.035, "drift": 0.00055},
}


def generate_synthetic_ohlcv(
    tickers: list[str] | None = None,
    years: int = 2,
    seed: int = 42,
) -> dict[str, pd.DataFrame]:
    """Generate business-day OHLCV panels via geometric Brownian motion."""
    tickers = tickers or TICKERS
    rng = np.random.default_rng(seed)
    n_days = 252 * years
    days = pd.bdate_range(end=pd.Timestamp.today().normalize(), periods=n_days)

    frames: dict[str, pd.DataFrame] = {}
    for symbol in tickers:
        profile = _PROFILE.get(
            symbol,
            {"start": 100.0, "vol": 0.02, "drift": 0.0003},
        )
        shocks = rng.normal(profile["drift"], profile["vol"], n_days)
        close = profile["start"] * np.cumprod(1 + shocks)
        noise = rng.normal(0, 0.003, n_days)
        open_ = close * (1 + noise)
        high = np.maximum(open_, close) * (1 + np.abs(rng.normal(0, 0.004, n_days)))
        low = np.minimum(open_, close) * (1 - np.abs(rng.normal(0, 0.004, n_days)))
        volume = rng.integers(1_000_000, 50_000_000, n_days)

        frames[symbol] = pd.DataFrame(
            {"Open": open_, "High": high, "Low": low, "Close": close, "Volume": volume},
            index=days,
        )
    return frames
