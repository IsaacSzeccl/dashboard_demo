import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
 
# ==========================================
# 1. PAGE CONFIGURATION
# ==========================================
st.set_page_config(page_title="Chatbot Performance Dashboard Demo", layout="wide")
 
# Side bar
st.markdown(
    """
    <style>
    section[data-testid="stSidebar"] {
        min-width: 200px !important;
        max-width: 400px !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)
 
with st.sidebar:
    st.markdown("### Menu")
    menu_selection = st.selectbox("", ["Dashboard"], label_visibility="collapsed")
 
# ==========================================
# 2. MOCK DATA GENERATION
# ==========================================
np.random.seed(42)
 
TODAY = datetime(2026, 7, 31)
ROLLING_WINDOW_DAYS = 30
# Use days=29 so that ROLLING_START through TODAY inclusive spans exactly 30 days
ROLLING_START = TODAY - timedelta(days=ROLLING_WINDOW_DAYS - 1)
 
# Generate 365 days of historical daily data ending at TODAY
end_date = TODAY
start_date = end_date - timedelta(days=365)
dates = pd.date_range(start=start_date, end=end_date)
 
daily_data = pd.DataFrame({
    "Date": dates,
    "Queries Responded": np.random.poisson(lam=1.2, size=len(dates)),
    "Active Users": np.clip(
        np.round(np.linspace(5, 9, len(dates)) + np.random.normal(loc=0, scale=0.4, size=len(dates))),
        1,
        None,
    ).astype(int),
    "New Users": np.clip(
        np.round(np.linspace(18, 22, len(dates)) + np.random.normal(loc=0, scale=0.8, size=len(dates))),
        1,
        None,
    ).astype(int),
    "AE Flags": np.random.poisson(lam=0.05, size=len(dates)),
    "CSAT Rating": np.random.uniform(low=3.8, high=4.9, size=len(dates))
})
 
# Rolling 30-day window for KPI computation
rolling_data = daily_data[daily_data["Date"] >= ROLLING_START].copy()
kpi_queries_responded = int(rolling_data["Queries Responded"].sum())
kpi_queries_resolved = int(round(kpi_queries_responded * 0.80)) # Sample data: we set at 80% of total queries first for demo purposes only.
kpi_active_users = int(round(rolling_data["Active Users"].mean()))
kpi_new_users = int(round(rolling_data["New Users"].mean()))
kpi_ae_flags = int(rolling_data["AE Flags"].sum())
kpi_avg_csat = round(rolling_data["CSAT Rating"].mean(), 2)
# CSAT respondents: approx 70 % of average daily active users responded to the survey
kpi_csat_respondents = max(1, round(kpi_active_users * 0.70))
 
# Previous 30-day window for delta computation
prev_start = ROLLING_START - timedelta(days=ROLLING_WINDOW_DAYS)
prev_data = daily_data[(daily_data["Date"] >= prev_start) & (daily_data["Date"] < ROLLING_START)].copy()
prev_queries_responded = int(prev_data["Queries Responded"].sum())
prev_queries_resolved = int(round(prev_queries_responded * 0.80))
prev_active_users = int(round(prev_data["Active Users"].mean()))
prev_new_users = int(round(prev_data["New Users"].mean()))
prev_ae_flags = int(prev_data["AE Flags"].sum())
 
def pct_delta(current, previous):
    if previous == 0:
        return "N/A"
    return f"{round((current - previous) / previous * 100):+d}%"
 
# Group data by week (starting Monday) for historical charts
weekly_data = daily_data.resample("W-MON", on="Date").agg({
    "Queries Responded": "sum",
    "Active Users": "mean",
    "New Users": "mean",
    "AE Flags": "sum",
    "CSAT Rating": "mean"
}).reset_index()
 
weekly_data["Active Users"] = weekly_data["Active Users"].round(1)
weekly_data["New Users"] = weekly_data["New Users"].round(1)
weekly_data["AE Flags"] = weekly_data["AE Flags"].round(1)
weekly_data["CSAT Rating"] = weekly_data["CSAT Rating"].round(2)
 
# Query category mock data (consistent with rolling 30-day totals)
# Ensure category totals sum to kpi_queries_responded
total_queries_assigned = kpi_queries_responded - kpi_ae_flags
 
# Allocate queries proportionally to categories (maintaining approximately 4:3:2:1 ratio)
category_values = {
    "General Enquiry": max(1, round(total_queries_assigned * 0.4)),
    "Saizen Product Enquiry": max(1, round(total_queries_assigned * 0.3)),
    "Device Enquiry": max(1, round(total_queries_assigned * 0.2)),
    "Forbidden Enquiries": max(1, round(total_queries_assigned * 0.1)),
}
 
# Adjust to ensure exact sum (excluding AE)
sum_allocated = sum(category_values.values())
if sum_allocated != total_queries_assigned:
    diff = total_queries_assigned - sum_allocated
    category_values["General Enquiry"] += diff
 
# Add AE category
category_values["AE"] = kpi_ae_flags
 
category_df = pd.DataFrame({
    "Category": list(category_values.keys()),
    "Total Queries": list(category_values.values()),
})
category_df = category_df.sort_values("Total Queries", ascending=False).reset_index(drop=True)
 
# AE patient records — dynamically generated to match kpi_ae_flags exactly
_AE_PHONE_POOL = [
    "852-9123-4567", "852-9876-5432", "852-6234-8901",
    "852-5512-3344", "852-9001-2222", "852-6688-9900",
    "852-5544-1122", "852-9321-0011", "852-6677-8899", "852-5500-4411",
]
_AE_CONTENT_POOL = [
    "I experienced severe redness and swelling at the injection site after my last dose. It has not subsided for 3 days.",
    "I felt dizzy and had shortness of breath approximately 2 hours after administering my weekly injection.",
    "There is a hard lump forming under my skin at the injection site and it is painful to touch.",
    "I developed a rash across my abdomen within hours of the injection. It is spreading and very itchy.",
    "My blood sugar levels have been unusually high since starting the injection. I am concerned about dosage.",
    "I experienced nausea and vomiting after the injection. This has happened twice in a row now.",
    "My injection site looks infected — there is yellow discharge and it feels warm.",
    "I had a severe headache and blurred vision about 30 minutes after administering the injection.",
    "I noticed unusual bruising at multiple injection sites over the past week.",
    "I experienced muscle weakness and fatigue that started the day after my last injection.",
]
 
if kpi_ae_flags == 0:
    ae_patient_data = pd.DataFrame(columns=["Patient Phone Number", "Query Date", "Query Content"])
else:
    # Collect one date entry per AE flag from the rolling window
    _ae_dates = []
    for _, _ae_row in rolling_data.iterrows():
        _ae_dates.extend([_ae_row["Date"]] * int(_ae_row["AE Flags"]))
    # Pad with random rolling-window dates if the sum differs (safety net)
    _ae_rng_pad = np.random.default_rng(seed=99)
    while len(_ae_dates) < kpi_ae_flags:
        _ae_dates.append(rolling_data["Date"].iloc[int(_ae_rng_pad.integers(0, len(rolling_data)))])
    _ae_dates = sorted(_ae_dates[:kpi_ae_flags])
 
    _ae_rng = np.random.default_rng(seed=42)
    _phone_idx = _ae_rng.integers(0, len(_AE_PHONE_POOL), size=kpi_ae_flags)
    _needs_replace = kpi_ae_flags > len(_AE_CONTENT_POOL)
    _content_idx = _ae_rng.choice(len(_AE_CONTENT_POOL), size=kpi_ae_flags, replace=_needs_replace)
 
    ae_patient_data = pd.DataFrame({
        "Patient Phone Number": [_AE_PHONE_POOL[i] for i in _phone_idx],
        "Query Date": [d.strftime("%Y-%m-%d") for d in _ae_dates],
        "Query Content": [_AE_CONTENT_POOL[i] for i in _content_idx],
    })
 
# ==========================================
# 3. GLOBAL STYLES
# ==========================================
st.markdown(
    """
    <style>
    :root {
        --kpi-bg-start: #eef7ff;
        --kpi-bg-end: #ffffff;
        --kpi-border: #0b6dbf;
        --kpi-shadow: rgba(12, 74, 110, 0.14);
        --section-bg: #f8fafc;
        --section-border: #e2e8f0;
    }
 
    div[data-testid="stMetric"] {
        background: linear-gradient(145deg, var(--kpi-bg-start), var(--kpi-bg-end));
        border: 1px solid #c8ddf1;
        border-left: 4px solid var(--kpi-border);
        border-radius: 12px;
        padding: 12px 14px;
        box-shadow: 0 6px 16px -10px var(--kpi-shadow);
        min-height: 118px;
    }
 
    div[data-testid="stMetricLabel"] p {
        font-weight: 600;
    }
 
    div[data-testid="stMetricValue"] {
        color: #0f172a;
        font-weight: 700;
    }
 
    .plain-metric div[data-testid="stMetric"] {
        background: transparent;
        border: 0;
        border-left: 0;
        border-radius: 0;
        padding: 0;
        box-shadow: none;
        min-height: 0;
    }
 
    .plain-metric div[data-testid="stMetricLabel"] p,
    .plain-metric div[data-testid="stMetricValue"] {
        font-weight: 600;
    }
 
    .section-shell {
        background: var(--section-bg);
        border: 1px solid var(--section-border);
        border-radius: 12px;
        padding: 8px 14px 2px 14px;
        margin-top: 2px;
        margin-bottom: 2px;
    }
 
    .cat-card {
        background: #ffffff;
        border: 1px solid #e6eaf2;
        border-radius: 16px;
        padding: 16px 18px 14px 18px;
        box-shadow: 0 8px 24px rgba(15, 23, 42, 0.06);
    }
    </style>
    """,
    unsafe_allow_html=True,
)
 
# AE Flags dialog (floating window)
@st.dialog(f"AE Flag Records — Past {ROLLING_WINDOW_DAYS} Days", width="large")
def show_ae_dialog():
    st.caption(f"Period: {ROLLING_START.strftime('%Y-%m-%d')} to {TODAY.strftime('%Y-%m-%d')}")
    if ae_patient_data.empty:
        st.info("No AE flags recorded in the past 30 days.")
    else:
        st.dataframe(ae_patient_data, use_container_width=True, hide_index=True)
 
# ==========================================
# 4. TITLE ROW WITH AE FLAGS BUTTON
# ==========================================
title_col, btn_col = st.columns([5, 1])
with title_col:
    st.title("Chatbot Performance Dashboard Demo")
with btn_col:
    st.markdown("<div style='margin-top:1.6rem'></div>", unsafe_allow_html=True)
    if st.button("Display all AE Flags", type="primary", use_container_width=True):
        show_ae_dialog()
 
# ==========================================
# LAYER 1: TOP KPIs (ROLLING 30-DAY WINDOW)
# ==========================================
st.markdown(
    f"### Key Performance Indicators  "
    f"<span style='font-size:0.8rem; color:#64748b; font-weight:400'>"
    f"Rolling 30-day window: {ROLLING_START.strftime('%b %d')} – {TODAY.strftime('%b %d, %Y')}"
    f"</span>",
    unsafe_allow_html=True,
)
 
kpi1, kpi2, kpi3, kpi4, kpi5 = st.columns(5)
 
with kpi1:
    st.metric(
        label="Total number of Queries",
        value=str(kpi_queries_responded),
        delta=pct_delta(kpi_queries_responded, prev_queries_responded),
        help="Total number of medication or dosage queries responded to by the chatbot in the past 30 days."
    )
with kpi2:
    st.metric(
        label="Queries Resolved",
        value=str(kpi_queries_resolved),
        delta=pct_delta(kpi_queries_resolved, prev_queries_resolved),
        help="The number of queries that the chatbot can answer by the knowledge base."
    )
with kpi3:
    st.metric(
        label="Active Users",
        value=str(kpi_active_users),
        delta=pct_delta(kpi_active_users, prev_active_users),
        help="Average daily unique patients who interacted with the chatbot in the past 30 days."
    )
with kpi4:
    st.metric(
        label="New Users",
        value=str(kpi_new_users),
        delta=pct_delta(kpi_new_users, prev_new_users),
        help="Total number of first-time patients onboarded to the digital health platform in the past 30 days."
    )
with kpi5:
    st.metric(
        label="AE Flags",
        value=str(kpi_ae_flags),
        delta=pct_delta(kpi_ae_flags, prev_ae_flags),
        delta_color="inverse",
        help="Total Adverse Events automatically flagged in the past 30 days based on compliance keyword triggers, forwarded for human safety review."
    )
 
# ==========================================
# LAYER 2: HISTORICAL TRENDS (moved above granular insights)
# ==========================================
st.markdown("### Historical Trends")
 
filter_col1, filter_col2 = st.columns(2)
with filter_col1:
    timeframe = st.selectbox(
        "Select Timeframe",
        options=["Past 1 Month", "Past 3 Months", "Past 6 Months", "All Time"],
        index=2
    )
with filter_col2:
    selected_metric = st.selectbox(
        "Select Metric to Display",
        options=["Active & New Users", "Total number of Queries", "AE Flags", "Average user rating"],
        index=1
    )
 
metric_to_columns = {
    "Active & New Users": ["Active Users", "New Users"],
    "Total number of Queries": ["Queries Responded"],
    "AE Flags": ["AE Flags"],
    "Average user rating": ["CSAT Rating"],
}
selected_metric_columns = metric_to_columns[selected_metric]
 
# Filter dataframe based on timeframe selection
if timeframe == "Past 1 Month":
    filtered_df = weekly_data[weekly_data["Date"] >= (end_date - timedelta(days=30))].copy()
    time_grain_label = "Week"
elif timeframe == "Past 3 Months":
    recent_daily = daily_data[daily_data["Date"] >= (end_date - timedelta(days=90))]
    filtered_df = recent_daily.resample("MS", on="Date").agg({
        "Queries Responded": "sum",
        "Active Users": "mean",
        "New Users": "mean",
        "AE Flags": "sum",
        "CSAT Rating": "mean"
    }).reset_index()
    time_grain_label = "Month"
elif timeframe == "Past 6 Months":
    recent_daily = daily_data[daily_data["Date"] >= (end_date - timedelta(days=180))]
    filtered_df = recent_daily.resample("MS", on="Date").agg({
        "Queries Responded": "sum",
        "Active Users": "mean",
        "New Users": "mean",
        "AE Flags": "sum",
        "CSAT Rating": "mean"
    }).reset_index()
    time_grain_label = "Month"
else:
    filtered_df = daily_data.resample("MS", on="Date").agg({
        "Queries Responded": "sum",
        "Active Users": "mean",
        "New Users": "mean",
        "AE Flags": "sum",
        "CSAT Rating": "mean"
    }).reset_index()
    time_grain_label = "Month"
 
filtered_df["Active Users"] = filtered_df["Active Users"].round(1)
filtered_df["New Users"] = filtered_df["New Users"].round(1)
filtered_df["AE Flags"] = filtered_df["AE Flags"].round(1)
filtered_df["CSAT Rating"] = filtered_df["CSAT Rating"].round(2)
 
metric_shade_map = {
    "Active Users": ("#bfdbfe", "#1d4ed8"),
    "New Users": ("#ffedd5", "#f97316"),
    "Queries Responded": ("#ccfbf1", "#0f766e"),
    "AE Flags": ("#fee2e2", "#dc2626"),
    "Average user rating": ("#fef3c7", "#b45309")
}
 
def shaded_bar_colors(values, light_hex, dark_hex):
    numeric_values = pd.Series(values, dtype="float64")
    if numeric_values.empty:
        return []
 
    minimum = numeric_values.min()
    maximum = numeric_values.max()
 
    def hex_to_rgb(hex_color):
        hex_color = hex_color.lstrip("#")
        return tuple(int(hex_color[index:index + 2], 16) for index in (0, 2, 4))
 
    def rgb_to_hex(rgb_color):
        return "#{:02x}{:02x}{:02x}".format(*rgb_color)
 
    light_rgb = hex_to_rgb(light_hex)
    dark_rgb = hex_to_rgb(dark_hex)
 
    if np.isclose(minimum, maximum):
        return [rgb_to_hex(tuple(int((lc + dc) / 2) for lc, dc in zip(light_rgb, dark_rgb)))] * len(numeric_values)
 
    colors = []
    for value in numeric_values:
        ratio = (value - minimum) / (maximum - minimum)
        interpolated_rgb = tuple(
            int(lc + (dc - lc) * ratio)
            for lc, dc in zip(light_rgb, dark_rgb)
        )
        colors.append(rgb_to_hex(interpolated_rgb))
    return colors
 
def bar_value_text(values, decimals=0):
    if decimals == 0:
        return [f"{int(round(value))}" for value in values]
    return [f"{value:.{decimals}f}" for value in values]
 
fig_line = go.Figure()
if selected_metric == "Active & New Users":
    fig_line.add_trace(go.Bar(
        x=filtered_df["Date"],
        y=filtered_df["Active Users"],
        name="Active Users",
        text=bar_value_text(filtered_df["Active Users"]),
        textposition="inside",
        insidetextanchor="end",
        marker_color=shaded_bar_colors(filtered_df["Active Users"], *metric_shade_map["Active Users"])
    ))
    fig_line.add_trace(go.Bar(
        x=filtered_df["Date"],
        y=filtered_df["New Users"],
        name="New Users",
        text=bar_value_text(filtered_df["New Users"]),
        textposition="inside",
        insidetextanchor="end",
        marker_color=shaded_bar_colors(filtered_df["New Users"], *metric_shade_map["New Users"])
    ))
elif selected_metric == "Total number of Queries":
    fig_line.add_trace(go.Bar(
        x=filtered_df["Date"],
        y=filtered_df["Queries Responded"],
        name="Total number of Queries",
        text=bar_value_text(filtered_df["Queries Responded"]),
        textposition="inside",
        insidetextanchor="end",
        marker_color=shaded_bar_colors(filtered_df["Queries Responded"], *metric_shade_map["Queries Responded"])
    ))
elif selected_metric == "AE Flags":
    fig_line.add_trace(go.Bar(
        x=filtered_df["Date"],
        y=filtered_df["AE Flags"],
        name="AE Flags",
        text=bar_value_text(filtered_df["AE Flags"]),
        textposition="inside",
        insidetextanchor="end",
        marker_color=shaded_bar_colors(filtered_df["AE Flags"], *metric_shade_map["AE Flags"])
    ))
else:
    fig_line.add_trace(go.Bar(
        x=filtered_df["Date"],
        y=filtered_df["CSAT Rating"],
        name="Average user rating",
        text=bar_value_text(filtered_df["CSAT Rating"], decimals=2),
        textposition="inside",
        insidetextanchor="end",
        marker_color=shaded_bar_colors(filtered_df["CSAT Rating"], *metric_shade_map["Average user rating"])
    ))
 
fig_line.update_layout(
    height=380,
    margin=dict(t=40, b=0, l=0, r=0),
    xaxis_title=f"{time_grain_label}",
    yaxis_title="Users" if selected_metric == "Active & New Users" else selected_metric,
    barmode="group" if selected_metric == "Active & New Users" else "relative",
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
)
 
st.plotly_chart(fig_line, use_container_width=True)
 
# ==========================================
# LAYER 3: GRANULAR INSIGHTS
# ==========================================
col_feedback, _, col_categories, _, col_consent = st.columns([1, 0.05, 1, 0.05, 1])
 
# --- Left Column: Feedback & CSAT ---
with col_feedback:
    st.subheader(
        "User Feedback & Satisfaction",
        help="Summary of patient sentiment, current Average User Rating, and qualitative feedback highlights."
    )
    st.metric(
        label="Average User Rating",
        value=f"⭐ {kpi_avg_csat} / 5.0"
    )
    st.caption(f"{kpi_csat_respondents} responded / {kpi_active_users} active users")
 
    with st.expander("View Positive Feedback Highlights", expanded=False):
        st.success("- *\"Clear instructions on cartridge storage.\"*\n- *\"Very fast and reassuring.\"*")
 
    with st.expander("View Areas for Improvement", expanded=False):
        st.warning("- *\"Didn't understand my problem on injection instructions.\"*\n- *\"Took too long to transfer me to a live nurse.\"*")
 
# --- Middle Column: Query Categories Bar Chart ---
with col_categories:
    st.subheader(
        "Query Categories Breakdown",
        help="Total query volume by category in the past 30 days."
    )
 
    fig_cat = go.Figure(go.Bar(
        x=category_df["Total Queries"],
        y=category_df["Category"],
        orientation="h",
        text=category_df["Total Queries"],
        textposition="outside",
        marker=dict(
            color=category_df["Total Queries"],
            colorscale=[[0, "#c7d2fe"], [1, "#4f46e5"]],
            showscale=False,
        ),
    ))
    fig_cat.update_layout(
        height=320,
        margin=dict(t=10, b=10, l=0, r=40),
        xaxis_title="Number of Queries",
        yaxis_title=None,
        yaxis=dict(autorange="reversed"),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
    )
    st.plotly_chart(fig_cat, use_container_width=True)
 
# --- Right Column: Consent Pie Chart ---
with col_consent:
    st.subheader(
        "Patient Data Consent",
        help="Breakdown of patient consent status for data usage in the platform."
    )
 
    consent_data = pd.DataFrame({
        "Status": ["Agree", "Disagree"],
        "Count": [200, 40]
    })
    st.markdown("<div style='margin-top:0px'></div>", unsafe_allow_html=True)
 
    fig_pie = px.pie(
        consent_data,
        values="Count",
        names="Status",
        hole=0.4,
        color="Status",
        color_discrete_map={
            "Agree": "#28a745",
            "Disagree": "#ffc107",
        }
    )
    fig_pie.update_traces(textfont_size=16)
    fig_pie.update_layout(margin=dict(t=0, b=0, l=0, r=0), height=300, legend=dict(font=dict(size=12)))
    st.plotly_chart(fig_pie, use_container_width=True)
 