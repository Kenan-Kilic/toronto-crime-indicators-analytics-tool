# US-01 — Import Crime Dataset
# INPUT : CSV file path
# OUTPUT: pd.DataFrame (raw)

import pandas as pd
from pathlib import Path


def load_dataset(output_path: str) -> pd.DataFrame:
    if not Path(output_path).exists():
        raise FileNotFoundError(f"Dataset not found: {output_path}")
    df = pd.read_csv(output_path, low_memory=False)
    if df.empty:
        raise ValueError("Dataset is empty.")
    print(f"[US-01] Dataset loaded | rows={len(df):,}  cols={df.shape[1]}")
    return df


def preview_dataset(df: pd.DataFrame) -> None:
    print("\nDataset Preview:")
    print(df.head())


def get_dataset_summary(df: pd.DataFrame) -> dict:
    return {
        "total_rows": df.shape[0],
        "total_columns": df.shape[1],
        "column_names": list(df.columns)
    }
