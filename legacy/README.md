# Legacy Streamlit Dashboard

Frozen as backup. The current dashboard is the React/HTML build under
[`../web/`](../web/) — run it with `./run.sh` from the repo root.

## Run

```sh
cd legacy
../.venv/bin/streamlit run streamlit_app.py --server.port 8501
```

Then open <http://localhost:8501>.

## What's here

- `streamlit_app.py` — landing page (4 KPI tiles + hero ω chart + sub-allocation strip + 4 nav cards)
- `pages/` — System / Consultant / State / Methodology pages
- `.streamlit/config.toml` — Streamlit theme config

## Dependencies

- Imports the data layer from `../dashboard/lib/` (`data_loader`,
  `aggregations`, `config`) — those files stay in the project root because
  the new web build also depends on them.
- `../dashboard/lib/charts.py` and `../dashboard/lib/ui.py` are
  Streamlit-only helpers used exclusively by this legacy app; they remain
  in `../dashboard/lib/` for import simplicity.

## Known issues (not fixed — kept as backup, not active)

- **Landing-page AUM display reads "$5B" instead of "$5.1T".**
  The landing page uses `MktAssets_net.sum() / 1e9`, but `MktAssets_net`
  is in **thousands** of dollars (CalPERS row = `477,322,752` =
  $477.3B). The correct divisor is `/ 1e6` for billions. The new
  `web/bake_data.py` uses the right unit; this legacy code does not.
