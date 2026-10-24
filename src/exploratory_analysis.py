"""
AstroGuard exploratory analysis.
Run from any working directory:
    python src/exploratory_analysis.py
All paths are resolved relative to this file's project root.
"""
from pathlib import Path
import warnings
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "data" / "processed" / "astronaut_health.csv"
CHART_DIR = ROOT / "assets" / "analysis_charts"
RESULT_DIR = ROOT / "assets" / "analysis_results"
DOCS_DIR = ROOT / "docs"

NUMERIC_COLUMNS = [
    "sleep_hours", "sleep_quality", "resting_heart_rate", "exercise_minutes",
    "fatigue_score", "stress_score", "reaction_time_ms", "workload_hours",
]
REQUIRED_COLUMNS = [
    "crew_id", "mission_day", "timestamp", *NUMERIC_COLUMNS
]
CHART_DPI = 150


def ensure_directories():
    for path in (CHART_DIR, RESULT_DIR, DOCS_DIR):
        path.mkdir(parents=True, exist_ok=True)


def load_data():
    if not DATA_PATH.exists():
        raise FileNotFoundError(
            f"Dataset not found at: {DATA_PATH}\n"
            "Keep astronaut_health.csv in data/processed/ inside the project folder."
        )
    data = pd.read_csv(DATA_PATH, parse_dates=["timestamp"])
    missing_columns = [c for c in REQUIRED_COLUMNS if c not in data.columns]
    if missing_columns:
        raise ValueError(f"Dataset is missing required columns: {missing_columns}")
    data = data.sort_values(["crew_id", "mission_day"]).reset_index(drop=True)
    return data


def save_chart(fig, filename):
    fig.tight_layout()
    fig.savefig(CHART_DIR / filename, dpi=CHART_DPI, bbox_inches="tight")
    plt.close(fig)


def make_charts(data, baseline):
    crew = "Crew-01"
    subset = data[data["crew_id"] == crew].copy()
    if subset.empty:
        crew = sorted(data["crew_id"].dropna().unique())[0]
        subset = data[data["crew_id"] == crew].copy()

    chart_specs = [
        ("sleep_hours", "Sleep duration", "Sleep hours", "sleep_crew01.png"),
        ("fatigue_score", "Fatigue trend", "Fatigue score", "fatigue_crew01.png"),
        ("workload_hours", "Workload trend", "Workload hours", "workload_crew01.png"),
        ("reaction_time_ms", "Reaction-time trend", "Reaction time (ms)", "reaction_time_crew01.png"),
    ]
    for column, title, ylabel, filename in chart_specs:
        fig, ax = plt.subplots(figsize=(12, 5))
        ax.plot(subset["mission_day"], subset[column], linewidth=1.5)
        ax.set(title=f"{title} for {crew}", xlabel="Mission day", ylabel=ylabel)
        ax.grid(True, alpha=0.3)
        save_chart(fig, filename)

    corr = data[NUMERIC_COLUMNS].corr(numeric_only=True)
    fig, ax = plt.subplots(figsize=(10, 8))
    image = ax.imshow(corr, cmap="coolwarm", vmin=-1, vmax=1, aspect="auto")
    ax.set_xticks(range(len(corr.columns)), corr.columns, rotation=45, ha="right")
    ax.set_yticks(range(len(corr.index)), corr.index)
    for i in range(len(corr.index)):
        for j in range(len(corr.columns)):
            value = corr.iloc[i, j]
            label = "NA" if pd.isna(value) else f"{value:.2f}"
            ax.text(j, i, label, ha="center", va="center", fontsize=8)
    fig.colorbar(image, ax=ax, label="Pearson correlation")
    ax.set_title("Correlation Between Simulated Health and Performance Variables")
    save_chart(fig, "correlation_heatmap.png")

    # Daily averages across all crew members.
    daily = data.groupby("mission_day", as_index=False)[
        ["sleep_hours", "fatigue_score", "reaction_time_ms", "workload_hours"]
    ].mean()
    average_specs = [
        ("fatigue_score", "Average fatigue score across all crew", "Fatigue score",
         "fatigue_score_all_crew_daily_average.png"),
        ("reaction_time_ms", "Average reaction time across all crew", "Reaction time (ms)",
         "reaction_time_ms_all_crew_daily_average.png"),
        ("sleep_hours", "Average sleep duration across all crew", "Sleep hours",
         "sleep_hours_all_crew_daily_average.png"),
        ("workload_hours", "Average workload across all crew", "Workload hours",
         "workload_hours_all_crew_daily_average.png"),
    ]
    for column, title, ylabel, filename in average_specs:
        fig, ax = plt.subplots(figsize=(12, 5))
        ax.plot(daily["mission_day"], daily[column], linewidth=1.6)
        ax.set(title=title, xlabel="Mission day", ylabel=ylabel)
        ax.grid(True, alpha=0.3)
        save_chart(fig, filename)

    # Personal baseline comparison for the first crew member.
    crew_baseline = baseline.loc[crew, "sleep_hours"]
    fig, ax = plt.subplots(figsize=(12, 5))
    ax.plot(subset["mission_day"], subset["sleep_hours"], label="Actual sleep", linewidth=1.5)
    ax.axhline(crew_baseline, linestyle="--", label="Days 1–14 personal baseline")
    ax.set(title=f"Sleep Compared With Personal Baseline ({crew})",
           xlabel="Mission day", ylabel="Sleep hours")
    ax.legend()
    ax.grid(True, alpha=0.3)
    save_chart(fig, "sleep_vs_baseline.png")


def build_results(data):
    # Data quality
    missing = data.isna().sum().rename("missing_count").to_frame()
    missing["missing_percent"] = (missing["missing_count"] / len(data) * 100).round(3)
    missing.to_csv(RESULT_DIR / "missing_values.csv", index_label="column")

    summary = data[NUMERIC_COLUMNS].describe().T
    summary.to_csv(RESULT_DIR / "analysis_summary_statistics.csv", index_label="variable")

    crew_summary = data.groupby("crew_id")[NUMERIC_COLUMNS].agg(["mean", "median", "std", "min", "max"])
    crew_summary.to_csv(RESULT_DIR / "crew_summary_statistics.csv")

    corr = data[NUMERIC_COLUMNS].corr(numeric_only=True)
    corr.to_csv(RESULT_DIR / "correlation_matrix.csv")

    crew_coverage = data.groupby("crew_id").agg(
        first_mission_day=("mission_day", "min"),
        last_mission_day=("mission_day", "max"),
        records=("mission_day", "count"),
        unique_mission_days=("mission_day", "nunique"),
        first_timestamp=("timestamp", "min"),
        last_timestamp=("timestamp", "max"),
    )
    crew_coverage.to_csv(RESULT_DIR / "crew_coverage.csv")

    # Data dictionary / observed types and completeness.
    column_info = pd.DataFrame({
        "column": data.columns,
        "dtype": [str(data[c].dtype) for c in data.columns],
        "non_missing_count": [int(data[c].notna().sum()) for c in data.columns],
        "missing_count": [int(data[c].isna().sum()) for c in data.columns],
        "unique_values": [int(data[c].nunique(dropna=True)) for c in data.columns],
    })
    column_info.to_csv(RESULT_DIR / "column_information.csv", index=False)

    # Measurement ranges are observed ranges, not medical reference ranges.
    ranges = data[NUMERIC_COLUMNS].agg(["count", "min", "max", "mean", "median", "std"]).T
    ranges.index.name = "variable"
    ranges["interpretation"] = "Observed in this simulated dataset; not a clinical reference range"
    ranges.to_csv(RESULT_DIR / "measurement_ranges.csv")

    baseline_period = data[data["mission_day"].between(1, 14)]
    baseline = baseline_period.groupby("crew_id")[NUMERIC_COLUMNS].mean()
    baseline.to_csv(RESULT_DIR / "personal_baselines_days_1_14.csv")

    # Compare each record with that crew member's baseline.
    baseline_named = baseline.add_suffix("_baseline")
    comparisons = data.merge(baseline_named, left_on="crew_id", right_index=True, how="left")
    for col in NUMERIC_COLUMNS:
        comparisons[f"{col}_difference_from_baseline"] = comparisons[col] - comparisons[f"{col}_baseline"]
    comparisons.to_csv(RESULT_DIR / "measurements_vs_baseline.csv", index=False)

    # Exploratory sleep z-score using each crew member's whole-mission distribution.
    # This is exploratory only and is not a forward-looking production alert method.
    crew_stats = data.groupby("crew_id")["sleep_hours"].agg(["mean", "std"]).rename(
        columns={"mean": "sleep_crew_mean", "std": "sleep_crew_std"}
    )
    z_data = data.merge(crew_stats, on="crew_id", how="left")
    z_data["sleep_z_score"] = (
        (z_data["sleep_hours"] - z_data["sleep_crew_mean"]) /
        z_data["sleep_crew_std"].replace(0, np.nan)
    )
    possible_sleep_changes = z_data[z_data["sleep_z_score"].abs() > 2].copy()
    possible_sleep_changes.to_csv(RESULT_DIR / "possible_sleep_changes.csv", index=False)

    # Four key relationships requested in the guide.
    pairs = [
        ("sleep_hours", "fatigue_score", "Sleep and fatigue"),
        ("workload_hours", "stress_score", "Workload and stress"),
        ("fatigue_score", "reaction_time_ms", "Fatigue and reaction time"),
        ("stress_score", "resting_heart_rate", "Stress and resting heart rate"),
    ]
    key_corr = pd.DataFrame([
        {"relationship": label, "variable_1": a, "variable_2": b,
         "pearson_correlation": data[[a, b]].corr().iloc[0, 1],
         "paired_records": int(data[[a, b]].dropna().shape[0])}
        for a, b, label in pairs
    ])
    key_corr.to_csv(RESULT_DIR / "key_correlations.csv", index=False)

    daily = data.groupby("mission_day").agg(
        crew_records=("crew_id", "count"),
        mean_sleep_hours=("sleep_hours", "mean"),
        mean_fatigue_score=("fatigue_score", "mean"),
        mean_stress_score=("stress_score", "mean"),
        mean_reaction_time_ms=("reaction_time_ms", "mean"),
        mean_workload_hours=("workload_hours", "mean"),
        mean_exercise_minutes=("exercise_minutes", "mean"),
    )
    daily["mission_period"] = pd.cut(
        daily.index, bins=[0, 30, 60, 90, 120, 150, 180],
        labels=["Days 1-30", "Days 31-60", "Days 61-90", "Days 91-120", "Days 121-150", "Days 151-180"]
    )
    period_summary = daily.groupby("mission_period", observed=False).mean(numeric_only=True)
    period_summary.to_csv(RESULT_DIR / "mission_period_summary.csv")

    make_charts(data, baseline)
    return {
        "data": data, "baseline": baseline, "summary": summary, "corr": corr,
        "missing": missing, "crew_summary": crew_summary, "key_corr": key_corr,
        "possible_sleep_changes": possible_sleep_changes,
        "duplicate_count": int(data.duplicated().sum()),
        "daily": daily, "period_summary": period_summary,
    }


def write_report(results):
    data = results["data"]
    summary = results["summary"]
    missing = results["missing"]
    corr = results["corr"]
    key_corr = results["key_corr"]
    baseline = results["baseline"]
    duplicates = results["duplicate_count"]

    def stat(col, item):
        return float(summary.loc[col, item])
    missing_total = int(data.isna().sum().sum())
    missing_cols = missing[missing["missing_count"] > 0]
    missing_text = ", ".join(
        f"`{idx}` ({int(row['missing_count'])})" for idx, row in missing_cols.iterrows()
    ) or "None"
    correlations = "\n".join(
        f"- **{r['relationship']}**: Pearson r = {r['pearson_correlation']:.3f} "
        f"(paired records = {int(r['paired_records'])})."
        for _, r in key_corr.iterrows()
    )
    crew_means = data.groupby("crew_id")[NUMERIC_COLUMNS].mean()
    personal = (
        f"Across crew-level averages, sleep ranges from {crew_means['sleep_hours'].min():.2f} "
        f"to {crew_means['sleep_hours'].max():.2f} hours; fatigue from "
        f"{crew_means['fatigue_score'].min():.2f} to {crew_means['fatigue_score'].max():.2f}; "
        f"and reaction time from {crew_means['reaction_time_ms'].min():.1f} to "
        f"{crew_means['reaction_time_ms'].max():.1f} ms. This supports comparing each person "
        f"with their own baseline instead of treating one value as normal for everyone."
    )
    period = results["period_summary"]
    trend_rows = []
    for col, label, unit in [
        ("mean_sleep_hours", "average sleep", "hours"),
        ("mean_fatigue_score", "average fatigue", "score points"),
        ("mean_reaction_time_ms", "average reaction time", "ms"),
        ("mean_workload_hours", "average workload", "hours"),
    ]:
        valid = period[col].dropna()
        if not valid.empty:
            low_period, high_period = valid.idxmin(), valid.idxmax()
            trend_rows.append(
                f"- {label.capitalize()} was lowest in **{low_period}** "
                f"({valid.loc[low_period]:.2f} {unit}) and highest in **{high_period}** "
                f"({valid.loc[high_period]:.2f} {unit}) when comparing six 30-day periods."
            )
    trend_observations = "\n".join(trend_rows)
    lines = f"""# AstroGuard Exploratory Data Analysis

## 1. Purpose

This report describes the simulated astronaut health and performance measurements. It checks data quality, summarizes the variables, looks for patterns over mission days, compares measurements with personal baselines, and suggests signals the ML member could monitor. This is exploratory analysis, not a medical assessment.

## 2. Dataset overview

- **Number of rows:** {len(data):,}
- **Number of columns:** {data.shape[1]}
- **Crew members:** {data['crew_id'].nunique()}
- **Mission duration:** days {int(data['mission_day'].min())}–{int(data['mission_day'].max())}
- **Variables:** crew ID, mission day, timestamp, sleep hours, sleep quality, resting heart rate, exercise minutes, fatigue score, stress score, reaction time, and workload hours.
- **Missing measurements:** {missing_total} cells across the dataset. Columns with missing values: {missing_text}.
- **Duplicate rows:** {duplicates}
- **Ground-truth labels:** not used.

Each crew member has {data.groupby('crew_id')['mission_day'].nunique().min()} unique mission days at minimum. The dataset contains simulated daily records, so its patterns should not be treated as clinical evidence.

## 3. Summary statistics

| Measurement | Mean | Median | Minimum | Maximum | Standard deviation |
|---|---:|---:|---:|---:|---:|
| Sleep hours | {stat('sleep_hours','mean'):.2f} | {stat('sleep_hours','50%'):.2f} | {stat('sleep_hours','min'):.2f} | {stat('sleep_hours','max'):.2f} | {stat('sleep_hours','std'):.2f} |
| Sleep quality | {stat('sleep_quality','mean'):.2f} | {stat('sleep_quality','50%'):.2f} | {stat('sleep_quality','min'):.2f} | {stat('sleep_quality','max'):.2f} | {stat('sleep_quality','std'):.2f} |
| Resting heart rate | {stat('resting_heart_rate','mean'):.2f} | {stat('resting_heart_rate','50%'):.2f} | {stat('resting_heart_rate','min'):.2f} | {stat('resting_heart_rate','max'):.2f} | {stat('resting_heart_rate','std'):.2f} |
| Exercise minutes | {stat('exercise_minutes','mean'):.2f} | {stat('exercise_minutes','50%'):.2f} | {stat('exercise_minutes','min'):.2f} | {stat('exercise_minutes','max'):.2f} | {stat('exercise_minutes','std'):.2f} |
| Fatigue score | {stat('fatigue_score','mean'):.2f} | {stat('fatigue_score','50%'):.2f} | {stat('fatigue_score','min'):.2f} | {stat('fatigue_score','max'):.2f} | {stat('fatigue_score','std'):.2f} |
| Stress score | {stat('stress_score','mean'):.2f} | {stat('stress_score','50%'):.2f} | {stat('stress_score','min'):.2f} | {stat('stress_score','max'):.2f} | {stat('stress_score','std'):.2f} |
| Reaction time (ms) | {stat('reaction_time_ms','mean'):.2f} | {stat('reaction_time_ms','50%'):.2f} | {stat('reaction_time_ms','min'):.2f} | {stat('reaction_time_ms','max'):.2f} | {stat('reaction_time_ms','std'):.2f} |
| Workload hours | {stat('workload_hours','mean'):.2f} | {stat('workload_hours','50%'):.2f} | {stat('workload_hours','min'):.2f} | {stat('workload_hours','max'):.2f} | {stat('workload_hours','std'):.2f} |

These are observed values in this dataset, not medical reference ranges. Unusually low or high values should be checked and kept for review rather than automatically deleted, because they may be simulated events.

## 4. Personal differences

{personal}

The project calculates a separate baseline for each crew member using mission days 1–14. Later measurements are compared with that crew member's baseline. This is more informative than applying one fixed average to all crew members. The first 14 days are only a baseline choice for this assignment, not a validated clinical baseline.

## 5. Time-series observations

The four single-crew charts show sleep, fatigue, workload, and reaction time across mission days for Crew-01. Four additional charts show daily averages across all crew members for fatigue, reaction time, sleep, and workload. The observations below compare six 30-day periods; they describe this dataset and should not be treated as medical conclusions.

{trend_observations}

The dataset-wide observed ranges include sleep from {stat('sleep_hours','min'):.1f} to {stat('sleep_hours','max'):.1f} hours, fatigue from {stat('fatigue_score','min'):.1f} to {stat('fatigue_score','max'):.1f}, and reaction time from {stat('reaction_time_ms','min'):.0f} to {stat('reaction_time_ms','max'):.0f} ms. Higher reaction time means slower performance, as stated in the assignment guide. Daily averages can hide individual changes, so review the single-crew plots alongside group averages.

## 6. Relationships between variables

{correlations}

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
"""
    (DOCS_DIR / "DATA_ANALYSIS.md").write_text(lines, encoding="utf-8")


def run_analysis():
    ensure_directories()
    data = load_data()
    print("=" * 72)
    print("ASTROGUARD EXPLORATORY ANALYSIS")
    print("=" * 72)
    print(f"Dataset: {DATA_PATH.relative_to(ROOT)}")
    print(f"Shape: {data.shape[0]} rows x {data.shape[1]} columns")
    print(f"Crew members: {data['crew_id'].nunique()}")
    print(f"Mission days: {data['mission_day'].min()} to {data['mission_day'].max()}")
    print(f"Duplicate rows: {data.duplicated().sum()}")
    print("\nMissing values by column:")
    print(data.isna().sum().to_string())
    print("\nNumerical summary:")
    print(data[NUMERIC_COLUMNS].describe().round(2).to_string())
    results = build_results(data)
    write_report(results)
    print("\nKey correlations:")
    print(results["key_corr"].to_string(index=False))
    print(f"\nCharts saved: {len(list(CHART_DIR.glob('*.png')))} in {CHART_DIR.relative_to(ROOT)}")
    print(f"Result tables saved: {len(list(RESULT_DIR.glob('*.csv')))} in {RESULT_DIR.relative_to(ROOT)}")
    print(f"Report saved: {(DOCS_DIR / 'DATA_ANALYSIS.md').relative_to(ROOT)}")
    return results


if __name__ == "__main__":
    run_analysis()
