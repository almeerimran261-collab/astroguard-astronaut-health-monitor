# AstroGuard — ML Handoff

## Analysis completed

The exploratory analysis examined the simulated astronaut health and performance dataset containing 20 crew members across 180 mission days.

The analysis covered data quality, summary statistics, individual differences, personal baselines, time-series charts, correlations, and possible unusual sleep measurements.

## Important findings

- Workload and stress showed a moderate positive association in the overall dataset.
- Fatigue and reaction time showed a moderate positive association.
- Sleep and fatigue showed a weak negative association.
- Stress and resting heart rate showed a weak positive association.
- Individual baseline comparisons provide a way to identify changes relative to each astronaut's usual measurements.

## Candidate model features

Consider sleep duration, sleep quality, fatigue, stress, workload, exercise, resting heart rate, and reaction time.

Use personal baselines based on mission days 1–14 when comparing later measurements. Avoid using future data to judge earlier mission days.

Consider sustained changes and multiple indicators changing together. The ML teammate must determine and evaluate the final method and alert thresholds.

## Limitations

The dataset is simulated. These findings are exploratory and do not establish causation or provide clinical evidence.

## Files provided

- `exploratory_analysis.ipynb`
- `DATA_ANALYSIS.md`
- `analysis_charts/`
- `analysis_results/`
