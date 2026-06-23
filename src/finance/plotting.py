"""Generate charts for the portfolio report."""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from matplotlib.figure import Figure

from src.config import IMAGES_DIR, TICKERS


def _ensure_images_dir() -> Path:
    IMAGES_DIR.mkdir(parents=True, exist_ok=True)
    return IMAGES_DIR


def plot_cumulative_returns(cum_log: pd.DataFrame, save: bool = True) -> Path | Figure:
    fig, ax = plt.subplots(figsize=(12, 5))
    for col in cum_log.columns:
        cum_log[col].plot(ax=ax, label=col)
    ax.set_title("Cumulative Log Returns (2Y)")
    ax.set_ylabel("Cumulative log return")
    ax.legend(ncol=2, fontsize=8)
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    if save:
        path = _ensure_images_dir() / "cumulative_log_returns.png"
        fig.savefig(path, dpi=150)
        plt.close(fig)
        return path
    return fig


def plot_correlation_heatmap(corr: pd.DataFrame, save: bool = True) -> Path | Figure:
    fig, ax = plt.subplots(figsize=(7, 6))
    sns.heatmap(corr, annot=True, fmt=".2f", cmap="RdYlGn", center=0, ax=ax, vmin=-1, vmax=1)
    ax.set_title("Daily Return Correlation Matrix")
    plt.tight_layout()
    if save:
        path = _ensure_images_dir() / "correlation_heatmap.png"
        fig.savefig(path, dpi=150)
        plt.close(fig)
        return path
    return fig


def plot_rolling_volatility(roll_vol: pd.DataFrame, save: bool = True) -> Path | Figure:
    fig, ax = plt.subplots(figsize=(12, 5))
    for col in roll_vol.columns:
        roll_vol[col].plot(ax=ax, label=col, alpha=0.8)
    ax.set_title("20-Day Rolling Volatility (Daily Returns)")
    ax.set_ylabel("Std dev")
    ax.legend(ncol=2, fontsize=8)
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    if save:
        path = _ensure_images_dir() / "rolling_volatility.png"
        fig.savefig(path, dpi=150)
        plt.close(fig)
        return path
    return fig


def plot_monthly_returns_bar(monthly: pd.DataFrame, save: bool = True) -> Path | Figure:
    """Bar chart of last 12 months average return for each ticker."""
    tail = monthly.tail(12)
    x = np.arange(len(tail))
    tickers = [c for c in TICKERS if c in tail.columns]
    width = 0.8 / max(len(tickers), 1)
    fig, ax = plt.subplots(figsize=(12, 5))
    for i, col in enumerate(tickers):
        ax.bar(x + i * width, tail[col], width=width, label=col)
    ax.set_xticks(x + width * (len(tickers) - 1) / 2)
    ax.set_xticklabels(tail.index, rotation=45, ha="right")
    ax.set_title("Monthly Mean Daily Returns (Last 12 Months)")
    ax.set_ylabel("Mean daily return")
    ax.legend(ncol=4, fontsize=8)
    ax.grid(True, axis="y", alpha=0.3)
    plt.tight_layout()
    if save:
        path = _ensure_images_dir() / "monthly_returns_bar.png"
        fig.savefig(path, dpi=150)
        plt.close(fig)
        return path
    return fig


def generate_all_figures(results: dict) -> list[Path]:
    paths = [
        plot_cumulative_returns(results["cumulative_log_return"]),
        plot_correlation_heatmap(results["correlation"]),
        plot_rolling_volatility(results["rolling_volatility"]),
        plot_monthly_returns_bar(results["monthly_groupby"]),
    ]
    return [p for p in paths if p is not None]
