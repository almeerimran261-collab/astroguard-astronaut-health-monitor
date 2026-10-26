"""
Personal-baseline calculations for AstroGuard.

This module defines each astronaut's initial normal pattern using
mission days 1 through 14. It does not create alerts yet.
"""

from pathlib import Path

import numpy as np
import pandas as pd


# Resolve paths relative to the project root.
PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = PROJECT_ROOT / "data" / "processed" / "astronaut_health.csv"


FEATURE_COLUMNS = [
    "sleep_hours",
    "sleep_quality",
    "resting_heart_rate",
    "exercise_minutes",
    "fatigue_score",
    "stress_score",
    "reaction_time_ms",
    "workload_hours",
]


# For each feature, True means that higher values are potentially concerning.
# False means that lower values are potentially concerning.
HIGHER_IS_CONCERNING = {
    "sleep_hours": False,
    "sleep_quality": False,
    "resting_heart_rate": True,
    "exercise_minutes": False,
    "fatigue_score": True,
    "stress_score": True,
    "reaction_time_ms": True,
    "workload_hours": True,
}


def load_health_data(path: Path = DATA_PATH) -> pd.DataFrame:
    """
    Load and validate the processed astronaut-health dataset.
    """

    if not path.exists():
        raise FileNotFoundError(
            f"Dataset not found at: {path}"
        )

    data = pd.read_csv(path, parse_dates=["timestamp"])

    required_columns = [
        "crew_id",
        "mission_day",
        "timestamp",
        *FEATURE_COLUMNS,
    ]

    missing_columns = [
        column for column in required_columns
        if column not in data.columns
    ]

    if missing_columns:
        raise ValueError(
            f"Dataset is missing required columns: {missing_columns}"
        )

    data = data.sort_values(
        ["crew_id", "mission_day"]
    ).reset_index(drop=True)

    return data


def calculate_personal_baselines(
    data: pd.DataFrame,
    baseline_days: int = 14,
) -> pd.DataFrame:
    """
    Calculate a separate baseline for every astronaut.

    The baseline uses mission days 1 through baseline_days.
    Missing values are ignored when calculating each mean, median,
    standard deviation, and MAD.
    """

    baseline_data = data[
        data["mission_day"].between(1, baseline_days)
    ].copy()

    if baseline_data.empty:
        raise ValueError("The baseline period contains no records.")

    grouped = baseline_data.groupby("crew_id")

    mean_values = grouped[FEATURE_COLUMNS].mean().add_suffix("_mean")
    median_values = grouped[FEATURE_COLUMNS].median().add_suffix("_median")
    std_values = grouped[FEATURE_COLUMNS].std().add_suffix("_std")

    # Median absolute deviation:
    # MAD = median(abs(value - median))
    mad_values = grouped[FEATURE_COLUMNS].agg(
        lambda column: np.median(
            np.abs(column.dropna() - np.median(column.dropna()))
        )
        if column.dropna().size > 0
        else np.nan
    ).add_suffix("_mad")

    valid_counts = grouped[FEATURE_COLUMNS].count().add_suffix(
        "_valid_count"
    )

    baselines = pd.concat(
        [
            mean_values,
            median_values,
            std_values,
            mad_values,
            valid_counts,
        ],
        axis=1,
    )

    baselines["baseline_days"] = baseline_days
    baselines["baseline_start_day"] = 1
    baselines["baseline_end_day"] = baseline_days

    return baselines.reset_index()


def add_baseline_features(
    data: pd.DataFrame,
    baselines: pd.DataFrame,
) -> pd.DataFrame:
    """
    Add personal-baseline differences and robust deviations.

    The returned data contains one row per original measurement.
    """

    result = data.copy()

    result = result.merge(
        baselines,
        on="crew_id",
        how="left",
        validate="many_to_one",
    )

    for feature in FEATURE_COLUMNS:
        mean_column = f"{feature}_mean"
        median_column = f"{feature}_median"
        mad_column = f"{feature}_mad"

        result[f"{feature}_difference"] = (
            result[feature] - result[mean_column]
        )

        # Robust z-score based on the baseline median and MAD.
        # 0.6745 makes MAD comparable to standard deviation
        # for a normally distributed variable.
        mad_scale = result[mad_column].replace(0, np.nan)

        result[f"{feature}_robust_z"] = (
            0.6745
            * (result[feature] - result[median_column])
            / mad_scale
        )

        # If MAD is unavailable or zero, use the baseline standard
        # deviation as a fallback.
        std_column = f"{feature}_std"
        fallback_scale = result[std_column].replace(0, np.nan)

        fallback_z = (
            result[feature] - result[mean_column]
        ) / fallback_scale

        result[f"{feature}_robust_z"] = (
            result[f"{feature}_robust_z"].fillna(fallback_z)
        )

        # Convert the raw deviation to a concerning deviation.
        # For example:
        # - low sleep is concerning, so the sign is reversed
        # - high fatigue is concerning, so the sign is preserved
        if HIGHER_IS_CONCERNING[feature]:
            result[f"{feature}_concerning_z"] = (
                result[f"{feature}_robust_z"]
            )
        else:
            result[f"{feature}_concerning_z"] = (
                -result[f"{feature}_robust_z"]
            )

    return result

def add_past_only_rolling_features(
    data: pd.DataFrame,
    window: int = 7,
    minimum_periods: int = 3,
) -> pd.DataFrame:
    """
    Add rolling statistics using only measurements from previous days.

    The current day's value is excluded with shift(1). This prevents
    the current value and future values from influencing the historical
    reference used for the current row.
    """

    if window < 2:
        raise ValueError("The rolling window must be at least 2 days.")

    if minimum_periods < 1 or minimum_periods > window:
        raise ValueError(
            "minimum_periods must be between 1 and the window size."
        )

    result = data.sort_values(
        ["crew_id", "mission_day"]
    ).reset_index(drop=True).copy()

    grouped = result.groupby("crew_id", sort=False)

    for feature in FEATURE_COLUMNS:
        result[f"{feature}_past_{window}d_mean"] = (
            grouped[feature]
            .transform(
                lambda values: values.shift(1).rolling(
                    window=window,
                    min_periods=minimum_periods,
                ).mean()
            )
        )

        result[f"{feature}_past_{window}d_std"] = (
            grouped[feature]
            .transform(
                lambda values: values.shift(1).rolling(
                    window=window,
                    min_periods=minimum_periods,
                ).std()
            )
        )

        result[f"{feature}_past_{window}d_count"] = (
            grouped[feature]
            .transform(
                lambda values: values.shift(1).rolling(
                    window=window,
                    min_periods=minimum_periods,
                ).count()
            )
        )

    return result


def build_baseline_features(
    data: pd.DataFrame,
    baseline_days: int = 14,
    rolling_window: int = 7,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Calculate personal baselines, baseline deviations, and
    past-only rolling features.

    Returns:
        enriched_data, baselines
    """

    baselines = calculate_personal_baselines(
        data,
        baseline_days=baseline_days,
    )

    enriched_data = add_baseline_features(
        data,
        baselines,
    )

    enriched_data = add_past_only_rolling_features(
        enriched_data,
        window=rolling_window,
        minimum_periods=3,
    )

    return enriched_data, baselines


    print("Dataset shape:", health_data.shape)
    print("Baseline shape:", baselines.shape)
    print("Enriched data shape:", enriched_data.shape)
    print()
    print("Baseline columns:")
    print(baselines.columns.tolist())
    print()
    print("First five baseline rows:")
    print(baselines.head().to_string(index=False))
