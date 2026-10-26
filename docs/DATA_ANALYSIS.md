# AstroGuard Exploratory Data Analysis

## 1. Purpose

This analysis explores the simulated astronaut health and performance
dataset to describe its structure, summarize its measurements, examine
changes over mission days, compare measurements against personal
baselines, and recommend candidate monitoring signals.

## 2. Dataset Overview

- Number of rows: 3600
- Number of original columns: 11
- Number of crew members: 20
- Mission-day range: 1–180
- Missing cells: 9
- Duplicate complete rows: 0
- Source file: `data/processed/astronaut_health.csv`

### Missing Values

- sleep_hours: 1
- sleep_quality: 1
- resting_heart_rate: 3
- fatigue_score: 1
- reaction_time_ms: 3

### Data Quality

The dataset was checked for missing values, duplicate rows, duplicate
crew-day combinations, crew coverage, and unusual measurement ranges.
See the supporting CSV files in the `assets` directory.

## 3. Summary Statistics

| variable | count | mean | median | std | min | 25% | 50% | 75% | max |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| sleep_hours | 3599.0 | 7.17 | 7.2 | 0.67 | 3.6 | 6.8 | 7.2 | 7.6 | 9.0 |
| sleep_quality | 3599.0 | 7.089 | 7.0 | 1.28 | 2.0 | 6.0 | 7.0 | 8.0 | 10.0 |
| resting_heart_rate | 3597.0 | 67.319 | 67.0 | 5.191 | 51.0 | 64.0 | 67.0 | 71.0 | 82.0 |
| exercise_minutes | 3600.0 | 57.663 | 58.0 | 11.845 | 14.0 | 50.0 | 58.0 | 66.0 | 96.0 |
| fatigue_score | 3599.0 | 3.83 | 4.0 | 1.37 | 1.0 | 3.0 | 4.0 | 5.0 | 9.0 |
| stress_score | 3600.0 | 3.267 | 3.0 | 1.44 | 1.0 | 2.0 | 3.0 | 4.0 | 9.0 |
| reaction_time_ms | 3597.0 | 468.865 | 464.0 | 40.872 | 356.0 | 437.0 | 464.0 | 499.0 | 640.0 |
| workload_hours | 3600.0 | 8.56 | 8.6 | 1.188 | 5.0 | 7.7 | 8.6 | 9.3 | 13.6 |

These values describe the simulated dataset. They are not clinical
reference ranges.

## 4. Personal Differences

The lowest average sleep duration was observed for Crew-18
(6.619 hours).

The highest average sleep duration was observed for Crew-02
(7.877 hours).

Individual baselines calculated from mission days 1–14 are saved in
`assets/personal_baselines_days_1_14.csv`. Personal baselines are useful
because different crew members can have different usual measurements.

## 5. Time-Series Observations

Average measurements by 30-day period:

| mission_period | sleep_hours | sleep_quality | resting_heart_rate | exercise_minutes | fatigue_score | stress_score | reaction_time_ms | workload_hours |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Days 1–30 | 7.239 | 6.983 | 67.321 | 57.647 | 3.762 | 3.252 | 466.855 | 8.582 |
| Days 31–60 | 7.107 | 7.117 | 67.317 | 57.56 | 3.938 | 3.293 | 472.332 | 8.463 |
| Days 61–90 | 7.141 | 7.082 | 67.182 | 57.635 | 3.853 | 3.212 | 468.352 | 8.54 |
| Days 91–120 | 7.158 | 7.135 | 67.668 | 56.592 | 3.813 | 3.48 | 468.653 | 8.79 |
| Days 121–150 | 7.169 | 7.168 | 67.17 | 58.143 | 3.818 | 3.208 | 468.448 | 8.467 |
| Days 151–180 | 7.207 | 7.048 | 67.254 | 58.402 | 3.797 | 3.155 | 468.548 | 8.519 |

Individual and crew-wide time-series charts are saved in
`assets/analysis_charts/`.

Observations from the mission-period summaries

Sleep duration: Average sleep was 7.239 hours during days 1–30 and 7.107 hours during days 31–60. It then remained relatively stable, reaching 7.207 hours during days 151–180. These period averages do not show a consistent decline throughout the mission.

Sleep quality: The period averages ranged from 6.983 to 7.168. The values fluctuated slightly rather than showing a clear sustained increase or decrease.

Fatigue: Average fatigue increased from 3.762 during days 1–30 to 3.938 during days 31–60, then fluctuated within a relatively narrow range for the remaining periods.

Workload: Average workload ranged from 8.463 to 8.790 hours across the six periods. It was highest during days 91–120 and lower during days 121–150.

Reaction time: Average reaction time increased from 466.855 ms during days 1–30 to 472.332 ms during days 31–60. It subsequently remained between approximately 468 and 469 ms for most periods.

Overall interpretation: The 30-day summaries show some variation in the measurements, but they do not establish a continuous deterioration in astronaut health or performance. Individual time-series charts and personal-baseline comparisons should be examined to identify changes that may be hidden by averages.

These are exploratory observations from simulated data. They describe patterns in the reported averages and do not establish medical causes or validated alert thresholds.

## 6. Relationships Between Variables

- **Sleep and fatigue**: r = -0.122; weak negative association; n = 3598.
- **Workload and stress**: r = 0.498; moderate positive association; n = 3600.
- **Fatigue and reaction time**: r = 0.441; moderate positive association; n = 3596.
- **Stress and resting heart rate**: r = 0.246; weak positive association; n = 3597.

These correlations describe associations in the simulated data.
Correlation does not prove causation.

## 7. Possible Monitoring Signals

Candidate patterns for further investigation include:

- Sleep remaining below an astronaut's personal baseline over several days.
- Fatigue increasing over time.
- Reaction time becoming slower than the astronaut's usual level.
- Workload increasing while exercise decreases.
- Multiple indicators changing together.

These are candidate monitoring signals, not validated medical alerts.

## 8. Limitations

- The dataset is simulated.
- Results are not clinical evidence.
- The sample is not representative of all astronauts.
- Correlations do not establish cause and effect.
- Missing values may affect individual calculations.
- Exploratory z-scores use the entire mission and therefore include
  future observations.
- A baseline calculated from days 1–14 should only be used to evaluate
  later observations, after that baseline period is complete.
- The final anomaly-detection method and alert thresholds have not been
  validated by this exploratory analysis.

## 9. Recommendations for the ML Member

Candidate features include sleep duration, sleep quality, resting heart
rate, exercise minutes, fatigue score, stress score, reaction time, and
workload hours.

Use personal baselines calculated from mission days 1–14 for later-day
comparisons. Avoid future-data leakage when creating training features,
evaluating predictions, or setting alert thresholds.

Investigate sustained changes and combinations of indicators. The ML
member should select the final detection method, define thresholds, and
evaluate performance using an appropriate validation strategy.
