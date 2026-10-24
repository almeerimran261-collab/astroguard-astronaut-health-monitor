# AstroGuard ML Handoff

## What this analysis provides

The analysis reads `data/processed/astronaut_health.csv` only. It creates statistics, missing-value checks, ten charts, a report, and personal-baseline comparisons. It does not use ground-truth label files and does not train a model.

## Main points to consider

- Dataset: 3,600 rows, 11 columns, 20 simulated crew members, mission days 1–180.
- There are 9 missing measurement cells in total: sleep hours (1), sleep quality (1), resting heart rate (3), fatigue score (1), and reaction time (3). There are no duplicate rows.
- Candidate measurements include sleep hours and quality, resting heart rate, exercise minutes, fatigue score, stress score, reaction time, and workload hours.
- The strongest of the four relationships requested in the assignment is workload and stress (Pearson r is about 0.498); fatigue and reaction time are also positively associated (r is about 0.441). These are associations in simulated data, not proof of cause.
- Each person's baseline table is in `assets/analysis_results/personal_baselines_days_1_14.csv`.
- The file `measurements_vs_baseline.csv` contains differences from that person's days 1–14 average.

## Suggested next steps for the ML member

1. Calculate a separate baseline for each `crew_id` using only days 1–14.
2. When evaluating day N, do not use information from days after N. Prevent future-data leakage.
3. Explore persistent changes over multiple days, such as sleep below personal baseline, rising fatigue, slower reaction time, or workload rising while exercise falls.
4. Check multiple signals together, but do not treat these exploratory suggestions as final alert thresholds.
5. Keep data-quality warnings visible. Do not silently drop missing or unusual values.
6. Test any model with the approved evaluation data only after the exploratory analysis is complete.
7. Describe results as simulated-data findings. This analysis is not a diagnostic tool or clinical validation.

## Message to send to the ML teammate

I completed the exploratory analysis of `data/processed/astronaut_health.csv`. The data contains 20 simulated crew members across 180 mission days. I analyzed sleep, fatigue, stress, workload, exercise, resting heart rate, and reaction time. The main patterns to monitor are reduced sleep, increasing fatigue, slower reaction time, increasing workload, and multiple indicators changing together. Please use personal baselines from mission days 1–14 and ensure that future days are not used to judge earlier days. The analysis is based on simulated data and should not be interpreted as clinical evidence.

## Message to send to the dashboard teammate

The dashboard should display the measurements and personal-baseline comparisons. It should not create a separate dataset or rename the shared dataset columns. Useful views include a mission overview, an individual crew view, baseline comparisons, trend charts, alert explanations, and data-quality warnings.
