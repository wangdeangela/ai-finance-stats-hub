"""Download and clean market data for assignment tickers."""

from __future__ import annotations

import time
from pathlib import Path

import pandas as pd
import yfinance as yf

from src.config import DEMO_PRICES_PATH, PERIOD, PROCESSED_DIR, RAW_DIR, TICKERS
from src.finance.demo_data import generate_synthetic_ohlcv


def load_demo_prices() -> pd.DataFrame:
    """Load bundled demo wide price table (reproducible offline runs)."""
    if DEMO_PRICES_PATH.exists():
        df = pd.read_csv(DEMO_PRICES_PATH, index_col=0, parse_dates=True)
        df.index = pd.to_datetime(df.index)
        return df.sort_index()
    wide = build_close_wide(generate_synthetic_ohlcv(seed=42))
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    wide.to_csv(DEMO_PRICES_PATH)
    return wide


def download_all(
    tickers: list[str] | None = None,
    period: str = PERIOD,
    retries: int = 4,
    pause_seconds: float = 3.0,
) -> dict[str, pd.DataFrame]:
    """Download daily OHLCV for all tickers in one batch request (with retries)."""
    tickers = tickers or TICKERS
    last_error: Exception | None = None

    for attempt in range(retries):
        try:
            panel = yf.download(
                tickers,
                period=period,
                progress=False,
                auto_adjust=True,
                group_by="ticker",
                threads=False,
            )
            if panel.empty:
                raise ValueError("yfinance returned empty panel")

            frames: dict[str, pd.DataFrame] = {}
            if len(tickers) == 1:
                single = panel.copy()
                if isinstance(single.columns, pd.MultiIndex):
                    single.columns = single.columns.get_level_values(0)
                frames[tickers[0]] = single
            else:
                for symbol in tickers:
                    if symbol not in panel.columns.get_level_values(0):
                        raise ValueError(f"Missing column group for {symbol}")
                    df = panel[symbol].copy()
                    df = df.dropna(how="all")
                    if df.empty:
                        raise ValueError(f"No data returned for {symbol}")
                    frames[symbol] = df

            return frames
        except Exception as exc:  # noqa: BLE001 - retry on any fetch failure
            last_error = exc
            if attempt < retries - 1:
                time.sleep(pause_seconds * (attempt + 1))

    if all((RAW_DIR / f"{t}.csv").exists() for t in tickers):
        return {t: load_raw(t) for t in tickers}

    print(
        "WARNING: yfinance download failed (often rate limits). "
        "Using synthetic demo data — re-run later without --demo for live prices."
    )
    return generate_synthetic_ohlcv(tickers)


def save_raw(frames: dict[str, pd.DataFrame], directory: Path | None = None) -> None:
    """Save each ticker's data to data/raw/{TICKER}.csv."""
    directory = directory or RAW_DIR
    directory.mkdir(parents=True, exist_ok=True)
    for symbol, df in frames.items():
        path = directory / f"{symbol}.csv"
        df.to_csv(path)


def load_raw(ticker: str, directory: Path | None = None) -> pd.DataFrame:
    """Load a single raw CSV and normalize index/columns."""
    directory = directory or RAW_DIR
    df = pd.read_csv(directory / f"{ticker}.csv", index_col=0, parse_dates=True)
    return clean_single(df)


def clean_single(df: pd.DataFrame) -> pd.DataFrame:
    """Standardize one ticker's DataFrame: datetime index, lowercase columns."""
    out = df.copy()
    out.index = pd.to_datetime(out.index)
    out.columns = [str(c).strip().lower() for c in out.columns]
    out = out.sort_index()
    if "close" in out.columns:
        out["close"] = out["close"].ffill().bfill()
    out = out[~out.index.duplicated(keep="last")]
    return out


def build_close_wide(frames: dict[str, pd.DataFrame] | None = None) -> pd.DataFrame:
    """Merge closing prices into a wide table (one column per ticker)."""
    frames = frames or {t: load_raw(t) for t in TICKERS}
    series_list = []
    for symbol, df in frames.items():
        cleaned = clean_single(df)
        close = cleaned["close"].rename(symbol)
        series_list.append(close)

    wide = series_list[0].to_frame()
    for s in series_list[1:]:
        wide = wide.merge(s, left_index=True, right_index=True, how="outer")

    wide = wide.sort_index()
    wide = wide.dropna(how="all")
    wide = wide.ffill().dropna()
    return wide


def run_pipeline(save: bool = True, use_cache: bool = True, demo: bool = False) -> pd.DataFrame:
    """Download, save raw CSVs, build wide close table, save processed CSV."""
    if demo:
        return load_demo_prices()
    if use_cache and all((RAW_DIR / f"{t}.csv").exists() for t in TICKERS):
        frames = {t: load_raw(t) for t in TICKERS}
    else:
        frames = download_all()
    if save:
        save_raw(frames)
    wide = build_close_wide(frames)
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    wide.to_csv(PROCESSED_DIR / "prices_wide.csv")
    return wide
