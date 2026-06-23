"""Statistical inference pipeline - auto-routes tests and generates PDF reports."""

from __future__ import annotations

import argparse
import os
import sys
from typing import Any

import numpy as np
import pandas as pd

from src.stats import ab_testers as testers
from src.stats import assumptions_checker as checker
from src.stats import pdf_generator as generator


def load_data(filepath: str) -> pd.DataFrame:
    """Load data from CSV."""
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"File not found at '{filepath}'")
    return pd.read_csv(filepath)


def analyze(
    df: pd.DataFrame,
    group_col: str,
    value_col: str,
    alpha: float = 0.05,
    alternative: str = "two-sided",
    force_test: str | None = None,
    output_pdf: str | None = None,
    report_metadata: dict[str, Any] | None = None,
    verbose: bool = True,
) -> tuple[dict, dict | None]:
    """
    Analyze data, run calculations, and optionally write a PDF report.
    Returns (test_results, assumptions_results).
    """
    if verbose:
        print(f"\n--- Starting Analysis on '{value_col}' by '{group_col}' ---")

    df_clean = df[[group_col, value_col]].dropna()
    unique_groups = df_clean[group_col].unique()
    if len(unique_groups) < 2:
        raise ValueError(
            f"Expected at least 2 groups in column '{group_col}', "
            f"found {len(unique_groups)}: {unique_groups}"
        )

    group_names = sorted(list(unique_groups))
    group_data = [df_clean[df_clean[group_col] == name][value_col] for name in group_names]
    if verbose:
        for idx, (name, data) in enumerate(zip(group_names, group_data), start=1):
            print(f"Group {idx} ({name}): n = {len(data)}")

    values = df_clean[value_col].values
    is_numeric = np.issubdtype(values.dtype, np.number)
    unique_vals = np.unique(values)
    is_binary = len(unique_vals) <= 2 and (
        all(v in [0, 1, 0.0, 1.0] for v in unique_vals)
        or all(v in [True, False] for v in unique_vals)
        or all(
            isinstance(v, str) and v.lower() in ["yes", "no", "success", "failure", "true", "false"]
            for v in unique_vals
        )
    )

    if force_test:
        test_type = force_test.lower()
    elif is_binary:
        test_type = "proportion_z"
    elif is_numeric and len(group_names) == 2:
        test_type = "means_t"
    elif is_numeric:
        test_type = "anova"
    else:
        test_type = "chi_square"

    if verbose:
        kind = (
            "Binary/Success-Failure"
            if is_binary
            else "Continuous Numerical"
            if is_numeric
            else "Categorical"
        )
        print(f"Detected variable type: {kind}")
        print(f"Selected route: {test_type.upper()}")

    test_results = None
    assumptions_results = None

    if test_type == "proportion_z":

        def count_successes(series: pd.Series) -> int:
            clean = series.dropna()
            if clean.empty:
                return 0
            if np.issubdtype(clean.dtype, np.number):
                unique_numeric = set(clean.astype(float).unique())
                if unique_numeric.issubset({0.0, 1.0}):
                    return int((clean.astype(float) == 1.0).sum())
            normalized = clean.astype(str).str.strip().str.lower()
            success_labels = ["1", "true", "yes", "success"]
            for label in success_labels:
                if label in set(normalized.unique()):
                    return int((normalized == label).sum())
            max_val = sorted(normalized.unique())[-1]
            return int((normalized == max_val).sum())

        if len(group_names) != 2:
            contingency_table = pd.crosstab(df_clean[group_col], df_clean[value_col])
            observed = contingency_table.values
            test_results = testers.run_chi_square_test(observed, alpha)
        else:
            group_a_data, group_b_data = group_data[0], group_data[1]
            x_a = count_successes(group_a_data)
            n_a = len(group_a_data)
            x_b = count_successes(group_b_data)
            n_b = len(group_b_data)
            if verbose:
                print(
                    f"Proportion conversions: Group A = {x_a}/{n_a} ({x_a/n_a:.4%}), "
                    f"Group B = {x_b}/{n_b} ({x_b/n_b:.4%})"
                )
            test_results = testers.run_proportion_z_test(x_a, n_a, x_b, n_b, alpha, alternative)

    elif test_type == "means_t":
        if verbose:
            print("Running normality and variance check...")
        group_a_data, group_b_data = group_data[0], group_data[1]
        assumptions_results = checker.analyze_assumptions(
            group_a_data.values, group_b_data.values, alpha
        )
        rec = assumptions_results["recommended_test"]
        if verbose:
            print(f"Normality A: {assumptions_results['group_a_normality']['note']}")
            print(f"Normality B: {assumptions_results['group_b_normality']['note']}")
            print(f"Equal Variance: {assumptions_results['variance_equality']['note']}")
            print(f"Recommendation: Use {rec}")
        if "Student's T-test" in rec:
            test_results = testers.run_means_t_test(
                group_a_data.values, group_b_data.values, alpha, equal_var=True, alternative=alternative
            )
        elif "Welch's T-test" in rec:
            test_results = testers.run_means_t_test(
                group_a_data.values, group_b_data.values, alpha, equal_var=False, alternative=alternative
            )
        else:
            test_results = testers.run_mann_whitney_u_test(
                group_a_data.values, group_b_data.values, alpha, alternative=alternative
            )

    elif test_type == "anova":
        if verbose:
            print("Running One-Way ANOVA for 3+ numeric groups...")
        numeric_groups = [data.astype(float).values for data in group_data]
        test_results = testers.run_one_way_anova(numeric_groups, group_names, alpha)

    elif test_type in {"chi_square", "categorical"}:
        contingency_table = pd.crosstab(df_clean[group_col], df_clean[value_col])
        if verbose:
            print("Contingency Table (Observed):")
            print(contingency_table)
        observed = contingency_table.values
        test_results = testers.run_chi_square_test(observed, alpha)

    else:
        raise ValueError(f"Unknown test route '{force_test}'")

    test_results["group_names"] = group_names
    test_results["group_a_name"] = group_names[0]
    test_results["group_b_name"] = group_names[1] if len(group_names) > 1 else "Group B"

    if output_pdf:
        if verbose:
            print(f"Generating PDF report: {output_pdf}...")
        generator.generate_report(test_results, assumptions_results, output_pdf, metadata=report_metadata)
        if verbose:
            print("Report completed successfully!")

    return test_results, assumptions_results


def run_pipeline(
    df: pd.DataFrame,
    group_col: str,
    value_col: str,
    alpha: float = 0.05,
    alternative: str = "two-sided",
    output_pdf: str = "ab_test_report.pdf",
    force_test: str | None = None,
    report_metadata: dict[str, Any] | None = None,
) -> tuple[dict, dict | None]:
    """CLI-compatible wrapper around analyze()."""
    return analyze(
        df,
        group_col,
        value_col,
        alpha=alpha,
        alternative=alternative,
        force_test=force_test,
        output_pdf=output_pdf,
        report_metadata=report_metadata,
        verbose=True,
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Stats inference: A/B testing & statistical reports"
    )
    parser.add_argument("--data", required=True, help="Path to input CSV data file")
    parser.add_argument("--group-col", required=True, help="Group/variant column name")
    parser.add_argument("--value-col", required=True, help="Outcome metric column name")
    parser.add_argument("--alpha", type=float, default=0.05, help="Significance level")
    parser.add_argument(
        "--alternative",
        choices=["two-sided", "greater", "less"],
        default="two-sided",
        help="Alternative hypothesis",
    )
    parser.add_argument("--output", default="ab_test_report.pdf", help="Output PDF path")
    parser.add_argument(
        "--force-test",
        choices=["proportion_z", "means_t", "categorical", "mann_whitney"],
        default=None,
        help="Force a specific statistical test",
    )
    parser.add_argument("--client-name", default=None, help="Client/project name on PDF cover")
    parser.add_argument("--prepared-by", default=None, help="Analyst name on PDF cover")
    parser.add_argument(
        "--audience",
        choices=["fiverr_buyer", "small_business", "researcher"],
        default="researcher",
        help="PDF audience style",
    )
    args = parser.parse_args(argv)

    try:
        df = load_data(args.data)
        run_pipeline(
            df,
            group_col=args.group_col,
            value_col=args.value_col,
            alpha=args.alpha,
            alternative=args.alternative,
            output_pdf=args.output,
            force_test=args.force_test,
            report_metadata={
                "client_name": args.client_name,
                "prepared_by": args.prepared_by,
                "audience": args.audience,
            },
        )
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
