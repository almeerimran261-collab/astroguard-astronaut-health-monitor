# AstroGuard Data Dictionary

## Important note

AstroGuard's dataset is simulated. It is not real astronaut or patient data. Its value ranges are software checks, not medical reference ranges. Do not use it to make medical decisions.

## Daily measurement data

The daily data files contain one row for each crew member and mission day.

| Column | Meaning | Unit | Allowed values | Missing-value policy |
|---|---|---|---|---|
| `crew_id` | Simulated crew member identifier | Text | `Crew-01` to `Crew-20` | Not allowed |
| `mission_day` | Day number in the simulated mission | Day | Whole number from 1 to 180 | Not allowed |
| `timestamp` | Calendar date for that crew member's mission day | Date (`YYYY-MM-DD`) | Must match the mission-day sequence | Not allowed |
| `sleep_hours` | Hours slept | Hours | 0–14 | Blank values stay blank and are logged |
| `sleep_quality` | Simulated sleep-quality score; higher means better | Score | Whole number from 1 to 10 | Blank values stay blank and are logged |
| `resting_heart_rate` | Resting heart rate | Beats per minute | Whole number from 30 to 200 | Blank values stay blank and are logged; impossible readings are blanked |
| `exercise_minutes` | Daily exercise time | Minutes | Whole number from 0 to 300 | Blank values stay blank and are logged |
| `fatigue_score` | Simulated fatigue; higher means more fatigue | Score | Whole number from 1 to 10 | Blank values stay blank and are logged |
| `stress_score` | Simulated stress; higher means more stress | Score | Whole number from 1 to 10 | Blank values stay blank and are logged |
| `reaction_time_ms` | Simulated reaction-test time; higher means slower | Milliseconds | Whole number from 100 to 2,000 | Blank values stay blank and are logged |
| `workload_hours` | Daily work time | Hours | 0–18 | Blank values stay blank and are logged |

Missing measurements are not guessed or filled in. The cleaning step records missing values and invalid sensor readings in `data/processed/data_quality_log.csv`.

## Evaluation files

Files in `data/evaluation/ground_truth/` are answer keys. **Do not use them as model inputs.** Use them only after predictions have been made, to evaluate the results.

### `anomaly_labels.csv`
Rows with `anomaly_reason` equal to `sensor_error` are data-quality problems, not health events. See `docs/EVALUATION.md` for how to handle them when scoring.

| Column | Meaning | Allowed values |
|---|---|---|
| `crew_id` | Simulated crew identifier | `Crew-01` to `Crew-20` |
| `mission_day` | Mission day for the label | Whole number from 1 to 180 |
| `anomaly_label` | Whether the generator marked this day as anomalous | `0` = not labeled anomalous; `1` = labeled anomalous |
| `anomaly_reason` | Simulated reason for the label | Text such as `normal_simulated_day`, a planted event name, or `sensor_error` |

These labels describe the generator's scenarios. They are not medical findings.

### `risk_labels.csv`

| Column | Meaning | Allowed values |
|---|---|---|
| `crew_id` | Simulated crew identifier | `Crew-01` to `Crew-20` |
| `mission_day` | Mission day for the label | Whole number from 1 to 180 |
| `risk_category` | Simulated category assigned by the generator | `low`, `moderate`, or `high` |
| `label_source` | Where the label came from | `predefined_simulation_scenario` |

`risk_category` is a made-up practice label, not a clinical risk score.

### `scenario_ground_truth.csv`

This file describes the planted simulated events and deliberately added data problems. It is the answer key, not model input. Its rows can describe different kinds of records, so some columns are blank when they do not apply.

Common columns include:

- `crew_id`: crew member involved.
- `event`: name of a simulated health-event scenario.
- `start_day` and `end_day`: first and last mission days of an event.
- `start_date` and `end_date`: calendar dates for those event days.
- `changed_columns`: measurements intentionally changed by an event.
- `mission_day`: day of an inserted data fault, when applicable.
- `column`: measurement column affected by a data fault, when applicable.
- `record_type`: kind of record, such as `health_event`, `sensor_error`, or `missing_value`.
- `description` and `note`: plain-language details.

## Split file

`data/evaluation/splits.csv` assigns each crew member to one group.

| Column | Meaning | Allowed values |
|---|---|---|
| `crew_id` | Simulated crew identifier | `Crew-01` to `Crew-20`, once each |
| `split` | Which dataset group the crew belongs to | `train`, `validation`, or `test` |

A crew member must appear in only one group. Do not split individual rows at random, because that could put the same crew member in more than one group.
