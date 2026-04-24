"""System / Pension view — data layer wired, charts in Step 3."""

from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).parent.parent / "dashboard"))
from lib import aggregations as agg
from lib.data_loader import get_systems, load_plan_clean
from lib.charts import allocation_area, funding_trend, omega_trend, return_bars
from lib.ui import ATTRIBUTION_HTML, apply_theme, kpi_grid, page_header, rule

st.set_page_config(
    page_title="System / Pension · PPD Explorer",
    page_icon="◉",
    layout="wide",
    initial_sidebar_state="expanded",
)
apply_theme()

page_header(
    eyebrow="◉ 01 · System View",
    title="System / Pension",
    lead=(
        "Select a pension system and fiscal-year range to explore asset allocation "
        "trends, funding trajectories, and net investment returns."
    ),
)

# ── Load & aggregate ──────────────────────────────────────────────────────────────────────
df      = load_plan_clean()
sys_df  = agg.cached_system_year(df)
systems = get_systems(df)

# ── Sidebar selector ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown('<p class="ppd-eyebrow">◉ System Search</p>', unsafe_allow_html=True)
    system_options = {
        row.pub_system_name: row.pub_id
        for row in systems.itertuples()
    }
    selected_name = st.selectbox(
        "Pension System",
        options=list(system_options.keys()),
        index=0,
        label_visibility="collapsed",
    )
    selected_pub_id = system_options[selected_name]

    fy_lo, fy_hi = int(df["fy"].min()), int(df["fy"].max())
    fy_range = st.slider("Fiscal Year Range", fy_lo, fy_hi, (fy_lo, fy_hi))

# ── Filter to selected system ──────────────────────────────────────────────────────────────
sel = agg.filter_systems(agg.filter_fy(sys_df, *fy_range), [selected_pub_id])

if sel.empty:
    st.warning("No data found for the selected system and fiscal-year range.")
else:
    row0 = sel.sort_values("fy", ascending=False).iloc[0]
    st.markdown(
        f'<p class="ppd-eyebrow">{row0.get("StateAbbrev", "")} &nbsp;·&nbsp; {row0.get("region", "")}</p>',
        unsafe_allow_html=True,
    )
    kpi_grid([
        ("System",          str(selected_pub_id),                       selected_name),
        ("FY Range",        f"{fy_range[0]}–{fy_range[1]}",            f"{len(sel)} years of data"),
        ("Latest Omega",    f"{row0['omega']:.1%}" if 'omega' in row0 and row0['omega']==row0['omega'] else "–",
                             "alt÷(alt+equity) target"),
        ("Latest Risky",    f"{row0['risky_trgt']:.1%}" if 'risky_trgt' in row0 and row0['risky_trgt']==row0['risky_trgt'] else "–",
                             "% portfolio in risky assets"),
        ("Funded Ratio",    f"{row0['ActFundedRatio_GASB']:.1%}" if 'ActFundedRatio_GASB' in row0 and row0['ActFundedRatio_GASB']==row0['ActFundedRatio_GASB'] else "–",
                             "GASB 25 actuarial (latest)"),
        ("Consultant",      str(row0.get('general_consultant', '–') or '–'),  "general investment consultant"),
    ])

    c1, c2 = st.columns(2)
    with c1:
        st.plotly_chart(allocation_area(sys_df, selected_pub_id), use_container_width=True)
    with c2:
        st.plotly_chart(omega_trend(sys_df, selected_pub_id), use_container_width=True)

    c3, c4 = st.columns(2)
    with c3:
        st.plotly_chart(funding_trend(sys_df, selected_pub_id), use_container_width=True)
    with c4:
        st.plotly_chart(return_bars(sys_df, selected_pub_id), use_container_width=True)

    st.download_button(
        label="⬇ Download CSV",
        data=sel.to_csv(index=False),
        file_name=f"{selected_pub_id}_annual_data.csv",
        mime="text/csv",
    )

rule()
st.markdown(ATTRIBUTION_HTML, unsafe_allow_html=True)
