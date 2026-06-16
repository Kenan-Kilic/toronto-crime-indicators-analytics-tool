# Toronto Crime Analytics — Integrated Dashboard v7
# US-01 through US-15 Pipeline + Interactive Dashboard
#
# ── How to run ────────────────────────────────────────────────────────────────
# LOCAL:
#   pip install streamlit pandas matplotlib folium gdown numpy
#   streamlit run toronto_crime_dashboard.py
#
# STREAMLIT CLOUD (share.streamlit.io):
#   Push only this file + requirements.txt to your GitHub repo and deploy.
#   No other US_*.py files needed — all pipeline logic is embedded here.
#
# ── requirements.txt contents ─────────────────────────────────────────────────
#   streamlit>=1.32
#   pandas>=2.0
#   matplotlib>=3.8
#   folium>=0.15
#   gdown>=5.0
#   numpy>=1.26
# ─────────────────────────────────────────────────────────────────────────────

import os, sys, io, traceback
import streamlit as st
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker

# ── Page config (must be first Streamlit call) ────────────────────────────────
st.set_page_config(
    page_title="Toronto Crime Analytics",
    page_icon="🚔",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ────────────────────────────────────────────────────────────────
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
    .pipeline-log {
        background: #0d1117; color: #58a6ff;
        font-family: monospace; font-size: 0.8rem;
        padding: 12px; border-radius: 8px;
        max-height: 320px; overflow-y: auto;
    }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# PATHS & SESSION STATE INIT
# ─────────────────────────────────────────────────────────────────────────────
_HERE     = os.path.dirname(os.path.abspath(__file__)) if "__file__" in dir() else os.getcwd()
_DATA_DIR = os.path.join(_HERE, "data")
_OUT_DIR  = os.path.join(_HERE, "outputs")
os.makedirs(_DATA_DIR, exist_ok=True)
os.makedirs(_OUT_DIR,  exist_ok=True)

_GDRIVE_RAW_ID    = "19KRbMioffzNXTYF8tOci2KALpW3DaypW"
_RAW_CSV_NAME     = "Toronto_Crime_Indicators.csv"
_CLEANED_CSV_NAME = "cleaned_toronto_crime.csv"

def _dp(fname): return os.path.join(_DATA_DIR, fname)
def _op(fname): return os.path.join(_OUT_DIR,  fname)

for _k, _v in [
    ("raw_df",       None),
    ("cleaned_df",   None),
    ("pipeline_ran", False),
    ("pipeline_log", []),
]:
    if _k not in st.session_state:
        st.session_state[_k] = _v

# ─────────────────────────────────────────────────────────────────────────────
# GENERAL HELPERS
# ─────────────────────────────────────────────────────────────────────────────

@st.cache_data(show_spinner=False)
def load_csv(path):
    if os.path.exists(path):
        return pd.read_csv(path, low_memory=False)
    return None

def _kpi_card(col, label, value, delta=None):
    col.metric(label, value, delta)

def _hbar(df, x_col, y_col, title, xlabel="Crime Count",
          highlight_top=True, color="#2980b9", figsize=(10, 6)):
    fig, ax = plt.subplots(figsize=figsize)
    colors = (["#c0392b"] + [color] * (len(df) - 1)) if highlight_top else [color] * len(df)
    ax.barh(df[x_col].astype(str), df[y_col], color=colors, edgecolor="white", linewidth=0.4)
    ax.invert_yaxis()
    ax.set_xlabel(xlabel, fontsize=10)
    ax.set_title(title, fontsize=13, fontweight="bold", pad=10)
    ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f"{int(v):,}"))
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.grid(axis="x", alpha=0.25, linestyle="--")
    for bar in ax.patches:
        w = bar.get_width()
        ax.text(w + df[y_col].max() * 0.005, bar.get_y() + bar.get_height() / 2,
                f"{int(w):,}", va="center", fontsize=8, color="#444")
    plt.tight_layout()
    return fig

def _log(msg, level="info"):
    icon = {"info": "ℹ️", "ok": "✅", "err": "❌", "run": "⏳", "warn": "⚠️"}.get(level, "•")
    st.session_state.pipeline_log.append(f"{icon}  {msg}")

# ─────────────────────────────────────────────────────────────────────────────
# EMBEDDED PIPELINE FUNCTIONS  (replaces all US_*.py module imports)
# ─────────────────────────────────────────────────────────────────────────────

# ── US-02: Clean dataset ──────────────────────────────────────────────────────
def _us02_clean(raw_df):
    df = raw_df.copy()
    df.columns = df.columns.str.strip()

    # Normalise OCC_DOW to full weekday names
    dow_map = {
        "mon": "Monday",  "tue": "Tuesday", "wed": "Wednesday",
        "thu": "Thursday","fri": "Friday",  "sat": "Saturday", "sun": "Sunday",
        "0": "Monday", "1": "Tuesday", "2": "Wednesday", "3": "Thursday",
        "4": "Friday",  "5": "Saturday", "6": "Sunday",
    }
    if "OCC_DOW" in df.columns:
        def _map_dow(x):
            s = str(x).strip()
            if s.lower() in ("nan", "none", ""):
                return np.nan
            key = s[:3].lower()
            return dow_map.get(key, s.capitalize())
        df["OCC_DOW"] = df["OCC_DOW"].map(_map_dow)

    # Derive TIME_BLOCK from OCC_HOUR
    if "OCC_HOUR" in df.columns and "TIME_BLOCK" not in df.columns:
        h = pd.to_numeric(df["OCC_HOUR"], errors="coerce")
        df["TIME_BLOCK"] = np.where(h.between(7, 14), "07-15h",
                           np.where(h.between(15, 22), "15-23h", "23-07h"))

    # Derive MCI_CATEGORY if missing
    if "MCI_CATEGORY" not in df.columns and "OFFENCE" in df.columns:
        def _cat(o):
            o = str(o).upper()
            if "ASSAULT"  in o: return "Assault"
            if "ROBBERY"  in o: return "Robbery"
            if "BREAK"    in o: return "Break and Enter"
            if "THEFT"    in o: return "Theft Over"
            if "AUTO"     in o: return "Auto Theft"
            return "Other"
        df["MCI_CATEGORY"] = df["OFFENCE"].apply(_cat)

    # Normalise neighbourhood column name variants
    for variant in ["NEIGHBOURHOOD_158 ", "NEIGHBOURHOOD158", "neighbourhood_158"]:
        if variant in df.columns:
            df = df.rename(columns={variant: "NEIGHBOURHOOD_158"})

    # Drop rows where ALL key columns are NaN
    key_cols = [c for c in ["OCC_YEAR", "OCC_MONTH", "OCC_HOUR",
                             "NEIGHBOURHOOD_158", "OFFENCE"] if c in df.columns]
    df = df.dropna(subset=key_cols, how="all")
    return df

# ── US-03: KPI computation ────────────────────────────────────────────────────
def _us03_kpis(df):
    return {
        "total_crimes":                int(len(df)),
        "most_common_offence":         df["OFFENCE"].mode().iloc[0]
                                       if "OFFENCE" in df.columns and not df["OFFENCE"].empty else "N/A",
        "highest_crime_neighbourhood": df["NEIGHBOURHOOD_158"].value_counts().idxmax()
                                       if "NEIGHBOURHOOD_158" in df.columns else "N/A",
        "total_neighbourhoods":        int(df["NEIGHBOURHOOD_158"].nunique())
                                       if "NEIGHBOURHOOD_158" in df.columns else 0,
        "total_offence_types":         int(df["OFFENCE"].nunique())
                                       if "OFFENCE" in df.columns else 0,
        "year_range":                  f"{int(df['OCC_YEAR'].min())}–{int(df['OCC_YEAR'].max())}"
                                       if "OCC_YEAR" in df.columns else "N/A",
        "total_divisions":             int(df["DIVISION"].nunique())
                                       if "DIVISION" in df.columns else 0,
    }

# ── US-04: Neighbourhood ranking ──────────────────────────────────────────────
def _us04_rank(df, top_n=10):
    if "NEIGHBOURHOOD_158" not in df.columns:
        return pd.DataFrame()
    r = df["NEIGHBOURHOOD_158"].dropna().value_counts().head(top_n).reset_index()
    r.columns = ["neighbourhood", "crime_count"]
    r["rank"] = range(1, len(r) + 1)
    return r

# ── US-05: Peak periods ───────────────────────────────────────────────────────
def _us05_peak(df):
    result = {}
    if "OCC_HOUR" in df.columns:
        result["hourly"] = (pd.to_numeric(df["OCC_HOUR"], errors="coerce")
                            .dropna().astype(int).value_counts().sort_index())
    if "OCC_MONTH" in df.columns:
        result["monthly"] = df["OCC_MONTH"].dropna().astype(str).value_counts()
    if "OCC_YEAR" in df.columns:
        result["yearly"]  = (pd.to_numeric(df["OCC_YEAR"], errors="coerce")
                             .dropna().astype(int).value_counts().sort_index())
    return result

# ── US-06: Crime type distribution ───────────────────────────────────────────
def _us06_dist(df, top_n=15):
    if "OFFENCE" not in df.columns:
        return pd.DataFrame(), pd.DataFrame()
    dist = df["OFFENCE"].dropna().value_counts().head(top_n).reset_index()
    dist.columns = ["offence", "crime_count"]
    dist["pct"] = (dist["crime_count"] / dist["crime_count"].sum() * 100).round(2)
    cat = pd.DataFrame()
    if "MCI_CATEGORY" in df.columns:
        cat = df["MCI_CATEGORY"].dropna().value_counts().reset_index()
        cat.columns = ["category", "count"]
    return dist, cat

# ── US-08: Division activity ──────────────────────────────────────────────────
def _us08_div(df):
    if "DIVISION" not in df.columns:
        return pd.DataFrame()
    d = df["DIVISION"].dropna().value_counts().reset_index()
    d.columns = ["division", "crime_count"]
    d["pct"]  = (d["crime_count"] / d["crime_count"].sum() * 100).round(2)
    d["rank"] = range(1, len(d) + 1)
    return d

# ── US-14: Year-over-year trend ───────────────────────────────────────────────
def _us14_yoy(df):
    if "OCC_YEAR" not in df.columns:
        return pd.DataFrame()
    t = (pd.to_numeric(df["OCC_YEAR"], errors="coerce")
           .dropna().astype(int).value_counts().sort_index().reset_index())
    t.columns = ["year", "crime_count"]
    t["pct_change"] = (t["crime_count"].pct_change() * 100).round(2)
    t["is_peak"]    = t["crime_count"] == t["crime_count"].max()
    t["is_lowest"]  = t["crime_count"] == t["crime_count"].min()
    return t

# ── US-10: Filters ────────────────────────────────────────────────────────────
def _get_filter_options(df):
    opts = {"years": [], "offence_types": [], "divisions": [], "neighbourhoods": []}
    if df is None:
        return opts
    if "OCC_YEAR" in df.columns:
        opts["years"] = sorted(df["OCC_YEAR"].dropna().astype(int).unique().tolist())
    if "OFFENCE" in df.columns:
        opts["offence_types"] = sorted(df["OFFENCE"].dropna().unique().tolist())
    if "DIVISION" in df.columns:
        opts["divisions"] = sorted(df["DIVISION"].dropna().astype(str).unique().tolist())
    if "NEIGHBOURHOOD_158" in df.columns:
        opts["neighbourhoods"] = sorted(df["NEIGHBOURHOOD_158"].dropna().unique().tolist())
    return opts

def _apply_filters(df, neighbourhood=None, offence_type=None, year=None, division=None):
    if df is None:
        return None
    out = df.copy()
    if neighbourhood and neighbourhood != "All" and "NEIGHBOURHOOD_158" in out.columns:
        out = out[out["NEIGHBOURHOOD_158"] == neighbourhood]
    if offence_type and offence_type != "All" and "OFFENCE" in out.columns:
        out = out[out["OFFENCE"] == offence_type]
    if year and year != "All" and "OCC_YEAR" in out.columns:
        out = out[pd.to_numeric(out["OCC_YEAR"], errors="coerce") == int(year)]
    if division and division != "All" and "DIVISION" in out.columns:
        out = out[out["DIVISION"].astype(str) == str(division)]
    return out

# ─────────────────────────────────────────────────────────────────────────────
# FULL PIPELINE RUNNER  (US-01 → US-14 in one click)
# ─────────────────────────────────────────────────────────────────────────────

def run_full_pipeline(raw_df, progress_bar, status_text):
    """Runs all analytics steps and saves CSV outputs to data/ folder."""
    st.session_state.pipeline_log = []
    steps = 9
    step  = 0

    def _tick(label):
        nonlocal step
        step += 1
        progress_bar.progress(step / steps)
        status_text.markdown(f"**⏳ {label}**")

    try:
        # US-01: Validate raw data
        _tick("US-01 · Validating raw dataset…")
        _log(f"Raw dataset loaded: {raw_df.shape[0]:,} rows × {raw_df.shape[1]} columns", "ok")

        # US-02: Clean
        _tick("US-02 · Cleaning dataset…")
        cleaned = _us02_clean(raw_df)
        cleaned.to_csv(_dp(_CLEANED_CSV_NAME), index=False)
        _log(f"Cleaned: {cleaned.shape[0]:,} rows → saved {_CLEANED_CSV_NAME}", "ok")
        # Verify key derived columns
        for col in ["TIME_BLOCK", "OCC_DOW", "MCI_CATEGORY"]:
            status = "✓" if col in cleaned.columns else "✗ missing"
            _log(f"  Column {col}: {status}", "ok" if col in cleaned.columns else "warn")

        # US-03: KPIs
        _tick("US-03 · Computing KPIs…")
        kpis = _us03_kpis(cleaned)
        pd.DataFrame([kpis]).to_csv(_dp("crime_overview_kpis.csv"), index=False)
        _log(f"KPIs: {kpis['total_crimes']:,} crimes | {kpis['year_range']} | "
             f"{kpis['total_neighbourhoods']} neighbourhoods | {kpis['total_divisions']} divisions", "ok")

        # US-04: Neighbourhood ranking
        _tick("US-04 · Ranking neighbourhoods…")
        nb_df = _us04_rank(cleaned, top_n=20)
        if not nb_df.empty:
            nb_df.to_csv(_dp("top_neighbourhoods.csv"), index=False)
            _log(f"Top neighbourhood: {nb_df.iloc[0]['neighbourhood']} "
                 f"({nb_df.iloc[0]['crime_count']:,} crimes)", "ok")
        else:
            _log("NEIGHBOURHOOD_158 column not found — skipping US-04", "warn")

        # US-05: Peak periods
        _tick("US-05 · Detecting peak crime periods…")
        peak = _us05_peak(cleaned)
        rows = []
        for ptype, series in peak.items():
            for pval, cnt in series.items():
                rows.append({"period_type": ptype, "period_value": str(pval), "crime_count": int(cnt)})
        if rows:
            pd.DataFrame(rows).to_csv(_dp("peak_crime_periods.csv"), index=False)
            peak_h = peak.get("hourly", pd.Series())
            _log(f"Peak hour: {peak_h.idxmax() if not peak_h.empty else 'N/A'}:00 "
                 f"({int(peak_h.max()):,} crimes)" if not peak_h.empty else "Hourly data N/A", "ok")

        # US-06: Crime type distribution
        _tick("US-06 · Analysing crime type distribution…")
        dist_df, cat_df = _us06_dist(cleaned, top_n=15)
        if not dist_df.empty:
            dist_df.to_csv(_dp("crime_type_distribution.csv"), index=False)
            _log(f"Top offence: {dist_df.iloc[0]['offence']} ({dist_df.iloc[0]['crime_count']:,})", "ok")
        if not cat_df.empty:
            cat_df.to_csv(_dp("category_distribution.csv"), index=False)
            _log(f"MCI categories found: {list(cat_df['category'].values)}", "ok")

        # US-08: Division activity
        _tick("US-08 · Comparing division activity…")
        div_df = _us08_div(cleaned)
        if not div_df.empty:
            div_df.to_csv(_dp("division_activity.csv"), index=False)
            _log(f"Divisions: {len(div_df)} | Top: {div_df.iloc[0]['division']} "
                 f"({div_df.iloc[0]['pct']:.1f}%)", "ok")
        else:
            _log("DIVISION column not found — skipping US-08", "warn")

        # US-14: Year-over-year trend
        _tick("US-14 · Computing year-over-year trend…")
        yoy = _us14_yoy(cleaned)
        if not yoy.empty:
            yoy.to_csv(_dp("yoy_crime_trend.csv"), index=False)
            peak_yr = yoy[yoy["is_peak"]]["year"].iloc[0] if yoy["is_peak"].any() else "N/A"
            low_yr  = yoy[yoy["is_lowest"]]["year"].iloc[0] if yoy["is_lowest"].any() else "N/A"
            _log(f"YoY trend: peak year {peak_yr}, lowest year {low_yr}", "ok")
        else:
            _log("OCC_YEAR column not found — skipping US-14", "warn")

        progress_bar.progress(1.0)
        status_text.markdown("**✅ Pipeline complete — navigate to any dashboard page.**")
        _log("─────────────────────────────────────────────", "info")
        _log("All pipeline steps completed successfully.", "ok")
        return cleaned

    except Exception as e:
        _log(f"PIPELINE FAILED at step {step}: {e}", "err")
        _log(traceback.format_exc(), "err")
        status_text.markdown("**❌ Pipeline failed. See log below.**")
        return None

# ─────────────────────────────────────────────────────────────────────────────
# ─────────────────────────────────────────────────────────────────────────────
# HELPER: render PNG gallery from outputs/
# ─────────────────────────────────────────────────────────────────────────────
def _show_visuals(files_labels):
    """Display a list of (filename, caption) pairs as a 2-col image gallery."""
    # Try dashboard-relative outputs/ first, then repo-root outputs/
    _OUTPUTS_DIR = os.path.join(_HERE, "outputs")
    if not any(os.path.exists(os.path.join(_OUTPUTS_DIR, f)) for f, _ in files_labels):
        _OUTPUTS_DIR = os.path.join(os.path.dirname(_HERE), "outputs")
    available = [(f, l) for f, l in files_labels
                 if os.path.exists(os.path.join(_OUTPUTS_DIR, f))]
    if not available:
        st.info("No saved images found. Commit outputs/ PNGs to GitHub.")
        return
    for i in range(0, len(available), 2):
        cols = st.columns(2)
        for j, (fname, label) in enumerate(available[i:i+2]):
            with cols[j]:
                st.image(os.path.join(_OUTPUTS_DIR, fname),
                         caption=label, use_container_width=True)

# AUTO-STARTUP: Download cleaned CSV from Google Drive and run pipeline
# ─────────────────────────────────────────────────────────────────────────────
_GDRIVE_CLEANED_ID = "19KRbMioffzNXTYF8tOci2KALpW3DaypW"

def _auto_startup():
    """
    On first load:
    1. Try to load cleaned CSV from disk (fast path — already processed).
    2. If not found, download from Google Drive and run the full pipeline.
    """
    # Fast path: cleaned CSV already on disk
    cached = load_csv(_dp(_CLEANED_CSV_NAME))
    if cached is not None:
        st.session_state.cleaned_df = cached
        st.session_state.pipeline_ran = True
        return

    # Slow path: download from Google Drive then run pipeline
    dest = _dp(_CLEANED_CSV_NAME)
    placeholder = st.empty()
    try:
        placeholder.info("⬇️ First run — downloading dataset from Google Drive…")
        import gdown
        url = f"https://drive.google.com/uc?id={_GDRIVE_CLEANED_ID}"
        gdown.download(url=url, output=dest, quiet=True)

        if os.path.exists(dest):
            load_csv.clear()
            df = pd.read_csv(dest, low_memory=False)
            df.columns = df.columns.str.strip()
            # Rename neighbourhood variants
            for variant in ["NEIGHBOURHOOD_158 ", "NEIGHBOURHOOD158", "neighbourhood_158"]:
                if variant in df.columns:
                    df = df.rename(columns={variant: "NEIGHBOURHOOD_158"})
            st.session_state.cleaned_df = df
            st.session_state.pipeline_ran = True
            placeholder.success(f"✅ Dataset loaded — {df.shape[0]:,} records ready.")
        else:
            placeholder.warning(
                "⚠️ Auto-download failed. Go to **⚙️ Run Pipeline** to load data manually."
            )
    except Exception as e:
        placeholder.warning(
            f"⚠️ Auto-download error: {e}. Go to **⚙️ Run Pipeline** to load data manually."
        )

if st.session_state.cleaned_df is None:
    _auto_startup()

# ─────────────────────────────────────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────────────────────────────────────
st.sidebar.image(
    "https://upload.wikimedia.org/wikipedia/commons/thumb/9/9a/Flag_of_Toronto.svg/240px-Flag_of_Toronto.svg.png",
    width=90,
)
st.sidebar.title("🚔 Toronto Crime\nAnalytics Tool")
st.sidebar.caption("Sprint 2 — Integrated Dashboard v7")

# Pipeline status indicator
if st.session_state.pipeline_ran:
    n_rows = len(st.session_state.cleaned_df) if st.session_state.cleaned_df is not None else 0
    st.sidebar.success(f"Pipeline ready · {n_rows:,} records")
else:
    st.sidebar.warning("Pipeline not run yet")

st.sidebar.divider()

PAGE_LABELS = {
    "⚙️ Run Pipeline":               "Pipeline",
    "📊 Overview":                   "Overview",
    "🏘️ Neighbourhoods":             "Neighbourhoods",
    "🔎 Crime Types":                "Crime Types",
    "⏰ Peak Periods":               "Peak Periods",
    "🚓 Police Divisions":           "Divisions",
    "🗺️ Hotspot Map":                "Hotspot Map",
    "📈 Year-over-Year Trend":       "YoY Trend",
    "── VISUALS ──":                 "_divider_",
    "🏘️ US-04 · Neighbourhoods":    "VIS_US04",
    "⏰ US-05 · Peak Periods":       "VIS_US05",
    "🔎 US-06 · Crime Types":        "VIS_US06",
    "📍 US-07 · Hotspots":           "VIS_US07",
    "🚓 US-08 · Divisions":          "VIS_US08",
    "📈 US-14 · YoY Trend":          "VIS_US14",
    "🔬 US-15 · QA & Temporal":      "VIS_US15",
}
# Build nav options, inserting a disabled-looking separator
_nav_options = list(PAGE_LABELS.keys())
page_icon = st.sidebar.radio("Navigate", _nav_options,
    format_func=lambda x: x if x != "── VISUALS ──" else "───────────────")
page = PAGE_LABELS[page_icon]
if page == "_divider_":
    st.stop()

# ── Global Filters ────────────────────────────────────────────────────────────
cleaned_df  = st.session_state.cleaned_df
filtered_df = None

if page != "Pipeline" and cleaned_df is not None:
    st.sidebar.divider()
    st.sidebar.subheader("🔧 Global Filters (US-10)")
    opts      = _get_filter_options(cleaned_df)
    year_list = [int(y) for y in opts["years"]]
    sel_nb    = st.sidebar.selectbox("Neighbourhood", ["All"] + opts["neighbourhoods"], key="nb")
    sel_off   = st.sidebar.selectbox("Offence Type",  ["All"] + opts["offence_types"],  key="off")
    sel_year  = st.sidebar.select_slider("Year", options=["All"] + year_list, value="All", key="yr")
    sel_div   = st.sidebar.selectbox("Division",      ["All"] + opts["divisions"],      key="div")
    year_val  = None if sel_year == "All" else int(sel_year)
    filtered_df = _apply_filters(cleaned_df,
                                 neighbourhood=sel_nb,
                                 offence_type=sel_off,
                                 year=year_val,
                                 division=sel_div)
    n = len(filtered_df) if filtered_df is not None else 0
    st.sidebar.caption(f"✅ **{n:,}** records match filters")
elif page != "Pipeline":
    st.sidebar.divider()
    st.sidebar.warning("Run the pipeline first to enable filters.")

st.sidebar.divider()
st.sidebar.caption("© 2026 Toronto Crime Analytics")

# ─────────────────────────────────────────────────────────────────────────────
# PAGE ── PIPELINE
# ─────────────────────────────────────────────────────────────────────────────
if page == "Pipeline":
    st.title("⚙️ Run Analytics Pipeline")
    st.caption("US-01 → US-14 · No Colab required — runs entirely inside Streamlit")

    st.info(
        "**How it works:** Upload `Toronto_Crime_Indicators.csv` (or point to Google Drive), "
        "then click **Run Full Pipeline**. All US-01 through US-14 analytics steps execute here. "
        "Once complete, every other dashboard page becomes live.",
        icon="ℹ️",
    )

    # ── Step 1: Data source ───────────────────────────────────────────────────
    st.subheader("Step 1 — Load Raw Data")
    tab_up, tab_gdrive, tab_disk = st.tabs(["📁 Upload CSV", "🔗 Google Drive", "💾 Use Existing"])

    with tab_up:
        uploaded = st.file_uploader(
            "Upload Toronto_Crime_Indicators.csv",
            type=["csv"],
            help="Raw dataset from Toronto Open Data",
        )
        if uploaded:
            with st.spinner("Reading file…"):
                raw = pd.read_csv(uploaded, low_memory=False)
                raw.columns = raw.columns.str.strip()
                st.session_state.raw_df = raw
            st.success(f"Loaded: **{raw.shape[0]:,} rows** × **{raw.shape[1]} columns**")

    with tab_gdrive:
        gdrive_id = st.text_input("Google Drive File ID", value=_GDRIVE_RAW_ID,
                                  help="From the share URL: drive.google.com/file/d/FILE_ID/view")
        if st.button("⬇️ Download from Google Drive"):
            dest = _dp(_RAW_CSV_NAME)
            try:
                import gdown
                url = f"https://drive.google.com/uc?id={gdrive_id}"
                with st.spinner("Downloading…"):
                    gdown.download(url=url, output=dest, quiet=True)
                if os.path.exists(dest):
                    raw = pd.read_csv(dest, low_memory=False)
                    raw.columns = raw.columns.str.strip()
                    st.session_state.raw_df = raw
                    st.success(f"Downloaded: **{raw.shape[0]:,} rows**")
                else:
                    st.error("Download failed — check file ID and sharing permissions (must be 'Anyone with link').")
            except ImportError:
                st.error("`gdown` not installed. Add it to requirements.txt and redeploy.")
            except Exception as e:
                st.error(f"Download error: {e}")

    with tab_disk:
        existing = load_csv(_dp(_RAW_CSV_NAME))
        if existing is not None:
            st.success(f"Found `{_RAW_CSV_NAME}` on disk: **{existing.shape[0]:,} rows**")
            if st.button("Use this file"):
                st.session_state.raw_df = existing
                st.rerun()
        else:
            st.warning(f"`{_RAW_CSV_NAME}` not found in the `data/` folder.")

    # ── Step 2: Run pipeline ──────────────────────────────────────────────────
    st.divider()
    st.subheader("Step 2 — Run Pipeline")

    raw_ready = st.session_state.raw_df is not None
    if not raw_ready:
        st.warning("⬆️ Load a dataset in Step 1 first.")
    else:
        r = st.session_state.raw_df
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Rows",    f"{r.shape[0]:,}")
        c2.metric("Columns", r.shape[1])
        c3.metric("Size",    f"{r.memory_usage(deep=True).sum() / 1e6:.1f} MB")
        c4.metric("Status",  "Ready ✅")

        if st.button("🚀 Run Full Pipeline  (US-01 → US-14)",
                     type="primary", use_container_width=True):
            prog   = st.progress(0)
            status = st.empty()
            result = run_full_pipeline(st.session_state.raw_df, prog, status)
            if result is not None:
                st.session_state.cleaned_df = result
                st.session_state.pipeline_ran = True
                load_csv.clear()
                st.balloons()
            else:
                st.error("Pipeline failed. See log below.")

    # ── Pipeline log ──────────────────────────────────────────────────────────
    if st.session_state.pipeline_log:
        st.divider()
        st.subheader("Pipeline Log")
        log_html = ("<div class='pipeline-log'>"
                    + "<br>".join(st.session_state.pipeline_log)
                    + "</div>")
        st.markdown(log_html, unsafe_allow_html=True)

    # ── Output file summary ───────────────────────────────────────────────────
    if st.session_state.pipeline_ran:
        st.divider()
        st.subheader("Generated Output Files")
        csv_files = sorted(f for f in os.listdir(_DATA_DIR) if f.endswith(".csv"))
        if csv_files:
            rows = [{"File": f,
                     "Rows": len(load_csv(_dp(f))) if load_csv(_dp(f)) is not None else "—",
                     "Size (KB)": f"{os.path.getsize(_dp(f))/1024:.1f}"}
                    for f in csv_files]
            st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

# ─────────────────────────────────────────────────────────────────────────────
# PAGE ── OVERVIEW
# ─────────────────────────────────────────────────────────────────────────────
elif page == "Overview":
    st.title("📊 Toronto Crime Risk Overview")
    st.caption("US-03 · KPI summary — updates live with sidebar filters")

    df_view = filtered_df if filtered_df is not None else cleaned_df
    if df_view is None or df_view.empty:
        st.warning("No data loaded. Go to **⚙️ Run Pipeline** first.")
        st.stop()

    kpis = _us03_kpis(df_view)
    c1, c2, c3, c4, c5 = st.columns(5)
    _kpi_card(c1, "Total Crimes",        f"{kpis['total_crimes']:,}")
    _kpi_card(c2, "Most Common Offence", kpis["most_common_offence"])
    _kpi_card(c3, "Highest Crime Area",  kpis["highest_crime_neighbourhood"])
    _kpi_card(c4, "Unique Hoods",        kpis["total_neighbourhoods"])
    _kpi_card(c5, "Offence Types",       kpis["total_offence_types"])
    st.caption(f"*Year range: {kpis['year_range']} · {kpis['total_divisions']} police divisions. "
               "KPIs update live with sidebar filters.*")

    if "OCC_YEAR" in df_view.columns:
        st.divider()
        st.subheader("Crime Count by Year")
        yr = (pd.to_numeric(df_view["OCC_YEAR"], errors="coerce")
              .dropna().astype(int).value_counts().sort_index().reset_index())
        yr.columns = ["Year", "Count"]
        fig, ax = plt.subplots(figsize=(11, 3.5))
        ax.fill_between(yr["Year"], yr["Count"], alpha=0.18, color="#2980b9")
        ax.plot(yr["Year"], yr["Count"], marker="o", linewidth=2, color="#2980b9")
        ax.set_title("Annual Crime Count (filtered)", fontsize=12)
        ax.grid(True, linestyle="--", alpha=0.3)
        ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f"{int(v):,}"))
        plt.tight_layout()
        st.pyplot(fig); plt.close(fig)

# ─────────────────────────────────────────────────────────────────────────────
# PAGE ── NEIGHBOURHOODS
# ─────────────────────────────────────────────────────────────────────────────
elif page == "Neighbourhoods":
    st.title("🏘️ High-Risk Neighbourhoods")
    st.caption("US-04 · Ranking updates with sidebar filters")

    df_view = filtered_df if filtered_df is not None else cleaned_df
    if df_view is None or df_view.empty:
        st.warning("No data. Run the pipeline first."); st.stop()

    top_n = st.slider("Show top N neighbourhoods", 5, 30, 10, key="top_nb")
    nb = _us04_rank(df_view, top_n)
    if nb.empty:
        st.info("Column `NEIGHBOURHOOD_158` not found in dataset.")
    else:
        col1, col2 = st.columns([1, 2])
        with col1:
            st.dataframe(nb, use_container_width=True, height=430)
        with col2:
            fig = _hbar(nb, "neighbourhood", "crime_count",
                        f"Top {top_n} High-Risk Neighbourhoods",
                        figsize=(9, max(4, top_n * 0.42)))
            st.pyplot(fig); plt.close(fig)

# ─────────────────────────────────────────────────────────────────────────────
# PAGE ── CRIME TYPES
# ─────────────────────────────────────────────────────────────────────────────
elif page == "Crime Types":
    st.title("🔎 Crime Type Distribution")
    st.caption("US-06 · Distribution of offences — updates with sidebar filters")

    df_view = filtered_df if filtered_df is not None else cleaned_df
    if df_view is None or df_view.empty:
        st.warning("No data. Run the pipeline first."); st.stop()

    top_n = st.slider("Show top N offence types", 5, 30, 15, key="top_off")
    dist_df, cat_df = _us06_dist(df_view, top_n)

    if dist_df.empty:
        st.info("Column `OFFENCE` not found in dataset.")
    else:
        tab1, tab2 = st.tabs(["Bar Chart", "Data Table"])
        with tab1:
            fig = _hbar(dist_df, "offence", "crime_count",
                        f"Top {top_n} Offence Types",
                        figsize=(10, max(5, top_n * 0.38)))
            st.pyplot(fig); plt.close(fig)
        with tab2:
            st.dataframe(dist_df, use_container_width=True)

    if not cat_df.empty:
        st.divider()
        st.subheader("MCI Crime Category Breakdown")
        colors = ["#c0392b", "#2980b9", "#27ae60", "#e67e22", "#8e44ad", "#16a085", "#7f8c8d"]
        fig2, ax2 = plt.subplots(figsize=(7, 7))
        ax2.pie(cat_df["count"], labels=cat_df["category"], autopct="%1.1f%%",
                startangle=140, colors=colors[:len(cat_df)],
                wedgeprops={"edgecolor": "white", "linewidth": 1.5})
        ax2.set_title("MCI Category Distribution", fontsize=13, fontweight="bold")
        plt.tight_layout(); st.pyplot(fig2); plt.close(fig2)

# ─────────────────────────────────────────────────────────────────────────────
# PAGE ── PEAK PERIODS
# ─────────────────────────────────────────────────────────────────────────────
elif page == "Peak Periods":
    st.title("⏰ Peak Crime Periods")
    st.caption("US-05 · Hourly, monthly, and yearly crime patterns")

    df_view = filtered_df if filtered_df is not None else cleaned_df
    if df_view is None or df_view.empty:
        st.warning("No data. Run the pipeline first."); st.stop()

    tab_h, tab_m, tab_y = st.tabs(["By Hour", "By Month", "By Year"])

    with tab_h:
        if "OCC_HOUR" in df_view.columns:
            h_c = (pd.to_numeric(df_view["OCC_HOUR"], errors="coerce")
                   .dropna().astype(int).value_counts().sort_index().reset_index())
            h_c.columns = ["hour", "crime_count"]
            peak_h = h_c["crime_count"].max()
            colors = ["#c0392b" if v == peak_h else "#2980b9" for v in h_c["crime_count"]]
            fig, ax = plt.subplots(figsize=(12, 4))
            ax.bar(h_c["hour"], h_c["crime_count"], color=colors, width=0.85)
            ax.set_xlabel("Hour of Day"); ax.set_ylabel("Crime Count")
            ax.set_title("Crime Count by Hour  (red = peak hour)", fontweight="bold")
            ax.set_xticks(range(24)); ax.grid(axis="y", alpha=0.25, linestyle="--")
            plt.tight_layout(); st.pyplot(fig); plt.close(fig)
        else:
            st.info("Column `OCC_HOUR` not available.")

    with tab_m:
        if "OCC_MONTH" in df_view.columns:
            month_order = ["January", "February", "March", "April", "May", "June",
                           "July", "August", "September", "October", "November", "December"]
            m_c = df_view["OCC_MONTH"].dropna().astype(str).value_counts().reset_index()
            m_c.columns = ["month", "crime_count"]
            try:
                m_c["month"] = pd.Categorical(m_c["month"], categories=month_order, ordered=True)
                m_c = m_c.sort_values("month")
            except Exception:
                m_c = m_c.sort_values("crime_count", ascending=False)
            fig, ax = plt.subplots(figsize=(12, 4))
            ax.bar(m_c["month"].astype(str), m_c["crime_count"], color="#2980b9", edgecolor="white")
            ax.set_title("Crime Count by Month", fontweight="bold"); ax.set_ylabel("Crime Count")
            plt.xticks(rotation=30, ha="right"); ax.grid(axis="y", alpha=0.25, linestyle="--")
            plt.tight_layout(); st.pyplot(fig); plt.close(fig)
        else:
            st.info("Column `OCC_MONTH` not available.")

    with tab_y:
        if "OCC_YEAR" in df_view.columns:
            y_c = (pd.to_numeric(df_view["OCC_YEAR"], errors="coerce")
                   .dropna().astype(int).value_counts().sort_index().reset_index())
            y_c.columns = ["year", "crime_count"]
            fig, ax = plt.subplots(figsize=(12, 4))
            ax.plot(y_c["year"], y_c["crime_count"], marker="o", linewidth=2, color="#2980b9")
            ax.fill_between(y_c["year"], y_c["crime_count"], alpha=0.15, color="#2980b9")
            ax.set_title("Annual Crime Count Trend", fontweight="bold")
            ax.set_ylabel("Crime Count"); ax.set_xlabel("Year")
            ax.grid(True, linestyle="--", alpha=0.3)
            plt.tight_layout(); st.pyplot(fig); plt.close(fig)
        else:
            st.info("Column `OCC_YEAR` not available.")

# ─────────────────────────────────────────────────────────────────────────────
# PAGE ── DIVISIONS
# ─────────────────────────────────────────────────────────────────────────────
elif page == "Divisions":
    st.title("🚓 Police Division Activity")
    st.caption("US-08 · Crime volume per TPS division — updates with sidebar filters")

    df_view = filtered_df if filtered_df is not None else cleaned_df
    if df_view is None or df_view.empty:
        st.warning("No data. Run the pipeline first."); st.stop()

    div_df = _us08_div(df_view)
    if div_df.empty:
        st.info("Column `DIVISION` not found in dataset.")
    else:
        col1, col2 = st.columns([1, 2])
        with col1:
            st.dataframe(div_df, use_container_width=True)
        with col2:
            fig = _hbar(div_df, "division", "crime_count",
                        "Crime Count by Toronto Police Division")
            st.pyplot(fig); plt.close(fig)

        with st.expander("🥧 Division share — pie chart"):
            top10 = div_df.head(10).copy()
            other = div_df.iloc[10:]["crime_count"].sum() if len(div_df) > 10 else 0
            if other > 0:
                top10 = pd.concat(
                    [top10, pd.DataFrame([{"division": "Other", "crime_count": other, "pct": 0, "rank": 0}])],
                    ignore_index=True,
                )
            fig2, ax2 = plt.subplots(figsize=(7, 7))
            ax2.pie(top10["crime_count"], labels=top10["division"],
                    autopct="%1.1f%%", startangle=140)
            ax2.set_title("Crime Share by Division (Top 10)")
            plt.tight_layout(); st.pyplot(fig2); plt.close(fig2)

# ─────────────────────────────────────────────────────────────────────────────
# PAGE ── HOTSPOT MAP  (US-13)
# ─────────────────────────────────────────────────────────────────────────────
elif page == "Hotspot Map":
    st.title("🗺️ Crime Hotspot Map")
    st.caption("US-13 · Interactive Folium MarkerCluster map")

    df_view  = filtered_df if filtered_df is not None else cleaned_df
    html_path = _op("toronto_hotspot_map.html")

    col_a, col_b, col_c = st.columns(3)
    sample_size = col_a.slider("Sample size (markers)", 500, 8000, 3000, 500, key="map_sample")
    top_n_hoods = col_b.slider("Top N neighbourhoods",  5, 20, 10,         key="map_hoods")
    regen       = col_c.button("🔄 Build / Rebuild Map")

    need_build = regen or not os.path.exists(html_path)

    if need_build:
        if df_view is None:
            st.error("No data — run the pipeline first.")
        else:
            lat_col = next((c for c in ["LAT_WGS84", "Lat", "latitude", "LAT"] if c in df_view.columns), None)
            lon_col = next((c for c in ["LONG_WGS84", "Long", "longitude", "LON", "LONG"] if c in df_view.columns), None)
            nb_col  = "NEIGHBOURHOOD_158" if "NEIGHBOURHOOD_158" in df_view.columns else None

            if lat_col and lon_col and nb_col:
                with st.spinner("Building Folium map…"):
                    try:
                        import folium
                        from folium.plugins import MarkerCluster

                        top_hoods = df_view[nb_col].value_counts().head(top_n_hoods).index.tolist()
                        map_df = df_view[df_view[nb_col].isin(top_hoods)].dropna(subset=[lat_col, lon_col])
                        if len(map_df) > sample_size:
                            map_df = map_df.sample(sample_size, random_state=42)

                        m = folium.Map(location=[43.7, -79.42], zoom_start=11,
                                       tiles="CartoDB positron")
                        cluster = MarkerCluster().add_to(m)
                        for _, row in map_df.iterrows():
                            label = str(row.get("OFFENCE", "Crime"))
                            folium.CircleMarker(
                                location=[float(row[lat_col]), float(row[lon_col])],
                                radius=4, color="#c0392b", fill=True, fill_opacity=0.6,
                                popup=label,
                            ).add_to(cluster)
                        m.save(html_path)
                        st.success(f"Map built — {len(map_df):,} markers")
                    except Exception as e:
                        st.error(f"Map build failed: {e}")
            elif not lat_col or not lon_col:
                st.warning(
                    f"Coordinate columns not found. Expected `LAT_WGS84` / `LONG_WGS84`.  \n"
                    f"Columns in dataset: `{'`, `'.join(list(df_view.columns[:15]))}`"
                )
            else:
                st.warning("Column `NEIGHBOURHOOD_158` not found — cannot filter by neighbourhood.")

    if os.path.exists(html_path):
        with open(html_path, "r", encoding="utf-8") as f:
            map_html = f.read()
        st.components.v1.html(map_html, height=620, scrolling=False)
        if df_view is not None and "NEIGHBOURHOOD_158" in df_view.columns:
            st.divider()
            st.subheader("Top Neighbourhood Crime Counts")
            top_nb = (df_view["NEIGHBOURHOOD_158"].dropna()
                      .value_counts().head(top_n_hoods).reset_index())
            top_nb.columns = ["Neighbourhood", "Crime Count"]
            st.dataframe(top_nb, use_container_width=True, height=320)
    else:
        st.info("No map yet. Click **Build / Rebuild Map** above.", icon="ℹ️")

# ─────────────────────────────────────────────────────────────────────────────
# PAGE ── YoY TREND  (US-14)
# ─────────────────────────────────────────────────────────────────────────────
elif page == "YoY Trend":
    st.title("📈 Year-over-Year Crime Trend")
    st.caption("US-14 · Annual crime counts with % change — updates with sidebar filters")

    df_view = filtered_df if filtered_df is not None else cleaned_df
    if df_view is None or df_view.empty:
        st.warning("No data. Run the pipeline first."); st.stop()

    trend = _us14_yoy(df_view)
    if trend.empty:
        st.info("Column `OCC_YEAR` not found."); st.stop()

    # Line chart
    fig, ax = plt.subplots(figsize=(12, 5))
    ax.plot(trend["year"], trend["crime_count"], marker="o", linewidth=2,
            color="#2980b9", label="Annual Crime Count")
    peak_rows = trend[trend["is_peak"]]
    low_rows  = trend[trend["is_lowest"]]
    ax.scatter(peak_rows["year"], peak_rows["crime_count"],
               color="#c0392b", s=120, zorder=5, label="Peak Year")
    ax.scatter(low_rows["year"],  low_rows["crime_count"],
               color="#27ae60", s=120, zorder=5, label="Lowest Year")
    for _, r in peak_rows.iterrows():
        ax.annotate(f"Peak {int(r['year'])}\n({int(r['crime_count']):,})",
                    xy=(r["year"], r["crime_count"]), xytext=(8, 8),
                    textcoords="offset points", color="#c0392b",
                    fontsize=9, fontweight="bold")
    for _, r in low_rows.iterrows():
        ax.annotate(f"Lowest {int(r['year'])}\n({int(r['crime_count']):,})",
                    xy=(r["year"], r["crime_count"]), xytext=(8, -22),
                    textcoords="offset points", color="#27ae60",
                    fontsize=9, fontweight="bold")
    ax.set_xlabel("Year"); ax.set_ylabel("Crime Count")
    ax.set_title("Year-over-Year Crime Trend in Toronto", fontweight="bold", fontsize=13)
    ax.legend(); ax.grid(True, linestyle="--", alpha=0.3)
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f"{int(v):,}"))
    plt.tight_layout(); st.pyplot(fig); plt.close(fig)

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
    plt.tight_layout(); st.pyplot(fig2); plt.close(fig2)

    with st.expander("📋 Data table"):
        st.dataframe(trend, use_container_width=True)

# ─────────────────────────────────────────────────────────────────────────────
# PAGE ── VIS_US04
# ─────────────────────────────────────────────────────────────────────────────
elif page == "VIS_US04":
    st.title("🏘️ US-04 · High-Risk Neighbourhoods")
    st.caption("Pre-generated visuals from the master pipeline")
    _show_visuals([
        ("us04_neighbourhood_ranking.png", "Top-10 High-Risk Neighbourhoods — bar chart"),
    ])

# ─────────────────────────────────────────────────────────────────────────────
# PAGE ── VIS_US05
# ─────────────────────────────────────────────────────────────────────────────
elif page == "VIS_US05":
    st.title("⏰ US-05 · Peak Crime Periods")
    st.caption("Pre-generated visuals from the master pipeline")
    _show_visuals([
        ("us05_hourly_bar.png",       "Crime by Hour (0–23)"),
        ("us05_monthly_bar.png",      "Crime by Month"),
        ("us05_yearly_trend.png",     "Crime by Year"),
        ("us05_clock_polar.png",      "Clock-Rose — All Hours"),
        ("us05_dow_clock_grid.png",   "Day-of-Week Clock Grid (7 panels)"),
        ("us05_timeblock_weekly.png", "Time-Block Weekly Patterns (3 shifts)"),
    ])

# ─────────────────────────────────────────────────────────────────────────────
# PAGE ── VIS_US06
# ─────────────────────────────────────────────────────────────────────────────
elif page == "VIS_US06":
    st.title("🔎 US-06 · Crime Type Distribution")
    st.caption("Pre-generated visuals from the master pipeline")
    _show_visuals([
        ("us06_offence_distribution.png", "Top-15 Offence Types"),
        ("us06_category_pie.png",         "MCI Crime Category Pie"),
        ("us06_category_clock_grid.png",  "Category × Day-of-Week Clock Grid"),
    ])

# ─────────────────────────────────────────────────────────────────────────────
# PAGE ── VIS_US07
# ─────────────────────────────────────────────────────────────────────────────
elif page == "VIS_US07":
    st.title("📍 US-07 · Crime Hotspots")
    st.caption("Pre-generated visuals from the master pipeline")
    _show_visuals([
        ("us07_hotspot_scatter.png",      "Hotspot Scatter Map"),
        ("us07_area_timeblock_clock.png", "Top-4 Areas × Time-Block Clock Grid"),
    ])

# ─────────────────────────────────────────────────────────────────────────────
# PAGE ── VIS_US08
# ─────────────────────────────────────────────────────────────────────────────
elif page == "VIS_US08":
    st.title("🚓 US-08 · Police Division Activity")
    st.caption("Pre-generated visuals from the master pipeline")
    _show_visuals([
        ("us08_division_ranking.png", "Division Crime Ranking — bar chart"),
        ("us08_division_pie.png",     "Division Crime Share — pie chart"),
    ])

# ─────────────────────────────────────────────────────────────────────────────
# PAGE ── VIS_US14
# ─────────────────────────────────────────────────────────────────────────────
elif page == "VIS_US14":
    st.title("📈 US-14 · Year-over-Year Trend")
    st.caption("Pre-generated visuals from the master pipeline")
    _show_visuals([
        ("us14_yoy_trend.png",      "YoY Crime Trend — line chart (peak/lowest annotated)"),
        ("us14_yoy_pct_change.png", "YoY % Change — bar chart"),
    ])

# ─────────────────────────────────────────────────────────────────────────────
# PAGE ── VIS_US15
# ─────────────────────────────────────────────────────────────────────────────
elif page == "VIS_US15":
    st.title("🔬 US-15 · QA & Temporal Patterns")
    st.caption("Pre-generated visuals from the master pipeline")
    _show_visuals([
        ("us15_clock_polar.png",         "Clock-Rose (QA validation)"),
        ("us15_dow_clock_grid.png",      "Day-of-Week Clock Grid (QA)"),
        ("us15_timeblock_weekly.png",    "Time-Block Weekly Patterns (QA)"),
        ("us15_category_clock_grid.png", "Category × Day Clock Grid (QA)"),
    ])
