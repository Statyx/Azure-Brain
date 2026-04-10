# Icon Pipeline — SVG→PNG via Playwright

## Why Playwright?
PowerPoint (python-pptx) does NOT support SVG natively — PNG conversion is mandatory.
FabricToolset SVGs use gradients, which rules out most Python SVG renderers on Windows.

| Approach | Result |
|----------|--------|
| **Playwright + Chromium** | ✅ Pixel-perfect, full gradients, transparent background |
| svglib + reportlab | ❌ Loses gradients (flat colors only) |
| cairosvg | ❌ Broken on Windows (missing libcairo-2.dll) |
| cairocffi | ❌ Same DLL issue, conflicts with rlPyCairo |
| Edge headless | ❌ Process hangs indefinitely |

## FabricToolset Source

Repository: `astrzala/FabricToolset` (clone to `_FabricToolset/`)

SVG categories under `Microsoft Fabric & Azure Icon Pack/svg/`:
```
Fabric Core/           — Fabric, Power BI, Data Factory, OneLake, User, Copilot, etc.
Fabric Artifacts/      — Lakehouse, Pipeline, Notebook, Semantic Model, Report, Data Agent, etc.
Fabric Datasources/    — Excel, SQL Server, Cosmos DB, File Regular, etc.
Azure Core/            — Azure services (App Service, Functions, Storage, etc.)
Azure DevOps/          — DevOps icons
Fabric Black/          — Monochrome variants
Microsoft Tool and Platforms/ — Teams, Office, Edge, etc.
```

## Standard Icon Mapping

```python
ICONS = {
    # Fabric Core
    "Fabric":           "Fabric Core/Fabric.svg",
    "Data_Factory":     "Fabric Core/Data Factory.svg",
    "Data_Engineering": "Fabric Core/Data Engineering.svg",
    "Power_BI":         "Fabric Core/Power BI.svg",
    "OneLake":          "Fabric Core/One Lake.svg",
    "User":             "Fabric Core/User.svg",
    "Users":            "Fabric Core/Users.svg",
    "Copilot":          "Fabric Core/Copilot.svg",
    
    # Fabric Artifacts
    "Lakehouse":        "Fabric Artifacts/Lakehouse.svg",
    "Pipeline":         "Fabric Artifacts/Pipeline.svg",
    "Notebook":         "Fabric Artifacts/Notebook.svg",
    "Semantic_Model":   "Fabric Artifacts/Semantic Model.svg",
    "Report":           "Fabric Artifacts/Power BI Report.svg",
    "Data_Agent":       "Fabric Artifacts/Data Agent.svg",
    "Warehouse":        "Fabric Artifacts/Warehouse.svg",
    "Eventstream":      "Fabric Artifacts/Eventstream.svg",
    "Eventhouse":       "Fabric Artifacts/Eventhouse.svg",
    "KQL_Database":     "Fabric Artifacts/KQL Database.svg",
    "KQL_Queryset":     "Fabric Artifacts/KQL Queryset.svg",
    "Dashboard":        "Fabric Artifacts/Dashboard (Real-Time).svg",
    "Dataflow_Gen2":    "Fabric Artifacts/Dataflow Gen2.svg",
    
    # Fabric Datasources
    "Excel":            "Fabric Datasources/Excel.svg",
    "CSV":              "Fabric Datasources/File Regular.svg",
    "SQL_Server":       "Fabric Datasources/SQL Server.svg",
    "Cosmos_DB":        "Fabric Datasources/Azure Cosmos DB.svg",
}
```

## Conversion Script Pattern

```python
from playwright.sync_api import sync_playwright
from PIL import Image

RENDER_SIZE = 256  # viewport size — icons render at 200px inside

with sync_playwright() as pw:
    browser = pw.chromium.launch()
    page = browser.new_page(viewport={"width": RENDER_SIZE, "height": RENDER_SIZE})
    
    for name, svg_path in ICONS.items():
        svg_content = svg_path.read_text(encoding="utf-8")
        page.set_content(f"""<!DOCTYPE html>
<html><head><style>
* {{ margin:0; padding:0; box-sizing:border-box; }}
html, body {{ width:{RENDER_SIZE}px; height:{RENDER_SIZE}px; background:transparent; }}
body {{ display:flex; align-items:center; justify-content:center; }}
svg {{ width:200px; height:200px; }}
</style></head><body>{svg_content}</body></html>""", wait_until="networkidle")
        
        page.screenshot(path=str(png_path), omit_background=True)
        
        # Auto-crop + square with padding
        img = Image.open(str(png_path)).convert("RGBA")
        bbox = img.getbbox()
        if bbox:
            pad = 6
            x0, y0, x1, y1 = bbox
            x0, y0 = max(0, x0 - pad), max(0, y0 - pad)
            x1, y1 = min(img.width, x1 + pad), min(img.height, y1 + pad)
            w, h = x1 - x0, y1 - y0
            s = max(w, h)
            cx, cy = (x0 + x1) // 2, (y0 + y1) // 2
            x0, y0 = max(0, cx - s // 2), max(0, cy - s // 2)
            x1, y1 = min(img.width, x0 + s), min(img.height, y0 + s)
            img.crop((x0, y0, x1, y1)).save(str(png_path))
    
    browser.close()
```

## Key Details
- `omit_background=True` gives transparent PNG background
- SVG rendered at 200px inside 256px viewport — ensures margin for crop
- Auto-crop removes whitespace, then squares the result (icons must be square for layout)
- Padding of 6px prevents edge clipping
- All icons converted in ONE browser session for speed (~2 seconds total for 16 icons)
