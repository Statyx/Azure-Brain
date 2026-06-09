# PBIR Template — `Template.Report/`

Minimal working PBIR skeleton. Copy the entire folder, rename to `<YourReport>.Report/`, and:

1. Edit `definition.pbir` — replace `<WORKSPACE_NAME>`, `<MODEL_NAME>`, `<MODEL_GUID>`.
2. Edit `definition/report.json` — keep `themeCollection.baseTheme.name` matching the theme file in `StaticResources/SharedResources/BaseThemes/`.
3. Edit `definition/pages/overview/visuals/card_revenue_0001/visual.json` — replace `fact_general_ledger` / `Total Revenue` with your entity and measure.
4. Edit `definition/pages/overview/visuals/line_revenue_trend_0001/visual.json` — same.
5. Add more pages by copying `pages/overview/` to `pages/<newPage>/` and adding the page to `pages.json.pageOrder`.

## Layout

```
Template.Report/
├── definition.pbir
├── definition/
│   ├── report.json
│   └── pages/
│       ├── pages.json
│       └── overview/
│           ├── page.json
│           └── visuals/
│               ├── card_revenue_0001/
│               │   └── visual.json
│               └── line_revenue_trend_0001/
│                   └── visual.json
└── StaticResources/
    └── SharedResources/
        └── BaseThemes/
            └── AzureBrainLight.json
```

## Validate

```powershell
powerbi-report-author validate Template.Report --format text
```

Expect zero errors. Warnings about missing measures are normal if the semantic model isn't bound.

## Deploy

Use the reference uploader at [`../../deploy_report.py`](../../deploy_report.py).

## References

- Folder anatomy → [`../../../report_structure.md`](../../../report_structure.md)
- Expression encoding → [`../../../themes_styling.md`](../../../themes_styling.md)
- Visual selection → [`../../../visual_catalog.md`](../../../visual_catalog.md)
- Property lookups → [`../../../cli_knowledge/`](../../../cli_knowledge/)
