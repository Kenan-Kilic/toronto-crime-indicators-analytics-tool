# US-05 — Detect Peak Crime Periods
# INPUT : pd.DataFrame (cleaned, from US-02)
# OUTPUT: dict of DataFrames + peak_crime_periods.csv + charts
#
# REVISED v4 — Final:
#   - All clock plots fixed: proper sizing, no clipping, colorbars separate
#   - plot_clock_polar       : standalone polar rose with inline annotation
#   - plot_clock_by_day_of_week : 7-panel grid, constrained_layout, shared colourbar
#   - plot_time_block_weekly : 3-panel line chart with proper legend placement

import pandas as pd
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.cm as cm
from matplotlib.colors import Normalize, LinearSegmentedColormap
from matplotlib.patches import Patch

OCC_HOUR_COL   = "OCC_HOUR"
OCC_MONTH_COL  = "OCC_MONTH"
OCC_YEAR_COL   = "OCC_YEAR"
OCC_DOW_COL    = "OCC_DOW"
OCC_DATE_COL   = "OCC_DATE"
MCI_COL        = "MCI_CATEGORY"
TIME_BLOCK_COL = "TIME_BLOCK"

MONTH_ORDER = ["January","February","March","April","May","June",
               "July","August","September","October","November","December"]
MONTH_SHORT = ["Jan","Feb","Mar","Apr","May","Jun",
               "Jul","Aug","Sep","Oct","Nov","Dec"]
DAY_ORDER   = ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]

_GREEN_BROWN = LinearSegmentedColormap.from_list(
    "green_brown", ["#27ae60","#f39c12","#c0392b"]
)

_PALETTE = {
    "Crimes Against Person": "#c0392b",
    "Break and Enter"      : "#2980b9",
    "Theft Over"           : "#27ae60",
    "Theft Under"          : "#e67e22",
    "Auto Theft"           : "#8e44ad",
    "Fraud"                : "#16a085",
    "Other Crimes"         : "#7f8c8d",
}


# ─────────────────────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────────────────────
def _assign_time_block(hour) -> str:
    if pd.isna(hour): return "Unknown"
    h = int(hour)
    if 7 <= h < 15:    return "07-15h"
    elif 15 <= h < 23: return "15-23h"
    else:              return "23-07h"


def _ensure_occ_dow(df: pd.DataFrame) -> pd.DataFrame:
    """Populate OCC_DOW from OCC_DATE when missing."""
    if OCC_DOW_COL in df.columns and df[OCC_DOW_COL].notna().sum() > 0:
        return df
    if OCC_DATE_COL in df.columns:
        day_map = {0:"Monday",1:"Tuesday",2:"Wednesday",3:"Thursday",
                   4:"Friday",5:"Saturday",6:"Sunday"}
        df = df.copy()
        df[OCC_DOW_COL] = pd.to_datetime(df[OCC_DATE_COL], errors="coerce") \
                            .dt.dayofweek.map(day_map)
        print(f"[US-05] OCC_DOW derived from OCC_DATE")
    return df


# ─────────────────────────────────────────────────────────────────────────────
# DATA FUNCTION
# ─────────────────────────────────────────────────────────────────────────────
def detect_peak_crime_periods(
    cleaned_df: pd.DataFrame,
    output_path: str = None
) -> dict:
    """
    Compute hourly / monthly / yearly / DOW peak crime periods.
    INPUT : cleaned pd.DataFrame
    OUTPUT: dict  {hourly, monthly, yearly, dow_hour_df, timeblock_dow_cat}
    """
    results = {}
    df = cleaned_df.copy()

    if TIME_BLOCK_COL not in df.columns and OCC_HOUR_COL in df.columns:
        df[TIME_BLOCK_COL] = df[OCC_HOUR_COL].apply(_assign_time_block)

    df = _ensure_occ_dow(df)

    # ── Hourly ──────────────────────────────────────────────────────────────
    if OCC_HOUR_COL in df.columns:
        hourly = (df[OCC_HOUR_COL].dropna()
                  .astype(int).value_counts().reindex(range(24), fill_value=0)
                  .sort_index().reset_index())
        hourly.columns = ["hour", "crime_count"]
        hourly["is_peak"] = hourly["crime_count"] == hourly["crime_count"].max()
        results["hourly"] = hourly

    # ── Monthly ──────────────────────────────────────────────────────────────
    if OCC_MONTH_COL in df.columns:
        ms = df[OCC_MONTH_COL].dropna().astype(str).str.strip()
        sample = ms.iloc[0] if len(ms) > 0 else ""
        try:
            int(float(sample))
            mdf = ms.value_counts().reset_index()
            mdf.columns = ["month","crime_count"]
            mdf["month_num"] = mdf["month"].astype(float).astype(int)
            mdf = mdf.sort_values("month_num").drop(columns="month_num").reset_index(drop=True)
            mdf["display"] = mdf["month"].apply(
                lambda m: MONTH_SHORT[int(float(m))-1] if 1 <= int(float(m)) <= 12 else m)
        except (ValueError, TypeError):
            mdf = ms.value_counts().reset_index()
            mdf.columns = ["month","crime_count"]
            mdf["month_num"] = mdf["month"].apply(
                lambda m: MONTH_ORDER.index(m) if m in MONTH_ORDER else 99)
            mdf = mdf.sort_values("month_num").drop(columns="month_num").reset_index(drop=True)
            mdf["display"] = mdf["month"].apply(
                lambda m: MONTH_SHORT[MONTH_ORDER.index(m)] if m in MONTH_ORDER else m)
        mdf["is_peak"] = mdf["crime_count"] == mdf["crime_count"].max()
        results["monthly"] = mdf

    # ── Yearly ───────────────────────────────────────────────────────────────
    if OCC_YEAR_COL in df.columns:
        ydf = (df[OCC_YEAR_COL].dropna().astype(int)
               .value_counts().sort_index().reset_index())
        ydf.columns = ["year","crime_count"]
        ydf["pct_change"] = ydf["crime_count"].pct_change() * 100
        results["yearly"] = ydf

    # ── DOW × Hour matrix ────────────────────────────────────────────────────
    if OCC_DOW_COL in df.columns and OCC_HOUR_COL in df.columns:
        sub = df.dropna(subset=[OCC_DOW_COL, OCC_HOUR_COL])
        sub = sub[sub[OCC_DOW_COL].isin(DAY_ORDER)]
        if not sub.empty:
            dh = (sub.assign(**{OCC_HOUR_COL: lambda x: x[OCC_HOUR_COL].astype(int)})
                  .groupby([OCC_DOW_COL, OCC_HOUR_COL]).size()
                  .unstack(fill_value=0)
                  .reindex(DAY_ORDER, fill_value=0)
                  .reindex(columns=range(24), fill_value=0))
            results["dow_hour_df"] = dh
            print(f"[US-05] dow_hour_df: {dh.shape}, max={dh.values.max()}")

    # ── Time-block × DOW × Category ──────────────────────────────────────────
    tb_need = [TIME_BLOCK_COL, OCC_DOW_COL, MCI_COL]
    if all(c in df.columns for c in tb_need):
        sub2 = df.dropna(subset=tb_need)
        sub2 = sub2[sub2[OCC_DOW_COL].isin(DAY_ORDER)]
        if not sub2.empty:
            tb = sub2.groupby(tb_need).size().reset_index(name="count")
            results["timeblock_dow_cat"] = tb
            print(f"[US-05] timeblock_dow_cat: {len(tb)} rows")

    # ── Save CSV ─────────────────────────────────────────────────────────────
    if output_path and results:
        frames = []
        for k, v in results.items():
            if isinstance(v, pd.DataFrame) and not v.empty:
                tmp = v.copy(); tmp.insert(0, "period_type", k)
                frames.append(tmp)
        if frames:
            pd.concat(frames, ignore_index=True).to_csv(output_path, index=False)
            print(f"[US-05] Saved -> {output_path}")

    return results


# ─────────────────────────────────────────────────────────────────────────────
# ORIGINAL CHARTS (unchanged API)
# ─────────────────────────────────────────────────────────────────────────────
def plot_peak_crime_periods(periods: dict) -> dict:
    figs = {}

    if "hourly" in periods:
        df = periods["hourly"]
        colors = ["#d62728" if p else "#3498db" for p in df["is_peak"]]
        fig, ax = plt.subplots(figsize=(13, 5))
        bars = ax.bar(df["hour"], df["crime_count"], color=colors, edgecolor="white", linewidth=0.5)
        ax.set_xlabel("Hour of Day (0–23)", fontsize=11)
        ax.set_ylabel("Crime Count", fontsize=11)
        ax.set_title("Crime by Hour of Day  (red = peak hour)", fontsize=13, fontweight="bold")
        ax.set_xticks(range(24))
        ax.set_xticklabels([f"{h:02d}h" for h in range(24)], fontsize=8, rotation=45)
        ax.grid(axis="y", alpha=0.3)
        ax.spines["top"].set_visible(False); ax.spines["right"].set_visible(False)
        # Annotate peak
        peak_row = df[df["is_peak"]].iloc[0]
        ax.annotate(f"Peak: {int(peak_row['crime_count']):,}\nat {int(peak_row['hour']):02d}:00",
                    xy=(peak_row["hour"], peak_row["crime_count"]),
                    xytext=(5, 8), textcoords="offset points",
                    fontsize=9, color="#d62728", fontweight="bold")
        plt.tight_layout(); figs["hourly"] = fig

    if "monthly" in periods:
        df = periods["monthly"]
        labels = df["display"].tolist()
        colors = ["#d62728" if p else "#2ecc71" for p in df["is_peak"]]
        fig, ax = plt.subplots(figsize=(12, 5))
        ax.bar(labels, df["crime_count"], color=colors, edgecolor="white", linewidth=0.5)
        ax.set_xlabel("Month", fontsize=11)
        ax.set_ylabel("Crime Count", fontsize=11)
        ax.set_title("Crime by Month  (red = peak month)", fontsize=13, fontweight="bold")
        ax.grid(axis="y", alpha=0.3)
        ax.spines["top"].set_visible(False); ax.spines["right"].set_visible(False)
        plt.tight_layout(); figs["monthly"] = fig

    if "yearly" in periods:
        df = periods["yearly"]
        fig, ax = plt.subplots(figsize=(11, 5))
        ax.plot(df["year"], df["crime_count"], marker="o", linewidth=2.5,
                color="#2c3e50", markersize=7, markerfacecolor="#e74c3c")
        ax.fill_between(df["year"], df["crime_count"], alpha=0.12, color="#2c3e50")
        ax.set_xlabel("Year", fontsize=11); ax.set_ylabel("Crime Count", fontsize=11)
        ax.set_title("Crime Trend by Year", fontsize=13, fontweight="bold")
        ax.grid(True, linestyle="--", alpha=0.4)
        ax.spines["top"].set_visible(False); ax.spines["right"].set_visible(False)
        plt.tight_layout(); figs["yearly"] = fig

    return figs


# ─────────────────────────────────────────────────────────────────────────────
# NEW VISUAL 1 — Single clock-rose (all hours)   FIX v4
# ─────────────────────────────────────────────────────────────────────────────
def plot_clock_polar(periods: dict) -> plt.Figure:
    """
    Clock-rose polar bar: total crime by hour.
    Green-orange-red colour scale.  12 o'clock = 00:00, clockwise.
    FIX v4: no embedded colorbar (was squeezing the polar), uses annotation instead.
    """
    if "hourly" not in periods or periods["hourly"].empty:
        fig, ax = plt.subplots(figsize=(7, 7))
        ax.text(0.5, 0.5, "No hourly data", ha="center", va="center", fontsize=12)
        return fig

    hourly = periods["hourly"]
    counts = hourly.set_index("hour").reindex(range(24), fill_value=0)["crime_count"].values.astype(float)
    hours  = np.arange(24)
    angles = hours / 24 * 2 * np.pi
    width  = (2 * np.pi / 24) * 0.88

    norm       = Normalize(vmin=0, vmax=counts.max())
    bar_colors = _GREEN_BROWN(norm(counts))

    fig = plt.figure(figsize=(9, 9))
    ax  = fig.add_subplot(111, polar=True)
    ax.set_theta_zero_location("N")
    ax.set_theta_direction(-1)

    ax.bar(angles, counts, width=width, bottom=0.0,
           color=bar_colors, edgecolor="white", linewidth=0.6, alpha=0.93)

    # Hour labels every 3 hours
    sparse = list(range(0, 24, 3))
    ax.set_xticks([h / 24 * 2 * np.pi for h in sparse])
    ax.set_xticklabels([f"{h:02d}:00" for h in sparse], fontsize=10)
    ax.set_yticks([]); ax.yaxis.set_tick_params(labelleft=False)

    # Radial guide labels
    r_ticks = np.linspace(0, counts.max(), 4)[1:]
    ax.set_rticks(r_ticks)
    ax.set_yticklabels([f"{int(r):,}" for r in r_ticks], fontsize=8, color="#555")
    ax.set_rlabel_position(45)

    ax.set_title("Crimes by Hour — Clock Plot", pad=20, fontsize=14, fontweight="bold")

    # Colour legend as patches (no colorbar squeezing)
    legend_patches = [
        Patch(color=_GREEN_BROWN(0.0), label="Low activity"),
        Patch(color=_GREEN_BROWN(0.5), label="Mid activity"),
        Patch(color=_GREEN_BROWN(1.0), label="High activity"),
    ]
    ax.legend(handles=legend_patches, loc="lower left",
              bbox_to_anchor=(-0.18, -0.08), fontsize=9, framealpha=0.9,
              title="Crime intensity", title_fontsize=9)

    # Peak annotation
    peak_h = int(hourly.loc[hourly["is_peak"], "hour"].iloc[0])
    peak_c = int(hourly.loc[hourly["is_peak"], "crime_count"].iloc[0])
    ax.annotate(f"Peak: {peak_h:02d}:00\n({peak_c:,} crimes)",
                xy=(peak_h / 24 * 2 * np.pi, peak_c),
                xytext=(0.82, 0.92), textcoords="figure fraction",
                fontsize=9, color="#c0392b", fontweight="bold",
                bbox=dict(boxstyle="round,pad=0.3", facecolor="white",
                          edgecolor="#c0392b", alpha=0.9))

    plt.tight_layout()
    return fig


# ─────────────────────────────────────────────────────────────────────────────
# NEW VISUAL 2 — 7-panel DOW clock grid   FIX v4
# ─────────────────────────────────────────────────────────────────────────────
def plot_clock_by_day_of_week(periods: dict) -> plt.Figure:
    """
    2-row × 4-col grid (7 panels + 1 info panel).
    Consistent green-orange-red colour scale. Shared colourbar on right.
    FIX v4: constrained_layout + dedicated colourbar axis = no clipping.
    """
    dow_df = periods.get("dow_hour_df")
    if dow_df is None or (isinstance(dow_df, pd.DataFrame) and dow_df.empty):
        fig, ax = plt.subplots(figsize=(10, 4))
        ax.text(0.5, 0.5,
                "Day-of-week data not available.\n"
                "OCC_DOW or OCC_DATE column required.",
                ha="center", va="center", fontsize=11,
                bbox=dict(boxstyle="round", facecolor="#fff3cd", alpha=0.8))
        ax.axis("off"); ax.set_title("Crimes by Hour — Day of Week Grid")
        return fig

    days   = [d for d in DAY_ORDER if d in dow_df.index]
    hours  = np.arange(24)
    angles = hours / 24 * 2 * np.pi
    width  = (2 * np.pi / 24) * 0.88

    global_max = max(int(dow_df.values.max()), 1)
    norm       = Normalize(vmin=0, vmax=global_max)

    # 2 rows × 4 cols; last cell used for shared colorbar
    fig, axes = plt.subplots(2, 4, figsize=(22, 12),
                              subplot_kw={"polar": True},
                              constrained_layout=True)
    fig.suptitle("Crimes by Hour for Each Day of Week",
                 fontsize=16, fontweight="bold", y=1.02)

    sparse = range(0, 24, 3)
    sparse_angles = [h / 24 * 2 * np.pi for h in sparse]

    for idx, day in enumerate(days):
        row, col = divmod(idx, 4)
        ax = axes[row, col]
        counts = dow_df.loc[day].reindex(range(24), fill_value=0).values.astype(float)

        ax.set_theta_zero_location("N"); ax.set_theta_direction(-1)
        ax.bar(angles, counts, width=width, bottom=0.0,
               color=_GREEN_BROWN(norm(counts)), edgecolor="white",
               linewidth=0.4, alpha=0.93)
        ax.set_xticks(sparse_angles)
        ax.set_xticklabels([f"{h:02d}h" for h in sparse], fontsize=8)
        ax.set_yticks([])

        peak_h  = int(np.argmax(counts))
        peak_c  = int(counts.max())
        ax.set_title(f"{day}\nPeak: {peak_h:02d}:00 ({peak_c:,})",
                     fontsize=10, fontweight="bold", pad=10)

    # Hide the 8th (unused) panel and use it for colourbar
    cbar_ax = axes[1, 3]
    cbar_ax.remove()
    cbar_ax = fig.add_axes([0.78, 0.12, 0.015, 0.7])
    sm = plt.cm.ScalarMappable(cmap=_GREEN_BROWN, norm=norm)
    sm.set_array([])
    cb = fig.colorbar(sm, cax=cbar_ax)
    cb.set_label("Incidents per hour slot", fontsize=10)
    cb.ax.tick_params(labelsize=9)

    return fig


# ─────────────────────────────────────────────────────────────────────────────
# NEW VISUAL 3 — Time-block weekly line chart   FIX v4
# ─────────────────────────────────────────────────────────────────────────────
def plot_time_block_weekly(periods: dict) -> plt.Figure:
    """
    3-panel line chart: 07-15h / 15-23h / 23-07h.
    X = day of week, Y = incident count, one line per MCI category.
    FIX v4: marker sizes, linewidths, legend below panels, shaded area.
    """
    tb_df = periods.get("timeblock_dow_cat")
    if tb_df is None or (isinstance(tb_df, pd.DataFrame) and tb_df.empty):
        fig, ax = plt.subplots(figsize=(12, 4))
        ax.text(0.5, 0.5,
                "Time-block data not available.\n"
                "OCC_DOW and MCI_CATEGORY required.",
                ha="center", va="center", fontsize=11,
                bbox=dict(boxstyle="round", facecolor="#fff3cd", alpha=0.8))
        ax.axis("off"); ax.set_title("Weekly Crime Patterns by Time-Block")
        return fig

    time_blocks  = ["07-15h", "15-23h", "23-07h"]
    default_clrs = ["#c0392b","#2980b9","#27ae60","#e67e22","#8e44ad","#16a085","#7f8c8d"]

    fig, axes = plt.subplots(1, 3, figsize=(21, 7), sharey=False,
                              constrained_layout=True)
    fig.suptitle("Weekly Crime Patterns by Patrol Shift & Category",
                 fontsize=15, fontweight="bold")

    all_cats = sorted(tb_df[MCI_COL].unique()) if MCI_COL in tb_df.columns else []
    x_pos    = list(range(7))
    day_lbls = [d[:3] for d in DAY_ORDER]  # Mon/Tue/Wed…

    legend_handles = []
    for ax_idx, tb in enumerate(time_blocks):
        ax  = axes[ax_idx]
        sub = tb_df[tb_df[TIME_BLOCK_COL] == tb]
        if sub.empty:
            ax.set_title(tb, fontsize=12, fontweight="bold"); continue

        pivot = (sub.groupby([OCC_DOW_COL, MCI_COL])["count"]
                 .sum().unstack(fill_value=0)
                 .reindex(DAY_ORDER, fill_value=0))

        for i, cat in enumerate(pivot.columns):
            color = _PALETTE.get(cat, default_clrs[i % len(default_clrs)])
            y     = pivot[cat].values.astype(float)
            line, = ax.plot(x_pos, y, marker="o", label=cat,
                            color=color, linewidth=2.5, markersize=8,
                            markeredgecolor="white", markeredgewidth=1.2)
            ax.fill_between(x_pos, y, alpha=0.07, color=color)
            if ax_idx == 0:
                legend_handles.append(line)

        ax.set_title(tb, fontsize=13, fontweight="bold",
                     color={"07-15h":"#f39c12","15-23h":"#c0392b","23-07h":"#2c3e50"}[tb])
        ax.set_xticks(x_pos)
        ax.set_xticklabels(day_lbls, fontsize=10)
        ax.set_ylabel("Incidents" if ax_idx == 0 else "", fontsize=11)
        ax.grid(axis="y", alpha=0.3, linestyle="--")
        ax.spines["top"].set_visible(False); ax.spines["right"].set_visible(False)

    # Shared legend below all panels
    if legend_handles:
        fig.legend(legend_handles, [h.get_label() for h in legend_handles],
                   loc="lower center", ncol=min(len(legend_handles), 4),
                   bbox_to_anchor=(0.5, -0.08), fontsize=10,
                   title="Crime Category  (MCI_CATEGORY)", title_fontsize=10,
                   frameon=True, framealpha=0.95, edgecolor="#ccc")

    return fig
