"""Public Pension Data Explorer — Landing page.

Entry point for the Streamlit multi-page app.
Run locally:  streamlit run streamlit_app.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

# Ensure dashboard/ is importable regardless of working directory.
sys.path.insert(0, str(Path(__file__).parent / "dashboard"))

from lib.config import DATA_FILES, check_data_availability, get_data_root
from lib.data_loader import get_consultants, get_states, get_systems, load_plan_clean
from lib.ui import ATTRIBUTION_HTML, apply_theme

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Public Pension Data Explorer",
    page_icon="◈",
    layout="wide",
    initial_sidebar_state="collapsed",
)
apply_theme()

# ── Load data (cached) ────────────────────────────────────────────────────────
@st.cache_data(show_spinner=False)
def _get_summaries():
    df        = load_plan_clean()
    systems   = get_systems(df)
    consultants = get_consultants(df)
    states    = get_states(df)
    return df["fy"].min(), df["fy"].max(), len(systems), len(consultants), len(states)

fy_min, fy_max, n_sys, n_cons, n_states = _get_summaries()

# ── Data root status ──────────────────────────────────────────────────────────
data_root   = get_data_root()
availability = check_data_availability()
n_ok        = sum(availability.values())
n_total     = len(availability)
all_ok      = n_ok == n_total
dot_cls     = "dot-ok" if all_ok else ("dot-warn" if n_ok > 0 else "dot-err")
status_text = "All files ready" if all_ok else f"{n_ok} / {n_total} files found"

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown(
    """
<p class="ppd-eyebrow">◈ &nbsp;Research Tool &nbsp;·&nbsp; Begenau, Liang &amp; Siriwardane (2026)</p>
<h1 class="ppd-title">American Public<br>Pension Explorer</h1>
<p class="ppd-lead">
  Interactive analytics for U.S. public defined-benefit pension funds.
  Explore asset allocation trends, funding trajectories, consultant
  relationships, and state-level comparisons across the 2001–2021 sample.
</p>
<hr class="ppd-rule" />
""",
    unsafe_allow_html=True,
)

# ── Navigation cards ──────────────────────────────────────────────────────────
col1, col2, col3 = st.columns(3, gap="medium")

with col1:
    st.markdown(
        """
<div class="nav-card">
  <span class="nav-card-badge">◉ &nbsp;01 &nbsp;·&nbsp; System View</span>
  <div class="nav-card-title">System / Pension</div>
  <p class="nav-card-body">
    Drill into any pension system. Track omega (alt share within risky), total
    risky allocation, funding ratio, and net returns from 2001 to 2021.
    Compare against peer medians by state, region, or size tier.
  </p>
  <div class="nav-card-tags">
    <span class="tag">159 systems</span>
    <span class="tag">time-series</span>
    <span class="tag">peer bands</span>
  </div>
</div>""",
        unsafe_allow_html=True,
    )
    st.page_link("pages/1_System_or_Pension.py", label="Open System Explorer →")

with col2:
    st.markdown(
        """
<div class="nav-card">
  <span class="nav-card-badge">◉ &nbsp;02 &nbsp;·&nbsp; Consultant View</span>
  <div class="nav-card-title">Consultant</div>
  <p class="nav-card-body">
    Analyze investment consultants by client base, total AUM under advice, and
    average client metrics. Trace how consultant relationships and portfolio
    choices evolved across the sample period.
  </p>
  <div class="nav-card-tags">
    <span class="tag">57 consultants</span>
    <span class="tag">client metrics</span>
    <span class="tag">AUM-weighted</span>
  </div>
</div>""",
        unsafe_allow_html=True,
    )
    st.page_link("pages/2_Consultant.py", label="Open Consultant Explorer →")

with col3:
    st.markdown(
        """
<div class="nav-card">
  <span class="nav-card-badge">◉ &nbsp;03 &nbsp;·&nbsp; Geography View</span>
  <div class="nav-card-title">State / Region</div>
  <p class="nav-card-body">
    Compare portfolio allocations and funding health across states and Census
    regions. Rank by omega, funding ratio, or assumed return for any fiscal
    year in the sample.
  </p>
  <div class="nav-card-tags">
    <span class="tag">50 states</span>
    <span class="tag">4 regions</span>
    <span class="tag">rankings</span>
  </div>
</div>""",
        unsafe_allow_html=True,
    )
    st.page_link("pages/3_State_or_Region.py", label="Open State Explorer →")

# ── Status panel ──────────────────────────────────────────────────────────────
st.markdown('<hr class="ppd-rule" />', unsafe_allow_html=True)

st.markdown(
    f"""
<div class="status-panel">
  <div class="status-item">
    <span class="status-label">Dataset Status</span>
    <span class="status-value">
      <span class="dot {dot_cls}"></span>{status_text}
    </span>
  </div>
  <div class="status-item">
    <span class="status-label">Data Root</span>
    <span class="status-value">{data_root}</span>
  </div>
  <div class="status-item">
    <span class="status-label">Sample Period</span>
    <span class="status-value">FY {int(fy_min)} – {int(fy_max)}</span>
  </div>
  <div class="status-item">
    <span class="status-label">Coverage</span>
    <span class="status-value">~3,128 system-years &nbsp;·&nbsp; {n_sys} systems &nbsp;·&nbsp; {n_states} states</span>
  </div>
</div>
""",
    unsafe_allow_html=True,
)

# ── Attribution ───────────────────────────────────────────────────────────────
st.markdown(ATTRIBUTION_HTML, unsafe_allow_html=True)
