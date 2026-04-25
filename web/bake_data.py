"""Bake real PPD data into web/static/ppd-data.js.

Reads the parquet through the existing dashboard.lib data layer, then writes
a single JS file that exposes `window.PPDData` in exactly the shape the
React prototype expects (see web/static/ppd-shared.jsx and the original
mock at /tmp/design_dl/.../ppd-data.js).

Run:  python -m web.bake_data
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from dashboard.lib.aggregations import (  # noqa: E402
    cached_consultant_year,
    cached_state_year,
    cached_system_year,
)
from dashboard.lib.data_loader import (  # noqa: E402
    get_consultants,
    get_systems,
    load_plan_clean,
)

OUT = ROOT / "web" / "static" / "ppd-data.js"


# ── small helpers ─────────────────────────────────────────────────────────────

def _is_nan(v) -> bool:
    try:
        return v is None or (isinstance(v, float) and (np.isnan(v) or np.isinf(v)))
    except TypeError:
        return False


def pct(v, d: int = 1):
    """Convert a 0..1 ratio to a rounded percentage, NaN-safe."""
    if _is_nan(v):
        return None
    return round(float(v) * 100, d)


def num(v, d: int = 1):
    """Round a number, NaN-safe."""
    if _is_nan(v):
        return None
    return round(float(v), d)


def safe(v):
    """Coerce NaN → None for direct json output."""
    return None if _is_nan(v) else v


# ── per-year aggregate (AUM-weighted) ────────────────────────────────────────

def wavg_by_year(sys_df: pd.DataFrame, col: str, years: list[int]) -> list:
    out = []
    for y in years:
        g = sys_df[(sys_df["fy"] == y) & sys_df[col].notna()]
        if g.empty:
            out.append(None); continue
        w = g["MktAssets_net"].fillna(0).clip(lower=0)
        if w.sum() == 0:
            out.append(None); continue
        out.append(round(float(np.average(g[col], weights=w)) * 100, 1))
    return out


# ── main bake ────────────────────────────────────────────────────────────────

def bake() -> dict:
    df = load_plan_clean()
    sys_df = cached_system_year(df)
    state_df = cached_state_year(sys_df)  # noqa: F841 — kept for future expansion
    consultants_meta = get_consultants(df)
    systems_meta = get_systems(df)

    YEARS = sorted(int(y) for y in df["fy"].unique())
    fy_max = max(YEARS)

    # ── Aggregate trends (landing hero) ────────────────────────────────────────
    AGG_OMEGA = wavg_by_year(sys_df, "omega", YEARS)
    AGG_FUNDED = wavg_by_year(sys_df, "ActFundedRatio_GASB", YEARS)
    LANDING_DATA = [
        {"year": str(y), "avgOmega": AGG_OMEGA[i], "avgFunded": AGG_FUNDED[i]}
        for i, y in enumerate(YEARS)
    ]

    # Per-year sub-allocation aggregates (AUM-weighted, % of total AUM)
    # Used by the landing-page sub-allocation sparkline strip.
    SUB_ALLOC = {
        "realAssets":    wavg_by_year(sys_df, "RETotal_Trgt", YEARS),
        "privateEquity": wavg_by_year(sys_df, "PETotal_Trgt", YEARS),
        "hedgeFunds":    wavg_by_year(sys_df, "HFTotal_Trgt", YEARS),
    }

    # AUM-weighted assumed-return endpoints (used in Methodology page)
    ARR_TREND = {
        "firstFy":    YEARS[0],
        "firstValue": wavg_by_year(sys_df, "InvestmentReturnAssumption_GASB", [YEARS[0]])[0],
        "lastFy":     YEARS[-1],
        "lastValue":  wavg_by_year(sys_df, "InvestmentReturnAssumption_GASB", [YEARS[-1]])[0],
    }

    # Omega range across the panel (used in Methodology page)
    omega_vals = sys_df["omega"].dropna()
    OMEGA_RANGE = {
        "min": round(float(omega_vals.min()) * 100, 1),
        "max": round(float(omega_vals.max()) * 100, 1),
    }

    # ── SYSTEMS ────────────────────────────────────────────────────────────────
    sys_by_id = {row.pub_id: row for row in systems_meta.itertuples()}

    # Latest-year snapshot per system (for AUM + consultant lookup)
    latest = (
        sys_df[sys_df["fy"] == fy_max]
        .drop_duplicates(subset=["pub_id"], keep="first")
        .set_index("pub_id")
    )

    SYSTEMS = []
    for pub_id, group in sys_df.sort_values("fy").groupby("pub_id", sort=False):
        meta = sys_by_id.get(pub_id)
        if meta is None:
            continue

        gy = group.drop_duplicates(subset=["fy"], keep="first").set_index("fy")
        years_data = []
        for y in YEARS:
            if y in gy.index:
                row = gy.loc[y]
                # Allocation buckets — design wants 5: PE, FI, PE, HF, RA
                eq    = float(row.get("EQTotal_Trgt") or 0)
                fi    = float(row.get("FITotal_Trgt") or 0) + float(row.get("CashTotal_Trgt") or 0)
                pe    = float(row.get("PETotal_Trgt") or 0)
                hf    = (float(row.get("HFTotal_Trgt")    or 0)
                         + float(row.get("COMDTotal_Trgt")   or 0)
                         + float(row.get("AltMiscTotal_Trgt") or 0)
                         + float(row.get("OtherTotal_Trgt")  or 0))
                ra    = float(row.get("RETotal_Trgt") or 0)

                years_data.append({
                    "year": int(y),
                    "omega": pct(row.get("omega")),
                    "fundedRatio": pct(row.get("ActFundedRatio_GASB")),
                    "netReturn": pct(row.get("ret_bgnassets")),
                    "assumedReturn": pct(row.get("InvestmentReturnAssumption_GASB"), d=2),
                    "allocation": {
                        "publicEquity":  round(eq * 100, 1),
                        "fixedIncome":   round(fi * 100, 1),
                        "privateEquity": round(pe * 100, 1),
                        "hedgeFunds":    round(hf * 100, 1),
                        "realAssets":    round(ra * 100, 1),
                    },
                })
            else:
                years_data.append({
                    "year": int(y), "omega": None, "fundedRatio": None,
                    "netReturn": None, "assumedReturn": None,
                    "allocation": {"publicEquity": 0, "fixedIncome": 0,
                                   "privateEquity": 0, "hedgeFunds": 0, "realAssets": 0},
                })

        latest_aum_raw = latest["MktAssets_net"].get(pub_id) if pub_id in latest.index else 0
        latest_aum = float(latest_aum_raw) if not _is_nan(latest_aum_raw) else 0.0
        cid_raw = latest["consultant_id"].get(pub_id) if pub_id in latest.index else None
        consultant_id = None
        if not _is_nan(cid_raw):
            try:
                consultant_id = str(int(cid_raw))
            except (ValueError, TypeError):
                consultant_id = str(cid_raw)

        SYSTEMS.append({
            "id": str(pub_id),
            "name": meta.pub_system_name,
            "stateCode": meta.StateAbbrev or "",
            "stateName": meta.StateName or "",
            "consultantId": consultant_id,
            # MktAssets_net is in thousands of dollars ⇒ /1e6 = billions.
            "aumB": round(latest_aum / 1e6, 1),
            "years": years_data,
        })

    SYSTEMS.sort(key=lambda s: (s["stateCode"], s["name"]))

    # ── CONSULTANTS ────────────────────────────────────────────────────────────
    cons_meta_by_id = {str(int(row.consultant_id)): row.general_consultant
                       for row in consultants_meta.itertuples()
                       if not _is_nan(row.consultant_id)}

    cons_buckets: dict[str, list[dict]] = {}
    for s in SYSTEMS:
        cid = s["consultantId"]
        if cid is None:
            continue
        cons_buckets.setdefault(cid, []).append(s)

    CONSULTANTS = []
    for cid, sys_list in cons_buckets.items():
        name = cons_meta_by_id.get(cid, f"Consultant #{cid}")
        CONSULTANTS.append({
            "id": cid,
            "name": name or f"Consultant #{cid}",
            "clientCount": len(sys_list),
            "totalAUM": round(sum(s["aumB"] for s in sys_list)),
            "clients": sys_list,  # full denormalized system objects (matches design)
        })
    CONSULTANTS.sort(key=lambda c: -c["totalAUM"])

    # ── STATES ─────────────────────────────────────────────────────────────────
    state_buckets: dict[str, dict] = {}
    for s in SYSTEMS:
        state_buckets.setdefault(s["stateCode"],
                                 {"code": s["stateCode"], "name": s["stateName"], "systems": []})
        state_buckets[s["stateCode"]]["systems"].append(s)

    STATES = []
    for code, st in state_buckets.items():
        sys_list = st["systems"]
        avgByYear = []
        for i in range(len(YEARS)):
            omegas = [s["years"][i]["omega"] for s in sys_list if s["years"][i]["omega"] is not None]
            funded = [s["years"][i]["fundedRatio"] for s in sys_list if s["years"][i]["fundedRatio"] is not None]
            avgByYear.append({
                "year": YEARS[i],
                "avgOmega":  round(sum(omegas) / len(omegas), 1) if omegas else None,
                "avgFunded": round(sum(funded) / len(funded), 1) if funded else None,
            })
        STATES.append({
            "code": code,
            "name": st["name"],
            "systems": sys_list,
            "totalAUM": round(sum(s["aumB"] for s in sys_list)),
            "systemCount": len(sys_list),
            "avgByYear": avgByYear,
            "latestOmega": avgByYear[-1]["avgOmega"],
        })
    STATES.sort(key=lambda x: -x["totalAUM"])

    # ── Top-level scalars ──────────────────────────────────────────────────────
    TOTAL_AUM = round(sum(s["aumB"] for s in SYSTEMS) / 100) * 100  # to nearest 100B
    SYSTEM_COUNT = len(SYSTEMS)
    CONSULTANT_COUNT = len(consultants_meta)
    TOTAL_AUM_EXACT = round(sum(s["aumB"] for s in SYSTEMS), 1)  # exact billion sum

    # Count of system-years with non-zero target allocations (the analytic sample
    # size — paper reports ≈3,128 such observations).
    ANALYTIC_OBS = sum(
        1 for s in SYSTEMS for y in s["years"]
        if sum(y["allocation"].values()) > 0
    )

    # Top-4 consultants by total client AUM (used in Methodology body)
    TOP_CONSULTANTS = [c["name"] for c in CONSULTANTS[:4]]

    return {
        "SYSTEMS": SYSTEMS,
        "CONSULTANTS": CONSULTANTS,
        "STATES": STATES,
        "LANDING_DATA": LANDING_DATA,
        "SUB_ALLOC": SUB_ALLOC,
        "YEARS": YEARS,
        "AGG_OMEGA": AGG_OMEGA,
        "AGG_FUNDED": AGG_FUNDED,
        "TOTAL_AUM": TOTAL_AUM,
        "TOTAL_AUM_EXACT": TOTAL_AUM_EXACT,
        "SYSTEM_COUNT": SYSTEM_COUNT,
        "CONSULTANT_COUNT": CONSULTANT_COUNT,
        "ANALYTIC_OBS": ANALYTIC_OBS,
        "ARR_TREND": ARR_TREND,
        "OMEGA_RANGE": OMEGA_RANGE,
        "TOP_CONSULTANTS": TOP_CONSULTANTS,
    }


def write(payload: dict, out_path: Path = OUT) -> Path:
    body = json.dumps(payload, separators=(",", ":"), ensure_ascii=False)
    js = (
        "// AUTO-GENERATED by web/bake_data.py — do not edit by hand.\n"
        "// Source: real PPD parquet via dashboard.lib.aggregations.\n"
        f"window.PPDData = {body};\n"
        "console.log(`PPDData loaded: ${window.PPDData.SYSTEM_COUNT} systems, "
        "${window.PPDData.CONSULTANTS.length} consultants, "
        "${window.PPDData.STATES.length} states`);\n"
    )
    out_path.write_text(js, encoding="utf-8")
    return out_path


def main() -> None:
    payload = bake()
    out = write(payload)
    size = out.stat().st_size
    print(f"✓ wrote {out} — {size:,} bytes ({size/1024:.0f} KB)")
    print(f"  systems:     {payload['SYSTEM_COUNT']}")
    print(f"  consultants: {len(payload['CONSULTANTS'])} active "
          f"(of {payload['CONSULTANT_COUNT']} in panel)")
    print(f"  states:      {len(payload['STATES'])}")
    print(f"  fy range:    {payload['YEARS'][0]}–{payload['YEARS'][-1]}")
    print(f"  total AUM:   ${payload['TOTAL_AUM']:,}B")
    print(f"  ω trend:     {payload['AGG_OMEGA'][0]}% → {payload['AGG_OMEGA'][-1]}%")


if __name__ == "__main__":
    main()
