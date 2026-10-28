"""
Social Media Impact on Life — Streamlit dashboard

Uses only Streamlit plus pandas/numpy (both are installed with Streamlit).
Run with:  streamlit run main.py

Each section is labeled with the Streamlit feature it shows (look for "FEATURE:").
"""

import time

import numpy as np
import pandas as pd
import streamlit as st

DATA_PATH = "./dataset/social_media_impact_on_life.csv"

# Blue palette, used for the built-in charts
BLUE_DARK = "#0B3C8C"
BLUE = "#1E6FD9"
BLUE_LIGHT = "#6FA8F5"
BLUE_PALE = "#B9D4FA"
BLUES = [BLUE_DARK, BLUE, BLUE_LIGHT, BLUE_PALE, "#3F8EF0", "#0F5BB5", "#8DBBF7"]

# FEATURE: st.set_page_config must be the first Streamlit call on the page
st.set_page_config(
    page_title="Social Media Impact Dashboard",
    page_icon="📱",
    layout="wide",
    initial_sidebar_state="expanded",
)

# FEATURE: st.markdown with unsafe_allow_html lets you add your own CSS.
# The theme colors live in .streamlit/config.toml; this adds the finishing touches.
st.markdown(
    f"""
    <style>
    .hero {{
        background: linear-gradient(120deg, {BLUE_DARK} 0%, {BLUE} 60%, {BLUE_LIGHT} 100%);
        padding: 1.6rem 2rem; border-radius: 16px; color: white; margin-bottom: 1rem;
    }}
    .hero h1 {{ color: white; margin: 0; font-size: 2rem; }}
    .hero p  {{ color: #E3EEFB; margin: .3rem 0 0 0; }}
    div[data-testid="stMetric"] {{
        background: white; border: 1px solid {BLUE_PALE}; border-left: 6px solid {BLUE};
        border-radius: 12px; padding: .8rem 1rem;
    }}
    section[data-testid="stSidebar"] {{ border-right: 1px solid {BLUE_PALE}; }}
    </style>
    """,
    unsafe_allow_html=True,
)


# --------------------------------------------------------------------------- #
# Data loading
# --------------------------------------------------------------------------- #

# FEATURE: st.cache_data runs the function once and reuses the result on every
# rerun (Streamlit re-runs the whole script after each widget interaction).
@st.cache_data(show_spinner="Loading dataset…")
def load_data(path: str) -> pd.DataFrame:
    df = pd.read_csv(path)
    df["Total_Weekly_Hours"] = df["Daily_Usage_Hours"] * 7 + df["Weekend_Extra_Hours"] * 2
    df["Usage_Band"] = pd.cut(
        df["Daily_Usage_Hours"],
        bins=[0, 2, 4, 6, 8, 24],
        labels=["0-2h", "2-4h", "4-6h", "6-8h", "8h+"],
    ).astype(str)
    return df


df_all = load_data(DATA_PATH)

# FEATURE: st.session_state keeps values between reruns
if "visits" not in st.session_state:
    st.session_state.visits = 0
    st.session_state.notes = []
st.session_state.visits += 1


# --------------------------------------------------------------------------- #
# Sidebar filters
# --------------------------------------------------------------------------- #

with st.sidebar:
    st.title("📱 Filters")
    st.caption("Every chart on the page follows these filters.")

    # FEATURE: multiselect
    platforms = st.multiselect(
        "Primary platform",
        options=sorted(df_all["Primary_Platform"].unique()),
        default=sorted(df_all["Primary_Platform"].unique()),
    )

    # FEATURE: pills (pick one or more by clicking)
    levels = st.pills(
        "Academic level",
        options=["High School", "Undergraduate", "Postgraduate"],
        selection_mode="multi",
        default=["High School", "Undergraduate", "Postgraduate"],
    )

    # FEATURE: range slider (pass a tuple as the value)
    age_min, age_max = int(df_all["Age"].min()), int(df_all["Age"].max())
    age_range = st.slider("Age", age_min, age_max, (age_min, age_max))

    # FEATURE: select_slider (slider over text values)
    max_usage = st.select_slider(
        "Max daily usage",
        options=[2, 4, 6, 8, 10, 12, 14],
        value=14,
        format_func=lambda h: f"{h} h",
    )

    # FEATURE: radio
    late_night = st.radio("Late-night usage", ["All", "Yes", "No"], horizontal=True)

    # FEATURE: toggle
    drop_missing = st.toggle("Hide rows with missing values", value=False)

    st.divider()

    # FEATURE: expander for content you don't always need
    with st.expander("ℹ️ About this dataset"):
        st.write(
            f"{len(df_all):,} students with their social media habits, sleep, "
            "stress, mental health and GPA."
        )
        st.caption("Source: dataset/social_media_impact_on_life.csv")

    st.caption(f"Page reruns this session: **{st.session_state.visits}**")


# Apply the filters
df = df_all[
    df_all["Primary_Platform"].isin(platforms)
    & df_all["Academic_Level"].isin(levels or [])
    & df_all["Age"].between(*age_range)
    & (df_all["Daily_Usage_Hours"] <= max_usage)
]
if late_night != "All":
    df = df[df["Late_Night_Usage"] == (late_night == "Yes")]
if drop_missing:
    df = df.dropna()


# --------------------------------------------------------------------------- #
# Header + KPIs
# --------------------------------------------------------------------------- #

st.markdown(
    """
    <div class="hero">
        <h1>Social Media Impact on Student Life</h1>
        <p>How daily usage relates to sleep, stress, mental health and grades</p>
    </div>
    """,
    unsafe_allow_html=True,
)

# FEATURE: st.stop ends the script early (useful when filters leave nothing)
if df.empty:
    st.warning("No students match these filters. Try widening them in the sidebar.", icon="⚠️")
    st.stop()

# FEATURE: st.columns + st.metric (the delta compares the filtered group to everyone)
k1, k2, k3, k4, k5 = st.columns(5)
k1.metric("Students", f"{len(df):,}", f"{len(df) / len(df_all):.0%} of total", delta_color="off")
k2.metric(
    "Avg daily usage",
    f"{df['Daily_Usage_Hours'].mean():.1f} h",
    f"{df['Daily_Usage_Hours'].mean() - df_all['Daily_Usage_Hours'].mean():+.1f} h vs all",
    delta_color="inverse",  # more usage shown in red
)
k3.metric(
    "Avg sleep",
    f"{df['Sleep_Duration_Hours'].mean():.1f} h",
    f"{df['Sleep_Duration_Hours'].mean() - df_all['Sleep_Duration_Hours'].mean():+.1f} h vs all",
)
k4.metric(
    "Mental health index",
    f"{df['Mental_Health_Index'].mean():.1f}",
    f"{df['Mental_Health_Index'].mean() - df_all['Mental_Health_Index'].mean():+.1f} vs all",
)
k5.metric(
    "Avg GPA",
    f"{df['Academic_Performance_GPA'].mean():.2f}",
    f"{df['Academic_Performance_GPA'].mean() - df_all['Academic_Performance_GPA'].mean():+.2f} vs all",
)

st.write("")

# --------------------------------------------------------------------------- #
# Tabs
# --------------------------------------------------------------------------- #

# FEATURE: st.tabs splits the page into sections
tab_overview, tab_explore, tab_data, tab_whatif, tab_widgets = st.tabs(
    ["📊 Overview", "🔍 Explore", "🗂️ Data", "🧪 What-if", "🧰 More widgets"]
)

# ----------------------------- Overview tab -------------------------------- #
with tab_overview:
    left, right = st.columns(2)

    # FEATURE: st.container(border=True) draws a card around its content
    with left.container(border=True):
        st.subheader("Students per platform")
        counts = df["Primary_Platform"].value_counts().sort_values()
        # FEATURE: st.bar_chart (horizontal)
        st.bar_chart(counts, horizontal=True, color=BLUE, x_label="Students", y_label="")

    with right.container(border=True):
        st.subheader("Overall impact by academic level")
        impact = pd.crosstab(df["Academic_Level"], df["Overall_Impact"])
        # FEATURE: stacked bar chart, one color per column
        st.bar_chart(
            impact,
            color=[BLUE, BLUE_PALE, BLUE_DARK][: len(impact.columns)],
            stack=True,
            y_label="Students",
        )

    with st.container(border=True):
        st.subheader("Average wellbeing by daily usage")
        st.caption("As daily screen time goes up, how do sleep and mental health change?")
        by_band = (
            df.groupby("Usage_Band")[["Sleep_Duration_Hours", "Sleep_Quality_Score", "Perceived_Stress_Score"]]
            .mean()
            .reindex(["0-2h", "2-4h", "4-6h", "6-8h", "8h+"])
            .dropna(how="all")
        )
        # FEATURE: st.line_chart with several lines
        st.line_chart(by_band, color=[BLUE_DARK, BLUE, BLUE_LIGHT], x_label="Daily usage", y_label="Average")

    c1, c2 = st.columns([2, 1])
    with c1.container(border=True):
        st.subheader("Mental health index by usage band")
        mh = (
            df.groupby("Usage_Band")["Mental_Health_Index"]
            .mean()
            .reindex(["0-2h", "2-4h", "4-6h", "6-8h", "8h+"])
            .dropna()
        )
        # FEATURE: st.area_chart
        st.area_chart(mh, color=BLUE, x_label="Daily usage", y_label="Mental health index")

    with c2.container(border=True):
        st.subheader("Device type")
        dev = df["Device_Type"].value_counts(normalize=True)
        # FEATURE: st.progress used as a simple percentage bar
        for name, share in dev.items():
            st.write(f"**{name}** — {share:.0%}")
            st.progress(float(share))

# ------------------------------ Explore tab -------------------------------- #
with tab_explore:
    numeric_cols = [
        "Daily_Usage_Hours", "Weekend_Extra_Hours", "Total_Weekly_Hours", "Sleep_Duration_Hours",
        "Sleep_Quality_Score", "Perceived_Stress_Score", "Mental_Health_Index",
        "Academic_Performance_GPA", "Age",
    ]
    category_cols = [
        "Primary_Platform", "Academic_Level", "Gender", "Device_Type",
        "Social_Comparison_Frequency", "Overall_Impact", "Late_Night_Usage",
    ]

    s1, s2, s3 = st.columns(3)
    # FEATURE: selectbox
    x_col = s1.selectbox("X axis", numeric_cols, index=0)
    y_col = s2.selectbox("Y axis", numeric_cols, index=6)
    color_col = s3.selectbox("Color by", [None] + category_cols, index=2)

    with st.container(border=True):
        st.subheader(f"{y_col} vs {x_col}")
        plot_df = df.dropna(subset=[x_col, y_col])
        if color_col:
            plot_df = plot_df.assign(**{color_col: plot_df[color_col].astype(str)})
        # FEATURE: st.scatter_chart, optionally colored by a column
        st.scatter_chart(plot_df, x=x_col, y=y_col, color=color_col or BLUE, height=420)

        corr = plot_df[x_col].corr(plot_df[y_col])
        strength = "strong" if abs(corr) > 0.5 else "moderate" if abs(corr) > 0.3 else "weak"
        # FEATURE: st.info / st.success / st.warning call-outs
        msg = f"Correlation between **{x_col}** and **{y_col}**: **{corr:.2f}** ({strength})"
        (st.success if abs(corr) > 0.3 else st.info)(msg)

    a, b = st.columns(2)
    with a.container(border=True):
        st.subheader("Distribution")
        hist_col = st.selectbox("Column", numeric_cols, index=6, key="hist_col")
        # FEATURE: number_input
        bins = st.number_input("Number of bins", min_value=5, max_value=40, value=15, step=1)
        counts, edges = np.histogram(df[hist_col].dropna(), bins=int(bins))
        hist = pd.DataFrame({"Students": counts}, index=[f"{e:.1f}" for e in edges[:-1]])
        st.bar_chart(hist, color=BLUE, x_label=hist_col)

    with b.container(border=True):
        st.subheader("Correlation matrix")
        st.caption("Darker blue = stronger positive relationship")
        corr_m = df[numeric_cols].corr().round(2)
        # FEATURE: st.dataframe with a pandas Styler (background gradient without matplotlib)
        st.dataframe(
            corr_m.style.format("{:.2f}").map(
                lambda v: f"background-color: rgba(30,111,217,{abs(v):.2f}); "
                f"color: {'white' if abs(v) > 0.5 else '#0B2545'}"
            ),
            height=360,
        )

    with st.container(border=True):
        st.subheader("Averages by group")
        group_by = st.radio("Group by", category_cols, horizontal=True, key="group_by")
        metrics = st.multiselect(
            "Metrics",
            numeric_cols,
            default=["Daily_Usage_Hours", "Sleep_Duration_Hours", "Academic_Performance_GPA"],
        )
        if metrics:
            grouped = df.groupby(df[group_by].astype(str))[metrics].mean()
            st.bar_chart(grouped, color=BLUES[: len(metrics)], stack=False)
        else:
            st.info("Pick at least one metric.")

# -------------------------------- Data tab --------------------------------- #
with tab_data:
    # FEATURE: text_input used as a search box
    search = st.text_input("🔎 Search Student ID", placeholder="e.g. STU_2024010")
    table = df[df["Student_ID"].str.contains(search, case=False)] if search else df

    st.caption(f"Showing {len(table):,} rows — click a row to see that student's profile.")

    # FEATURE: st.dataframe with column_config (progress bars, number formats, checkboxes)
    # and on_select so clicking a row returns the selection.
    event = st.dataframe(
        table,
        hide_index=True,
        height=380,
        on_select="rerun",
        selection_mode="single-row",
        column_config={
            "Student_ID": st.column_config.TextColumn("Student", pinned=True),
            "Daily_Usage_Hours": st.column_config.ProgressColumn(
                "Daily usage", format="%.1f h", min_value=0, max_value=14
            ),
            "Mental_Health_Index": st.column_config.ProgressColumn(
                "Mental health", format="%d", min_value=0, max_value=100
            ),
            "Academic_Performance_GPA": st.column_config.NumberColumn("GPA", format="%.2f"),
            "Late_Night_Usage": st.column_config.CheckboxColumn("Late night"),
            "Sleep_Quality_Score": st.column_config.NumberColumn("Sleep quality", format="%d ⭐"),
        },
    )

    # FEATURE: st.dialog opens a pop-up window
    @st.dialog("Student profile")
    def show_student(row: pd.Series):
        st.subheader(row["Student_ID"])
        st.write(f"{row['Age']} y/o · {row['Gender']} · {row['Academic_Level']}")
        m1, m2, m3 = st.columns(3)
        m1.metric("Daily usage", f"{row['Daily_Usage_Hours']} h")
        m2.metric("Sleep", f"{row['Sleep_Duration_Hours']} h")
        m3.metric("GPA", "–" if pd.isna(row["Academic_Performance_GPA"]) else row["Academic_Performance_GPA"])
        # FEATURE: st.json shows dicts nicely
        st.json(row.drop("Student_ID").astype(str).to_dict(), expanded=False)

    selected = event.selection.rows
    if selected:
        if st.button("Open profile of selected student", type="primary"):
            show_student(table.iloc[selected[0]])

    st.divider()
    d1, d2 = st.columns(2)
    with d1:
        st.subheader("Summary statistics")
        # FEATURE: st.table renders a static table
        st.table(df[numeric_cols].describe().T[["mean", "std", "min", "max"]].round(2))
    with d2:
        st.subheader("Missing values")
        missing = df.isna().sum()
        missing = missing[missing > 0]
        if missing.empty:
            st.success("No missing values in the filtered data 🎉")
        else:
            st.bar_chart(missing, color=BLUE_LIGHT, horizontal=True)

        # FEATURE: download_button
        st.download_button(
            "⬇️ Download filtered data (CSV)",
            data=df.to_csv(index=False).encode("utf-8"),
            file_name="filtered_social_media_data.csv",
            mime="text/csv",
            width="stretch",
        )

# ------------------------------ What-if tab -------------------------------- #
with tab_whatif:
    st.subheader("Compare yourself with similar students")
    st.caption("Fill in the form and press Submit. Inside a form, nothing reruns until you submit.")

    # FEATURE: st.form groups widgets and submits them together
    with st.form("whatif"):
        f1, f2, f3 = st.columns(3)
        my_usage = f1.slider("My daily usage (h)", 0.0, 14.0, 5.0, 0.5)
        my_sleep = f2.slider("My sleep (h)", 3.0, 10.5, 7.0, 0.5)
        my_platform = f3.selectbox("My main platform", sorted(df_all["Primary_Platform"].unique()))
        submitted = st.form_submit_button("Submit", type="primary")

    if submitted:
        # FEATURE: st.status shows progress for multi-step work
        with st.status("Finding similar students…", expanded=True) as status:
            st.write("Matching usage and sleep within ±1 hour…")
            time.sleep(0.4)
            peers = df_all[
                df_all["Daily_Usage_Hours"].between(my_usage - 1, my_usage + 1)
                & df_all["Sleep_Duration_Hours"].between(my_sleep - 1, my_sleep + 1)
            ]
            st.write(f"Found {len(peers)} peers.")
            time.sleep(0.4)
            status.update(label="Done!", state="complete", expanded=False)

        if peers.empty:
            st.error("No similar students found — try different values.")
        else:
            p1, p2, p3, p4 = st.columns(4)
            p1.metric("Peers found", len(peers))
            p2.metric("Their avg GPA", f"{peers['Academic_Performance_GPA'].mean():.2f}")
            p3.metric("Their avg stress", f"{peers['Perceived_Stress_Score'].mean():.1f}")
            p4.metric("Their mental health", f"{peers['Mental_Health_Index'].mean():.0f}")

            on_platform = peers[peers["Primary_Platform"] == my_platform]
            st.write(f"Of these, **{len(on_platform)}** mainly use **{my_platform}**.")
            st.bar_chart(peers["Overall_Impact"].value_counts(), color=BLUE)
            # FEATURE: st.toast shows a small notification in the corner
            st.toast("Comparison ready!", icon="✅")

# --------------------------- More widgets tab ------------------------------ #
with tab_widgets:
    st.subheader("Other Streamlit features")

    w1, w2 = st.columns(2)

    with w1.container(border=True):
        st.markdown("#### Notes (session state)")
        st.caption("Notes are kept in st.session_state, so they survive reruns until you refresh the page.")
        # FEATURE: text_area + button with on_click callback
        st.text_area("Write a note", key="note_input", height=80)

        def add_note():
            if st.session_state.note_input.strip():
                st.session_state.notes.append(st.session_state.note_input.strip())
                st.session_state.note_input = ""

        st.button("Add note", on_click=add_note)
        for i, note in enumerate(st.session_state.notes, 1):
            st.write(f"{i}. {note}")

    with w2.container(border=True):
        st.markdown("#### Random sample (fragment)")
        st.caption("Inside an st.fragment, the button reruns only this card, not the whole page.")

        # FEATURE: st.fragment reruns only part of the page
        @st.fragment
        def random_sample():
            if st.button("🎲 New sample"):
                pass  # clicking reruns the fragment, which draws a new sample
            st.dataframe(
                df.sample(min(5, len(df)))[["Student_ID", "Primary_Platform", "Daily_Usage_Hours", "Overall_Impact"]],
                hide_index=True,
            )

        random_sample()

    w3, w4 = st.columns(2)
    with w3.container(border=True):
        st.markdown("#### Editable table")
        # FEATURE: st.data_editor (an editable table)
        target = st.data_editor(
            pd.DataFrame(
                {
                    "Goal": ["Daily usage under 3h", "Sleep at least 8h", "No phone after 11pm"],
                    "Done": [False, False, False],
                    "Priority": ["High", "Medium", "Low"],
                }
            ),
            column_config={
                "Priority": st.column_config.SelectboxColumn(options=["High", "Medium", "Low"]),
            },
            hide_index=True,
            num_rows="dynamic",
            width="stretch",
        )
        done = int(target["Done"].sum())
        st.progress(done / max(len(target), 1), text=f"{done}/{len(target)} goals done")

    with w4.container(border=True):
        st.markdown("#### Popover, segmented control & feedback")
        # FEATURE: segmented_control
        unit = st.segmented_control("Show usage in", ["Hours/day", "Hours/week"], default="Hours/day")
        avg = df["Daily_Usage_Hours"].mean()
        st.write(f"Average: **{avg:.1f} h/day**" if unit != "Hours/week" else f"Average: **{df['Total_Weekly_Hours'].mean():.1f} h/week**")

        # FEATURE: popover (a small pop-up attached to a button)
        with st.popover("⚙️ How is weekly usage calculated?"):
            # FEATURE: st.latex for formulas
            st.latex(r"\text{Weekly} = 7 \times \text{Daily} + 2 \times \text{WeekendExtra}")

        # FEATURE: st.feedback (thumbs / stars)
        rating = st.feedback("stars")
        if rating is not None:
            st.write(f"Thanks for rating the dashboard {rating + 1} ⭐")
            if rating == 4:
                st.balloons()  # FEATURE: st.balloons

    with st.expander("📄 Code used to filter the data"):
        # FEATURE: st.code shows syntax-highlighted code
        st.code(
            """df = df_all[
    df_all["Primary_Platform"].isin(platforms)
    & df_all["Academic_Level"].isin(levels)
    & df_all["Age"].between(*age_range)
    & (df_all["Daily_Usage_Hours"] <= max_usage)
]""",
            language="python",
        )

st.divider()
st.caption("Built with Streamlit · only built-in charts and widgets · theme in .streamlit/config.toml")
