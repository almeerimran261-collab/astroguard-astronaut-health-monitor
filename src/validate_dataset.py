"""Check AstroGuard's data files before model work."""

from pathlib import Path

import pandas as pd

from data_loader import EXPECTED_COLUMNS, PROCESSED_PATH


ROOT = Path(__file__).resolve().parent.parent
SPLITS_PATH = ROOT / "data" / "evaluation" / "splits.csv"
GROUND_TRUTH_DIR = ROOT / "data" / "evaluation" / "ground_truth"

HEALTH_RANGES = {
    "sleep_hours": (0, 14),
    "sleep_quality": (1, 10),
    "resting_heart_rate": (30, 200),
    "exercise_minutes": (0, 300),
    "fatigue_score": (1, 10),
    "stress_score": (1, 10),
    "reaction_time_ms": (100, 2000),
    "workload_hours": (0, 18),
}

INTEGER_COLUMNS = {
    "mission_day",
    "sleep_quality",
    "resting_heart_rate",
    "exercise_minutes",
    "fatigue_score",
    "stress_score",
    "reaction_time_ms",
}

FORBIDDEN_INPUT_COLUMNS = {
    "anomaly_label",
    "anomaly_reason",
    "risk_category",
    "label_source",
    "event",
    "record_type",
    "description",
    "changed_columns",
}

ALLOWED_SPLITS = {"train", "validation", "test"}


def validate_dataset():
    errors = []

    if not PROCESSED_PATH.is_file():
        return [f"Processed dataset not found: {PROCESSED_PATH}"]

    if not SPLITS_PATH.is_file():
        return [f"Split file not found: {SPLITS_PATH}"]

    data = pd.read_csv(PROCESSED_PATH)

    missing_columns = sorted(set(EXPECTED_COLUMNS) - set(data.columns))
    extra_columns = sorted(set(data.columns) - set(EXPECTED_COLUMNS))

    if missing_columns:
        errors.append(f"Missing required columns: {missing_columns}")
    if extra_columns:
        errors.append(f"Unexpected columns: {extra_columns}")

    leaked_columns = sorted(FORBIDDEN_INPUT_COLUMNS.intersection(data.columns))
    if leaked_columns:
        errors.append(
            f"Answer labels/ground truth found in model input: {leaked_columns}"
        )

    if missing_columns:
        return errors

    # Check that measurements are numbers and within the allowed ranges.
    for column, (low, high) in HEALTH_RANGES.items():
        values = pd.to_numeric(data[column], errors="coerce")

        invalid_text = data[column].notna() & values.isna()
        if invalid_text.any():
            errors.append(f"{column} contains values that are not numbers")

        out_of_range = values.notna() & ~values.between(low, high)
        if out_of_range.any():
            errors.append(
                f"{column} has {int(out_of_range.sum())} value(s) "
                f"outside {low} to {high}"
            )

    # These columns should contain whole numbers.
    for column in INTEGER_COLUMNS:
        values = pd.to_numeric(data[column], errors="coerce").dropna()
        whole_numbers = values.map(
            lambda value: float(value).is_integer()
        )
        if not whole_numbers.all():
            errors.append(f"{column} must contain whole numbers")

    if data["crew_id"].isna().any():
        errors.append("crew_id contains a blank value")

    if data["mission_day"].isna().any():
        errors.append("mission_day contains a blank value")
    else:
        days = pd.to_numeric(data["mission_day"], errors="coerce")
        if not days.between(1, 180).all():
            errors.append("mission_day must be from 1 to 180")

    # Each crew member should have one record per day, with no duplicates.
    if data.duplicated().any():
        errors.append("The dataset contains exact duplicate rows")

    if data.duplicated(["crew_id", "mission_day"]).any():
        errors.append("A crew member has more than one row for a mission day")

    # Check dates and make sure each crew has all mission days 1 through 180.
    dates = pd.to_datetime(data["timestamp"], errors="coerce")

    if dates.isna().any():
        errors.append("timestamp contains an invalid or blank date")
    else:
        days = pd.to_numeric(data["mission_day"], errors="coerce")
        date_offsets = dates - pd.to_timedelta(days - 1, unit="D")

        for crew, row_indexes in data.groupby("crew_id").groups.items():
            crew_days = sorted(
                pd.to_numeric(data.loc[row_indexes, "mission_day"]).astype(int)
            )
            if crew_days != list(range(1, 181)):
                errors.append(f"{crew} does not have mission days 1 through 180")

            if date_offsets.loc[row_indexes].nunique() != 1:
                errors.append(
                    f"{crew} timestamps do not match the mission-day sequence"
                )

    # Each crew must be assigned exactly once to train, validation, or test.
    splits = pd.read_csv(SPLITS_PATH)

    if list(splits.columns) != ["crew_id", "split"]:
        errors.append("splits.csv must have exactly these columns: crew_id, split")
    else:
        if splits["crew_id"].duplicated().any():
            errors.append("A crew member appears more than once in splits.csv")

        if set(splits["split"].dropna()) != ALLOWED_SPLITS:
            errors.append(
                "splits.csv must include train, validation, and test"
            )

        data_crews = set(data["crew_id"].astype(str))
        split_crews = set(splits["crew_id"].dropna().astype(str))

        if data_crews != split_crews:
            errors.append("Split crew IDs do not match the dataset crew IDs")

    # Check that the answer-key files are in their evaluation-only folder.
    required_answer_files = {
        "scenario_ground_truth.csv",
        "anomaly_labels.csv",
        "risk_labels.csv",
    }

    if not GROUND_TRUTH_DIR.is_dir():
        errors.append("Missing evaluation/ground_truth folder")
    else:
        for filename in sorted(required_answer_files):
            if not (GROUND_TRUTH_DIR / filename).is_file():
                errors.append(f"Missing answer-key file: {filename}")

    return errors


if __name__ == "__main__":
    problems = validate_dataset()

    if problems:
        print("DATASET VALIDATION FAILED")
        for problem in problems:
            print(f"- {problem}")
        raise SystemExit(1)

    print("DATASET VALIDATION PASSED")
    print(f"Checked {len(pd.read_csv(PROCESSED_PATH))} data rows.")
    print("Answer keys are separate from model input.")
