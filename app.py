# ============================================================
# GENESIS EiR DASHBOARD — FINAL VERSION
# Source: Genesis workbook -> Sheet4 only
# EIR 1 + EIR 2 combined by default
# Employment Generated = Current Team Size - Team size at onboarding
# ============================================================

from pathlib import Path
import re

import pandas as pd
import plotly.express as px
import streamlit as st


# ------------------------- APP CONFIG -------------------------
st.set_page_config(
    page_title="GENESIS EiR Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

OFFICIAL_INCUBATORS = 64
SOURCE_SHEET = "Sheet4"

PLOT_CONFIG = {
    "displayModeBar": False,   # removes camera / zoom / share toolbar icons
    "displaylogo": False,
    "responsive": True,
}


# ------------------------- PREMIUM UI -------------------------
st.markdown(
    """
    <style>
        .stApp {
            background:
                radial-gradient(circle at 5% 0%, rgba(31,95,139,.10), transparent 28%),
                radial-gradient(circle at 96% 3%, rgba(31,122,108,.10), transparent 28%),
                linear-gradient(180deg, #F8FBFE 0%, #EEF4F8 100%);
        }

        .block-container {
            max-width: 1540px;
            padding-top: 1.2rem;
            padding-bottom: 2rem;
        }

        section[data-testid="stSidebar"] {
            background: linear-gradient(180deg, #FFFFFF 0%, #F7FAFD 100%);
            border-right: 1px solid #DCE6EF;
        }

        .hero {
            background: linear-gradient(120deg, #0B2036 0%, #1E5F8B 55%, #167A6C 100%);
            border-radius: 23px;
            padding: 28px 32px;
            color: white;
            box-shadow: 0 20px 42px rgba(15,41,64,.20);
            margin-bottom: 17px;
        }

        .tag {
            display: inline-block;
            padding: 6px 12px;
            border-radius: 999px;
            background: rgba(255,255,255,.15);
            border: 1px solid rgba(255,255,255,.30);
            color: #EAF7F4;
            font-size: 11px;
            font-weight: 800;
            letter-spacing: .8px;
            text-transform: uppercase;
            margin-bottom: 12px;
        }

        .hero-title {
            font-size: 2.25rem;
            font-weight: 850;
            letter-spacing: -.7px;
            line-height: 1.05;
            margin: 0;
        }

        .hero-sub {
            margin-top: 9px;
            color: #DDECF6;
            font-size: .98rem;
            line-height: 1.55;
        }

        .section-title {
            font-size: 1.22rem;
            font-weight: 800;
            color: #102A43;
            border-left: 5px solid #1F7A6C;
            padding-left: 12px;
            margin: 21px 0 6px 0;
        }

        .section-note {
            color: #667085;
            font-size: .87rem;
            margin: 0 0 12px 17px;
        }

        [data-testid="stMetric"] {
            background: linear-gradient(180deg, #FFFFFF 0%, #F8FBFD 100%);
            border: 1px solid #DCE6EF;
            border-radius: 17px;
            padding: 15px 16px;
            box-shadow: 0 8px 19px rgba(15,23,42,.06);
        }

        [data-testid="stMetricLabel"] {
            color: #52606D;
            font-weight: 650;
            font-size: .83rem;
        }

        [data-testid="stMetricValue"] {
            color: #102A43;
            font-weight: 850;
            font-size: 1.52rem;
        }

        .stTabs [data-baseweb="tab-list"] {
            gap: 10px;
            border-bottom: 1px solid #DCE6EF;
            padding-bottom: 4px;
        }

        .stTabs [data-baseweb="tab"] {
            background: #FFFFFF;
            border: 1px solid #DCE6EF;
            border-radius: 999px;
            padding: 10px 18px;
            font-weight: 700;
            color: #3C4F65;
        }

        .stTabs [aria-selected="true"] {
            background: linear-gradient(120deg, #1F5F8B, #1F7A6C) !important;
            color: white !important;
            border-color: transparent !important;
        }

        .highlight-card {
            background: #FFFFFF;
            border: 1px solid #DCE6EF;
            border-radius: 18px;
            padding: 15px 16px;
            box-shadow: 0 7px 17px rgba(15,23,42,.05);
            min-height: 112px;
        }

        .h-label {
            font-size: .74rem;
            font-weight: 750;
            letter-spacing: .45px;
            text-transform: uppercase;
            color: #667085;
        }

        .h-value {
            font-size: 1.20rem;
            font-weight: 850;
            color: #102A43;
            margin: 7px 0 5px;
            line-height: 1.18;
        }

        .h-note {
            font-size: .80rem;
            color: #667085;
            line-height: 1.35;
        }

        [data-testid="stDataFrame"] {
            border: 1px solid #DCE6EF;
            border-radius: 14px;
            overflow: hidden;
        }
    </style>
    """,
    unsafe_allow_html=True,
)


# ------------------------- HELPERS -------------------------
def clean_text(value):
    """Standardise blank/NA text without changing genuine values."""
    if pd.isna(value):
        return "Not Available"

    text = str(value).strip()
    if text.lower() in {"", "na", "n/a", "nil", "none", "-", "not applicable"}:
        return "Not Available"
    return text


def to_number(value):
    """Safely converts numeric cells and mixed text values into numbers."""
    if pd.isna(value):
        return 0.0

    text = str(value).replace(",", "").strip()
    if text.lower() in {"", "na", "n/a", "nil", "none", "-", "not applicable"}:
        return 0.0

    match = re.search(r"-?\d+(?:\.\d+)?", text)
    return float(match.group()) if match else 0.0


def to_trl(value):
    match = re.search(r"\b([1-9])\b", str(value))
    return int(match.group(1)) if match else None


def clean_state(value):
    """Only fixes clear known spelling variants."""
    text = clean_text(value)
    replacements = {
        "Rajesthan": "Rajasthan",
        "Madhy Pradesh": "Madhya Pradesh",
        "New Delhi": "Delhi",
        "NCT of Delhi": "Delhi",
        "Jammu and Kashmir": "Jammu & Kashmir",
        "Andaman and Nicobar Islands": "Andaman & Nicobar Islands",
    }
    return replacements.get(text, text)


def clean_stage(value):
    text = clean_text(value)
    lowered = text.lower()

    if text == "Not Available":
        return text
    if "mvp" in lowered:
        return "MVP"
    if "poc" in lowered or "proof of concept" in lowered:
        return "POC"
    if "prototype" in lowered:
        return "Prototype"
    if "idea" in lowered or "ideation" in lowered:
        return "Ideation"
    if "pilot" in lowered or "testing" in lowered or "validation" in lowered:
        return "Validation / Testing"
    if "market" in lowered or "gtm" in lowered or "commercial" in lowered:
        return "Market / GTM"
    if "scal" in lowered or "growth" in lowered:
        return "Scaling / Growth"
    return text


def fmt(value):
    return f"{int(round(value)):,}"


def show_chart(fig, height):
    """Consistent premium Plotly style without toolbar icons."""
    fig.update_layout(
        height=height,
        paper_bgcolor="white",
        plot_bgcolor="white",
        margin=dict(l=10, r=10, t=50, b=10),
        title_font=dict(size=16, color="#102A43"),
        font=dict(family="Arial", color="#344054"),
        hoverlabel=dict(bgcolor="white", font_color="#102A43"),
        legend_title_text="",
    )
    fig.update_xaxes(gridcolor="#EAF0F5", zeroline=False)
    fig.update_yaxes(gridcolor="#EAF0F5", zeroline=False)
    st.plotly_chart(fig, use_container_width=True, config=PLOT_CONFIG)


# Stable coordinates used for the original fixed India bubble map
STATE_CENTROIDS = {
    "Andhra Pradesh": (15.9129, 79.7400),
    "Arunachal Pradesh": (28.2180, 94.7278),
    "Assam": (26.2006, 92.9376),
    "Bihar": (25.0961, 85.3131),
    "Chandigarh": (30.7333, 76.7794),
    "Chhattisgarh": (21.2787, 81.8661),
    "Delhi": (28.7041, 77.1025),
    "Goa": (15.2993, 74.1240),
    "Gujarat": (22.2587, 71.1924),
    "Haryana": (29.0588, 76.0856),
    "Himachal Pradesh": (31.1048, 77.1734),
    "Jammu & Kashmir": (33.7782, 76.5762),
    "Jharkhand": (23.6102, 85.2799),
    "Karnataka": (15.3173, 75.7139),
    "Kerala": (10.8505, 76.2711),
    "Ladakh": (34.1526, 77.5771),
    "Madhya Pradesh": (22.9734, 78.6569),
    "Maharashtra": (19.7515, 75.7139),
    "Manipur": (24.6637, 93.9063),
    "Meghalaya": (25.4670, 91.3662),
    "Mizoram": (23.1645, 92.9376),
    "Nagaland": (26.1584, 94.5624),
    "Odisha": (20.9517, 85.0985),
    "Punjab": (31.1471, 75.3412),
    "Rajasthan": (27.0238, 74.2179),
    "Sikkim": (27.5330, 88.5122),
    "Tamil Nadu": (11.1271, 78.6569),
    "Telangana": (18.1124, 79.0193),
    "Tripura": (23.9408, 91.9882),
    "Uttar Pradesh": (26.8467, 80.9462),
    "Uttarakhand": (30.0668, 79.0193),
    "West Bengal": (22.9868, 87.8550),
}


# ------------------------- DATA LOAD -------------------------
@st.cache_data(show_spinner=False)
def load_sheet4(file_path, file_modified_time):
    """
    Reads only Sheet4 from the Genesis workbook.
    The uploaded workbook's column `EIR ` has a trailing space;
    stripping all column names converts it correctly to `EIR`.
    """
    raw = pd.read_excel(file_path, sheet_name=SOURCE_SHEET)
    raw.columns = [str(column).strip() for column in raw.columns]

    required_columns = [
        "EIR",
        "Incubator Name",
        "Startup Name",
        "Gender of Founder",
        "State of the Startup",
        "District of the Startup",
        "City of the Startup",
        "Tier of the City",
        "Domain in which EIR is working",
        "Current Stage of development?",
        "Technology used by EIR / Founder",
        "TRL level before EIR",
        "TRL level after EIR",
        "No of Patent filed",
        "No of Patent granted",
        "No of Patent Published",
        "Any Woman Team Member:",
        "Current Number of Customers / clients",
        "Team size at the time of onboarding",
        "Current Team Size",
    ]

    missing = [column for column in required_columns if column not in raw.columns]
    if missing:
        raise ValueError("Sheet4 headers missing: " + ", ".join(missing))

    # Keeps all 570 actual startup records.
    raw = raw[raw["Startup Name"].notna()].copy()

    text_columns = [
        "EIR",
        "Incubator Name",
        "Startup Name",
        "Gender of Founder",
        "State of the Startup",
        "District of the Startup",
        "City of the Startup",
        "Tier of the City",
        "Domain in which EIR is working",
        "Current Stage of development?",
        "Technology used by EIR / Founder",
        "Any Woman Team Member:",
    ]
    for column in text_columns:
        raw[column] = raw[column].apply(clean_text)

    numeric_columns = [
        "No of Patent filed",
        "No of Patent granted",
        "No of Patent Published",
        "Current Number of Customers / clients",
        "Team size at the time of onboarding",
        "Current Team Size",
    ]
    for column in numeric_columns:
        raw[column] = raw[column].apply(to_number)

    raw["EIR Clean"] = raw["EIR"].astype(str).str.strip().str.upper()
    raw["State Clean"] = raw["State of the Startup"].apply(clean_state)
    raw["Domain Clean"] = raw["Domain in which EIR is working"].apply(clean_text)
    raw["Stage Clean"] = raw["Current Stage of development?"].apply(clean_stage)

    raw["TRL Before"] = raw["TRL level before EIR"].apply(to_trl)
    raw["TRL After"] = raw["TRL level after EIR"].apply(to_trl)

    # EMPLOYMENT GENERATED (exact requested calculation):
    # SUM(Current Team Size) - SUM(Team size at the time of onboarding).
    # No row-level clipping is applied, so every dashboard aggregation follows this exact formula.
    raw["Employment Generated"] = (
        raw["Current Team Size"] - raw["Team size at the time of onboarding"]
    )

    # Directly based on the "Any Woman Team Member:" field only.
    # This is not inferred from founder gender.
    women_team = raw["Any Woman Team Member:"].astype(str).str.lower().str.strip()
    raw["Women Team Member"] = women_team.eq("yes")

    return raw


# ------------------------- AUTO FILE PICK -------------------------
# No file upload needed. Keep app.py and the Genesis workbook in the same folder.
app_folder = Path(__file__).resolve().parent
excel_files = [
    file for file in app_folder.glob("*.xlsx")
    if not file.name.startswith("~$")
]

genesis_files = [
    file for file in excel_files
    if "genesis" in file.name.lower()
]

if not genesis_files:
    st.error("Genesis Excel workbook app.py ke same folder mein nahi mili.")
    st.stop()

# Supports Genesis.xlsx, Genesis .xlsx, Genesis (1).xlsx, etc.
excel_file = max(genesis_files, key=lambda file: file.stat().st_mtime)

try:
    workbook = pd.ExcelFile(excel_file)
    if SOURCE_SHEET not in workbook.sheet_names:
        st.error(f"`{SOURCE_SHEET}` sheet {excel_file.name} mein nahi mili.")
        st.stop()

    df = load_sheet4(str(excel_file), excel_file.stat().st_mtime)
except Exception as error:
    st.error(f"Workbook load error: {error}")
    st.stop()


# ------------------------- FILTERS -------------------------
st.sidebar.markdown("## 🔎 Filters")
st.sidebar.caption(f"Source: {excel_file.name} • Sheet4 • {len(df):,} records")

eir_options = sorted(df["EIR Clean"].unique().tolist())
state_options = sorted(
    value for value in df["State Clean"].unique().tolist()
    if value != "Not Available"
)
domain_options = sorted(
    value for value in df["Domain Clean"].unique().tolist()
    if value != "Not Available"
)
incubator_options = sorted(
    value for value in df["Incubator Name"].unique().tolist()
    if value != "Not Available"
)
tier_options = sorted(
    value for value in df["Tier of the City"].unique().tolist()
    if value != "Not Available"
)
stage_options = sorted(
    value for value in df["Stage Clean"].unique().tolist()
    if value != "Not Available"
)

# Both EIR 1 and EIR 2 are selected by default.
selected_eir = st.sidebar.multiselect(
    "EIR Programme",
    eir_options,
    default=eir_options,
)
selected_states = st.sidebar.multiselect("State", state_options)
selected_domains = st.sidebar.multiselect("Domain", domain_options)
selected_incubators = st.sidebar.multiselect("Incubator", incubator_options)

# Two additional useful filters requested by user.
selected_tiers = st.sidebar.multiselect("City Tier", tier_options)
selected_stages = st.sidebar.multiselect("Current Stage", stage_options)

filtered = df[df["EIR Clean"].isin(selected_eir)].copy()

if selected_states:
    filtered = filtered[filtered["State Clean"].isin(selected_states)]
if selected_domains:
    filtered = filtered[filtered["Domain Clean"].isin(selected_domains)]
if selected_incubators:
    filtered = filtered[filtered["Incubator Name"].isin(selected_incubators)]
if selected_tiers:
    filtered = filtered[filtered["Tier of the City"].isin(selected_tiers)]
if selected_stages:
    filtered = filtered[filtered["Stage Clean"].isin(selected_stages)]

if filtered.empty:
    st.warning("Selected filters ke baad koi startup record nahi mila.")
    st.stop()


# ------------------------- KPI CALCULATIONS -------------------------
total_startups = len(filtered)
eir1_count = int((filtered["EIR Clean"] == "EIR 1").sum())
eir2_count = int((filtered["EIR Clean"] == "EIR 2").sum())
states_covered = filtered.loc[
    filtered["State Clean"] != "Not Available",
    "State Clean",
].nunique()
# Exact programme-level employment calculation requested:
team_at_onboarding = filtered["Team size at the time of onboarding"].sum()
current_team_size = filtered["Current Team Size"].sum()
employment_generated = current_team_size - team_at_onboarding

customers = filtered["Current Number of Customers / clients"].sum()

# Count based only on "Any Woman Team Member:" = Yes.
women_team_startups = int(filtered["Women Team Member"].sum())
women_team_pct = (women_team_startups / total_startups * 100) if total_startups else 0

# TRL improvement is counted only where both before and after TRL are available.
trl_comparable = filtered[
    filtered["TRL Before"].notna() & filtered["TRL After"].notna()
].copy()
trl_improved_startups = int((trl_comparable["TRL After"] > trl_comparable["TRL Before"]).sum())

patents_filed = filtered["No of Patent filed"].sum()
patents_granted = filtered["No of Patent granted"].sum()


# ------------------------- HEADER -------------------------
st.markdown(
    """
    <div class="hero">
        <div class="tag">GENESIS EiR • Portfolio Intelligence</div>
        <div class="hero-title">GENESIS EiR Dashboard</div>
        <div class="hero-sub">
            Combined EIR 1 + EIR 2 portfolio analysis.
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)


# ------------------------- TABS -------------------------
tab_exec, tab_geo, tab_sector, tab_incubator = st.tabs(
    ["📌 Executive View", "🗺️ Geography", "🏭 Sector & Tech", "🏢 Incubator"]
)


# ------------------------- EXECUTIVE VIEW -------------------------
with tab_exec:
    st.markdown('<div class="section-title">Programme Snapshot</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="section-note"></div>',
        unsafe_allow_html=True,
    )

    c1, c2, c3, c4, c5, c6 = st.columns(6)
    c1.metric("Total Startups", fmt(total_startups))
    c2.metric("Official Incubators", fmt(OFFICIAL_INCUBATORS))
    c3.metric("EIR 1 Startups", fmt(eir1_count))
    c4.metric("EIR 2 Startups", fmt(eir2_count))
    c5.metric("States Covered", fmt(states_covered))
    c6.metric("Employment Generated", fmt(employment_generated))

    c7, c8, c9, c10, c11 = st.columns(5)
    c7.metric("Customers / Clients", fmt(customers))
    c8.metric("Women Team Startups", fmt(women_team_startups))
    c9.metric("TRL Improved Startups", fmt(trl_improved_startups))
    c10.metric("Patents Filed", fmt(patents_filed))
    c11.metric("Patents Granted", fmt(patents_granted))

    state_counts = (
        filtered.loc[filtered["State Clean"] != "Not Available", "State Clean"]
        .value_counts()
    )
    domain_counts = (
        filtered.loc[filtered["Domain Clean"] != "Not Available", "Domain Clean"]
        .value_counts()
    )
    incubator_counts = filtered["Incubator Name"].value_counts()

    leading_state = state_counts.index[0] if not state_counts.empty else "—"
    leading_domain = domain_counts.index[0] if not domain_counts.empty else "—"
    leading_incubator = incubator_counts.index[0] if not incubator_counts.empty else "—"
    leading_incubator_count = int(incubator_counts.iloc[0]) if not incubator_counts.empty else 0

    st.markdown('<div class="section-title">Portfolio Highlights</div>', unsafe_allow_html=True)

    h1, h2, h3, h4 = st.columns(4)

    with h1:
        st.markdown(
            f'<div class="highlight-card"><div class="h-label">Leading State</div><div class="h-value">{leading_state}</div><div class="h-note">Highest startup concentration</div></div>',
            unsafe_allow_html=True,
        )

    with h2:
        st.markdown(
            f'<div class="highlight-card"><div class="h-label">Leading Domain</div><div class="h-value">{leading_domain}</div><div class="h-note">Most represented startup domain</div></div>',
            unsafe_allow_html=True,
        )

    with h3:
        st.markdown(
            f'<div class="highlight-card"><div class="h-label">Top Incubator</div><div class="h-value">{leading_incubator}</div><div class="h-note">{leading_incubator_count} startups across EIR 1 + EIR 2</div></div>',
            unsafe_allow_html=True,
        )

    with h4:
        st.markdown(
            f'<div class="highlight-card"><div class="h-label">Women Team Startups</div><div class="h-value">{women_team_startups:,}</div><div class="h-note">{women_team_pct:.1f}% startups marked Yes under Any Woman Team Member</div></div>',
            unsafe_allow_html=True,
        )

    st.markdown('<div class="section-title">Performance Overview</div>', unsafe_allow_html=True)

    left, right = st.columns(2)

    with left:
        state_summary = (
            filtered[filtered["State Clean"] != "Not Available"]
            .groupby("State Clean", as_index=False)
            .size()
            .rename(columns={"size": "Startups"})
            .sort_values("Startups", ascending=False)
            .head(12)
        )
        fig = px.bar(
            state_summary.sort_values("Startups"),
            x="Startups",
            y="State Clean",
            orientation="h",
            text_auto=True,
            title="Top States by Startup Count",
            color_discrete_sequence=["#1F5F8B"],
        )
        fig.update_xaxes(title=None)
        fig.update_yaxes(title=None)
        show_chart(fig, 390)

    with right:
        stage_summary = (
            filtered[filtered["Stage Clean"] != "Not Available"]
            .groupby("Stage Clean", as_index=False)
            .size()
            .rename(columns={"size": "Startups"})
            .sort_values("Startups", ascending=False)
        )
        fig = px.bar(
            stage_summary,
            x="Stage Clean",
            y="Startups",
            text_auto=True,
            title="Startup Development Stage Distribution",
            color_discrete_sequence=["#1F7A6C"],
        )
        fig.update_xaxes(title=None, tickangle=-25)
        fig.update_yaxes(title=None)
        show_chart(fig, 390)

    # Requested outcome and team-growth visuals only.
    st.markdown('<div class="section-title">Team, TRL and City Tier Insights</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="section-note">Employment is calculated as total Current Team Size minus total Team Size at Onboarding.</div>',
        unsafe_allow_html=True,
    )

    o1, o2, o3 = st.columns(3)

    with o1:
        tier_summary = (
            filtered[filtered["Tier of the City"] != "Not Available"]
            .groupby("Tier of the City", as_index=False)
            .size()
            .rename(columns={"size": "Startups"})
            .sort_values("Startups", ascending=False)
        )
        fig = px.pie(
            tier_summary,
            names="Tier of the City",
            values="Startups",
            hole=0.58,
            title="Startup Mix by City Tier",
            color_discrete_sequence=["#1F5F8B", "#1F7A6C", "#F59E0B"],
        )
        fig.update_traces(textinfo="percent+label")
        show_chart(fig, 360)

    with o2:
        trl_status = pd.DataFrame(
            {
                "TRL Status": [
                    "Improved",
                    "No Change",
                    "Declined",
                    "Not Reported",
                ],
                "Startups": [
                    int((trl_comparable["TRL After"] > trl_comparable["TRL Before"]).sum()),
                    int((trl_comparable["TRL After"] == trl_comparable["TRL Before"]).sum()),
                    int((trl_comparable["TRL After"] < trl_comparable["TRL Before"]).sum()),
                    int(total_startups - len(trl_comparable)),
                ],
            }
        )
        fig = px.bar(
            trl_status,
            x="TRL Status",
            y="Startups",
            text_auto=True,
            title="TRL Progress Based on Before vs After EIR",
            color_discrete_sequence=["#1F7A6C"],
        )
        fig.update_xaxes(title=None)
        fig.update_yaxes(title=None)
        show_chart(fig, 360)

    with o3:
        team_growth = pd.DataFrame(
            {
                "Team Measure": [
                    "At Onboarding",
                    "Current Team Size",
                    "Employment Generated",
                ],
                "Count": [
                    team_at_onboarding,
                    current_team_size,
                    employment_generated,
                ],
            }
        )
        fig = px.bar(
            team_growth,
            x="Team Measure",
            y="Count",
            text_auto=True,
            title="Team Growth and Employment Generated",
            color_discrete_sequence=["#1F5F8B"],
        )
        fig.update_xaxes(title=None)
        fig.update_yaxes(title=None)
        show_chart(fig, 360)


# ------------------------- GEOGRAPHY: MAP + RANKING ONLY -------------------------
with tab_geo:
    st.markdown('<div class="section-title">India Startup Coverage</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="section-note">Bubble size shows startup count. State Ranking combines EIR 1 + EIR 2.</div>',
        unsafe_allow_html=True,
    )

    geography = (
        filtered[filtered["State Clean"] != "Not Available"]
        .groupby("State Clean", as_index=False)
        .agg(
            Startups=("Startup Name", "size"),
            Employment_Generated=("Employment Generated", "sum"),
            Customers=("Current Number of Customers / clients", "sum"),
            Patents_Filed=("No of Patent filed", "sum"),
            Women_Team_Startups=("Women Team Member", "sum"),
        )
        .sort_values("Startups", ascending=False)
    )

    geography["Latitude"] = geography["State Clean"].map(
        lambda value: STATE_CENTROIDS.get(value, (None, None))[0]
    )
    geography["Longitude"] = geography["State Clean"].map(
        lambda value: STATE_CENTROIDS.get(value, (None, None))[1]
    )
    map_data = geography.dropna(subset=["Latitude", "Longitude"]).copy()

    map_col, ranking_col = st.columns([1.46, 0.54])

    with map_col:
        if map_data.empty:
            st.warning("Map ke liye matched state data available nahi hai.")
        else:
            fig = px.scatter_geo(
                map_data,
                lat="Latitude",
                lon="Longitude",
                size="Startups",
                color="Startups",
                hover_name="State Clean",
                hover_data={
                    "Latitude": False,
                    "Longitude": False,
                    "Startups": True,
                    "Employment_Generated": True,
                    "Customers": True,
                    "Patents_Filed": True,
                    "Women_Team_Startups": True,
                },
                projection="mercator",
                color_continuous_scale="Blues",
                size_max=52,
                title="India Coverage — Startups",
            )

            fig.update_geos(
                scope="asia",
                center=dict(lat=22.5, lon=80.5),
                projection_scale=3.15,
                showcountries=True,
                countrycolor="#C9D5E6",
                showcoastlines=True,
                coastlinecolor="#C9D5E6",
                showland=True,
                landcolor="#F5F8FC",
                showocean=True,
                oceancolor="#FFFFFF",
                lataxis_range=[6, 37],
                lonaxis_range=[67, 99],
            )
            fig.update_layout(
                height=640,
                margin=dict(l=0, r=0, t=50, b=0),
                paper_bgcolor="white",
                coloraxis_colorbar=dict(title="Startups"),
            )
            st.plotly_chart(fig, use_container_width=True, config=PLOT_CONFIG)

    with ranking_col:
        st.markdown("#### State Ranking")
        st.caption("Combined EIR 1 + EIR 2")
        ranking_table = geography[
            ["State Clean", "Startups", "Employment_Generated"]
        ].rename(
            columns={
                "State Clean": "State",
                "Employment_Generated": "Employment Generated",
            }
        )
        st.dataframe(
            ranking_table.head(14),
            use_container_width=True,
            hide_index=True,
            height=570,
        )


# ------------------------- SECTOR & TECH -------------------------
with tab_sector:
    st.markdown('<div class="section-title">Sector and Technology Overview</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="section-note">Domain, technology, startup stage and TRL progress insights from the combined portfolio.</div>',
        unsafe_allow_html=True,
    )

    # Visual 1 and 2
    row1_left, row1_right = st.columns(2)

    with row1_left:
        domain_summary = (
            filtered[filtered["Domain Clean"] != "Not Available"]
            .groupby("Domain Clean", as_index=False)
            .size()
            .rename(columns={"size": "Startups"})
            .sort_values("Startups", ascending=False)
            .head(12)
        )
        fig = px.bar(
            domain_summary,
            x="Domain Clean",
            y="Startups",
            text_auto=True,
            title="Top Domains by Startup Count",
            color_discrete_sequence=["#1F5F8B"],
        )
        fig.update_xaxes(title=None, tickangle=-25)
        fig.update_yaxes(title=None)
        show_chart(fig, 390)

    with row1_right:
        technology_summary = (
            filtered[filtered["Technology used by EIR / Founder"] != "Not Available"]
            .groupby("Technology used by EIR / Founder", as_index=False)
            .size()
            .rename(columns={"size": "Startups"})
            .sort_values("Startups", ascending=False)
            .head(12)
        )
        fig = px.bar(
            technology_summary.sort_values("Startups"),
            x="Startups",
            y="Technology used by EIR / Founder",
            orientation="h",
            text_auto=True,
            title="Top Technologies Used by Startups",
            color_discrete_sequence=["#1F7A6C"],
        )
        fig.update_xaxes(title=None)
        fig.update_yaxes(title=None)
        show_chart(fig, 390)


# ------------------------- INCUBATOR -------------------------
with tab_incubator:
    st.markdown('<div class="section-title">Incubator Performance</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="section-note">Counts are combined across EIR 1 and EIR 2 for every incubator.</div>',
        unsafe_allow_html=True,
    )

    incubators = (
        filtered[filtered["Incubator Name"] != "Not Available"]
        .groupby("Incubator Name", as_index=False)
        .agg(
            Startups=("Startup Name", "size"),
            Employment_Generated=("Employment Generated", "sum"),
            Customers=("Current Number of Customers / clients", "sum"),
            Patents_Filed=("No of Patent filed", "sum"),
            Women_Team_Startups=("Women Team Member", "sum"),
            TRL_Improved_Startups=(
                "TRL Before",
                lambda series: 0,
            ),
        )
    )

    # Accurate TRL-improved count at incubator level:
    trl_incubator = (
        filtered[
            filtered["TRL Before"].notna()
            & filtered["TRL After"].notna()
            & (filtered["TRL After"] > filtered["TRL Before"])
        ]
        .groupby("Incubator Name", as_index=False)
        .size()
        .rename(columns={"size": "TRL_Improved_Startups_Actual"})
    )
    incubators = incubators.drop(columns=["TRL_Improved_Startups"]).merge(
        trl_incubator,
        on="Incubator Name",
        how="left",
    )
    incubators["TRL_Improved_Startups_Actual"] = incubators["TRL_Improved_Startups_Actual"].fillna(0).astype(int)

    # Visual 1 and 2
    row1_left, row1_right = st.columns(2)

    with row1_left:
        chart_data = incubators.sort_values("Startups", ascending=False).head(15)
        fig = px.bar(
            chart_data.sort_values("Startups"),
            x="Startups",
            y="Incubator Name",
            orientation="h",
            text_auto=True,
            title="Top Incubators by Startup Count",
            color_discrete_sequence=["#1F5F8B"],
        )
        fig.update_xaxes(title=None)
        fig.update_yaxes(title=None)
        show_chart(fig, 440)

    with row1_right:
        chart_data = incubators.sort_values("Employment_Generated", ascending=False).head(15)
        fig = px.bar(
            chart_data.sort_values("Employment_Generated"),
            x="Employment_Generated",
            y="Incubator Name",
            orientation="h",
            text_auto=True,
            title="Top Incubators by Employment Generated",
            color_discrete_sequence=["#1F7A6C"],
        )
        fig.update_xaxes(title=None)
        fig.update_yaxes(title=None)
        show_chart(fig, 440)

    # Visual 3 and 4
    row2_left, row2_right = st.columns(2)

    with row2_left:
        chart_data = incubators.sort_values("Customers", ascending=False).head(15)
        fig = px.bar(
            chart_data.sort_values("Customers"),
            x="Customers",
            y="Incubator Name",
            orientation="h",
            text_auto=True,
            title="Top Incubators by Customers / Clients",
            color_discrete_sequence=["#F59E0B"],
        )
        fig.update_xaxes(title=None)
        fig.update_yaxes(title=None)
        show_chart(fig, 440)

    with row2_right:
        chart_data = incubators.sort_values("Patents_Filed", ascending=False).head(15)
        fig = px.bar(
            chart_data.sort_values("Patents_Filed"),
            x="Patents_Filed",
            y="Incubator Name",
            orientation="h",
            text_auto=True,
            title="Top Incubators by Patents Filed",
            color_discrete_sequence=["#7C3AED"],
        )
        fig.update_xaxes(title=None)
        fig.update_yaxes(title=None)
        show_chart(fig, 440)

    st.markdown("#### Complete Incubator Summary")
    st.dataframe(
        incubators.rename(
            columns={
                "Employment_Generated": "Employment Generated",
                "Patents_Filed": "Patents Filed",
                "Women_Team_Startups": "Women Team Startups",
                "TRL_Improved_Startups_Actual": "TRL Improved Startups",
            }
        ).sort_values(["Startups", "Employment Generated"], ascending=False),
        use_container_width=True,
        hide_index=True,
        height=440,
    )
