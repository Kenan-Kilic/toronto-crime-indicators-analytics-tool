import pandas as pd


def generate_crime_overview(df: pd.DataFrame) -> dict:
    """
    Generate a high-level Toronto crime risk overview.

    Returns total crimes, most common offence,
    highest-crime neighbourhood, and total neighbourhood count.
    """
    data = df.copy()

    total_crimes = len(data)

    most_common_offence = (
        data["OFFENCE"].mode().iloc[0]
        if "OFFENCE" in data.columns and not data["OFFENCE"].dropna().empty
        else None
    )

    highest_crime_neighbourhood = (
        data["NEIGHBOURHOOD_158"].value_counts().idxmax()
        if "NEIGHBOURHOOD_158" in data.columns
        and not data["NEIGHBOURHOOD_158"].dropna().empty
        else None
    )

    total_neighbourhoods = (
        data["NEIGHBOURHOOD_158"].nunique()
        if "NEIGHBOURHOOD_158" in data.columns
        else None
    )

    return {
        "total_crimes": total_crimes,
        "most_common_offence": most_common_offence,
        "highest_crime_neighbourhood": highest_crime_neighbourhood,
        "total_neighbourhoods": total_neighbourhoods,
    }
