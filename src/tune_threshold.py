"""
Tune the point-anomaly threshold using validation crews only.

The test split must not be used to choose the final threshold.
"""

from pathlib import Path

import pandas as pd

from src.anomaly_detection import (
    generate_point_anomaly_results,
)
from src.evaluate_model import (
    evaluate_split,
)
from src.recommendations import (
    add_explanations_and_recommendations,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]

SPLITS_PATH = (
    PROJECT_ROOT
    / "data"
    / "evaluation"
    / "splits.csv"
)

LABELS_PATH = (
    PROJECT_ROOT
    / "data"
    / "evaluation"
    / "ground_truth"
    / "anomaly_labels.csv"
)

OUTPUT_DIR = (
    PROJECT_ROOT
    / "assets"
    / "ml_results"
)


THRESHOLDS_TO_TEST = [
    2.0,
    2.5,
    3.0,
    3.5,
]


def main():
    splits = pd.read_csv(SPLITS_PATH)
    labels = pd.read_csv(LABELS_PATH)

    results = []

    for threshold in THRESHOLDS_TO_TEST:
        print(
            f"Testing validation threshold: {threshold}"
        )

        anomaly_results = generate_point_anomaly_results(
            threshold=threshold,
        )

        alert_results = (
            add_explanations_and_recommendations(
                anomaly_results
            )
        )

        overall, _, _, _ = evaluate_split(
            alert_results,
            splits,
            labels,
            "validation",
        )

        row = overall.iloc[0].to_dict()
        row["threshold"] = threshold
        results.append(row)

    calibration = pd.DataFrame(results)

    calibration = calibration[
        [
            "threshold",
            "event_precision",
            "event_recall",
            "false_alarm_events",
            "false_alarms_per_100_crew_days",
            "median_detection_delay",
            "predicted_events",
        ]
    ]

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    output_path = (
        OUTPUT_DIR
        / "threshold_calibration_validation.csv"
    )

    calibration.to_csv(
        output_path,
        index=False,
    )

    print()
    print("Validation calibration results:")
    print(calibration.to_string(index=False))
    print()
    print("Saved:", output_path)


if __name__ == "__main__":
    main()
