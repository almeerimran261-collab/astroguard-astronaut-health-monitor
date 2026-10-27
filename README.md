# AstroGuard

AstroGuard is an explainable, non-diagnostic health and performance monitoring system for astronauts on long-duration missions.

## Project goal

The system monitors astronaut health and performance indicators such as:

- Sleep
- Fatigue
- Exercise
- Resting heart rate
- Reaction time
- Workload

It learns each astronaut's personal baseline, detects meaningful changes, and displays whether the astronaut is Stable, on Watch, or requires Review.

## Important limitation

AstroGuard is a hackathon prototype. It is not a medical diagnostic system, it is not clinically validated, and it is not an official NASA system. It is designed to support monitoring and review, not replace medical professionals.

## Planned technology

- Python
- Pandas
- Scikit-learn
- Plotly
- Streamlit
- NASA open-data resources
## Repository structure

```text
app/                    Streamlit dashboard
data/                   Processed data and evaluation files
docs/                   Methodology, analysis, and project documentation
notebooks/              Exploratory analysis notebook
src/                    Data, ML, and evaluation modules
tests/                  Automated tests
assets/analysis_charts/ Analysis visualizations
assets/analysis_results/ Statistical outputs
assets/ml_results/      ML alerts and evaluation outputs
## Installation

Create a virtual environment:

```powershell
python -m venv .venv
```

Activate it:

```powershell
.\.venv\Scripts\Activate.ps1
```

If PowerShell blocks activation, run:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

Install dependencies:

```powershell
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

## Run the ML pipeline

From the repository root:

```powershell
python -m src.run_pipeline
```

This generates:

```text
assets/ml_results/personal_baselines.csv
assets/ml_results/baseline_features.csv
assets/ml_results/alert_results.csv
```

`baseline_features.csv` is a generated intermediate file. It can be removed before committing because the pipeline regenerates it.

## Run the tests

```powershell
python -m pytest tests -q
```

The tests check dataset shape, crew coverage, warm-up protection, missing-data warnings, persistent anomalies, recovery behavior, past-only rolling features, and required output columns.

## Run the evaluator

Generate predictions first:

```powershell
python -m src.run_pipeline
```

Then run:

```powershell
python -m src.evaluate_model
```

The evaluation summaries are written to:

```text
assets/ml_results/evaluation_overall.csv
assets/ml_results/evaluation_by_crew.csv
```

Ground-truth files are used only for evaluation. They must not be used as model inputs.

## Run the dashboard

If the Streamlit application is available:

```powershell
streamlit run app\streamlit_app.py
```

## Final simulated evaluation

The point-anomaly threshold was selected using the validation crew group.

On the small simulated test split, the event-level evaluator reported:

- Event precision: 100%
- Event recall: 100%
- False-alarm events: 0
- Median detection delay: 2 days

These results are not clinical validation and should not be generalized to real astronaut health data.

## ML method

See:

```text
docs/ML_METHOD.md
```

for the baseline, feature-engineering, anomaly-detection, persistence, scoring, explanation, and evaluation methodology.

## Safety and scope

AstroGuard is an educational hackathon prototype. It is not an official NASA system, is not clinically validated, and must not be used for diagnosis, treatment, or autonomous medical decisions.

