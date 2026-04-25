"""State / Regional view — two modes: rank all states, or compare specific states."""

from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "dashboard"))
from lib import aggregations as agg
from lib.data_loader import get_states, load_plan_clean
from lib.charts import (
    scatter_omega_funding,
    state_ranking,
    state_trend,
    METRIC_CHOICES,
    METRIC_LABELS,
)
from lib.ui import (
    ATTRIBUTION_HTML, apply_theme, insight, kpi_grid, page_header, section,
)

st.set_page_config(
    page_title="State & Regional · PPD Explorer",
    page_icon="◫",
    layout="wide",
    initial_sidebar_state="expanded",
)
apply_theme()

page_header(
    eyebrow="◫ State & Regional",
    title="Geographic View",
    lead="Rank all states on a chosen metric for any fiscal year, or compare a hand-picked set over time.",
)

# ── Load & aggregate ──────────────────────────────────────────────────────────
df       = load_plan_clean()
sys_df   = agg.cached_system_year(df)
state_df = agg.cached_state_year(sys_df)
states   = get_states(df)

fy_lo, fy_hi = int(df["fy"].min()), int(df["fy"].max())
all_abbrevs  = sorted(states["StateAbbrev"].dropna().unique())

# Top 5 states by AUM in latest year (sensible default)
latest_state = state_df[state_df["fy"] == fy_hi]
top5_default = (
    latest_state.dropna(subset=["MktAssets_net"])
    .sort_values("MktAssets_net", ascending=False)
    .head(5)["StateAbbrev"].tolist()
)
if not top5_default:
    top5_default = all_abbrevs[:5]

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown('<div class="ppd-eyebrow">◫ Mode</div>', unsafe_allow_html=True)
    mode = st.radio(
        "Mode",
        options=["Rank all states", "Compare specific states"],
        label_visibility="collapsed",
        index=0,
    )

    metric = st.selectbox(
        "Metric",
        options=METRIC_CHOICES,
        format_func=lambda k: METRIC_LABELS[k],
        index=0,
    )

    if mode == "Compare specific states":
        st.markdown('<div class="ppd-eyebrow">States to compare</div>',
                    unsafe_allow_html=True)
        selected_states = st.multiselect(
            "States",
            options=all_abbrevs,
            default=top5_default,
            label_visibility="collapsed",
        )
    else:
        selected_states = all_abbrevs

    fy_range = st.slider("Fiscal Year Range", fy_lo, fy_hi, (fy_lo, fy_hi))

# ── Filter ────────────────────────────────────────────────────────────────────
sel = agg.filter_states(
    agg.filter_fy(state_df, *fy_range),
    selected_states if selected_states else all_abbrevs,
)

if sel.empty:
    st.warning("No data found for the selection.")
    st.stop()

latest_fy = int(sel["fy"].max())
latest    = sel[sel["fy"] == latest_fy]
total_aum = float(latest["MktAssets_net"].sum())
aum_str = (f"${total_aum/1e12:.2f}T" if total_aum >= 1e12
           else f"${total_aum/1e9:.0f}B")

kpi_grid([
    ("States in View", str(len(latest)), f"Through FY {latest_fy}", "blue"),
    ("Total AUM", aum_str, "Sum of state-level market assets", "sky"),
    ("Avg Omega",
     f"{latest['omega'].mean()*100:.1f}%" if latest['omega'].notna().any() else "—",
     "Equal-weighted across states in view", "purple"),
    ("Avg Funded Ratio",
     f"{latest['ActFundedRatio_GASB'].mean()*100:.1f}%" if latest['ActFundedRatio_GASB'].notna().any() else "—",
     "Equal-weighted across states in view", "green"),
])

# ── Mode-dependent body ───────────────────────────────────────────────────────
if mode == "Rank all states":
    section(f"State Ranking — {METRIC_LABELS[metric]} (FY {latest_fy})")
    snap_metric = state_df[state_df["fy"] == latest_fy][metric].dropna()
    if len(snap_metric):
        top  = snap_metric.idxmax()
        bot  = snap_metric.idxmin()
        top_state = state_df.loc[top, "StateAbbrev"]
        bot_state = state_df.loc[bot, "StateAbbrev"]
        spread = (snap_metric.max() - snap_metric.min()) * 100
        insight(
            f"In FY {latest_fy}, {top_state} leads {METRIC_LABELS[metric].lower()} at "
            f"{snap_metric.max()*100:.1f}% while {bot_state} sits at {snap_metric.min()*100:.1f}% "
            f"— a spread of {spread:.1f}pp."
        )
    st.plotly_chart(state_ranking(state_df, latest_fy, metric), use_container_width=True)

    section("Cross-Section: Omega vs Funded Ratio")
    insight(
        "Each marker is a state in the latest year, sized by total AUM. Color encodes omega — "
        "purple = high alternative share, blue = low."
    )
    st.plotly_chart(scatter_omega_funding(state_df, latest_fy), use_container_width=True)

else:  # Compare specific states
    section(f"Trend — {METRIC_LABELS[metric]}")
    if selected_states:
        insight(
            f"Time series of {METRIC_LABELS[metric].lower()} for {len(selected_states)} selected "
            f"state{'s' if len(selected_states) != 1 else ''} across FY {fy_range[0]}–{fy_range[1]}."
        )
        st.plotly_chart(state_trend(sel, selected_states, metric), use_container_width=True)
    else:
        st.info("Select one or more states in the sidebar to render the trend chart.")

    section("Cross-Section: Omega vs Funded Ratio")
    st.plotly_chart(scatter_omega_funding(state_df, latest_fy), use_container_width=True)

st.markdown('<hr class="ppd-rule" />', unsafe_allow_html=True)
st.download_button(
    label="↓ Export state-year data",
    data=sel.to_csv(index=False),
    file_name=f"states_fy{fy_range[0]}-{fy_range[1]}.csv",
    mime="text/csv",
)

st.markdown(ATTRIBUTION_HTML, unsafe_allow_html=True)
