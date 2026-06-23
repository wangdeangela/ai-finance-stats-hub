"""Live single-ticker fetch via yfinance with price-change summary."""

from __future__ import annotations

import argparse
import sys

import pandas as pd
import yfinance as yf

from src.config import PERIOD, TICKERS


def download_single(ticker: str, period: str = PERIOD) -> pd.DataFrame:
    """Download daily OHLCV for one ticker."""
    symbol = ticker.upper().strip()
    panel = yf.download(
        symbol,
        period=period,
        progress=False,
        auto_adjust=True,
        threads=False,
    )
    if panel.empty:
        raise ValueError(f"yfinance returned no data for {symbol}")

    df = panel.copy()
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    df = df.dropna(how="all")
    if df.empty:
        raise ValueError(f"No usable rows for {symbol}")
    return df.sort_index()


def extract_close(df: pd.DataFrame) -> pd.Series:
    """Return close price series with a normalized column name."""
    columns = {str(c).lower(): c for c in df.columns}
    if "close" not in columns:
        raise ValueError("Downloaded data has no Close column")
    close = df[columns["close"]].astype(float)
    close.index = pd.to_datetime(close.index)
    return close.sort_index()


def summarize_price_changes(close: pd.Series) -> dict[str, float | pd.Timestamp]:
    """Compute latest close and percentage changes."""
    if len(close) < 2:
        raise ValueError("Need at least 2 trading days to compute returns")

    latest = close.iloc[-1]
    previous = close.iloc[-2]
    first = close.iloc[0]
    daily_pct = (latest / previous - 1.0) * 100.0
    period_pct = (latest / first - 1.0) * 100.0

    return {
        "latest_date": close.index[-1],
        "latest_close": float(latest),
        "previous_close": float(previous),
        "daily_pct": float(daily_pct),
        "period_pct": float(period_pct),
        "period_start": close.index[0],
    }


def print_price_summary(ticker: str, summary: dict[str, float | pd.Timestamp]) -> None:
    """Print human-readable price and return summary."""
    print(f"=== {ticker.upper()} quote summary ===")
    print(f"Latest date: {summary['latest_date'].date()}")
    print(f"Close: {summary['latest_close']:.2f}")
    print(f"Prev close: {summary['previous_close']:.2f}")
    print(f"Daily change: {summary['daily_pct']:+.2f}%")
    print(
        f"Period change ({summary['period_start'].date()} → {summary['latest_date'].date()}): "
        f"{summary['period_pct']:+.2f}%"
    )


def run(ticker: str, period: str = PERIOD) -> dict[str, float | pd.Timestamp]:
    """Fetch live data and print summary."""
    ohlcv = download_single(ticker, period=period)
    close = extract_close(ohlcv)
    summary = summarize_price_changes(close)
    print_price_summary(ticker, summary)
    return summary


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Fetch one ticker and print price changes.")
    parser.add_argument(
        "ticker",
        nargs="?",
        default=TICKERS[0],
        help=f"Ticker symbol (default: {TICKERS[0]})",
    )
    parser.add_argument("--period", default=PERIOD, help=f"yfinance period (default: {PERIOD})")
    args = parser.parse_args(argv)

    try:
        run(args.ticker, period=args.period)
    except Exception as exc:  # noqa: BLE001
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
