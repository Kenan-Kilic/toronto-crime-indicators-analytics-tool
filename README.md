# Toronto Crime Analytics Tool

**Course:** Agile Software Development (CPSC-620-3)  
**University:** University of Niagara Falls Canada  
**Instructor:** William Pourmajidi

---

# Project Overview

The Toronto Crime Analytics Tool is an Agile software development project that analyzes crime incidents across Toronto using Python, Streamlit, GitHub, and Taiga.

The system provides crime intelligence insights through data cleaning, analytics modules, interactive visualizations, and dashboard-based exploration.

This project follows Agile development practices including sprint planning, Test-Driven Development (TDD), automated testing, refactoring, pull requests, code reviews, and sprint tracking.

---

# Sprint Goal

Build the core Toronto crime analytics foundation and the first dashboard version.

---

# Team

| Name | Role | Responsibilities |
|--------|--------|--------|
| Angela Aisa Siagan | Scrum Master / Agile Coordinator | Sprint tracking, Taiga management, burndown chart, velocity tracking, Agile compliance |
| Minh Phuong Nhan | Product Owner / Analytics Lead | User stories, acceptance criteria, analytics insights, dashboard design |
| Jennielyn Nemenzo | Technical Lead / Developer | GitHub setup, architecture, implementation, dashboard development, refactoring |
| Kenan Kilic | QA / Testing Lead | Pytest, TDD stories, testing, validation, documentation support |

---

# User Stories

### US-01 Import Crime Dataset
As a system user, I want the Toronto crime dataset loaded automatically so that analysis can begin without manual preprocessing.

### US-02 Validate and Clean Crime Data
As a crime analyst, I want invalid or incomplete records handled so that insights are reliable.

### US-03 Generate Toronto Crime Risk Overview
As a resident, I want a summary of Toronto crime activity so that I can understand overall safety trends.

### US-04 Identify High-Risk Neighbourhoods
As a resident, I want neighbourhood crime rankings so that I can identify higher-risk areas.

### US-05 Detect Peak Crime Periods
As a city planner, I want crime activity analyzed by time so that high-risk periods can be identified.

### US-06 Analyze Crime Type Distribution
As a public safety analyst, I want crime categories analyzed so that common offence patterns can be identified.

### US-07 Identify Crime Hotspots
As a city planner, I want geographic hotspot visualization so that concentrated crime areas can be monitored.

### US-08 Compare Police Division Activity
As a police analyst, I want crime levels compared across divisions so that resource allocation can be improved.

### US-09 Build Interactive Dashboard
As a user, I want an interactive dashboard so that crime insights are accessible in one location.

### US-10 Add Dashboard Filters
As a user, I want filters for neighbourhood, offence type, and year so that analysis becomes customizable.

### US-11 Implement Automated Testing
As a developer, I want automated testing so that core analytics functions remain reliable.

### US-12 Refactor Analytics Modules
As a developer, I want analytics code modularized so that maintenance and reuse improve.

---

# Project Structure

```text
toronto-crime-analytics-tool/

├── data/
│   └── Toronto_Crime_Indicators.csv

├── src/
│   ├── data_loader.py
│   ├── data_cleaning.py
│   ├── risk_overview.py
│   ├── neighbourhood_analysis.py
│   ├── crime_period_analysis.py
│   ├── crime_type_analysis.py
│   ├── hotspot_analysis.py
│   └── police_division_analysis.py

├── dashboard/
│   └── app.py

├── tests/
│   ├── test_data_loader.py
│   ├── test_data_cleaning.py
│   ├── test_crime_period_analysis.py
│   └── test_neighbourhood_analysis.py

├── outputs/
│   └── charts/

├── requirements.txt
└── README.md
```

---

# Technologies

- Python
- Pandas
- NumPy
- Matplotlib
- Plotly
- Streamlit
- Pytest
- GitHub
- Taiga

---

# Agile Workflow

- Product Backlog managed in Taiga
- Sprint Planning and Sprint Reviews
- Feature Branch Development
- Pull Requests and Peer Reviews
- Test-Driven Development (TDD)
- Refactoring Activities
- Burndown and Velocity Tracking
- Continuous Team Collaboration

---

# How to Run

Install dependencies:

```bash
pip install -r requirements.txt
```

Run the dashboard:

```bash
streamlit run dashboard/app.py
```

---

# License

This project was developed for academic purposes as part of the Agile Software Development course at the University of Niagara Falls Canada.
