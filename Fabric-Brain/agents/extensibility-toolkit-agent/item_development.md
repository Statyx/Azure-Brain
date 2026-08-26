# Item Development — Manifests and Feature Areas

Companion to [instructions.md](instructions.md). The spine file scaffolds, builds
and publishes a workload; this file is what puts an actual **item type** inside it.

Two parts: the manifest pair every item type needs (§1), and the seven feature
areas a workload can opt into (§2). For full code templates see
[starter_kit_reference.md](starter_kit_reference.md) and
[components_reference.md](components_reference.md); for the manifest schema itself
see [manifest_reference.md](manifest_reference.md).

---

## 1. Item Development

> **For complete code templates, view registration patterns, and the 15-step checklist, see `starter_kit_reference.md`.**

### Item Manifest Files

Each item type requires **two manifest files**:

#### Backend Manifest (`[ItemName]Item.xml`)
```xml
<ItemManifest>
  <Name>MyItem</Name>
  <DisplayName>My Custom Item</DisplayName>
  <Description>A custom Fabric item</Description>
  <SmallIcon>assets/item-icon-small.png</SmallIcon>
  <MediumIcon>assets/item-icon-medium.png</MediumIcon>
  <LargeIcon>assets/item-icon-large.png</LargeIcon>
  <!-- Optional: Enable features -->
  <SupportedInMonitoringHub>true</SupportedInMonitoringHub>
</ItemManifest>
```

#### Frontend Manifest (`[ItemName]Item.json`)
```json
{
  "name": "MyItem",
  "displayName": "My Custom Item",
  "editor": {
    "path": "/items/MyItem/MyItemItemEditor"
  },
  "icon": {
    "name": "my-item-icon"
  },
  "contextMenu": {
    "actions": ["edit", "delete", "rename"]
  }
}
```

### ItemEditor Component (Mandatory)

```tsx
import React from 'react';
import { ItemEditor } from '../../components/ItemEditor';

export const MyItemItemEditor: React.FC = () => {
  return (
    <ItemEditor
      itemType="MyItem"
      onSave={async (definition) => {
        // Save item definition to OneLake
        await saveDefinition(definition);
      }}
    >
      {/* Your custom editing UI goes here */}
      <div>
        <h2>My Custom Item Editor</h2>
        {/* Fluent UI v9 components */}
      </div>
    </ItemEditor>
  );
};
```

### Host API — Token Acquisition

```typescript
import { workloadClient } from '@ms-fabric/workload-client';

// Acquire OBO token for accessing APIs
const token = await workloadClient.auth.acquireAccessToken({
  additionalScopesToConsent: ["https://storage.azure.com/.default"]
});

// Use token to call OneLake, Fabric REST, or external APIs
const response = await fetch('https://onelake.dfs.fabric.microsoft.com/...', {
  headers: { 'Authorization': `Bearer ${token.accessToken}` }
});
```

### OneLake Storage Model

```
OneLake/
└── [WorkspaceName]/
    └── [ItemName].[ItemType]/
        ├── .pbi/                    # Hidden — Item definition & metadata
        │   ├── definition.json      # Item configuration, references
        │   └── state.json           # Runtime state
        ├── Tables/                  # Structured data (Delta/Iceberg)
        └── Files/                   # Unstructured data (any format)
```

- **Definition storage** (`.pbi/` hidden folder): metadata, config, references — NOT large data
- **Data storage** (`Tables/`, `Files/`): actual data accessible via standard OneLake paths
- **Shortcuts**: Use Shortcut API for referencing external data (single-copy promise)

---

## 2. Key Feature Areas

### 7.1 Standard Item Creation
Fabric provides a built-in creation dialog (workspace selection, naming, sensitivity labels). Your workload does NOT need to build this — it's handled by the host.

### 7.2 Frontend Entra Tokens (OBO)
The host API acquires tokens on behalf of the signed-in user. These tokens can target:
- OneLake DFS API
- Fabric REST API
- Spark Livy API
- Any Entra-protected external API

### 7.3 CRUD Item API
Standard Fabric Item REST APIs (`GET /items`, `POST /items`, `PATCH /items/{id}`, `DELETE /items/{id}`) work automatically for workload items. No custom CRUD logic needed.

### 7.4 CI/CD Support (Preview)
- **Git Integration**: Workspace items automatically serialize to Git (`.platform` + `definition.json`)
- **Deployment Pipelines**: Items move through dev → test → prod stages
- **Variable Library**: Store environment-specific values (workspace IDs, connection strings) as variables instead of hard-coded values
- No custom logic needed — automatic participation once workload is Git-integrated

### 7.5 Remote Lifecycle Notification API (Preview)
- Opt-in webhook for item CRUD events: `Created`, `Updated`, `Deleted`
- Use cases: licensing checks, infrastructure provisioning, external system sync
- Works with CI/CD — pipeline promotion triggers notifications per workspace
- Register webhook endpoint in WorkloadManifest.xml

### 7.6 Fabric Scheduler / Remote Jobs (Preview)
- Register job types in manifest
- Users schedule jobs via standard Fabric scheduling UI
- Backend receives signed request with item context + OBO token
- Job can do anything user is authorized for (OneLake, Fabric REST, external APIs)
- Results appear in standard Fabric job history / Monitoring Hub

### 7.7 iFrame Relaxation
Extended capabilities (file downloads, external API calls from frontend) available with user consent. Requires additional Entra permissions configuration.

