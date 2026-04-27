"""Server-side analysis layer for the PPD Explorer.

Builds a tidy system-year panel (one row per pub_id × fy) from the same
data layer used by the rest of the app, and exposes the variable registry
shared between backend runners and the frontend dropdowns.

Public API
----------
    build_panel() -> pd.DataFrame   # cached system-year panel
    get_variables() -> list[dict]   # variable registry
    run_univariate(y, group_by) -> dict
    run_ols(y, xs, controls, fe, weights, cluster) -> dict
    run_group_comparison(y, group_a, group_b) -> dict
    run_correlation(vars_list, scatter_pair) -> dict
"""
from __future__ import annotations

import sys
from functools import lru_cache
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from dashboard.lib.aggregations import cached_system_year  # noqa: E402
from dashboard.lib.data_loader import load_plan_clean       # noqa: E402


# ── Variable registry ─────────────────────────────────────────────────────────
# Shared by every endpoint and the frontend selects. Keep in sync with the
# columns built in build_panel() below.

VARIABLES: list[dict] = [
    # Outcomes
    {"key": "omega",                       "label": "Omega (alt share of risky)",      "units": "ratio 0–1", "group": "outcome"},
    {"key": "omega_actl",                  "label": "Omega — actual",                  "units": "ratio 0–1", "group": "outcome"},
    {"key": "ret_bgnassets",               "label": "Net return (of fees)",            "units": "ratio",     "group": "outcome"},
    {"key": "ActFundedRatio_GASB",         "label": "Funded ratio (GASB)",             "units": "ratio",     "group": "outcome"},

    # Allocation buckets (target weights, 0–1)
    {"key": "PETotal_Trgt",                "label": "Private equity (target)",         "units": "ratio 0–1", "group": "allocation"},
    {"key": "HFTotal_Trgt",                "label": "Hedge funds (target)",            "units": "ratio 0–1", "group": "allocation"},
    {"key": "RETotal_Trgt",                "label": "Real assets (target)",            "units": "ratio 0–1", "group": "allocation"},
    {"key": "EQTotal_Trgt",                "label": "Public equity (target)",          "units": "ratio 0–1", "group": "allocation"},
    {"key": "FITotal_Trgt",                "label": "Fixed income (target)",           "units": "ratio 0–1", "group": "allocation"},
    {"key": "alternatives_trgt",           "label": "Alternatives total (target)",     "units": "ratio 0–1", "group": "allocation"},

    # Controls / continuous regressors
    {"key": "log_aum",                     "label": "log(AUM)",                        "units": "log $K",    "group": "control"},
    {"key": "MktAssets_net",               "label": "AUM (net market assets)",         "units": "$K",        "group": "control"},
    {"key": "InvestmentReturnAssumption_GASB", "label": "Assumed rate of return",      "units": "ratio",     "group": "control"},
    {"key": "pct_retired",                 "label": "Share of members retired",        "units": "ratio 0–1", "group": "control"},

    # Fixed-effect / grouping dimensions (categorical)
    {"key": "pub_id",                      "label": "System (entity FE)",              "units": "id",        "group": "fe"},
    {"key": "fy",                          "label": "Fiscal year (time FE)",           "units": "year",      "group": "fe"},
    {"key": "StateAbbrev",                 "label": "State",                           "units": "code",      "group": "fe"},
    {"key": "consultant_id",               "label": "Investment consultant",           "units": "id",        "group": "fe"},
    {"key": "aum_tercile",                 "label": "AUM tercile (within year)",       "units": "1–3",       "group": "fe"},
]

VARIABLE_KEYS: set[str] = {v["key"] for v in VARIABLES}


def get_variables() -> list[dict]:
    """Return the variable registry (used by the /api/analysis/variables route)."""
    return VARIABLES


# ── Panel builder ─────────────────────────────────────────────────────────────

_PANEL_COLS = [
    "pub_id", "fy", "StateAbbrev", "consultant_id", "MktAssets_net",
    "omega", "omega_actl",
    "ret_bgnassets", "ActFundedRatio_GASB", "InvestmentReturnAssumption_GASB",
    "EQTotal_Trgt", "FITotal_Trgt", "PETotal_Trgt", "HFTotal_Trgt", "RETotal_Trgt",
    "alternatives_trgt", "pct_retired",
]


def _within_year_terciles(s: pd.Series, year: pd.Series) -> pd.Series:
    """Tercile (1=small, 3=large) computed within each fiscal year."""
    out = pd.Series(pd.NA, index=s.index, dtype="Int64")
    valid = s.notna() & (s > 0)
    for y, idx in year[valid].groupby(year[valid]).groups.items():
        vals = s.loc[idx]
        try:
            out.loc[idx] = pd.qcut(vals, q=3, labels=[1, 2, 3]).astype("Int64")
        except ValueError:
            # Not enough distinct values in this year — fall back to rank-based.
            ranks = vals.rank(method="first")
            edges = np.linspace(0, len(vals), 4)[1:-1]
            out.loc[idx] = (ranks.values > edges[:, None]).sum(axis=0).astype("Int64") + 1
    return out


@lru_cache(maxsize=1)
def build_panel() -> pd.DataFrame:
    """One row per (pub_id, fy) with the columns the analysis runners need.

    Cached at the module level — the underlying dataset doesn't change at
    runtime, so subsequent calls are free.
    """
    plan = load_plan_clean()
    sys_df = cached_system_year(plan)

    # Keep only rows that actually exist in the panel (drop fully-empty
    # system-year cells); the omega NaN handling stays per-test.
    panel = sys_df[_PANEL_COLS].copy()
    panel["fy"] = panel["fy"].astype("Int64")

    # Derived columns
    aum_pos = panel["MktAssets_net"].where(panel["MktAssets_net"] > 0)
    panel["log_aum"] = np.log(aum_pos)
    panel["aum_tercile"] = _within_year_terciles(panel["MktAssets_net"], panel["fy"])

    return panel.reset_index(drop=True)


# ── Test runners ──────────────────────────────────────────────────────────────

# Y must be a continuous panel column (not a dimension).
_NUMERIC_KEYS: set[str] = {
    v["key"] for v in VARIABLES if v["group"] in ("outcome", "allocation", "control")
}
_GROUPABLE: set[str] = {"StateAbbrev", "consultant_id", "aum_tercile"}


def _wavg(values: pd.Series, weights: pd.Series) -> float | None:
    mask = values.notna() & weights.notna() & (weights > 0)
    if not mask.any():
        return None
    w = weights[mask].astype(float)
    v = values[mask].astype(float)
    wsum = float(w.sum())
    if wsum <= 0:
        return None
    return float((v * w).sum() / wsum)


def _series_for(df: pd.DataFrame, y: str) -> list[dict]:
    """AUM-weighted Y by fiscal year for one (sub)frame."""
    out: list[dict] = []
    for fy, g in df.groupby("fy", sort=True):
        val = _wavg(g[y], g["MktAssets_net"])
        n = int(g[y].notna().sum())
        out.append({"year": int(fy), "value": val, "n": n})
    return out


def run_univariate(y: str, group_by: str | None = None) -> dict:
    """AUM-weighted Y over time, optionally split by a categorical dimension.

    Returns
    -------
    dict
        {
          "summary": str,
          "series": [{"group": str, "points": [{"year","value","n"}, ...]}, ...],
          "sample": {"n", "n_systems", "fy_min", "fy_max"},
        }
    """
    if y not in _NUMERIC_KEYS:
        raise ValueError(f"y must be a numeric variable; got {y!r}")
    if group_by is not None and group_by not in _GROUPABLE:
        raise ValueError(f"group_by must be one of {sorted(_GROUPABLE)} or null; got {group_by!r}")

    panel = build_panel()
    cols = ["fy", "pub_id", "MktAssets_net", y] + ([group_by] if group_by else [])
    df = panel[cols].dropna(subset=[y]).copy()

    if group_by is None:
        series = [{"group": "All", "points": _series_for(df, y)}]
    else:
        df = df.dropna(subset=[group_by])
        series = []
        for key, sub in df.groupby(group_by, sort=True):
            if isinstance(key, (int, np.integer)) or (isinstance(key, float) and key.is_integer()):
                label = str(int(key))
            else:
                label = str(key)
            series.append({"group": label, "points": _series_for(sub, y)})

    sample = {
        "n": int(len(df)),
        "n_systems": int(df["pub_id"].nunique()),
        "fy_min": int(df["fy"].min()) if len(df) else None,
        "fy_max": int(df["fy"].max()) if len(df) else None,
    }
    summary = (
        f"AUM-weighted {y} by fiscal year"
        + (f", grouped by {group_by}" if group_by else "")
        + f" — N={sample['n']:,} obs across {sample['n_systems']} systems."
    )
    return {"summary": summary, "series": series, "sample": sample}


# ── OLS regression ────────────────────────────────────────────────────────────

_FE_OPTIONS: set[str] = {"pub_id", "fy", "StateAbbrev", "consultant_id"}
_SCATTER_CAP = 1000  # downsample large scatters for chart payload size


def _validate_var(name: str, val: str) -> None:
    if val not in _NUMERIC_KEYS:
        raise ValueError(f"{name} {val!r} is not a numeric variable")


_WEIGHTS_OPTIONS: set[str] = {"equal", "aum"}
_CLUSTER_OPTIONS: set[str] = {"entity", "twoway"}


def run_ols(
    y: str,
    xs: list[str],
    controls: list[str] | None = None,
    fe: list[str] | None = None,
    weights: str = "equal",
    cluster: str = "entity",
) -> dict:
    """Panel OLS of Y on Xs (+ optional controls, fixed effects, weights, cluster mode).

    Parameters
    ----------
    weights : {"equal", "aum"}
        ``"equal"`` (default) gives every system-year the same weight. ``"aum"``
        weights observations by ``MktAssets_net`` — paper-style WLS where larger
        funds dominate the estimate.
    cluster : {"entity", "twoway"}
        ``"entity"`` (default) clusters SEs by ``pub_id`` only. ``"twoway"``
        clusters by both ``pub_id`` and ``fy`` (Cameron-Gelbach-Miller),
        appropriate when residuals are correlated within both dimensions.

    Returns the coefficient table, a residual-by-year series, and a partial-
    regression scatter for the first X (slope = the multivariate β shown in
    the coefficient table, by Frisch-Waugh-Lovell).
    """
    controls = controls or []
    fe = fe or []
    if not xs:
        raise ValueError("OLS requires at least one X variable")
    if weights not in _WEIGHTS_OPTIONS:
        raise ValueError(f"weights must be one of {sorted(_WEIGHTS_OPTIONS)}; got {weights!r}")
    if cluster not in _CLUSTER_OPTIONS:
        raise ValueError(f"cluster must be one of {sorted(_CLUSTER_OPTIONS)}; got {cluster!r}")
    _validate_var("y", y)
    for v in xs:
        _validate_var("X", v)
    for v in controls:
        _validate_var("control", v)
    for f in fe:
        if f not in _FE_OPTIONS:
            raise ValueError(f"FE {f!r} must be one of {sorted(_FE_OPTIONS)}")

    panel = build_panel()
    needed = list({"pub_id", "fy", y, *xs, *controls, "MktAssets_net", "StateAbbrev", "consultant_id"})
    df = panel[needed].dropna(subset=[y, *xs, *controls, "pub_id", "fy"]).copy()

    # Drop rows missing a requested categorical FE so they don't get bucketed
    # into a synthetic "_nan" category (which would silently bias the estimate).
    fe_categorical = [f for f in ("StateAbbrev", "consultant_id") if f in fe]
    if fe_categorical:
        df = df.dropna(subset=fe_categorical)

    # When AUM-weighted, drop rows with missing/zero weights too.
    if weights == "aum":
        df = df[df["MktAssets_net"].notna() & (df["MktAssets_net"] > 0)]

    if df.empty:
        raise ValueError("No observations after dropping rows with missing y/x/controls/FE/weights")

    model_x_cols = list(xs) + list(controls)

    # Categorical FE (state, consultant) → dummies. Entity/time absorbed by linearmodels.
    for fe_var in fe_categorical:
        dums = pd.get_dummies(
            df[fe_var].astype(str), prefix=fe_var, drop_first=True, dtype=float
        )
        df = pd.concat([df, dums], axis=1)
        model_x_cols += dums.columns.tolist()

    use_entity = "pub_id" in fe
    use_time = "fy" in fe

    from linearmodels.panel import PanelOLS  # local import to keep module load light

    panel_df = df.set_index(["pub_id", "fy"])
    w_series = panel_df["MktAssets_net"].astype(float) if weights == "aum" else None

    fit_kwargs: dict = {"cov_type": "clustered", "cluster_entity": True}
    if cluster == "twoway":
        fit_kwargs["cluster_time"] = True

    res = PanelOLS(
        panel_df[y],
        panel_df[model_x_cols],
        weights=w_series,
        entity_effects=use_entity,
        time_effects=use_time,
        drop_absorbed=True,
        check_rank=False,
    ).fit(**fit_kwargs)

    # Coefficient table — restrict to user-named regressors (not dummy bloat)
    user_named = set(xs) | set(controls)
    coefficients = []
    ci = res.conf_int()
    for name in res.params.index:
        if name not in user_named:
            continue
        coefficients.append({
            "name": str(name),
            "beta":  float(res.params[name]),
            "se":    float(res.std_errors[name]),
            "t":     float(res.tstats[name]),
            "p":     float(res.pvalues[name]),
            "ci_lo": float(ci.loc[name].iloc[0]),
            "ci_hi": float(ci.loc[name].iloc[1]),
        })

    # Residuals by fiscal year (mean + 10/90 percentiles)
    resid = res.resids
    rdf = pd.DataFrame({
        "resid": resid.values,
        "fy": resid.index.get_level_values("fy"),
    })
    residual_series = []
    for fy, g in rdf.groupby("fy", sort=True):
        residual_series.append({
            "year": int(fy),
            "mean": float(g["resid"].mean()),
            "p10": float(g["resid"].quantile(0.10)),
            "p90": float(g["resid"].quantile(0.90)),
        })

    # Partial-regression scatter for the first X (Frisch-Waugh-Lovell).
    # The slope on this scatter is *exactly* the multivariate β shown in the
    # coefficient table, because:
    #     residual(Y on others, FE) = main_residuals + β_first_x · residual(X on others, FE)
    # When there are no other regressors and no FE, partial residuals collapse
    # to mean-centred raw values and the slope == univariate slope == β anyway.
    first_x = xs[0]
    other_x_cols = [c for c in model_x_cols if c != first_x]

    if not other_x_cols and not use_entity and not use_time:
        # Nothing to partial out → centre raw values around their means.
        e_x = panel_df[first_x].to_numpy(dtype=float) - float(panel_df[first_x].mean())
        e_y = panel_df[y].to_numpy(dtype=float) - float(panel_df[y].mean())
    else:
        # Auxiliary regression of first_x on (other regressors + FE) to get e_x;
        # then FWL identity gives e_y from main residuals + β · e_x.
        if other_x_cols:
            aux_x_fit = PanelOLS(
                panel_df[first_x], panel_df[other_x_cols],
                weights=w_series,
                entity_effects=use_entity, time_effects=use_time,
                drop_absorbed=True, check_rank=False,
            ).fit(cov_type="unadjusted")
            e_x = aux_x_fit.resids.to_numpy(dtype=float)
        else:
            # FE-only case: demean first_x by FE without other regressors.
            const = pd.DataFrame({"_const": 1.0}, index=panel_df.index)
            aux_x_fit = PanelOLS(
                panel_df[first_x], const,
                weights=w_series,
                entity_effects=use_entity, time_effects=use_time,
                drop_absorbed=True, check_rank=False,
            ).fit(cov_type="unadjusted")
            e_x = aux_x_fit.resids.to_numpy(dtype=float)
        beta_first = float(res.params[first_x]) if first_x in res.params.index else 0.0
        e_y = res.resids.to_numpy(dtype=float) + beta_first * e_x

    points = [{"x": float(xi), "y": float(yi)} for xi, yi in zip(e_x, e_y)]
    if len(points) > _SCATTER_CAP:
        rng = np.random.default_rng(42)
        idx = rng.choice(len(points), size=_SCATTER_CAP, replace=False)
        points = [points[i] for i in sorted(idx.tolist())]

    # Fit line: slope = β from main regression, anchored at e_x range
    beta_fx = float(res.params[first_x]) if first_x in res.params.index else 0.0
    e_x_min, e_x_max = float(min(e_x)), float(max(e_x))
    fit_line = [
        {"x": e_x_min, "y": beta_fx * e_x_min},
        {"x": e_x_max, "y": beta_fx * e_x_max},
    ]
    scatter = {
        "x_label": first_x,
        "y_label": y,
        "is_partial": (bool(other_x_cols) or use_entity or use_time),
        "points": points,
        "fit_line": fit_line,
        "fit_note": (
            f"Partial-regression plot (FWL). Line slope = β = {beta_fx:.4g} — "
            f"matches the multivariate coefficient in the table above."
            if (other_x_cols or use_entity or use_time)
            else f"Univariate fit. Slope = β = {beta_fx:.4g} (no controls/FE to partial out)."
        ),
    }

    # R² within is only meaningful with FE
    r2_within = float(getattr(res, "rsquared_within", np.nan))
    if not np.isfinite(r2_within):
        r2_within = None

    cluster_desc = "clustered SE by pub_id" if cluster == "entity" else "two-way clustered SE (pub_id × fy)"
    weight_desc = "AUM-weighted" if weights == "aum" else "equal-weighted"
    sample = {
        "n": int(res.nobs),
        "n_systems": int(panel_df.index.get_level_values("pub_id").nunique()),
        "fy_min": int(panel_df.index.get_level_values("fy").min()),
        "fy_max": int(panel_df.index.get_level_values("fy").max()),
        "r2": float(res.rsquared),
        "r2_within": r2_within,
        "weights": weights,
        "cluster": cluster,
    }
    fe_desc = " + ".join(f"{f} FE" for f in fe) or "no FE"
    summary = (
        f"OLS of {y} on {', '.join(xs)}"
        + (f" with controls {', '.join(controls)}" if controls else "")
        + f"; {fe_desc}; {weight_desc}; {cluster_desc}; N={sample['n']:,}, "
        + f"R²={sample['r2']:.3f}"
        + (f" (within={r2_within:.3f})" if r2_within is not None else "")
        + "."
    )
    return {
        "summary": summary,
        "coefficients": coefficients,
        "residual_series": residual_series,
        "scatter": scatter,
        "sample": sample,
    }


# ── Two-group comparison (AUM-weighted Y by year, A vs B) ─────────────────────

# Note: this is a descriptive group-comparison test, not a formal event study —
# there is no event date, no pre/post split, and no parallel-trends assumption.
# The output is simply two AUM-weighted time series plus their difference.

_GROUP_DIMS: set[str] = {"consultant_id", "StateAbbrev"}


def _coerce_match(by: str, values: list) -> list:
    """Normalise group-filter values to match the panel's column dtype."""
    if by == "consultant_id":
        out = []
        for v in values:
            try:
                out.append(float(v))
            except (TypeError, ValueError):
                pass
        return out
    return [str(v) for v in values]


def run_group_comparison(y: str, group_a: dict, group_b: dict) -> dict:
    """Two-group AUM-weighted Y by year, plus an A−B difference series.

    Each group is a filter ``{by: 'consultant_id'|'StateAbbrev', values: [...]}``.
    Descriptive only — does *not* implement event-time dynamics or
    difference-in-differences.
    """
    _validate_var("y", y)
    for name, g in (("group_a", group_a), ("group_b", group_b)):
        if not isinstance(g, dict) or "by" not in g or "values" not in g:
            raise ValueError(f"{name} must be {{by, values}}")
        if g["by"] not in _GROUP_DIMS:
            raise ValueError(f"{name}.by must be one of {sorted(_GROUP_DIMS)}")
        if not g["values"]:
            raise ValueError(f"{name}.values is empty")

    panel = build_panel()
    cols = ["fy", "pub_id", "MktAssets_net", y, "StateAbbrev", "consultant_id"]
    df = panel[cols].dropna(subset=[y]).copy()

    df_a = df[df[group_a["by"]].isin(_coerce_match(group_a["by"], group_a["values"]))]
    df_b = df[df[group_b["by"]].isin(_coerce_match(group_b["by"], group_b["values"]))]

    series_a = _series_for(df_a, y)
    series_b = _series_for(df_b, y)

    # A − B by year
    a_map = {p["year"]: p["value"] for p in series_a}
    b_map = {p["year"]: p["value"] for p in series_b}
    n_a_map = {p["year"]: p["n"] for p in series_a}
    n_b_map = {p["year"]: p["n"] for p in series_b}
    years = sorted(set(a_map) | set(b_map))
    diff_series = []
    for fy in years:
        va, vb = a_map.get(fy), b_map.get(fy)
        diff = (va - vb) if (va is not None and vb is not None) else None
        diff_series.append({
            "year": fy,
            "value": diff,
            "n": n_a_map.get(fy, 0) + n_b_map.get(fy, 0),
        })

    sample = {
        "n_a": int(len(df_a)),
        "n_b": int(len(df_b)),
        "n_systems_a": int(df_a["pub_id"].nunique()),
        "n_systems_b": int(df_b["pub_id"].nunique()),
        "fy_min": int(df["fy"].min()) if len(df) else None,
        "fy_max": int(df["fy"].max()) if len(df) else None,
    }
    def _fmt_vals(vs):
        head = list(vs)[:3]
        return f"{head}{'…' if len(vs) > 3 else ''}"
    summary = (
        f"Group comparison of {y}: A ({group_a['by']}={_fmt_vals(group_a['values'])}) vs "
        f"B ({group_b['by']}={_fmt_vals(group_b['values'])}). "
        f"N_A={sample['n_a']:,} obs / {sample['n_systems_a']} systems · "
        f"N_B={sample['n_b']:,} obs / {sample['n_systems_b']} systems."
    )
    return {
        "summary": summary,
        "series": [
            {"group": "A", "points": series_a},
            {"group": "B", "points": series_b},
            {"group": "A−B", "points": diff_series},
        ],
        "sample": sample,
    }


# ── Correlation matrix (+ optional scatter) ───────────────────────────────────

def run_correlation(vars_list: list[str], scatter_pair: list[str] | None = None) -> dict:
    """Pearson + Spearman matrices over the system-year panel; optional scatter."""
    if not vars_list or len(vars_list) < 2:
        raise ValueError("correlation requires at least 2 variables")
    for v in vars_list:
        _validate_var("vars", v)
    if scatter_pair is not None:
        if not isinstance(scatter_pair, list) or len(scatter_pair) != 2:
            raise ValueError("scatter_pair must be a 2-element list")
        for v in scatter_pair:
            if v not in vars_list:
                raise ValueError(f"scatter_pair includes {v!r} not in vars")

    panel = build_panel()
    cols = list({*vars_list, "fy", "pub_id"})
    df = panel[cols].dropna(subset=vars_list).copy()
    if df.empty:
        raise ValueError("No observations after dropping rows with missing values")

    pearson = df[vars_list].corr(method="pearson")
    spearman = df[vars_list].corr(method="spearman")
    matrices = {
        "vars": vars_list,
        "pearson":  [[float(v) for v in row] for row in pearson.values.tolist()],
        "spearman": [[float(v) for v in row] for row in spearman.values.tolist()],
    }

    scatter = None
    if scatter_pair is not None:
        x_col, y_col = scatter_pair
        sub = df[[x_col, y_col]].copy()
        if len(sub) > _SCATTER_CAP:
            sub = sub.sample(_SCATTER_CAP, random_state=42)
        scatter = {
            "x_label": x_col,
            "y_label": y_col,
            "points": [
                {"x": float(r[x_col]), "y": float(r[y_col])} for _, r in sub.iterrows()
            ],
        }

    sample = {
        "n": int(len(df)),
        "n_systems": int(df["pub_id"].nunique()),
        "fy_min": int(df["fy"].min()),
        "fy_max": int(df["fy"].max()),
    }
    summary = (
        f"Pairwise correlations across {len(vars_list)} variables — "
        f"N={sample['n']:,} obs / {sample['n_systems']} systems."
    )
    return {"summary": summary, "matrices": matrices, "scatter": scatter, "sample": sample}
