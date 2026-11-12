\# AstroGuard Dashboard



A Streamlit dashboard that displays the results of the AstroGuard ML pipeline.



AstroGuard uses \*\*simulated data\*\* and is \*\*non-diagnostic\*\*. It is an

educational hackathon prototype. It is not an official NASA system, it is not

clinically validated, and it is not a medical tool.



\## How to run



Use Python 3.12. The pinned package versions do not install on Python 3.14.



From the repository root:



&#x20;   python -m pip install -r requirements.txt

&#x20;   python -m src.run\_pipeline

&#x20;   python -m streamlit run app/streamlit\_app.py



The dashboard opens at http://localhost:8501.



\## Where the data comes from



The dashboard only \*\*reads\*\* files. It does not run the pipeline and it does

not create or change any results. If a file is missing, it shows an error

message instead of showing made-up numbers.



\- `assets/ml\_results/alert\_results.csv`: alert states, scores, confidence,

&#x20; explanations, recommendations and data-quality warnings

&#x20; (made by `python -m src.run\_pipeline`).

\- `data/processed/astronaut\_health.csv`: daily measurements for the trend

&#x20; charts.

\- `data/processed/data\_quality\_log.csv`: record of bad values that were

&#x20; cleaned.



The ground-truth files in `data/evaluation/` are answer keys for evaluation

only. The dashboard does not use them.



Run the pipeline again whenever the ML code changes, so that

`alert\_results.csv` is current.



\## What the dashboard shows



\- Simulated-data disclaimer (always visible at the top)

\- Mission overview: crew count, mission days, alert-state counts, and a

&#x20; crew comparison chart

\- Sidebar: crew member selector and mission-day filter

\- Alert-state chart for the selected crew member

\- Tabs:

&#x20; - \*\*Trends:\*\* 7 health measurements by mission day, with Watch and Review

&#x20;   Required days marked

&#x20; - \*\*Alerts:\*\* alert table and alert detail with contributing features,

&#x20;   persistent features, combined patterns, explanation and recommendation

&#x20; - \*\*Data quality:\*\* missing-value counts, warnings, baseline sufficiency

&#x20; - \*\*Method notes:\*\* how AstroGuard works and what the results do not mean

