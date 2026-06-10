# US-06 — Analyze Crime Type Distribution
# INPUT : cleaned_toronto_crime.csv (pd.DataFrame passed in)
# OUTPUT: dist_df + crime_type_distribution.csv + 3 charts
#
# REVISED v4 — Final:
#   - plot_category_clock_by_day: proper panel size (no half-visible charts)
#   - Uses subplots_adjust (not tight_layout) for stable layout
#   - Bigger figure, wider panels, readable tick labels

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import Normalize, LinearSegmentedColormap
from matplotlib.patches import Patch

OFFENCE_COL  = "OFFENCE"
MCI_COL      = "MCI_CATEGORY"
OCC_HOUR_COL = "OCC_HOUR"
OCC_DOW_COL  = "OCC_DOW"

DAY_ORDER     = ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]
_ORANGE_RED   = LinearSegmentedColormap.from_list("orange_red", ["#fef9e7","#f39c12","#c0392b"])


# ─────────────────────────────────────────────────────────────────────────────
# DATA FUNCTIONS (unchanged API)
# ─────────────────────────────────────────────────────────────────────────────
def get_offence_distribution(
    cleaned_df: pd.DataFrame,
    top_n: int = 15,
    output_path: str = None
) -> pd.DataFrame:
    if OFFENCE_COL not in cleaned_df.columns:
        raise ValueError(f"Column not found: {OFFENCE_COL}")
    dist_df = cleaned_df[OFFENCE_COL].dropna().value_counts().reset_index()
    dist_df.columns = ["offence", "crime_count"]
    dist_df["pct"] = (dist_df["crime_count"] / dist_df["crime_count"].sum() * 100).round(2)
    dist_df = dist_df.head(top_n).reset_index(drop=True)
    if output_path:
        dist_df.to_csv(output_path, index=False)
        print(f"[US-06] Saved -> {output_path}")
    print(f"[US-06] Top {top_n} offence types identified.")
    return dist_df


def get_category_distribution(
    cleaned_df: pd.DataFrame,
    output_path: str = None
) -> pd.DataFrame:
    if MCI_COL not in cleaned_df.columns:
        print(f"[US-06] Warning: {MCI_COL} not found — skipping category distribution.")
        return pd.DataFrame()
    cat_df = cleaned_df[MCI_COL].dropna().value_counts().reset_index()
    cat_df.columns = ["category", "crime_count"]
    cat_df["pct"] = (cat_df["crime_count"] / cat_df["crime_count"].sum() * 100).round(2)
    if output_path:
        cat_df.to_csv(output_path, index=False)
        print(f"[US-06] Category saved -> {output_path}")
    return cat_df


# ─────────────────────────────────────────────────────────────────────────────
# ORIGINAL PLOT FUNCTIONS   FIX v4: better styling
# ─────────────────────────────────────────────────────────────────────────────
def plot_offence_distribution(dist_df: pd.DataFrame) -> plt.Figure:
    """Horizontal bar chart — top N offence types."""
    fig, ax = plt.subplots(figsize=(12, 8))
    colors = ["#d62728"] + ["#2980b9"] * (len(dist_df) - 1)
    bars = ax.barh(dist_df["offence"], dist_df["crime_count"],
                   color=colors, edgecolor="white", linewidth=0.5)
    ax.invert_yaxis()
    # Value labels
    for bar, pct in zip(bars, dist_df["pct"]):
        ax.text(bar.get_width() + dist_df["crime_count"].max() * 0.01,
                bar.get_y() + bar.get_height() / 2,
                f"{pct:.1f}%", va="center", fontsize=8, color="#555")
    ax.set_xlabel("Crime Count", fontsize=11)
    ax.set_title("Top Offence Types in Toronto", fontsize=14, fontweight="bold")
    ax.spines["top"].set_visible(False); ax.spines["right"].set_visible(False)
    ax.grid(axis="x", alpha=0.3)
    plt.tight_layout()
    return fig


def plot_category_pie(cat_df: pd.DataFrame) -> plt.Figure:
    """Pie chart of MCI crime categories."""
    if cat_df.empty:
        fig, ax = plt.subplots()
        ax.text(0.5, 0.5, "No MCI_CATEGORY data", ha="center", va="center")
        return fig
    colors = ["#c0392b","#2980b9","#27ae60","#e67e22","#8e44ad","#16a085","#7f8c8d"]
    fig, ax = plt.subplots(figsize=(10, 10))
    wedges, texts, autotexts = ax.pie(
        cat_df["crime_count"],
        labels=cat_df["category"],
        autopct="%1.1f%%",
        startangle=140,
        colors=colors[:len(cat_df)],
        wedgeprops={"edgecolor": "white", "linewidth": 2},
        pctdistance=0.82,
        explode=[0.03] * len(cat_df),
    )
    for t in texts: t.set_fontsize(11)
    for a in autotexts: a.set_fontsize(9); a.set_fontweight("bold")
    ax.set_title("Crime Category Distribution (MCI_CATEGORY)",
                 fontsize=14, fontweight="bold", pad=20)
    plt.tight_layout()
    return fig


# ─────────────────────────────────────────────────────────────────────────────
# NEW VISUAL — Category × Day clock-rose grid   FIX v4
# ─────────────────────────────────────────────────────────────────────────────
def plot_category_clock_by_day(
    cleaned_df: pd.DataFrame,
    top_n_categories: int = 3
) -> plt.Figure:
    """
    Grid: rows = top_n_categories, cols = 7 days of week.
    Each cell = clock-rose (hourly crime count).
    FIX v4: explicit per-panel size, subplots_adjust, no tight_layout clipping.

    INPUT : cleaned pd.DataFrame  (MCI_CATEGORY, OCC_DOW, OCC_HOUR required)
    OUTPUT: matplotlib Figure
    """
    needed  = [MCI_COL, OCC_DOW_COL, OCC_HOUR_COL]
    missing = [c for c in needed if c not in cleaned_df.columns]
    if missing:
        fig, ax = plt.subplots(figsize=(10, 3))
        ax.text(0.5, 0.5,
                f"Category clock grid not available.\nMissing: {missing}",
                ha="center", va="center", fontsize=11,
                bbox=dict(boxstyle="round", facecolor="#fff3cd", alpha=0.8))
        ax.axis("off"); ax.set_title("Crime Clock-Plots by Day & Category")
        return fig

    df = cleaned_df[cleaned_df[OCC_DOW_COL].isin(DAY_ORDER)].copy()
    if df.empty:
        fig, ax = plt.subplots()
        ax.text(0.5, 0.5, "No valid OCC_DOW rows", ha="center", va="center")
        return fig

    top_cats = df[MCI_COL].value_counts().head(top_n_categories).index.tolist()

    hours  = np.arange(24)
    angles = hours / 24 * 2 * np.pi
    width  = (2 * np.pi / 24) * 0.85

    # Fixed panel size: 3.2 wide × 3.2 tall per panel
    panel_w = 3.2
    panel_h = 3.2
    n_rows  = top_n_categories
    n_cols  = 7

    # Extra space: left margin for row labels, right margin for colorbar, top for title
    left_margin   = 1.2   # inches
    right_margin  = 1.4   # inches
    top_margin    = 0.9   # inches
    bottom_margin = 0.4   # inches
    h_gap = 0.35          # inches between panels horizontal
    v_gap = 0.55          # inches between panels vertical

    total_w = left_margin + n_cols * panel_w + (n_cols - 1) * h_gap + right_margin
    total_h = top_margin  + n_rows * panel_h + (n_rows - 1) * v_gap + bottom_margin

    fig = plt.figure(figsize=(total_w, total_h))

    # Compute axes positions in figure fractions
    def pos(row_idx, col_idx):
        x0 = (left_margin + col_idx * (panel_w + h_gap)) / total_w
        y0 = 1.0 - (top_margin + (row_idx + 1) * panel_h + row_idx * v_gap) / total_h
        w  = panel_w / total_w
        h  = panel_h / total_h
        return [x0, y0, w, h]

    fig.text(0.5, 1.0 - (top_margin * 0.4) / total_h,
             f"Crime Clock-Plots by Day of Week — Top {top_n_categories} MCI Categories\n"
             "(orange = low, dark red = high  |  12 o'clock = midnight)",
             ha="center", va="top", fontsize=14, fontweight="bold")

    # Day-of-week column headers
    for col_idx, day in enumerate(DAY_ORDER):
        x_center = (left_margin + col_idx * (panel_w + h_gap) + panel_w / 2) / total_w
        y_header = 1.0 - top_margin / total_h + 0.005
        fig.text(x_center, y_header, day[:3],
                 ha="center", va="bottom", fontsize=11, fontweight="bold", color="#2c3e50")

    sparse_h = [0, 6, 12, 18]
    sparse_a = [h / 24 * 2 * np.pi for h in sparse_h]

    all_axes = []
    for row_idx, cat in enumerate(top_cats):
        cat_df = df[df[MCI_COL] == cat]

        # Row label (category name)
        y_center = 1.0 - (top_margin + (row_idx + 0.5) * panel_h + row_idx * v_gap) / total_h
        fig.text(left_margin * 0.45 / total_w, y_center,
                 cat, ha="center", va="center", fontsize=10,
                 fontweight="bold", color="#2c3e50", rotation=90)

        # Per-category max for consistent colour scale across days
        day_counts = {}
        for day in DAY_ORDER:
            day_counts[day] = (
                cat_df[cat_df[OCC_DOW_COL] == day][OCC_HOUR_COL]
                .dropna().astype(int)
                .value_counts().reindex(range(24), fill_value=0)
                .sort_index().values.astype(float)
            )
        cat_max = max((v.max() for v in day_counts.values()), default=1) or 1
        norm    = Normalize(vmin=0, vmax=cat_max)

        for col_idx, day in enumerate(DAY_ORDER):
            rect = pos(row_idx, col_idx)
            ax   = fig.add_axes(rect, polar=True)
            all_axes.append(ax)

            counts = day_counts[day]
            ax.set_theta_zero_location("N"); ax.set_theta_direction(-1)
            ax.bar(angles, counts, width=width, bottom=0.0,
                   color=_ORANGE_RED(norm(counts)),
                   edgecolor="white", linewidth=0.3, alpha=0.93)

            ax.set_xticks(sparse_a)
            ax.set_xticklabels([f"{h:02d}h" for h in sparse_h], fontsize=7.5)
            ax.set_yticks([])

            # Peak annotation inside panel
            if counts.max() > 0:
                peak_h = int(np.argmax(counts))
                ax.set_title(f"{peak_h:02d}:00 ▲", fontsize=8,
                             pad=4, color="#c0392b")

    # Colourbar on the right — use a single representative norm
    global_max = max(
        df[df[MCI_COL] == cat][OCC_HOUR_COL].dropna().astype(int)
        .value_counts().max()
        for cat in top_cats
    )
    cbar_x  = (left_margin + n_cols * (panel_w + h_gap) - h_gap + 0.3) / total_w
    cbar_y  = (top_margin + 0.2) / total_h
    cbar_h  = (n_rows * panel_h + (n_rows - 1) * v_gap - 0.4) / total_h
    cbar_ax = fig.add_axes([cbar_x, cbar_y, 0.018, cbar_h])

    sm = plt.cm.ScalarMappable(cmap=_ORANGE_RED, norm=Normalize(0, global_max))
    sm.set_array([])
    cb = fig.colorbar(sm, cax=cbar_ax)
    cb.set_label("Incidents per hour slot", fontsize=9, labelpad=8)
    cb.ax.tick_params(labelsize=8)

    return fig
