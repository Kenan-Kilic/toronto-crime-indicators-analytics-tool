# US-01 - Import Crime Dataset
# INPUT : CSV file path or Google Drive file ID
# OUTPUT: pd.DataFrame (raw)

import pandas as pd
from pathlib import Path
import gdown

GDRIVE_FILE_ID = "19KRbMioffzNXTYF8tOci2KALpW3DaypW"

def load_dataset(output_path: str) -> pd.DataFrame:
    url = f"https://drive.google.com/uc?id={GDRIVE_FILE_ID}"
    downloaded = gdown.download(url, quiet=False, fuzzy=True)
    df = pd.read_csv(downloaded, low_memory=False)

    if df.empty:
        raise ValueError("Dataset is empty.")
    print(f"[US-01] Dataset loaded | rows={len(df):,} cols={df.shape[1]}")
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
