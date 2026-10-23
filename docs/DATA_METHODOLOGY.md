# How We Made the AstroGuard Data (Simple Guide)

## Please read first
- This data is **fake (simulated)**. It is not from real astronauts.
- The numbers and the connections between them are **our team's guesses**.
  They are not proven medical facts.
- It is made only to test and demo our software.

## How we made it
Script: `src/generate_synthetic_data.py`
(It always gives the same data, because we fixed the random seed at 42.)

1. We create 20 crew members (Crew-01 to Crew-20) and 180 mission days.
2. Each crew member gets their own **normal** values (their baseline).
3. Every day, each value moves up or down a little, like real life.
4. We add **planned events** on certain days (for example, a few nights of bad sleep).
5. Some columns follow others (see "Connections" below).
6. We keep all values in sensible ranges.
7. We add the answer keys (labels) and a crew-level train/validation/test split.
8. We blank 8 values on purpose (missing data) and add 1 broken sensor reading.

## Each crew member's normal values (our guesses)
Each crew member's baseline is picked at random (but repeatable) from these ranges.
The exact values are in `src/generate_synthetic_data.py`.

| Measure | Normal range across crew members |
|---|---|
| Sleep (hours) | 6.5 to 8.0 |
| Sleep quality (1-10) | 6 to 8 |
| Resting heart rate (beats per minute) | 58 to 76 |
| Exercise (minutes) | 35 to 70 |
| Fatigue (1-10) | 2 to 5 |
| Stress (1-10) | 2 to 5 |
| Reaction time (ms) | 420 to 530 |
| Work (hours) | 7.0 to 10.0 |

## Connections between columns (our guesses)
| If this changes... | ...this changes too |
|---|---|
| Less sleep than normal | Sleep quality goes down (about 1.2 points per hour) |
| Less sleep than normal | Fatigue goes up (about 0.8 points per hour) |
| More work than normal | Stress goes up (about 0.8 points per hour) |
| More fatigue than normal | Reaction gets slower (about 25 ms per point) |
| More stress than normal | Heart rate goes up (about 1.5 beats per point) |

## What happens to each crew member
The exact days are in `data/evaluation/ground_truth/scenario_ground_truth.csv`.
That file is only for checking results afterwards. Models must never load it.

- **Crew-01 to Crew-08:** 2 planned events each.
- **Crew-09 to Crew-16:** 3 planned events each.
- **Crew-17 to Crew-20:** nothing planned. They stay normal (control crew members).

Each event lasts 8 to 10 days and is one of these:

| Event | What we change |
|---|---|
| Reduced sleep | 2.0 to 2.5 fewer hours of sleep |
| Increased workload | 3.0 to 3.5 more work hours, and 15 to 20 fewer exercise minutes (some events) |
| Increased fatigue | Fatigue score +3 |
| Increased stress | Stress score +3 |

The connections above then move the linked columns too. We know these events in advance,
so we can check if our alerts find them. There are no recovery days after events yet.

## Labels and split
- `anomaly_labels.csv`: 1 for every day inside a planned event (and for the sensor-error
  day), 0 otherwise. 369 rows are labeled 1.
- `risk_labels.csv`: low (no event), moderate (workload or stress events), high (reduced
  sleep or fatigue events).
- `splits.csv`: each crew member is in exactly one of train, validation or test.

## Our own 1-10 scores
Sleep quality, fatigue and stress are scored from 1 to 10.
We made these scales ourselves. They are not official medical scales.

## Blank cells and bad values
- **A blank means "we don't know."** It does not mean zero, and it does not mean normal.
- **Impossible values become blank.** Example: heart rate 255 cannot be real.
  We blank it and write it in `data/processed/data_quality_log.csv`.
- **We never fill blanks with guesses** in the shared file. A guess would look real
  when it is not.
- **Alerts that use a blank value should show lower confidence** and a data warning.
- **We keep unusual values** (outliers). They are the events we want to detect.

## Where real data could come from (ideas for the future, NOT built)
| Column | Possible real source |
|---|---|
| Sleep hours and quality | Wearable sleep tracker or a sleep questionnaire |
| Resting heart rate | Wearable sensor |
| Exercise minutes | Exercise machine logs or a wearable |
| Fatigue and stress scores | Short daily questionnaire for the crew |
| Reaction time | Quick computer test (press a button when a light appears) |
| Work hours | Mission schedule or crew activity log |

Nothing in this prototype is connected to real sensors.