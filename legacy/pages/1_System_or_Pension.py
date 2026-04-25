"""System / Pension view — search-as-you-type selector, full-width charts with insights."""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import streamlit as st

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "dashboard"))
from lib import aggregations as agg
from lib.data_loader import get_systems, load_plan_clean
from lib.charts import allocation_area, funding_trend, omega_trend, return_bars
from lib.ui import (
    ATTRIBUTION_HTML, apply_theme, insight, kpi_grid, page_header, section,
)

st.set_page_config(
    page_title="System Deep Dive · PPD Explorer",
    page_icon="◉",
    layout="wide",
    initial_sidebar_state="expanded",
)
apply_theme()

page_header(
    eyebrow="◉ System Deep Dive",
    title="Single-Fund Explorer",
    lead="Search any of the panel's pension systems. All charts respond to the selected fund and fiscal-year window.",
)

# ── Load & aggregate ──────────────────────────────────────────────────────────
df      = load_plan_clean()
sys_df  = agg.cached_system_year(df)
systems = get_systems(df).sort_values(["StateAbbrev", "pub_system_name"])

# ── Sidebar: search-as-you-type selector grouped by state ─────────────────────
with st.sidebar:
    st.markdown('<div class="ppd-eyebrow">◉ Select Pension System</div>',
                unsafe_allow_html=True)

    # Streamlit's selectbox supports type-to-search natively; group by state via label prefix.
    options = [
        (row.pub_id, f"{row.StateAbbrev} · {row.pub_system_name}")
        for row in systems.itertuples()
    ]
    labels = [lbl for _, lbl in options]
    default_idx = next((i for i, (pid, _) in enumerate(options) if str(pid).startswith("CA")), 0)
    selected_label = st.selectbox(
        "Search by state code or system name",
        options=labels,
        index=default_idx,
    )
    selected_pub_id = next(pid for pid, lbl in options if lbl == selected_label)
    selected_name   = next(row.pub_system_name for row in systems.itertuples()
                           if row.pub_id == selected_pub_id)

    fy_lo, fy_hi = int(df["fy"].min()), int(df["fy"].max())
    fy_range = st.slider("Fiscal Year Range", fy_lo, fy_hi, (fy_lo, fy_hi))

# ── Filter ────────────────────────────────────────────────────────────────────
sel = agg.filter_systems(agg.filter_fy(sys_df, *fy_range), [selected_pub_id])

if sel.empty:
    st.warning("No data found for the selected system and fiscal-year range.")
    st.stop()

sel_sorted = sel.sort_values("fy")
row_first = sel_sorted.iloc[0]
row0      = sel_sorted.iloc[-1]

# Peer aggregate omega in latest year (AUM-weighted)
latest_fy = int(row0["fy"])
peer_snap = sys_df[(sys_df["fy"] == latest_fy) & sys_df["omega"].notna()]
if not peer_snap.empty and peer_snap["MktAssets_net"].sum() > 0:
    peer_omega = float(np.average(peer_snap["omega"],
                                  weights=peer_snap["MktAssets_net"].fillna(0).clip(lower=0)))
else:
    peer_omega = float("nan")

# Eyebrow with state · region
st.markdown(
    f'<div class="ppd-eyebrow">{row0.get("StateAbbrev","")} &nbsp;·&nbsp; '
    f'{row0.get("region","")} &nbsp;·&nbsp; {selected_name}</div>',
    unsafe_allow_html=True,
)

# ── 3 KPI tiles ───────────────────────────────────────────────────────────────
def _pct(v, d=1):
    return f"{v*100:.{d}f}%" if v == v else "—"  # NaN-safe

omega_latest = row0.get("omega", float("nan"))
fund_latest  = row0.get("ActFundedRatio_GASB", float("nan"))
consult      = row0.get("general_consultant", "—") or "—"

above_below = "above" if (omega_latest == omega_latest and peer_omega == peer_omega
                          and omega_latest >= peer_omega) else "below"
fund_accent = ("green" if fund_latest >= 0.80
               else "sky" if fund_latest >= 0.65 else "red") if fund_latest == fund_latest else "muted"

kpi_grid([
    ("Latest Omega (FY {})".format(latest_fy),
     _pct(omega_latest),
     f"Alt share of risky portfolio — {above_below} peer avg of {_pct(peer_omega)}",
     "blue"),
    ("Funded Ratio (FY {})".format(latest_fy),
     _pct(fund_latest),
     "Actuarial assets ÷ liabilities (GASB basis)",
     fund_accent),
    ("Investment Consultant",
     str(consult).split(",")[0][:28] if consult != "—" else "None",
     f"General investment consultant of record" if consult != "—" else "No external general consultant",
     "purple"),
])

# ── Charts (full width, stacked, with auto-insights) ─────────────────────────
omega_first = row_first.get("omega", float("nan"))
omega_delta_pp = (omega_latest - omega_first) * 100 if (omega_latest == omega_latest
                                                        and omega_first == omega_first) else 0

section("Target Allocation Over Time")
insight(
    f"{selected_name} expanded its alternatives share from {_pct(omega_first)} in {int(row_first['fy'])} "
    f"to {_pct(omega_latest)} in {latest_fy} — a {omega_delta_pp:+.1f}pp shift {above_below} the "
    f"{_pct(peer_omega)} peer average."
)
st.plotly_chart(allocation_area(sys_df, selected_pub_id), use_container_width=True)

section("Alternative Share vs Peer Average")
gap = abs(omega_latest - peer_omega) * 100 if (omega_latest == omega_latest
                                                and peer_omega == peer_omega) else 0
insight(
    f"The fund's alternative share is {gap:.1f}pp {above_below} the cross-sectional AUM-weighted "
    f"mean in {latest_fy}."
)
st.plotly_chart(omega_trend(sys_df, selected_pub_id), use_container_width=True)

section("Funding Status")
fund_first = row_first.get("ActFundedRatio_GASB", float("nan"))
ar_first   = row_first.get("InvestmentReturnAssumption_GASB", float("nan"))
ar_latest  = row0.get("InvestmentReturnAssumption_GASB", float("nan"))
insight(
    f"Funded ratio moved from {_pct(fund_first)} ({int(row_first['fy'])}) to {_pct(fund_latest)} ({latest_fy}); "
    f"the assumed return adjusted from {_pct(ar_first,2)} to {_pct(ar_latest,2)} as boards revised expectations."
)
st.plotly_chart(funding_trend(sys_df, selected_pub_id), use_container_width=True)

section("Annual Performance")
ret_series = sel_sorted["ret_bgnassets"].dropna()
if len(ret_series):
    worst = ret_series.min() * 100
    best  = ret_series.max() * 100
    insight(
        f"Returns track market cycles. Worst year in window: {worst:+.1f}%; best year: {best:+.1f}%. "
        "Bars are net of fees (ret_bgnassets)."
    )
st.plotly_chart(return_bars(sys_df, selected_pub_id), use_container_width=True)

# ── Download ──────────────────────────────────────────────────────────────────
st.markdown('<hr class="ppd-rule" />', unsafe_allow_html=True)
st.download_button(
    label=f"↓ Export {selected_pub_id} data",
    data=sel.to_csv(index=False),
    file_name=f"{selected_pub_id}_annual_data.csv",
    mime="text/csv",
)

st.markdown(ATTRIBUTION_HTML, unsafe_allow_html=True)
