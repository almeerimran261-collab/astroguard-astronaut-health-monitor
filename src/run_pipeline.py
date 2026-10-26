"""
Run the complete AstroGuard ML monitoring pipeline.

This module generates:
- Personal baselines
- Baseline and rolling features
- Point anomalies
- Persistent anomalies
- Alert states
- Explanations
- Recommendations
"""

from pathlib import Path

from src.baseline import (
    build_baseline_features,
    load_health_data,
)

from src.anomaly_detection import (
    detect_point_anomalies,
)

from src.recommendations import (
    add_explanations_and_recommendations,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = PROJECT_ROOT / "assets" / "ml_results"

BASELINE_DAYS = 14
ROLLING_WINDOW = 7
POINT_ANOMALY_THRESHOLD = 3.5


def run_pipeline():
    """
    Run all AstroGuard ML stages and save the results.
    """

    health_data = load_health_data()

    enriched_data, baselines = build_baseline_features(
        health_data,
        baseline_days=BASELINE_DAYS,
        rolling_window=ROLLING_WINDOW,
    )

    anomaly_results = detect_point_anomalies(
        enriched_data,
        threshold=POINT_ANOMALY_THRESHOLD,
        baseline_days=BASELINE_DAYS,
    )

    final_results = add_explanations_and_recommendations(
        anomaly_results
    )

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    baselines_path = OUTPUT_DIR / "personal_baselines.csv"
    features_path = OUTPUT_DIR / "baseline_features.csv"
    alerts_path = OUTPUT_DIR / "alert_results.csv"

    baselines.to_csv(
        baselines_path,
        index=False,
    )

    enriched_data.to_csv(
        features_path,
        index=False,
    )

    final_results.to_csv(
        alerts_path,
        index=False,
    )

    return final_results


if __name__ == "__main__":
    results = run_pipeline()

    print("AstroGuard ML pipeline completed.")
    print("Rows processed:", len(results))
    print()
    print("Alert states:")
    print(
        results["alert_state"]
        .value_counts()
        .to_string()
    )
    print()
    print(
        "Operational alerts:",
        int(results["operational_alert"].sum()),
    )
    print()
    print("Saved files:")
    print(OUTPUT_DIR / "personal_baselines.csv")
    print(OUTPUT_DIR / "baseline_features.csv")
    print(OUTPUT_DIR / "alert_results.csv")
