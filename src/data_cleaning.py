"""
AstroGuard data checking (Step 7) and cleaning (Step 8).

Run from the project root:
    python src/data_cleaning.py

What it does:
    1. Reads the RAW file   data/raw/astronaut_health_raw.csv   (never changed)
    2. Prints a data-quality report on the raw data
    3. Cleans a COPY of the data
    4. Saves   data/processed/astronaut_health.csv      (cleaned data for the team)
               data/processed/data_quality_log.csv      (every issue and what we did)

Cleaning rules (from the AstroGuard guide):
    - Impossible values / sensor errors  -> set to blank (never guessed)
    - Missing values                     -> KEPT blank (never filled in);
                                            alerts should show lower confidence
    - Outliers                           -> KEPT (planned events must stay)
    - Duplicates / messy IDs             -> removed / tidied
"""
import re

import numpy as np
import pandas as pd

from data_loader import PROCESSED_PATH, RAW_PATH, load_health_data

HEALTH_COLS = [
    "sleep_hours", "sleep_quality", "resting_heart_rate", "exercise_minutes",
    "fatigue_score", "stress_score", "reaction_time_ms", "workload_hours",
]

# Physically possible ranges (min, max). Outside = impossible / sensor error.
VALID_RANGES = {
    "sleep_hours": (0, 14),
    "sleep_quality": (1, 10),
    "resting_heart_rate": (30, 200),
    "exercise_minutes": (0, 300),
    "fatigue_score": (1, 10),
    "stress_score": (1, 10),
    "reaction_time_ms": (100, 2000),
    "workload_hours": (0, 18),
}


def check_missing(df):
    """Count blanks per column."""
    counts = df[HEALTH_COLS].isna().sum()
    return counts[counts > 0]


def check_duplicates(df):
    """Exact duplicate rows, and the same astronaut+day appearing twice."""
    exact = int(df.duplicated().sum())
    same_day = int(df.duplicated(subset=["crew_id", "mission_day"]).sum())
    return exact, same_day


def check_impossible(df):
    """Rows where a value is outside its valid range (blanks are ignored)."""
    problems = []
    for col, (low, high) in VALID_RANGES.items():
        bad = df[(df[col] < low) | (df[col] > high)]
        for idx, row in bad.iterrows():
            problems.append((idx, row["crew_id"], int(row["mission_day"]), col, row[col]))
    return problems


def check_timestamps(df):
    """Dates should match mission_day, and each astronaut should have no gaps."""
    issues = []
    for crew, g in df.groupby("crew_id"):
        offsets = (g["timestamp"] - pd.to_timedelta(g["mission_day"], unit="D")).nunique()
        if offsets > 1:
            issues.append(f"{crew}: timestamps do not match mission_day")
        days = sorted(g["mission_day"].unique())
        expected = list(range(days[0], days[-1] + 1))
        if days != expected:
            issues.append(f"{crew}: missing mission days {sorted(set(expected) - set(days))}")
    return issues


def check_units(df):
    """Simple hints that a column may be in the wrong unit."""
    hints = []
    if df["reaction_time_ms"].median() < 10:
        hints.append("reaction_time_ms looks like SECONDS, not milliseconds")
    if df["sleep_hours"].median() > 24:
        hints.append("sleep_hours looks like MINUTES, not hours")
    return hints


def check_outliers(df, threshold=3.5):
    """
    Values far from THAT astronaut's own typical value (robust z-score).
    Outlier does NOT mean error: planned events show up here too.
    """
    flagged = {}
    for col in HEALTH_COLS:
        count = 0
        for _, g in df.groupby("crew_id"):
            x = g[col].dropna().astype(float)
            median = x.median()
            mad = (x - median).abs().median()
            if mad == 0:
                continue
            z = 0.6745 * (x - median) / mad
            count += int((z.abs() > threshold).sum())
        if count:
            flagged[col] = count
    return flagged


def check_ids(df):
    """Astronaut IDs should all look like Crew-01 (no spaces, no odd spellings)."""
    ids = sorted(df["crew_id"].astype(str).unique())
    bad = [i for i in ids if not re.fullmatch(r"Crew-\d{2}", i)]
    return ids, bad


def run_quality_report(df):
    print("=" * 55)
    print("ASTROGUARD DATA-QUALITY REPORT")
    print("=" * 55)
    print(f"Rows: {len(df)} | Columns: {df.shape[1]}")

    missing = check_missing(df)
    print(f"\n1) MISSING VALUES: {int(missing.sum())} total")
    for col, n in missing.items():
        print(f"   - {col}: {n}")

    exact, same_day = check_duplicates(df)
    print(f"\n2) DUPLICATES: exact duplicate rows = {exact}, "
          f"repeated astronaut+day = {same_day}")

    impossible = check_impossible(df)
    print(f"\n3) IMPOSSIBLE VALUES / SENSOR ERRORS: {len(impossible)}")
    for idx, crew, day, col, val in impossible:
        low, high = VALID_RANGES[col]
        print(f"   - row {idx}: {crew}, day {day}, {col} = {val} "
              f"(valid range {low}-{high})")

    ts = check_timestamps(df)
    print(f"\n4) TIMESTAMP PROBLEMS: {len(ts)}")
    for t in ts:
        print(f"   - {t}")

    units = check_units(df)
    print(f"\n5) UNIT PROBLEMS: {len(units)}")
    for u in units:
        print(f"   - {u}")

    outliers = check_outliers(df)
    print(f"\n6) OUTLIERS (unusual for that astronaut): {sum(outliers.values())}")
    for col, n in outliers.items():
        print(f"   - {col}: {n}")
    print("   Note: outliers are NOT errors. Planned events show up here.")

    ids, bad_ids = check_ids(df)
    print(f"\n7) CREW IDs: {ids}")
    print(f"   Badly formatted IDs: {bad_ids if bad_ids else 'none'}")

    print("\n8) DATA LEAKAGE: not checked here. Later, the ML member must "
          "never use future days to predict today.")
    print("=" * 55)


INT_COLS = ["sleep_quality", "resting_heart_rate", "exercise_minutes",
            "fatigue_score", "stress_score", "reaction_time_ms"]


def clean_data(raw_df):
    """Return (clean_df, log_df). The input is never changed."""
    df = raw_df.copy()
    log = []

    # tidy IDs, remove duplicates, sort
    df["crew_id"] = df["crew_id"].astype(str).str.strip()
    df = df.drop_duplicates()
    df = df.drop_duplicates(subset=["crew_id", "mission_day"], keep="first")
    df = df.sort_values(["crew_id", "mission_day"]).reset_index(drop=True)

    # missing values: KEEP them blank, but write them in the log
    for col in HEALTH_COLS:
        for idx in df.index[df[col].isna()]:
            log.append({
                "crew_id": df.at[idx, "crew_id"],
                "mission_day": int(df.at[idx, "mission_day"]),
                "column": col,
                "issue": "missing value",
                "original_value": "",
                "action": "kept blank (lower alert confidence, show warning)",
            })

    # impossible values: set to blank (never guess a replacement)
    for col, (low, high) in VALID_RANGES.items():
        bad_rows = df.index[(df[col] < low) | (df[col] > high)]
        for idx in bad_rows:
            log.append({
                "crew_id": df.at[idx, "crew_id"],
                "mission_day": int(df.at[idx, "mission_day"]),
                "column": col,
                "issue": f"impossible value (valid range {low}-{high})",
                "original_value": df.at[idx, col],
                "action": "set to blank (sensor error)",
            })
            df.at[idx, col] = np.nan

    # whole-number columns stay whole numbers (blanks allowed)
    for col in INT_COLS:
        df[col] = df[col].round().astype("Int64")

    log_df = pd.DataFrame(log, columns=["crew_id", "mission_day", "column",
                                        "issue", "original_value", "action"])
    return df, log_df


if __name__ == "__main__":
    raw = load_health_data(RAW_PATH)
    print(">>> BEFORE CLEANING (raw file)")
    run_quality_report(raw)

    clean, log = clean_data(raw)

    PROCESSED_PATH.parent.mkdir(parents=True, exist_ok=True)
    clean.to_csv(PROCESSED_PATH, index=False)
    log.to_csv(PROCESSED_PATH.parent / "data_quality_log.csv", index=False)

    print("\n>>> AFTER CLEANING (processed file)")
    run_quality_report(clean)
    print(f"\nSaved clean data : {PROCESSED_PATH}")
    print(f"Saved issue log  : {PROCESSED_PATH.parent / 'data_quality_log.csv'}")
    print(f"Log entries: {len(log)} (raw file was not changed)")
