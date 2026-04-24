"""Aggregation utilities — fully vectorised, no groupby.apply callbacks."""

from __future__ import annotations

import numpy as np
import pandas as pd

_WAVG_COLS = [
    "alternatives_trgt", "public_equity_trgt", "fixed_income_trgt", "risky_trgt",
    "PETotal_Trgt", "RETotal_Trgt", "HFTotal_Trgt",
    "COMDTotal_Trgt", "AltMiscTotal_Trgt", "OtherTotal_Trgt",
    "EQTotal_Trgt", "FITotal_Trgt", "CashTotal_Trgt",
    "alternatives_actl", "public_equity_actl", "fixed_income_actl", "risky_actl",
    "EQTotal_Actl", "FITotal_Actl",
    "ret_bgnassets", "AvgReturn_3yr", "AvgReturn_5yr", "AvgReturn_10yr",
    "InvestmentReturn_1yr",
    "ActFundedRatio_GASB", "ActFundedRatio_GASB67",
    "InvestmentReturnAssumption_GASB",
    "pct_retired",
]
_SUM_COLS   = ["MktAssets_net", "TotMembership", "beneficiaries_tot",
               "actives_tot", "UAAL_GASB", "payroll"]
_FLAG_COLS  = ["trgt_zero_actl_nonzero", "is_actual_replaced",
               "is_target_replaced", "Leverage_Flag", "POB_Flag"]
_FIRST_SYS  = ["pub_system_name", "StateAbbrev", "StateName",
               "region", "division", "general_consultant", "consultant_id", "fye_month"]
_FIRST_CONS = ["general_consultant"]
_FIRST_ST   = ["StateName", "region", "division"]


def _vagg(df, keys, wavg, sums, firsts, flags, wcol="MktAssets_net", cnt=None):
    """Fully vectorised groupby aggregation — no Python-level callbacks."""
    pw  = [c for c in wavg   if c in df.columns]
    ps  = [c for c in sums   if c in df.columns]
    pf  = [c for c in firsts if c in df.columns]
    pfl = [c for c in flags  if c in df.columns]

    w = df[wcol].where(df[wcol].notna() & (df[wcol] > 0), 0.0)
    g = df.groupby(keys, sort=False)

    parts = []

    # AUM-weighted means: build num/den DataFrames then groupby-sum together
    if pw:
        num_data = {}
        den_data = {}
        for col in pw:
            vw = w.where(df[col].notna(), 0.0)
            num_data[col] = df[col].fillna(0.0) * vw
            den_data[col] = vw
        num_df = pd.DataFrame(num_data, index=df.index)
        den_df = pd.DataFrame(den_data, index=df.index)
        # attach keys so we can groupby
        for k in keys:
            num_df[k] = df[k].values
            den_df[k] = df[k].values
        n_sum = num_df.groupby(keys, sort=False)[pw].sum()
        d_sum = den_df.groupby(keys, sort=False)[pw].sum()
        wavg_out = pd.DataFrame(index=n_sum.index)
        for col in pw:
            wavg_out[col] = np.where(d_sum[col] > 0, n_sum[col] / d_sum[col], np.nan)
        parts.append(wavg_out)

    if ps:
        parts.append(g[ps].sum(min_count=1))
    if pfl:
        parts.append(g[pfl].max())
    if pf:
        parts.append(g[pf].first())
    if cnt and cnt in df.columns:
        parts.append(g[cnt].nunique().rename("n_systems"))

    result = parts[0].copy()
    for p in parts[1:]:
        result = result.join(p, how="outer")
    return result.reset_index()


def _add_omega(df):
    df = df.copy()
    if "alternatives_trgt" in df.columns and "public_equity_trgt" in df.columns:
        d = df["alternatives_trgt"] + df["public_equity_trgt"]
        df["omega"] = np.where(d > 1e-6, df["alternatives_trgt"] / d, np.nan)
    if "alternatives_actl" in df.columns and "public_equity_actl" in df.columns:
        da = df["alternatives_actl"] + df["public_equity_actl"]
        df["omega_actl"] = np.where(da > 1e-6, df["alternatives_actl"] / da, np.nan)
    return df


def system_year(df):
    r = _vagg(df, ["pub_id","fy"], _WAVG_COLS, _SUM_COLS, _FIRST_SYS, _FLAG_COLS)
    r["fy"] = r["fy"].astype("Int64")
    return _add_omega(r)


def consultant_year(sys_df):
    v = sys_df[sys_df["general_consultant"].notna()].copy()
    if "pub_id" not in v.columns:
        v["pub_id"] = v.index
    r = _vagg(v, ["consultant_id","fy"], _WAVG_COLS, _SUM_COLS,
              _FIRST_CONS, [], cnt="pub_id")
    r["fy"] = r["fy"].astype("Int64")
    return _add_omega(r)


def state_year(sys_df):
    v = sys_df.copy()
    if "pub_id" not in v.columns:
        v["pub_id"] = v.index
    r = _vagg(v, ["StateAbbrev","fy"], _WAVG_COLS, _SUM_COLS,
              _FIRST_ST, [], cnt="pub_id")
    r["fy"] = r["fy"].astype("Int64")
    return _add_omega(r)


# ── Filters ───────────────────────────────────────────────────────────────────

def filter_fy(df, lo, hi):
    return df[(df["fy"] >= lo) & (df["fy"] <= hi)]

def filter_systems(df, pub_ids):
    return df[df["pub_id"].isin(pub_ids)]

def filter_consultants(df, consultant_ids):
    return df[df["consultant_id"].isin(consultant_ids)]

def filter_states(df, states):
    return df[df["StateAbbrev"].isin(states)]


# ── Cached wrappers ───────────────────────────────────────────────────────────
try:
    import streamlit as st

    @st.cache_data(show_spinner="Aggregating system data…")
    def cached_system_year(_df):
        return system_year(_df)

    @st.cache_data(show_spinner="Aggregating consultant data…")
    def cached_consultant_year(_sys_df):
        return consultant_year(_sys_df)

    @st.cache_data(show_spinner="Aggregating state data…")
    def cached_state_year(_sys_df):
        return state_year(_sys_df)

except ModuleNotFoundError:
    cached_system_year     = system_year
    cached_consultant_year = consultant_year
    cached_state_year      = state_year
