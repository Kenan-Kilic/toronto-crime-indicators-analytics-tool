# Toronto Crime Analytics — Streamlit Deployment Guide

## What changed (Sprint 2 final)

| File | Status | What changed |
|---|---|---|
| `US_09_dashboard.py` | ✅ REVISED | Integrated US-10 filters + US-13 map + YoY page + polish |
| `US_10_dashboard_filters.py` | ✅ NO CHANGE NEEDED | Already correct; imported by US-09 |
| `US_13_hotspot_map.py` | ✅ NO CHANGE NEEDED | Already correct; imported by US-09 |
| `requirements.txt` | ✅ NEW | Required for Streamlit Cloud |

---

## GitHub repo layout required

```
your-repo/
├── US_09_dashboard.py          ← main app (entry point)
├── US_10_dashboard_filters.py
├── US_13_hotspot_map.py
├── US_01_data_loader.py
├── US_02_data_cleaning.py
├── ...all other US_*.py files...
├── requirements.txt
└── data/
    ├── cleaned_toronto_crime.csv   ← REQUIRED (run pipeline first)
    ├── crime_overview_kpis.csv
    ├── top_neighbourhoods.csv
    ├── crime_type_distribution.csv
    ├── peak_crime_periods.csv
    ├── division_activity.csv
    └── yoy_crime_trend.csv
```

> **Important:** `cleaned_toronto_crime.csv` is ~156 MB.
> Streamlit Cloud has a 1 GB repo limit but GitHub blocks files >100 MB.
> Use [Git LFS](https://git-lfs.github.com/) for this file, OR
> host it on Google Drive and use `gdown` to fetch it at startup
> (wrap in a `@st.cache_data` function at the top of US_09_dashboard.py).

---

## Deploying to Streamlit Cloud (share.streamlit.io)

1. Push your repo to GitHub (must be public, or private with Streamlit Cloud Pro).
2. Go to [share.streamlit.io](https://share.streamlit.io) → **New app**.
3. Select your repo, branch (`main`), and set **Main file path** to `US_09_dashboard.py`.
4. Click **Deploy**. Streamlit Cloud installs `requirements.txt` automatically.
5. Your app URL will be `https://<your-app-name>.streamlit.app`.

---

## Running locally

```bash
pip install -r requirements.txt
streamlit run US_09_dashboard.py
```

## Running in Google Colab

```python
!pip install streamlit pyngrok -q
!streamlit run US_09_dashboard.py &
from pyngrok import ngrok
print(ngrok.connect(8501))
```

---

## Dashboard pages

| Page | User Story | What it shows |
|---|---|---|
| 📊 Overview | US-03 | Live KPI metrics, annual trend chart |
| 🏘️ Neighbourhoods | US-04 | Top N high-risk neighbourhoods bar chart |
| 🔎 Crime Types | US-06 | Top N offences + MCI category pie |
| ⏰ Peak Periods | US-05 | Hour / month / year bar & line charts |
| 🚓 Police Divisions | US-08 | Division ranking bar + pie chart |
| 🗺️ Hotspot Map | US-13 | Interactive Folium MarkerCluster map |
| 📈 YoY Trend | US-14 | Year-over-year line + % change bar chart |

All pages (except the map) update live when you change the **sidebar filters** (US-10):
- Neighbourhood
- Offence Type
- Year (slider)
- Division
