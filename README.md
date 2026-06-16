# Toronto Crime Analytics Tool

![Python](https://img.shields.io/badge/Python-3.10+-blue?logo=python&logoColor=white)
[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://toronto-crime-analytics.streamlit.app/)
![License](https://img.shields.io/badge/License-MIT-green)
![Agile](https://img.shields.io/badge/Methodology-Agile%20%7C%20Scrum-orange)
![Course](https://img.shields.io/badge/UNFC-CPSC--620--3-blueviolet)

An interactive crime analytics dashboard built for the city of Toronto, developed using Agile/Scrum methodology with Python, Streamlit, GitHub, and Taiga.

> **Course:** Agile Software Development (CPSC-620-3) · University of Niagara Falls Canada · Instructor: William Pourmajidi

---

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Project Structure](#project-structure)
- [Getting Started](#getting-started)
- [Technologies](#technologies)
- [Team](#team)
- [User Stories](#user-stories)
- [Agile Workflow](#agile-workflow)
- [License](#license)

---

## Overview

The Toronto Crime Analytics Tool processes and visualizes Toronto Police Service crime incident data to surface actionable public safety insights. It enables residents, city planners, and analysts to explore neighbourhood-level risk, peak crime periods, geographic hotspots, and police division performance through an interactive Streamlit dashboard.

---

## Features

- Automated dataset ingestion and data cleaning
- Neighbourhood crime risk rankings and summaries
- Peak crime period detection by time and season
- Crime type distribution analysis
- Geographic hotspot visualization
- Police division activity comparisons
- Interactive dashboard with filters for neighbourhood, offence type, and year
- Automated test suite (Pytest + TDD)

---

## Project Structure

```text
toronto-crime-analytics-tool/
│
├── data/
│   └── Toronto_Crime_Indicators.csv     # Source dataset
│
├── src/
│   └── US_06_crime_type_distribution.py # Analytics modules
│
├── dashboard/
│   └── toronto_crime_dashboard.py       # Streamlit app entry point
│
├── notebooks/
│   └── Final_Toronto_crime_June_2026.ipynb  # Exploratory analysis
│
├── tests/                               # Pytest test suite
│
├── outputs/                             # Generated charts and reports
│
├── requirements.txt
└── README.md
```

---

## Getting Started

### Prerequisites

- Python 3.10 or higher
- pip

### Installation

```bash
# 1. Clone the repository
git clone https://github.com/Kenan-Kilic/toronto-crime-indicators-analytics-tool.git
cd toronto-crime-indicators-analytics-tool

# 2. Install dependencies
pip install -r requirements.txt
```

### Run the Dashboard

```bash
streamlit run dashboard/toronto_crime_dashboard.py
```

The app will open in your browser at `http://localhost:8501`.

### Run Tests

```bash
pytest tests/
```

---

## Technologies

| Category | Tools |
|----------|-------|
| Language | Python 3.10+ |
| Dashboard | Streamlit |
| Data Processing | Pandas, NumPy |
| Visualization | Plotly, Matplotlib |
| Testing | Pytest |
| Project Management | Taiga (Scrum backlog, burndown) |
| Version Control | GitHub (feature branches, pull requests) |

---

## Team

| Name | Role | Responsibilities |
|------|------|-----------------|
| Angela Aisa Siagan | Scrum Master / Agile Coordinator | Sprint tracking, Taiga management, burndown chart, velocity tracking, Agile compliance |
| Minh Phuong Nhan | Product Owner / Analytics Lead | User stories, acceptance criteria, analytics insights, dashboard design |
| Jennielyn Nemenzo | Technical Lead / Developer | GitHub setup, architecture, implementation, dashboard development, refactoring |
| Kenan Kilic | QA / Testing Lead | Pytest, TDD stories, testing, validation, documentation support |

---

## User Stories

| ID | Story | Role |
|----|-------|------|
| US-01 | Import crime dataset automatically so analysis can begin without manual preprocessing | System User |
| US-02 | Validate and clean invalid or incomplete records so insights are reliable | Crime Analyst |
| US-03 | Generate a summary of Toronto crime activity to understand overall safety trends | Resident |
| US-04 | Rank neighbourhoods by crime level to identify higher-risk areas | Resident |
| US-05 | Analyze crime activity by time to identify high-risk periods | City Planner |
| US-06 | Analyze crime categories to identify common offence patterns | Public Safety Analyst |
| US-07 | Visualize geographic crime hotspots to monitor concentrated areas | City Planner |
| US-08 | Compare crime levels across police divisions to improve resource allocation | Police Analyst |
| US-09 | Build an interactive dashboard making crime insights accessible in one location | End User |
| US-10 | Filter by neighbourhood, offence type, and year to customize analysis | End User |
| US-11 | Implement automated testing so core analytics functions remain reliable | Developer |
| US-12 | Modularize analytics code to improve maintenance and reuse | Developer |

---

## Agile Workflow

This project was developed over multiple sprints using the Scrum framework:

- Product backlog and sprint tracking managed in **Taiga**
- Feature development via **GitHub feature branches** with pull requests and peer code reviews
- **Test-Driven Development (TDD)** applied to core analytics functions
- Sprint planning, reviews, and retrospectives conducted each sprint
- **Burndown and velocity charts** maintained throughout the project
- Refactoring activities performed to improve code quality and modularity

---

## License

This project was developed for academic purposes as part of the Agile Software Development course at the University of Niagara Falls Canada. Licensed under the [MIT License](LICENSE).
