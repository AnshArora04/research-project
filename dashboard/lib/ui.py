"""Shared UI helpers: theme injection and common layout components.

Every Streamlit page should call ``apply_theme()`` immediately after
``st.set_page_config()``.
"""

from __future__ import annotations

import streamlit as st

# ── Design tokens ─────────────────────────────────────────────────────────────
# Kept in sync with .streamlit/config.toml and the CSS :root variables below.
AMBER  = "#C68B20"
BLUE   = "#4A8DF5"
GREEN  = "#3DAD6E"
RED    = "#E05252"
MUTED  = "#5A6480"

# ── Global CSS ────────────────────────────────────────────────────────────────
_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,700;0,900;1,700&family=IBM+Plex+Mono:wght@400;500;600&family=IBM+Plex+Sans:wght@300;400;500;600&display=swap');

/* ── Design tokens ────────────────────────────────────────────────────────── */
:root {
  --ppd-bg:       #0C0E12;
  --ppd-surface:  #131720;
  --ppd-border:   #1F2636;
  --ppd-text:     #D6DCE8;
  --ppd-muted:    #5A6480;
  --ppd-amber:    #C68B20;
  --ppd-amber-lo: rgba(198, 139, 32, 0.15);
  --ppd-blue:     #4A8DF5;
  --ppd-green:    #3DAD6E;
  --ppd-red:      #E05252;
  --ppd-rule:     #1A2030;
}

/* ── Typography ───────────────────────────────────────────────────────────── */
html, body, .stApp, [class*="st-"] {
  font-family: 'IBM Plex Sans', sans-serif !important;
}
h1, h2, h3 {
  font-family: 'Playfair Display', serif !important;
  letter-spacing: -0.01em;
}
code, pre, .stCode, .mono {
  font-family: 'IBM Plex Mono', monospace !important;
}

/* ── Chrome cleanup ───────────────────────────────────────────────────────── */
#MainMenu          { visibility: hidden; }
footer             { visibility: hidden; }
.stDeployButton    { display: none !important; }
[data-testid="stDecoration"]   { display: none !important; }
[data-testid="stStatusWidget"] { display: none !important; }

/* ── Layout ───────────────────────────────────────────────────────────────── */
.block-container {
  padding-top: 2.2rem;
  padding-bottom: 5rem;
  max-width: 1180px;
}

/* ── Sidebar ──────────────────────────────────────────────────────────────── */
[data-testid="stSidebar"] {
  border-right: 1px solid var(--ppd-border) !important;
}
[data-testid="stSidebar"] .block-container {
  padding-top: 1.6rem;
}

/* ── Cards ────────────────────────────────────────────────────────────────── */
.ppd-card {
  background: var(--ppd-surface);
  border: 1px solid var(--ppd-border);
  border-radius: 3px;
  padding: 1.4rem 1.5rem 1.2rem;
  height: 100%;
}
.ppd-card:hover {
  border-color: rgba(198, 139, 32, 0.4);
}

/* ── Navigation cards (landing) ──────────────────────────────────────────── */
.nav-card {
  background: var(--ppd-surface);
  border: 1px solid var(--ppd-border);
  border-radius: 3px;
  padding: 1.8rem 1.6rem 1.3rem;
  height: 100%;
  transition: border-color 0.12s;
}
.nav-card:hover { border-color: rgba(198, 139, 32, 0.5); }

.nav-card-badge {
  font-family: 'IBM Plex Mono', monospace;
  font-size: 0.66rem;
  letter-spacing: 0.14em;
  text-transform: uppercase;
  color: var(--ppd-amber);
  margin-bottom: 0.9rem;
  display: block;
}
.nav-card-title {
  font-family: 'Playfair Display', serif;
  font-size: 1.2rem;
  font-weight: 700;
  color: var(--ppd-text);
  margin: 0 0 0.5rem 0;
}
.nav-card-body {
  font-size: 0.84rem;
  color: var(--ppd-muted);
  line-height: 1.6;
  margin: 0 0 1.1rem 0;
}
.nav-card-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 0.35rem;
}
.tag {
  font-family: 'IBM Plex Mono', monospace;
  font-size: 0.62rem;
  letter-spacing: 0.05em;
  text-transform: uppercase;
  padding: 0.18rem 0.5rem;
  border: 1px solid var(--ppd-border);
  border-radius: 2px;
  color: var(--ppd-muted);
}

/* ── Page link overrides ──────────────────────────────────────────────────── */
[data-testid="stPageLink"] a,
[data-testid="stPageLink"] span {
  font-family: 'IBM Plex Mono', monospace !important;
  font-size: 0.76rem !important;
  letter-spacing: 0.05em !important;
  text-transform: uppercase !important;
  color: var(--ppd-amber) !important;
  text-decoration: none !important;
}
[data-testid="stPageLink"] a:hover { color: var(--ppd-text) !important; }

/* ── Section divider ──────────────────────────────────────────────────────── */
.ppd-rule {
  border: none;
  border-top: 1px solid var(--ppd-border);
  margin: 2rem 0;
}

/* ── Eyebrow / label ──────────────────────────────────────────────────────── */
.ppd-eyebrow {
  font-family: 'IBM Plex Mono', monospace;
  font-size: 0.68rem;
  letter-spacing: 0.16em;
  text-transform: uppercase;
  color: var(--ppd-amber);
  margin-bottom: 0.4rem;
}

/* ── Page title ───────────────────────────────────────────────────────────── */
.ppd-title {
  font-family: 'Playfair Display', serif;
  font-size: clamp(2rem, 4.5vw, 3.5rem);
  font-weight: 900;
  line-height: 1.06;
  color: var(--ppd-text);
  margin: 0 0 0.8rem 0;
}

/* ── Subtitle / lead paragraph ────────────────────────────────────────────── */
.ppd-lead {
  font-size: 0.9rem;
  color: var(--ppd-muted);
  line-height: 1.65;
  max-width: 580px;
  margin: 0 0 2.2rem 0;
}

/* ── Status dots ──────────────────────────────────────────────────────────── */
.status-panel {
  background: var(--ppd-surface);
  border: 1px solid var(--ppd-border);
  border-radius: 3px;
  padding: 1rem 1.5rem;
  display: flex;
  align-items: center;
  gap: 2rem;
  flex-wrap: wrap;
}
.status-item { display: flex; flex-direction: column; gap: 0.1rem; }
.status-label {
  font-family: 'IBM Plex Mono', monospace;
  font-size: 0.6rem;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: var(--ppd-muted);
}
.status-value {
  font-family: 'IBM Plex Mono', monospace;
  font-size: 0.8rem;
  color: var(--ppd-text);
}
.dot {
  display: inline-block;
  width: 6px; height: 6px;
  border-radius: 50%;
  margin-right: 0.35rem;
  vertical-align: middle;
}
.dot-ok   { background: #3DAD6E; }
.dot-warn { background: #C68B20; }
.dot-err  { background: #E05252; }

/* ── Metric tiles ─────────────────────────────────────────────────────────── */
.kpi-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
  gap: 1px;
  background: var(--ppd-border);
  border: 1px solid var(--ppd-border);
  border-radius: 3px;
  overflow: hidden;
}
.kpi-tile {
  background: var(--ppd-surface);
  padding: 1.1rem 1.3rem;
}
.kpi-label {
  font-family: 'IBM Plex Mono', monospace;
  font-size: 0.6rem;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: var(--ppd-muted);
  margin-bottom: 0.35rem;
}
.kpi-value {
  font-family: 'IBM Plex Mono', monospace;
  font-size: 1.6rem;
  font-weight: 600;
  color: var(--ppd-text);
  line-height: 1;
}
.kpi-sub {
  font-family: 'IBM Plex Sans', sans-serif;
  font-size: 0.72rem;
  color: var(--ppd-muted);
  margin-top: 0.25rem;
}

/* ── Attribution fine print ───────────────────────────────────────────────── */
.ppd-attribution {
  font-size: 0.7rem;
  color: var(--ppd-muted);
  margin-top: 1.8rem;
  line-height: 1.6;
}
.ppd-attribution a { color: var(--ppd-muted); }
.ppd-attribution a:hover { color: var(--ppd-text); }

/* ── Placeholder / coming-soon blocks ────────────────────────────────────── */
.ppd-placeholder {
  border: 1px dashed var(--ppd-border);
  border-radius: 3px;
  padding: 3rem 2rem;
  text-align: center;
  color: var(--ppd-muted);
}
.ppd-placeholder .ph-icon {
  font-family: 'IBM Plex Mono', monospace;
  font-size: 1.8rem;
  display: block;
  margin-bottom: 1rem;
  color: var(--ppd-amber);
  opacity: 0.5;
}
.ppd-placeholder .ph-label {
  font-family: 'Playfair Display', serif;
  font-size: 1.1rem;
  color: var(--ppd-text);
  margin-bottom: 0.4rem;
}
.ppd-placeholder .ph-body {
  font-size: 0.82rem;
  line-height: 1.6;
}
</style>
"""


def apply_theme() -> None:
    """Inject the global CSS theme.  Call once per page, after set_page_config()."""
    st.markdown(_CSS, unsafe_allow_html=True)


def page_header(eyebrow: str, title: str, lead: str = "") -> None:
    """Render a consistent page header with eyebrow label, title, and optional lead."""
    html = f'<p class="ppd-eyebrow">{eyebrow}</p><h1 class="ppd-title">{title}</h1>'
    if lead:
        html += f'<p class="ppd-lead">{lead}</p>'
    html += '<hr class="ppd-rule" />'
    st.markdown(html, unsafe_allow_html=True)


def rule() -> None:
    """Render a section divider."""
    st.markdown('<hr class="ppd-rule" />', unsafe_allow_html=True)


def placeholder(label: str, body: str = "Available in the next build step.") -> None:
    """Render a dashed placeholder block for upcoming content."""
    st.markdown(
        f"""
<div class="ppd-placeholder">
  <span class="ph-icon">◈</span>
  <div class="ph-label">{label}</div>
  <p class="ph-body">{body}</p>
</div>""",
        unsafe_allow_html=True,
    )


def kpi_grid(items: list[tuple[str, str, str]]) -> None:
    """Render a horizontal KPI strip.

    Parameters
    ----------
    items : list of (label, value, sub_label) tuples
    """
    tiles = "".join(
        f'<div class="kpi-tile">'
        f'<div class="kpi-label">{lbl}</div>'
        f'<div class="kpi-value">{val}</div>'
        f'<div class="kpi-sub">{sub}</div>'
        f'</div>'
        for lbl, val, sub in items
    )
    st.markdown(f'<div class="kpi-grid">{tiles}</div>', unsafe_allow_html=True)


ATTRIBUTION_HTML = """
<p class="ppd-attribution">
  Data: <a href="https://publicplansdata.org" target="_blank">Public Plans Database</a>
  (Center for Retirement Research, Boston College) ·
  Research: Begenau, Liang &amp; Siriwardane (2026),
  <em>The Rise of Alternatives</em>, <em>Review of Financial Studies</em> ·
  Consultant data: Andonov, Bonetti &amp; Stefanescu (2025)
</p>
"""
