# AstroGuard Exploratory Data Analysis

## 1. Purpose

This report describes the simulated astronaut health and performance measurements. It checks data quality, summarizes the variables, looks for patterns over mission days, compares measurements with personal baselines, and suggests signals the ML member could monitor. This is exploratory analysis, not a medical assessment.

## 2. Dataset overview

- **Number of rows:** 3,600
- **Number of columns:** 11
- **Crew members:** 20
- **Mission duration:** days 1–180
- **Variables:** crew ID, mission day, timestamp, sleep hours, sleep quality, resting heart rate, exercise minutes, fatigue score, stress score, reaction time, and workload hours.
- **Missing measurements:** 9 cells across the dataset. Columns with missing values: `sleep_hours` (1), `sleep_quality` (1), `resting_heart_rate` (3), `fatigue_score` (1), `reaction_time_ms` (3).
- **Duplicate rows:** 0
- **Ground-truth labels:** not used.

Each crew member has 180 unique mission days at minimum. The dataset contains simulated daily records, so its patterns should not be treated as clinical evidence.

## 3. Summary statistics

| Measurement | Mean | Median | Minimum | Maximum | Standard deviation |
|---|---:|---:|---:|---:|---:|
| Sleep hours | 7.17 | 7.20 | 3.60 | 9.00 | 0.67 |
| Sleep quality | 7.09 | 7.00 | 2.00 | 10.00 | 1.28 |
| Resting heart rate | 67.32 | 67.00 | 51.00 | 82.00 | 5.19 |
| Exercise minutes | 57.66 | 58.00 | 14.00 | 96.00 | 11.85 |
| Fatigue score | 3.83 | 4.00 | 1.00 | 9.00 | 1.37 |
| Stress score | 3.27 | 3.00 | 1.00 | 9.00 | 1.44 |
| Reaction time (ms) | 468.86 | 464.00 | 356.00 | 640.00 | 40.87 |
| Workload hours | 8.56 | 8.60 | 5.00 | 13.60 | 1.19 |

These are observed values in this dataset, not medical reference ranges. Unusually low or high values should be checked and kept for review rather than automatically deleted, because they may be simulated events.

## 4. Personal differences

Across crew-level averages, sleep ranges from 6.62 to 7.88 hours; fatigue from 2.01 to 5.24; and reaction time from 428.1 to 523.3 ms. This supports comparing each person with their own baseline instead of treating one value as normal for everyone.

The project calculates a separate baseline for each crew member using mission days 1–14. Later measurements are compared with that crew member's baseline. This is more informative than applying one fixed average to all crew members. The first 14 days are only a baseline choice for this assignment, not a validated clinical baseline.

## 5. Time-series observations

The four single-crew charts show sleep, fatigue, workload, and reaction time across mission days for Crew-01. Four additional charts show daily averages across all crew members for fatigue, reaction time, sleep, and workload. The observations below compare six 30-day periods; they describe this dataset and should not be treated as medical conclusions.

- Average sleep was lowest in **Days 31-60** (7.11 hours) and highest in **Days 1-30** (7.24 hours) when comparing six 30-day periods.
- Average fatigue was lowest in **Days 1-30** (3.76 score points) and highest in **Days 31-60** (3.94 score points) when comparing six 30-day periods.
- Average reaction time was lowest in **Days 1-30** (466.85 ms) and highest in **Days 31-60** (472.33 ms) when comparing six 30-day periods.
- Average workload was lowest in **Days 31-60** (8.46 hours) and highest in **Days 91-120** (8.79 hours) when comparing six 30-day periods.

The dataset-wide observed ranges include sleep from 3.6 to 9.0 hours, fatigue from 1.0 to 9.0, and reaction time from 356 to 640 ms. Higher reaction time means slower performance, as stated in the assignment guide. Daily averages can hide individual changes, so review the single-crew plots alongside group averages.

## 6. Relationships between variables

- **Sleep and fatigue**: Pearson r = -0.122 (paired records = 3598).
- **Workload and stress**: Pearson r = 0.498 (paired records = 3600).
- **Fatigue and reaction time**: Pearson r = 0.441 (paired records = 3596).
- **Stress and resting heart rate**: Pearson r = 0.246 (paired records = 3597).

A correlation describes how two variables move together in this simulated dataset. It does not prove that one variable causes another. The correlation heatmap shows the pairwise relationships among the eight numeric measurements. Relationships may reflect assumptions used to create the simulated data.

## 7. Possible monitoring signals

The ML member could investigate these candidate signals:

- Sleep stays below an individual's days 1–14 baseline for several consecutive days.
- Fatigue increases over multiple days compared with the person's usual pattern.
- Reaction time becomes slower than the individual's baseline.
- Workload rises while exercise minutes fall.
- Several indicators change together over the same period.
- Missing or out-of-range measurements appear and may affect an alert.

The file `possible_sleep_changes.csv` contains exploratory sleep observations whose whole-mission crew-specific z-score has an absolute value above 2. This is only a screening aid. Because it uses each person's entire mission, it must not be used as a real-time, forward-looking alert rule.

## 8. Limitations

- The data is simulated, not collected from real astronauts.
- Relationships may reflect team-created simulation assumptions.
- This is not clinical evidence and does not diagnose health conditions.
- The sample is not representative evidence about astronauts generally.
- Missing measurements can affect statistics and correlations; pandas calculates each statistic using available values.
- Correlation does not prove cause and effect.
- Days 1–14 are an assignment baseline choice, not a validated medical threshold.
- Exploratory z-scores use the full mission and are not suitable as a real-time prediction method.
- Observed minimum and maximum values are not official clinical limits.

## 9. Recommendations for the ML member

1. Use the measurement variables as candidate features: sleep hours, sleep quality, resting heart rate, exercise minutes, fatigue, stress, reaction time, and workload.
2. Calculate personal baselines from mission days 1–14, separately for each `crew_id`.
3. Compare each future measurement only with information available up to that point. Do not use future days to judge earlier days.
4. Consider changes over several consecutive days and multiple indicators together, rather than relying only on one unusually high or low reading.
5. Keep missingness and data-quality checks visible; do not silently replace missing values or delete unusual measurements.
6. Treat the analysis as evidence for model design, not as a validated alert threshold or clinical decision rule.
7. Evaluate any later model separately using the approved evaluation process. Ground-truth label files were not used for this exploratory analysis.

## Files created

- `notebooks/exploratory_analysis.ipynb` — notebook entry point and interpretation guide.
- `src/exploratory_analysis.py` — repeatable analysis code.
- `assets/analysis_charts/` — ten saved charts.
- `assets/analysis_results/` — summary tables, missingness, correlations, baselines, and exploratory changes.
