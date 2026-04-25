# Legacy Streamlit Dashboard

Frozen as backup. The current dashboard is the React/HTML build under
`../web/`.

## Run

```sh
cd legacy
../.venv/bin/streamlit run streamlit_app.py --server.port 8501
```

Then open http://localhost:8501.

## What's here

- `streamlit_app.py` — landing page
- `pages/` — System / Consultant / State / Methodology pages
- `.streamlit/config.toml` — Streamlit theme config

## Dependencies

- Imports the data layer from `../dashboard/lib/` (data_loader,
  aggregations, config) — those files stay in the project root because
  the new web build also depends on them.
- `dashboard/lib/charts.py` and `dashboard/lib/ui.py` are Streamlit-only
  helpers used exclusively by this legacy app; they remain in
  `../dashboard/lib/` for import simplicity.
