# Visual Presentation — Badges, Screenshots, Diagrams

## Badges

### shields.io Quick Reference

Base URL: `https://img.shields.io/badge/{label}-{message}-{color}`

**Styles:** `?style=flat` | `flat-square` | `for-the-badge` | `plastic`

### Dynamic Badges (auto-update from GitHub)

```markdown
<!-- Repository metadata -->
![License](https://img.shields.io/github/license/{owner}/{repo}?style=for-the-badge)
![Stars](https://img.shields.io/github/stars/{owner}/{repo}?style=for-the-badge)
![Forks](https://img.shields.io/github/forks/{owner}/{repo}?style=for-the-badge)
![Issues](https://img.shields.io/github/issues/{owner}/{repo}?style=for-the-badge)
![Last Commit](https://img.shields.io/github/last-commit/{owner}/{repo}?style=for-the-badge)

<!-- CI/CD -->
![Build](https://img.shields.io/github/actions/workflow/status/{owner}/{repo}/{workflow}.yml?style=for-the-badge)
![Coverage](https://img.shields.io/codecov/c/github/{owner}/{repo}?style=for-the-badge)

<!-- Package registries -->
![PyPI](https://img.shields.io/pypi/v/{package}?style=for-the-badge&logo=pypi)
![npm](https://img.shields.io/npm/v/{package}?style=for-the-badge&logo=npm)
![NuGet](https://img.shields.io/nuget/v/{package}?style=for-the-badge&logo=nuget)
```

### Static Badges (custom)

```markdown
<!-- Technology -->
![Python](https://img.shields.io/badge/python-3.10+-blue?style=for-the-badge&logo=python&logoColor=white)
![TypeScript](https://img.shields.io/badge/TypeScript-5.x-3178C6?style=for-the-badge&logo=typescript&logoColor=white)
![Fabric](https://img.shields.io/badge/Microsoft_Fabric-REST_API-742774?style=for-the-badge&logo=microsoft&logoColor=white)
![Power BI](https://img.shields.io/badge/Power_BI-F2C811?style=for-the-badge&logo=powerbi&logoColor=black)

<!-- Status -->
![Active](https://img.shields.io/badge/status-active-brightgreen?style=for-the-badge)
![WIP](https://img.shields.io/badge/status-WIP-yellow?style=for-the-badge)
![Archived](https://img.shields.io/badge/status-archived-lightgrey?style=for-the-badge)
![Demo](https://img.shields.io/badge/type-demo-blue?style=for-the-badge)

<!-- Counts -->
![Agents](https://img.shields.io/badge/agents-19-blue?style=for-the-badge&logo=github)
![Knowledge](https://img.shields.io/badge/knowledge_files-19-green?style=for-the-badge)
```

### Badge Placement Rules
- Place on the line **immediately after** the title and description
- Group by category: status → tech → metrics → CI
- Maximum 6-8 badges — more becomes visual noise
- Use consistent style across the same README

---

## Screenshots

### Capture Guidelines
| Rule | Details |
|------|---------|
| Resolution | Capture at 1x or 2x, resize to ≤ 800px wide |
| Format | PNG for UI, JPEG for photos, WebP for size optimization |
| Annotations | Use red rectangles/arrows to highlight key areas |
| Naming | `feature-name-screenshot.png` (kebab-case, descriptive) |
| Storage | `docs/images/` or `assets/` — never repo root |

### Embedding

```markdown
<!-- Simple -->
![Dashboard Screenshot](docs/images/dashboard-overview.png)

<!-- With link to full-size -->
[![Dashboard](docs/images/dashboard-thumb.png)](docs/images/dashboard-full.png)

<!-- Centered (GitHub supports HTML) -->
<p align="center">
  <img src="docs/images/dashboard-overview.png" alt="Dashboard" width="700">
</p>

<!-- Side by side -->
<p align="center">
  <img src="docs/images/before.png" alt="Before" width="400">
  <img src="docs/images/after.png" alt="After" width="400">
</p>
```

---

## Architecture Diagrams (Mermaid)

GitHub renders Mermaid natively — no image files needed.

### Flowchart (most common)

````markdown
```mermaid
graph LR
    A[Data Source] -->|Ingest| B[Lakehouse]
    B -->|Transform| C[Semantic Model]
    C -->|Visualize| D[Power BI Report]
    C -->|Query| E[Data Agent]
    
    style A fill:#e1f5fe
    style D fill:#c8e6c9
    style E fill:#fff3e0
```
````

### Sequence Diagram (API flows)

````markdown
```mermaid
sequenceDiagram
    participant User
    participant CLI as Analyzer CLI
    participant API as Fabric API
    participant Agent as Data Agent

    User->>CLI: python -m analyzer run
    CLI->>API: GET /semantic-model/definition
    API-->>CLI: TMDL schema
    CLI->>Agent: POST /aiassistant/openai
    Agent-->>CLI: DAX query + answer
    CLI->>CLI: Grade & score
    CLI-->>User: Report (93% pass)
```
````

### Entity Relationship (data models)

````markdown
```mermaid
erDiagram
    CUSTOMERS ||--o{ ORDERS : places
    ORDERS ||--|{ ORDER_LINES : contains
    PRODUCTS ||--o{ ORDER_LINES : "is in"
    CAMPAIGNS ||--o{ ORDERS : "attributed to"
```
````

### Subgraph Layout (platform architecture)

````markdown
```mermaid
graph TD
    subgraph Ingestion
        A[EventHub] --> B[EventStream]
    end
    subgraph Storage
        B --> C[Lakehouse]
        C --> D[Delta Tables]
    end
    subgraph Analytics
        D --> E[Semantic Model]
        E --> F[Report]
        E --> G[Data Agent]
    end
    subgraph Operations
        H[Monitoring] -.-> C
        H -.-> E
    end
```
````

---

## Demo GIFs & Videos

### GIF Recording Tools
| Tool | Platform | Notes |
|------|----------|-------|
| ScreenToGif | Windows | Best for short UI demos |
| LICEcap | Windows/Mac | Lightweight |
| Peek | Linux | Simple recorder |
| asciinema | Terminal | For CLI tools (embed or convert to GIF) |

### GIF Best Practices
- **Duration**: 15-30 seconds max
- **Size**: < 10 MB (GitHub will reject > 25 MB)
- **FPS**: 10-15 fps is sufficient
- **Resolution**: 800px wide max
- **Loop**: Should loop seamlessly
- **Speed**: Real-time or 1.5x — never faster

### Embedding Videos

```markdown
<!-- YouTube embed (thumbnail + link) -->
[![Demo Video](https://img.youtube.com/vi/VIDEO_ID/maxresdefault.jpg)](https://www.youtube.com/watch?v=VIDEO_ID)

<!-- GIF -->
<p align="center">
  <img src="docs/images/demo.gif" alt="Demo" width="700">
</p>
```

---

## Color Reference for Badges & Diagrams

| Use Case | Color | Hex |
|----------|-------|-----|
| Success / Active | brightgreen | `#4c1` |
| Warning / WIP | yellow | `#dfb317` |
| Error / Deprecated | red | `#e05d44` |
| Info / Neutral | blue | `#007ec6` |
| Microsoft Fabric | purple | `#742774` |
| Power BI | gold | `#F2C811` |
| Python | blue | `#3776AB` |
| TypeScript | blue | `#3178C6` |
