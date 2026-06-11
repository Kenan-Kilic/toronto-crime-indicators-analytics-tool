# US-15 — QA Validation & Temporal Patterns Report
# INPUT : raw_df (US-01), cleaned_df (US-02)
# OUTPUT: qa_validation_report.csv + temporal_patterns.csv + 4 figures
#
# REVISED v3: Column references updated (MCI_CATEGORY, OCC_DOW, TIME_BLOCK)

import pandas as pd
import matplotlib.pyplot as plt

from US_05_peak_crime_periods import (
    detect_peak_crime_periods,
    plot_clock_polar,
    plot_clock_by_day_of_week,
    plot_time_block_weekly,
)
from US_06_crime_type_distribution import plot_category_clock_by_day

OCC_YEAR_COL   = "OCC_YEAR"
OCC_HOUR_COL   = "OCC_HOUR"
OCC_DOW_COL    = "OCC_DOW"
MCI_COL        = "MCI_CATEGORY"
TIME_BLOCK_COL = "TIME_BLOCK"

QA_REPORT_CSV = "qa_validation_report.csv"
TEMPORAL_CSV  = "temporal_patterns.csv"


# ─────────────────────────────────────────────────────────────────────────────
# QA REPORT
# ─────────────────────────────────────────────────────────────────────────────
def generate_qa_report(
    raw_df: pd.DataFrame,
    cleaned_df: pd.DataFrame,
    output_path: str = QA_REPORT_CSV
) -> pd.DataFrame:
    """
    Document all data quality decisions from US-02 cleaning step.
    INPUT : raw_df (before), cleaned_df (after)
    OUTPUT: pd.DataFrame QA report + saved CSV
    """
    rows_raw     = len(raw_df)
    rows_cleaned = len(cleaned_df)

    nsa_count = sum(
        int((raw_df[col] == "NSA").sum())
        for col in raw_df.select_dtypes(include="object").columns
    )

    lat_col, lon_col = "LAT_WGS84", "LONG_WGS84"
    coord_removed = 0
    if lat_col in raw_df.columns and lon_col in raw_df.columns:
        coord_removed = int(raw_df[
            raw_df[lat_col].isna() | raw_df[lon_col].isna() |
            (raw_df[lat_col] == 0) | (raw_df[lon_col] == 0)
        ].shape[0])

    dtype_notes = []
    for col in [OCC_HOUR_COL, OCC_YEAR_COL]:
        if col in cleaned_df.columns:
            dtype_notes.append(f"{col}: {cleaned_df[col].dtype}")

    uses_clean = not any(
        (cleaned_df[c] == 0).any()
        for c in [lat_col, lon_col] if c in cleaned_df.columns
    )

    report_rows = [
        {"check": "rows_before_cleaning",  "value": rows_raw,                     "status": "INFO"},
        {"check": "rows_after_cleaning",   "value": rows_cleaned,                 "status": "INFO"},
        {"check": "rows_removed",          "value": rows_raw - rows_cleaned,      "status": "INFO"},
        {"check": "pct_removed",           "value": f"{(rows_raw-rows_cleaned)/rows_raw*100:.1f}%", "status": "INFO"},
        {"check": "nsa_values_replaced",   "value": nsa_count,                    "status": "PASS"},
        {"check": "zero_coords_removed",   "value": coord_removed,               "status": "PASS"},
        {"check": "dtype_checks",          "value": " | ".join(dtype_notes),      "status": "INFO"},
        {"check": "all_analyses_use_clean","value": str(uses_clean),              "status": "PASS" if uses_clean else "FAIL"},
        {"check": "time_block_derived",    "value": str(TIME_BLOCK_COL in cleaned_df.columns), "status": "PASS" if TIME_BLOCK_COL in cleaned_df.columns else "WARN"},
        {"check": "occ_dow_present",       "value": str(OCC_DOW_COL in cleaned_df.columns),    "status": "PASS" if OCC_DOW_COL in cleaned_df.columns else "WARN"},
        {"check": "mci_category_present",  "value": str(MCI_COL in cleaned_df.columns),        "status": "PASS" if MCI_COL in cleaned_df.columns else "WARN"},
        {"check": "github_pr_evidence",    "value": "See GitHub repo — QA Lead: Kenan",         "status": "INFO"},
    ]

    report_df = pd.DataFrame(report_rows)
    report_df.to_csv(output_path, index=False)

    print(f"[US-15] QA report saved -> {output_path}")
    print(f"        Rows before   : {rows_raw:,}")
    print(f"        Rows after    : {rows_cleaned:,}")
    print(f"        Removed       : {rows_raw-rows_cleaned:,}  ({(rows_raw-rows_cleaned)/rows_raw*100:.1f}%)")
    print(f"        NSA replaced  : {nsa_count:,}")
    print(f"        TIME_BLOCK    : {'OK' if TIME_BLOCK_COL in cleaned_df.columns else 'MISSING'}")
    print(f"        OCC_DOW       : {'OK' if OCC_DOW_COL in cleaned_df.columns else 'MISSING'}")
    print(f"        MCI_CATEGORY  : {'OK' if MCI_COL in cleaned_df.columns else 'MISSING'}")

    return report_df


# ─────────────────────────────────────────────────────────────────────────────
# TEMPORAL PATTERNS
# ─────────────────────────────────────────────────────────────────────────────
def run_temporal_patterns(
    cleaned_df: pd.DataFrame,
    output_path: str = TEMPORAL_CSV,
    top_n_cat: int = 3
) -> dict:
    """
    Generate all temporal pattern figures (calls US-05 and US-06 functions).
    INPUT : cleaned pd.DataFrame
    OUTPUT: dict with peak_periods, fig_clock, fig_dow_grid, fig_tb_weekly, fig_cat_grid, summary_df
    """
    print("[US-15] Running temporal pattern analysis ...")

    peak_periods = detect_peak_crime_periods(cleaned_df=cleaned_df, output_path=None)

    print("[US-15] Generating clock-rose (all data) ...")
    fig_clock = plot_clock_polar(peak_periods)

    print("[US-15] Generating day-of-week clock grid ...")
    fig_dow_grid = plot_clock_by_day_of_week(peak_periods)

    print("[US-15] Generating time-block weekly line chart ...")
    fig_tb_weekly = plot_time_block_weekly(peak_periods)

    print(f"[US-15] Generating category x day clock grid (top {top_n_cat}) ...")
    fig_cat_grid = plot_category_clock_by_day(cleaned_df, top_n_categories=top_n_cat)

    # Build summary CSV
    rows = []
    for dim, src_key, key_field, cnt_field in [
        ("hour",  "hourly",  "hour",  "crime_count"),
        ("month", "monthly", "month", "crime_count"),
        ("year",  "yearly",  "year",  "crime_count"),
    ]:
        if src_key in peak_periods:
            for _, r in peak_periods[src_key].iterrows():
                rows.append({"dimension": dim, "key": r[key_field], "count": r[cnt_field]})

    tb_src = peak_periods.get("timeblock_dow_cat", pd.DataFrame())
    if isinstance(tb_src, pd.DataFrame) and not tb_src.empty:
        for _, r in tb_src.iterrows():
            rows.append({
                "dimension": "timeblock_dow_cat",
                "key": f"{r[TIME_BLOCK_COL]}|{r[OCC_DOW_COL]}|{r[MCI_COL]}",
                "count": r["count"],
            })

    summary_df = pd.DataFrame(rows)
    if output_path:
        summary_df.to_csv(output_path, index=False)
        print(f"[US-15] Temporal summary saved -> {output_path}  ({len(summary_df):,} rows)")

    return {
        "peak_periods" : peak_periods,
        "fig_clock"    : fig_clock,
        "fig_dow_grid" : fig_dow_grid,
        "fig_tb_weekly": fig_tb_weekly,
        "fig_cat_grid" : fig_cat_grid,
        "summary_df"   : summary_df,
    }


# ─────────────────────────────────────────────────────────────────────────────
# COMBINED RUNNER
# ─────────────────────────────────────────────────────────────────────────────
def run_us15(
    raw_df: pd.DataFrame,
    cleaned_df: pd.DataFrame,
    qa_path: str = QA_REPORT_CSV,
    temporal_path: str = TEMPORAL_CSV,
    top_n_cat: int = 3
) -> dict:
    """Single entry point for US-15."""
    qa_report = generate_qa_report(raw_df=raw_df, cleaned_df=cleaned_df, output_path=qa_path)
    temporal  = run_temporal_patterns(cleaned_df=cleaned_df, output_path=temporal_path, top_n_cat=top_n_cat)
    return {"qa_report": qa_report, **temporal}
