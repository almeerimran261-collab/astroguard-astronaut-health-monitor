# How to Evaluate the Anomaly Detector

## Keep the answer key separate

Use `data/processed/astronaut_health.csv` as the measurement input.

Use `data/evaluation/splits.csv` to find which crew members belong to train, validation, and test.

Do not give any files in `data/evaluation/ground_truth/` to the model. Those files contain the answers. Use them only after the model has made predictions.

Use the training group to fit the model. Use validation to choose its settings. Use the test group once for the final score. Do not keep changing the model based on its test score.

Predict each day using only that day and earlier days. Never use later days to judge an earlier day.

## Baseline window

Each crew member's normal values should be learned from that crew member's own early days. In this dataset the first planned event starts on day 20, so days 1-14 of every crew member are event-free and can be used as the baseline window. (This is a suggestion. If the team chooses a different window, write the final choice here.)

## What is an event?

A true event is a run of consecutive days for the same crew member where `anomaly_label` equals `1` in `anomaly_labels.csv`. First remove every row where `anomaly_reason` equals `sensor_error` (see "Sensor errors are not health anomalies" below).

A predicted event is a run of consecutive days for the same crew member where the model predicts an anomaly.

For this project, count a predicted event as finding a true event if they overlap on at least one day. Count each event only once.

## What to report

1. **Event precision:** Of the events the model predicted, how many overlapped a true event?
2. **Event recall:** Of the true events, how many did the model find?
3. **False alarms:** How many predicted events did not overlap any true event? Also report false alarms per 100 crew-days.
4. **Detection delay:** For each event the model found, count how many days passed between the event's first day and the model's first alert during it. Report the median number of days.
5. **Results for each crew:** Show the scores and event counts separately for each test crew, as well as the overall results.

If the model predicts no events, write `N/A` for precision. If there are no true events, write `N/A` for recall and detection delay.

## Sensor errors are not health anomalies

Rows with `anomaly_reason = sensor_error` in `anomaly_labels.csv` are data-quality problems, not health events. The cleaning step turns them into blank values, so a detector cannot see them.

- Do NOT count them when scoring health-anomaly detection (precision, recall, detection delay). Filter them out before scoring.
- They are handled by the data-quality checks, and the dashboard should show a data-quality warning for those days.

## Important limits

This is a small simulated dataset with planned patterns. It is not real astronaut data and is not clinically validated. The test group has only 5 events (validation has 8), so scores will be noisy. Report the number of crews and events with the scores. Do not claim that these results prove a model will work on real people or real missions.