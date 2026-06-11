# US-13 — Generate Crime Hotspot Map (Folium)
# INPUT : cleaned_toronto_crime.csv  (pd.DataFrame passed in)
# OUTPUT: toronto_hotspot_map.html  (interactive Folium map)

import pandas as pd

LAT_COL           = "LAT_WGS84"
LON_COL           = "LONG_WGS84"
NEIGHBOURHOOD_COL = "NEIGHBOURHOOD_158"
OFFENCE_COL       = "OFFENCE"

LAT_MIN, LAT_MAX  = 43.58, 43.86
LON_MIN, LON_MAX  = -79.64, -79.11


def build_hotspot_map(
    cleaned_df: pd.DataFrame,
    output_html: str = "toronto_hotspot_map.html",
    sample_size: int = 5000,
    top_n_hoods: int = 10
) -> object:
    """
    Generate a Folium MarkerCluster map of crime hotspots.
    INPUT : cleaned pd.DataFrame
    OUTPUT: folium.Map saved as HTML

    Acceptance Criteria:
      ✓ Folium map renders with crime markers
      ✓ MarkerCluster groups nearby crimes
      ✓ crime_clean dataset used (no invalid coordinates)
      ✓ Map saved as HTML output
    """
    try:
        import folium
        from folium.plugins import MarkerCluster
    except ImportError:
        print("[US-13] Installing folium...")
        import subprocess
        subprocess.run(["pip", "install", "folium", "-q"])
        import folium
        from folium.plugins import MarkerCluster

    # Filter valid coordinates
    valid_df = cleaned_df[
        cleaned_df[LAT_COL].between(LAT_MIN, LAT_MAX) &
        cleaned_df[LON_COL].between(LON_MIN, LON_MAX)
    ].copy()

    # Focus on top-N neighbourhoods
    top_hoods = (
        valid_df[NEIGHBOURHOOD_COL]
        .value_counts()
        .head(top_n_hoods)
        .index
        .tolist()
    )
    map_df = valid_df[valid_df[NEIGHBOURHOOD_COL].isin(top_hoods)]

    # Sample for performance
    map_df = map_df.sample(n=min(sample_size, len(map_df)), random_state=42)

    # Build map
    toronto_map = folium.Map(
        location=[43.6532, -79.3832],
        zoom_start=11,
        tiles="OpenStreetMap"
    )

    cluster = MarkerCluster(name="Crime Incidents").add_to(toronto_map)

    for _, row in map_df.iterrows():
        folium.Marker(
            location=[row[LAT_COL], row[LON_COL]],
            popup=folium.Popup(
                f"<b>Neighbourhood:</b> {row[NEIGHBOURHOOD_COL]}<br>"
                f"<b>Offence:</b> {row[OFFENCE_COL]}",
                max_width=250
            ),
            icon=folium.Icon(color="red", icon="info-sign")
        ).add_to(cluster)

    # Add top neighbourhood center markers
    for hood in top_hoods:
        hood_df = valid_df[valid_df[NEIGHBOURHOOD_COL] == hood]
        avg_lat = hood_df[LAT_COL].mean()
        avg_lon = hood_df[LON_COL].mean()
        count   = len(hood_df)
        folium.Marker(
            location=[avg_lat, avg_lon],
            popup=f"{hood}: {count:,} crimes",
            icon=folium.Icon(color="darkred", icon="star")
        ).add_to(toronto_map)

    folium.LayerControl().add_to(toronto_map)

    toronto_map.save(output_html)
    print(f"[US-13] Hotspot map saved -> {output_html}")
    print(f"        Markers plotted  : {len(map_df):,}")
    print(f"        Top neighbourhoods: {top_n_hoods}")

    return toronto_map
