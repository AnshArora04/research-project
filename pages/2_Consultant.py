"""Consultant view — data layer wired, charts in Step 3."""

from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).parent.parent / "dashboard"))
from lib import aggregations as agg
from lib.data_loader import get_consultants, load_plan_clean
from lib.charts import (
    consultant_client_table,
    consultant_metric_trend,
    consultant_trend,
    METRIC_CHOICES,
    METRIC_LABELS,
)
from lib.ui import ATTRIBUTION_HTML, apply_theme, kpi_grid, page_header, rule

st.set_page_config(
    page_title="Consultant · PPD Explorer",
    page_icon="◉",
    layout="wide",
    initial_sidebar_state="expanded",
)
apply_theme()

page_header(
    eyebrow="◉ 02 · Consultant View",
    title="Consultant",
    lead=(
        "Select an investment consultant to see their client base, total AUM under "
        "advice, and average client-level metrics over the 2001–2021 period."
    ),
)

# ── Load & aggregate ──────────────────────────────────────────────────────────────────────
df      = load_plan_clean()
sys_df  = agg.cached_system_year(df)
cons_df = agg.cached_consultant_year(sys_df)
consultants = get_consultants(df)

# ── Sidebar selector ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown('<p class="ppd-eyebrow">◉ Consultant Search</p>', unsafe_allow_html=True)
    cons_options = {
        row.general_consultant: row.consultant_id
        for row in consultants.itertuples()
    }
    selected_name = st.selectbox(
        "Consultant",
        options=list(cons_options.keys()),
        index=0,
        label_visibility="collapsed",
    )
    selected_id = cons_options[selected_name]
    fy_lo, fy_hi = int(df["fy"].min()), int(df["fy"].max())
    fy_range = st.slider("Fiscal Year Range", fy_lo, fy_hi, (fy_lo, fy_hi))

# ── Filter to selected consultant ───────────────────────────────────────────────────────────
sel = agg.filter_consultants(agg.filter_fy(cons_df, *fy_range), [selected_id])

if sel.empty:
    st.warning("No data found for the selected consultant and fiscal-year range.")
else:
    row0 = sel.sort_values("fy", ascending=False).iloc[0]
    latest_aum = row0.get("MktAssets_net", 0) or 0
    aum_str    = f"${latest_aum/1e9:.1f}B" if latest_aum >= 1e9 else f"${latest_aum/1e6:.0f}M"

    kpi_grid([
        ("Client Systems (latest)",  str(int(row0.get("n_systems", 0) or 0)),   "distinct pension systems"),
        ("Client AUM (latest)",       aum_str,                                    "sum of client AUM"),
        ("FY Range",                  f"{fy_range[0]}–{fy_range[1]}",            f"{len(sel)} years of data"),
        ("Avg Client Omega",
         f"{row0['omega']:.1%}" if 'omega' in row0 and row0['omega']==row0['omega'] else "–",
         "AUM-weighted alt share"),
        ("Avg Funded Ratio",
         f"{row0['ActFundedRatio_GASB']:.1%}" if 'ActFundedRatio_GASB' in row0 and row0['ActFundedRatio_GASB']==row0['ActFundedRatio_GASB'] else "–",
         "AUM-weighted client avg"),
    ])

    st.plotly_chart(consultant_trend(cons_df, selected_id), use_container_width=True)

    metric = st.selectbox(
        "Client metric to compare against all systems",
        options=METRIC_CHOICES,
        format_func=lambda k: METRIC_LABELS[k],
        index=0,
    )
    st.plotly_chart(
        consultant_metric_trend(cons_df, selected_id, sys_df, metric, METRIC_LABELS[metric]),
        use_container_width=True,
    )

    latest_fy_all = int(sys_df["fy"].max())
    tbl = consultant_client_table(sys_df, selected_id, latest_fy_all)
    if not tbl.empty:
        st.markdown(f'<p class="ppd-eyebrow">Client systems &mdash; FY {latest_fy_all}</p>', unsafe_allow_html=True)
        st.dataframe(tbl, use_container_width=True, hide_index=True)

    st.download_button(
        label="⬇ Download CSV",
        data=sel.to_csv(index=False),
        file_name=f"consultant_{selected_id}_annual_data.csv",
        mime="text/csv",
    )

rule()
st.markdown(ATTRIBUTION_HTML, unsafe_allow_html=True)
