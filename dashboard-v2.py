import streamlit as st
import pandas as pd
import numpy as np
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
    "Total Number of Queries": np.random.poisson(lam=1.2, size=len(dates)),
    "Active Users": np.clip(
        np.round(np.linspace(12, 18, len(dates)) + np.random.normal(loc=0, scale=0.5, size=len(dates))),
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
kpi_queries_responded = int(rolling_data["Total Number of Queries"].sum())
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
prev_queries_responded = int(prev_data["Total Number of Queries"].sum())
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
    "Total Number of Queries": "sum",
    "Active Users": "mean",
    "New Users": "mean",
    "AE Flags": "sum",
    "CSAT Rating": "mean"
}).reset_index()
 
weekly_data["Active Users"] = weekly_data["Active Users"].round(1)
weekly_data["New Users"] = weekly_data["New Users"].round(1)
weekly_data["AE Flags"] = weekly_data["AE Flags"].round(1)
weekly_data["CSAT Rating"] = weekly_data["CSAT Rating"].round(2)
weekly_data["Queries Resolved"] = (weekly_data["Total Number of Queries"] * 0.80).round(0)
 
# Query category mock data (consistent with rolling 30-day totals)
# Ensure category totals sum to kpi_queries_responded
total_queries_assigned = kpi_queries_responded - kpi_ae_flags  # kpi_queries_responded is sum of "Total Number of Queries"
 
# Allocate queries proportionally to categories (maintaining approximately 4:3:2:1 ratio)
category_values = {
    "Saizen Product Enquiry": max(1, round(total_queries_assigned * 0.4)),
    "Device Enquiry": max(1, round(total_queries_assigned * 0.35)),
    "Restricted Information Enquiry": max(1, round(total_queries_assigned * 0.25)), # (side effects, product price and recommendation, and information out of knowledge base)
}
 
# Adjust to ensure exact sum (excluding AE)
sum_allocated = sum(category_values.values())
if sum_allocated != total_queries_assigned:
    diff = total_queries_assigned - sum_allocated
    category_values["Saizen Product Enquiry"] += diff
 
# Add AE category
category_values["AE"] = kpi_ae_flags
 
category_df = pd.DataFrame({
    "Category": list(category_values.keys()),
    "Total Queries": list(category_values.values()),
})
category_df = category_df.sort_values("Total Queries", ascending=False).reset_index(drop=True)
 
# Monthly summary table data — last 12 full months (calendar months ending before TODAY's month)
_FEEDBACK_POSITIVE_POOL = [
    "Clear instructions on cartridge storage.",
    "Very fast and reassuring response.",
    "Helped me understand the injection technique perfectly.",
    "Prompt reply, felt well supported.",
    "The chatbot answered all my questions about side effects.",
    "Easy to use, very clear explanations.",
    "Saved me a trip to the clinic — thank you!",
    "Appreciated the quick escalation to a live nurse.",
    "Great help with medication timing and dosage questions.",
    "The chatbot made it easy to understand possible allergic reactions.",
    "Excellent guidance on proper injection site rotation.",
    "Very helpful information about drug interactions.",
    "Quickly resolved my concerns about the injection procedure.",
    "Clear and supportive responses throughout our conversation.",
    "The chatbot provided exactly what I needed to feel confident.",
    "Impressive accuracy in answering my medical questions.",
    "Felt heard and understood by the chatbot.",
    "Helpful advice on managing side effects at home.",
    "Great resource for understanding my treatment plan.",
    "The chatbot's explanations were simple yet comprehensive.",
    "Very reassuring support when I was feeling anxious.",
    "Excellent information about appointment scheduling.",
    "The chatbot helped me make an informed decision.",
    "Clear guidance on what to do if I miss a dose.",
    "Very professional and caring interaction.",
    "The chatbot remembered my preferences and concerns.",
    "Helpful reminders and follow-up suggestions.",
    "Great way to get answers without visiting the clinic.",
    "The chatbot explained everything in simple terms.",
    "Felt much more confident after the conversation.",
]
_FEEDBACK_NEGATIVE_POOL = [
    "Didn't understand my problem on injection instructions.",
    "Took too long to transfer me to a live nurse.",
    "Answer was too generic, not helpful for my situation.",
    "Could not find information about my specific device model.",
    "The bot repeated itself without resolving my question.",
    "Response felt robotic and unhelpful.",
    "Needed a human but the chatbot kept looping.",
    "Not enough information about storage temperatures.",
    "Couldn't find answers to my specific concerns.",
    "The chatbot misunderstood my question multiple times.",
    "Response was confusing and hard to follow.",
    "Limited information about less common side effects.",
    "The chatbot couldn't help with my dosage concerns.",
    "Felt frustrated with the lack of personalization.",
    "The chatbot provided outdated information.",
    "Couldn't get a straight answer to a simple question.",
    "Very slow response times throughout the interaction.",
    "The chatbot doesn't understand complex medical questions.",
    "Limited ability to discuss my specific health conditions.",
    "Felt like the chatbot was just reading from a script.",
    "The chatbot provided conflicting information.",
    "Very difficult to navigate and find relevant answers.",
    "The chatbot couldn't help with insurance or payment questions.",
    "Response lacked empathy and human touch.",
    "The chatbot didn't address my main concern.",
    "Information provided was incomplete.",
    "Frustrated with frequent clarification requests.",
    "The chatbot kept suggesting irrelevant solutions.",
    "No option to speak with a real person easily.",
    "The chatbot's medical advice seemed incomplete.",
]
_FEEDBACK_PHONE_POOL = [
    "852-9100-0001", "852-9100-0002", "852-9100-0003", "852-9100-0004",
    "852-9100-0005", "852-9100-0006", "852-9100-0007", "852-9100-0008",
    "852-9100-0009", "852-9100-0010", "852-9100-0011", "852-9100-0012",
    "852-9100-0013", "852-9100-0014", "852-9100-0015", "852-9100-0016",
]
 
# Build per-month aggregates for the last 13 months (including current month)
_month_starts = pd.date_range(
    end=TODAY.replace(day=1),  # start of current month
    periods=13,
    freq="MS"
)
 
monthly_summary_rows = []
monthly_feedback_by_month = {}
 
_fb_rng = np.random.default_rng(seed=7)
 
for _ms in _month_starts:
    _me = (_ms + pd.offsets.MonthEnd(0)).to_pydatetime()
    _mask = (daily_data["Date"] >= _ms) & (daily_data["Date"] <= _me)
    _m = daily_data[_mask]
 
    _q_responded = int(_m["Total Number of Queries"].sum())
    _q_resolved = int(round(_q_responded * 0.80))
    _active = int(round(_m["Active Users"].mean())) if len(_m) > 0 else 0
    _new = int(round(_m["New Users"].mean())) if len(_m) > 0 else 0
    _ae = int(_m["AE Flags"].sum())
    _csat = round(_m["CSAT Rating"].mean(), 2) if len(_m) > 0 else 0.0
    _respondents = max(1, round(_active * 0.70))
 
    # Consented patients: 80% of new users that month gave consent
    _consented = int(round(_new * 0.80))
    _not_consented = _new - _consented
 
    # Feedback records for this month
    _n_pos = max(1, round(_respondents * 0.72))
    _n_neg = max(1, _respondents - _n_pos)
    _pos_phones = [_FEEDBACK_PHONE_POOL[i % len(_FEEDBACK_PHONE_POOL)]
                   for i in _fb_rng.integers(0, len(_FEEDBACK_PHONE_POOL), size=_n_pos)]
    _neg_phones = [_FEEDBACK_PHONE_POOL[i % len(_FEEDBACK_PHONE_POOL)]
                   for i in _fb_rng.integers(0, len(_FEEDBACK_PHONE_POOL), size=_n_neg)]
    _pos_msgs = [_FEEDBACK_POSITIVE_POOL[i] for i in _fb_rng.integers(0, len(_FEEDBACK_POSITIVE_POOL), size=_n_pos)]
    _neg_msgs = [_FEEDBACK_NEGATIVE_POOL[i] for i in _fb_rng.integers(0, len(_FEEDBACK_NEGATIVE_POOL), size=_n_neg)]
 
    _fb_df = pd.DataFrame({
        "Phone Number": _pos_phones + _neg_phones,
        "Type": ["Positive"] * _n_pos + ["Negative"] * _n_neg,
        "Message": _pos_msgs + _neg_msgs,
    })
    _month_key = _ms.strftime("%Y-%m")
    monthly_feedback_by_month[_month_key] = _fb_df
 
    monthly_summary_rows.append({
        "Month": _ms.strftime("%b %Y"),
        "month_key": _month_key,
        "Total Number of Queries": _q_responded,
        "Queries Resolved": _q_resolved,
        "Active Users": _active,
        "New Users": _new,
        "AE Flags": _ae,
        "Avg. User Rating": _csat,
        "Feedback Responses": _respondents,
        "Consented Patients": _consented,
        "Non-Consented": _not_consented,
    })
 
monthly_summary_df = pd.DataFrame(monthly_summary_rows[::-1])  # most recent first
 
# Rolling 30-day feedback records (consistent with kpi_csat_respondents)
_rolling_fb_rng = np.random.default_rng(seed=13)
_r_respondents = max(1, round(kpi_active_users * 0.70))
_r_n_pos = max(1, round(_r_respondents * 0.72))
_r_n_neg = max(1, _r_respondents - _r_n_pos)
_r_pos_phones = [_FEEDBACK_PHONE_POOL[i % len(_FEEDBACK_PHONE_POOL)]
                 for i in _rolling_fb_rng.integers(0, len(_FEEDBACK_PHONE_POOL), size=_r_n_pos)]
_r_neg_phones = [_FEEDBACK_PHONE_POOL[i % len(_FEEDBACK_PHONE_POOL)]
                 for i in _rolling_fb_rng.integers(0, len(_FEEDBACK_PHONE_POOL), size=_r_n_neg)]
_r_pos_msgs = [_FEEDBACK_POSITIVE_POOL[i] for i in _rolling_fb_rng.integers(0, len(_FEEDBACK_POSITIVE_POOL), size=_r_n_pos)]
_r_neg_msgs = [_FEEDBACK_NEGATIVE_POOL[i] for i in _rolling_fb_rng.integers(0, len(_FEEDBACK_NEGATIVE_POOL), size=_r_n_neg)]
rolling_feedback_df = pd.DataFrame({
    "Phone Number": _r_pos_phones + _r_neg_phones,
    "Type": ["Positive"] * _r_n_pos + ["Negative"] * _r_n_neg,
    "Message": _r_pos_msgs + _r_neg_msgs,
})
 
# Rolling 30-day consent submissions (80% of new users submitted consent)
rolling_total_patients_in_window = kpi_new_users
rolling_consent_submitted = int(round(rolling_total_patients_in_window * 0.80))
rolling_consent_not_submitted = rolling_total_patients_in_window - rolling_consent_submitted
 
# AE patient records — dynamically generated to match kpi_ae_flags exactly
_AE_PHONE_POOL = [
    "852-9123-4567", "852-9876-5432", "852-6234-8901",
    "852-5512-3344", "852-9001-2222", "852-6688-9900",
    "852-5544-1122", "852-9321-0011", "852-6677-8899", "852-5500-4411",
]
_AE_CONTENT_POOL = [
    "My child developed severe redness and swelling at the injection site after the last dose. It has not subsided for 3 days.",
    "My child complained of joint pain and swelling in the knees approximately 2 hours after the weekly injection.",
    "There is a hard lump forming under my child's skin at the injection site and it is painful to touch.",
    "My child has experienced headaches more frequently since starting the growth hormone. I'm concerned about increased intracranial pressure.",
    "My child experienced nausea and complained of stomach pain after the injection. This has happened twice in a row now.",
    "The injection site looks infected — there is redness and swelling that feels warm. I'm worried about an abscess.",
    "My child developed a high fever approximately 6 hours after the injection. Temperature reached 38.5°C.",
    "My child reported numbness and tingling in the hands and feet after the last injection.",
    "My child experienced a severe allergic reaction with hives and facial swelling within 15 minutes of injection.",
    "My child reported severe leg pain and muscle cramps the night after the injection.",
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
 
# User Feedback dialog (floating window)
@st.dialog("User Feedback Details", width="large")
def show_feedback_dialog(month_label, fb_df):
    st.caption(f"Feedback records for {month_label}")
    if fb_df.empty:
        st.info("No feedback recorded for this month.")
        return
    pos_count = (fb_df["Type"] == "Positive").sum()
    neg_count = (fb_df["Type"] == "Negative").sum()
    c1, c2 = st.columns(2)
    c1.metric("Positive", pos_count)
    c2.metric("Negative", neg_count)
    st.dataframe(
        fb_df.style.apply(
            lambda row: ["background-color: #f0fdf4; color: #166534" if row["Type"] == "Positive"
                         else "background-color: #fef2f2; color: #991b1b"] * len(row),
            axis=1
        ),
        use_container_width=True,
        hide_index=True,
        height=min(400, 40 + len(fb_df) * 35),
    )
 
# Rolling 30-day feedback dialog
@st.dialog(f"User Feedback — Past {ROLLING_WINDOW_DAYS} Days", width="large")
def show_rolling_feedback_dialog():
    st.caption(f"Period: {ROLLING_START.strftime('%Y-%m-%d')} to {TODAY.strftime('%Y-%m-%d')}")
    pos_count = (rolling_feedback_df["Type"] == "Positive").sum()
    neg_count = (rolling_feedback_df["Type"] == "Negative").sum()
    c1, c2 = st.columns(2)
    c1.metric("Positive", pos_count)
    c2.metric("Negative", neg_count)
    st.dataframe(
        rolling_feedback_df.style.apply(
            lambda row: ["background-color: #f0fdf4; color: #166534" if row["Type"] == "Positive"
                         else "background-color: #fef2f2; color: #991b1b"] * len(row),
            axis=1
        ),
        use_container_width=True,
        hide_index=True,
        height=min(400, 40 + len(rolling_feedback_df) * 35),
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
        label="Total Number of Queries",
        value=str(kpi_queries_responded),
        delta=pct_delta(kpi_queries_responded, prev_queries_responded),
        help="Total number of patient queries responded to by the chatbot in the past 30 days."
    )
with kpi2:
    st.metric(
        label="Queries Resolved",
        value=str(kpi_queries_resolved),
        delta=pct_delta(kpi_queries_resolved, prev_queries_resolved),
        help="Total number of patient queries responded to by the chatbot in the past 30 days."
    )
with kpi3:
    st.metric(
        label="Active Users",
        value=str(kpi_active_users),
        delta=pct_delta(kpi_active_users, prev_active_users),
        help="Total number of unique patients who interacted with the chatbot in the past 30 days."
    )
with kpi4:
    st.metric(
        label="New Users",
        value=str(kpi_new_users),
        delta=pct_delta(kpi_new_users, prev_new_users),
        help="Total number of new patients onboarded to the HK PSP AI Chatbot in the past 30 days."
    )
with kpi5:
    st.metric(
        label="AE Flags",
        value=str(kpi_ae_flags),
        delta=pct_delta(kpi_ae_flags, prev_ae_flags),
        delta_color="inverse",
        help="Total Adverse Events automatically flagged in the past 30 days based on AE keyword triggers, for PSP Nurse/Medical Team review and report AE."
    )
 
# ==========================================
# LAYER 2: HISTORICAL TRENDS (moved above granular insights)
# ==========================================
st.markdown("### Historical Trends")
 
filter_col1, filter_col2, _, filter_col3 = st.columns([1, 1, 1, 1.2])
 
all_months = pd.date_range(start=start_date, end=end_date, freq="MS").tolist()
month_labels = [d.strftime("%b %Y") for d in all_months]
 
with filter_col1:
    start_idx = max(0, len(all_months) - 12)
    start_month = st.selectbox(
        "Select Start Month",
        options=month_labels,
        index=start_idx
    )
    start_month_date = pd.to_datetime(start_month, format="%b %Y")
 
with filter_col2:
    available_end_dates = [d for d in all_months if d >= start_month_date]
    available_end_labels = [d.strftime("%b %Y") for d in available_end_dates]
    end_idx = min(11, len(available_end_labels) - 1) if available_end_labels else 0
 
    end_month = st.selectbox(
        "Select End Month",
        options=available_end_labels if available_end_labels else [start_month],
        index=end_idx
    )
    end_month_date = pd.to_datetime(end_month, format="%b %Y") + pd.offsets.MonthEnd(0)
 
with filter_col3:
    selected_metric = st.selectbox(
        "Select Metric",
        options=["Active & New Users", "Total Number of Queries", "Queries Resolved", "AE Flags", "Average user rating"],
        index=1
    )
 
metric_to_columns = {
    "Active & New Users": ["Active Users", "New Users"],
    "Total Number of Queries": ["Total Number of Queries"],
    "Queries Resolved": ["Queries Resolved"],
    "AE Flags": ["AE Flags"],
    "Average user rating": ["CSAT Rating"],
}
selected_metric_columns = metric_to_columns[selected_metric]
 
# Filter dataframe based on month range selection
range_daily = daily_data[(daily_data["Date"] >= start_month_date) & (daily_data["Date"] <= end_month_date)]
filtered_df = range_daily.resample("MS", on="Date").agg({
    "Total Number of Queries": "sum",
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
filtered_df["Queries Resolved"] = (filtered_df["Total Number of Queries"] * 0.80).round(0)
 
metric_shade_map = {
    "Active Users": ("#bfdbfe", "#1d4ed8"),
    "New Users": ("#ffedd5", "#f97316"),
    "Total Number of Queries": ("#ccfbf1", "#0f766e"),
    "Queries Resolved": ("#d1fae5", "#059669"),
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
elif selected_metric == "Total Number of Queries":
    fig_line.add_trace(go.Bar(
        x=filtered_df["Date"],
        y=filtered_df["Total Number of Queries"],
        name="Total Number of Queries",
        text=bar_value_text(filtered_df["Total Number of Queries"]),
        textposition="inside",
        insidetextanchor="end",
        marker_color=shaded_bar_colors(filtered_df["Total Number of Queries"], *metric_shade_map["Total Number of Queries"])
    ))
elif selected_metric == "Queries Resolved":
    fig_line.add_trace(go.Bar(
        x=filtered_df["Date"],
        y=filtered_df["Queries Resolved"],
        name="Queries Resolved",
        text=bar_value_text(filtered_df["Queries Resolved"]),
        textposition="inside",
        insidetextanchor="end",
        marker_color=shaded_bar_colors(filtered_df["Queries Resolved"], *metric_shade_map["Queries Resolved"])
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
        help="Summary of current Average User Rating, and qualitative feedback highlights."
    )
    st.metric(
        label="Average User Rating",
        value=f"⭐ {kpi_avg_csat} / 5.0"
    )
    st.caption(f"{kpi_csat_respondents} responded / {kpi_active_users} active users")
 
    if st.button("Show User Feedback", use_container_width=True):
        show_rolling_feedback_dialog()
 
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
 
# --- Right Column: Consent Gauge Chart ---
with col_consent:
    st.subheader(
        "Patient Data Consent",
        help="Number of patients who gave consent in the past 30 days."
    )
 
    submission_rate = int(round((rolling_consent_submitted / rolling_total_patients_in_window) * 100))
 
    fig_gauge = go.Figure(go.Indicator(
        mode="gauge",
        value=submission_rate,
        domain={"x": [0, 1], "y": [0, 1]},
        gauge={
            "axis": {"range": [0, 100], "tickwidth": 0, "showticklabels": False, "ticklen": 0, "visible": False},
            "bar": {"color": "#10b981"},
            "steps": [
                {"range": [0, 100], "color": "#f0fdf4"}
            ]
        }
    ))
    fig_gauge.add_annotation(
        text=f"<b>{rolling_consent_submitted}/{rolling_total_patients_in_window}</b>",
        x=0.5, y=0.35,
        showarrow=False,
        font=dict(size=50, color="#0f766e"),
        yref="paper"
    )
    fig_gauge.update_layout(
        margin=dict(t=30, b=10, l=10, r=10),
        height=250,
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)"
    )
    st.plotly_chart(fig_gauge, use_container_width=True)
 
    st.markdown("<p style='text-align: center; color: #64748b;'>new patients gave consent</p>", unsafe_allow_html=True)
 
# ==========================================
# LAYER 4: MONTHLY SUMMARY TABLE
# ==========================================
st.markdown("### Monthly Summary")
 
summary_col1, summary_col2, _ = st.columns([1, 1, 2.2])
with summary_col1:
    table_start_month = st.selectbox(
        "Select Start Month (Summary)",
        options=month_labels,
        index=max(0, len(month_labels) - 13),
        key="summary_start_month"
    )
    table_start_date = pd.to_datetime(table_start_month, format="%b %Y")
 
with summary_col2:
    table_available_dates = [d for d in all_months if d >= table_start_date]
    table_available_labels = [d.strftime("%b %Y") for d in table_available_dates]
    table_end_idx = min(12, len(table_available_labels) - 1) if table_available_labels else 0
 
    table_end_month = st.selectbox(
        "Select End Month (Summary)",
        options=table_available_labels if table_available_labels else [table_start_month],
        index=table_end_idx,
        key="summary_end_month"
    )
    table_end_date = pd.to_datetime(table_end_month, format="%b %Y") + pd.offsets.MonthEnd(0)
 
# Filter monthly_summary_df based on selected timeframe
filtered_summary_df = monthly_summary_df[
    (pd.to_datetime(monthly_summary_df["Month"], format="%b %Y") >= table_start_date) &
    (pd.to_datetime(monthly_summary_df["Month"], format="%b %Y") <= table_end_date)
].copy()
 
st.caption("Click 'View Feedback' on any row to see detailed user feedback.")
 
_TABLE_COLS = [
    (" \nMonth", 1.1),
    ("Total number\nof queries", 0.6),
    ("Queries\nResolved", 0.4),
    ("Active\nUsers", 0.4),
    ("New\nUsers", 0.4),
    ("AE\nFlags", 0.45),
    ("Avg. User\nRating", 0.65),
    ("Feedback\nResponses", 0.65),
    ("Consented\nPatients", 0.7),
    ("Non-\nConsented", 0.6),
    (" \nFeedback", 0.65),
]
_COL_KEYS = [
    "Month", "Total Number of Queries", "Queries Resolved",
    "Active Users", "New Users",
    "AE Flags", "Avg. User Rating",
    "Feedback Responses", "Consented Patients", "Non-Consented",
]
_RATIOS = [w for _, w in _TABLE_COLS]
 
# Header row
_header_cols = st.columns(_RATIOS)
for _hcol, (_label, _) in zip(_header_cols, _TABLE_COLS):
    _hcol.markdown(
        f"<div style='font-size:0.72rem;font-weight:700;color:#475569;"
        f"padding:4px 2px 4px 2px;border-bottom:2px solid #cbd5e1;"
        f"white-space:pre-line;line-height:1.3'>{_label}</div>",
        unsafe_allow_html=True
    )
 
# Data rows (show filtered months, scrollable via container)
with st.container(height=265):
    for _, _row in filtered_summary_df.iterrows():
        _row_cols = st.columns(_RATIOS)
        for _rcol, _key in zip(_row_cols[:-1], _COL_KEYS):
            _val = _row[_key]
            _rcol.markdown(
                f"<div style='font-size:0.8rem;padding:6px 2px;border-bottom:1px solid #f1f5f9'>{_val}</div>",
                unsafe_allow_html=True
            )
        with _row_cols[-1]:
            st.markdown("<div style='padding-top:2px'>", unsafe_allow_html=True)
            if st.button("View", key=f"fb_{_row['month_key']}", use_container_width=True):
                show_feedback_dialog(
                    _row["Month"],
                    monthly_feedback_by_month[_row["month_key"]]
                )
            st.markdown("</div>", unsafe_allow_html=True)