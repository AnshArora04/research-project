# Research Project: U.S. Public Pension Fund Data Pipeline & Replication

This repository builds a Python-based data pipeline for the [Public Plans Data](https://publicplansdata.org/public-plans-database/download-full-data-set/) (PPD) from the Center for Retirement Research at Boston College, replicates key results from Begenau, Liang, and Siriwardane (2026) *"The Rise of Alternatives,"* and ships an interactive web dashboard (`./run.sh` → http://localhost:8000) that surfaces the cleaned panel for ad-hoc exploration.

## Credits & Attribution

This work builds directly on the Stata codebase and research design from the following papers. **Please cite them if you use this repository.**

```
@article{BLS2026,
  author  = {Begenau, Juliane and Liang, Pauline and Siriwardane, Emil N},
  journal = {Review of Financial Studies},
  title   = {The Rise of Alternatives},
  year    = {2026}
}
```

```
@article{ABS2025,
  title   = {Choosing Pension Fund Investment Consultants},
  author  = {Andonov, Aleksandar and Bonetti, Matteo and Stefanescu, Irina},
  year    = {2025},
  journal = {SSRN}
}
```

The original Stata pipeline (`legacy/` in [ppd-data](https://github.com/AnshArora04/ppd-data)) was authored by the teams behind the papers above. This repository re-implements that pipeline in Python and adds a full replication of Table 1 and Figure 2 from Begenau et al. (2026).

---

## What This Repository Does

### 1. Python Pipeline (Steps 1–5)

Five notebooks in `notebooks/` mirror the original Stata pipeline end-to-end. Each notebook is verified to produce output that matches the Stata results exactly (except for intentional Internet Appendix corrections, see Step 3).

| Notebook | Description | Output |
|---|---|---|
| `01_create_mapping_table.ipynb` | Builds plan-to-system mapping with time-series coverage via annual expansion | `mapping_table_fy_final` |
| `02_create_ppd_dta.ipynb` | Imports PPD CSV, merges Census regions and mapping table | `ppd_plan_level_raw` |
| `03_adjust_allocations.ipynb` | CAFR-based allocation corrections; asset class harmonization; IA A.1.3 fixes | `ppd_plan_clean_allocations` |
| `04_adjust_performance.ipynb` | Computes `ret_bgnassets` (net return); handles fiscal year edge cases | `ppd_performance` |
| `05_clean_ppd.ipynb` | Applies sequential sample filters; merges consultants, zipcodes, performance | `ppd_plan_level_clean` |

All pipeline outputs are saved to `output_python/` as CSV, Stata `.dta`, and Parquet.

### 2. Replication: Table 1 & Figure 2

`notebooks/Begenau replication work/replicate_table1_figure2.ipynb` replicates Table 1 (summary statistics) and Figure 2 (asset allocation trends) from Begenau et al. (2026).

**Key results:**

- **3,128 system-year observations** — exact match to the paper's Internet Appendix target
- **Figure 2: 12/12 metrics within ±2pp** of paper anchor values (total gap: 1.8pp)
- **Table 1 Panel A** funding ratio, assumed return, and percent retired all match the paper exactly

**Table 1 Panel A (replication vs. paper):**

| | 2001–2005 | 2006–2010 | 2011–2015 | 2016–2021 |
|---|---|---|---|---|
| Members (millions) | 20.6 | 23.5 | 25.0 | 27.0 |
| Percent Retired (%) | 29 | 32 | 36 | 38 |
| AUM ($ trillions) | 2.02 | 2.60 | 3.10 | 4.06 |
| GASB 25 Funding (%) | 94 | 85 | 76 | 76 |
| Assumed Return (%) | 8.0 | 7.9 | 7.6 | 7.2 |
| Annual Return (%) | 4.8 | 5.2 | 10.6 | 11.0 |

**Figure 2 anchor values:**

| Year | Alternatives | Public Equities | Fixed Income | Omega |
|---|---|---|---|---|
| 2001 | 9.3% | 59.4% | 31.4% | 13.5% |
| 2021 | 30.1% | 46.1% | 23.8% | 39.5% |

### 3. Full Pipeline Audit (Section 8)

The replication notebook includes a Section 8 with 7 programmatic audit cells verifying:
- All 5 pipeline output files exist and have expected shapes
- Python outputs match Stata outputs column-by-column (at rtol=1e-4)
- All variable definitions match the paper and Internet Appendix
- Internet Appendix A.1.3 special plan fixes are correctly applied
- All 7 sample filters match the Stata `clean_ppd.do` logic
- Performance pipeline (`ret_bgnassets`) matches Stata exactly (3,780 rows)
- Final 3,128 system-year count and 12/12 Figure 2 accuracy confirmed

---

## Data

The pipeline uses the **2023-07-28 release** of the PPD (`raw/ppd-data-2023-07-28.csv`), which covers FY2001–2022. This is the release used by Begenau et al. (2026) per Internet Appendix A.1.

The final cleaned dataset is `output_python/ppd_plan_level_clean.csv` (4,000 rows × 291 columns, FY2001–2021).

---

## Key Corrections Applied

### 1. Asset Allocation Adjustments (Step 3)

Following the original Stata code and the paper's Internet Appendix, ~6,700 CAFR-sourced `replace` statements correct mismatches between PPD recorded values and underlying CAFRs. Four categories of adjustment:

1. **Category definition** — e.g., separating Alabama ERS 2017 fixed income target from bundled alternatives
2. **CAFR mismatches** — e.g., correcting Minnesota TRA 2003 equity target from 0.627 → 0.600
3. **Missing data** — e.g., filling Michigan MERS 2004 missing targets from CAFR
4. **Leverage** — e.g., San Diego CERA 2012 cash allocation corrected to −0.25

### 2. Internet Appendix A.1.3 Special Plan Fixes

Two systems required additional correction beyond the original Stata pipeline:

- **Idaho PERSI (ppd_id=31):** Private equity is included in the general "equity target." All 10 target allocation columns are set equal to actual allocations for all available years (21 rows in cleaned data), so that target PE exposure is correctly recorded rather than zero.
- **NY SLRS (ppd_id=83, FY2001–2003):** Equity target was incorrectly set to 0.70 in early years. All 10 target columns are set equal to actual allocations for FY2001–2003 only.

### 3. Performance Measure

The `InvestmentReturn_1yr` variable in the PPD does not distinguish between gross and net returns (~25% of observations are gross). The alternative `ret_bgnassets` variable (net investment income ÷ beginning-of-year assets) is used throughout, as it always reflects net performance. See the section below for full detail.

---

## Web Dashboard (`web/`)

An interactive dashboard for exploring the cleaned panel. Built as a verbatim React/HTML prototype delivered by the Claude design tool, then wired to **real PPD data** baked from `output_python/ppd_plan_level_clean.parquet`.

### Quick start

```sh
./run.sh                  # bakes data → ppd-data.js, then serves on :8000
PORT=8080 ./run.sh        # custom port
SKIP_BAKE=1 ./run.sh      # skip bake on restart
```

Open <http://localhost:8000>.

### What it shows (all from real data, no synthetic values)

- **Overview** — AUM-weighted aggregate omega chart, sub-allocation sparklines (Real Assets, PE, HF), KPI strip (sample AUM, system-years, omega growth, # consultants).
- **System Deep Dive** — Search-as-you-type selector grouped by state across all 174 systems; per-fund allocation, omega-vs-peer, funded ratio + ARR, and annual returns.
- **Consultant Analysis** — Ranked dropdown of advisors by client AUM; metric comparison vs. all-system average; client distribution and per-client table.
- **State & Regional** — Mode toggle: rank all 51 states by latest-year omega, or compare a hand-picked set over time.
- **Methodology** — Numbered reference doc with definitions and provenance — every figure (system count, AUM total, ω range, ARR endpoints, top-4 consultants) is interpolated from the bake.

### How it works

```
output_python/ppd_plan_level_clean.parquet
        │
        │   load_plan_clean() / cached_system_year() / cached_consultant_year() / cached_state_year()
        ▼
web/bake_data.py     ─emits→     web/static/ppd-data.js   (window.PPDData)
                                          │
                                          │  loaded by  <script src="/static/ppd-data.js">
                                          ▼
web/server.py (FastAPI)  ─serves→  web/static/index.html + .jsx  (React + Recharts via CDN)
```

- `web/bake_data.py` reuses the existing data layer (`dashboard/lib/`) and writes a single 2 MB JSON-in-JS file — the React app reads it from `window.PPDData` exactly like the original prototype's mock did.
- `web/server.py` is ~50 lines: FastAPI + a `NoCacheStaticFiles` mount that disables browser caching (Babel transpiles JSX in-browser and would otherwise cache aggressively).
- Numbers verified against parquet: 9,376/9,376 system-year × field cross-checks pass exactly; `ANALYTIC_OBS = 3,128` matches the paper's reported sample size to the row.

### Files

```
web/
├── bake_data.py        # parquet → ppd-data.js (run at server start)
├── server.py           # FastAPI app, no-cache static serve
├── __init__.py
└── static/
    ├── index.html      # entry HTML (loads React + Recharts via CDN)
    ├── ppd-data.js     # AUTO-GENERATED real-data bundle
    ├── ppd-shared.jsx  # shared components (KPITile, ChartShell, …)
    ├── ppd-landing.jsx
    ├── ppd-system.jsx
    ├── ppd-consultant.jsx
    ├── ppd-state.jsx
    └── ppd-app.jsx     # app shell + Methodology page
```

The original Streamlit dashboard is preserved under `legacy/` (run with `cd legacy && ../.venv/bin/streamlit run streamlit_app.py`).

---

## Repository Structure

```
research-project/
├── notebooks/                              # Pipeline + replication notebooks
│   ├── 01_create_mapping_table.ipynb     # Step 1: Plan-to-system mapping
│   ├── 02_create_ppd_dta.ipynb           # Step 2: Import + merge PPD
│   ├── 03_adjust_allocations.ipynb       # Step 3: Allocation corrections + IA fixes
│   ├── 04_adjust_performance.ipynb       # Step 4: Net return computation
│   ├── 05_clean_ppd.ipynb                # Step 5: Sample filters + final merge
│   ├── audit_all_steps.ipynb             # Pipeline audit (Steps 1–5)
│   ├── audit_steps_1_4.ipynb             # Pipeline audit (Steps 1–4)
│   └── Begenau replication work/
│       ├── replicate_table1_figure2.ipynb # Main replication notebook (Sections 1–8)
│       ├── figure_2.png
│       ├── figure_2_paper_faithful.png
│       └── table_1.csv
├── dashboard/lib/                          # Shared Python data layer (used by web/ and legacy/)
│   ├── data_loader.py                    # load_plan_clean, get_systems, get_consultants…
│   ├── aggregations.py                   # cached_system_year, _consultant_year, _state_year
│   ├── config.py                         # data root + file path resolution
│   ├── charts.py                         # Plotly chart builders (Streamlit-only)
│   └── ui.py                             # Streamlit theme + CSS (Streamlit-only)
├── web/                                    # React/HTML dashboard (current)
│   ├── server.py                         # FastAPI server + no-cache static mount
│   ├── bake_data.py                      # Parquet → ppd-data.js
│   └── static/                           # Verbatim design files + baked data bundle
├── legacy/                                 # Streamlit dashboard (kept as backup)
│   ├── streamlit_app.py
│   ├── pages/
│   ├── .streamlit/config.toml
│   └── README.md
├── output_python/                          # Pipeline outputs (CSV + DTA + Parquet)
├── raw/                                    # Source data
│   ├── ppd-data-2023-07-28.csv           # PPD 2023-07-28 release (used in paper)
│   ├── ppd-data-2024-12-08.csv           # PPD 2024-12-08 release (newer)
│   ├── general_consultants_final.dta
│   ├── mapping_table_final.xlsx
│   ├── us_census_bureau_regions_and_divisions.csv
│   ├── zipcodes.csv
│   └── allocation_adjustments/
├── DESIGN_BRIEF.md                         # Original design brief (historical)
├── BegenauEtAl2026RFS.pdf                  # Published paper
├── BegenauEtAl2026_machine_readable.md
├── BegenauEtAl2026_InternetAppendix_machine_readable.md
├── requirements.txt                        # pandas, fastapi, uvicorn, streamlit, plotly…
└── run.sh                                  # bake + serve web dashboard
```

---

## Background: The PPD Dataset

The PPD contains information on asset allocation, performance, and plan structure for U.S. public pension funds. It focuses on defined-benefit (DB) plans (as opposed to defined contribution). The underlying source is Comprehensive Annual Financial Reports (CAFRs) filed by each pension.

PPD data is indexed by pension plan (`ppd_id`) and fiscal year (`fy`). Since plans often pool assets before investing (e.g., the Retirement System of Alabama manages assets for the Teachers' Retirement System, the Employees' Retirement System, and the Judicial Retirement Fund), this repo aggregates individual plans to their larger *pension system* (`pub_id`), accounting for mergers during the sample.

### Sample Period

The pipeline targets the **2023-07-28 PPD release**, covering FY2001–2022. The PPD is sparse before FY2001, so the analysis focuses on **FY2001–2021** (the 2022 fiscal year is excluded to match the paper's sample).

### Performance Measure Details

The `ret_bgnassets` variable is the recommended performance measure. It estimates net return as:

$$r_t = \frac{\text{Net Investment Income}_t}{\text{Total Assets}_{t-1}}$$

Net investment income includes changes in asset value (capital gains), dividends, interest, investment expenses, and securities lending income and fees. An estimated ~25% of `InvestmentReturn_1yr` observations reflect gross-of-fee returns (confirmed via CAFR cross-checks for Contra Costa County ERS, Chicago Public Teachers, Louisiana TRS, MassPRIM, Ohio P&F, among others).

It is also important to account for differences in fiscal-year-end dates across plans when analyzing performance. The variable `pfmonth` gives the reporting month at the system level. Around 65% of plans report at June year-end; 24% at December. The remainder report in March, April, August, or September.

### General Consultants

The data includes general investment consultant information. The pipeline merges hand-collected consultant data to supplement and cross-check PPD consultant records. Mergers and name changes are standardized: post-merger, the new firm name is used for all subsequent years; name changes are backdated to the full sample. The variable `consultant_final` holds the consultant name; `consultant_id_final` is a unique identifier.

### Asset Allocation Adjustments

A flag `trgt_zero_actl_nonzero` marks plan-year observations where any asset class (excluding Cash and Other) has a zero target allocation but a nonzero actual allocation. This flag helps identify cases like Idaho PERSI where private equity is embedded in the general equity target. Researchers can decide how to handle such observations for their specific use case.
