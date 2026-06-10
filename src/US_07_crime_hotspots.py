# US-07 — Identify Crime Hotspots
# INPUT : cleaned_toronto_crime.csv  (pd.DataFrame passed in)
# OUTPUT: hotspot_summary.csv + scatter map + folium HTML map
#
# REVISED v3:
#   - plot_area_timeblock_clock() now checks TIME_BLOCK gracefully
#   - Falls back to info panel if TIME_BLOCK missing

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import Normalize, LinearSegmentedColormap

LAT_COL           = "LAT_WGS84"
LON_COL           = "LONG_WGS84"
NEIGHBOURHOOD_COL = "NEIGHBOURHOOD_158"
OFFENCE_COL       = "OFFENCE"
OCC_HOUR_COL      = "OCC_HOUR"
TIME_BLOCK_COL    = "TIME_BLOCK"

LAT_MIN, LAT_MAX = 43.58, 43.86
LON_MIN, LON_MAX = -79.64, -79.11
TIME_BLOCKS      = ["07-15h", "15-23h", "23-07h"]
_GREEN_BROWN     = LinearSegmentedColormap.from_list("green_brown", ["#2ecc71", "#8B4513"])


# ─────────────────────────────────────────────────────────────────────────────
# DATA FUNCTION
# ─────────────────────────────────────────────────────────────────────────────
def get_hotspot_summary(
    cleaned_df: pd.DataFrame,
    top_n: int = 10,
    output_path: str = None
) -> pd.DataFrame:
    """
    Compute crime count + average coordinates per neighbourhood.
    INPUT : cleaned pd.DataFrame
    OUTPUT: pd.DataFrame [NEIGHBOURHOOD_158, crime_count, avg_lat, avg_lon]
    """
    valid = cleaned_df[
        cleaned_df[LAT_COL].between(LAT_MIN, LAT_MAX) &
        cleaned_df[LON_COL].between(LON_MIN, LON_MAX)
    ].copy()

    summary = (
        valid.groupby(NEIGHBOURHOOD_COL)
        .agg(
            crime_count=(NEIGHBOURHOOD_COL, "count"),
            avg_lat=(LAT_COL, "mean"),
            avg_lon=(LON_COL, "mean")
        )
        .reset_index()
        .sort_values("crime_count", ascending=False)
        .head(top_n)
        .reset_index(drop=True)
    )

    if output_path:
        summary.to_csv(output_path, index=False)
        print(f"[US-07] Hotspot summary saved -> {output_path}")
    print(f"[US-07] Top {top_n} hotspot neighbourhoods identified.")
    return summary


# ─────────────────────────────────────────────────────────────────────────────
# ORIGINAL SCATTER MAP
# ─────────────────────────────────────────────────────────────────────────────
def plot_hotspot_scatter(
    cleaned_df: pd.DataFrame,
    hotspot_summary: pd.DataFrame
) -> plt.Figure:
    """Scatter map with top neighbourhood labels."""
    valid  = cleaned_df[
        cleaned_df[LAT_COL].between(LAT_MIN, LAT_MAX) &
        cleaned_df[LON_COL].between(LON_MIN, LON_MAX)
    ]
    sample = valid.sample(n=min(10000, len(valid)), random_state=42)

    fig, ax = plt.subplots(figsize=(12, 10))
    ax.scatter(sample[LON_COL], sample[LAT_COL],
               alpha=0.12, s=4, color="#1f77b4", label="Crime incident")

    for _, row in hotspot_summary.iterrows():
        ax.scatter(row["avg_lon"], row["avg_lat"],
                   s=120, color="#d62728", zorder=5)
        ax.annotate(row[NEIGHBOURHOOD_COL],
                    xy=(row["avg_lon"], row["avg_lat"]),
                    xytext=(4, 4), textcoords="offset points",
                    fontsize=8, color="#c0392b", fontweight="bold")

    ax.set_xlabel("Longitude", fontsize=11)
    ax.set_ylabel("Latitude", fontsize=11)
    ax.set_title("Toronto Crime Hotspots — Top Neighbourhoods", fontsize=13, fontweight="bold")
    ax.grid(True, linestyle="--", alpha=0.3)
    plt.tight_layout()
    return fig


# ─────────────────────────────────────────────────────────────────────────────
# ORIGINAL FOLIUM MAP
# ─────────────────────────────────────────────────────────────────────────────
def build_folium_map(
    cleaned_df: pd.DataFrame,
    hotspot_summary: pd.DataFrame,
    output_html: str = None,
    sample_size: int = 3000
) -> object:
    """Interactive Folium MarkerCluster map."""
    try:
        import folium
        from folium.plugins import MarkerCluster
    except ImportError:
        print("[US-07] folium not installed. Run: pip install folium"); return None

    top_hoods = hotspot_summary[NEIGHBOURHOOD_COL].tolist()
    map_df = cleaned_df[
        cleaned_df[NEIGHBOURHOOD_COL].isin(top_hoods) &
        cleaned_df[LAT_COL].between(LAT_MIN, LAT_MAX) &
        cleaned_df[LON_COL].between(LON_MIN, LON_MAX)
    ].sample(n=min(sample_size, len(cleaned_df)), random_state=42)

    toronto_map = folium.Map(location=[43.6532, -79.3832], zoom_start=11)
    cluster     = MarkerCluster().add_to(toronto_map)
    for _, row in map_df.iterrows():
        folium.Marker(
            location=[row[LAT_COL], row[LON_COL]],
            popup=f"Neighbourhood: {row[NEIGHBOURHOOD_COL]}<br>Offence: {row[OFFENCE_COL]}"
        ).add_to(cluster)

    if output_html:
        toronto_map.save(output_html)
        print(f"[US-07] Folium map saved -> {output_html}")
    return toronto_map


# ─────────────────────────────────────────────────────────────────────────────
# NEW VISUAL — Top areas × Time-block clock-rose grid
# ─────────────────────────────────────────────────────────────────────────────
def plot_area_timeblock_clock(
    cleaned_df: pd.DataFrame,
    hotspot_summary: pd.DataFrame = None,
    top_n: int = 4
) -> plt.Figure:
    """
    Grid: rows = top_n neighbourhoods, cols = 3 time-blocks.
    Each cell = clock-rose. Green (low) -> brown (high).
    Requires TIME_BLOCK column (derived by US-02).
    """
    needed  = [NEIGHBOURHOOD_COL, OCC_HOUR_COL, TIME_BLOCK_COL]
    missing = [c for c in needed if c not in cleaned_df.columns]
    if missing:
        fig, ax = plt.subplots(figsize=(10, 3))
        ax.text(0.5, 0.5,
                f"Area time-block clock not available.\nMissing columns: {missing}\n"
                f"Ensure US-02 clean_dataset() runs before US-07.",
                ha="center", va="center", fontsize=11,
                bbox=dict(boxstyle="round", facecolor="#fff3cd", alpha=0.8))
        ax.axis("off")
        ax.set_title("Crime Clock Plots by Time-Block for Top Areas", fontsize=12)
        return fig

    # Top areas
    if hotspot_summary is not None and not hotspot_summary.empty:
        top_areas = hotspot_summary[NEIGHBOURHOOD_COL].head(top_n).tolist()
    else:
        top_areas = cleaned_df[NEIGHBOURHOOD_COL].value_counts().head(top_n).index.tolist()

    hours = np.arange(24); angles = hours / 24 * 2 * np.pi; width = 2 * np.pi / 24
    sparse_hours  = [0, 6, 12, 18]
    sparse_angles = [h / 24 * 2 * np.pi for h in sparse_hours]

    n_rows = len(top_areas)
    fig, axes = plt.subplots(
        n_rows, 3, figsize=(3 * 5, n_rows * 5),
        subplot_kw={"polar": True}
    )
    if n_rows == 1: axes = axes[np.newaxis, :]

    fig.suptitle(
        f"Crime Clock Plots by Time-Block — Top {top_n} Areas\n(green = low, brown = high)",
        fontsize=14, fontweight="bold", y=1.02
    )

    for row_idx, area in enumerate(top_areas):
        area_df = cleaned_df[cleaned_df[NEIGHBOURHOOD_COL] == area]
        for col_idx, tb in enumerate(TIME_BLOCKS):
            ax    = axes[row_idx, col_idx]
            tb_df = area_df[area_df[TIME_BLOCK_COL] == tb]
            counts = (
                tb_df[OCC_HOUR_COL].dropna().astype(int)
                .value_counts().reindex(range(24), fill_value=0)
                .sort_index().values.astype(float)
            )
            norm       = Normalize(vmin=0, vmax=max(counts.max(), 1))
            bar_colors = _GREEN_BROWN(norm(counts))
            ax.set_theta_zero_location("N"); ax.set_theta_direction(-1)
            ax.bar(angles, counts, width=width * 0.9, bottom=0.0,
                   color=bar_colors, edgecolor="white", linewidth=0.3, alpha=0.92)
            ax.set_xticks(sparse_angles)
            ax.set_xticklabels([f"{h:02d}:00" for h in sparse_hours], fontsize=7)
            ax.set_yticks([])
            if row_idx == 0:
                ax.set_title(tb, fontsize=11, pad=10, fontweight="bold")
            if col_idx == 0:
                ax.text(-0.3, 0.5, area, transform=ax.transAxes,
                        fontsize=8, fontweight="bold", va="center", ha="right")

    plt.tight_layout()
    return fig
