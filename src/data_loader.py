"""
Load the AstroGuard astronaut health data.
Everyone on the team should load the data using this file.
"""
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
RAW_PATH = PROJECT_ROOT / "data" / "raw" / "astronaut_health_raw.csv"          # original, never edited
PROCESSED_PATH = PROJECT_ROOT / "data" / "processed" / "astronaut_health.csv"  # cleaned, used by the team

EXPECTED_COLUMNS = [
    "crew_id", "mission_day", "timestamp", "sleep_hours", "sleep_quality",
    "resting_heart_rate", "exercise_minutes", "fatigue_score", "stress_score",
    "reaction_time_ms", "workload_hours",
]


def load_health_data(path=PROCESSED_PATH):
    """Read the CSV and make sure all 11 expected columns are there."""
    df = pd.read_csv(path, parse_dates=["timestamp"])
    missing_cols = [c for c in EXPECTED_COLUMNS if c not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing columns: {missing_cols}")
    return df


if __name__ == "__main__":
    pd.set_option("display.max_columns", None)   # show all columns
    pd.set_option("display.width", 250)          # use a wider line
    df = load_health_data()
    print("Shape (rows, columns):", df.shape)
    print(df.head())
    print("\nMissing values per column:")
    print(df.isna().sum())
