"""
Event-level evaluation for the AstroGuard alert system.

Ground-truth files are used only here, after predictions have been
generated. They must not be imported into the ML detection modules.
"""

from pathlib import Path

import numpy as np
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]

ML_RESULTS_PATH = (
    PROJECT_ROOT
    / "assets"
    / "ml_results"
    / "alert_results.csv"
)

SPLITS_PATH = (
    PROJECT_ROOT
    / "data"
    / "evaluation"
    / "splits.csv"
)

ANOMALY_LABELS_PATH = (
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


def load_inputs():
    """
    Load predictions, crew splits, and anomaly labels.
    """

    predictions = pd.read_csv(ML_RESULTS_PATH)
    splits = pd.read_csv(SPLITS_PATH)
    labels = pd.read_csv(ANOMALY_LABELS_PATH)

    required_prediction_columns = [
        "crew_id",
        "mission_day",
        "operational_alert",
    ]

    required_split_columns = [
        "crew_id",
        "split",
    ]

    required_label_columns = [
        "crew_id",
        "mission_day",
        "anomaly_label",
        "anomaly_reason",
    ]

    for column in required_prediction_columns:
        if column not in predictions.columns:
            raise ValueError(
                f"Prediction file is missing column: {column}"
            )

    for column in required_split_columns:
        if column not in splits.columns:
            raise ValueError(
                f"Split file is missing column: {column}"
            )

    for column in required_label_columns:
        if column not in labels.columns:
            raise ValueError(
                f"Label file is missing column: {column}"
            )

    return predictions, splits, labels


def remove_sensor_errors(labels: pd.DataFrame) -> pd.DataFrame:
    """
    Remove sensor-error rows from health-event scoring.

    Sensor errors are data-quality events, not health anomalies.
    """

    clean_labels = labels[
        labels["anomaly_reason"].ne("sensor_error")
    ].copy()

    return clean_labels


def build_events(
    data: pd.DataFrame,
    flag_column: str,
) -> pd.DataFrame:
    """
    Convert daily flags into consecutive mission-day events.

    An event is a consecutive run of flagged days for the same crew.
    """

    required_columns = [
        "crew_id",
        "mission_day",
        flag_column,
    ]

    missing_columns = [
        column
        for column in required_columns
        if column not in data.columns
    ]

    if missing_columns:
        raise ValueError(
            f"Missing event columns: {missing_columns}"
        )

    working = data[
        required_columns
    ].copy()

    working[flag_column] = (
        working[flag_column]
        .fillna(False)
        .astype(bool)
    )

    working = working[
        working[flag_column]
    ].sort_values(
        ["crew_id", "mission_day"]
    )

    if working.empty:
        return pd.DataFrame(
            columns=[
                "crew_id",
                "start_day",
                "end_day",
                "duration",
            ]
        )

    working["previous_day"] = (
        working.groupby("crew_id")["mission_day"]
        .shift(1)
    )

    working["new_event"] = (
        working["previous_day"].isna()
        | (
            working["mission_day"]
            != working["previous_day"] + 1
        )
    )

    working["event_number"] = (
        working.groupby("crew_id")["new_event"]
        .cumsum()
    )

    events = (
        working
        .groupby(["crew_id", "event_number"], as_index=False)
        .agg(
            start_day=("mission_day", "min"),
            end_day=("mission_day", "max"),
            duration=("mission_day", "size"),
        )
        .drop(columns=["event_number"])
    )

    return events


def events_overlap(
    first: pd.Series,
    second: pd.Series,
) -> bool:
    """
    Return True when two events overlap by at least one day.
    """

    return (
        first["crew_id"] == second["crew_id"]
        and first["start_day"] <= second["end_day"]
        and second["start_day"] <= first["end_day"]
    )


def match_predicted_events(
    predicted_events: pd.DataFrame,
    true_events: pd.DataFrame,
) -> pd.DataFrame:
    """
    Match predicted events to overlapping true events.

    Each predicted event is counted once. A predicted event is a hit
    if it overlaps at least one true event.
    """

    if predicted_events.empty:
        return predicted_events.assign(
            matched=False,
            matched_true_event=False,
            detection_delay=np.nan,
        )

    rows = []

    for _, predicted in predicted_events.iterrows():
        matching_true = true_events[
            true_events["crew_id"].eq(
                predicted["crew_id"]
            )
            & true_events["start_day"].le(
                predicted["end_day"]
            )
            & true_events["end_day"].ge(
                predicted["start_day"]
            )
        ]

        if matching_true.empty:
            rows.append(
                {
                    **predicted.to_dict(),
                    "matched": False,
                    "matched_true_event": False,
                    "detection_delay": np.nan,
                }
            )
            continue

        first_true = matching_true.sort_values(
            "start_day"
        ).iloc[0]

        first_prediction_inside_true = max(
            int(predicted["start_day"]),
            int(first_true["start_day"]),
        )

        detection_delay = (
            first_prediction_inside_true
            - int(first_true["start_day"])
        )

        rows.append(
            {
                **predicted.to_dict(),
                "matched": True,
                "matched_true_event": True,
                "detection_delay": detection_delay,
            }
        )

    return pd.DataFrame(rows)


def evaluate_split(
    predictions: pd.DataFrame,
    splits: pd.DataFrame,
    labels: pd.DataFrame,
    split_name: str,
):
    """
    Calculate event-level metrics for one split.
    """

    split_crews = splits.loc[
        splits["split"].eq(split_name),
        "crew_id",
    ].tolist()

    split_predictions = predictions[
        predictions["crew_id"].isin(split_crews)
    ].copy()

    split_labels = labels[
        labels["crew_id"].isin(split_crews)
    ].copy()

    split_labels = remove_sensor_errors(split_labels)

    true_daily = split_labels[
        ["crew_id", "mission_day", "anomaly_label"]
    ].copy()

    true_daily["true_anomaly"] = (
        true_daily["anomaly_label"].eq(1)
    )

    predicted_daily = split_predictions[
        ["crew_id", "mission_day", "operational_alert"]
    ].copy()

    predicted_daily["predicted_anomaly"] = (
        predicted_daily["operational_alert"]
        .fillna(False)
        .astype(bool)
    )

    true_events = build_events(
        true_daily.rename(
            columns={"true_anomaly": "event_flag"}
        ),
        flag_column="event_flag",
    )

    predicted_events = build_events(
        predicted_daily.rename(
            columns={"predicted_anomaly": "event_flag"}
        ),
        flag_column="event_flag",
    )

    matched_predictions = match_predicted_events(
        predicted_events,
        true_events,
    )

    predicted_event_count = len(predicted_events)
    true_event_count = len(true_events)

    matched_prediction_count = int(
        matched_predictions["matched"].sum()
    )

    matched_true_event_count = 0

    for _, true_event in true_events.iterrows():
        has_match = any(
            events_overlap(true_event, predicted_event)
            for _, predicted_event in predicted_events.iterrows()
        )

        if has_match:
            matched_true_event_count += 1

    false_alarm_count = (
        predicted_event_count
        - matched_prediction_count
    )

    event_precision = (
        matched_prediction_count / predicted_event_count
        if predicted_event_count > 0
        else np.nan
    )

    event_recall = (
        matched_true_event_count / true_event_count
        if true_event_count > 0
        else np.nan
    )

    crew_days = (
        split_predictions["crew_id"].nunique()
        * split_predictions["mission_day"].nunique()
    )

    false_alarms_per_100_crew_days = (
        false_alarm_count / crew_days * 100
        if crew_days > 0
        else np.nan
    )

    matched_delays = matched_predictions.loc[
        matched_predictions["matched"],
        "detection_delay",
    ].dropna()

    median_detection_delay = (
        matched_delays.median()
        if not matched_delays.empty
        else np.nan
    )

    per_crew_rows = []

    for crew_id in split_crews:
        crew_predictions = split_predictions[
            split_predictions["crew_id"].eq(crew_id)
        ]

        crew_labels = split_labels[
            split_labels["crew_id"].eq(crew_id)
        ]

        crew_true_daily = crew_labels[
            ["crew_id", "mission_day", "anomaly_label"]
        ].copy()

        crew_true_daily["event_flag"] = (
            crew_true_daily["anomaly_label"].eq(1)
        )

        crew_pred_daily = crew_predictions[
            ["crew_id", "mission_day", "operational_alert"]
        ].copy()

        crew_pred_daily["event_flag"] = (
            crew_pred_daily["operational_alert"]
            .fillna(False)
            .astype(bool)
        )

        crew_true_events = build_events(
            crew_true_daily,
            flag_column="event_flag",
        )

        crew_pred_events = build_events(
            crew_pred_daily,
            flag_column="event_flag",
        )

        crew_matched_predictions = match_predicted_events(
            crew_pred_events,
            crew_true_events,
        )

        crew_predicted_count = len(crew_pred_events)
        crew_true_count = len(crew_true_events)
        crew_hits = int(
            crew_matched_predictions["matched"].sum()
        )

        crew_true_hits = 0

        for _, true_event in crew_true_events.iterrows():
            if any(
                events_overlap(true_event, predicted_event)
                for _, predicted_event
                in crew_pred_events.iterrows()
            ):
                crew_true_hits += 1

        crew_delays = crew_matched_predictions.loc[
            crew_matched_predictions["matched"],
            "detection_delay",
        ].dropna()

        per_crew_rows.append(
            {
                "crew_id": crew_id,
                "true_events": crew_true_count,
                "predicted_events": crew_predicted_count,
                "matched_predicted_events": crew_hits,
                "matched_true_events": crew_true_hits,
                "false_alarm_events": (
                    crew_predicted_count - crew_hits
                ),
                "event_precision": (
                    crew_hits / crew_predicted_count
                    if crew_predicted_count > 0
                    else np.nan
                ),
                "event_recall": (
                    crew_true_hits / crew_true_count
                    if crew_true_count > 0
                    else np.nan
                ),
                "median_detection_delay": (
                    crew_delays.median()
                    if not crew_delays.empty
                    else np.nan
                ),
            }
        )

    overall = pd.DataFrame(
        [
            {
                "split": split_name,
                "crews": len(split_crews),
                "true_events": true_event_count,
                "predicted_events": predicted_event_count,
                "matched_predicted_events": (
                    matched_prediction_count
                ),
                "matched_true_events": (
                    matched_true_event_count
                ),
                "false_alarm_events": false_alarm_count,
                "event_precision": event_precision,
                "event_recall": event_recall,
                "false_alarms_per_100_crew_days": (
                    false_alarms_per_100_crew_days
                ),
                "median_detection_delay": (
                    median_detection_delay
                ),
            }
        ]
    )

    per_crew = pd.DataFrame(per_crew_rows)

    return overall, per_crew, true_events, predicted_events


def main():
    predictions, splits, labels = load_inputs()

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    all_overall = []
    all_per_crew = []

    for split_name in ["train", "validation", "test"]:
        overall, per_crew, _, _ = evaluate_split(
            predictions,
            splits,
            labels,
            split_name,
        )

        all_overall.append(overall)
        all_per_crew.append(per_crew)

    overall_results = pd.concat(
        all_overall,
        ignore_index=True,
    )

    per_crew_results = pd.concat(
        all_per_crew,
        ignore_index=True,
    )

    overall_path = OUTPUT_DIR / "evaluation_overall.csv"
    per_crew_path = OUTPUT_DIR / "evaluation_by_crew.csv"

    overall_results.to_csv(
        overall_path,
        index=False,
    )

    per_crew_results.to_csv(
        per_crew_path,
        index=False,
    )

    print("Evaluation completed.")
    print()
    print("Overall results:")
    print(
        overall_results.to_string(index=False)
    )
    print()
    print("Saved:")
    print(overall_path)
    print(per_crew_path)


if __name__ == "__main__":
    main()
