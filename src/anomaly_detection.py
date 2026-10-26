"""
Point-level anomaly detection for AstroGuard.

This module identifies measurements that are unusually concerning
relative to each astronaut's personal baseline.

It does not diagnose a medical condition.
It does not yet assign Stable, Watch, or Review Required states.
"""

from pathlib import Path

import pandas as pd

from src.baseline import (
    FEATURE_COLUMNS,
    HIGHER_IS_CONCERNING,
    build_baseline_features,
    load_health_data,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]
ML_RESULTS_DIR = PROJECT_ROOT / "assets" / "ml_results"


# This is an initial engineering threshold.
# It is not a clinical threshold.
POINT_ANOMALY_THRESHOLD = 3.5

# Initial baseline validity requirement.
# A baseline with fewer than this many valid values is considered weak.
MINIMUM_BASELINE_OBSERVATIONS = 10

# Alerts should not normally be evaluated during the initial baseline period.
BASELINE_DAYS = 14
PERSISTENCE_DAYS = 3



def get_concerning_z_column(feature: str) -> str:
    """
    Return the name of the concerning-direction z-score column.
    """

    return f"{feature}_concerning_z"


def get_missing_column(feature: str) -> str:
    """
    Return the name of the missing-value indicator column.
    """

    return f"{feature}_missing"


def add_data_quality_flags(
    data: pd.DataFrame,
    minimum_baseline_observations: int = MINIMUM_BASELINE_OBSERVATIONS,
) -> pd.DataFrame:
    """
    Add missing-value and baseline-quality flags.

    Missing values are not silently imputed or deleted.
    """

    result = data.copy()

    missing_columns = []

    for feature in FEATURE_COLUMNS:
        missing_column = get_missing_column(feature)
        result[missing_column] = result[feature].isna()
        missing_columns.append(missing_column)

    result["missing_feature_count"] = (
        result[missing_columns].sum(axis=1)
    )

    valid_count_columns = [
        f"{feature}_valid_count"
        for feature in FEATURE_COLUMNS
    ]

    result["insufficient_baseline_count"] = (
        result[valid_count_columns]
        .lt(minimum_baseline_observations)
        .sum(axis=1)
    )

    result["baseline_is_sufficient"] = (
        result["insufficient_baseline_count"] == 0
    )

    result["data_quality_warning"] = ""

    missing_mask = result["missing_feature_count"] > 0
    insufficient_mask = result["insufficient_baseline_count"] > 0

    result.loc[
        missing_mask,
        "data_quality_warning",
    ] = "One or more current measurements are missing."

    result.loc[
        insufficient_mask,
        "data_quality_warning",
    ] = (
        "One or more personal baselines have insufficient valid observations."
    )

    result.loc[
        missing_mask & insufficient_mask,
        "data_quality_warning",
    ] = (
        "Current measurements are missing and one or more personal "
        "baselines have insufficient valid observations."
    )

    return result


def add_point_anomaly_flags(
    data: pd.DataFrame,
    threshold: float = POINT_ANOMALY_THRESHOLD,
    baseline_days: int = BASELINE_DAYS,
) -> pd.DataFrame:
    """
    Add point-level anomaly flags for every monitored feature.

    A feature is flagged when its concerning-direction robust z-score
    reaches the configured threshold.

    The first baseline_days are marked as warm-up days. They can
    contain diagnostic flags for inspection, but they are not eligible
    for production-style alerting.
    """

    if threshold <= 0:
        raise ValueError("The anomaly threshold must be positive.")

    result = data.copy()

    anomaly_columns = []

    for feature in FEATURE_COLUMNS:
        z_column = get_concerning_z_column(feature)
        anomaly_column = f"{feature}_point_anomaly"

        if z_column not in result.columns:
            raise ValueError(
                f"Required column is missing: {z_column}"
            )

        result[anomaly_column] = (
            result[z_column] >= threshold
        ).fillna(False)

        anomaly_columns.append(anomaly_column)

    result["point_anomaly_count"] = (
        result[anomaly_columns].sum(axis=1)
    )

    result["point_anomaly_detected"] = (
        result["point_anomaly_count"] > 0
    )

    result["warmup_period"] = (
        result["mission_day"] <= baseline_days
    )

    result["eligible_for_alert"] = (
        ~result["warmup_period"]
        & result["baseline_is_sufficient"]
    )

    result["eligible_point_anomaly"] = (
        result["point_anomaly_detected"]
        & result["eligible_for_alert"]
    )

    return result

def add_persistence_flags(
    data: pd.DataFrame,
    persistence_days: int = PERSISTENCE_DAYS,
    baseline_days: int = BASELINE_DAYS,
) -> pd.DataFrame:
    """
    Detect point anomalies that continue for consecutive mission days.

    The current day's flag and previous days' flags are used.
    Future days are never used to calculate the current persistence count.
    """

    if persistence_days < 2:
        raise ValueError(
            "persistence_days must be at least 2."
        )

    result = data.sort_values(
        ["crew_id", "mission_day"]
    ).reset_index(drop=True).copy()

    persistent_columns = []

    for feature in FEATURE_COLUMNS:
        point_column = f"{feature}_point_anomaly"
        run_column = f"{feature}_anomaly_run_length"
        persistent_column = f"{feature}_persistent_anomaly"

        if point_column not in result.columns:
            raise ValueError(
                f"Required point-anomaly column is missing: {point_column}"
            )

        def calculate_run_length(values: pd.Series) -> pd.Series:
            flags = values.fillna(False).astype(bool)
            groups = (~flags).cumsum()
            return flags.astype(int).groupby(groups).cumsum()

        result[run_column] = (
            result.groupby("crew_id", sort=False)[point_column]
            .transform(calculate_run_length)
        )

        result[persistent_column] = (
            result[run_column] >= persistence_days
        )

        persistent_columns.append(persistent_column)

    result["persistent_anomaly_count"] = (
        result[persistent_columns].sum(axis=1)
    )

    result["persistent_anomaly_detected"] = (
        result["persistent_anomaly_count"] > 0
    )

    result["eligible_persistent_anomaly"] = (
        result["persistent_anomaly_detected"]
        & result["eligible_for_alert"]
        & (result["mission_day"] > baseline_days)
    )

    return result


def add_anomaly_feature_summary(
    data: pd.DataFrame,
) -> pd.DataFrame:
    """
    Add readable lists of point and persistent anomaly features.
    """

    result = data.copy()

    point_columns = [
        f"{feature}_point_anomaly"
        for feature in FEATURE_COLUMNS
    ]

    persistent_columns = [
        f"{feature}_persistent_anomaly"
        for feature in FEATURE_COLUMNS
    ]

    def get_feature_list(
        row: pd.Series,
        columns: list[str],
    ) -> str:
        flagged = []

        for feature, column in zip(
            FEATURE_COLUMNS,
            columns,
        ):
            if bool(row[column]):
                flagged.append(feature)

        return ", ".join(flagged)

    result["point_anomaly_features"] = result.apply(
        lambda row: get_feature_list(row, point_columns),
        axis=1,
    )

    result["persistent_anomaly_features"] = result.apply(
        lambda row: get_feature_list(row, persistent_columns),
        axis=1,
    )

    return result


def detect_point_anomalies(
    data: pd.DataFrame,
    threshold: float = POINT_ANOMALY_THRESHOLD,
    baseline_days: int = BASELINE_DAYS,
) -> pd.DataFrame:
    """
    Run the complete point-anomaly detection stage.

    The input should be the enriched data produced by
    build_baseline_features().
    """

    result = add_data_quality_flags(data)

    result = add_point_anomaly_flags(
        result,
        threshold=threshold,
        baseline_days=baseline_days,
    )

    result = add_persistence_flags(
        result,
        persistence_days=PERSISTENCE_DAYS,
        baseline_days=baseline_days,
    )

    result = add_anomaly_feature_summary(result)

    result = add_alert_scores_and_states(
        result,
        baseline_days=baseline_days,
    )

    return result


def add_alert_scores_and_states(
    data: pd.DataFrame,
    baseline_days: int = BASELINE_DAYS,
) -> pd.DataFrame:
    """
    Combine point anomalies, persistent anomalies, and multi-signal
    patterns into an interpretable alert score and alert state.

    The score is an engineering prototype score. It is not a medical
    risk score or diagnostic result.
    """

    result = data.copy()

    point_columns = [
        f"{feature}_point_anomaly"
        for feature in FEATURE_COLUMNS
    ]

    persistent_columns = [
        f"{feature}_persistent_anomaly"
        for feature in FEATURE_COLUMNS
    ]

    # Count currently concerning point anomalies.
    result["point_signal_count"] = (
        result[point_columns].sum(axis=1)
    )

    # Count persistent concerning features.
    result["persistent_signal_count"] = (
        result[persistent_columns].sum(axis=1)
    )

    # Multi-signal patterns.
    result["sleep_fatigue_pattern"] = (
        result["sleep_hours_point_anomaly"]
        & result["fatigue_score_point_anomaly"]
    )

    result["fatigue_reaction_pattern"] = (
        result["fatigue_score_point_anomaly"]
        & result["reaction_time_ms_point_anomaly"]
    )

    result["workload_stress_pattern"] = (
        result["workload_hours_point_anomaly"]
        & result["stress_score_point_anomaly"]
    )

    result["workload_exercise_pattern"] = (
        result["workload_hours_point_anomaly"]
        & result["exercise_minutes_point_anomaly"]
    )

    pattern_columns = [
        "sleep_fatigue_pattern",
        "fatigue_reaction_pattern",
        "workload_stress_pattern",
        "workload_exercise_pattern",
    ]

    result["multi_signal_count"] = (
        result[pattern_columns].sum(axis=1)
    )

    # Start the score at zero.
    result["alert_score"] = 0

    # One point for each current concerning feature.
    result["alert_score"] += result["point_signal_count"]

    # Two additional points for each persistent feature.
    result["alert_score"] += (
        2 * result["persistent_signal_count"]
    )

    # Two additional points for each multi-signal pattern.
    result["alert_score"] += (
        2 * result["multi_signal_count"]
    )

    # Missing values affect confidence and reviewability.
    # They do not automatically create a health/performance alert.
    result["data_quality_penalty"] = (
        result["missing_feature_count"] > 0
    ).astype(int)

    # Warm-up rows are not operationally eligible for alerts.
    warmup_mask = result["mission_day"] <= baseline_days

    result["alert_state"] = "Stable"

    watch_mask = (
        (result["alert_score"] >= 3)
        & ~warmup_mask
        & result["baseline_is_sufficient"]
    )

    review_mask = (
        (result["alert_score"] >= 6)
        & ~warmup_mask
        & result["baseline_is_sufficient"]
    )

    result.loc[watch_mask, "alert_state"] = "Watch"
    result.loc[review_mask, "alert_state"] = "Review Required"

    # Keep warm-up rows explicitly marked as warm-up.
    result.loc[warmup_mask, "alert_state"] = "Warm-up"

    # If the baseline is insufficient, do not present a normal
    # operational alert state.
    result.loc[
        ~result["baseline_is_sufficient"],
        "alert_state",
    ] = "Data Quality Review"

    # Operational alert eligibility.
    result["operational_alert"] = (
        ~warmup_mask
        & result["baseline_is_sufficient"]
        & result["alert_state"].isin(
            ["Watch", "Review Required"]
        )
    )

    return result


def generate_point_anomaly_results(
    threshold: float = POINT_ANOMALY_THRESHOLD,
) -> pd.DataFrame:
    """
    Load the dataset, build baseline features, and detect
    point-level anomalies.
    """

    health_data = load_health_data()

    enriched_data, _ = build_baseline_features(
        health_data,
        baseline_days=BASELINE_DAYS,
        rolling_window=7,
    )

    return detect_point_anomalies(
        enriched_data,
        threshold=threshold,
        baseline_days=BASELINE_DAYS,
    )


if __name__ == "__main__":
    results = generate_point_anomaly_results()

    ML_RESULTS_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    output_path = ML_RESULTS_DIR / "point_anomaly_results.csv"
    results.to_csv(output_path, index=False)

    print("Point-anomaly detection completed.")
    print("Rows:", len(results))
    print("Point anomaly rows:", int(results["point_anomaly_detected"].sum()))
    print(
        "Eligible point anomaly rows:",
        int(results["eligible_point_anomaly"].sum()),
    )
    print(
        "Rows with data-quality warnings:",
        int((results["data_quality_warning"] != "").sum()),
    )
    print("Saved:", output_path)

    print()
    print("Most common flagged features:")

    flagged_rows = results[
        results["eligible_point_anomaly"]
    ]

    if flagged_rows.empty:
        print("No eligible point anomalies detected.")
    else:
        print(
            flagged_rows["point_anomaly_features"]
            .value_counts()
            .head(10)
            .to_string()
        )
