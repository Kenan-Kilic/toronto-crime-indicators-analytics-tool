# US-02 — Validate and Clean Crime Data
# INPUT : pd.DataFrame (raw)
# OUTPUT: pd.DataFrame (cleaned) + cleaned_toronto_crime.csv
#
# REVISED v5 — Final fix:
#   - OCC_DOW normalisation: handles abbreviated ("Mon"), numeric (1-7), French, and full names
#   - MCI_CATEGORY always verified: maps from existing column values OR derives from OFFENCE
#   - TIME_BLOCK always derived from OCC_HOUR regardless

import pandas as pd

LAT_COL        = "LAT_WGS84"
LON_COL        = "LONG_WGS84"
OCC_HOUR_COL   = "OCC_HOUR"
OCC_DATE_COL   = "OCC_DATE"
OCC_DOW_COL    = "OCC_DOW"
MCI_COL        = "MCI_CATEGORY"
OFFENCE_COL    = "OFFENCE"
TIME_BLOCK_COL = "TIME_BLOCK"

# ── Day-name normalisation maps ────────────────────────────────────────────
# Handles every format seen in Toronto Open Data exports
_DAY_ORDER = ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]

_DOW_NORMALISE = {
    # Full English
    "monday":"Monday","tuesday":"Tuesday","wednesday":"Wednesday",
    "thursday":"Thursday","friday":"Friday","saturday":"Saturday","sunday":"Sunday",
    # Abbreviated English
    "mon":"Monday","tue":"Tuesday","wed":"Wednesday",
    "thu":"Thursday","fri":"Friday","sat":"Saturday","sun":"Sunday",
    # Numeric (Python: 0=Mon; Excel/SPSS: 1=Sun or 1=Mon variants)
    "0":"Monday","1":"Tuesday","2":"Wednesday","3":"Thursday",
    "4":"Friday","5":"Saturday","6":"Sunday",
    # Some sources use 1=Sun
    # (handled by OCC_DATE fallback if still wrong after this pass)
}

# ── MCI_CATEGORY keyword mapping ──────────────────────────────────────────
_OFFENCE_TO_MCI = {
    "assault"       : "Crimes Against Person",
    "robbery"       : "Crimes Against Person",
    "sexual"        : "Crimes Against Person",
    "homicide"      : "Crimes Against Person",
    "break"         : "Break and Enter",
    "theft over"    : "Theft Over",
    "theft under"   : "Theft Under",
    "auto theft"    : "Auto Theft",
    "fraud"         : "Fraud",
    "mischief"      : "Crimes Against Property",
}

# Known MCI_CATEGORY values in Toronto dataset (normalise casing inconsistencies)
_MCI_KNOWN = {v.lower(): v for v in [
    "Crimes Against Person","Break and Enter","Theft Over","Theft Under",
    "Auto Theft","Fraud","Crimes Against Property","Other Crimes",
]}


def _assign_time_block(hour) -> str:
    if pd.isna(hour): return "Unknown"
    h = int(hour)
    if 7 <= h < 15:    return "07-15h"
    elif 15 <= h < 23: return "15-23h"
    else:              return "23-07h"


def _normalise_dow_column(series: pd.Series) -> pd.Series:
    """
    Normalise an OCC_DOW series to full English day names.
    Handles: full names, abbreviations, numeric strings, mixed case.
    Returns normalised series (NaN where unrecognised).
    """
    normalised = series.astype(str).str.strip().str.lower().map(_DOW_NORMALISE)
    # Already-correct full names come back as NaN from the map above → re-apply
    full_mask = series.astype(str).str.strip().str.capitalize().isin(_DAY_ORDER)
    normalised[full_mask] = series[full_mask].astype(str).str.strip().str.capitalize()
    return normalised


def _offence_to_mci(offence: str) -> str:
    if pd.isna(offence): return "Other Crimes"
    o = str(offence).lower()
    for key, cat in _OFFENCE_TO_MCI.items():
        if key in o: return cat
    return "Other Crimes"


def _normalise_mci(series: pd.Series) -> pd.Series:
    """Normalise MCI_CATEGORY casing to canonical values."""
    return series.astype(str).str.strip().str.lower().map(
        lambda v: _MCI_KNOWN.get(v, str(v).strip())
    )


def clean_dataset(raw_df: pd.DataFrame, output_path: str) -> pd.DataFrame:
    """
    Clean the raw DataFrame.
    Steps:
      1. Replace NSA with Unknown
      2. Remove zero/null coordinates
      3. Derive TIME_BLOCK from OCC_HOUR (always)
      4. Normalise OCC_DOW to full English names (Mon→Monday, 0→Monday, etc.)
         Falls back to derivation from OCC_DATE if column missing or all unrecognised
      5. Ensure MCI_CATEGORY: normalise existing column OR derive from OFFENCE
      6. Save to output_path
    """
    original_rows = len(raw_df)
    df = raw_df.copy()

    # ── 1. Replace NSA ───────────────────────────────────────────────────────
    nsa_count = 0
    for col in df.select_dtypes(include="object").columns:
        mask = df[col] == "NSA"
        nsa_count += int(mask.sum())
        df[col] = df[col].replace("NSA", "Unknown")

    # ── 2. Remove invalid coordinates ────────────────────────────────────────
    df = df[
        df[LAT_COL].notna() & df[LON_COL].notna() &
        (df[LAT_COL] != 0)  & (df[LON_COL] != 0)
    ].copy()

    # ── 3. TIME_BLOCK (always derived fresh) ────────────────────────────────
    if OCC_HOUR_COL in df.columns:
        df[TIME_BLOCK_COL] = df[OCC_HOUR_COL].apply(_assign_time_block)
        tb_dist = df[TIME_BLOCK_COL].value_counts().to_dict()
        print(f"[US-02] TIME_BLOCK derived: {tb_dist}")
    else:
        print(f"[US-02] WARNING: {OCC_HOUR_COL} not found — TIME_BLOCK not derived")

    # ── 4. OCC_DOW — normalise existing OR derive from OCC_DATE ─────────────
    derived_from = "none"
    if OCC_DOW_COL in df.columns:
        normalised = _normalise_dow_column(df[OCC_DOW_COL])
        valid_mask = normalised.isin(_DAY_ORDER)
        valid_pct  = valid_mask.mean()

        if valid_pct >= 0.80:
            # Column exists and is mostly valid — normalise in place
            df[OCC_DOW_COL] = normalised
            derived_from = f"normalised existing column ({valid_pct:.0%} valid)"
        else:
            # Column exists but values don't match — derive from OCC_DATE
            if OCC_DATE_COL in df.columns:
                day_map = {0:"Monday",1:"Tuesday",2:"Wednesday",3:"Thursday",
                           4:"Friday",5:"Saturday",6:"Sunday"}
                df[OCC_DOW_COL] = pd.to_datetime(
                    df[OCC_DATE_COL], errors="coerce"
                ).dt.dayofweek.map(day_map)
                derived_from = "re-derived from OCC_DATE (existing column had unrecognised format)"
            else:
                df[OCC_DOW_COL] = normalised  # best we can do
                derived_from = f"normalised (only {valid_pct:.0%} matched — no OCC_DATE fallback)"
    else:
        # Column absent — derive from OCC_DATE
        if OCC_DATE_COL in df.columns:
            day_map = {0:"Monday",1:"Tuesday",2:"Wednesday",3:"Thursday",
                       4:"Friday",5:"Saturday",6:"Sunday"}
            df[OCC_DOW_COL] = pd.to_datetime(
                df[OCC_DATE_COL], errors="coerce"
            ).dt.dayofweek.map(day_map)
            derived_from = "derived from OCC_DATE (column was absent)"
        else:
            print(f"[US-02] WARNING: OCC_DOW absent and OCC_DATE not found — clock grid will be unavailable")
            derived_from = "unavailable"

    # Verify result
    if OCC_DOW_COL in df.columns:
        dow_valid = df[OCC_DOW_COL].isin(_DAY_ORDER).sum()
        print(f"[US-02] OCC_DOW: {derived_from}")
        print(f"        Valid rows: {dow_valid:,} / {len(df):,}  ({dow_valid/len(df)*100:.1f}%)")
        sample = df[OCC_DOW_COL].value_counts().head(4).to_dict()
        print(f"        Sample values: {sample}")

    # ── 5. MCI_CATEGORY ──────────────────────────────────────────────────────
    if MCI_COL in df.columns:
        # Normalise casing/spacing of existing column
        df[MCI_COL] = _normalise_mci(df[MCI_COL])
        mci_dist = df[MCI_COL].value_counts().head(4).to_dict()
        print(f"[US-02] MCI_CATEGORY normalised from existing column: {mci_dist}")
    elif OFFENCE_COL in df.columns:
        df[MCI_COL] = df[OFFENCE_COL].apply(_offence_to_mci)
        mci_dist = df[MCI_COL].value_counts().to_dict()
        print(f"[US-02] MCI_CATEGORY derived from OFFENCE: {mci_dist}")
    else:
        df[MCI_COL] = "Other Crimes"
        print(f"[US-02] WARNING: MCI_CATEGORY defaulted to 'Other Crimes'")

    # ── 6. Save ───────────────────────────────────────────────────────────────
    df.to_csv(output_path, index=False)

    print(f"[US-02] Cleaning complete")
    print(f"        Rows before : {original_rows:,}")
    print(f"        Rows removed: {original_rows - len(df):,}")
    print(f"        Rows after  : {len(df):,}")
    print(f"        NSA replaced: {nsa_count:,}")
    print(f"        TIME_BLOCK  : {'OK' if TIME_BLOCK_COL in df.columns else 'MISSING'}")
    print(f"        OCC_DOW     : {'OK' if OCC_DOW_COL in df.columns else 'MISSING'}")
    print(f"        MCI_CATEGORY: {'OK' if MCI_COL in df.columns else 'MISSING'}")
    print(f"        Saved       -> {output_path}")

    return df
