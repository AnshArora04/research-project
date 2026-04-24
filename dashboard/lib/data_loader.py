"""Data loader for the Public Pension Data Explorer.

Loads ``ppd_plan_level_clean`` (parquet preferred, CSV fallback), derives
computed metric columns, and caches the result for the Streamlit session.

Public API
----------
    load_plan_clean() -> pd.DataFrame   # plan-level data with derived cols
    get_fy_range(df) -> tuple[int, int]
    get_systems(df) -> pd.DataFrame      # pub_id, pub_system_name, state…
    get_consultants(df) -> pd.DataFrame  # consultant_id, general_consultant
    get_states(df) -> pd.DataFrame       # StateAbbrev, StateName, region…
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
from dashboard.lib.config import get_data_path

# ── Required columns (checked on load) ────────────────────────────────────────
_REQUIRED = [
    "ppd_id", "pub_id", "pub_system_name", "fy",
    "StateAbbrev", "StateName", "region", "division",
    "general_consultant", "consultant_id",
    "EQTotal_Trgt", "FITotal_Trgt", "RETotal_Trgt",
    "PETotal_Trgt", "HFTotal_Trgt", "COMDTotal_Trgt",
    "AltMiscTotal_Trgt", "CashTotal_Trgt", "OtherTotal_Trgt",
    "EQTotal_Actl", "FITotal_Actl", "RETotal_Actl",
    "PETotal_Actl", "HFTotal_Actl", "COMDTotal_Actl",
    "AltMiscTotal_Actl", "CashTotal_Actl", "OtherTotal_Actl",
    "MktAssets_net", "ret_bgnassets",
    "ActFundedRatio_GASB", "InvestmentReturnAssumption_GASB",
    "TotMembership", "beneficiaries_tot", "actives_tot",
    "trgt_zero_actl_nonzero", "is_actual_replaced", "is_target_replaced",
]


# ── Internal loader (not cached → called by the cached wrapper) ────────────────
def _load_raw() -> pd.DataFrame:
    """Read the parquet file, falling back to CSV."""
    path = get_data_path("plan_clean")
    if path.suffix == ".parquet":
        try:
            df = pd.read_parquet(path)
        except Exception:
            csv_path = path.with_suffix(".csv")
            df = pd.read_csv(csv_path, low_memory=False)
    else:
        df = pd.read_csv(path, low_memory=False)
    return df


def _validate(df: pd.DataFrame) -> None:
    """Raise a clear error if any required column is missing."""
    missing = [c for c in _REQUIRED if c not in df.columns]
    if missing:
        raise ValueError(
            f"Required columns missing from dataset: {missing}. "
            "Re-run the pipeline notebooks (01–05) to regenerate output files."
        )


def _derive_metrics(df: pd.DataFrame) -> pd.DataFrame:
    """Add computed columns. Does not mutate the original DataFrame."""
    df = df.copy()

    # ── Target allocation buckets ──────────────────────────────────────────────
    df["alternatives_trgt"] = (
        df["PETotal_Trgt"].fillna(0)
        + df["RETotal_Trgt"].fillna(0)
        + df["HFTotal_Trgt"].fillna(0)
        + df["COMDTotal_Trgt"].fillna(0)
        + df["AltMiscTotal_Trgt"].fillna(0)
        + df["OtherTotal_Trgt"].fillna(0)
    )
    df["public_equity_trgt"] = df["EQTotal_Trgt"].fillna(0)
    df["fixed_income_trgt"]  = df["FITotal_Trgt"].fillna(0) + df["CashTotal_Trgt"].fillna(0)
    df["risky_trgt"]         = df["alternatives_trgt"] + df["public_equity_trgt"]

    # omega (target): alt / (alt + public equity)
    denom = df["risky_trgt"]
    df["omega"] = np.where(denom > 1e-6, df["alternatives_trgt"] / denom, np.nan)

    # ── Actual allocation buckets ──────────────────────────────────────────────
    df["alternatives_actl"] = (
        df["PETotal_Actl"].fillna(0)
        + df["RETotal_Actl"].fillna(0)
        + df["HFTotal_Actl"].fillna(0)
        + df["COMDTotal_Actl"].fillna(0)
        + df["AltMiscTotal_Actl"].fillna(0)
        + df["OtherTotal_Actl"].fillna(0)
    )
    df["public_equity_actl"] = df["EQTotal_Actl"].fillna(0)
    df["fixed_income_actl"]  = df["FITotal_Actl"].fillna(0) + df["CashTotal_Actl"].fillna(0)
    df["risky_actl"]         = df["alternatives_actl"] + df["public_equity_actl"]

    denom_a = df["risky_actl"]
    df["omega_actl"] = np.where(denom_a > 1e-6, df["alternatives_actl"] / denom_a, np.nan)

    # ── Membership ────────────────────────────────────────────────────────────
    df["pct_retired"] = np.where(
        df["TotMembership"].notna() & (df["TotMembership"] > 0),
        df["beneficiaries_tot"] / df["TotMembership"],
        np.nan,
    )

    # ── Fiscal-year-end month (for timing-aware analysis) ───────────────────
    df["fye_month"] = pd.to_datetime(df.get("fye"), errors="coerce").dt.month

    # ── Clean up fy type ──────────────────────────────────────────────────────
    df["fy"] = df["fy"].astype("Int64")

    return df


@st.cache_data(show_spinner="Loading pension dataset…")
def load_plan_clean() -> pd.DataFrame:
    """Return the plan-level cleaned dataset with derived metric columns.

    The result is cached for the Streamlit session.  Parquet is preferred;
    CSV is used as fallback.

    Returns
    -------
    pd.DataFrame
        4,000 rows × 291 + derived columns, plan × fiscal-year level.
    """
    df = _load_raw()
    _validate(df)
    df = _derive_metrics(df)
    return df


# ── Lookup helpers ─────────────────────────────────────────────────────────────

def get_fy_range(df: pd.DataFrame) -> tuple[int, int]:
    """Return (min_fy, max_fy) as plain ints."""
    return int(df["fy"].min()), int(df["fy"].max())


def get_systems(df: pd.DataFrame) -> pd.DataFrame:
    """Return one row per system (pub_id) with name + location metadata."""
    return (
        df.sort_values("fy", ascending=False)
          .drop_duplicates(subset=["pub_id"])
          [["pub_id", "pub_system_name", "StateAbbrev", "StateName", "region", "division"]]
          .sort_values("pub_system_name")
          .reset_index(drop=True)
    )


def get_consultants(df: pd.DataFrame) -> pd.DataFrame:
    """Return one row per consultant with id + name."""
    return (
        df[df["general_consultant"].notna()]
          .sort_values("fy", ascending=False)
          .drop_duplicates(subset=["consultant_id"])
          [["consultant_id", "general_consultant"]]
          .sort_values("general_consultant")
          .reset_index(drop=True)
    )


def get_states(df: pd.DataFrame) -> pd.DataFrame:
    """Return one row per state with abbreviation, name, and region."""
    return (
        df.drop_duplicates(subset=["StateAbbrev"])
          [["StateAbbrev", "StateName", "region", "division"]]
          .sort_values("StateAbbrev")
          .reset_index(drop=True)
    )
