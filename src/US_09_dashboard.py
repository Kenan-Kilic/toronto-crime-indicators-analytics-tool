# US-09 — Build Interactive Dashboard (v3 — Final / Streamlit Cloud Ready)
# Integrates: US-10 filters (live sidebar widgets) + US-13 Folium hotspot map
#
# ── How to run ────────────────────────────────────────────────────────────────
# LOCAL / Colab:
#   streamlit run US_09_dashboard.py
#
# STREAMLIT CLOUD (share.streamlit.io):
#   1. Push all US_*.py files + requirements.txt + cleaned_toronto_crime.csv
#      (or adjust DATA_PATH below) to your GitHub repo.
#   2. Connect repo on share.streamlit.io → deploy.
#
# ── Folder layout expected ────────────────────────────────────────────────────
#   repo/
#     US_09_dashboard.py          ← this file
#     US_10_dashboard_filters.py
#     US_13_hotspot_map.py
#     data/
#       cleaned_toronto_crime.csv
#       crime_overview_kpis.csv
#       top_neighbourhoods.csv
#       crime_type_distribution.csv
#       peak_crime_periods.csv
#       division_activity.csv
#       yoy_crime_trend.csv           (optional)
#     outputs/
#       toronto_hotspot_map.html      (pre-generated, OR built at runtime)
#
# requirements.txt must contain:
#   streamlit
#   pandas
#   matplotlib
#   folium
# ─────────────────────────────────────────────────────────────────────────────

import os
import sys
import streamlit as st
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker

# ── Path setup (works locally, in Colab, and on Streamlit Cloud) ──────────────
_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

# Google Drive path (Colab only — ignored on Streamlit Cloud)
_COLAB_BASE = "/content/drive/MyDrive/Colab Notebooks"
# Streamlit Cloud / local path
_LOCAL_DATA = os.path.join(_HERE, "data")
# Auto-select base
DATA_BASE = _COLAB_BASE if os.path.exists(_COLAB_BASE) else _LOCAL_DATA

# ── Google Drive auto-download (Streamlit Cloud only) ────────────────────────
# Downloads cleaned_toronto_crime.csv from Google Drive if not present locally.
# File ID from: https://drive.google.com/file/d/19KRbMioffzNXTYF8tOci2KALpW3DaypW/view
_GDRIVE_FILE_ID  = "19KRbMioffzNXTYF8tOci2KALpW3DaypW"
_CLEANED_CSV     = os.path.join(_LOCAL_DATA, "cleaned_toronto_crime.csv")
_IS_STREAMLIT_CLOUD = not os.path.exists(_COLAB_BASE)

@st.cache_resource(show_spinner=False)
def _download_cleaned_csv():
    """Download cleaned_toronto_crime.csv from Google Drive using gdown."""
    if os.path.exists(_CLEANED_CSV):
        return True
    os.makedirs(_LOCAL_DATA, exist_ok=True)
    try:
        import gdown
        with st.spinner("⬇️ Downloading dataset from Google Drive (~167 MB)... please wait."):
            gdown.download(id=_GDRIVE_FILE_ID, output=_CLEANED_CSV, quiet=False)
        return True
    except Exception as e:
        st.error(f"Failed to download dataset: {e}")
        return False

if _IS_STREAMLIT_CLOUD:
    _download_cleaned_csv()

# ── Import project modules ────────────────────────────────────────────────────
try:
    from US_10_dashboard_filters import get_filter_options, apply_filters, filter_summary
    _FILTERS_AVAILABLE = True
except ImportError:
    _FILTERS_AVAILABLE = False

try:
    from US_13_hotspot_map import build_hotspot_map
    _MAP_MODULE_AVAILABLE = True
except ImportError:
    _MAP_MODULE_AVAILABLE = False

# ─────────────────────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────────────────────

def _p(filename: str) -> str:
    """Resolve a data file path."""
    return os.path.join(DATA_BASE, filename)


@st.cache_data(show_spinner=False)
def load_csv(path: str) -> pd.DataFrame | None:
    if os.path.exists(path):
        return pd.read_csv(path, low_memory=False)
    return None


def _kpi_card(col, label: str, value, delta=None):
    col.metric(label, value, delta)


def _hbar(df, x_col, y_col, title, xlabel="Crime Count",
          highlight_top=True, color="#2980b9", figsize=(10, 6)):
    fig, ax = plt.subplots(figsize=figsize)
    colors = (["#c0392b"] + [color] * (len(df) - 1)) if highlight_top else [color] * len(df)
    bars = ax.barh(df[x_col].astype(str), df[y_col], color=colors, edgecolor="white", linewidth=0.4)
    ax.invert_yaxis()
    ax.set_xlabel(xlabel, fontsize=10)
    ax.set_title(title, fontsize=13, fontweight="bold", pad=10)
    ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f"{int(v):,}"))
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.grid(axis="x", alpha=0.25, linestyle="--")
    for bar in bars:
        w = bar.get_width()
        ax.text(w + df[y_col].max() * 0.005, bar.get_y() + bar.get_height() / 2,
                f"{int(w):,}", va="center", fontsize=8, color="#444")
    plt.tight_layout()
    return fig


# ─────────────────────────────────────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Toronto Crime Analytics",
    page_icon="🚔",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS — subtle polish
st.markdown("""
<style>
    [data-testid="stSidebar"] { background-color: #1a1f2e; }
    [data-testid="stSidebar"] * { color: #e8eaf0 !important; }
    [data-testid="stSidebar"] .stSelectbox label,
    [data-testid="stSidebar"] .stSlider label { color: #adb5c8 !important; font-size: 0.82rem; }
    div[data-testid="metric-container"] {
        background: #f7f9fc; border: 1px solid #e0e5ef;
        border-radius: 10px; padding: 12px 18px;
    }
    .block-container { padding-top: 1.5rem; }
    h1 { color: #1a1f2e; }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# LOAD CLEANED DATASET (needed for live filters)
# ─────────────────────────────────────────────────────────────────────────────
cleaned_df = load_csv(_p("cleaned_toronto_crime.csv"))

# Normalize column names — strip whitespace and fix encoding issues
if cleaned_df is not None:
    cleaned_df.columns = cleaned_df.columns.str.strip()
    # Rename common variants to expected names
    col_renames = {
        "NEIGHBOURHOOD_158 ": "NEIGHBOURHOOD_158",
        "NEIGHBOURHOOD158": "NEIGHBOURHOOD_158",
        "neighbourhood_158": "NEIGHBOURHOOD_158",
    }
    cleaned_df = cleaned_df.rename(columns=col_renames)

# ─────────────────────────────────────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────────────────────────────────────
st.sidebar.image(
    "https://upload.wikimedia.org/wikipedia/commons/thumb/9/9a/Flag_of_Toronto.svg/240px-Flag_of_Toronto.svg.png",
    width=90,
)
st.sidebar.title("🚔 Toronto Crime\nAnalytics Tool")
st.sidebar.caption("Sprint 2 — Final Dashboard")
st.sidebar.divider()

PAGE_LABELS = {
    "📊 Overview":            "Overview",
    "🏘️ Neighbourhoods":      "Neighbourhoods",
    "🔎 Crime Types":         "Crime Types",
    "⏰ Peak Periods":        "Peak Periods",
    "🚓 Police Divisions":    "Divisions",
    "🗺️ Hotspot Map":         "Hotspot Map",
    "📈 Year-over-Year Trend":"YoY Trend",
}
page_icon = st.sidebar.radio("Navigate", list(PAGE_LABELS.keys()))
page = PAGE_LABELS[page_icon]

# ── US-10: Global Filters (sidebar) ──────────────────────────────────────────
st.sidebar.divider()
st.sidebar.subheader("🔧 Global Filters (US-10)")

if cleaned_df is not None and _FILTERS_AVAILABLE:
    # Debug: show actual columns if NEIGHBOURHOOD_158 missing
    required_cols = ["NEIGHBOURHOOD_158", "OFFENCE", "OCC_YEAR", "DIVISION"]
    missing_cols = [c for c in required_cols if c not in cleaned_df.columns]
    if missing_cols:
        st.sidebar.error(f"Missing columns: {missing_cols}")
        st.sidebar.write("Available:", list(cleaned_df.columns[:10]))
        filtered_df = cleaned_df
        _FILTERS_ACTIVE = False
    else:
        opts = get_filter_options(cleaned_df)

    sel_neighbourhood = st.sidebar.selectbox(
        "Neighbourhood", ["All"] + opts["neighbourhoods"], key="nb"
    )
    sel_offence = st.sidebar.selectbox(
        "Offence Type", ["All"] + opts["offence_types"], key="off"
    )
    year_list = [int(y) for y in opts["years"]]
    sel_year = st.sidebar.select_slider(
        "Year", options=["All"] + year_list, value="All", key="yr"
    )
    sel_division = st.sidebar.selectbox(
        "Division", ["All"] + opts["divisions"], key="div"
    )

    year_val = None if sel_year == "All" else int(sel_year)
    filtered_df = apply_filters(
        cleaned_df,
        neighbourhood=sel_neighbourhood,
        offence_type=sel_offence,
        year=year_val,
        division=sel_division,
    )

    fsum = filter_summary(filtered_df)
    st.sidebar.caption(
        f"✅ **{fsum['total_crimes']:,}** records match  \n"
        f"Offences: {fsum['unique_offences']}  |  "
        f"Hoods: {fsum['unique_neighbourhoods']}"
    )
    _FILTERS_ACTIVE = True
else:
    filtered_df = cleaned_df
    _FILTERS_ACTIVE = False
    if not _FILTERS_AVAILABLE:
        st.sidebar.warning("US_10_dashboard_filters.py not found.")
    elif cleaned_df is None:
        st.sidebar.warning("cleaned_toronto_crime.csv not found — filters disabled.")

st.sidebar.divider()
st.sidebar.caption("© 2026 Toronto Crime Analytics Team")

# ─────────────────────────────────────────────────────────────────────────────
# OVERVIEW PAGE
# ─────────────────────────────────────────────────────────────────────────────
if page == "Overview":
    st.title("📊 Toronto Crime Risk Overview")
    st.caption("US-03 · KPI summary derived from cleaned dataset")

    kpi_df = load_csv(_p("crime_overview_kpis.csv"))

    # Live filtered KPIs if dataset loaded
    if filtered_df is not None and not filtered_df.empty:
        offences  = filtered_df["OFFENCE"].dropna()
        hoods     = filtered_df["NEIGHBOURHOOD_158"].dropna()
        live_kpis = {
            "total_crimes":                      len(filtered_df),
            "most_common_offence":               offences.mode().iloc[0] if not offences.empty else "N/A",
            "highest_crime_neighbourhood":        hoods.value_counts().idxmax() if not hoods.empty else "N/A",
            "total_neighbourhoods":              int(hoods.nunique()),
            "total_offence_types":               int(offences.nunique()),
        }
        c1, c2, c3, c4, c5 = st.columns(5)
        _kpi_card(c1, "Total Crimes",       f"{live_kpis['total_crimes']:,}")
        _kpi_card(c2, "Most Common Offence",live_kpis["most_common_offence"])
        _kpi_card(c3, "Highest Crime Area", live_kpis["highest_crime_neighbourhood"])
        _kpi_card(c4, "Unique Hoods",       live_kpis["total_neighbourhoods"])
        _kpi_card(c5, "Offence Types",      live_kpis["total_offence_types"])
        st.caption("*KPIs update live with sidebar filters.*")

    elif kpi_df is not None:
        row = kpi_df.iloc[0]
        c1, c2, c3, c4 = st.columns(4)
        _kpi_card(c1, "Total Crimes",        f"{int(row['total_crimes']):,}")
        _kpi_card(c2, "Most Common Offence", row["most_common_offence"])
        _kpi_card(c3, "Highest Crime Area",  row["highest_crime_neighbourhood"])
        _kpi_card(c4, "Total Neighbourhoods",int(row["total_neighbourhoods"]))
    else:
        st.warning("Run pipeline first to generate crime_overview_kpis.csv")
        st.stop()

    # Crime over time mini-chart
    if filtered_df is not None and "OCC_YEAR" in filtered_df.columns:
        st.divider()
        st.subheader("Crime Count by Year")
        yr_counts = (
            filtered_df["OCC_YEAR"].dropna().astype(int)
            .value_counts().sort_index().reset_index()
        )
        yr_counts.columns = ["Year", "Count"]
        fig, ax = plt.subplots(figsize=(10, 3.5))
        ax.fill_between(yr_counts["Year"], yr_counts["Count"],
                        alpha=0.18, color="#2980b9")
        ax.plot(yr_counts["Year"], yr_counts["Count"],
                marker="o", linewidth=2, color="#2980b9")
        ax.set_title("Annual Crime Count (filtered)", fontsize=12)
        ax.grid(True, linestyle="--", alpha=0.3)
        ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f"{int(v):,}"))
        plt.tight_layout()
        st.pyplot(fig)
        plt.close(fig)

    if kpi_df is not None:
        with st.expander("📋 Full KPI table (from pipeline CSV)"):
            st.dataframe(kpi_df, use_container_width=True)

# ─────────────────────────────────────────────────────────────────────────────
# NEIGHBOURHOODS PAGE
# ─────────────────────────────────────────────────────────────────────────────
elif page == "Neighbourhoods":
    st.title("🏘️ High-Risk Neighbourhoods")
    st.caption("US-04 · Ranking updates with sidebar filters")

    if filtered_df is not None and not filtered_df.empty and "NEIGHBOURHOOD_158" in filtered_df.columns:
        top_n = st.slider("Show top N neighbourhoods", 5, 30, 10, key="top_nb")
        nb_live = (
            filtered_df["NEIGHBOURHOOD_158"].dropna()
            .value_counts().head(top_n).reset_index()
        )
        nb_live.columns = ["neighbourhood", "crime_count"]
        nb_live["rank"] = range(1, len(nb_live) + 1)

        col1, col2 = st.columns([1, 2])
        with col1:
            st.dataframe(nb_live, use_container_width=True, height=420)
        with col2:
            fig = _hbar(nb_live, "neighbourhood", "crime_count",
                        f"Top {top_n} High-Risk Neighbourhoods", figsize=(9, max(4, top_n * 0.42)))
            st.pyplot(fig)
            plt.close(fig)
    else:
        nb_df = load_csv(_p("top_neighbourhoods.csv"))
        if nb_df is not None:
            col1, col2 = st.columns([1, 2])
            with col1:
                st.dataframe(nb_df, use_container_width=True)
            with col2:
                fig = _hbar(nb_df, "neighbourhood", "crime_count",
                            "Top High-Risk Neighbourhoods")
                st.pyplot(fig); plt.close(fig)
        else:
            st.warning("Run pipeline first to generate top_neighbourhoods.csv")

# ─────────────────────────────────────────────────────────────────────────────
# CRIME TYPES PAGE
# ─────────────────────────────────────────────────────────────────────────────
elif page == "Crime Types":
    st.title("🔎 Crime Type Distribution")
    st.caption("US-06 · Distribution of offences — updates with sidebar filters")

    if filtered_df is not None and not filtered_df.empty and "OFFENCE" in filtered_df.columns:
        top_n = st.slider("Show top N offence types", 5, 30, 15, key="top_off")
        off_live = (
            filtered_df["OFFENCE"].dropna()
            .value_counts().head(top_n).reset_index()
        )
        off_live.columns = ["offence", "crime_count"]
        off_live["pct"] = (off_live["crime_count"] / off_live["crime_count"].sum() * 100).round(2)

        tab1, tab2 = st.tabs(["Bar Chart", "Data Table"])
        with tab1:
            fig = _hbar(off_live, "offence", "crime_count",
                        f"Top {top_n} Offence Types",
                        figsize=(10, max(5, top_n * 0.38)))
            st.pyplot(fig); plt.close(fig)
        with tab2:
            st.dataframe(off_live, use_container_width=True)

        # MCI Category pie if available
        if "MCI_CATEGORY" in filtered_df.columns:
            st.divider()
            st.subheader("MCI Crime Category Breakdown")
            cat_counts = (
                filtered_df["MCI_CATEGORY"].dropna()
                .value_counts().reset_index()
            )
            cat_counts.columns = ["category", "count"]
            fig2, ax2 = plt.subplots(figsize=(7, 7))
            colors = ["#c0392b","#2980b9","#27ae60","#e67e22","#8e44ad","#16a085","#7f8c8d"]
            ax2.pie(cat_counts["count"], labels=cat_counts["category"],
                    autopct="%1.1f%%", startangle=140,
                    colors=colors[:len(cat_counts)],
                    wedgeprops={"edgecolor": "white", "linewidth": 1.5})
            ax2.set_title("MCI Category Distribution", fontsize=13, fontweight="bold")
            plt.tight_layout()
            st.pyplot(fig2); plt.close(fig2)
    else:
        dist_df = load_csv(_p("crime_type_distribution.csv"))
        if dist_df is not None:
            fig = _hbar(dist_df, "offence", "crime_count", "Top Offence Types")
            st.pyplot(fig); plt.close(fig)
            st.dataframe(dist_df, use_container_width=True)
        else:
            st.warning("Run US-06 first to generate crime_type_distribution.csv")

# ─────────────────────────────────────────────────────────────────────────────
# PEAK PERIODS PAGE
# ─────────────────────────────────────────────────────────────────────────────
elif page == "Peak Periods":
    st.title("⏰ Peak Crime Periods")
    st.caption("US-05 · Hourly, monthly, and yearly crime patterns")

    # Live charts from filtered_df
    if filtered_df is not None and not filtered_df.empty:
        tab_h, tab_m, tab_y = st.tabs(["By Hour", "By Month", "By Year"])

        with tab_h:
            if "OCC_HOUR" in filtered_df.columns:
                h_counts = (
                    filtered_df["OCC_HOUR"].dropna().astype(int)
                    .value_counts().sort_index().reset_index()
                )
                h_counts.columns = ["hour", "crime_count"]
                h_counts["is_peak"] = h_counts["crime_count"] == h_counts["crime_count"].max()
                fig, ax = plt.subplots(figsize=(12, 4))
                colors = ["#c0392b" if p else "#2980b9" for p in h_counts["is_peak"]]
                ax.bar(h_counts["hour"], h_counts["crime_count"], color=colors, width=0.85)
                ax.set_xlabel("Hour of Day"); ax.set_ylabel("Crime Count")
                ax.set_title("Crime Count by Hour  (red = peak)", fontweight="bold")
                ax.set_xticks(range(24))
                ax.grid(axis="y", alpha=0.25, linestyle="--")
                plt.tight_layout()
                st.pyplot(fig); plt.close(fig)
            else:
                st.info("OCC_HOUR column not available.")

        with tab_m:
            if "OCC_MONTH" in filtered_df.columns:
                month_order = ["January","February","March","April","May","June",
                               "July","August","September","October","November","December"]
                m_counts = filtered_df["OCC_MONTH"].dropna().astype(str).value_counts().reset_index()
                m_counts.columns = ["month", "crime_count"]
                # Try to sort by calendar order
                try:
                    m_counts["month"] = pd.Categorical(m_counts["month"], categories=month_order, ordered=True)
                    m_counts = m_counts.sort_values("month")
                except Exception:
                    m_counts = m_counts.sort_values("crime_count", ascending=False)
                fig, ax = plt.subplots(figsize=(12, 4))
                ax.bar(m_counts["month"].astype(str), m_counts["crime_count"],
                       color="#2980b9", edgecolor="white")
                ax.set_title("Crime Count by Month", fontweight="bold")
                ax.set_ylabel("Crime Count")
                plt.xticks(rotation=30, ha="right")
                ax.grid(axis="y", alpha=0.25, linestyle="--")
                plt.tight_layout()
                st.pyplot(fig); plt.close(fig)
            else:
                st.info("OCC_MONTH column not available.")

        with tab_y:
            if "OCC_YEAR" in filtered_df.columns:
                y_counts = (
                    filtered_df["OCC_YEAR"].dropna().astype(int)
                    .value_counts().sort_index().reset_index()
                )
                y_counts.columns = ["year", "crime_count"]
                fig, ax = plt.subplots(figsize=(12, 4))
                ax.plot(y_counts["year"], y_counts["crime_count"],
                        marker="o", linewidth=2, color="#2980b9")
                ax.fill_between(y_counts["year"], y_counts["crime_count"], alpha=0.15, color="#2980b9")
                ax.set_title("Annual Crime Count Trend", fontweight="bold")
                ax.set_ylabel("Crime Count"); ax.set_xlabel("Year")
                ax.grid(True, linestyle="--", alpha=0.3)
                plt.tight_layout()
                st.pyplot(fig); plt.close(fig)
            else:
                st.info("OCC_YEAR column not available.")
    else:
        peak_df = load_csv(_p("peak_crime_periods.csv"))
        if peak_df is not None:
            tabs = st.tabs(["Hourly", "Monthly", "Yearly"])
            for tab, period in zip(tabs, ["hourly", "monthly", "yearly"]):
                with tab:
                    sub = peak_df[peak_df["period_type"] == period].copy()
                    if not sub.empty:
                        st.dataframe(sub, use_container_width=True)
        else:
            st.warning("Run pipeline first to generate peak_crime_periods.csv")

# ─────────────────────────────────────────────────────────────────────────────
# DIVISIONS PAGE
# ─────────────────────────────────────────────────────────────────────────────
elif page == "Divisions":
    st.title("🚓 Police Division Activity")
    st.caption("US-08 · Crime volume per TPS division — updates with sidebar filters")

    if filtered_df is not None and not filtered_df.empty and "DIVISION" in filtered_df.columns:
        div_live = (
            filtered_df["DIVISION"].dropna()
            .value_counts().reset_index()
        )
        div_live.columns = ["division", "crime_count"]
        div_live["pct"] = (div_live["crime_count"] / div_live["crime_count"].sum() * 100).round(2)
        div_live["rank"] = range(1, len(div_live) + 1)

        col1, col2 = st.columns([1, 2])
        with col1:
            st.dataframe(div_live, use_container_width=True)
        with col2:
            fig = _hbar(div_live, "division", "crime_count",
                        "Crime Count by Toronto Police Division")
            st.pyplot(fig); plt.close(fig)

        # Pie chart
        with st.expander("🥧 Division share (pie chart)"):
            top10 = div_live.head(10).copy()
            other = div_live.iloc[10:]["crime_count"].sum()
            if other > 0:
                top10 = pd.concat([top10, pd.DataFrame([{
                    "division":"Other","crime_count":other,"pct":0,"rank":0
                }])], ignore_index=True)
            fig2, ax2 = plt.subplots(figsize=(7, 7))
            ax2.pie(top10["crime_count"], labels=top10["division"],
                    autopct="%1.1f%%", startangle=140)
            ax2.set_title("Crime Share by Division (Top 10)")
            plt.tight_layout()
            st.pyplot(fig2); plt.close(fig2)
    else:
        div_df = load_csv(_p("division_activity.csv"))
        if div_df is not None:
            col1, col2 = st.columns([1, 2])
            with col1:
                st.dataframe(div_df, use_container_width=True)
            with col2:
                fig = _hbar(div_df, "division", "crime_count", "Crime by Division")
                st.pyplot(fig); plt.close(fig)
        else:
            st.warning("Run US-08 first to generate division_activity.csv")

# ─────────────────────────────────────────────────────────────────────────────
# HOTSPOT MAP PAGE  (US-13)
# ─────────────────────────────────────────────────────────────────────────────
elif page == "Hotspot Map":
    st.title("🗺️ Crime Hotspot Map")
    st.caption("US-13 · Interactive Folium MarkerCluster map")

    html_path = _p("toronto_hotspot_map.html")
    # Also check outputs/ subfolder
    alt_path  = os.path.join(_HERE, "outputs", "toronto_hotspot_map.html")

    # Controls
    col_a, col_b, col_c = st.columns(3)
    sample_size = col_a.slider("Sample size (markers)", 500, 8000, 3000, 500, key="map_sample")
    top_n_hoods = col_b.slider("Top N neighbourhoods", 5, 20, 10, key="map_hoods")
    regen       = col_c.button("🔄 Regenerate map", help="Rebuild map with current filters & settings")

    map_df = filtered_df if (filtered_df is not None and not filtered_df.empty) else load_csv(_p("cleaned_toronto_crime.csv"))

    # Generate / load map
    if regen or (not os.path.exists(html_path) and not os.path.exists(alt_path)):
        if map_df is not None and _MAP_MODULE_AVAILABLE:
            with st.spinner("Building Folium map..."):
                os.makedirs(os.path.dirname(html_path) if os.path.dirname(html_path) else ".", exist_ok=True)
                build_hotspot_map(
                    map_df,
                    output_html=html_path,
                    sample_size=sample_size,
                    top_n_hoods=top_n_hoods,
                )
            st.success(f"Map saved → {html_path}")
        elif not _MAP_MODULE_AVAILABLE:
            st.error("US_13_hotspot_map.py not found in the same directory.")
        else:
            st.error("cleaned_toronto_crime.csv not found — cannot build map.")

    # Render
    resolved_path = html_path if os.path.exists(html_path) else (alt_path if os.path.exists(alt_path) else None)

    if resolved_path:
        with open(resolved_path, "r", encoding="utf-8") as f:
            map_html = f.read()
        st.components.v1.html(map_html, height=620, scrolling=False)
        st.caption(
            f"Showing up to **{sample_size:,}** crime markers across the top "
            f"**{top_n_hoods}** neighbourhoods. "
            "Click markers to see offence details. Zoom / pan freely."
        )

        # Quick stats below map
        if map_df is not None and "NEIGHBOURHOOD_158" in map_df.columns:
            st.divider()
            st.subheader("Top Neighbourhood Crime Counts")
            top_nb = (
                map_df["NEIGHBOURHOOD_158"].dropna()
                .value_counts().head(top_n_hoods).reset_index()
            )
            top_nb.columns = ["Neighbourhood", "Crime Count"]
            st.dataframe(top_nb, use_container_width=True, height=320)
    else:
        st.info(
            "No pre-generated map found.  \n"
            "Click **🔄 Regenerate map** above to build it from the loaded dataset.",
            icon="ℹ️",
        )

# ─────────────────────────────────────────────────────────────────────────────
# YEAR-OVER-YEAR TREND PAGE  (US-14)
# ─────────────────────────────────────────────────────────────────────────────
elif page == "YoY Trend":
    st.title("📈 Year-over-Year Crime Trend")
    st.caption("US-14 · Annual crime counts with % change — updates with sidebar filters")

    yoy_df = load_csv(_p("yoy_crime_trend.csv"))

    # Build live if filtered_df available
    if filtered_df is not None and not filtered_df.empty and "OCC_YEAR" in filtered_df.columns:
        trend = (
            filtered_df["OCC_YEAR"].dropna().astype(int)
            .value_counts().sort_index().reset_index()
        )
        trend.columns = ["year", "crime_count"]
        trend["pct_change"] = trend["crime_count"].pct_change() * 100
        trend["pct_change"] = trend["pct_change"].round(2)
        trend["is_peak"]   = trend["crime_count"] == trend["crime_count"].max()
        trend["is_lowest"] = trend["crime_count"] == trend["crime_count"].min()

        # Line chart
        fig, ax = plt.subplots(figsize=(12, 5))
        ax.plot(trend["year"], trend["crime_count"], marker="o", linewidth=2,
                color="#2980b9", label="Annual Crime Count")
        peak = trend[trend["is_peak"]]
        low  = trend[trend["is_lowest"]]
        ax.scatter(peak["year"], peak["crime_count"], color="#c0392b", s=120, zorder=5, label="Peak Year")
        ax.scatter(low["year"],  low["crime_count"],  color="#27ae60", s=120, zorder=5, label="Lowest Year")
        for _, r in peak.iterrows():
            ax.annotate(f"Peak {int(r['year'])}\n({int(r['crime_count']):,})",
                        xy=(r["year"], r["crime_count"]), xytext=(8, 8),
                        textcoords="offset points", color="#c0392b", fontsize=9, fontweight="bold")
        for _, r in low.iterrows():
            ax.annotate(f"Lowest {int(r['year'])}\n({int(r['crime_count']):,})",
                        xy=(r["year"], r["crime_count"]), xytext=(8, -22),
                        textcoords="offset points", color="#27ae60", fontsize=9, fontweight="bold")
        ax.set_xlabel("Year"); ax.set_ylabel("Crime Count")
        ax.set_title("Year-over-Year Crime Trend in Toronto", fontweight="bold", fontsize=13)
        ax.legend(); ax.grid(True, linestyle="--", alpha=0.3)
        ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f"{int(v):,}"))
        plt.tight_layout()
        st.pyplot(fig); plt.close(fig)

        # % change bar chart
        st.subheader("Year-over-Year % Change")
        df_pct = trend.dropna(subset=["pct_change"])
        colors = ["#c0392b" if v > 0 else "#27ae60" for v in df_pct["pct_change"]]
        fig2, ax2 = plt.subplots(figsize=(12, 4))
        ax2.bar(df_pct["year"], df_pct["pct_change"], color=colors, edgecolor="white")
        ax2.axhline(0, color="black", linewidth=0.8, linestyle="--")
        ax2.set_title("YoY % Change  (red = increase, green = decrease)", fontweight="bold")
        ax2.set_xlabel("Year"); ax2.set_ylabel("% Change")
        ax2.grid(axis="y", alpha=0.25, linestyle="--")
        plt.tight_layout()
        st.pyplot(fig2); plt.close(fig2)

        with st.expander("📋 Data table"):
            st.dataframe(trend, use_container_width=True)

    elif yoy_df is not None:
        st.dataframe(yoy_df, use_container_width=True)
    else:
        st.warning("Run US-14 (compute_yoy_trend) first, or load cleaned_toronto_crime.csv.")
