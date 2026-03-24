# Architecture — Fabric Extensibility Toolkit

## 4-Component Model

The Fabric Extensibility Toolkit architecture consists of four interconnected components:

### 1. Fabric Frontend (Host)

The Fabric portal acts as the **host** for workloads. It:
- Loads the workload web app inside an **iFrame**
- Provides a **Host API** for bidirectional communication
- Manages navigation, breadcrumbs, and workspace context
- Acquires **Entra tokens** on behalf of the user and passes them to the workload
- Handles the standard item creation dialog (workspace selection, naming, sensitivity labels)
- Controls the item context menu, ribbon, and lifecycle events

### 2. Workload Web App (Your Code)

A React/TypeScript application that you build and host:
- Uses `@ms-fabric/workload-client` npm package to communicate with the host
- Built with **Fluent UI v9** components for native look-and-feel
- Runs inside the Fabric iFrame — no separate URL for end users
- Handles item editing, visualization, and custom business logic
- Can call external APIs using OBO tokens from the host

**Key constraint**: The workload is a **frontend-only** application from Fabric's perspective. All backend logic is either:
- Handled by Fabric APIs (item CRUD, OneLake)
- Handled by your own hosted backend (external API calls via OBO tokens)
- Handled by DevGateway during development (emulates Fabric backend locally)

### 3. Fabric Service & Public APIs

Fabric APIs that work automatically with workload items:
- **Item CRUD**: `GET/POST/PATCH/DELETE /items` — standard Fabric Item REST APIs
- **OneLake DFS**: `https://onelake.dfs.fabric.microsoft.com/` — file and table storage
- **Content Management**: Item definitions stored in OneLake hidden folder
- **Sharing & Permissions**: Standard Fabric RBAC applies to workload items
- **Monitoring Hub**: Workload jobs appear in standard monitoring

### 4. Microsoft Entra (Authentication)

OAuth 2.0 On-Behalf-Of (OBO) flow:
```
User → Fabric Portal → Entra Token (user context)
                     → OBO Token → OneLake DFS
                     → OBO Token → Fabric REST API
                     → OBO Token → Spark Livy API
                     → OBO Token → Your External API
```

**Entra App Registration required** with:
- Application (client) ID
- Redirect URIs for the Fabric portal
- API permissions for OneLake, Fabric, and any external services
- OBO token exchange configuration

---

## End-to-End Flow

```
1. User opens Fabric portal, navigates to workspace
2. User clicks "New" → selects workload item type
3. Fabric shows standard creation dialog (name, workspace, sensitivity)
4. After creation, Fabric loads workload iFrame
5. Host API sends item context (workspaceId, itemId, itemType)
6. Host acquires Entra OBO token
7. Workload renders ItemEditor with custom UI
8. User edits → workload saves definition to OneLake (.pbi/ hidden folder)
9. User triggers action → workload calls APIs with OBO token
10. Data stored in OneLake Tables/ or Files/ folders
11. Job results appear in Fabric Monitoring Hub
```

---

## Item Lifecycle

### Creation
```
Fabric creation dialog → Item registered in Fabric metadata
                       → OneLake folder created: [WorkspaceName]/[ItemName].[ItemType]/
                       → .pbi/ hidden folder initialized
                       → ItemEditor loaded in iFrame
```

### Editing
```
User opens item → Fabric loads iFrame → Host sends context
                → Workload reads definition from .pbi/ folder
                → User modifies → Workload saves back to .pbi/ folder
```

### Deletion
```
User deletes item → Fabric removes metadata
                  → OneLake folder deleted
                  → Remote Lifecycle notification (if opt-in) → Deleted webhook
```

### Sharing
Standard Fabric sharing model applies:
- Workspace roles (Admin, Member, Contributor, Viewer)
- Item-level sharing via Fabric UI
- Sensitivity labels inherited from workspace

---

## OneLake Storage Architecture

### Item Definition vs Item Data

```
OneLake/
└── [WorkspaceName]/
    └── [ItemName].[ItemType]/
        │
        ├── .pbi/                           # HIDDEN — Definition storage
        │   ├── definition.json             # Item configuration
        │   ├── state.json                  # Runtime state
        │   └── [other metadata files]      # Custom metadata
        │
        ├── Tables/                         # VISIBLE — Structured data
        │   └── [DeltaTable]/               # Delta Lake format
        │       ├── _delta_log/
        │       └── part-*.parquet
        │
        └── Files/                          # VISIBLE — Unstructured data
            └── [any files]                 # Any format
```

**Rules:**
- `.pbi/` hidden folder: metadata, config, references, small state — NOT large datasets
- `Tables/`: structured data in Delta Lake or Iceberg format — queryable via SQL endpoint
- `Files/`: unstructured data (images, documents, raw files)
- **Shortcuts**: Reference external data without copying — use Shortcut API

### Storage Access Patterns

| Access Context | Method | Authentication |
|---------------|--------|----------------|
| Frontend (iFrame) | Host API → `acquireAccessToken()` → OneLake DFS | OBO token |
| Scheduled job | Fabric Scheduler → OBO token in request | Signed request + OBO |
| External app | Direct OneLake DFS API | Service principal or user token |
| Fabric UI | Standard item browsing | User session |

---

## Authentication Deep Dive

### Token Flow

```
┌─────────┐     ┌──────────┐     ┌──────────┐     ┌──────────┐
│  User    │────►│  Fabric  │────►│  Entra   │────►│ OneLake  │
│ Browser  │     │  Portal  │     │  ID      │     │ or API   │
└─────────┘     └──────────┘     └──────────┘     └──────────┘
                     │                 │
                     │  1. User signs  │
                     │     into Fabric │
                     │                 │
                     │  2. Fabric gets │
                     │     user token  │
                     │                 │
                     ▼                 │
              ┌──────────┐            │
              │ Workload │            │
              │ iFrame   │            │
              └──────┬───┘            │
                     │                │
                     │  3. Workload   │
                     │     calls Host │
                     │     API for    │
                     │     OBO token  │
                     │                │
                     │  4. Host does  │
                     │     OBO exchange│
                     │     with Entra │
                     │                │
                     │  5. Workload   │
                     │     uses OBO   │
                     │     token to   │
                     │     call APIs  │
                     └────────────────┘
```

### Token Scopes

| Target API | Scope |
|-----------|-------|
| OneLake DFS | `https://storage.azure.com/.default` |
| Fabric REST API | `https://api.fabric.microsoft.com/.default` |
| Spark Livy | `https://api.fabric.microsoft.com/.default` (same) |
| Custom external API | Your API's App ID URI + `/.default` |

### iFrame Relaxation

By default, the workload iFrame has restricted capabilities. With **iFrame relaxation** (requires user consent + Entra config):
- File downloads from the iFrame
- Direct external API calls from frontend
- Additional browser capabilities

---

## Workload Examples

The Extensibility Toolkit enables building diverse workload types:

| Workload Type | Description | Example |
|--------------|-------------|---------|
| **Data Application** | Custom data processing UI | ETL pipeline builder, data quality manager |
| **Data Store** | Custom storage integration | Time-series DB connector, graph DB viewer |
| **Data Visualization** | Custom analytical views | Domain-specific dashboards, 3D visualizers |
| **Fabric Customization** | Extended Fabric capabilities | Custom governance tools, audit dashboards |
| **Package Installer** | Turnkey solution deployment | Industry vertical accelerators |
| **OneLake Editor** | Custom data editing | No-code data entry forms, content editor |
