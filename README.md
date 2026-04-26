# Research Project: U.S. Public Pension Fund Data Pipeline, Replication, and Dashboard

A Python implementation of the [Public Plans Database (PPD)](https://publicplansdata.org/public-plans-database/download-full-data-set/) cleaning pipeline (Center for Retirement Research, Boston College), a full replication of key tables and figures from **Begenau, Liang & Siriwardane (2026, *Review of Financial Studies*)** *"The Rise of Alternatives,"* and an interactive web dashboard (`./run.sh` → http://localhost:8000) that surfaces the cleaned panel for exploratory research.

## Quick Start

```sh
# 1. Clone and create a venv
git clone <this repo>
cd research-project
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt

# 2. Run the web dashboard (bakes data → serves on :8000)
./run.sh

# 3. Optional: run the pipeline notebooks
.venv/bin/jupyter lab notebooks/
```

Open <http://localhost:8000> for the dashboard. To rebuild the parquet outputs, execute `notebooks/01_create_mapping_table.ipynb` through `notebooks/05_clean_ppd.ipynb` in order — outputs land in `output_python/`.

## Credits & Attribution

This work builds directly on the Stata codebase and research design from the papers below. **Please cite them if you use this repository.**

```bibtex
@article{BLS2026,
  author  = {Begenau, Juliane and Liang, Pauline and Siriwardane, Emil N.},
  journal = {Review of Financial Studies},
  title   = {The Rise of Alternatives},
  year    = {2026}
}
```

```bibtex
@article{ABS2025,
  title   = {Choosing Pension Fund Investment Consultants},
  author  = {Andonov, Aleksandar and Bonetti, Matteo and Stefanescu, Irina},
  year    = {2025},
  journal = {SSRN}
}
```

The original Stata pipeline ([ppd-data](https://github.com/AnshArora04/ppd-data)) was authored by the teams behind the papers above. This repository re-implements that pipeline in Python, replicates Table 1 / Figure 2 / Figure 3 / Figure 6 / Table 7 of Begenau et al. (2026), and ships an interactive dashboard built on the resulting parquet.

---

## What's in this repository

Three coordinated pieces share a single source-of-truth parquet:

| Piece | Where | What it does |
|---|---|---|
| **Data pipeline** | `notebooks/01_…` → `05_…` | Stata-faithful PPD cleaning (mapping → import → allocations → performance → filters) |
| **Replication & exploration** | `notebooks/replicate_paper_figures_tables.ipynb`, `notebooks/Begenau replication work/`, `notebooks/exploration/` | Reproduce the paper's headline results; explore the panel from data-landscape, geographic, time-series, and research-angle perspectives |
| **Web dashboard** | `web/` (current), `legacy/` (Streamlit backup) | FastAPI + verbatim React/HTML build serving real PPD numbers via `web/bake_data.py` |

All three depend on the same shared data layer in `dashboard/lib/` (`data_loader.py`, `aggregations.py`, `config.py`).

---

## 1. The Data Pipeline

Five sequential notebooks mirror the original Stata pipeline. Each is verified to match Stata outputs at `rtol=1e-4` (with intentional Internet Appendix corrections).

| Notebook | Purpose | Output (CSV + DTA + Parquet) |
|---|---|---|
| `01_create_mapping_table.ipynb` | Plan-to-system mapping with annual expansion across mergers/name-changes | `mapping_table_fy_final` |
| `02_create_ppd_dta.ipynb` | Imports PPD CSV; merges Census regions + mapping table | `ppd_plan_level_raw` |
| `03_adjust_allocations.ipynb` | ~6,700 CAFR-sourced corrections; asset-class harmonization; IA A.1.3 fixes (Idaho PERSI, NY SLRS) | `ppd_plan_clean_allocations` |
| `04_adjust_performance.ipynb` | Computes `ret_bgnassets` (net return); fiscal-year edge cases | `ppd_performance` |
| `05_clean_ppd.ipynb` | Sequential sample filters; merges consultants, zipcodes, performance | **`ppd_plan_level_clean`** (4,000 rows × 291 cols) |

`output_python/ppd_plan_level_clean.parquet` (2.2 MB) is the canonical input for the dashboard and all downstream replication.

### Pipeline audit

Two notebooks programmatically verify the pipeline:
- `notebooks/audit_steps_1_4.ipynb` — verifies steps 1–4 file shapes, column-by-column equality vs Stata
- `notebooks/audit_all_steps.ipynb` — full end-to-end audit through the cleaned final file

---

## 2. Replication of Paper Results

### Headline replication: Table 1 + Figure 2

Source: `notebooks/Begenau replication work/replicate_table1_figure2.ipynb`

- **3,128 system-year observations** — exact match to the paper's Internet Appendix target
- **Figure 2: 12/12 metrics within ±2pp** of paper anchor values (total gap: 1.8pp)
- **Table 1 Panel A** funding ratio, assumed return, and percent retired all match the paper exactly

Table 1 Panel A (replication vs. paper):

| | 2001–2005 | 2006–2010 | 2011–2015 | 2016–2021 |
|---|---|---|---|---|
| Members (millions) | 20.6 | 23.5 | 25.0 | 27.0 |
| Percent Retired (%) | 29 | 32 | 36 | 38 |
| AUM ($ trillions) | 2.02 | 2.60 | 3.10 | 4.06 |
| GASB 25 Funding (%) | 94 | 85 | 76 | 76 |
| Assumed Return (%) | 8.0 | 7.9 | 7.6 | 7.2 |
| Annual Return (%) | 4.8 | 5.2 | 10.6 | 11.0 |

Figure 2 anchor values:

| Year | Alternatives | Public Equities | Fixed Income | Omega (ω) |
|---|---|---|---|---|
| 2001 | 9.3% | 59.4% | 31.4% | 13.5% |
| 2021 | 30.1% | 46.1% | 23.8% | 39.5% |

Outputs: `notebooks/Begenau replication work/{figure_2.png, figure_2_paper_faithful.png, table_1.csv}`

### Extended replication: Figures 1, 3, 6, A5 + Table 7 + Transitions

Source: `notebooks/replicate_paper_figures_tables.ipynb` (31 cells)

Outputs in `output_python/replication_outputs/`:
- `figure_1a.png` + `figure_1a_data.csv` — total US public-pension AUM growth
- `figure_3a.png`, `figure_3b.png`, `figure_3c.png` — cross-sectional ω dispersion (median, p10, p90)
- `figure_6a.png`, `figure_6b.png` — alternatives sub-allocation breakdown
- `figure_a5.png` — additional Internet Appendix figure
- `table_7.csv` — risk-seeking motive regressions
- `table_a1a_transition_risky.csv`, `table_a1b_transition_omega.csv` — Markov transition matrices

### Audit (Section 8 of the main replication notebook)

7 programmatic audit cells verify:
- All 5 pipeline output files exist and have expected shapes
- Python outputs match Stata column-by-column (`rtol=1e-4`)
- Variable definitions match the paper and Internet Appendix
- IA A.1.3 special plan fixes correctly applied (Idaho PERSI, NY SLRS)
- All 7 sample filters match the Stata `clean_ppd.do` logic
- Performance pipeline (`ret_bgnassets`) matches Stata exactly (3,780 rows)
- Final 3,128 system-year count and 12/12 Figure 2 accuracy

---

## 3. Exploration Notebooks

Four notebooks under `notebooks/exploration/` characterize the panel from different angles — useful as research-question scaffolding:

| Notebook | Lens |
|---|---|
| `01_data_landscape.ipynb` | Coverage, missingness, plan/system structure, distributions |
| `02_geographic_patterns.ipynb` | State/region rankings, regional allocation patterns, size effects |
| `03_time_series_deep_dive.ipynb` | Allocation evolution, dispersion, hurdle rates, sub-alternatives |
| `04_research_angles.ipynb` | Funding pressure, return chasing, rebalancing, consultant effects, convergence |

26 plots emit to `output_python/exploration/` (e.g., `correlation_matrix.png`, `geo_state_omega_ranking.png`, `ts_allocation_stacked.png`, `ra_consultant_effects.png`).

---

## 4. Web Dashboard (`web/`)

Interactive dashboard for exploring the cleaned panel. Built as a verbatim React/HTML prototype (delivered by the Claude design tool), wired to **real PPD data** baked from `output_python/ppd_plan_level_clean.parquet`.

### Run

```sh
./run.sh                  # bakes data → ppd-data.js, then serves on :8000
PORT=8080 ./run.sh        # custom port
SKIP_BAKE=1 ./run.sh      # skip bake on restart (useful for UI-only iteration)
HOST=0.0.0.0 ./run.sh     # expose to LAN
```

### Pages

- **Overview** — AUM-weighted aggregate ω chart (Figure 2c shape), three sub-allocation sparklines (Real Assets, PE, HF), KPI strip (sample AUM, system-years, ω growth, # consultants in panel).
- **System Deep Dive** — Search-as-you-type selector grouped by state across all 174 systems; defaults to CalPERS (largest by AUM). Per-fund: stacked allocation area, ω vs. peer line, funded ratio + ARR composed chart, annual returns bar chart with auto-generated insights.
- **Consultant Analysis** — Ranked dropdown of advisors by client AUM. Metric toggle (ω / funded ratio / net return / assumed return) vs. all-system average. Client distribution (omega bucket histogram) + per-client table with download.
- **State & Regional** — Mode toggle: rank all 51 states by latest-year ω, or compare a hand-picked set over time (defaults to top 5 by AUM: CA, NY, TX, OH, FL). Compare mode also includes scatter (ω vs. funded ratio).
- **Methodology** — Numbered reference doc; every numeric claim (system count, ω range, ARR endpoints, top-4 consultants, total AUM) is interpolated from the bake — no hardcoded values.

### Architecture

```
output_python/ppd_plan_level_clean.parquet
        │
        │   load_plan_clean()  →  cached_system_year() / _consultant_year() / _state_year()
        ▼
web/bake_data.py     ─emits→     web/static/ppd-data.js   (window.PPDData)
                                          │
                                          │  loaded by  <script src="/static/ppd-data.js">
                                          ▼
web/server.py (FastAPI)  ─serves→  web/static/index.html + .jsx  (React + Recharts via CDN)
```

- `web/bake_data.py` reuses the shared data layer (`dashboard/lib/`) and writes a single ~2 MB JSON-in-JS file. The React app reads it from `window.PPDData` exactly like the original prototype's mock did — but with real values.
- `web/server.py` is a ~50-line FastAPI app with a `NoCacheStaticFiles` mount that disables browser caching (Babel transpiles JSX in-browser and would otherwise serve stale UI after edits).
- Determinism: re-running `./run.sh` produces a byte-identical `ppd-data.js`. End-to-end correctness: 9,376/9,376 system-year × field cross-checks vs. parquet pass exactly; `ANALYTIC_OBS = 3,128` matches the paper's reported sample size to the row.

### Key facts the dashboard exposes (live from real data)

| | Value |
|---|---|
| Systems in the panel | 174 (PPD raw; paper trims to 159 via filters 5+7) |
| Consultants in panel | 66 (21 active in latest year by client AUM) |
| Sample AUM (FY 2021) | $5,097.6B |
| ω 2001 → 2021 (AUM-weighted) | 13.0% → 38.8% |
| ω panel range | 0.0% – 82.4% |
| Sub-allocations 2001 → 2021 | RE 4.0%→9.8%, PE 4.1%→10.2%, HF 0.3%→5.8% |
| Assumed return (AUM-weighted) | 8.0% (2001) → 7.0% (2021) |
| Top-4 consultants by client AUM | Aon Hewitt, Meketa, Callan, Wilshire |

---

## 5. Legacy Streamlit Dashboard (`legacy/`)

The previous Streamlit-based dashboard, preserved as a runnable backup. Run with:

```sh
cd legacy
../.venv/bin/streamlit run streamlit_app.py --server.port 8501
```

See [`legacy/README.md`](legacy/README.md) for details (and a known AUM-display unit bug that the new `web/` build fixes). The original design intent that drove the rewrite is preserved verbatim in [`DESIGN_BRIEF.md`](DESIGN_BRIEF.md).

---

## Repository Structure

```
research-project/
├── notebooks/
│   ├── 01_create_mapping_table.ipynb     # Pipeline step 1: plan→system mapping
│   ├── 02_create_ppd_dta.ipynb           # Step 2: import + merge PPD
│   ├── 03_adjust_allocations.ipynb       # Step 3: CAFR corrections + IA fixes
│   ├── 04_adjust_performance.ipynb       # Step 4: ret_bgnassets
│   ├── 05_clean_ppd.ipynb                # Step 5: filters + final merge
│   ├── audit_steps_1_4.ipynb             # Pipeline audit (steps 1–4)
│   ├── audit_all_steps.ipynb             # Pipeline audit (all 5 steps)
│   ├── replicate_paper_figures_tables.ipynb   # Figures 1, 3, 6, A5 + Table 7 + transitions
│   ├── Begenau replication work/
│   │   ├── replicate_table1_figure2.ipynb # Headline replication (3,128 obs)
│   │   ├── figure_2.png
│   │   ├── figure_2_paper_faithful.png
│   │   └── table_1.csv
│   └── exploration/                       # Open-ended panel exploration
│       ├── 01_data_landscape.ipynb
│       ├── 02_geographic_patterns.ipynb
│       ├── 03_time_series_deep_dive.ipynb
│       └── 04_research_angles.ipynb
│
├── dashboard/lib/                          # Shared Python data layer
│   ├── data_loader.py                    # load_plan_clean, get_systems, get_consultants…
│   ├── aggregations.py                   # cached_system/consultant/state_year
│   ├── config.py                         # data root + file path resolution
│   ├── charts.py                         # Plotly chart builders (Streamlit-only)
│   └── ui.py                             # Streamlit theme + CSS (Streamlit-only)
│
├── web/                                    # Current dashboard (React + FastAPI)
│   ├── server.py                         # FastAPI app + no-cache static mount
│   ├── bake_data.py                      # Parquet → ppd-data.js
│   └── static/
│       ├── index.html                    # Loads React + Recharts via CDN
│       ├── ppd-data.js                   # AUTO-GENERATED, real PPD bundle
│       ├── ppd-shared.jsx                # KPITile, ChartShell, InsightBox…
│       ├── ppd-landing.jsx               # Overview page
│       ├── ppd-system.jsx                # System Deep Dive page
│       ├── ppd-consultant.jsx            # Consultant Analysis page
│       ├── ppd-state.jsx                 # State & Regional page
│       └── ppd-app.jsx                   # App shell + Methodology page
│
├── legacy/                                 # Streamlit backup
│   ├── streamlit_app.py
│   ├── pages/
│   ├── .streamlit/config.toml
│   └── README.md
│
├── output_python/                          # Pipeline outputs (CSV + DTA + Parquet)
│   ├── mapping_table_fy_final.{csv,dta,parquet}
│   ├── ppd_plan_level_raw.{csv,dta,parquet}
│   ├── ppd_plan_clean_allocations.{csv,dta,parquet}
│   ├── ppd_performance.{csv,dta,parquet}
│   ├── ppd_plan_level_clean.{csv,dta,parquet}    # ← canonical cleaned dataset
│   ├── exploration/                              # 26 plots from notebooks/exploration/
│   └── replication_outputs/                      # Figures 1/3/6/A5 + Table 7 + transitions
│
├── raw/                                    # Source data
│   ├── ppd-data-2023-07-28.csv           # PPD release used by the paper (Begenau et al. 2026)
│   ├── ppd-data-2024-12-08.csv           # Newer PPD release (not used by current pipeline)
│   ├── general_consultants_final.dta     # Hand-collected consultant assignments
│   ├── mapping_table_final.xlsx          # Hand-collected plan→system mapping
│   ├── us_census_bureau_regions_and_divisions.csv
│   ├── zipcodes.csv
│   └── allocation_adjustments/           # 12 CAFR PDFs sourced for adjustments
│
├── BegenauEtAl2026RFS.pdf                 # Published paper
├── BegenauEtAl2026_machine_readable.md    # Machine-readable paper summary
├── BegenauEtAl2026_InternetAppendix_machine_readable.md
├── DESIGN_BRIEF.md                         # Original design brief (with status header)
├── LICENSE                                 # MIT
├── README.md                               # This file
├── requirements.txt                        # Pinned floors for all deps
└── run.sh                                  # Bake + serve web dashboard
```

---

## Data

### Source

The pipeline uses the **2023-07-28 release** of the PPD (`raw/ppd-data-2023-07-28.csv`), which covers FY 2001–2022. This is the release used by Begenau et al. (2026) per Internet Appendix A.1. The newer 2024-12-08 release is included for reference but is not consumed by the current pipeline.

### Coverage

- **Unit of observation:** pension plan (`ppd_id`) × fiscal year (`fy`)
- **Aggregation:** plans are aggregated to investment system (`pub_id`) before analysis, because many plans pool assets before investing (e.g., the Retirement System of Alabama manages the Teachers, Employees, and Judicial plans jointly)
- **Sample window:** FY 2001–2021 (FY 2022 excluded — sparse coverage and out of paper's window)
- **Final cleaned dataset:** `output_python/ppd_plan_level_clean` (4,000 rows × 291 columns)
- **Analytic system-year observations** (rows with non-zero target allocations): **3,128** — exact match to the paper

### Auxiliary inputs

- `general_consultants_final.dta` — hand-collected and FOIA-cross-checked consultant assignments (>98% of system-years covered)
- `mapping_table_final.xlsx` — hand-collected plan-to-system mapping with mergers and name changes
- `us_census_bureau_regions_and_divisions.csv` — for state → region/division joins
- `allocation_adjustments/` — 12 CAFR PDFs used to source ~6,700 hand-coded allocation corrections (e.g., Chicago Police, Montana, North Dakota RIO, Philadelphia)

---

## Key Corrections Applied

### 1. Asset Allocation Adjustments (Step 3)

Following the original Stata code and Internet Appendix, ~6,700 CAFR-sourced `replace` statements correct mismatches between PPD-recorded values and underlying CAFRs. Four categories:

1. **Category definition** — e.g., separating Alabama ERS 2017 fixed income target from bundled alternatives
2. **CAFR mismatches** — e.g., correcting Minnesota TRA 2003 equity target from 0.627 → 0.600
3. **Missing data** — e.g., filling Michigan MERS 2004 missing targets from CAFR
4. **Leverage** — e.g., San Diego CERA 2012 cash allocation corrected to −0.25

### 2. Internet Appendix A.1.3 Special Plan Fixes

Two systems required additional correction beyond the original Stata pipeline:

- **Idaho PERSI (`ppd_id=31`):** Private equity is included in the general "equity target." All 10 target allocation columns are set equal to actual allocations for all available years (21 rows in cleaned data) so that target PE exposure is correctly recorded.
- **NY SLRS (`ppd_id=83`, FY 2001–2003):** Equity target was incorrectly set to 0.70 in early years. All 10 target columns are set equal to actual allocations for FY 2001–2003 only.

Observations where target shares were replaced by actuals are flagged via `is_target_replaced`; the inverse case via `is_actual_replaced`.

### 3. Performance Measure: `ret_bgnassets`, not `InvestmentReturn_1yr`

Approximately **25% of `InvestmentReturn_1yr`** observations in the PPD reflect *gross-of-fee* returns rather than net (confirmed via CAFR cross-checks for Contra Costa County ERS, Chicago Public Teachers, Louisiana TRS, MassPRIM, Ohio P&F, and others).

`ret_bgnassets` is computed from each system's CAFR as:

$$r_t = \frac{\text{Net Investment Income}_t}{\text{Total Assets}_{t-1}}$$

Net investment income includes capital gains, dividends, interest, investment expenses, and securities-lending income. This measure is always net of fees and is the return variable used throughout Begenau et al. (2026).

### 4. Sample Filters (Step 5)

Seven sequential filters reduce the raw PPD observations to the analytic sample:

1. Restrict to FY 2001–2021
2. Drop observations where *both* target and actual weight sums differ from 1 by more than 5pp
3. Drop plans with no system-level (`pub_id`) assignment
4. Aggregate plans to the system level (AUM-weighted)
5. Require at least one non-missing target allocation in the main asset classes
6. Drop system-years with no AUM data
7. Restrict to systems with at least 3 years of data

Final sample: **3,128 system-year observations** with non-zero target allocations.

---

## Background: The PPD Dataset

The PPD contains asset allocation, performance, and plan structure data for U.S. public defined-benefit pension funds. The underlying source is each fund's Comprehensive Annual Financial Report (CAFR).

### Sample Period

The pipeline targets the **2023-07-28 PPD release**, covering FY 2001–2022. The PPD is sparse before FY 2001, so analysis focuses on **FY 2001–2021** (the 2022 fiscal year is excluded to match the paper's sample).

### Performance Measure Details

The `ret_bgnassets` variable is the recommended performance measure (see "Key Corrections Applied" above). Fiscal-year-end timing also matters — `pfmonth` gives the system-level reporting month. ~65% of plans report at June year-end, ~24% at December, and the remainder at March, April, August, or September. In 2008, June-end plans averaged **−4.5%** while December-end plans averaged **−24.3%**. When comparing returns across systems, control for `pfmonth`.

### General Consultants

The pipeline merges hand-collected consultant data to supplement and cross-check PPD consultant records. Mergers and name changes are standardized: post-merger, the new firm name is used for all subsequent years; pure name changes are backdated to the full sample. The variable `consultant_final` holds the standardized name; `consultant_id_final` is a unique integer identifier. Coverage exceeds 98% of system-year observations.

### Asset Allocation Flags

A flag `trgt_zero_actl_nonzero` marks plan-year observations where any asset class (excluding Cash and Other) has a zero target allocation but a nonzero actual allocation. This identifies cases like Idaho PERSI where private equity is embedded in the general equity target. Researchers can decide how to handle these for their specific use case.

---

## Dependencies

Pinned floors in `requirements.txt`:

| Package | Floor | Used by |
|---|---|---|
| pandas | 2.0.0 | pipeline + dashboards |
| numpy | 1.24.0 | pipeline + dashboards |
| pyarrow | 14.0.0 | parquet I/O |
| fastapi | 0.115.0 | `web/server.py` |
| uvicorn[standard] | 0.30.0 | `web/server.py` (ASGI server) |
| streamlit | 1.35.0 | `legacy/` only |
| plotly | 5.18.0 | `legacy/` only |

Notebook execution additionally requires `jupyter` and `matplotlib` (install separately if needed).

The web dashboard loads React 18, Recharts 2.12, Babel-standalone, and prop-types from CDNs at runtime — no `npm install` is required.

---

## License

MIT — see [LICENSE](LICENSE). Copyright © 2025 Aleksandar Andonov, Juliane Begenau, Pauline Liang, and Emil Siriwardane.
