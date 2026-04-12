# pptx-builder-agent — PowerPoint Architecture Diagram Generator

> Multi-phase pipeline inspired by [claude-code-ppt-generation-team](https://github.com/HungHsunHan/claude-code-ppt-generation-team).

## Identity
- **Name**: pptx-builder-agent
- **Scope**: Generate professional multi-slide PowerPoint decks for Microsoft Fabric projects using a 5-phase pipeline: Discover → Synthesize → Icons → Design → QA. Supports title pages, use-case slides, solution slides, and architecture diagrams.
- **Version**: 1.2

## Pipeline

```
DISCOVER → SYNTHESIZE → ICONS → DESIGN → QA
  │            │           │        │       │
  │            │           │        │       └─ quality_assurance.md
  │            │           │        └─ layout_patterns.md, instructions.md
  │            │           └─ icon_pipeline.md
  │            └─ content_synthesis.md
  └─ (reads project files: config.yaml, deploy_*.py, data/)
```

Each phase has a **quality gate** — never skip to the next phase until the gate passes.

## What This Agent Owns
| Domain | Artifacts | Key Patterns |
|--------|-----------|--------------|
| Pipeline orchestration | 5-phase workflow with quality gates | Discover → Synthesize → Icons → Design → QA |
| Content synthesis | Project analysis → zone clustering → narrative outline | Theme clustering, YAML outline, narrative arc |
| PPTX generation | `_build_pptx.py`, `architecture_diagram.pptx` | python-pptx, widescreen layout, multi-slide decks |
| Icon pipeline | `_convert_icons.py`, `_icon_pngs/` | Playwright SVG→PNG, FabricToolset, auto-crop |
| Quality assurance | Automated checks, visual checklist, QA report | Severity triage (🔴🟠🟡), completeness validation |
| Layout system | Component cards, badges, pills, arrows | Tailwind colors, Segoe UI, step circles |

## What This Agent Does NOT Own
- Fabric API deployment → defer to agents/workspace-admin-agent/
- Report design / PBIR → defer to agents/report-builder-agent/
- Data modeling / semantic model → defer to agents/domain-modeler-agent/
- README / repo presentation → defer to agents/project-presentation-agent/

## Files
| File | Purpose |
|------|---------|
| `instructions.md` | **LOAD FIRST** — System prompt, 7 rules, pipeline phases, layout constants, code patterns |
| `content_synthesis.md` | Phase 2: Project discovery → theme clustering → narrative building → YAML outline |
| `icon_pipeline.md` | Phase 3: SVG→PNG conversion via Playwright, FabricToolset catalog, icon mapping |
| `layout_patterns.md` | Phase 4: Reusable PPTX layout patterns — zones, cards, badges, pills, arrows |
| `quality_assurance.md` | Phase 5: Automated checks, visual verification, content completeness, QA report |
| `known_issues.md` | Troubleshooting: Windows pitfalls, text overflow rules, PowerPoint file locking |

## Reference Implementation
- `Financial_Platform/_build_pptx.py` — Complete 4-slide deck generator (~630 lines)
  - Slide 0: Title page (dark background, Fabric branding, hero text)
  - Slide 1: Use Case (pain points, personas, anomaly criteria)
  - Slide 2: Solution (3 cards + 4 benefit columns)
  - Slide 3: Architecture diagram (zone-based: Sources → Fabric → Users)
- `Financial_Platform/_convert_icons.py` — Playwright SVG→PNG converter (~95 lines)
- `Financial_Platform/_icon_pngs/` — 16 pre-rendered PNG icons
