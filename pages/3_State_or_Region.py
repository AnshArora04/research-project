"""State / Region view — data layer wired, charts in Step 3."""

from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).parent.parent / "dashboard"))
from lib import aggregations as agg
from lib.data_loader import get_states, load_plan_clean
from lib.charts import (
    scatter_omega_funding,
    state_ranking,
    state_trend,
    METRIC_CHOICES,
    METRIC_LABELS,
)
from lib.ui import ATTRIBUTION_HTML, apply_theme, kpi_grid, page_header, rule

st.set_page_config(
    page_title="State / Region · PPD Explorer",
    page_icon="◉",
    layout="wide",
    initial_sidebar_state="expanded",
)
apply_theme()

page_header(
    eyebrow="◉ 03 · Geography View",
    title="State / Region",
    lead=(
        "Compare pension systems across states and Census regions. "
        "Rank by omega, funding ratio, or assumed return for any fiscal year."
    ),
)

# ── Load & aggregate ──────────────────────────────────────────────────────────────────────
df       = load_plan_clean()
sys_df   = agg.cached_system_year(df)
state_df = agg.cached_state_year(sys_df)
states   = get_states(df)

# ── Sidebar selectors ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown('<p class="ppd-eyebrow">◉ Geography Filter</p>', unsafe_allow_html=True)

    all_abbrevs = sorted(states["StateAbbrev"].unique())
    selected_states = st.multiselect(
        "States", options=all_abbrevs, default=all_abbrevs[:5], label_visibility="collapsed"
    )

    regions = sorted(states["region"].dropna().unique())
    selected_region = st.selectbox("Or filter by region", options=["All regions"] + regions)
    if selected_region != "All regions" and not selected_states:
        selected_states = states.loc[states["region"] == selected_region, "StateAbbrev"].tolist()

    fy_lo, fy_hi = int(df["fy"].min()), int(df["fy"].max())
    fy_range = st.slider("Fiscal Year Range", fy_lo, fy_hi, (fy_lo, fy_hi))

# ── Filter ──────────────────────────────────────────────────────────────────────────────
sel = agg.filter_states(
    agg.filter_fy(state_df, *fy_range),
    selected_states if selected_states else all_abbrevs,
)

if sel.empty:
    st.warning("No data found for the selected states and fiscal-year range.")
else:
    latest_fy = int(sel["fy"].max())
    latest    = sel[sel["fy"] == latest_fy]

    kpi_grid([
        ("States Selected",    str(len(latest)),      f"data through FY {latest_fy}"),
        ("Total AUM",
         f"${latest['MktAssets_net'].sum()/1e12:.2f}T" if latest['MktAssets_net'].sum() >= 1e12
         else f"${latest['MktAssets_net'].sum()/1e9:.1f}B",
         "sum of state AUM"),
        ("Avg Omega (latest)",
         f"{latest['omega'].mean():.1%}" if latest['omega'].notna().any() else "–",
         "equal-weighted across states"),
        ("Avg Funded Ratio",
         f"{latest['ActFundedRatio_GASB'].mean():.1%}" if latest['ActFundedRatio_GASB'].notna().any() else "–",
         "equal-weighted across states"),
    ])

    metric = st.selectbox(
        "Metric",
        options=METRIC_CHOICES,
        format_func=lambda k: METRIC_LABELS[k],
        index=0,
    )

    st.plotly_chart(state_ranking(state_df, latest_fy, metric), use_container_width=True)

    if selected_states:
        st.plotly_chart(state_trend(sel, selected_states, metric), use_container_width=True)

    st.plotly_chart(scatter_omega_funding(state_df, latest_fy), use_container_width=True)

    st.download_button(
        label="⬇ Download CSV",
        data=sel.to_csv(index=False),
        file_name=f"states_fy{fy_range[0]}-{fy_range[1]}_data.csv",
        mime="text/csv",
    )

rule()
st.markdown(ATTRIBUTION_HTML, unsafe_allow_html=True)
