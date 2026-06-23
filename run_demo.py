"""Regenerate sample A/B reports from bundled demo data."""

from pathlib import Path

import pandas as pd

from src.config import DEMO_DATA_DIR, REPORTS_DIR
from src.stats.inference import run_pipeline

SCENARIOS = [
    ("conversion_data.csv", "group", "converted", "conversion_z_report.pdf"),
    ("revenue_data.csv", "group", "revenue", "revenue_t_report.pdf"),
    ("session_data.csv", "group", "session_minutes", "session_nonparametric_report.pdf"),
    ("feedback_data.csv", "group", "rating", "feedback_chisquare_report.pdf"),
]


def main() -> None:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    for data_file, group_col, value_col, out_name in SCENARIOS:
        path = DEMO_DATA_DIR / data_file
        df = pd.read_csv(path)
        out = REPORTS_DIR / out_name
        print(f"Generating {out.name} from {data_file}...")
        run_pipeline(
            df,
            group_col=group_col,
            value_col=value_col,
            output_pdf=str(out),
            report_metadata={"audience": "researcher"},
        )
    print("All sample reports written to reports/")


if __name__ == "__main__":
    main()
