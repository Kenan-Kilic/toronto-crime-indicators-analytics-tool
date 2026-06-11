# US-11 — Implement Automated Testing
# INPUT : All US module functions
# OUTPUT: pytest test results (run with: pytest US_11_automated_testing.py -v)
#
# TDD Stories covered: US-01, US-02, US-03, US-04, US-05
# REVISED v3: Fixtures updated with OCC_DOW and MCI_CATEGORY columns

import pytest
import pandas as pd
import numpy as np
import sys
import os

DRIVE_BASE = "/content/drive/MyDrive/Colab Notebooks"
if os.path.exists(DRIVE_BASE):
    sys.path.insert(0, DRIVE_BASE)


# ── Shared Fixtures ───────────────────────────────────────────────────────────
@pytest.fixture
def sample_raw_df():
    """Minimal raw dataset mimicking Toronto_Crime_Indicators.csv structure."""
    return pd.DataFrame({
        "OBJECTID"          : [1, 2, 3, 4, 5, 6],
        "OFFENCE"           : ["Assault", "Robbery", "Assault", "NSA",
                               "Break & Enter", "Auto Theft"],
        "NEIGHBOURHOOD_158" : ["Kensington", "Annex", "NSA", "Kensington", "Annex", "Annex"],
        "DIVISION"          : ["D14", "D52", "D14", "D52", "D14", "D52"],
        "LAT_WGS84"         : [43.65, 43.67, 0.0,   43.66, 43.64, 43.68],
        "LONG_WGS84"        : [-79.40, -79.39, 0.0, -79.41, -79.38, -79.37],
        "OCC_HOUR"          : [0, 12, 23, 6, 18, 9],
        "OCC_MONTH"         : ["January", "April", "July", "October", "December", "March"],
        "OCC_YEAR"          : [2020, 2021, 2022, 2020, 2021, 2022],
        "OCC_DOW"           : ["Monday", "Wednesday", "Friday", "Monday", "Saturday", "Tuesday"],
        "MCI_CATEGORY"      : ["Crimes Against Person", "Crimes Against Person",
                               "Break and Enter", "Other Crimes",
                               "Break and Enter", "Auto Theft"],
        "OCC_DATE"          : ["2020-01-06", "2021-04-14", "2022-07-01",
                               "2020-10-05", "2021-12-18", "2022-03-08"],
    })


@pytest.fixture
def sample_cleaned_df(sample_raw_df, tmp_path):
    from US_02_data_cleaning import clean_dataset
    out = str(tmp_path / "cleaned.csv")
    return clean_dataset(sample_raw_df, output_path=out)


# ── US-01 Tests ───────────────────────────────────────────────────────────────
class TestUS01LoadDataset:

    def test_load_returns_dataframe(self, tmp_path):
        """US-01 AC: CSV loads successfully."""
        from US_01_data_loader import load_dataset
        csv_path = str(tmp_path / "test.csv")
        pd.DataFrame({"A": [1, 2], "B": [3, 4]}).to_csv(csv_path, index=False)
        df = load_dataset(csv_path)
        assert isinstance(df, pd.DataFrame)

    def test_load_raises_on_missing_file(self):
        """US-01 AC: Errors handled if file missing."""
        from US_01_data_loader import load_dataset
        with pytest.raises(FileNotFoundError):
            load_dataset("nonexistent_file.csv")

    def test_dataset_not_empty(self, tmp_path):
        """US-01 AC: Dataset is not empty after load."""
        from US_01_data_loader import load_dataset
        csv_path = str(tmp_path / "test.csv")
        pd.DataFrame({"A": [1]}).to_csv(csv_path, index=False)
        df = load_dataset(csv_path)
        assert len(df) > 0


# ── US-02 Tests ───────────────────────────────────────────────────────────────
class TestUS02CleanDataset:

    def test_nsa_replaced(self, sample_raw_df, tmp_path):
        """US-02 AC: NSA entries replaced with Unknown."""
        from US_02_data_cleaning import clean_dataset
        out = str(tmp_path / "cleaned.csv")
        cleaned = clean_dataset(sample_raw_df, out)
        assert "NSA" not in cleaned["OFFENCE"].values
        assert "NSA" not in cleaned["NEIGHBOURHOOD_158"].values

    def test_zero_coordinates_removed(self, sample_raw_df, tmp_path):
        """US-02 AC: Zero/invalid coordinates removed."""
        from US_02_data_cleaning import clean_dataset
        out = str(tmp_path / "cleaned.csv")
        cleaned = clean_dataset(sample_raw_df, out)
        assert (cleaned["LAT_WGS84"] == 0).sum() == 0
        assert (cleaned["LONG_WGS84"] == 0).sum() == 0

    def test_output_csv_saved(self, sample_raw_df, tmp_path):
        """US-02 AC: Output CSV saved."""
        from US_02_data_cleaning import clean_dataset
        out = str(tmp_path / "cleaned.csv")
        clean_dataset(sample_raw_df, out)
        assert os.path.exists(out)

    def test_fewer_rows_after_cleaning(self, sample_raw_df, tmp_path):
        """US-02 AC: Invalid rows removed."""
        from US_02_data_cleaning import clean_dataset
        out = str(tmp_path / "cleaned.csv")
        cleaned = clean_dataset(sample_raw_df, out)
        assert len(cleaned) < len(sample_raw_df)

    def test_time_block_derived(self, sample_raw_df, tmp_path):
        """US-02 AC: TIME_BLOCK column derived from OCC_HOUR."""
        from US_02_data_cleaning import clean_dataset
        out = str(tmp_path / "cleaned.csv")
        cleaned = clean_dataset(sample_raw_df, out)
        assert "TIME_BLOCK" in cleaned.columns
        assert cleaned["TIME_BLOCK"].isin(["07-15h", "15-23h", "23-07h"]).all()

    def test_mci_category_present(self, sample_raw_df, tmp_path):
        """US-02 AC: MCI_CATEGORY column present after cleaning."""
        from US_02_data_cleaning import clean_dataset
        out = str(tmp_path / "cleaned.csv")
        cleaned = clean_dataset(sample_raw_df, out)
        assert "MCI_CATEGORY" in cleaned.columns


# ── US-03 Tests ───────────────────────────────────────────────────────────────
class TestUS03CrimeOverview:

    def test_returns_dict(self, sample_cleaned_df, tmp_path):
        """US-03 AC: Summary statistics generated."""
        from US_03_crime_overview import generate_crime_overview
        out = str(tmp_path / "kpis.csv")
        result = generate_crime_overview(sample_cleaned_df, out)
        assert isinstance(result, dict)

    def test_total_crimes_correct(self, sample_cleaned_df, tmp_path):
        """US-03 AC: Crime totals displayed correctly."""
        from US_03_crime_overview import generate_crime_overview
        out = str(tmp_path / "kpis.csv")
        result = generate_crime_overview(sample_cleaned_df, out)
        assert result["total_crimes"] == len(sample_cleaned_df)

    def test_most_common_offence_identified(self, sample_cleaned_df, tmp_path):
        """US-03 AC: Most common offence identified."""
        from US_03_crime_overview import generate_crime_overview
        out = str(tmp_path / "kpis.csv")
        result = generate_crime_overview(sample_cleaned_df, out)
        assert result["most_common_offence"] != "N/A"

    def test_kpi_csv_saved(self, sample_cleaned_df, tmp_path):
        """US-03 AC: Output CSV saved for dashboard."""
        from US_03_crime_overview import generate_crime_overview
        out = str(tmp_path / "kpis.csv")
        generate_crime_overview(sample_cleaned_df, out)
        assert os.path.exists(out)


# ── US-04 Tests ───────────────────────────────────────────────────────────────
class TestUS04NeighbourhoodRanking:

    def test_returns_dataframe(self, sample_cleaned_df, tmp_path):
        """US-04 AC: Top neighbourhoods displayed."""
        from US_04_neighborhood_ranking import rank_neighbourhoods
        out = str(tmp_path / "ranking.csv")
        result = rank_neighbourhoods(sample_cleaned_df, top_n=5, output_path=out)
        assert isinstance(result, pd.DataFrame)

    def test_ranking_column_exists(self, sample_cleaned_df, tmp_path):
        """US-04 AC: Ranking column included."""
        from US_04_neighborhood_ranking import rank_neighbourhoods
        out = str(tmp_path / "ranking.csv")
        result = rank_neighbourhoods(sample_cleaned_df, top_n=5, output_path=out)
        assert "rank" in result.columns

    def test_top_n_respected(self, sample_cleaned_df, tmp_path):
        """US-04 AC: top_n limit respected."""
        from US_04_neighborhood_ranking import rank_neighbourhoods
        out = str(tmp_path / "ranking.csv")
        result = rank_neighbourhoods(sample_cleaned_df, top_n=2, output_path=out)
        assert len(result) <= 2


# ── US-05 Tests ───────────────────────────────────────────────────────────────
class TestUS05PeakCrimePeriods:

    def test_returns_dict_with_hourly(self, sample_cleaned_df, tmp_path):
        """US-05 AC: Crime by hour dict returned."""
        from US_05_peak_crime_periods import detect_peak_crime_periods
        out = str(tmp_path / "peak.csv")
        result = detect_peak_crime_periods(sample_cleaned_df, out)
        assert isinstance(result, dict)
        assert "hourly" in result

    def test_hourly_has_is_peak_column(self, sample_cleaned_df, tmp_path):
        """US-05 AC: Peak periods highlighted with is_peak flag."""
        from US_05_peak_crime_periods import detect_peak_crime_periods
        out = str(tmp_path / "peak.csv")
        result = detect_peak_crime_periods(sample_cleaned_df, out)
        assert "is_peak" in result["hourly"].columns

    def test_peak_csv_saved(self, sample_cleaned_df, tmp_path):
        """US-05 AC: Output CSV saved."""
        from US_05_peak_crime_periods import detect_peak_crime_periods
        out = str(tmp_path / "peak.csv")
        detect_peak_crime_periods(sample_cleaned_df, out)
        assert os.path.exists(out)

    def test_dow_hour_df_computed(self, sample_cleaned_df, tmp_path):
        """US-05 AC: Day-of-week clock grid data computed."""
        from US_05_peak_crime_periods import detect_peak_crime_periods
        out = str(tmp_path / "peak.csv")
        result = detect_peak_crime_periods(sample_cleaned_df, out)
        assert "dow_hour_df" in result
        assert not result["dow_hour_df"].empty

    def test_clock_polar_returns_figure(self, sample_cleaned_df, tmp_path):
        """US-05 AC: Clock-rose figure returned."""
        import matplotlib.pyplot as plt
        from US_05_peak_crime_periods import detect_peak_crime_periods, plot_clock_polar
        out = str(tmp_path / "peak.csv")
        periods = detect_peak_crime_periods(sample_cleaned_df, out)
        fig = plot_clock_polar(periods)
        assert isinstance(fig, plt.Figure)
        plt.close("all")


# ── Runner ────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
