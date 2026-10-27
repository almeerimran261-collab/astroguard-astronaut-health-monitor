"""
Tests for AstroGuard baseline and anomaly-detection behavior.
"""

import numpy as np

from src.anomaly_detection import (
    detect_point_anomalies,
)
from src.baseline import (
    build_baseline_features,
    load_health_data,
)


def build_results(data):
    """
    Build the complete anomaly result table for a dataset.
    """

    enriched, _ = build_baseline_features(
        data,
        baseline_days=14,
        rolling_window=7,
    )

    return detect_point_anomalies(
        enriched,
        threshold=3.5,
        baseline_days=14,
    )


def test_dataset_has_expected_shape():
    data = load_health_data()

    assert len(data) == 3600
    assert data["crew_id"].nunique() == 20
    assert data["mission_day"].min() == 1
    assert data["mission_day"].max() == 180


def test_every_crew_member_has_180_rows():
    data = load_health_data()

    rows_per_crew = data.groupby("crew_id").size()

    assert rows_per_crew.nunique() == 1
    assert rows_per_crew.iloc[0] == 180


def test_warmup_rows_are_not_operational_alerts():
    data = load_health_data()
    results = build_results(data)

    warmup = results[
        results["mission_day"] <= 14
    ]

    assert len(warmup) == 280
    assert warmup["operational_alert"].sum() == 0
    assert warmup["eligible_point_anomaly"].sum() == 0
    assert warmup["eligible_persistent_anomaly"].sum() == 0


def test_missing_measurements_create_data_quality_warnings():
    data = load_health_data()
    results = build_results(data)

    warning_rows = results[
        results["data_quality_warning"].ne("")
    ]

    assert len(warning_rows) == 9
    assert (warning_rows["missing_feature_count"] > 0).all()


def test_poor_sleep_for_three_days_becomes_persistent():
    data = load_health_data()

    mask = (
        data["crew_id"].eq("Crew-01")
        & data["mission_day"].between(50, 52)
    )

    data.loc[mask, "sleep_hours"] = 3.5

    results = build_results(data)

    target = results[
        results["crew_id"].eq("Crew-01")
        & results["mission_day"].between(50, 52)
    ]

    assert target["sleep_hours_point_anomaly"].all()
    assert not target.iloc[0]["sleep_hours_persistent_anomaly"]
    assert not target.iloc[1]["sleep_hours_persistent_anomaly"]
    assert target.iloc[2]["sleep_hours_persistent_anomaly"]


def test_recovery_ends_persistent_sleep_signal():
    data = load_health_data()

    abnormal_mask = (
        data["crew_id"].eq("Crew-01")
        & data["mission_day"].between(50, 52)
    )

    recovery_mask = (
        data["crew_id"].eq("Crew-01")
        & data["mission_day"].eq(53)
    )

    data.loc[abnormal_mask, "sleep_hours"] = 3.5

    # Return to a normal-looking value.
    data.loc[recovery_mask, "sleep_hours"] = 7.8

    results = build_results(data)

    recovery_row = results[
        results["crew_id"].eq("Crew-01")
        & results["mission_day"].eq(53)
    ].iloc[0]

    assert not recovery_row["sleep_hours_persistent_anomaly"]


def test_day_15_rolling_mean_uses_only_days_8_to_14():
    data = load_health_data()

    enriched, _ = build_baseline_features(
        data,
        baseline_days=14,
        rolling_window=7,
    )

    crew_data = data[
        data["crew_id"].eq("Crew-01")
        & data["mission_day"].between(8, 14)
    ]

    expected_mean = crew_data["sleep_hours"].mean()

    actual_mean = enriched.loc[
        enriched["crew_id"].eq("Crew-01")
        & enriched["mission_day"].eq(15),
        "sleep_hours_past_7d_mean",
    ].iloc[0]

    assert np.isclose(actual_mean, expected_mean)


def test_alert_results_contain_required_columns():
    data = load_health_data()
    results = build_results(data)

    required_columns = [
        "alert_score",
        "alert_state",
        "operational_alert",
        "point_anomaly_features",
        "persistent_anomaly_features",
        "data_quality_warning",
        "baseline_is_sufficient",
    ]

    for column in required_columns:
        assert column in results.columns
