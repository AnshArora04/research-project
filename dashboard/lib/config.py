"""Data-root configuration for the Public Pension Data Explorer.

Priority order for resolving the output_python/ directory:
  1. PENSION_DATA_ROOT environment variable (absolute path to an output_python/ folder)
  2. Sibling output_python/ relative to the repository root (default)

Usage
-----
    from dashboard.lib.config import get_data_root, get_data_path

    root = get_data_root()          # -> Path(".../output_python")
    f    = get_data_path("ppd_plan_level_clean.parquet")
"""

from __future__ import annotations

import os
from pathlib import Path

# Canonical filenames that the dashboard depends on.
DATA_FILES: dict[str, str] = {
    "plan_clean":   "ppd_plan_level_clean.parquet",
    "plan_raw":     "ppd_plan_level_raw.parquet",
    "allocations":  "ppd_plan_clean_allocations.parquet",
    "performance":  "ppd_performance.parquet",
    "mapping":      "mapping_table_fy_final.parquet",
}

# CSV fallbacks (same keys).
DATA_FILES_CSV: dict[str, str] = {k: v.replace(".parquet", ".csv") for k, v in DATA_FILES.items()}

# Repository root: two levels up from this file (dashboard/lib/config.py → repo root).
_REPO_ROOT = Path(__file__).resolve().parent.parent.parent


def get_data_root() -> Path:
    """Return the resolved path to the output_python/ directory."""
    env = os.environ.get("PENSION_DATA_ROOT", "").strip()
    if env:
        p = Path(env).expanduser().resolve()
        if not p.is_dir():
            raise FileNotFoundError(
                f"PENSION_DATA_ROOT={env!r} does not exist or is not a directory."
            )
        return p
    default = _REPO_ROOT / "output_python"
    return default.resolve()


def get_data_path(key: str, *, prefer_parquet: bool = True) -> Path:
    """Return the full path for a named data file.

    Parameters
    ----------
    key:
        One of the keys defined in DATA_FILES (e.g. ``"plan_clean"``).
    prefer_parquet:
        If True (default), return the .parquet path when it exists, falling
        back to the CSV equivalent.  If False, always return the CSV path.

    Raises
    ------
    KeyError
        When *key* is not recognised.
    FileNotFoundError
        When neither the parquet nor the CSV variant exists on disk.
    """
    if key not in DATA_FILES:
        raise KeyError(f"Unknown data key {key!r}. Valid keys: {list(DATA_FILES)}")

    root = get_data_root()

    if prefer_parquet:
        parquet_path = root / DATA_FILES[key]
        if parquet_path.exists():
            return parquet_path

    csv_path = root / DATA_FILES_CSV[key]
    if csv_path.exists():
        return csv_path

    raise FileNotFoundError(
        f"Could not find {DATA_FILES[key]!r} or {DATA_FILES_CSV[key]!r} "
        f"in {root}. Re-run the pipeline notebooks to regenerate output files."
    )


def check_data_availability() -> dict[str, bool]:
    """Return a dict mapping each data key to whether it exists on disk."""
    root = get_data_root()
    result: dict[str, bool] = {}
    for key, fname in DATA_FILES.items():
        parquet_ok = (root / fname).exists()
        csv_ok     = (root / DATA_FILES_CSV[key]).exists()
        result[key] = parquet_ok or csv_ok
    return result
