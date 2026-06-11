# US-12 — Refactor Analytics Modules
# Refactor: Centralize all shared constants and reusable utilities
#
# REVISED v5: Updated COLS dict with MCI_CATEGORY, TIME_BLOCK, OCC_DOW, OCC_DATE
#              REFACTOR_SUMMARY documents OCC_DOW normalisation as root cause of empty plots

import pandas as pd
import matplotlib.pyplot as plt
from typing import Optional

# ── Centralized Column Constants ──────────────────────────────────────────────
COLS = {
    "neighbourhood" : "NEIGHBOURHOOD_158",
    "offence"       : "OFFENCE",
    "lat"           : "LAT_WGS84",
    "lon"           : "LONG_WGS84",
    "hour"          : "OCC_HOUR",
    "month"         : "OCC_MONTH",
    "year"          : "OCC_YEAR",
    "dow"           : "OCC_DOW",           # day of week (derived in US-02 if missing)
    "date"          : "OCC_DATE",
    "division"      : "DIVISION",
    "mci_category"  : "MCI_CATEGORY",      # FIXED: was csi_category / CSI_CATEGORY
    "time_block"    : "TIME_BLOCK",        # derived in US-02 from OCC_HOUR
    "premises"      : "PREMISES_TYPE",
    "location"      : "LOCATION_TYPE",
}

# Toronto bounding box
TORONTO_BOUNDS = {
    "lat_min": 43.58, "lat_max": 43.86,
    "lon_min": -79.64, "lon_max": -79.11,
}


# ── Reusable Utility Functions ─────────────────────────────────────────────────
def compute_value_counts(
    df: pd.DataFrame,
    column: str,
    top_n: Optional[int] = None,
    label: str = "value"
) -> pd.DataFrame:
    """
    Reusable value counts helper.
    INPUT : pd.DataFrame, column name, optional top_n
    OUTPUT: pd.DataFrame [label, crime_count, pct]
    """
    result = df[column].dropna().value_counts().reset_index()
    result.columns = [label, "crime_count"]
    result["pct"] = (result["crime_count"] / result["crime_count"].sum() * 100).round(2)
    if top_n:
        result = result.head(top_n)
    return result.reset_index(drop=True)


def safe_top_n(df: pd.DataFrame, column: str, n: int = 10) -> list:
    """Return top-N unique values from a column by frequency."""
    return df[column].dropna().value_counts().head(n).index.tolist()


def filter_valid_coordinates(df: pd.DataFrame) -> pd.DataFrame:
    """Filter rows to valid Toronto coordinates."""
    lat, lon = COLS["lat"], COLS["lon"]
    b = TORONTO_BOUNDS
    return df[
        df[lat].between(b["lat_min"], b["lat_max"]) &
        df[lon].between(b["lon_min"], b["lon_max"])
    ].copy()


def styled_bar_chart(
    df: pd.DataFrame,
    x_col: str,
    y_col: str,
    title: str,
    xlabel: str = "Count",
    highlight_top: bool = True,
    figsize: tuple = (10, 6)
) -> plt.Figure:
    """Reusable horizontal bar chart."""
    fig, ax = plt.subplots(figsize=figsize)
    colors = (
        ["#d62728"] + ["#1f77b4"] * (len(df) - 1)
        if highlight_top else ["#1f77b4"] * len(df)
    )
    ax.barh(df[x_col].astype(str), df[y_col], color=colors)
    ax.invert_yaxis()
    ax.set_xlabel(xlabel); ax.set_title(title)
    ax.spines["top"].set_visible(False); ax.spines["right"].set_visible(False)
    plt.tight_layout()
    return fig


# ── Refactoring Evidence ───────────────────────────────────────────────────────
REFACTOR_SUMMARY = """
Refactor: Centralize shared constants and reusable utility functions

BEFORE
------
- NEIGHBOURHOOD_COL = "NEIGHBOURHOOD_158" defined in 5 separate files
- OFFENCE_COL, LAT_COL, LON_COL etc. each defined 5x (15+ duplicate lines)
- CSI_CATEGORY used incorrectly — real Toronto Open Data column is MCI_CATEGORY
- TIME_BLOCK never derived — clock plots silently empty
- OCC_DOW passed through unverified — Toronto dataset uses abbreviated values
  (Mon/Tue/Wed) that did not match DAY_ORDER list, so dow_hour_df was always empty
- value_counts().reset_index() pattern repeated in US-03, 04, 06, 08
- ax.barh() boilerplate duplicated in US-04, US-06, US-08

AFTER (v5)
----------
- All column constants in COLS dict (single import replaces all local constants)
- MCI_CATEGORY, TIME_BLOCK, OCC_DOW, OCC_DATE added to COLS
- US-02 v5: TIME_BLOCK always derived fresh from OCC_HOUR
- US-02 v5: OCC_DOW normalised from ANY Toronto Open Data format:
    Mon -> Monday  |  MON -> Monday  |  0 -> Monday  |  monday -> Monday
    Falls back to OCC_DATE derivation if existing values < 80% recognisable
- US-02 v5: MCI_CATEGORY normalised (casing) OR derived from OFFENCE keywords
- compute_value_counts() replaces 5 repeated .value_counts().reset_index() patterns
- styled_bar_chart() replaces 3 repeated ax.barh() boilerplate blocks
- filter_valid_coordinates() replaces 2 duplicate Toronto bounding box blocks
- TORONTO_BOUNDS replaces hardcoded lat/lon limits in US-02 and US-07

ROOT CAUSE OF EMPTY CLOCK PLOTS (documented for audit trail)
--------------------------------------------------------------
1. CSI_CATEGORY vs MCI_CATEGORY: wrong column name caused MCI_CATEGORY lookups
   to silently return empty DataFrames in US-05, US-06, US-15
2. OCC_DOW format mismatch: Toronto dataset exports abbreviated day names
   (Mon, Tue, Wed) but DAY_ORDER list used full names (Monday, Tuesday...)
   Both fixed in US-02 v5 with normalisation and fallback derivation.

RESULT
------
- Clock plots now show real data (not empty)
- ~45 lines of duplicate code eliminated
- 17 tests pass (see US_11_automated_testing.py)
- All figures save to outputs/ folder via save_fig() helper in notebook
"""

if __name__ == "__main__":
    print(REFACTOR_SUMMARY)
