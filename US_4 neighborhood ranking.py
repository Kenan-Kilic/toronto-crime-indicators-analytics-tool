# US-04 — Identify High-Risk Neighbourhoods
# INPUT : pd.DataFrame (cleaned)
# OUTPUT: pd.DataFrame (ranked) + top_neighbourhoods.csv + chart

import pandas as pd
import matplotlib.pyplot as plt

NEIGHBOURHOOD_COL = "NEIGHBOURHOOD_158"


def rank_neighbourhoods(
    cleaned_df: pd.DataFrame,
    top_n: int = 10,
    output_path: str = None
) -> pd.DataFrame:
    if NEIGHBOURHOOD_COL not in cleaned_df.columns:
        raise ValueError(f"Column not found: {NEIGHBOURHOOD_COL}")

    ranking_df = (
        cleaned_df[NEIGHBOURHOOD_COL]
        .dropna()
        .value_counts()
        .reset_index()
    )
    ranking_df.columns = ["neighbourhood", "crime_count"]
    ranking_df["rank"] = (
        ranking_df["crime_count"]
        .rank(method="dense", ascending=False)
        .astype(int)
    )
    ranking_df = ranking_df.sort_values(
        ["crime_count", "neighbourhood"], ascending=[False, True]
    ).head(top_n).reset_index(drop=True)

    if output_path:
        ranking_df.to_csv(output_path, index=False)
        print(f"[US-04] Ranking saved -> {output_path}")

    return ranking_df


def plot_neighbourhood_ranking(ranking_df: pd.DataFrame) -> plt.Figure:
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.barh(ranking_df["neighbourhood"], ranking_df["crime_count"])
    ax.invert_yaxis()
    ax.set_xlabel("Crime Count")
    ax.set_ylabel("Neighbourhood")
    ax.set_title("Top High-Risk Neighbourhoods in Toronto")
    plt.tight_layout()
    return fig


def filter_neighbourhood(
    cleaned_df: pd.DataFrame,
    selected: str = None
) -> pd.DataFrame:
    if not selected or selected == "All":
        return cleaned_df
    return cleaned_df[cleaned_df[NEIGHBOURHOOD_COL] == selected]
