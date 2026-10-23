# AstroGuard Data README

**Dataset version: v2.0** (frozen 2026-10-17)
Python 3.13.9, pandas 3.0.6, numpy 2.5.3
Random seed: 42 (the same seed always recreates the same data)

## Important note
This project uses **simulated data**. It is not real astronaut or patient data, is not
clinically validated, and is not an official NASA system. Do not use it to make medical
decisions.

This prototype uses simulated crew-monitoring records inspired by NASA Human Research
Program risks. It demonstrates the software and analytics workflow.

## Dataset
- 3,600 daily records: 20 simulated crew members x 180 mission days.
- 11 columns: 3 identifier columns and 8 measurements.
- One row = one crew member on one day.
- Dates run from 2026-01-01 to 2026-06-29.

## Files
| File | What it is |
|---|---|
| `data/raw/astronaut_health_raw.csv` | Generated source data. Cleaning never overwrites it. |
| `data/processed/astronaut_health.csv` | Cleaned measurements. **This is the model-input file.** |
| `data/processed/data_quality_log.csv` | Every missing value and invalid sensor reading found during cleaning. |
| `data/evaluation/splits.csv` | Assigns each crew member to `train`, `validation` or `test`. |
| `data/evaluation/ground_truth/scenario_ground_truth.csv` | Answer key: simulated events and inserted data problems. |
| `data/evaluation/ground_truth/anomaly_labels.csv` | Simulated anomaly label for every crew-day, for scoring. |
| `data/evaluation/ground_truth/risk_labels.csv` | Simulated risk category for every crew-day, for scoring. |

**Do not use the files in `data/evaluation/ground_truth/` as model inputs.** Use them only
after predictions are made, to evaluate the results.

More documents: `docs/DATA_DICTIONARY.md` (every column, unit, range and label),
`docs/DATA_METHODOLOGY.md` (how the data was made), `docs/EVALUATION.md` (how to score
results) and `docs/DATA_SOURCES.md` (where the data comes from).

## How to generate, clean and check the data
Run these commands from the project folder:

```bash
python -m pip install -r requirements.txt
python src/generate_synthetic_data.py
python src/data_cleaning.py
python src/validate_dataset.py
python -m unittest discover -s tests -v
```

## Columns
| Column | Meaning | Unit / typical range |
|---|---|---|
| crew_id | Crew member ID | Crew-01 to Crew-20 |
| mission_day | Day of mission | 1-180 |
| timestamp | Date | YYYY-MM-DD |
| sleep_hours | Hours slept | hours |
| sleep_quality | Sleep quality score | 1-10 (higher = better) |
| resting_heart_rate | Heart rate at rest | beats per minute |
| exercise_minutes | Exercise time | minutes |
| fatigue_score | How tired | 1-10 (higher = more tired) |
| stress_score | How stressed | 1-10 (higher = more stress) |
| reaction_time_ms | Reaction test time | milliseconds (higher = slower) |
| workload_hours | Hours worked | hours |

Do not rename columns without telling the statistics, ML and dashboard members.

## Planned events and labels
- **Crew-01 to Crew-08:** 2 planned events each. **Crew-09 to Crew-16:** 3 planned events each.
  **Crew-17 to Crew-20:** no planned events (control crew members for false-alarm checks).
- 40 events in total. Types: increased workload, reduced sleep, increased fatigue,
  increased stress. Each lasts 8-10 days.
- Anomaly labels: 369 rows are labeled 1 (368 event days + 1 sensor-error row).
- Risk categories: 3,232 low, 168 moderate, 200 high.
- Rows with `anomaly_reason = sensor_error` are data-quality problems, not health events.
  Leave them out when scoring health-anomaly detection (see `docs/EVALUATION.md`).

## Train / validation / test split
- The split is by **crew member**: each crew member is in exactly one group.
- 12 crew members in train, 4 in validation, 4 in test (see `data/evaluation/splits.csv`).
- Health events per split: 27 train, 8 validation, 5 test.
- A detector should learn each crew member's own baseline from their early days and judge
  later days. It must never use future days to judge an earlier day.

## Cleaning rules
- Impossible values (sensor errors) are set to blank, never guessed.
- Missing values stay blank. Alerts that use a blank value should show lower confidence.
- Outliers are kept, because planned events must stay visible.
- Raw data is never overwritten. Every blank is listed in `data/processed/data_quality_log.csv`.
- Expected counts: 8 missing values in the raw file, 1 sensor error (Crew-19, day 9,
  resting heart rate 255), so 9 blank cells after cleaning.

## Known assumptions and limits
- All values and relationships are **team assumptions**, not medical rules.
- Each crew member has their own normal baseline.
- Links: less sleep -> lower sleep quality and more fatigue; more workload -> more stress;
  more fatigue -> slower reaction; more stress -> higher heart rate.
- The 1-10 scales (sleep quality, fatigue, stress) are team-created, not clinical scales.
- Events are planned and fairly predictable, and there are no recovery days after events yet.
- The dataset is small for machine learning (20 crew members). Use it to test the pipeline,
  not as evidence that a model works on real astronauts.