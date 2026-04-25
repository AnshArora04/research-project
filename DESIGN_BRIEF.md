# PPD Explorer — Design Brief for Redesign

## What is this?

An interactive research dashboard for exploring U.S. public pension fund data from the paper **"The Rise of Alternatives"** by Begenau, Liang & Siriwardane (2026, Review of Financial Studies). Primary users are academic researchers and finance PhD students — people who understand what "omega" and "GASB" mean but who have never heard of Streamlit.

**The data covers:**
- 174 public pension systems, FY 2001–2021
- ~3,128 system-year observations
- Key metrics: alternative-to-risky share (omega), funding ratio, net returns, asset allocation over time
- Three analytical lenses: system-level deep-dives, investment consultant analysis, state/regional comparisons

---

## Current Tech Stack

Built in **Streamlit** (Python web framework). Pages are Python files that emit Streamlit widgets — this is not React/HTML. Any redesign has to work within Streamlit's constraints:

- Layout is controlled via `st.columns()`, `st.sidebar`, `st.tabs()`
- Custom HTML/CSS injected via `st.markdown(html, unsafe_allow_html=True)`
- Charts are **Plotly** figures rendered with `st.plotly_chart(fig, use_container_width=True)`
- Streamlit widgets (selectbox, slider, multiselect, download_button) have limited styling via CSS selectors
- No JS allowed. No React components (without `st.components.v1`).

The CSS is all injected in one `<style>` block at the top of every page via a shared `apply_theme()` function in `dashboard/lib/ui.py`. All Plotly chart themes are in `dashboard/lib/charts.py`.

---

## Current Structure (5 pages)

```
streamlit_app.py         ← Landing page / hub
pages/
  1_System_or_Pension.py ← Drill into a single pension system
  2_Consultant.py        ← Drill into a single investment consultant
  3_State_or_Region.py   ← Compare states / Census regions
  4_Methodology.py       ← Static documentation
```

Navigation: Streamlit's built-in sidebar page list + custom nav cards on the landing page.

---

## What's Wrong Right Now (the problems to fix)

### 1. The landing page is dead weight
The landing page has three "nav cards" — boxes with a title, description, and a link. They look okay on paper but contribute nothing. The page just says "here are three sections, click one." There's no data visible on the landing page itself. A user lands there and has no idea what they're actually going to see or why they should care.

**What it should do instead:** Show the data immediately. Give the user something to look at on arrival — a headline chart (e.g., the rise of alternatives 2001–2021 across all systems), a few striking numbers (total AUM in the sample, how much omega has grown, etc.), and let them navigate from there.

### 2. The system selector is unusable
Page 1 has a `st.selectbox` with **174 pension system names** in a flat dropdown. There is no search, no grouping by state, no way to find "California Public Employees" without scrolling through an alphabetical list. This is the primary entry point for the most important page and it's terrible UX.

**What it should be:** A search-as-you-type text input that filters the list, or at minimum a two-step selector (pick a state → pick a system within that state). Streamlit's `st.selectbox` does support text search natively if used correctly.

### 3. The KPI tiles are visually confusing
Six "metric tiles" appear at the top of each detail page:
- System ID code (e.g. `CA1001`) displayed in giant monospace font — not useful
- FY Range: "2001–2021 · 21 years of data" — redundant with the slider right above it
- Latest Omega, Latest Risky, Funded Ratio, Consultant

The tile layout was designed to look like a Bloomberg terminal but it ends up being a grid of numbers with no context. The labels are too small to read, the values are too large to scan, and a user who doesn't know what "omega" is learns nothing from seeing "38.2%".

**What it should be:** Fewer tiles (3 max), with the most meaningful metrics, with brief inline explanations. Or replaced entirely by a summary sentence at the top: *"CalPERs holds 38% of its risky portfolio in alternatives, above the national average of 30%, and is 71% funded."*

### 4. Four charts stacked with no narrative
Page 1 has four Plotly charts in a 2×2 grid:
- Stacked area: target allocation over time
- Line: omega vs peer average
- Dual-axis: funding ratio + assumed return
- Bar: annual net return (green/red)

The charts themselves are data-rich and correct. The problem is there's nothing connecting them. A user sees four charts and has to figure out the story themselves. There's no text between charts, no titles that explain what to notice, no annotation of key events (2008 crisis, post-2010 shift to alternatives).

**What it should be:** Each chart should have a 1–2 line human-readable takeaway above or below it, auto-generated from the data (e.g., "Omega grew from X% in 2001 to Y% in 2021, above the peer average of Z%."). Charts should also be full width, not squished into half-width columns — on a 13" laptop those charts are illegible.

### 5. Consultant page is confusing to navigate
Page 2 has:
- A dropdown of 57 consultant names (many are just raw database strings like `"Callan Associates"`, `"Meketa Investment Group"`, etc. — no context on how big they are)
- A dual-axis line chart: client count + AUM over time
- A metric comparison chart: selected metric vs all-system average
- A raw dataframe of client systems for the latest year

The dataframe at the bottom is the raw pandas DataFrame with internal column names like `pub_id`, `pub_system_name`, `omega`, `ret_bgnassets` — completely unformatted for a user.

**What it should be:** The consultant dropdown should show AUM or client count next to each name so users can orient. The client table should have human-readable column names and percentage formatting. The metric comparison chart is actually good but its dropdown is populated with raw column names (`ActFundedRatio_GASB`) instead of nice labels.

**BUG:** The metric dropdown on Page 2 currently uses `METRIC_CHOICES` which is a list of raw column names — `format_func=lambda k: METRIC_LABELS[k]` is applied so labels show, but the dropdown default shows the internal key on initial render in some Streamlit versions.

### 6. State page defaults to 5 random states
Page 3 opens with the first 5 states alphabetically (`AK, AL, AR, AZ, CA`) selected. This is meaningless. The ranking chart shows all states regardless of selection, but the trend chart only shows selected states — so the default produces a trend chart for Alaska, Alabama, Arkansas, Arizona, California, which tells no story.

**What it should be:** Default to all states for the ranking chart. Default to the top 5 by AUM (CA, NY, TX, IL, FL) for the trend chart. Or simplify: one selector mode at a time — either "rank all states" OR "compare specific states."

### 7. Colors and typography technically work but feel inconsistent
Current palette:
- Background: `#0C0E12` (near black)
- Amber: `#C68B20` (primary accent)
- Text: `#D6DCE8` (light grey)
- Surface: `#131720`
- Charts use: amber, `#4A8DF5` (blue), `#3DAD6E` (green), `#E05252` (red)

Fonts:
- Headers: Playfair Display (serif)
- Data/labels: IBM Plex Mono (monospace)
- Body: IBM Plex Sans

The typography intent is Bloomberg-meets-editorial. The execution is that serif headers (Playfair Display) look slightly out of place next to monospace data, and the overall feel is "a developer tried to make it look like a financial terminal." It doesn't look unprofessional — it just doesn't look intentional.

---

## What Should Stay

- **Dark theme** — appropriate for a data-heavy research tool
- **The Plotly charts** — they are correct and comprehensive, just need better sizing and annotation
- **The Methodology page** — well-written, comprehensive, should stay
- **The amber accent** — distinctive, works well for highlights
- **The monospace data labels** — appropriate for financial data
- **Download CSV buttons** — researchers want the data

---

## Design Goals for the Redesign

1. **Show data on landing.** Replace nav cards with a live chart (e.g. the aggregate omega time series 2001–2021 for all systems) + 3 stat callouts.

2. **Fix the system selector.** Use Streamlit's native search in `st.selectbox` (it exists — just set `options` properly and let Streamlit handle it). Or add a state pre-filter: pick state → pick system.

3. **Reduce cognitive load per page.** Max 3 KPI tiles. One clear chart per section. A 1-line auto-generated insight above each chart.

4. **Full-width charts.** No 2×2 grid on detail pages. Stack charts vertically, full width.

5. **Humanize the consultant and state pages.** Friendly column names in tables, formatted numbers, context-setting labels.

6. **Fix the state page defaults.** Top 5 by AUM as default comparison set.

7. **Consistent typographic hierarchy.** Either lean fully into the monospace terminal aesthetic (drop Playfair Display, use IBM Plex Mono everywhere) OR lean fully into editorial (keep Playfair Display for all headers, use IBM Plex Sans for body, use IBM Plex Mono only for data values).

---

## Streamlit Constraints (Don't Break These)

- All layout must use `st.columns()`, `st.sidebar`, `st.tabs()`, `st.container()`
- Custom HTML/CSS injected via `st.markdown(html, unsafe_allow_html=True)` in a single `<style>` block
- No JavaScript
- All Plotly figures are emitted via `st.plotly_chart(fig, use_container_width=True)`
- Streamlit widget styling (selectbox, slider, button) is limited — can style with CSS class selectors but Streamlit regenerates DOM on every interaction
- The app is multi-page: each `.py` file in `pages/` is its own page with full page re-render on widget interaction
- Caching is via `@st.cache_data` — don't move data loading out of Python

---

## File Map

```
dashboard/lib/ui.py         ← All CSS and shared HTML components (kpi_grid, page_header, etc.)
dashboard/lib/charts.py     ← All Plotly chart builders + theme tokens
streamlit_app.py            ← Landing page
pages/1_System_or_Pension.py
pages/2_Consultant.py
pages/3_State_or_Region.py
pages/4_Methodology.py
.streamlit/config.toml      ← Streamlit theme config (colors, font)
```

The redesign should primarily touch:
1. `dashboard/lib/ui.py` — CSS overhaul + new component functions
2. `dashboard/lib/charts.py` — Plotly layout tweaks
3. `streamlit_app.py` — New landing page with live chart
4. `pages/1_System_or_Pension.py` — Better selector, fewer tiles, full-width charts
5. `pages/2_Consultant.py` — Formatted table, better defaults
6. `pages/3_State_or_Region.py` — Better state defaults, cleaner selector logic
