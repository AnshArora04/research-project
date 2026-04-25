"""Methodology & Caveats page — static content, fully implemented in Step 1."""

from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).parent.parent / "dashboard"))
from lib.ui import ATTRIBUTION_HTML, apply_theme, page_header, rule

st.set_page_config(
    page_title="Methodology · PPD Explorer",
    page_icon="◈",
    layout="wide",
    initial_sidebar_state="collapsed",
)
apply_theme()

page_header(
    eyebrow="◈ Data Notes",
    title="Methodology &amp; Caveats",
    lead=(
        "Key design choices, known limitations, and variable definitions "
        "for the Public Plans Data pipeline underlying this dashboard."
    ),
)

# ── 1. Data source ────────────────────────────────────────────────────────────
st.markdown("### 1 &nbsp; Data Source")
st.markdown(
    """
The underlying data is the **Public Plans Database (PPD)** published by the
Center for Retirement Research at Boston College.
This dashboard uses the **2023-07-28 release** (the version used in Begenau et al. 2026),
which covers fiscal years 2001–2022.
The analytic sample is restricted to **FY 2001–2021** because FY 2022 data is sparse
and was not part of the published paper's sample.

- Unit of observation: pension plan (`ppd_id`) × fiscal year (`fy`)
- Plans are aggregated to their **investment system** (`pub_id`) before analysis,
  because many plans pool assets before investing (e.g., the Retirement System of
  Alabama manages assets for its Teachers, Employees, and Judicial plans jointly).
- The pipeline tracks system mergers and name changes year-by-year via a hand-collected
  mapping table.
""",
    unsafe_allow_html=True,
)

rule()

# ── 2. Performance measure ────────────────────────────────────────────────────
st.markdown("### 2 &nbsp; Performance Measure")
st.markdown(
    r"""
**Use `ret_bgnassets`, not `InvestmentReturn_1yr`.**

Approximately **25 % of `InvestmentReturn_1yr`** observations in the PPD reflect
*gross*-of-fee returns rather than net returns (confirmed via CAFR cross-checks
for Contra Costa County ERS, Chicago Public Teachers, Louisiana TRS, MassPRIM,
Ohio P&F, and others).

`ret_bgnassets` is computed from each system's comprehensive annual financial report
(CAFR) as:

$$r_t = \frac{\text{Net Investment Income}_t}{\text{Total Assets}_{t-1}}$$

Net investment income includes capital gains/losses, dividends, interest,
investment expenses, and securities lending income. This measure is always net of
fees and is the return variable used throughout Begenau et al. (2026).

**Fiscal-year-end timing** creates additional comparability issues for raw returns:
- ~65 % of plans report at June year-end
- ~24 % report at December year-end
- Remainder report at March, April, August, or September

The divergence is most visible in crisis years. In 2008, June-end plans averaged
**–4.5 %** while December-end plans averaged **–24.3 %** (markets had not recovered
by June). When comparing returns across systems, always control for the fiscal-year-end
month (`pfmonth`).
""",
    unsafe_allow_html=True,
)

rule()

# ── 3. Asset allocation definitions ──────────────────────────────────────────
st.markdown("### 3 &nbsp; Asset Allocation Definitions")
st.markdown(
    """
The PPD records asset allocations at a granular class level. The pipeline
harmonises these into five buckets consistent with the paper:

| Bucket | Components | Note |
|---|---|---|
| **Public Equity** | Total equity minus private equity | Includes REITs (reclassified from real estate) |
| **Fixed Income** | Bonds + cash | |
| **Private Equity** | Private equity / buyout / venture | Includes private credit (merged per paper) |
| **Real Estate** | Core RE + private-equity RE | **Excludes** REITs |
| **Other Alternatives** | Hedge funds + commodities + misc alts | |

The paper's key metric **omega** is:

$$\\omega = \\frac{\\text{Alternatives (target)}}{\\text{Alternatives (target)} + \\text{Public Equity (target)}}$$

where Alternatives = PE + Real Estate + Hedge Funds + Commodities + Misc Alts.

**~6,700 manual corrections** sourced from individual CAFRs are applied in Step 3
of the pipeline to resolve mismatches between PPD-recorded values and underlying
documents.
""",
    unsafe_allow_html=True,
)

rule()

# ── 4. Special plan fixes ─────────────────────────────────────────────────────
st.markdown("### 4 &nbsp; Special Plan Fixes (Internet Appendix A.1.3)")
st.markdown(
    """
Two systems required corrections beyond the standard CAFR adjustment pass:

**Idaho PERSI (`ppd_id = 31`)**
Private equity is embedded in the general "equity target" rather than reported
separately. For all available years (21 rows in the cleaned data), all 10 target
allocation columns are set equal to the corresponding *actual* allocations, so that
true PE exposure is captured rather than recorded as zero.

**New York State and Local Retirement System (`ppd_id = 83`, FY 2001–2003)**
Early-year equity targets were incorrectly set to 0.70 in the PPD.
All 10 target columns are set equal to actual allocations for FY 2001–2003 only.

Observations where target shares were replaced by actuals are flagged via the
`is_target_replaced` column. Observations where actual shares were replaced by
targets are flagged via `is_actual_replaced`.
""",
    unsafe_allow_html=True,
)

rule()

# ── 5. Sample filters ─────────────────────────────────────────────────────────
st.markdown("### 5 &nbsp; Sample Filters")
st.markdown(
    """
Seven sequential filters reduce the raw PPD observations to the analytic sample:

1. Restrict to FY 2001–2021.
2. Drop observations where *both* target and actual weight sums differ from 1 by
   more than 5 percentage points (|sum – 1| > 0.05).
3. Drop plans with no system-level (`pub_id`) assignment.
4. Aggregate plans to the system level (AUM-weighted).
5. Require at least one non-missing target allocation in the main asset classes.
6. Drop system-years with no AUM data.
7. Restrict to systems with at least 3 years of data.

The final cleaned sample contains **3,128 system-year observations** across
**~159 systems**.

Observations where weight sums require *one-sided* adjustment (target or actual
only) are corrected and retained, with the `is_target_replaced` or
`is_actual_replaced` flag set to 1.
""",
    unsafe_allow_html=True,
)

rule()

# ── 6. Consultant data ────────────────────────────────────────────────────────
st.markdown("### 6 &nbsp; Consultant Data")
st.markdown(
    """
General investment consultant assignments were hand-collected from CAFRs and
cross-checked against Freedom of Information Act (FOIA) responses.
Coverage is **>98 % of system-year observations**.

Naming conventions:
- Post-merger firms use the **post-merger name** for all subsequent years.
- Name changes (without substantive mergers) are **backdated** to the full sample.

The variable `consultant_final` holds the standardised consultant name;
`consultant_id_final` is a unique integer identifier.
""",
    unsafe_allow_html=True,
)

rule()
st.markdown(ATTRIBUTION_HTML, unsafe_allow_html=True)
