# US-01 - Import Crime Dataset
# INPUT : CSV file path or Google Drive file ID
# OUTPUT: pd.DataFrame (raw)

import pandas as pd
from pathlib import Path
import requests
import io

GDRIVE_FILE_ID = "1fGIMMzoqixBSj16cDidPlkNkpz6BdovU"

def load_dataset(output_path: str) -> pd.DataFrame:
    local = Path(output_path)
    
    if local.exists() and local.stat().st_size > 1000:
        # Local file exists and is not an LFS pointer
        df = pd.read_csv(local, low_memory=False)
    else:
        # Download from Google Drive
        url = f"https://drive.google.com/uc?export=download&id={GDRIVE_FILE_ID}"
        response = requests.get(url, stream=True)
        response.raise_for_status()
        df = pd.read_csv(io.BytesIO(response.content), low_memory=False)
    
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
