"""
Create AstroGuard's simulated daily health dataset.

Run from the project folder:
    python src/generate_synthetic_data.py

All records and labels are simulated, not real astronaut medical data.
"""

from datetime import date, timedelta
from pathlib import Path

import numpy as np
import pandas as pd


# ---------- Settings ----------
SEED = 42
N_CREW = 20
N_DAYS = 180
START_DATE = date(2026, 1, 1)

rng = np.random.default_rng(SEED)
PROJECT_ROOT = Path(__file__).resolve().parent.parent

RAW_PATH = PROJECT_ROOT / "data" / "raw" / "astronaut_health_raw.csv"
EVAL_DIR = PROJECT_ROOT / "data" / "evaluation"
TRUTH_DIR = EVAL_DIR / "ground_truth"


# ---------- Simulated crew baselines ----------
# These are demonstration values, not medical reference values.

BASELINES = {}

for i in range(1, N_CREW + 1):
    crew = f"Crew-{i:02d}"
    BASELINES[crew] = {
        "sleep_hours": round(rng.uniform(6.5, 8.0), 1),
        "sleep_quality": int(rng.integers(6, 9)),
        "resting_heart_rate": int(rng.integers(58, 77)),
        "exercise_minutes": int(rng.integers(35, 71)),
        "fatigue_score": int(rng.integers(2, 6)),
        "stress_score": int(rng.integers(2, 6)),
        "reaction_time_ms": int(rng.integers(420, 531)),
        "workload_hours": round(rng.uniform(7.0, 10.0), 1),
    }


NOISE = {
    "sleep_hours": 0.4,
    "sleep_quality": 0.8,
    "resting_heart_rate": 2.0,
    "exercise_minutes": 8.0,
    "fatigue_score": 0.5,
    "stress_score": 0.5,
    "reaction_time_ms": 15.0,
    "workload_hours": 0.7,
}

HEALTH_COLS = list(NOISE.keys())


# ---------- Planned simulated events ----------
# Each item: crew, first day, last day, event name, changes.

EPISODES = [
    ("Crew-01", 20, 29, "increased workload",
     {"workload_hours": 3.0, "exercise_minutes": -15.0}),
    ("Crew-02", 35, 42, "reduced sleep",
     {"sleep_hours": -2.0}),
    ("Crew-03", 50, 59, "increased fatigue",
     {"fatigue_score": 3.0}),
    ("Crew-04", 65, 72, "increased stress",
     {"stress_score": 3.0}),
    ("Crew-05", 80, 89, "reduced sleep",
     {"sleep_hours": -2.5}),
    ("Crew-06", 95, 104, "increased workload",
     {"workload_hours": 3.5, "exercise_minutes": -20.0}),
    ("Crew-07", 110, 119, "increased fatigue",
     {"fatigue_score": 3.0}),
    ("Crew-08", 125, 132, "increased stress",
     {"stress_score": 3.0}),
    ("Crew-09", 140, 149, "reduced sleep",
     {"sleep_hours": -2.0}),
    ("Crew-10", 155, 164, "increased fatigue",
     {"fatigue_score": 3.0}),
    ("Crew-11", 45, 52, "reduced sleep",
     {"sleep_hours": -2.0}),
    ("Crew-12", 100, 109, "increased workload",
     {"workload_hours": 3.0}),
    ("Crew-13", 25, 34, "increased stress",
     {"stress_score": 3.0}),
    ("Crew-14", 70, 79, "increased fatigue",
     {"fatigue_score": 3.0}),
    ("Crew-15", 120, 129, "reduced sleep",
     {"sleep_hours": -2.0}),
    ("Crew-16", 150, 159, "increased workload",
     {"workload_hours": 3.0}),

    # ----- second events (Crew-01 to Crew-16) -----
    ("Crew-01", 75, 82, "reduced sleep",
     {"sleep_hours": -2.0}),
    ("Crew-02", 90, 99, "increased workload",
     {"workload_hours": 3.5, "exercise_minutes": -15.0}),
    ("Crew-03", 95, 102, "reduced sleep",
     {"sleep_hours": -2.5}),
    ("Crew-04", 25, 32, "increased fatigue",
     {"fatigue_score": 3.0}),
    ("Crew-05", 30, 37, "increased stress",
     {"stress_score": 3.0}),
    ("Crew-06", 40, 47, "reduced sleep",
     {"sleep_hours": -2.0}),
    ("Crew-07", 25, 34, "increased workload",
     {"workload_hours": 3.0, "exercise_minutes": -15.0}),
    ("Crew-08", 30, 39, "increased fatigue",
     {"fatigue_score": 3.0}),
    ("Crew-09", 35, 44, "increased stress",
     {"stress_score": 3.0}),
    ("Crew-10", 40, 47, "reduced sleep",
     {"sleep_hours": -2.0}),
    ("Crew-11", 95, 104, "increased workload",
     {"workload_hours": 3.0, "exercise_minutes": -15.0}),
    ("Crew-12", 30, 37, "increased fatigue",
     {"fatigue_score": 3.0}),
    ("Crew-13", 80, 89, "reduced sleep",
     {"sleep_hours": -2.0}),
    ("Crew-14", 20, 27, "increased workload",
     {"workload_hours": 3.0, "exercise_minutes": -15.0}),
    ("Crew-15", 35, 44, "increased fatigue",
     {"fatigue_score": 3.0}),
    ("Crew-16", 40, 49, "increased stress",
     {"stress_score": 3.0}),

    # ----- third events (Crew-09 to Crew-16) -----
    ("Crew-09", 90, 99, "increased workload",
     {"workload_hours": 3.0, "exercise_minutes": -15.0}),
    ("Crew-10", 100, 109, "increased stress",
     {"stress_score": 3.0}),
    ("Crew-11", 145, 154, "increased fatigue",
     {"fatigue_score": 3.0}),
    ("Crew-12", 150, 157, "reduced sleep",
     {"sleep_hours": -2.5}),
    ("Crew-13", 135, 144, "increased fatigue",
     {"fatigue_score": 3.0}),
    ("Crew-14", 125, 132, "increased stress",
     {"stress_score": 3.0}),
    ("Crew-15", 85, 92, "increased workload",
     {"workload_hours": 3.0, "exercise_minutes": -15.0}),
    ("Crew-16", 95, 102, "reduced sleep",
     {"sleep_hours": -2.0}),

]


# ---------- Build daily measurements ----------
rows = []

for crew, baseline in BASELINES.items():
    for day in range(1, N_DAYS + 1):
        row = {
            "crew_id": crew,
            "mission_day": day,
            "timestamp": (
                START_DATE + timedelta(days=day - 1)
            ).isoformat(),
        }

        for column in HEALTH_COLS:
            row[column] = baseline[column] + rng.normal(
                0, NOISE[column]
            )

        rows.append(row)

df = pd.DataFrame(rows)


# ---------- Apply planned events ----------
event_rows = []

for crew, first, last, label, changes in EPISODES:
    mask = (
        (df["crew_id"] == crew)
        & df["mission_day"].between(first, last)
    )

    for column, change in changes.items():
        df.loc[mask, column] += change

    event_rows.append({
        "crew_id": crew,
        "event": label,
        "start_day": first,
        "end_day": last,
        "start_date": (
            START_DATE + timedelta(days=first - 1)
        ).isoformat(),
        "end_date": (
            START_DATE + timedelta(days=last - 1)
        ).isoformat(),
        "changed_columns": "; ".join(
            f"{column}: {change:+g}"
            for column, change in changes.items()
        ),
        "record_type": "health_event",
        "note": "Simulated event; not a clinical diagnosis",
    })


# ---------- Add simple relationships between measurements ----------
# These are simulation assumptions, not medical rules.

for crew in BASELINES:
    mask = df["crew_id"] == crew
    baseline = BASELINES[crew]

    df.loc[mask, "sleep_quality"] += (
        -1.2 * (
            df.loc[mask, "sleep_hours"] - baseline["sleep_hours"]
        )
    )

    df.loc[mask, "fatigue_score"] += (
        0.8 * (
            baseline["sleep_hours"] - df.loc[mask, "sleep_hours"]
        )
    )

    df.loc[mask, "stress_score"] += (
        0.8 * (
            df.loc[mask, "workload_hours"]
            - baseline["workload_hours"]
        )
    )

    df.loc[mask, "reaction_time_ms"] += (
        25 * (
            df.loc[mask, "fatigue_score"]
            - baseline["fatigue_score"]
        )
    )

    df.loc[mask, "resting_heart_rate"] += (
        1.5 * (
            df.loc[mask, "stress_score"]
            - baseline["stress_score"]
        )
    )


# ---------- Keep measurements within simulation bounds ----------
df["sleep_hours"] = df["sleep_hours"].clip(0, 12).round(1)

for column in ["sleep_quality", "fatigue_score", "stress_score"]:
    df[column] = df[column].clip(1, 10).round()

df["resting_heart_rate"] = df["resting_heart_rate"].round()
df["exercise_minutes"] = df["exercise_minutes"].clip(0).round()
df["reaction_time_ms"] = df["reaction_time_ms"].round()
df["workload_hours"] = df["workload_hours"].clip(0, 16).round(1)


# ---------- Create simulated risk labels ----------
risk_rows = []

for _, row in df.iterrows():
    crew = row["crew_id"]
    day = int(row["mission_day"])
    event_name = None

    for event_crew, first, last, label, _changes in EPISODES:
        if event_crew == crew and first <= day <= last:
            event_name = label
            break

    if event_name is None:
        risk = "low"
    elif event_name in {"increased fatigue", "reduced sleep"}:
        risk = "high"
    else:
        risk = "moderate"

    risk_rows.append({
        "crew_id": crew,
        "mission_day": day,
        "risk_category": risk,
        "label_source": "predefined_simulation_scenario",
    })

risk_df = pd.DataFrame(risk_rows)


# ---------- Insert sensor error and missing measurements ----------
fault_rows = []

sensor_crew = "Crew-19"
sensor_day = 9
sensor_mask = (
    (df["crew_id"] == sensor_crew)
    & (df["mission_day"] == sensor_day)
)

df.loc[sensor_mask, "resting_heart_rate"] = 255

fault_rows.append({
    "crew_id": sensor_crew,
    "mission_day": sensor_day,
    "record_type": "sensor_error",
    "column": "resting_heart_rate",
    "description": "Deliberately inserted impossible sensor value",
})

# Insert eight missing cells. If a selected location is already missing,
# choose another so the data has eight distinct missing measurement cells.
missing_cells = set()

while len(missing_cells) < 8:
    row_index = int(rng.integers(0, len(df)))
    column = str(rng.choice(HEALTH_COLS))

    if (
        df.loc[row_index, "crew_id"] == sensor_crew
        and df.loc[row_index, "mission_day"] == sensor_day
        and column == "resting_heart_rate"
    ):
        continue

    if (row_index, column) in missing_cells:
        continue

    missing_cells.add((row_index, column))
    df.loc[row_index, column] = np.nan

    fault_rows.append({
        "crew_id": df.loc[row_index, "crew_id"],
        "mission_day": int(df.loc[row_index, "mission_day"]),
        "record_type": "missing_value",
        "column": column,
        "description": "Deliberately inserted missing measurement",
    })


# ---------- Create anomaly labels for evaluation only ----------
anomaly_df = df[["crew_id", "mission_day"]].copy()
anomaly_df["anomaly_label"] = 0
anomaly_df["anomaly_reason"] = "normal_simulated_day"

for crew, first, last, label, _changes in EPISODES:
    mask = (
        (anomaly_df["crew_id"] == crew)
        & anomaly_df["mission_day"].between(first, last)
    )
    anomaly_df.loc[mask, "anomaly_label"] = 1
    anomaly_df.loc[mask, "anomaly_reason"] = label

sensor_mask = (
    (anomaly_df["crew_id"] == sensor_crew)
    & (anomaly_df["mission_day"] == sensor_day)
)
anomaly_df.loc[sensor_mask, "anomaly_label"] = 1
anomaly_df.loc[sensor_mask, "anomaly_reason"] = "sensor_error"


# ---------- Save data and evaluation-only answer keys ----------
RAW_PATH.parent.mkdir(parents=True, exist_ok=True)
EVAL_DIR.mkdir(parents=True, exist_ok=True)
TRUTH_DIR.mkdir(parents=True, exist_ok=True)

df.to_csv(RAW_PATH, index=False)

truth_df = pd.DataFrame(event_rows + fault_rows)
truth_df.to_csv(TRUTH_DIR / "scenario_ground_truth.csv", index=False)

risk_df.to_csv(TRUTH_DIR / "risk_labels.csv", index=False)
anomaly_df.to_csv(TRUTH_DIR / "anomaly_labels.csv", index=False)


# ---------- Create three-way crew-level split ----------
# A crew member must belong to only one group.

crew_ids = sorted(BASELINES.keys())
rng.shuffle(crew_ids)

test_count = max(1, round(len(crew_ids) * 0.2))
validation_count = max(1, round(len(crew_ids) * 0.2))

test_crews = set(crew_ids[:test_count])
validation_crews = set(
    crew_ids[test_count:test_count + validation_count]
)

split_df = pd.DataFrame({
    "crew_id": sorted(BASELINES.keys()),
})

split_df["split"] = split_df["crew_id"].apply(
    lambda crew: (
        "test" if crew in test_crews
        else "validation" if crew in validation_crews
        else "train"
    )
)

split_df.to_csv(EVAL_DIR / "splits.csv", index=False)


# ---------- Print a short summary ----------
print(f"Raw dataset saved: {RAW_PATH}")
print(f"Answer keys saved in: {TRUTH_DIR}")
print(f"Three-way split saved: {EVAL_DIR / 'splits.csv'}")
print(f"Total records: {len(df)}")
print(f"Crew members: {df['crew_id'].nunique()}")
print(f"Days per crew member: {N_DAYS}")
print(f"Measurement columns: {len(HEALTH_COLS)}")
print(
    "Missing measurement cells before cleaning: "
    f"{int(df[HEALTH_COLS].isna().sum().sum())}"
)
print(f"Risk category counts:\n{risk_df['risk_category'].value_counts()}")
print(f"Anomaly label counts:\n{anomaly_df['anomaly_label'].value_counts()}")
print("Reminder: all generated data and labels are simulated.")

