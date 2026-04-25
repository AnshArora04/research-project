"""Shared UI helpers: theme injection and common layout components.

Every Streamlit page should call ``apply_theme()`` immediately after
``st.set_page_config()``.

Aesthetic: dark-blue terminal (IBM Plex Mono primary). Tokens kept in sync
with .streamlit/config.toml and the chart palette in lib/charts.py.
"""

from __future__ import annotations

import streamlit as st

# ── Design tokens ─────────────────────────────────────────────────────────────
BG          = "#080C14"
SURFACE     = "#0D1526"
CARD        = "#111D35"
BORDER      = "#1E3254"
TEXT        = "#E2EAF4"
MUTED       = "#7A9BBF"
BLUE        = "#3B82F6"
SKY         = "#38BDF8"
GREEN       = "#34D399"
RED         = "#F87171"
PURPLE      = "#A78BFA"
ORANGE      = "#FB923C"

# ── Global CSS ────────────────────────────────────────────────────────────────
_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500;600;700&family=IBM+Plex+Sans:ital,wght@0,400;0,500;0,600;1,400&display=swap');

:root {
  --ppd-bg:        #080C14;
  --ppd-surface:   #0D1526;
  --ppd-card:      #111D35;
  --ppd-border:    #1E3254;
  --ppd-text:      #E2EAF4;
  --ppd-muted:     #7A9BBF;
  --ppd-blue:      #3B82F6;
  --ppd-blue-soft: rgba(59,130,246,0.10);
  --ppd-blue-glow: 0 0 14px rgba(59,130,246,0.25);
  --ppd-sky:       #38BDF8;
  --ppd-green:     #34D399;
  --ppd-red:       #F87171;
  --ppd-purple:    #A78BFA;
}

/* ── Typography (mono primary, sans for body copy) ───────────────────────── */
html, body, .stApp, [class*="st-"] {
  font-family: 'IBM Plex Sans', sans-serif;
}
h1, h2, h3, h4, h5, h6,
.ppd-mono, .ppd-eyebrow, .ppd-title, .ppd-section, .kpi-label, .kpi-value,
.nav-card-title, .nav-card-badge, .insight-label,
[data-testid="stMetricValue"], [data-testid="stMetricLabel"] {
  font-family: 'IBM Plex Mono', monospace !important;
}
code, pre, .stCode { font-family: 'IBM Plex Mono', monospace !important; }

/* ── Chrome cleanup ──────────────────────────────────────────────────────── */
#MainMenu          { visibility: hidden; }
footer             { visibility: hidden; }
.stDeployButton    { display: none !important; }
[data-testid="stDecoration"]   { display: none !important; }
[data-testid="stStatusWidget"] { display: none !important; }
[data-testid="stHeader"]       { background: transparent; }

/* ── Layout ──────────────────────────────────────────────────────────────── */
.block-container {
  padding-top: 2.4rem;
  padding-bottom: 5rem;
  max-width: 1180px;
}

/* ── Sidebar — dark navy with blue accent ────────────────────────────────── */
[data-testid="stSidebar"] {
  background: var(--ppd-surface) !important;
  border-right: 1px solid var(--ppd-border) !important;
}
[data-testid="stSidebar"] .block-container {
  padding-top: 1.6rem;
}
[data-testid="stSidebarNav"] a {
  font-family: 'IBM Plex Mono', monospace !important;
  font-size: 0.78rem !important;
  letter-spacing: 0.04em;
}
[data-testid="stSidebarNav"] a[aria-current="page"] {
  background: var(--ppd-blue-soft) !important;
  border-left: 3px solid var(--ppd-blue) !important;
  color: var(--ppd-text) !important;
}

/* ── Scrollbars ──────────────────────────────────────────────────────────── */
::-webkit-scrollbar       { width: 6px; height: 6px; }
::-webkit-scrollbar-track { background: var(--ppd-surface); }
::-webkit-scrollbar-thumb { background: var(--ppd-border); border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: var(--ppd-blue); }

/* ── Eyebrow / labels ────────────────────────────────────────────────────── */
.ppd-eyebrow {
  font-size: 0.65rem;
  letter-spacing: 0.14em;
  text-transform: uppercase;
  color: var(--ppd-muted);
  margin-bottom: 0.55rem;
}

/* ── Page title (mono, tight) ────────────────────────────────────────────── */
.ppd-title {
  font-size: clamp(1.6rem, 3vw, 1.95rem);
  font-weight: 700;
  line-height: 1.15;
  letter-spacing: -0.01em;
  color: var(--ppd-text);
  margin: 0 0 0.55rem 0;
}
.ppd-title-hero {
  font-size: clamp(2rem, 4vw, 2.6rem);
}

/* ── Lead paragraph (sans) ───────────────────────────────────────────────── */
.ppd-lead {
  font-family: 'IBM Plex Sans', sans-serif !important;
  font-size: 0.92rem;
  color: var(--ppd-muted);
  line-height: 1.7;
  max-width: 620px;
  margin: 0 0 1.6rem 0;
}

/* ── Section header (uppercase mono, bottom border) ──────────────────────── */
.ppd-section {
  font-size: 0.66rem;
  letter-spacing: 0.14em;
  text-transform: uppercase;
  color: var(--ppd-muted);
  margin: 2rem 0 0.9rem 0;
  padding-bottom: 0.5rem;
  border-bottom: 1px solid var(--ppd-border);
}

/* ── Section divider ─────────────────────────────────────────────────────── */
.ppd-rule {
  border: none;
  border-top: 1px solid var(--ppd-border);
  margin: 1.6rem 0;
}

/* ── KPI tiles (left blue accent + glow) ─────────────────────────────────── */
.kpi-strip {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 14px;
  margin-bottom: 1.6rem;
}
.kpi-tile {
  background: var(--ppd-card);
  border-left: 3px solid var(--ppd-blue);
  padding: 16px 20px 18px;
  box-shadow: 0 0 14px rgba(59,130,246,0.14);
}
.kpi-tile.accent-sky    { border-left-color: var(--ppd-sky);    box-shadow: 0 0 14px rgba(56,189,248,0.14); }
.kpi-tile.accent-green  { border-left-color: var(--ppd-green);  box-shadow: 0 0 14px rgba(52,211,153,0.14); }
.kpi-tile.accent-red    { border-left-color: var(--ppd-red);    box-shadow: 0 0 14px rgba(248,113,113,0.14); }
.kpi-tile.accent-purple { border-left-color: var(--ppd-purple); box-shadow: 0 0 14px rgba(167,139,250,0.14); }
.kpi-tile.accent-muted  { border-left-color: var(--ppd-border); box-shadow: none; }

.kpi-label {
  font-size: 0.62rem;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: var(--ppd-muted);
  margin-bottom: 0.5rem;
}
.kpi-value {
  font-size: 1.55rem;
  font-weight: 600;
  color: var(--ppd-text);
  line-height: 1;
}
.kpi-sub {
  font-family: 'IBM Plex Sans', sans-serif !important;
  font-size: 0.74rem;
  color: var(--ppd-muted);
  margin-top: 0.45rem;
  line-height: 1.45;
}

/* ── Insight box (left blue rule, tinted background) ─────────────────────── */
.insight-box {
  border-left: 3px solid var(--ppd-blue);
  background: var(--ppd-blue-soft);
  padding: 10px 16px;
  margin: 0.4rem 0 1rem 0;
  color: var(--ppd-text);
  font-family: 'IBM Plex Sans', sans-serif !important;
  font-size: 0.84rem;
  line-height: 1.6;
  border-radius: 0 3px 3px 0;
}

/* ── Hero card (landing chart container) ─────────────────────────────────── */
.hero-card {
  background: var(--ppd-card);
  border: 1px solid var(--ppd-border);
  padding: 18px 20px 14px;
  margin-bottom: 1rem;
}
.hero-card-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 0.4rem;
}
.hero-card-title {
  font-size: 0.84rem;
  font-weight: 600;
  letter-spacing: 0.03em;
  color: var(--ppd-text);
}
.hero-card-sub {
  font-family: 'IBM Plex Sans', sans-serif !important;
  font-size: 0.78rem;
  color: var(--ppd-muted);
  margin-top: 2px;
}
.hero-card-stat {
  text-align: right;
}
.hero-card-stat-val {
  color: var(--ppd-blue);
  font-size: 1.5rem;
  font-weight: 700;
  line-height: 1;
}
.hero-card-stat-lbl {
  color: var(--ppd-muted);
  font-size: 0.62rem;
  margin-top: 3px;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}
.hero-card-foot {
  font-family: 'IBM Plex Sans', sans-serif !important;
  color: var(--ppd-muted);
  font-size: 0.74rem;
  margin-top: 10px;
  padding-top: 10px;
  border-top: 1px solid var(--ppd-border);
  line-height: 1.6;
}

/* ── Sub-allocation sparkline strip ──────────────────────────────────────── */
.sub-strip {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 12px;
  margin-bottom: 1.4rem;
}
.sub-card {
  background: var(--ppd-card);
  border: 1px solid var(--ppd-border);
  padding: 14px 16px;
}
.sub-card-label {
  font-size: 0.6rem;
  text-transform: uppercase;
  letter-spacing: 0.1em;
  color: var(--ppd-muted);
  margin-bottom: 8px;
}
.sub-card-row {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
}
.sub-card-start { color: var(--ppd-muted); font-size: 0.78rem; }
.sub-card-end   { font-size: 1.2rem; font-weight: 600; }
.sub-card-end.green  { color: var(--ppd-green); }
.sub-card-end.purple { color: var(--ppd-purple); }
.sub-card-end.sky    { color: var(--ppd-sky); }

/* ── Nav cards (landing) ─────────────────────────────────────────────────── */
.nav-card {
  background: var(--ppd-card);
  border: 1px solid var(--ppd-border);
  padding: 18px 22px;
  height: 100%;
  transition: border-color 0.15s, box-shadow 0.15s;
}
.nav-card:hover {
  border-color: var(--ppd-blue);
  box-shadow: var(--ppd-blue-glow);
}
.nav-card-icon {
  color: var(--ppd-blue);
  font-size: 1.05rem;
  margin-bottom: 6px;
}
.nav-card-title {
  font-size: 0.86rem;
  font-weight: 600;
  color: var(--ppd-text);
  margin: 0 0 0.4rem 0;
}
.nav-card-body {
  font-family: 'IBM Plex Sans', sans-serif !important;
  font-size: 0.8rem;
  color: var(--ppd-muted);
  line-height: 1.55;
  margin: 0;
}

/* ── Page link overrides ─────────────────────────────────────────────────── */
[data-testid="stPageLink"] a,
[data-testid="stPageLink"] span {
  font-family: 'IBM Plex Mono', monospace !important;
  font-size: 0.74rem !important;
  letter-spacing: 0.06em !important;
  text-transform: uppercase !important;
  color: var(--ppd-blue) !important;
  text-decoration: none !important;
}
[data-testid="stPageLink"] a:hover { color: var(--ppd-text) !important; }

/* ── Inputs (selectbox, slider, text) ────────────────────────────────────── */
[data-baseweb="select"] > div,
[data-testid="stTextInput"] input,
[data-testid="stMultiSelect"] > div {
  background: var(--ppd-card) !important;
  border-color: var(--ppd-border) !important;
  color: var(--ppd-text) !important;
  font-family: 'IBM Plex Mono', monospace !important;
  font-size: 0.82rem !important;
}
[data-baseweb="select"] > div:focus-within,
[data-testid="stTextInput"] input:focus {
  border-color: var(--ppd-blue) !important;
  box-shadow: var(--ppd-blue-glow) !important;
}

/* ── Buttons + download ──────────────────────────────────────────────────── */
[data-testid="stDownloadButton"] button,
[data-testid="stButton"] button {
  background: transparent !important;
  border: 1px solid var(--ppd-blue) !important;
  color: var(--ppd-blue) !important;
  font-family: 'IBM Plex Mono', monospace !important;
  font-size: 0.72rem !important;
  letter-spacing: 0.06em !important;
  text-transform: uppercase !important;
  padding: 6px 14px !important;
  border-radius: 2px !important;
}
[data-testid="stDownloadButton"] button:hover,
[data-testid="stButton"] button:hover {
  background: var(--ppd-blue-soft) !important;
}

/* ── Dataframe ───────────────────────────────────────────────────────────── */
[data-testid="stDataFrame"] {
  background: var(--ppd-card);
  border: 1px solid var(--ppd-border);
}

/* ── Attribution ─────────────────────────────────────────────────────────── */
.ppd-attribution {
  font-family: 'IBM Plex Sans', sans-serif !important;
  font-size: 0.74rem;
  color: var(--ppd-muted);
  margin-top: 1.8rem;
  padding-top: 1rem;
  border-top: 1px solid var(--ppd-border);
  line-height: 1.7;
}
.ppd-attribution a, .ppd-attribution strong { color: var(--ppd-text); font-weight: 500; }
.ppd-attribution em { color: var(--ppd-text); }

/* ── Citation block (Methodology) ────────────────────────────────────────── */
.citation-block {
  margin-top: 2rem;
  padding: 18px 22px;
  background: var(--ppd-card);
  border: 1px solid var(--ppd-border);
  border-left: 3px solid var(--ppd-blue);
}
.citation-block .insight-label {
  color: var(--ppd-blue);
  font-size: 0.66rem;
  text-transform: uppercase;
  letter-spacing: 0.1em;
  margin-bottom: 6px;
}
.citation-block p {
  font-family: 'IBM Plex Mono', monospace !important;
  color: var(--ppd-muted);
  font-size: 0.78rem;
  line-height: 1.7;
  margin: 0;
}
.citation-block em { color: var(--ppd-text); font-style: italic; }

/* ── Numbered methodology section heading ────────────────────────────────── */
.method-section {
  font-family: 'IBM Plex Mono', monospace !important;
  color: var(--ppd-blue);
  font-size: 0.78rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.1em;
  margin: 2rem 0 0.7rem 0;
  padding-bottom: 0.5rem;
  border-bottom: 1px solid var(--ppd-border);
}
.method-section .num {
  color: var(--ppd-muted);
  margin-right: 10px;
}
</style>
"""


def apply_theme() -> None:
    """Inject the global CSS theme.  Call once per page, after set_page_config()."""
    st.markdown(_CSS, unsafe_allow_html=True)


def page_header(eyebrow: str, title: str, lead: str = "", hero: bool = False) -> None:
    """Render a consistent page header."""
    title_cls = "ppd-title ppd-title-hero" if hero else "ppd-title"
    html = f'<div class="ppd-eyebrow">{eyebrow}</div><h1 class="{title_cls}">{title}</h1>'
    if lead:
        html += f'<p class="ppd-lead">{lead}</p>'
    st.markdown(html, unsafe_allow_html=True)


def section(label: str) -> None:
    st.markdown(f'<div class="ppd-section">{label}</div>', unsafe_allow_html=True)


def rule() -> None:
    st.markdown('<hr class="ppd-rule" />', unsafe_allow_html=True)


def insight(text: str) -> None:
    """One-line takeaway box, blue-accented, above a chart."""
    st.markdown(f'<div class="insight-box">{text}</div>', unsafe_allow_html=True)


# Backwards-compatible KPI grid (label, value, sub) tuples; supports optional accent
def kpi_grid(items) -> None:
    """Render a KPI tile strip.

    items: iterable of (label, value, sub) or (label, value, sub, accent).
    accent ∈ {'blue', 'sky', 'green', 'red', 'purple', 'muted'}.
    """
    tiles = []
    for it in items:
        if len(it) == 4:
            lbl, val, sub, accent = it
        else:
            lbl, val, sub = it
            accent = "blue"
        accent_cls = f"accent-{accent}" if accent != "blue" else ""
        tiles.append(
            f'<div class="kpi-tile {accent_cls}">'
            f'<div class="kpi-label">{lbl}</div>'
            f'<div class="kpi-value">{val}</div>'
            f'<div class="kpi-sub">{sub}</div>'
            f'</div>'
        )
    st.markdown(f'<div class="kpi-strip">{"".join(tiles)}</div>', unsafe_allow_html=True)


def hero_card_open(title: str, sub: str, stat_value: str, stat_label: str) -> None:
    """Open a hero chart card. Caller renders the chart, then calls hero_card_close."""
    st.markdown(
        f'''<div class="hero-card">
  <div class="hero-card-header">
    <div>
      <div class="hero-card-title">{title}</div>
      <div class="hero-card-sub">{sub}</div>
    </div>
    <div class="hero-card-stat">
      <div class="hero-card-stat-val">{stat_value}</div>
      <div class="hero-card-stat-lbl">{stat_label}</div>
    </div>
  </div>''',
        unsafe_allow_html=True,
    )


def hero_card_close(footer: str = "") -> None:
    foot = f'<div class="hero-card-foot">{footer}</div>' if footer else ""
    st.markdown(f"{foot}</div>", unsafe_allow_html=True)


ATTRIBUTION_HTML = """
<p class="ppd-attribution">
  Data: <a href="https://publicplansdata.org" target="_blank">Public Plans Database</a>
  (Center for Retirement Research, Boston College) ·
  Research: <strong>Begenau, Liang &amp; Siriwardane (2026)</strong>,
  <em>The Rise of Alternatives</em>, <em>Review of Financial Studies</em> ·
  Consultant data: Andonov, Bonetti &amp; Stefanescu (2025).
</p>
"""
