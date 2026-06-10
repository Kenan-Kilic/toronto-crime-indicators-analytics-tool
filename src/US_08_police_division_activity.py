# US-08 — Compare Police Division Activity
# INPUT : cleaned_toronto_crime.csv  (pd.DataFrame passed in)
# OUTPUT: pd.DataFrame (division ranking) + division_activity.csv + chart

import pandas as pd
import matplotlib.pyplot as plt

DIVISION_COL = "DIVISION"


def rank_divisions(
    cleaned_df: pd.DataFrame,
    output_path: str = None
) -> pd.DataFrame:
    """
    Rank Toronto Police Service divisions by total crime count.
    INPUT : cleaned pd.DataFrame
    OUTPUT: pd.DataFrame [division, crime_count, rank, pct]
    """
    if DIVISION_COL not in cleaned_df.columns:
        raise ValueError(f"Column not found: {DIVISION_COL}")

    div_df = (
        cleaned_df[DIVISION_COL]
        .dropna()
        .value_counts()
        .reset_index()
    )
    div_df.columns = ["division", "crime_count"]
    div_df["rank"] = div_df["crime_count"].rank(method="dense", ascending=False).astype(int)
    div_df["pct"]  = (div_df["crime_count"] / div_df["crime_count"].sum() * 100).round(2)
    div_df = div_df.sort_values("crime_count", ascending=False).reset_index(drop=True)

    if output_path:
        div_df.to_csv(output_path, index=False)
        print(f"[US-08] Division ranking saved -> {output_path}")

    print(f"[US-08] {len(div_df)} divisions ranked.")
    return div_df


def plot_division_ranking(div_df: pd.DataFrame) -> plt.Figure:
    """Horizontal bar chart of division crime counts."""
    fig, ax = plt.subplots(figsize=(10, 6))
    colors = ["#d62728" if i == 0 else "#1f77b4" for i in range(len(div_df))]
    ax.barh(div_df["division"], div_df["crime_count"], color=colors)
    ax.invert_yaxis()
    ax.set_xlabel("Crime Count")
    ax.set_ylabel("Division")
    ax.set_title("Crime Count by Toronto Police Division  (red = highest)")
    plt.tight_layout()
    return fig


def plot_division_pie(div_df: pd.DataFrame, top_n: int = 10) -> plt.Figure:
    """Pie chart showing share of crimes per division."""
    top = div_df.head(top_n).copy()
    other_count = div_df.iloc[top_n:]["crime_count"].sum()
    if other_count > 0:
        other_row = pd.DataFrame([{"division": "Other", "crime_count": other_count}])
        top = pd.concat([top, other_row], ignore_index=True)

    fig, ax = plt.subplots(figsize=(8, 8))
    ax.pie(top["crime_count"], labels=top["division"], autopct="%1.1f%%", startangle=140)
    ax.set_title(f"Crime Share by Division (Top {top_n})")
    plt.tight_layout()
    return fig
