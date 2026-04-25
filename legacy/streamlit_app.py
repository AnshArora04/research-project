"""Public Pension Data Explorer — Landing page.

Entry point for the Streamlit multi-page app.
Run locally:  streamlit run streamlit_app.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

# Ensure dashboard/ is importable regardless of working directory.
sys.path.insert(0, str(Path(__file__).parent.parent / "dashboard"))

from lib import aggregations as agg
from lib.charts import aggregate_omega_hero, sparkline, _GREEN, _PURPLE, _SKY
from lib.data_loader import get_consultants, get_states, get_systems, load_plan_clean
from lib.ui import (
    ATTRIBUTION_HTML, apply_theme, hero_card_close, hero_card_open,
    kpi_grid, page_header, section,
)

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="PPD Explorer — The Rise of Alternatives",
    page_icon="◈",
    layout="wide",
    initial_sidebar_state="collapsed",
)
apply_theme()

# ── Load data (cached) ────────────────────────────────────────────────────────
df       = load_plan_clean()
sys_df   = agg.cached_system_year(df)

@st.cache_data(show_spinner=False)
def _summaries():
    systems     = get_systems(df)
    consultants = get_consultants(df)
    states      = get_states(df)
    return (
        int(df["fy"].min()),
        int(df["fy"].max()),
        int(len(systems)),
        int(len(consultants)),
        int(len(states)),
    )

fy_min, fy_max, n_sys, n_cons, n_states = _summaries()

# Aggregate omega (AUM-weighted) for headline numbers
@st.cache_data(show_spinner=False)
def _omega_endpoints():
    s = (
        sys_df.dropna(subset=["omega"])
        .groupby("fy", observed=True)
        .apply(lambda g: (g["omega"] * g["MktAssets_net"].fillna(0)).sum()
                          / max(g["MktAssets_net"].fillna(0).sum(), 1.0),
               include_groups=False)
        .reset_index(name="omega").sort_values("fy")
    )
    return float(s["omega"].iloc[0]), float(s["omega"].iloc[-1])

omega_start, omega_end = _omega_endpoints()
omega_growth_pp = (omega_end - omega_start) * 100

# AUM 2021
@st.cache_data(show_spinner=False)
def _latest_aum():
    latest = sys_df[sys_df["fy"] == fy_max]
    total = float(latest["MktAssets_net"].sum())
    return total

total_aum = _latest_aum()
aum_str = (
    f"${total_aum/1e12:.1f}T" if total_aum >= 1e12
    else f"${total_aum/1e9:.0f}B"
)

# ── Header ────────────────────────────────────────────────────────────────────
page_header(
    eyebrow="◈ &nbsp;Research Tool &nbsp;·&nbsp; Begenau, Liang &amp; Siriwardane (2026, RFS)",
    title="American Public<br>Pension Explorer",
    lead=(
        f"U.S. public defined-benefit pension funds steadily shifted their risky portfolios "
        f"toward alternatives over {fy_min}–{fy_max}. Explore that transformation across "
        f"{n_sys} systems — allocation trends, funding trajectories, consultant "
        f"relationships, and state-level comparisons."
    ),
    hero=True,
)

# ── Hero chart card ───────────────────────────────────────────────────────────
hero_card_open(
    title="Alternative-to-Risky Share (Omega, ω)",
    sub=f"AUM-weighted aggregate, FY {fy_min}–{fy_max} &nbsp;·&nbsp; Figure 2c in paper",
    stat_value=f"{omega_end*100:.1f}%",
    stat_label=f"{fy_max} aggregate",
)
st.plotly_chart(aggregate_omega_hero(sys_df), use_container_width=True,
                config={"displayModeBar": False})
hero_card_close(
    "For every $1 out of fixed income since 2001, approximately $2.72 went to alternatives "
    "and $1.72 came from reduced public equity. Post-2012 acceleration coincides with the "
    "prolonged low-yield environment."
)

# ── Sub-allocation strip (3 sparklines) ───────────────────────────────────────
@st.cache_data(show_spinner=False)
def _share_endpoints(col):
    s = (
        sys_df.dropna(subset=[col])
        .groupby("fy", observed=True)
        .apply(lambda g: (g[col] * g["MktAssets_net"].fillna(0)).sum()
                          / max(g["MktAssets_net"].fillna(0).sum(), 1.0),
               include_groups=False)
        .reset_index(name="v").sort_values("fy")
    )
    if s.empty: return 0.0, 0.0
    return float(s["v"].iloc[0]), float(s["v"].iloc[-1])

sub_specs = [
    ("RETotal_Trgt", "Real Assets",    _GREEN,  "green"),
    ("PETotal_Trgt", "Private Equity", _PURPLE, "purple"),
    ("HFTotal_Trgt", "Hedge Funds",    _SKY,    "sky"),
]

cols = st.columns(3, gap="small")
for col_st, (col_name, label, hex_color, css_class) in zip(cols, sub_specs):
    s_start, s_end = _share_endpoints(col_name) if col_name in sys_df.columns else (0.0, 0.0)
    with col_st:
        st.markdown(
            f'''<div class="sub-card">
  <div class="sub-card-label">{label} &mdash; share of total AUM</div>
  <div class="sub-card-row">
    <span class="sub-card-start">{s_start*100:.0f}%</span>
    <span class="sub-card-end {css_class}">{s_end*100:.0f}%</span>
  </div>''',
            unsafe_allow_html=True,
        )
        if col_name in sys_df.columns:
            st.plotly_chart(
                sparkline(sys_df, col_name, hex_color),
                use_container_width=True,
                config={"displayModeBar": False, "staticPlot": True},
            )
        st.markdown("</div>", unsafe_allow_html=True)

# ── KPI strip ─────────────────────────────────────────────────────────────────
kpi_grid([
    ("Sample AUM",
     aum_str,
     f"{n_sys} systems &middot; FY {fy_max} balance",
     "blue"),
    ("System-Years",
     f"{len(sys_df):,}",
     f"{n_sys} systems × FY {fy_min}–{fy_max} balanced panel",
     "sky"),
    ("Omega Growth",
     f"+{omega_growth_pp:.1f}pp",
     f"{omega_start*100:.1f}% ({fy_min}) → {omega_end*100:.1f}% ({fy_max})",
     "green"),
    ("Consultants",
     str(n_cons),
     "Distinct general investment consultants",
     "purple"),
])

# ── Nav cards ─────────────────────────────────────────────────────────────────
section("Explore the Data")

nav = [
    ("pages/1_System_or_Pension.py", "◉", "System Deep Dive",
     f"Drill into any of {n_sys} funds — allocations, returns, funding trajectories, and peer comparison."),
    ("pages/2_Consultant.py", "◈", "Consultant Analysis",
     "Compare investment advisors by client AUM, count, and average alternative allocations."),
    ("pages/3_State_or_Region.py", "◫", "State & Regional",
     "Rank states by omega, compare funding health, and chart geographic adoption patterns."),
    ("pages/4_Methodology.py", "≡", "Methodology",
     "Variable definitions, sample construction, and data source documentation."),
]

for left, right in [(nav[0], nav[1]), (nav[2], nav[3])]:
    c1, c2 = st.columns(2, gap="small")
    for col_st, (page, icon, title, body) in zip((c1, c2), (left, right)):
        with col_st:
            st.markdown(
                f'''<div class="nav-card">
  <div class="nav-card-icon">{icon}</div>
  <div class="nav-card-title">{title}</div>
  <p class="nav-card-body">{body}</p>
</div>''',
                unsafe_allow_html=True,
            )
            st.page_link(page, label=f"Open {title} →")

# ── Attribution ───────────────────────────────────────────────────────────────
st.markdown(ATTRIBUTION_HTML, unsafe_allow_html=True)
