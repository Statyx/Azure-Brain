# Icon Catalog

Source: [astrzala/FabricToolset](https://github.com/astrzala/FabricToolset) — 303 SVG icons  
License: MIT

---

## Icon Categories (7 directories)

| Category | Directory | Count | Description |
|----------|-----------|-------|-------------|
| **Fabric Core** | `icons/Fabric_Core/` | ~80 | Core Fabric service icons (Fabric logo, OneLake, capacity) |
| **Fabric Artifacts** | `icons/Fabric_Artifacts/` | ~60 | Item types (Lakehouse, Notebook, Pipeline, Report, etc.) |
| **Fabric Black** | `icons/Fabric_Black/` | ~80 | Monochrome versions of Fabric icons |
| **Fabric Datasources** | `icons/Fabric_Datasources/` | ~30 | Data source connectors |
| **Azure Core** | `icons/Azure_Core/` | ~25 | Azure service icons (Key Vault, App Insights, etc.) |
| **Azure DevOps** | `icons/Azure_DevOps/` | ~15 | Azure DevOps pipeline, boards, repos icons |
| **Microsoft Tool and Platforms** | `icons/Microsoft_Tool_and_Platforms/` | ~13 | Teams, Power Platform, Copilot, etc. |

---

## Most-Used Icons (Architecture Diagrams)

These 13 icons are the core set for Fabric architecture diagrams:

| Icon Name | Alt Tag | Category | Typical Use |
|-----------|---------|----------|-------------|
| Fabric | `Fabric` | Fabric_Core | Main Fabric logo, title, zone header |
| OneLake | `OneLake` | Fabric_Core | Data lake references |
| Lakehouse | `Lakehouse` | Fabric_Artifacts | Lakehouse items |
| Notebook | `Notebook` | Fabric_Artifacts | PySpark notebooks |
| Pipeline | `Pipeline` | Fabric_Artifacts | Data Factory pipelines |
| Semantic Model | `Semantic Model` | Fabric_Artifacts | Semantic model items |
| Report | `Report` | Fabric_Artifacts | Power BI reports |
| Data Agent | `Data Agent` | Fabric_Artifacts | AI Data Agents |
| CSV | `CSV` | Fabric_Datasources | CSV file sources |
| Excel | `Excel` | Fabric_Datasources | Excel file sources |
| Power BI | `PBI` | Fabric_Core | Power BI service icon |
| User | `User` | Microsoft_Tool_and_Platforms | Business user personas |
| Copilot | `Copilot` | Microsoft_Tool_and_Platforms | AI/Copilot users |

---

## RTI (Real-Time Intelligence) Icons

Additional icons for streaming / real-time architectures:

| Icon Name | Alt Tag | Category |
|-----------|---------|----------|
| Eventhouse | `Eventhouse` | Fabric_Artifacts |
| KQL Database | `KQL Database` | Fabric_Artifacts |
| EventStream | `EventStream` | Fabric_Artifacts |
| KQL Dashboard | `KQL Dashboard` | Fabric_Artifacts |
| Event Hub | `Event Hub` | Azure_Core |

---

## Base64 Embedding Workflow

### Step 1: Download SVGs
```bash
# From FabricToolset repo — download specific icons
curl -o Fabric.svg "https://raw.githubusercontent.com/astrzala/FabricToolset/.../Fabric.svg"
```

### Step 2: Convert to Base64
```python
import base64
from pathlib import Path

svg_path = Path("icons/Fabric_Artifacts/Lakehouse.svg")
b64 = base64.b64encode(svg_path.read_bytes()).decode()
data_uri = f"data:image/svg+xml;base64,{b64}"
```

### Step 3: Use in HTML
```html
<img src="data:image/svg+xml;base64,PHN2ZyB4bWxucz0i..." alt="Lakehouse" style="width:36px;">
```

### Step 4: Extract from Existing HTML
```python
import re
icons = {}
for m in re.finditer(r'alt="([^"]+)"[^>]*src="(data:image/svg\+xml;base64,[^"]+)"', html):
    icons[m.group(1)] = m.group(2)
```

---

## Icon Sizing Guidelines

| Context | Size | CSS |
|---------|------|-----|
| Title logo | 50px height | `style="height:50px;"` |
| Zone header | 32px height | `style="height:32px;"` |
| Component card | 36×36px | `style="width:36px;height:36px;"` |
| Source item | 24–28px | `style="width:28px;height:28px;"` |
| User persona | 24px | `style="width:24px;height:24px;"` |
| Workload badge | 16px height | `style="height:16px;"` |

---

## Adding New Icons

1. Download SVG from [FabricToolset](https://github.com/astrzala/FabricToolset)
2. Place in appropriate `icons/` subdirectory
3. Add to existing HTML using the base64 embedding workflow above
4. Once embedded, the rebuild script will automatically extract and preserve it
5. Update this catalog with the new icon's alt tag and category
