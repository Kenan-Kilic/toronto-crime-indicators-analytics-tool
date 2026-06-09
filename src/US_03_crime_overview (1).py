# US-03 — Generate Toronto Crime Risk Overview
# INPUT : pd.DataFrame (cleaned)
# OUTPUT: dict of KPIs + crime_overview_kpis.csv

import pandas as pd

OFFENCE_COL       = "OFFENCE"
NEIGHBOURHOOD_COL = "NEIGHBOURHOOD_158"


def generate_crime_overview(cleaned_df: pd.DataFrame, output_path: str) -> dict:
    offences = cleaned_df[OFFENCE_COL].dropna()
    hoods    = cleaned_df[NEIGHBOURHOOD_COL].dropna()

    kpis = {
        "total_crimes":
            len(cleaned_df),
        "most_common_offence":
            offences.mode().iloc[0] if not offences.empty else "N/A",
        "most_common_offence_count":
            int(offences.value_counts().max()) if not offences.empty else 0,
        "highest_crime_neighbourhood":
            hoods.value_counts().idxmax() if not hoods.empty else "N/A",
        "highest_crime_neighbourhood_count":
            int(hoods.value_counts().max()) if not hoods.empty else 0,
        "total_neighbourhoods":
            int(hoods.nunique()),
        "total_offence_types":
            int(offences.nunique()),
    }

    pd.DataFrame([kpis]).to_csv(output_path, index=False)
    print(f"[US-03] Overview saved -> {output_path}")
    return kpis
