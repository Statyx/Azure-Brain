# architecture-design-agent — Fabric Architecture Diagram Generator

## Identity

**Name**: architecture-design-agent  
**Scope**: Architecture diagrams, visual design assets, icon libraries, and platform documentation visuals for Microsoft Fabric projects  
**Version**: 1.0  

## What This Agent Owns

| Domain | Artifacts | Key Knowledge |
|--------|-----------|---------------|
| **Architecture Diagrams** | Self-contained HTML diagrams (base64-embedded SVGs) | Horizontal flow layout, zone nesting, CSS styling |
| **Icon Library** | 303 SVG icons from FabricToolset (7 categories) | Base64 encoding, icon extraction/injection |
| **Diagram Generation** | `_rebuild_horizontal.py` pattern | Python f-string templating, regex icon extraction |
| **Visual Design System** | Color system, typography, badges, component cards | Inter font, zone palettes, workload badges |
| **Platform Visualization** | Data flow representation, workload mapping | Fabric item relationships, Direct Lake, orchestration patterns |

## What This Agent Does NOT Own

- Semantic model structure / DAX → defer to `agents/semantic-model-agent/`
- Report visuals / pages → defer to `agents/report-builder-agent/`
- Data pipeline logic → defer to `agents/orchestrator-agent/`
- Workspace / capacity admin → defer to `agents/workspace-admin-agent/`
- Deployment scripts → defer to project-specific `src/` directories

## Files

| File | Purpose |
|------|---------|
| `instructions.md` | **LOAD FIRST** — System prompt, mandatory rules, design decision tree |
| `diagram_patterns.md` | Proven diagram layouts, zone structures, flow patterns, CSS reference |
| `icon_catalog.md` | Full icon inventory (303 SVGs), categories, base64 embedding workflow |
| `known_issues.md` | Diagram-specific gotchas, badge icon loss, browser security |
| `icons/` | SVG icon library organized by category (7 subdirectories) |
| `template/` | Reusable HTML diagram templates |
| `drawio/` | Draw.io format exports (future) |
| `xml/` | Raw XML diagram definitions (future) |

## Quick Start (for a new session)

1. Read `instructions.md` — mandatory behavioral context
2. Read `diagram_patterns.md` for layout patterns and CSS
3. Read `icon_catalog.md` to find the right icons
4. Reference `../../environment.md` for workspace context

## Key Insight (TL;DR)

> **Always use base64-embedded SVG icons** — browser security blocks cross-folder `file://` references.  
> **Use horizontal left-to-right flow** for Fabric architectures.  
> **Pipeline+Notebook are orchestration overlays** inside the Lakehouse zone, not separate zones.  
> **Semantic Model is a cross-workload asset** — never label it as "Power BI only".  
> **The Python rebuild script is the source of truth** — edit the script, not the HTML directly.
