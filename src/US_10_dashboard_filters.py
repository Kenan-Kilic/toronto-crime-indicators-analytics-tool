# US-10 — Add Dashboard Filters  (v2 — integrated into US-09 dashboard)
# INPUT : cleaned_toronto_crime.csv  (pd.DataFrame passed in)
# OUTPUT: filtered pd.DataFrame + optional filtered_results.csv
#
# NOTE: No functional changes needed in this file.
#       US-09 dashboard now imports and calls these functions directly
#       via the sidebar widgets (get_filter_options → apply_filters → filter_summary).
#       All four filter dimensions (neighbourhood, offence, year, division)
#       are wired to live st.selectbox / st.select_slider widgets that
#       re-render every chart on the active page automatically.

import pandas as pd

NEIGHBOURHOOD_COL = "NEIGHBOURHOOD_158"
OFFENCE_COL       = "OFFENCE"
OCC_YEAR_COL      = "OCC_YEAR"
DIVISION_COL      = "DIVISION"


def get_filter_options(cleaned_df: pd.DataFrame) -> dict:
    """
    Return sorted lists of unique values for each filter dimension.
    INPUT : cleaned pd.DataFrame
    OUTPUT: dict with keys [neighbourhoods, offence_types, years, divisions]
    """
    return {
        "neighbourhoods": sorted(cleaned_df[NEIGHBOURHOOD_COL].dropna().unique().tolist()),
        "offence_types":  sorted(cleaned_df[OFFENCE_COL].dropna().unique().tolist()),
        "years":          sorted(cleaned_df[OCC_YEAR_COL].dropna().unique().tolist()),
        "divisions":      sorted(cleaned_df[DIVISION_COL].dropna().unique().tolist()),
    }


def apply_filters(
    cleaned_df: pd.DataFrame,
    neighbourhood: str = "All",
    offence_type:  str = "All",
    year:          int = None,
    division:      str = "All",
    output_path:   str = None
) -> pd.DataFrame:
    """
    Apply one or more filters to the cleaned dataset.
    Pass "All" or None to skip a filter.
    INPUT : cleaned pd.DataFrame + filter values
    OUTPUT: filtered pd.DataFrame
    """
    filtered = cleaned_df.copy()

    if neighbourhood and neighbourhood != "All":
        filtered = filtered[filtered[NEIGHBOURHOOD_COL] == neighbourhood]

    if offence_type and offence_type != "All":
        filtered = filtered[filtered[OFFENCE_COL] == offence_type]

    if year is not None:
        filtered = filtered[filtered[OCC_YEAR_COL] == int(year)]

    if division and division != "All":
        filtered = filtered[filtered[DIVISION_COL] == division]

    if output_path:
        filtered.to_csv(output_path, index=False)
        print(f"[US-10] Filtered results saved -> {output_path}")

    print(f"[US-10] Filter applied | rows returned: {len(filtered):,}")
    return filtered


def filter_summary(filtered_df: pd.DataFrame) -> dict:
    """
    Quick stats on a filtered dataset.
    INPUT : filtered pd.DataFrame
    OUTPUT: dict summary
    """
    offences = filtered_df[OFFENCE_COL].dropna()
    hoods    = filtered_df[NEIGHBOURHOOD_COL].dropna()

    return {
        "total_crimes":          len(filtered_df),
        "unique_offences":       int(offences.nunique()),
        "unique_neighbourhoods": int(hoods.nunique()),
        "top_offence":           offences.mode().iloc[0] if not offences.empty else "N/A",
        "top_neighbourhood":     hoods.value_counts().idxmax() if not hoods.empty else "N/A",
    }
