# US-14 — Analyze Year-over-Year Crime Trend
# INPUT : cleaned_toronto_crime.csv  (pd.DataFrame passed in)
# OUTPUT: pd.DataFrame (yearly trend) + yoy_crime_trend.csv + chart

import pandas as pd
import matplotlib.pyplot as plt

OCC_YEAR_COL = "OCC_YEAR"


def compute_yoy_trend(
    cleaned_df: pd.DataFrame,
    output_path: str = None
) -> pd.DataFrame:
    """
    Compute year-over-year crime counts and percentage change.
    INPUT : cleaned pd.DataFrame
    OUTPUT: pd.DataFrame [year, crime_count, pct_change, is_peak, is_lowest]

    Acceptance Criteria:
      ✓ Year-over-year line chart displayed
      ✓ Peak and lowest crime years highlighted
      ✓ Percentage change calculated year-over-year
      ✓ crime_clean dataset used
    """
    if OCC_YEAR_COL not in cleaned_df.columns:
        raise ValueError(f"Column not found: {OCC_YEAR_COL}")

    trend_df = (
        cleaned_df[OCC_YEAR_COL]
        .dropna()
        .astype(int)
        .value_counts()
        .sort_index()
        .reset_index()
    )
    trend_df.columns = ["year", "crime_count"]

    # Percentage change YoY
    trend_df["pct_change"] = trend_df["crime_count"].pct_change() * 100
    trend_df["pct_change"] = trend_df["pct_change"].round(2)

    # Peak and lowest years
    trend_df["is_peak"]   = trend_df["crime_count"] == trend_df["crime_count"].max()
    trend_df["is_lowest"] = trend_df["crime_count"] == trend_df["crime_count"].min()

    if output_path:
        trend_df.to_csv(output_path, index=False)
        print(f"[US-14] YoY trend saved -> {output_path}")

    peak_year   = trend_df.loc[trend_df["is_peak"],   "year"].iloc[0]
    lowest_year = trend_df.loc[trend_df["is_lowest"], "year"].iloc[0]
    print(f"[US-14] Peak year  : {peak_year}  ({trend_df.loc[trend_df['is_peak'],   'crime_count'].iloc[0]:,} crimes)")
    print(f"[US-14] Lowest year: {lowest_year} ({trend_df.loc[trend_df['is_lowest'], 'crime_count'].iloc[0]:,} crimes)")

    return trend_df


def plot_yoy_trend(trend_df: pd.DataFrame) -> plt.Figure:
    """
    Line chart with peak (red) and lowest (green) year markers.
    INPUT : yoy trend pd.DataFrame
    OUTPUT: matplotlib Figure
    """
    fig, ax = plt.subplots(figsize=(12, 6))

    ax.plot(
        trend_df["year"],
        trend_df["crime_count"],
        marker="o",
        linewidth=2,
        color="#1f77b4",
        label="Annual Crime Count"
    )

    # Highlight peak year
    peak = trend_df[trend_df["is_peak"]]
    ax.scatter(peak["year"], peak["crime_count"], color="red", s=120, zorder=5, label="Peak Year")
    for _, row in peak.iterrows():
        ax.annotate(
            f"Peak\n{int(row['year'])}\n({int(row['crime_count']):,})",
            xy=(row["year"], row["crime_count"]),
            xytext=(10, 10), textcoords="offset points",
            color="red", fontsize=9, fontweight="bold"
        )

    # Highlight lowest year
    low = trend_df[trend_df["is_lowest"]]
    ax.scatter(low["year"], low["crime_count"], color="green", s=120, zorder=5, label="Lowest Year")
    for _, row in low.iterrows():
        ax.annotate(
            f"Lowest\n{int(row['year'])}\n({int(row['crime_count']):,})",
            xy=(row["year"], row["crime_count"]),
            xytext=(10, -25), textcoords="offset points",
            color="green", fontsize=9, fontweight="bold"
        )

    ax.set_xlabel("Year")
    ax.set_ylabel("Crime Count")
    ax.set_title("Year-over-Year Crime Trend in Toronto")
    ax.legend()
    ax.grid(True, linestyle="--", alpha=0.5)
    plt.tight_layout()
    return fig


def plot_yoy_pct_change(trend_df: pd.DataFrame) -> plt.Figure:
    """
    Bar chart showing % change year-over-year.
    INPUT : yoy trend pd.DataFrame
    OUTPUT: matplotlib Figure
    """
    df = trend_df.dropna(subset=["pct_change"])
    colors = ["#d62728" if v > 0 else "#2ca02c" for v in df["pct_change"]]

    fig, ax = plt.subplots(figsize=(12, 5))
    ax.bar(df["year"], df["pct_change"], color=colors)
    ax.axhline(0, color="black", linewidth=0.8, linestyle="--")
    ax.set_xlabel("Year")
    ax.set_ylabel("% Change vs Previous Year")
    ax.set_title("Year-over-Year % Change in Crime (red = increase, green = decrease)")
    plt.tight_layout()
    return fig
