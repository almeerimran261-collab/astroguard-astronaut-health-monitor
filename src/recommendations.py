"""
Plain-language explanations and recommendations for AstroGuard.

This module explains monitoring signals. It does not diagnose illness
or prescribe treatment.
"""

from pathlib import Path

import pandas as pd

from src.baseline import FEATURE_COLUMNS


PROJECT_ROOT = Path(__file__).resolve().parents[1]
ML_RESULTS_DIR = PROJECT_ROOT / "assets" / "ml_results"


FEATURE_LABELS = {
    "sleep_hours": "sleep duration",
    "sleep_quality": "sleep quality",
    "resting_heart_rate": "resting heart rate",
    "exercise_minutes": "exercise",
    "fatigue_score": "fatigue",
    "stress_score": "stress",
    "reaction_time_ms": "reaction time",
    "workload_hours": "workload",
}


LOWER_IS_CONCERNING = {
    "sleep_hours",
    "sleep_quality",
    "exercise_minutes",
}


def format_feature_name(feature: str) -> str:
    """
    Convert a column name into a readable label.
    """

    return FEATURE_LABELS.get(
        feature,
        feature.replace("_", " "),
    )


def split_feature_list(value) -> list[str]:
    """
    Convert a comma-separated feature string into a list.

    Missing or empty values return an empty list.
    """

    if pd.isna(value) or str(value).strip() == "":
        return []

    return [
        item.strip()
        for item in str(value).split(",")
        if item.strip()
    ]


def build_signal_sentence(
    row: pd.Series,
) -> str:
    """
    Describe the strongest current signals in the row.
    """

    persistent_features = split_feature_list(
        row.get("persistent_anomaly_features", "")
    )

    point_features = split_feature_list(
        row.get("point_anomaly_features", "")
    )

    features = persistent_features or point_features

    if not features:
        return "No strong personal-baseline deviation was detected."

    labels = [
        format_feature_name(feature)
        for feature in features
    ]

    if len(labels) == 1:
        signal_text = labels[0]
    elif len(labels) == 2:
        signal_text = f"{labels[0]} and {labels[1]}"
    else:
        signal_text = (
            ", ".join(labels[:-1])
            + f", and {labels[-1]}"
        )

    if persistent_features:
        return (
            f"{signal_text.capitalize()} showed a persistent "
            "change from the personal baseline."
        )

    return (
        f"{signal_text.capitalize()} showed a point-in-time "
        "change from the personal baseline."
    )


def build_pattern_sentence(
    row: pd.Series,
) -> str:
    """
    Describe combinations of signals.
    """

    patterns = []

    if bool(row.get("sleep_fatigue_pattern", False)):
        patterns.append(
            "sleep and fatigue changed together"
        )

    if bool(row.get("fatigue_reaction_pattern", False)):
        patterns.append(
            "fatigue and reaction time changed together"
        )

    if bool(row.get("workload_stress_pattern", False)):
        patterns.append(
            "workload and stress changed together"
        )

    if bool(row.get("workload_exercise_pattern", False)):
        patterns.append(
            "workload increased while exercise decreased"
        )

    if not patterns:
        return ""

    if len(patterns) == 1:
        text = patterns[0]
    elif len(patterns) == 2:
        text = f"{patterns[0]} and {patterns[1]}"
    else:
        text = ", ".join(patterns[:-1]) + f", and {patterns[-1]}"

    return f"Multi-signal pattern: {text}."


def build_data_quality_sentence(
    row: pd.Series,
) -> str:
    """
    Explain missing-data or baseline-quality warnings.
    """

    warning = row.get("data_quality_warning", "")

    if pd.isna(warning) or str(warning).strip() == "":
        return ""

    return f"Data-quality warning: {warning}"


def build_alert_explanation(
    row: pd.Series,
) -> str:
    """
    Create a complete plain-language alert explanation.
    """

    crew_id = row.get("crew_id", "Unknown crew")
    mission_day = row.get("mission_day", "unknown")
    state = row.get("alert_state", "Unknown")
    score = row.get("alert_score", 0)

    signal_sentence = build_signal_sentence(row)
    pattern_sentence = build_pattern_sentence(row)
    quality_sentence = build_data_quality_sentence(row)

    parts = [
        f"{crew_id} on mission day {mission_day} "
        f"is in {state} status with an engineering alert score "
        f"of {score}.",
        signal_sentence,
    ]

    if pattern_sentence:
        parts.append(pattern_sentence)

    if quality_sentence:
        parts.append(quality_sentence)

    parts.append(
        "This is a simulated monitoring signal and not a diagnosis."
    )

    return " ".join(parts)


def calculate_confidence(
    row: pd.Series,
) -> str:
    """
    Calculate data-support confidence.

    This is not diagnostic confidence.
    """

    if not bool(row.get("baseline_is_sufficient", False)):
        return "Low"

    if int(row.get("missing_feature_count", 0)) > 0:
        return "Low"

    persistent_count = int(
        row.get("persistent_signal_count", 0)
    )

    multi_signal_count = int(
        row.get("multi_signal_count", 0)
    )

    point_count = int(
        row.get("point_signal_count", 0)
    )

    if persistent_count >= 2 or multi_signal_count >= 2:
        return "High"

    if persistent_count >= 1 or point_count >= 2:
        return "Medium"

    return "Low"


def generate_recommendation(
    row: pd.Series,
) -> str:
    """
    Generate a non-diagnostic recommendation.
    """

    state = row.get("alert_state", "Stable")

    if state == "Warm-up":
        return (
            "Continue collecting baseline information. "
            "Operational alerting has not started."
        )

    if state == "Stable":
        return (
            "Continue routine monitoring. "
            "No strong persistent personal-baseline change was detected."
        )

    if state == "Watch":
        return (
            "Continue monitoring the recent trend and review the "
            "contributing measurements if the pattern persists."
        )

    if state == "Review Required":
        return (
            "Recommend review by the mission medical officer or "
            "designated supervisor. This is a monitoring signal, "
            "not a diagnosis."
        )

    if state == "Data Quality Review":
        return (
            "Review the data source and measurement quality before "
            "interpreting the signal."
        )

    return "Review the result and associated data-quality information."


def add_explanations_and_recommendations(
    data: pd.DataFrame,
) -> pd.DataFrame:
    """
    Add explanations, confidence, and recommendations to every row.
    """

    result = data.copy()

    result["alert_explanation"] = result.apply(
        build_alert_explanation,
        axis=1,
    )

    result["confidence"] = result.apply(
        calculate_confidence,
        axis=1,
    )

    result["recommendation"] = result.apply(
        generate_recommendation,
        axis=1,
    )

    return result


if __name__ == "__main__":
    source_path = ML_RESULTS_DIR / "point_anomaly_results.csv"

    if not source_path.exists():
        raise FileNotFoundError(
            f"Run anomaly detection first: {source_path}"
        )

    results = pd.read_csv(source_path)

    results = add_explanations_and_recommendations(
        results
    )

    output_path = ML_RESULTS_DIR / "alert_results.csv"
    results.to_csv(output_path, index=False)

    print("Explanations and recommendations added.")
    print("Rows:", len(results))
    print("Saved:", output_path)

    print()
    print("Example non-stable results:")

    examples = results[
        results["alert_state"].isin(
            ["Watch", "Review Required"]
        )
    ]

    if examples.empty:
        print("No operational alerts found.")
    else:
        columns = [
            "crew_id",
            "mission_day",
            "alert_state",
            "alert_score",
            "confidence",
            "alert_explanation",
            "recommendation",
        ]

        print(
            examples[columns]
            .head(10)
            .to_string(index=False)
        )
