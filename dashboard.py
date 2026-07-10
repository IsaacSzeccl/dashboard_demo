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
        width: 300px !important;
        min-width: 300px !important;
        max-width: 300px !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

with st.sidebar:
    st.markdown("### Menu")
    menu_selection = st.selectbox("", ["Dashboard"], label_visibility="collapsed")

st.title("Chatbot Performance Dashboard Demo")

# Visual hierarchy: make KPI cards stand out from supporting sections
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

    .csat-metric div[data-testid="stMetric"] {
        background: transparent;
        border: 0;
        border-left: 0;
        border-radius: 0;
        padding: 0 !important;
        min-height: 0;
        box-shadow: none;
        margin-bottom: -0.25rem;
    }

    .csat-metric div[data-testid="stMetricLabel"] p {
        font-size: 0.66rem;
        line-height: 1;
        margin-bottom: 0;
    }

    .csat-metric div[data-testid="stMetricValue"] {
        font-size: 0.8rem;
        line-height: 1;
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

    .cat-row {
        display: flex;
        justify-content: space-between;
        align-items: baseline;
        gap: 12px;
        margin: 14px 0 6px 0;
        font-size: 0.92rem;
        color: #667085;
        font-weight: 600;
    }

    .cat-row span:last-child {
        color: #667085;
        font-weight: 500;
        white-space: nowrap;
        font-size: 0.86rem;
    }

    .cat-bar-bg {
        width: 100%;
        height: 10px;
        background: #eef0f5;
        border-radius: 999px;
        overflow: hidden;
    }

    .cat-bar-fill {
        height: 100%;
        border-radius: 999px;
        background: linear-gradient(90deg, #6f72f7 0%, #7f82ff 100%);
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ==========================================
# 2. MOCK DATA GENERATION
# ==========================================
np.random.seed(42)

# Generate 365 days of historical daily data
end_date = datetime.today()
start_date = end_date - timedelta(days=365)
dates = pd.date_range(start=start_date, end=end_date)

daily_data = pd.DataFrame({
    "Date": dates,
    # Lower weekly totals to ~40 solved queries for a smaller real-world user base
    "Queries Solved": np.random.poisson(lam=1.2, size=len(dates)),
    "Active Users": np.clip(
        np.round(np.linspace(5, 9, len(dates)) + np.random.normal(loc=0, scale=0.4, size=len(dates))),
        1,
        None,
    ).astype(int),
    "New Users": np.clip(
        np.round(np.linspace(10, 14, len(dates)) + np.random.normal(loc=0, scale=0.5, size=len(dates))),
        1,
        None,
    ).astype(int),
    # Keep AE flags low so the historical trend stays near a couple of events per month.
    "AE Flags": np.random.poisson(lam=0.05, size=len(dates)),
    "CSAT Rating": np.random.uniform(low=3.8, high=4.9, size=len(dates))
})

# Group data by week (starting Monday) and take the mean/sum appropriately
# This directly shifts the historical trend graph from daily to weekly data points
weekly_data = daily_data.resample('W-MON', on='Date').agg({
    'Queries Solved': 'sum',      # Total solved per week
    'Active Users': 'mean',        # Average active users in that week
    'New Users': 'mean',           # Average new users in that week
    'AE Flags': 'sum',             # Total AE flags in that week
    'CSAT Rating': 'mean'          # Average rating for that week
}).reset_index()

# Rounding for clean visualization
weekly_data['Active Users'] = weekly_data['Active Users'].round(1)
weekly_data['New Users'] = weekly_data['New Users'].round(1)
weekly_data['AE Flags'] = weekly_data['AE Flags'].round(1)
weekly_data['CSAT Rating'] = weekly_data['CSAT Rating'].round(2)

# ==========================================
# LAYER 1: TOP KPIs (MONTHLY TOTALS)
# ==========================================
st.markdown("### Key Performance Indicators")

kpi1, kpi2, kpi3, kpi4, kpi5 = st.columns(5)

with kpi1:
    st.metric(
        label="Queries Solved", 
        value="32", 
        delta="12%", 
        help="Total number of medication or dosage queries successfully resolved by the chatbot this month."
    )
with kpi2:
    st.metric(
        label="Active Users", 
        value="7", 
        delta="17%", 
        help="Total unique patients who interacted with the chatbot at least once this month."
    )
with kpi3:
    st.metric(
        label="New Users", 
        value="12", 
        delta="20%", 
        help="Total number of first-time patients onboarded to the digital health platform this month."
    )
with kpi4:
    st.metric(
        label="AE Flags", 
        value="2", 
        delta="0", 
        delta_color="inverse", 
        help="Total Adverse Events automatically flagged this month based on compliance keyword triggers (e.g., severe side effects) forwarded for human safety review."
    )
with kpi5:
    st.metric(
        label="Avg Response Time", 
        value="4.96s", 
        delta="-0.5s", 
        delta_color="inverse", 
        help="The monthly average time taken by the LLM pipeline to securely process and respond to a patient query."
    )

# st.divider()

# ==========================================
# LAYER 2: GRANULAR INSIGHTS
# ==========================================
col_feedback, _, col_categories, _, col_consent = st.columns([1, 0.05, 1, 0.05, 1])

# --- Left Column: Feedback & CSAT ---
with col_feedback:
    st.subheader(
        "User Feedback & Satisfaction",
        help="Summary of patient sentiment, current Average User Rating, and qualitative feedback highlights."
    )
    st.markdown('<div class="csat-metric">', unsafe_allow_html=True)
    st.metric(
        label="Average User Rating",
        value="⭐ 4.23 / 5.0"
    )
    st.caption("17 responded / 24 active users")
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("**Positive Feedback Highlights**")
    st.success("- *\"Clear instructions on cartridge storage.\"*\n- *\"Very fast and reassuring.\"*")
    
    st.markdown("**Areas for Improvement**")
    st.warning("- *\"Didn't understand my problem on injection instructions.\"*\n- *\"Took too long to transfer me to a live nurse.\"*")

# --- Middle Column: Category Bars ---
with col_categories:
    st.subheader(
        "Query Categories Breakdown",
        help="Total query volume by category, split into solved queries and queries not solved by chatbot."
    )
    # Categorical Mock Data for the bar chart
    category_df = pd.DataFrame({
        "Category": ["Adverse Events (AE)", "Minor Queries", "Equipment Issues", "Other"],
        "Total Queries": [2, 14, 8, 8],
        "Solved Queries": [2, 12, 6, 6]
    })
    category_df = category_df.sort_values("Total Queries", ascending=False).reset_index(drop=True)
    category_df["Queries not solved by chatbot"] = category_df["Total Queries"] - category_df["Solved Queries"]
    
    # st.markdown('<div style="margin-top:2px"></div>', unsafe_allow_html=True)
    for _, row in category_df.iterrows():
        pct = (row["Solved Queries"] / row["Total Queries"]) * 100
        st.markdown(
            f'''
            <div class="cat-row"><span>{row["Category"]}</span><span>{row["Solved Queries"]}/{row["Total Queries"]} solved ({pct:.0f}%)</span></div>
            <div class="cat-bar-bg"><div class="cat-bar-fill" style="width:{pct}%;"></div></div>
            ''',
            unsafe_allow_html=True,
        )
    st.markdown('</div>', unsafe_allow_html=True)

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
    st.markdown('<div style="margin-top:0px"></div>', unsafe_allow_html=True)
    
    fig_pie = px.pie(
        consent_data, 
        values='Count', 
        names='Status',
        hole=0.4, 
        color='Status',
        color_discrete_map={
            "Agree": "#28a745", 
            "Disagree": "#ffc107", 
            # "Not Given Yet": "#ffc107"
        }
    )
    fig_pie.update_traces(textfont_size=16)
    fig_pie.update_layout(margin=dict(t=0, b=0, l=0, r=0), height=300, legend=dict(font=dict(size=16)))
    st.plotly_chart(fig_pie, use_container_width=True)
st.markdown('</div>', unsafe_allow_html=True)

# st.divider()

# ==========================================
# LAYER 3: TEMPORAL TRENDS (WEEKLY AGGREGATED)
# ==========================================
# st.markdown('<div class="section-shell">', unsafe_allow_html=True)
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
        options=["Active & New Users", "Queries Solved", "AE Flags", "Average user rating"],
        index=1
    )

metric_to_columns = {
    "Active & New Users": ["Active Users", "New Users"],
    "Queries Solved": ["Queries Solved"],
    "AE Flags": ["AE Flags"],
    "Average user rating": ["CSAT Rating"],
}
selected_metric_columns = metric_to_columns[selected_metric]

# Filter dataframe based on timeframe selection
if timeframe == "Past 1 Month":
    filtered_df = weekly_data[weekly_data['Date'] >= (end_date - timedelta(days=30))].copy()
    time_grain_label = "Week"
elif timeframe == "Past 3 Months":
    recent_daily = daily_data[daily_data['Date'] >= (end_date - timedelta(days=90))]
    filtered_df = recent_daily.resample('MS', on='Date').agg({
        'Queries Solved': 'sum',
        'Active Users': 'mean',
        'New Users': 'mean',
        'AE Flags': 'sum',
        'CSAT Rating': 'mean'
    }).reset_index()
    time_grain_label = "Month"
elif timeframe == "Past 6 Months":
    recent_daily = daily_data[daily_data['Date'] >= (end_date - timedelta(days=180))]
    filtered_df = recent_daily.resample('MS', on='Date').agg({
        'Queries Solved': 'sum',
        'Active Users': 'mean',
        'New Users': 'mean',
        'AE Flags': 'sum',
        'CSAT Rating': 'mean'
    }).reset_index()
    time_grain_label = "Month"
else:
    filtered_df = daily_data.resample('MS', on='Date').agg({
        'Queries Solved': 'sum',
        'Active Users': 'mean',
        'New Users': 'mean',
        'AE Flags': 'sum',
        'CSAT Rating': 'mean'
    }).reset_index()
    time_grain_label = "Month"

filtered_df['Active Users'] = filtered_df['Active Users'].round(1)
filtered_df['New Users'] = filtered_df['New Users'].round(1)
filtered_df['AE Flags'] = filtered_df['AE Flags'].round(1)
filtered_df['CSAT Rating'] = filtered_df['CSAT Rating'].round(2)

# Dynamic titles based on whether the metric calculation is a weekly sum or weekly average
metric_title_prefix = "Weekly Total" if selected_metric_columns == ["Queries Solved"] else "Weekly Average"

# Build the bar chart with Plotly using the weekly resampled data
metric_color_map = {
    "Active Users": "#1d4ed8",
    "New Users": "#f97316",
    "Queries Solved": "#0f766e",
    "AE Flags": "#dc2626",
    "Average user rating": "#b45309"
}

metric_shade_map = {
    "Active Users": ("#bfdbfe", "#1d4ed8"),
    "New Users": ("#ffedd5", "#f97316"),
    "Queries Solved": ("#ccfbf1", "#0f766e"),
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
        return [rgb_to_hex(tuple(int((light_channel + dark_channel) / 2) for light_channel, dark_channel in zip(light_rgb, dark_rgb)))] * len(numeric_values)

    colors = []
    for value in numeric_values:
        ratio = (value - minimum) / (maximum - minimum)
        interpolated_rgb = tuple(
            int(light_channel + (dark_channel - light_channel) * ratio)
            for light_channel, dark_channel in zip(light_rgb, dark_rgb)
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
        marker_color=shaded_bar_colors(
            filtered_df["Active Users"],
            *metric_shade_map["Active Users"]
        )
    ))
    fig_line.add_trace(go.Bar(
        x=filtered_df["Date"],
        y=filtered_df["New Users"],
        name="New Users",
        text=bar_value_text(filtered_df["New Users"]),
        textposition="inside",
        insidetextanchor="end",
        marker_color=shaded_bar_colors(
            filtered_df["New Users"],
            *metric_shade_map["New Users"]
        )
    ))
elif selected_metric == "Queries Solved":
    fig_line.add_trace(go.Bar(
        x=filtered_df["Date"],
        y=filtered_df["Queries Solved"],
        name="Queries Solved",
        text=bar_value_text(filtered_df["Queries Solved"]),
        textposition="inside",
        insidetextanchor="end",
        marker_color=shaded_bar_colors(
            filtered_df["Queries Solved"],
            *metric_shade_map["Queries Solved"]
        )
    ))
elif selected_metric == "AE Flags":
    fig_line.add_trace(go.Bar(
        x=filtered_df["Date"],
        y=filtered_df["AE Flags"],
        name="AE Flags",
        text=bar_value_text(filtered_df["AE Flags"]),
        textposition="inside",
        insidetextanchor="end",
        marker_color=shaded_bar_colors(
            filtered_df["AE Flags"],
            *metric_shade_map["AE Flags"]
        )
    ))
else:
    fig_line.add_trace(go.Bar(
        x=filtered_df["Date"],
        y=filtered_df["CSAT Rating"],
        name="Average user rating",
        text=bar_value_text(filtered_df["CSAT Rating"], decimals=2),
        textposition="inside",
        insidetextanchor="end",
        marker_color=shaded_bar_colors(
            filtered_df["CSAT Rating"],
            *metric_shade_map["Average user rating"]
        )
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
st.markdown('</div>', unsafe_allow_html=True)