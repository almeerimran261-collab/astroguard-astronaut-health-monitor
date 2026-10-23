  # AstroGuard Data Sources

## Project purpose
AstroGuard monitors astronaut health and performance trends during long-duration
space missions. It learns each astronaut's personal baseline, detects meaningful
changes, explains alerts, and recommends monitoring or review by a mission medical
officer. It does not diagnose diseases or prescribe treatment.

## Required monitoring areas
- Sleep
- Fatigue
- Exercise
- Resting heart rate
- Stress
- Reaction time
- Workload

## Source record 1: Synthetic astronaut dataset (main dataset)
Dataset name: AstroGuard synthetic daily crew dataset
URL: Not applicable (created by our team with src/generate_synthetic_data.py)
Human, non-human, or synthetic: Synthetic
Spaceflight, analog, or general study: Simulation inspired by NASA Human Research Program risks
Variables used: crew_id, mission_day, timestamp, sleep_hours, sleep_quality,
resting_heart_rate, exercise_minutes, fatigue_score, stress_score,
reaction_time_ms, workload_hours
File format: CSV
License or access conditions: Created by our team, free to use in this project
How it supports the project: Gives a complete daily dataset with known expected
outcomes so the whole system can be tested safely.
Limitations: Not real data. Not clinically validated. Not an official NASA system.
Relationships between columns are team assumptions. Does not represent real
astronaut medical records.

## Source record 2: NASA Life Sciences Portal (reviewed, not used directly)
Dataset name: NASA Life Sciences Portal (NLSP) / Life Sciences Data Archive
URL: https://www.nasa.gov/hrp/nlsp/
Human, non-human, or synthetic: Human, plant and animal subjects (we only care about human studies)
Spaceflight, analog, or general study: Spaceflight and ground analog (for example bed rest)
Variables used: None directly. Used for background context only.
File format: Varies by study
License or access conditions: Public portal; some studies may need data sharing agreements
How it supports the project: Explains why sleep, fatigue, stress, heart rate and
reaction time matter on space missions
Limitations: Detailed research data, not a daily table with our 11 columns. Access may be limited.

## Source record 3: NASA Open Science Data Repository (reviewed, not used directly)
Dataset name: NASA OSDR
URL: https://osdr.nasa.gov/
Human, non-human, or synthetic: Mixed (many studies are not human)
Spaceflight, analog, or general study: Spaceflight-related research
Variables used: None directly
File format: Varies by study
License or access conditions: Check each study
How it supports the project: Background context only
Limitations: Many studies are not human astronaut data and do not have our daily columns

## Project statement
This prototype uses simulated crew-monitoring records inspired by NASA Human
Research Program risks. It demonstrates the software and analytics workflow.
It is not clinically validated, is not an official NASA system, and does not
represent real astronaut medical records.