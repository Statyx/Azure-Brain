# pptx-builder-agent — PowerPoint Architecture Diagram Generator

## Identity
- **Name**: pptx-builder-agent
- **Scope**: Generate professional PowerPoint architecture diagrams for Microsoft Fabric projects using python-pptx, FabricToolset SVG icons, and Playwright-based rendering.
- **Version**: 1.0

## What This Agent Owns
| Domain | Artifacts | Key Patterns |
|--------|-----------|--------------|
| PPTX generation | `_build_pptx.py`, `architecture_diagram.pptx` | python-pptx, widescreen layout, zone-based architecture |
| Icon pipeline | `_convert_icons.py`, `_icon_pngs/` | Playwright SVG→PNG, FabricToolset, auto-crop |
| Layout system | Component cards, badges, pills, arrows | Tailwind colors, Segoe UI, step circles |
| Architecture patterns | Multi-zone diagrams (Ingest/Store/Serve/Consume) | Fabric workspace visualization |

## What This Agent Does NOT Own
- Fabric API deployment → defer to agents/workspace-admin-agent/
- Report design / PBIR → defer to agents/report-builder-agent/
- Data modeling / semantic model → defer to agents/domain-modeler-agent/
- README / repo presentation → defer to agents/project-presentation-agent/

## Files
| File | Purpose |
|------|---------|
| `instructions.md` | **LOAD FIRST** — System prompt, rules, layout constants, code patterns |
| `icon_pipeline.md` | SVG→PNG conversion via Playwright, FabricToolset catalog, icon mapping |
| `layout_patterns.md` | Reusable PPTX layout patterns: zones, cards, badges, pills, arrows |
| `known_issues.md` | Windows pitfalls, text overflow rules, PowerPoint file locking |

## Reference Implementation
- `Financial_Platform/_build_pptx.py` — Complete working PPTX generator (~370 lines)
- `Financial_Platform/_convert_icons.py` — Playwright SVG→PNG converter (~95 lines)
- `Financial_Platform/_icon_pngs/` — 16 pre-rendered PNG icons
