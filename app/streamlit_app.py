from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "assets" / "ml_results" / "alert_results.csv"
HEALTH = ROOT / "data" / "processed" / "astronaut_health.csv"
LOG = ROOT / "data" / "processed" / "data_quality_log.csv"

STATE_ORDER = ["Stable", "Watch", "Review Required", "Warm-up"]
STATE_COLORS = {
    "Stable": "#2e7d32",
    "Watch": "#f9a825",
    "Review Required": "#c62828",
    "Warm-up": "#1565c0",
}
TABLE_STYLES = {
    "Stable": "background-color: #d1e7dd; color: #0f5132",
    "Watch": "background-color: #fff3cd; color: #664d03",
    "Review Required": "background-color: #f8d7da; color: #842029",
    "Warm-up": "background-color: #cfe2ff; color: #084298",
}


@st.cache_data
def load_csv(path):
    return pd.read_csv(path)


def clean_list(value):
    if pd.isna(value) or str(value).strip() == "":
        return "None"
    return str(value).replace("_", " ")


def style_state(value):
    return TABLE_STYLES.get(value, "")


st.set_page_config(page_title="AstroGuard", layout="wide")

st.title("AstroGuard")
st.caption("Astronaut health and performance monitoring prototype")

st.info(
    "This dashboard uses simulated data. AstroGuard is a non-diagnostic "
    "educational prototype. It is not an official NASA system, it is not "
    "clinically validated, and it is not a medical tool."
)

if not RESULTS.exists():
    st.error(
        "Could not find alert_results.csv. "
        "Run this first: python -m src.run_pipeline"
    )
    st.stop()

if not HEALTH.exists():
    st.error("Could not find astronaut_health.csv in data/processed.")
    st.stop()

results = load_csv(RESULTS)
health = load_csv(HEALTH)

# ---------------------------------------------------------------- Overview
st.subheader("Mission overview")

total_crew = results["crew_id"].nunique()
total_days = int(results["mission_day"].max())
counts = results["alert_state"].value_counts()
missing_data_days = int(results["data_quality_warning"].notna().sum())

top = st.columns(2)
top[0].metric("Total crew", total_crew)
top[1].metric("Total mission days", total_days)

states = st.columns(5)
states[0].metric("Stable", int(counts.get("Stable", 0)))
states[1].metric("Watch", int(counts.get("Watch", 0)))
states[2].metric("Review Required", int(counts.get("Review Required", 0)))
states[3].metric("Warm-up", int(counts.get("Warm-up", 0)))
states[4].metric("Days with missing data", missing_data_days)

st.caption(
    "Each count is one astronaut on one day. "
    "Warm-up means the first days of the mission, "
    "when the system is still learning each person's normal."
)

crew_compare = (
    pd.crosstab(results["crew_id"], results["alert_state"])
    .reindex(columns=["Watch", "Review Required"], fill_value=0)
    .reset_index()
    .melt(id_vars="crew_id", var_name="Alert state", value_name="Days")
)
fig_compare = px.bar(
    crew_compare,
    x="crew_id",
    y="Days",
    color="Alert state",
    color_discrete_map=STATE_COLORS,
    labels={"crew_id": "Crew member"},
    title="Watch and Review Required days per crew member (whole mission)",
)
fig_compare.update_layout(height=320, margin=dict(l=10, r=10, t=50, b=10))
st.plotly_chart(fig_compare)

# ----------------------------------------------------------------- Sidebar
st.sidebar.header("Choose what to see")

crew_ids = sorted(results["crew_id"].dropna().unique())
selected_crew = st.sidebar.selectbox("Crew member", crew_ids)

first_day = int(results["mission_day"].min())
last_day = int(results["mission_day"].max())
day_range = st.sidebar.slider(
    "Mission days", first_day, last_day, (first_day, last_day)
)

crew = results[results["crew_id"] == selected_crew]
crew = crew[crew["mission_day"].between(day_range[0], day_range[1])]

crew_health = health[health["crew_id"] == selected_crew]
crew_health = crew_health[
    crew_health["mission_day"].between(day_range[0], day_range[1])
]

st.header(f"{selected_crew}: days {day_range[0]} to {day_range[1]}")

state_counts = pd.DataFrame(
    {
        "Alert state": STATE_ORDER,
        "Days": [int((crew["alert_state"] == s).sum()) for s in STATE_ORDER],
    }
)
fig_states = px.bar(
    state_counts,
    x="Alert state",
    y="Days",
    color="Alert state",
    color_discrete_map=STATE_COLORS,
    title="Days in each alert state",
)
fig_states.update_layout(height=300, margin=dict(l=10, r=10, t=50, b=10))
fig_states.update_layout(showlegend=False)
st.plotly_chart(fig_states)

tab_trends, tab_alerts, tab_quality, tab_notes = st.tabs(
    ["Trends", "Alerts", "Data quality", "Method notes"]
)

# ------------------------------------------------------------------- Trends
with tab_trends:
    st.subheader("Health trends")

    mark_alerts = st.checkbox(
        "Mark Watch and Review Required days on the charts", value=True
    )

    trend_data = crew_health.merge(
        crew[["mission_day", "alert_state"]], on="mission_day", how="left"
    )

    charts = [
        ("sleep_hours", "Sleep (hours)"),
        ("fatigue_score", "Fatigue score"),
        ("exercise_minutes", "Exercise (minutes)"),
        ("resting_heart_rate", "Resting heart rate (bpm)"),
        ("reaction_time_ms", "Reaction time (ms)"),
        ("workload_hours", "Workload (hours)"),
        ("stress_score", "Stress score"),
    ]

    chart_columns = st.columns(2)
    for i, (column, label) in enumerate(charts):
        fig = px.line(
            trend_data,
            x="mission_day",
            y=column,
            title=label,
            labels={"mission_day": "Mission day", column: label},
        )
        if mark_alerts:
            for state in ["Watch", "Review Required"]:
                flagged = trend_data[
                    (trend_data["alert_state"] == state)
                    & trend_data[column].notna()
                ]
                if not flagged.empty:
                    fig.add_trace(
                        go.Scatter(
                            x=flagged["mission_day"],
                            y=flagged[column],
                            mode="markers",
                            name=state,
                            marker=dict(
                                color=STATE_COLORS[state],
                                size=9,
                                line=dict(width=1, color="white"),
                            ),
                            hovertemplate=(
                                f"Day %{{x}}<br>{state}<br>{label}: %{{y}}"
                                "<extra></extra>"
                            ),
                        )
                    )
        fig.update_layout(
            height=300, margin=dict(l=10, r=10, t=50, b=10), showlegend=False
        )
        chart_columns[i % 2].plotly_chart(fig)

    st.caption(
        "Each line shows one measurement over the mission. A gap in a line "
        "means that day's measurement is missing. Yellow dots are Watch days "
        "and red dots are Review Required days."
    )

# ------------------------------------------------------------------- Alerts
with tab_alerts:
    st.subheader("Alert table")

    only_alerts = st.checkbox(
        "Show only Watch and Review Required days", value=True
    )

    table = crew.sort_values("mission_day").copy()
    if only_alerts:
        table = table[table["alert_state"].isin(["Watch", "Review Required"])]

    table_view = table[
        [
            "mission_day",
            "alert_state",
            "alert_score",
            "confidence",
            "operational_alert",
        ]
    ].copy()
    table_view["operational_alert"] = table_view["operational_alert"].map(
        {True: "Yes", False: "No"}
    )
    table_view = table_view.rename(
        columns={
            "mission_day": "Mission day",
            "alert_state": "Alert state",
            "alert_score": "Alert score",
            "confidence": "Confidence",
            "operational_alert": "Operational alert",
        }
    )

    if table_view.empty:
        st.info("No days match this filter for the selected crew member and days.")
    else:
        st.dataframe(
            table_view.style.map(style_state, subset=["Alert state"]),
            hide_index=True,
        )

    st.caption(
        "Alert score is a simple count of warning signs. A higher score means "
        "more signs. Confidence is lower when measurements are missing or the "
        "mission is still in its first days."
    )

    st.subheader("Alert detail")

    day_options = table["mission_day"].tolist()
    if not day_options:
        day_options = crew["mission_day"].sort_values().tolist()

    if not day_options:
        st.info("No days to show for this selection.")
    else:
        selected_day = st.selectbox("Pick a mission day", day_options)
        row = crew[crew["mission_day"] == selected_day].iloc[0]

        state = row["alert_state"]
        message = f"{selected_crew}, day {selected_day}: {state}"
        if state == "Review Required":
            st.error(message)
        elif state == "Watch":
            st.warning(message)
        elif state == "Stable":
            st.success(message)
        else:
            st.info(message)

        detail = st.columns(3)
        detail[0].metric("Alert score", int(row["alert_score"]))
        detail[1].metric("Confidence", row["confidence"])
        detail[2].metric(
            "Operational alert", "Yes" if row["operational_alert"] else "No"
        )

        st.markdown("**Measurements that were unusual on this day**")
        st.write(clean_list(row["point_anomaly_features"]))

        st.markdown("**Measurements that stayed unusual for several days**")
        st.write(clean_list(row["persistent_anomaly_features"]))

        st.markdown("**Combined patterns**")
        patterns = {
            "sleep_fatigue_pattern": "Sleep and fatigue",
            "fatigue_reaction_pattern": "Fatigue and reaction time",
            "workload_stress_pattern": "Workload and stress",
            "workload_exercise_pattern": "Workload and exercise",
        }
        found = [name for column, name in patterns.items() if bool(row[column])]
        st.write(", ".join(found) if found else "None")

        st.markdown("**Explanation**")
        st.write(row["alert_explanation"])

        st.markdown("**Recommendation**")
        st.write(row["recommendation"])

# ------------------------------------------------------------- Data quality
with tab_quality:
    st.subheader("Data quality")

    feature_labels = {
        "sleep_hours": "Sleep hours",
        "sleep_quality": "Sleep quality",
        "resting_heart_rate": "Resting heart rate",
        "exercise_minutes": "Exercise minutes",
        "fatigue_score": "Fatigue score",
        "stress_score": "Stress score",
        "reaction_time_ms": "Reaction time",
        "workload_hours": "Workload hours",
    }

    days_shown = len(crew)
    days_enough_baseline = int(crew["baseline_is_sufficient"].sum())
    missing_rows = crew[crew["missing_feature_count"] > 0].sort_values(
        "mission_day"
    )

    quality = st.columns(3)
    quality[0].metric("Days shown", days_shown)
    quality[1].metric("Days with missing data", len(missing_rows))
    quality[2].metric(
        "Days with enough baseline data",
        f"{days_enough_baseline} of {days_shown}",
    )

    missing_by_feature = pd.DataFrame(
        {
            "Measurement": list(feature_labels.values()),
            "Missing days": [
                int(crew[f"{column}_missing"].sum()) for column in feature_labels
            ],
        }
    )
    st.markdown("**Missing values per measurement**")
    st.dataframe(missing_by_feature, hide_index=True)

    if missing_rows.empty:
        st.success(
            "No missing measurements for this crew member in the selected days."
        )
    else:
        st.warning(
            f"{len(missing_rows)} day(s) have a missing measurement. "
            "On those days the alert confidence is lower."
        )

        def missing_names(row):
            names = [
                label
                for column, label in feature_labels.items()
                if bool(row[f"{column}_missing"])
            ]
            return ", ".join(names)

        warning_view = pd.DataFrame(
            {
                "Mission day": missing_rows["mission_day"],
                "Missing measurement": missing_rows.apply(missing_names, axis=1),
                "Warning": missing_rows["data_quality_warning"],
                "Confidence": missing_rows["confidence"],
            }
        )
        st.dataframe(warning_view, hide_index=True)

    if LOG.exists():
        quality_log = load_csv(LOG)
        crew_log = quality_log[
            (quality_log["crew_id"] == selected_crew)
            & quality_log["mission_day"].between(day_range[0], day_range[1])
        ]
        if not crew_log.empty:
            st.markdown("**What was done to the bad values**")
            st.dataframe(
                crew_log[["mission_day", "column", "issue", "action"]].rename(
                    columns={
                        "mission_day": "Mission day",
                        "column": "Measurement",
                        "issue": "Problem found",
                        "action": "What was done",
                    }
                ),
                hide_index=True,
            )

    st.caption(
        "Baseline means the astronaut's own normal range, learned from their "
        "early days. Enough baseline data means the model had enough days to "
        "learn it."
    )

# ------------------------------------------------------------- Method notes
with tab_notes:
    st.subheader("Method notes")

    with st.expander("How AstroGuard works"):
        st.markdown(
            """
- **Personal baseline:** each astronaut is compared with their own normal
  range, not with other people.
- **Warm-up:** the first 14 days of the mission are used to learn that normal
  range, so no operational alerts are raised in this period.
- **Unusual day:** a measurement is flagged when it is far from the
  astronaut's own normal.
- **Persistent change:** a measurement is flagged as persistent when it stays
  unusual for several days in a row.
- **Combined patterns:** some measurements are checked in pairs, for example
  workload with stress, or sleep with fatigue.
- **Alert score and state:** the signs are added up into a score, and the
  score decides the state: Stable, Watch, or Review Required.
- **Missing data:** if a measurement is missing, it is left blank, a warning
  is shown, and the confidence of the alert is lowered.
"""
        )

    with st.expander("What these results do and don't mean"):
        st.markdown(
            """
- The data is **simulated**. No real astronaut is shown here.
- AstroGuard is **non-diagnostic**. An alert is a monitoring signal that asks
  a person to take a look. It is not a medical conclusion.
- The model was checked on a small simulated test set only. That is not
  clinical validation and not NASA validation.
- This is an educational hackathon prototype and not an official NASA system.
- This dashboard only displays the results of the ML pipeline. It does not
  change them, and it does not use the answer-key (ground truth) files.
"""
        )