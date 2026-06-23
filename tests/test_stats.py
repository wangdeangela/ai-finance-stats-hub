"""Tests for stats inference on sample data."""

from pathlib import Path

import pandas as pd

from src.config import DEMO_DATA_DIR
from src.stats.inference import analyze


def test_conversion_z_test_route():
    df = pd.read_csv(DEMO_DATA_DIR / "conversion_data.csv")
    test_results, _ = analyze(
        df,
        group_col="group",
        value_col="converted",
        output_pdf=None,
        verbose=False,
    )
    assert test_results["p_value"] >= 0
    assert "test_name" in test_results


def test_revenue_means_route():
    df = pd.read_csv(DEMO_DATA_DIR / "revenue_data.csv")
    test_results, assumptions = analyze(
        df,
        group_col="group",
        value_col="revenue",
        output_pdf=None,
        verbose=False,
    )
    assert test_results["p_value"] >= 0
    assert assumptions is not None
