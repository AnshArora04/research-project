"""Consultant view — ranked dropdown with AUM, formatted client table."""

from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "dashboard"))
from lib import aggregations as agg
from lib.data_loader import get_consultants, load_plan_clean
from lib.charts import (
    consultant_client_table,
    consultant_metric_trend,
    consultant_trend,
    METRIC_CHOICES,
    METRIC_LABELS,
)
from lib.ui import (
    ATTRIBUTION_HTML, apply_theme, insight, kpi_grid, page_header, section,
)

st.set_page_config(
    page_title="Consultant Analysis · PPD Explorer",
    page_icon="◈",
    layout="wide",
    initial_sidebar_state="expanded",
)
apply_theme()

page_header(
    eyebrow="◈ Consultant Analysis",
    title="Investment Advisor Comparison",
    lead="Examine each consultant's client base, AUM under advice, and how their average client metrics compare to the full sample.",
)

# ── Load & aggregate ──────────────────────────────────────────────────────────
df       = load_plan_clean()
sys_df   = agg.cached_system_year(df)
cons_df  = agg.cached_consultant_year(sys_df)
consultants = get_consultants(df)

# Build dropdown labels with latest AUM + client count for orientation
fy_max = int(cons_df["fy"].max())
latest_cons = cons_df[cons_df["fy"] == fy_max].copy()
latest_cons["aum_b"] = latest_cons["MktAssets_net"].fillna(0) / 1e9
latest_cons = latest_cons.sort_values("aum_b", ascending=False)

with st.sidebar:
    st.markdown('<div class="ppd-eyebrow">◈ Select Consultant</div>',
                unsafe_allow_html=True)
    options = []
    for row in latest_cons.itertuples():
        name = row.general_consultant or f"#{row.consultant_id}"
        clients = int(row.n_systems) if row.n_systems == row.n_systems else 0
        label = f"{name} — ${row.aum_b:,.0f}B · {clients} clients"
        options.append((row.consultant_id, label))
    labels = [lbl for _, lbl in options]
    selected_label = st.selectbox(
        "Sorted by client AUM in latest year",
        options=labels,
        index=0,
    )
    selected_id = next(cid for cid, lbl in options if lbl == selected_label)
    selected_name = next(row.general_consultant for row in latest_cons.itertuples()
                         if row.consultant_id == selected_id)

    fy_lo, fy_hi = int(df["fy"].min()), int(df["fy"].max())
    fy_range = st.slider("Fiscal Year Range", fy_lo, fy_hi, (fy_lo, fy_hi))

# ── Filter ────────────────────────────────────────────────────────────────────
sel = agg.filter_consultants(agg.filter_fy(cons_df, *fy_range), [selected_id])

if sel.empty:
    st.warning("No data found for the selected consultant and fiscal-year range.")
    st.stop()

row0 = sel.sort_values("fy", ascending=False).iloc[0]
latest_aum = row0.get("MktAssets_net", 0) or 0
aum_str = f"${latest_aum/1e9:,.1f}B" if latest_aum >= 1e9 else f"${latest_aum/1e6:,.0f}M"

def _pct(v, d=1):
    return f"{v*100:.{d}f}%" if v == v else "—"

st.markdown(
    f'<div class="ppd-eyebrow">{selected_name}</div>',
    unsafe_allow_html=True,
)

kpi_grid([
    ("Client Systems",
     str(int(row0.get("n_systems", 0) or 0)),
     f"Distinct pension systems advised in FY {int(row0['fy'])}",
     "blue"),
    ("Client AUM",
     aum_str,
     "Sum of advised client market assets",
     "sky"),
    ("Avg Client Omega",
     _pct(row0.get("omega", float("nan"))),
     "AUM-weighted average across advised systems",
     "purple"),
])

# ── Trend chart ───────────────────────────────────────────────────────────────
section("Client Base & AUM Over Time")
delta_clients = int(row0["n_systems"]) - int(sel.sort_values("fy").iloc[0]["n_systems"])
direction = "grew" if delta_clients > 0 else ("contracted" if delta_clients < 0 else "held")
insight(
    f"{selected_name}'s book {direction} by {abs(delta_clients)} client systems over the window, "
    f"ending at ${latest_aum/1e9:,.1f}B AUM in FY {int(row0['fy'])}."
)
st.plotly_chart(consultant_trend(cons_df, selected_id), use_container_width=True)

# ── Metric vs all-systems ─────────────────────────────────────────────────────
section("Client Metric vs All-System Average")
metric = st.selectbox(
    "Metric",
    options=METRIC_CHOICES,
    format_func=lambda k: METRIC_LABELS[k],
    index=0,
    key="cons_metric",
)
insight(
    f"Compare advised-client {METRIC_LABELS[metric].lower()} against the AUM-weighted sample average."
)
st.plotly_chart(
    consultant_metric_trend(cons_df, selected_id, sys_df, metric, METRIC_LABELS[metric]),
    use_container_width=True,
)

# ── Client table (formatted) ──────────────────────────────────────────────────
latest_fy_all = int(sys_df["fy"].max())
tbl = consultant_client_table(sys_df, selected_id, latest_fy_all)
if not tbl.empty:
    section(f"Client Systems — FY {latest_fy_all}")
    # Format display copy
    show = tbl.copy()
    show["AUM ($)"]         = show["AUM ($)"].apply(lambda v: f"${v/1e9:,.2f}B" if v >= 1e9 else f"${v/1e6:,.0f}M")
    show["Omega"]           = show["Omega"].apply(lambda v: f"{v*100:,.1f}%" if v == v else "—")
    show["Funded Ratio"]    = show["Funded Ratio"].apply(lambda v: f"{v*100:,.1f}%" if v == v else "—")
    show["Assumed Return"]  = show["Assumed Return"].apply(lambda v: f"{v*100:,.2f}%" if v == v else "—")
    show["Net Return"]      = show["Net Return"].apply(lambda v: f"{v*100:+,.2f}%" if v == v else "—")
    st.dataframe(show, use_container_width=True, hide_index=True)

st.markdown('<hr class="ppd-rule" />', unsafe_allow_html=True)
st.download_button(
    label=f"↓ Export {selected_name} client data",
    data=tbl.to_csv(index=False) if not tbl.empty else sel.to_csv(index=False),
    file_name=f"consultant_{selected_id}_clients_fy{latest_fy_all}.csv",
    mime="text/csv",
)

st.markdown(ATTRIBUTION_HTML, unsafe_allow_html=True)
