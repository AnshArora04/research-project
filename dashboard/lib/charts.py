"""Plotly chart builders for the Public Pension Data Explorer.

All charts share a single dark theme consistent with the Streamlit CSS.
Each builder returns a ``plotly.graph_objects.Figure`` ready for
``st.plotly_chart(fig, use_container_width=True)``.

Public API
----------
    allocation_area(df, pub_id)         # stacked area: alt/equity/fi over time
    omega_trend(df, pub_id, peer_df)    # omega line + peer median band
    funding_trend(df, pub_id, peer_df)  # funded ratio + assumed return
    return_bars(df, pub_id)             # annual net return bar chart
    consultant_trend(df, cons_id)       # consultant metrics over time
    state_ranking(state_df, fy, metric) # horizontal bar ranking
    state_trend(state_df, states)       # multi-state line
    scatter_omega_funding(state_df, fy) # omega vs funding ratio scatter
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# ── Theme tokens ───────────────────────────────────────────────────────────────
_BG      = "#080C14"
_SURFACE = "#0D1526"
_CARD    = "#111D35"
_BORDER  = "#1E3254"
_GRID    = "#162543"
_TEXT    = "#E2EAF4"
_MUTED   = "#7A9BBF"
_BLUE    = "#3B82F6"
_BLUE_F  = "rgba(59,130,246,0.18)"
_SKY     = "#38BDF8"
_GREEN   = "#34D399"
_RED     = "#F87171"
_PURPLE  = "#A78BFA"
_ORANGE  = "#FB923C"
# Legacy alias kept so any straggler reference doesn't break
_AMBER   = _BLUE
_AMBER_F = _BLUE_F

# Colour palette for multi-series (states, consultants, etc.)
_PALETTE = [_BLUE, _SKY, _GREEN, _RED, _PURPLE, _ORANGE,
            "#06B6D4", "#84CC16", "#EC4899", "#A855F7"]

_FONT = dict(family="IBM Plex Mono, monospace", color=_TEXT, size=11)

_LAYOUT_BASE = dict(
    paper_bgcolor=_BG,
    plot_bgcolor=_BG,
    font=_FONT,
    margin=dict(l=10, r=10, t=36, b=10),
    legend=dict(
        bgcolor="rgba(19,23,32,0.85)",
        bordercolor=_BORDER,
        borderwidth=1,
        font=dict(size=10),
        x=0.01, y=0.99, xanchor="left", yanchor="top",
    ),
    xaxis=dict(
        showgrid=False,
        zeroline=False,
        tickfont=dict(size=10),
        color=_MUTED,
        linecolor=_BORDER,
    ),
    yaxis=dict(
        showgrid=True,
        gridcolor=_GRID,
        gridwidth=1,
        zeroline=False,
        tickfont=dict(size=10),
        color=_MUTED,
        linecolor=_BORDER,
    ),
    hoverlabel=dict(
        bgcolor=_SURFACE,
        bordercolor=_BORDER,
        font=dict(family="IBM Plex Mono, monospace", size=11),
    ),
    modebar=dict(bgcolor="rgba(0,0,0,0)", color=_MUTED, activecolor=_BLUE),
)


def _base_fig(**kwargs) -> go.Figure:
    layout = {**_LAYOUT_BASE, **kwargs}
    return go.Figure(layout=go.Layout(**layout))


def _pct(val: float | None) -> str:
    if val is None or (isinstance(val, float) and np.isnan(val)):
        return "—"
    return f"{val:.1%}"


# ── System / Pension charts ────────────────────────────────────────────────────

def allocation_area(sys_df: pd.DataFrame, pub_id: str) -> go.Figure:
    """Stacked area chart of target allocation buckets over time."""
    df = sys_df[sys_df["pub_id"] == pub_id].sort_values("fy").copy()
    fy = df["fy"].astype(int)

    # Fill nulls with 0 for area chart continuity
    alts  = df["alternatives_trgt"].fillna(0)
    eq    = df["public_equity_trgt"].fillna(0)
    fi    = df["fixed_income_trgt"].fillna(0)
    other = (1 - alts - eq - fi).clip(lower=0)

    fig = _base_fig(title=dict(text="Target Allocation", font=dict(size=13, color=_TEXT), x=0))

    shared = dict(mode="lines", stackgroup="one", line=dict(width=0))
    fig.add_trace(go.Scatter(x=fy, y=alts,  name="Alternatives",  fillcolor="rgba(167,139,250,0.78)", **shared))
    fig.add_trace(go.Scatter(x=fy, y=eq,    name="Public Equity", fillcolor="rgba(59,130,246,0.78)",  **shared))
    fig.add_trace(go.Scatter(x=fy, y=fi,    name="Fixed Income",  fillcolor="rgba(56,189,248,0.62)",  **shared))
    fig.add_trace(go.Scatter(x=fy, y=other, name="Other",         fillcolor="rgba(122,155,191,0.32)", **shared))

    fig.update_layout(
        yaxis=dict(tickformat=".0%", range=[0, 1.02], **{k: v for k, v in _LAYOUT_BASE["yaxis"].items() if k != "tickformat"}),
        hovermode="x unified",
        legend=dict(**_LAYOUT_BASE["legend"], traceorder="normal"),
    )
    fig.update_yaxes(tickformat=".0%")
    return fig


def omega_trend(
    sys_df: pd.DataFrame,
    pub_id: str,
    peer_label: str = "All systems",
) -> go.Figure:
    """Omega (alt share within risky) for a system vs AUM-weighted peer median."""
    sel  = sys_df[sys_df["pub_id"] == pub_id].sort_values("fy")
    fy_s = sel["fy"].astype(int)
    ω_s  = sel["omega"]

    # Peer: AUM-weighted avg omega per year across ALL systems (ratio-of-means)
    peer = (
        sys_df.groupby("fy", observed=True)
        .apply(lambda g: _wavg_scalar(g, "omega", "MktAssets_net"), include_groups=False)
        .reset_index(name="omega_peer")
    )
    peer["fy"] = peer["fy"].astype(int)

    fig = _base_fig(title=dict(text="Omega — Alternative Share within Risky", font=dict(size=13, color=_TEXT), x=0))

    fig.add_trace(go.Scatter(
        x=peer["fy"], y=peer["omega_peer"],
        name=peer_label,
        mode="lines",
        line=dict(color=_MUTED, width=1.5, dash="dot"),
        hovertemplate="%{y:.1%}<extra>Peer avg</extra>",
    ))
    fig.add_trace(go.Scatter(
        x=fy_s, y=ω_s,
        name=sel["pub_system_name"].iloc[0] if len(sel) else pub_id,
        mode="lines+markers",
        line=dict(color=_BLUE, width=2.5),
        marker=dict(size=5, color=_BLUE),
        hovertemplate="%{y:.1%}<extra>This system</extra>",
    ))

    fig.update_yaxes(tickformat=".0%")
    fig.update_layout(hovermode="x unified")
    return fig


def funding_trend(sys_df: pd.DataFrame, pub_id: str) -> go.Figure:
    """Funding ratio and assumed return over time (dual y-axis)."""
    sel = sys_df[sys_df["pub_id"] == pub_id].sort_values("fy")
    fy  = sel["fy"].astype(int)

    fig = make_subplots(specs=[[{"secondary_y": True}]])

    fig.add_trace(go.Scatter(
        x=fy, y=sel["ActFundedRatio_GASB"],
        name="Funded Ratio (GASB 25)",
        mode="lines+markers",
        line=dict(color=_SKY, width=2.5),
        marker=dict(size=5),
        hovertemplate="%{y:.1%}<extra>Funded ratio</extra>",
    ), secondary_y=False)

    fig.add_trace(go.Scatter(
        x=fy, y=sel["InvestmentReturnAssumption_GASB"],
        name="Assumed Return",
        mode="lines+markers",
        line=dict(color=_PURPLE, width=2, dash="dash"),
        marker=dict(size=4, symbol="diamond"),
        hovertemplate="%{y:.2%}<extra>Assumed return</extra>",
    ), secondary_y=True)

    fig.update_layout(
        **{k: v for k, v in _LAYOUT_BASE.items() if k not in ("xaxis", "yaxis")},
        title=dict(text="Funding Ratio &amp; Assumed Return", font=dict(size=13, color=_TEXT), x=0),
        hovermode="x unified",
    )
    fig.update_xaxes(**_LAYOUT_BASE["xaxis"])
    fig.update_yaxes(tickformat=".0%", showgrid=True, gridcolor=_GRID, secondary_y=False)
    fig.update_yaxes(tickformat=".1%", showgrid=False, secondary_y=True)
    return fig


def return_bars(sys_df: pd.DataFrame, pub_id: str) -> go.Figure:
    """Annual net return (ret_bgnassets) as a bar chart."""
    sel = sys_df[sys_df["pub_id"] == pub_id].sort_values("fy")
    fy  = sel["fy"].astype(int)
    ret = sel["ret_bgnassets"]

    colors = [_GREEN if (r >= 0 and not np.isnan(r)) else _RED for r in ret]

    fig = _base_fig(title=dict(text="Annual Net Return (ret_bgnassets)", font=dict(size=13, color=_TEXT), x=0))
    fig.add_trace(go.Bar(
        x=fy, y=ret,
        marker_color=colors,
        name="Net return",
        hovertemplate="%{x}: %{y:.2%}<extra></extra>",
    ))
    fig.add_hline(y=0, line_color=_BORDER, line_width=1)
    fig.update_yaxes(tickformat=".0%")
    fig.update_layout(showlegend=False, bargap=0.25)
    return fig


# ── Consultant charts ──────────────────────────────────────────────────────────

def consultant_trend(cons_df: pd.DataFrame, consultant_id) -> go.Figure:
    """Client count and total AUM over time for a single consultant."""
    sel = cons_df[cons_df["consultant_id"] == consultant_id].sort_values("fy")
    fy  = sel["fy"].astype(int)
    name = sel["general_consultant"].iloc[0] if len(sel) else str(consultant_id)

    fig = make_subplots(specs=[[{"secondary_y": True}]])

    fig.add_trace(go.Bar(
        x=fy, y=sel["n_systems"],
        name="Client systems",
        marker_color=_BLUE_F,
        marker_line_color=_BLUE,
        marker_line_width=1.2,
        hovertemplate="%{y:.0f} clients<extra></extra>",
    ), secondary_y=False)

    aum_b = sel["MktAssets_net"] / 1e9
    fig.add_trace(go.Scatter(
        x=fy, y=aum_b,
        name="Client AUM ($B)",
        mode="lines+markers",
        line=dict(color=_BLUE, width=2.5),
        marker=dict(size=5),
        hovertemplate="$%{y:.1f}B AUM<extra></extra>",
    ), secondary_y=True)

    fig.update_layout(
        **{k: v for k, v in _LAYOUT_BASE.items() if k not in ("xaxis", "yaxis")},
        title=dict(text=f"{name} — Client Base &amp; AUM", font=dict(size=13, color=_TEXT), x=0),
        hovermode="x unified",
        bargap=0.3,
    )
    fig.update_xaxes(**_LAYOUT_BASE["xaxis"])
    fig.update_yaxes(title_text="Client systems", secondary_y=False,
                     showgrid=True, gridcolor=_GRID, tickfont=dict(size=10))
    fig.update_yaxes(title_text="AUM ($B)", secondary_y=True,
                     showgrid=False, tickfont=dict(size=10))
    return fig


def consultant_metric_trend(
    cons_df: pd.DataFrame,
    consultant_id,
    sys_df: pd.DataFrame,
    metric: str = "omega",
    metric_label: str = "Average client omega",
) -> go.Figure:
    """Avg client metric for a consultant vs. all-consultant average."""
    sel  = cons_df[cons_df["consultant_id"] == consultant_id].sort_values("fy")
    name = sel["general_consultant"].iloc[0] if len(sel) else str(consultant_id)

    # Peer: AUM-weighted average across all systems
    peer = (
        sys_df.groupby("fy", observed=True)
        .apply(lambda g: _wavg_scalar(g, metric, "MktAssets_net"), include_groups=False)
        .reset_index(name="peer")
    )

    fig = _base_fig(title=dict(text=metric_label, font=dict(size=13, color=_TEXT), x=0))

    fig.add_trace(go.Scatter(
        x=peer["fy"].astype(int), y=peer["peer"],
        name="All systems",
        mode="lines",
        line=dict(color=_MUTED, width=1.5, dash="dot"),
        hovertemplate="%{y:.2%}<extra>All systems</extra>",
    ))
    fig.add_trace(go.Scatter(
        x=sel["fy"].astype(int), y=sel[metric],
        name=name,
        mode="lines+markers",
        line=dict(color=_BLUE, width=2.5),
        marker=dict(size=5),
        hovertemplate="%{y:.2%}<extra>" + name + "</extra>",
    ))

    fig.update_yaxes(tickformat=".1%")
    fig.update_layout(hovermode="x unified")
    return fig


def consultant_client_table(sys_df: pd.DataFrame, consultant_id, fy: int) -> pd.DataFrame:
    """Return a display DataFrame of a consultant's clients for `fy`."""
    sel = sys_df[
        (sys_df["consultant_id"] == consultant_id) & (sys_df["fy"] == fy)
    ][["pub_system_name", "StateAbbrev", "MktAssets_net", "omega",
       "ActFundedRatio_GASB", "InvestmentReturnAssumption_GASB", "ret_bgnassets"]].copy()

    sel = sel.rename(columns={
        "pub_system_name": "System",
        "StateAbbrev": "State",
        "MktAssets_net": "AUM ($)",
        "omega": "Omega",
        "ActFundedRatio_GASB": "Funded Ratio",
        "InvestmentReturnAssumption_GASB": "Assumed Return",
        "ret_bgnassets": "Net Return",
    }).sort_values("AUM ($)", ascending=False).reset_index(drop=True)

    return sel


# ── State / Region charts ──────────────────────────────────────────────────────

_METRIC_META = {
    "omega":                          ("Omega (alt ÷ risky)",              ".1%"),
    "ActFundedRatio_GASB":            ("Funded Ratio (GASB 25)",           ".1%"),
    "InvestmentReturnAssumption_GASB":("Assumed Return",                   ".2%"),
    "risky_trgt":                     ("Risky Share (target)",             ".1%"),
    "alternatives_trgt":              ("Alternatives Share (target)",      ".1%"),
    "ret_bgnassets":                  ("Net Return (ret_bgnassets)",       ".2%"),
    "pct_retired":                    ("% Retired Members",                ".1%"),
}

METRIC_CHOICES = list(_METRIC_META.keys())
METRIC_LABELS  = {k: v[0] for k, v in _METRIC_META.items()}


def state_ranking(
    state_df: pd.DataFrame,
    fy: int,
    metric: str = "omega",
    n_top: int = 999,
) -> go.Figure:
    """Horizontal bar chart ranking states by `metric` in `fy`."""
    label, fmt = _METRIC_META.get(metric, (metric, ".2%"))
    snap = (
        state_df[state_df["fy"] == fy][[
            "StateAbbrev", "StateName", metric, "n_systems", "MktAssets_net"
        ]]
        .dropna(subset=[metric])
        .sort_values(metric, ascending=True)
        .tail(n_top)
        .reset_index(drop=True)
    )

    colors = [
        f"rgba(59,130,246,{0.35 + 0.6 * i / max(len(snap) - 1, 1):.2f})"
        for i in range(len(snap))
    ]

    fig = _base_fig(
        title=dict(text=f"{label} by State — FY {fy}", font=dict(size=13, color=_TEXT), x=0),
        height=max(300, 22 * len(snap) + 80),
        margin=dict(l=55, r=20, t=40, b=30),
    )
    fig.add_trace(go.Bar(
        x=snap[metric], y=snap["StateAbbrev"],
        orientation="h",
        marker_color=colors,
        customdata=snap[["StateName", "n_systems", "MktAssets_net"]].values,
        hovertemplate=(
            "<b>%{customdata[0]}</b><br>"
            f"{label}: %{{x:{fmt}}}<br>"
            "Systems: %{customdata[1]:.0f}<br>"
            "AUM: $%{customdata[2]:.2s}<extra></extra>"
        ),
    ))
    fig.update_xaxes(tickformat=fmt, showgrid=True, gridcolor=_GRID)
    fig.update_yaxes(showgrid=False, tickfont=dict(size=9))
    fig.update_layout(showlegend=False, bargap=0.2)
    return fig


def state_trend(
    state_df: pd.DataFrame,
    states: list[str],
    metric: str = "omega",
) -> go.Figure:
    """Multi-state line chart for `metric` over time."""
    label, fmt = _METRIC_META.get(metric, (metric, ".2%"))
    sel = state_df[state_df["StateAbbrev"].isin(states)].sort_values("fy")

    fig = _base_fig(title=dict(text=f"{label} over Time", font=dict(size=13, color=_TEXT), x=0))

    for i, state in enumerate(states):
        sub = sel[sel["StateAbbrev"] == state]
        if sub.empty:
            continue
        color = _PALETTE[i % len(_PALETTE)]
        state_name = sub["StateName"].iloc[0] if "StateName" in sub.columns else state
        fig.add_trace(go.Scatter(
            x=sub["fy"].astype(int), y=sub[metric],
            name=state_name or state,
            mode="lines+markers",
            line=dict(color=color, width=2),
            marker=dict(size=4),
            hovertemplate=f"%{{x}}: %{{y:{fmt}}}<extra>{state}</extra>",
        ))

    fig.update_yaxes(tickformat=fmt)
    fig.update_layout(hovermode="x unified")
    return fig


def scatter_omega_funding(state_df: pd.DataFrame, fy: int) -> go.Figure:
    """Scatter: omega (x) vs funded ratio (y), sized by AUM."""
    snap = state_df[state_df["fy"] == fy].dropna(subset=["omega", "ActFundedRatio_GASB"]).copy()
    aum  = snap["MktAssets_net"].fillna(snap["MktAssets_net"].median())
    marker_size = 8 + 30 * (aum / aum.max()).clip(0, 1)

    fig = _base_fig(
        title=dict(text=f"Omega vs Funded Ratio — FY {fy}", font=dict(size=13, color=_TEXT), x=0),
    )
    fig.add_trace(go.Scatter(
        x=snap["omega"],
        y=snap["ActFundedRatio_GASB"],
        mode="markers+text",
        text=snap["StateAbbrev"],
        textposition="top center",
        textfont=dict(size=8, color=_MUTED),
        marker=dict(
            size=marker_size,
            color=snap["omega"],
            colorscale=[[0, _SKY], [1, _PURPLE]],
            line=dict(color=_BORDER, width=0.5),
            opacity=0.85,
        ),
        customdata=snap[["StateName", "n_systems", "MktAssets_net"]].values,
        hovertemplate=(
            "<b>%{customdata[0]}</b><br>"
            "Omega: %{x:.1%}<br>"
            "Funded: %{y:.1%}<br>"
            "Systems: %{customdata[1]:.0f}<br>"
            "AUM: $%{customdata[2]:.2s}<extra></extra>"
        ),
    ))
    fig.update_xaxes(tickformat=".0%", title_text="Omega", title_font=dict(size=10))
    fig.update_yaxes(tickformat=".0%", title_text="Funded Ratio", title_font=dict(size=10))
    return fig


# ── Landing-page charts ────────────────────────────────────────────────────────

def aggregate_omega_hero(sys_df: pd.DataFrame) -> go.Figure:
    """AUM-weighted aggregate omega over time — landing hero (Figure 2c shape)."""
    series = (
        sys_df.groupby("fy", observed=True)
        .apply(lambda g: _wavg_scalar(g, "omega", "MktAssets_net"), include_groups=False)
        .reset_index(name="omega")
        .dropna()
        .sort_values("fy")
    )
    fy = series["fy"].astype(int)

    fig = _base_fig(margin=dict(l=10, r=10, t=10, b=10), height=240)
    fig.add_trace(go.Scatter(
        x=fy, y=series["omega"],
        mode="lines",
        line=dict(color=_BLUE, width=2.5, shape="spline"),
        fill="tozeroy",
        fillcolor="rgba(59,130,246,0.18)",
        hovertemplate="FY %{x}: %{y:.1%}<extra></extra>",
        name="Aggregate ω",
    ))
    fig.add_vline(x=2012, line=dict(color=_BORDER, width=1, dash="dash"),
                  annotation_text="low-yield era begins",
                  annotation_position="top right",
                  annotation_font=dict(color=_MUTED, size=9, family="IBM Plex Mono, monospace"))
    fig.update_yaxes(tickformat=".0%", rangemode="tozero")
    fig.update_layout(showlegend=False, hovermode="x unified")
    return fig


def sparkline(sys_df: pd.DataFrame, col: str, color: str = _GREEN) -> go.Figure:
    """Tiny area sparkline of an AUM-weighted aggregate over time."""
    series = (
        sys_df.groupby("fy", observed=True)
        .apply(lambda g: _wavg_scalar(g, col, "MktAssets_net"), include_groups=False)
        .reset_index(name="v")
        .dropna()
        .sort_values("fy")
    )
    fig = go.Figure(layout=go.Layout(
        paper_bgcolor=_CARD,
        plot_bgcolor=_CARD,
        margin=dict(l=0, r=0, t=2, b=0),
        height=44,
        xaxis=dict(visible=False),
        yaxis=dict(visible=False),
        showlegend=False,
    ))
    fig.add_trace(go.Scatter(
        x=series["fy"], y=series["v"],
        mode="lines",
        line=dict(color=color, width=1.6, shape="spline"),
        fill="tozeroy",
        fillcolor=f"rgba({_hex_to_rgb(color)},0.28)",
        hoverinfo="skip",
    ))
    return fig


def _hex_to_rgb(hx: str) -> str:
    h = hx.lstrip("#")
    return f"{int(h[0:2],16)},{int(h[2:4],16)},{int(h[4:6],16)}"


# ── Internal helpers ───────────────────────────────────────────────────────────

def _wavg_scalar(g: pd.DataFrame, col: str, wcol: str = "MktAssets_net") -> float:
    """AUM-weighted average of col in group g, returning scalar."""
    w = g[wcol].where(g[wcol].notna() & (g[wcol] > 0), 0.0)
    v = g[col]
    ok = v.notna() & (w > 0)
    if not ok.any():
        return float("nan")
    return float(np.average(v[ok], weights=w[ok]))
