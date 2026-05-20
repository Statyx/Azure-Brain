# Starter Kit Reference — Fabric Extensibility Toolkit

> Source: [microsoft/fabric-extensibility-toolkit](https://github.com/microsoft/fabric-extensibility-toolkit) — Latest release: **v2026.03**

---

## 1. Item Development Pattern (4-File + Ribbon + SCSS)

Every item type lives in `Workload/app/items/[ItemName]Item/` and follows this **mandatory** file structure:

| File | Purpose |
|------|---------|
| `[ItemName]ItemDefinition.ts` | Model / data interface — serializable to JSON |
| `[ItemName]ItemEditor.tsx` | Main editor (uses `<ItemEditor>` container) |
| `[ItemName]ItemEmptyView.tsx` | First-time empty state (uses `<ItemEditorEmptyView>`) |
| `[ItemName]ItemDefaultView.tsx` | Main content view when item has data |
| `[ItemName]ItemRibbon.tsx` | Ribbon toolbar (uses `<Ribbon>` + `<RibbonToolbar>`) |
| `[ItemName]Item.scss` | Item-specific styles ONLY (never modify component styles) |

### 1.1 ItemDefinition (Model)

```typescript
export interface [ItemName]ItemDefinition {
  message?: string;
  // JSON-serializable properties only
}
```

### 1.2 ItemEditor (Container — MANDATORY)

```tsx
import { ItemEditor, ItemEditorEmptyView } from "../../components/ItemEditor";

export function [ItemName]ItemEditor(props: PageProps) {
  const EDITOR_VIEW_TYPES = { EMPTY: 'empty', DEFAULT: 'default' } as const;
  const [item, setItem] = useState<ItemWithDefinition<[ItemName]ItemDefinition>>();
  const [currentView, setCurrentView] = useState(EDITOR_VIEW_TYPES.EMPTY);

  return (
    <ItemEditor
      ribbon={<[ItemName]ItemRibbon {...ribbonProps} />}
      views={(setCurrentView) => [
        {
          name: EDITOR_VIEW_TYPES.EMPTY,
          component: (
            <ItemEditorEmptyView
              title={t('Title')}
              description={t('Description')}
              imageSrc="/assets/items/[ItemName]Item/EditorEmpty.svg"
              tasks={[{
                id: 'start', label: t('Get Started'),
                onClick: () => setCurrentView(EDITOR_VIEW_TYPES.DEFAULT),
                appearance: 'primary'
              }]}
            />
          )
        },
        {
          name: EDITOR_VIEW_TYPES.DEFAULT,
          component: <[ItemName]ItemDefaultView workloadClient={workloadClient} item={item} />
        }
      ]}
      initialView={!item?.definition?.state ? EDITOR_VIEW_TYPES.EMPTY : EDITOR_VIEW_TYPES.DEFAULT}
    />
  );
}
```

### 1.3 Ribbon (MANDATORY pattern)

```tsx
import {
  Ribbon, RibbonToolbar, RibbonAction,
  createSaveAction, createSettingsAction, createRibbonTabs
} from '../../components/ItemEditor';

export function [ItemName]ItemRibbon(props) {
  const translate = (key, fallback?) => t(key, fallback);
  const tabs = createRibbonTabs(t("ItemEditor_Ribbon_Home_Label"));
  const actions: RibbonAction[] = [
    createSaveAction(props.saveItemCallback, !props.isSaveButtonEnabled, translate),
    createSettingsAction(props.openSettingsCallback, translate),
    // Custom actions inline:
    { key: 'custom', icon: Icon, label: t('Label'), onClick: handler, testId: 'btn-id' }
  ];
  return (
    <Ribbon tabs={tabs}>
      <RibbonToolbar actions={actions} />
    </Ribbon>
  );
}
```

**Rules:**
- `homeToolbarActions` is **mandatory** — every ribbon must have a Home tab
- Always use `createSaveAction()` / `createSettingsAction()` factories — never build custom save/settings buttons
- `RibbonToolbar` auto-applies the `Tooltip` + `ToolbarButton` pattern (accessibility)
- Never create custom `<Toolbar>` or `<div className="ribbon">` layouts

### 1.4 Styling Rules

- Create `[ItemName]Item.scss` in the item folder — import as `import "./[ItemName]Item.scss"`
- Use **item-prefixed BEM** class names: `.hello-world-view`, `.data-analyzer-section-title`
- Use **Fabric design tokens**: `var(--colorBrandForeground1)`, `var(--spacingVerticalL)`, `var(--fontWeightSemibold)`
- **NEVER modify** any file in `Workload/app/components/` — component styles are shared
- **NEVER duplicate** component structural styles (`display: flex`, `flex-direction: column`) in item SCSS
- **NEVER use inline styles** (`style={{...}}`) — always use SCSS file

---

## 2. View Registration System

ItemEditor manages views via a declarative registration system.

### 2.1 Core Types

```typescript
interface RegisteredView {
  name: string;
  component: React.ReactNode;
  isDetailView?: boolean;    // Enables auto back navigation
}

interface ViewContext {
  currentView: string;
  setCurrentView: (view: string) => void;
  isDetailView: boolean;
  goBack: () => void;
  viewHistory: string[];
}

interface RegisteredNotification {
  name: string;
  component: React.ReactNode;
  showInViews?: string[];    // Filter to specific views
}
```

### 2.2 View Registration Patterns

**Static views:**
```tsx
<ItemEditor views={[{ name: 'empty', component: <EmptyView /> }, { name: 'default', component: <DefaultView /> }]} />
```

**Dynamic views (with navigation control):**
```tsx
<ItemEditor views={(setCurrentView) => [
  { name: 'empty', component: <EmptyView onStart={() => setCurrentView('default')} /> },
  { name: 'default', component: <DefaultView /> },
  { name: 'record-detail-123', component: <DetailView />, isDetailView: true }
]} />
```

**viewSetter (post-load programmatic control):**
```tsx
<ItemEditor viewSetter={(setCurrentView) => {
  // Store setCurrentView for later use (e.g., in useEffect after data loads)
  viewSetterRef.current = setCurrentView;
}} />
```

### 2.3 MessageBar (Notifications)

```tsx
<ItemEditor messageBar={[
  { name: 'unsaved', component: <MessageBar intent="warning">Unsaved changes</MessageBar>, showInViews: ['default'] }
]} />
```

### 2.4 Detail Views (L2 Drill-Down)

Use `ItemEditorDetailView` for any sub-page/drill-down. Mark with `isDetailView: true` for automatic back navigation.

```tsx
{
  name: 'record-detail-123',
  component: (
    <ItemEditorDetailView
      left={{ content: <PropertiesPanel />, title: "Properties", width: 280, collapsible: true }}
      center={{ content: <RecordEditor /> }}
      actions={[
        { key: 'save', label: 'Save', icon: Save24Regular, onClick: handleSave },
        { key: 'delete', label: 'Delete', icon: Delete24Regular, onClick: handleDelete }
      ]}
    />
  ),
  isDetailView: true
}
```

### 2.5 EDITOR_VIEW_TYPES Constants

```typescript
const EDITOR_VIEW_TYPES = { EMPTY: 'empty', DEFAULT: 'default', DETAILS: 'details' };
```

---

## 3. Layout Components API

### 3.1 ItemEditorDefaultView (Multi-Panel)

```tsx
<ItemEditorDefaultView
  left={{
    content: <ExplorerPanel />,    // Optional left panel
    title: "Explorer",
    width: 260,
    minWidth: 180,
    maxWidth: 400,
    collapsible: true,
    enableUserResize: true,
    onCollapseChange: (collapsed) => {}
  }}
  center={{
    content: <MainEditor />,       // REQUIRED center panel
    ariaLabel: "Main Content",
    className: "my-item-center"
  }}
/>
```

### 3.2 ItemEditorEmptyView (First-Time UX)

```tsx
<ItemEditorEmptyView
  title="Welcome to [Item Name]!"
  description="Get started with your new item"
  imageSrc="/assets/items/[ItemName]Item/EditorEmpty.svg"
  imageAlt="Empty state illustration"
  tasks={[
    { id: 'start', label: 'Getting Started', description: 'Learn how', onClick: handler, appearance: 'primary' },
    { id: 'import', label: 'Import Data', onClick: importHandler }
  ]}
/>
```

### 3.3 ItemSettings (Platform Flyout)

Opens via `createSettingsAction()` — automatically includes item name/description fields.

```tsx
const handleOpenSettings = async () => {
  const item_res = await callGetItem(workloadClient, item.id);
  await callOpenSettings(workloadClient, item_res.item, 'About');
};
```

### 3.4 CSS Architecture

```
ItemEditor layout:
├── .base-item-editor           (root flex container)
│   ├── .base-item-editor__ribbon    (flex-shrink: 0 — stays fixed)
│   └── .base-item-editor__content   (flex: 1, overflow-y: auto — scrolls)
```

**CRITICAL — Content Padding Rule:**
> ItemEditor panels have **ZERO padding**. Views MUST add their own padding:
> ```css
> .my-item-view {
>   padding: var(--spacingVerticalM, 12px);
>   box-sizing: border-box;
>   overflow: hidden;
> }
> ```

**Do's:**
- Use `ItemEditorDefaultView` for multi-panel layouts
- Use Fabric design tokens for spacing/colors
- Test scrolling with long content
- Implement keyboard navigation
- Save panel collapse/width preferences

**Don'ts:**
- No `overflow: scroll` on outer container (managed by ItemEditor)
- No `height: 100vh` or fixed heights
- No multiple ribbons
- No `position: absolute` inside panels
- No nested scroll containers

---

## 4. OneLakeStorageClient — Wrapper Pattern

### CORRECT — Always use `createItemWrapper()`

```typescript
const oneLakeClient = new OneLakeStorageClient(props.workloadClient);
const itemWrapper = oneLakeClient.createItemWrapper({
  id: props.item.id,
  workspaceId: props.item.workspaceId
});

await itemWrapper.writeFileAsBase64('Files/myfile.txt', base64Content);
const content = await itemWrapper.readFileAsText('Files/myfile.txt');
const fullPath = itemWrapper.getPath('Files/myfile.txt');
```

### WRONG — Never construct paths manually

```typescript
// ❌ Manual path construction is error-prone
const filePath = `${props.item.id}/Files/myfile.txt`;
await oneLakeClient.writeFileAsBase64(filePath, base64Content);
```

---

## 5. OneLakeView Control

Import from `components/OneLakeView` — **NEVER** copy from `samples/`.

```tsx
import { OneLakeView } from '../../../components/OneLakeView';

<OneLakeView
  workloadClient={props.workloadClient}
  config={{
    mode: "edit",                    // "edit" | "view"
    initialItem: { id, workspaceId, displayName },   // ALL 3 REQUIRED
    allowItemSelection: true,
    allowedItemTypes: ["Lakehouse", "Warehouse", "KQLDatabase"],
    refreshTrigger: refreshTrigger
  }}
  callbacks={{
    onFileSelected: (fileName, oneLakeLink) => {},
    onTableSelected: (tableName, oneLakeLink) => {},
    onItemChanged: (item) => {}
  }}
/>
```

**Common Issues:**
- Empty control → missing `initialItem` (need all 3 fields: `id`, `workspaceId`, `displayName`)
- No add button → set `allowItemSelection: true`
- Permission errors → need `OneLake.Read.All` scope

---

## 6. WizardControl

```tsx
import { WizardControl } from '../../components/Wizard';

<WizardControl
  steps={[
    {
      id: 'step1', title: 'Basic Info', description: 'Enter details',
      component: StepComponent,    // React.ComponentType<WizardStepProps>
      validate: () => boolean,     // Gate before advancing
      onEnter: () => {},
      onExit: () => {}
    }
  ]}
  initialStepId="step1"
  onStepChange={(stepId) => {}}
  onComplete={() => {}}
  onCancel={() => {}}
  canFinish={true}
  initialContext={{}}
  showNavigation={true}
  allowStepNavigation={true}
/>
```

**WizardStepProps** (injected into each step component):
```typescript
interface WizardStepProps {
  stepId: string;
  stepIndex: number;
  context: any;
  onNext: () => void;
  onPrevious: () => void;
  onGoToStep: (stepId: string) => void;
  isFirstStep: boolean;
  isLastStep: boolean;
}
```

**Layout:** Steps Panel (left, 180px desktop / 140px mobile) + Content Panel (right) + Footer  
**Best practice:** 3-5 steps ideal, descriptive titles, validate before navigation  
**CSS:** BEM `.wizard-control`, responsive breakpoint at 768px

---

## 7. Development Guidelines (9 Rules)

| # | Rule | Detail |
|---|------|--------|
| 1 | **PascalCase naming** | All item files, components, interfaces |
| 2 | **Error handling** | Try/catch on all async operations, user-facing error messages |
| 3 | **Fluent UI v9 ONLY** | Import from `@fluentui/react-components` — **NEVER** `@fluentui/react` (v8) |
| 4 | **Ribbon pattern** | Always use `Ribbon` + `RibbonToolbar` + factory functions |
| 5 | **Tooltip + ToolbarButton** | Handled automatically by `RibbonToolbar` — don't implement manually |
| 6 | **Content padding** | Panels have ZERO padding — views add `padding: var(--spacingVerticalM, 12px)` + `box-sizing: border-box` |
| 7 | **Redux Toolkit** | For complex state management across item editors |
| 8 | **Lazy loading** | Code-split item editors for faster initial load |
| 9 | **Item loading optimization** | Check `pageContext.itemObjectId === item.id` before reloading to prevent unnecessary API calls/UI flicker |

---

## 8. Manifest Configuration

### File Locations

```
Workload/Manifest/
├── Product.json                              # Workload-level frontend config
├── WorkloadManifest.xml                      # Workload-level backend config  
├── *.xsd                                     # Schema validation files
├── assets/
│   ├── images/[ItemName]Item-icon.png        # Item icon (24×24 PNG)
│   └── locales/en-US/translations.json       # Manifest translations
└── items/[ItemName]Item/
    ├── [ItemName]Item.json                   # Item frontend manifest
    └── [ItemName]Item.xml                    # Item backend manifest (uses {{WORKLOAD_NAME}})
```

### Item XML Manifest

```xml
<?xml version='1.0' encoding='utf-8'?>
<ItemManifestConfiguration SchemaVersion="2.0.0">
  <Item TypeName="{{WORKLOAD_NAME}}.[ItemName]" Category="Data">
    <Workload WorkloadName="{{WORKLOAD_NAME}}" />
  </Item>
</ItemManifestConfiguration>
```

### Item JSON Manifest

```json
{
  "name": "[ItemName]",
  "version": "1.100",
  "displayName": "[ItemName]Item_DisplayName",
  "displayNamePlural": "[ItemName]Item_DisplayName_Plural",
  "editor": { "path": "/[ItemName]Item-editor" },
  "icon": { "name": "assets/images/[ItemName]Item-icon.png" },
  "contextMenuItems": [],
  "supportedInMonitoringHub": true,
  "supportedInDatahubL1": true,
  "itemSettings": { "getItemSettings": { "action": "getItemSettings" } },
  "createItemDialogConfig": {
    "onCreationFailure": { "action": "item.onCreationFailure" },
    "onCreationSuccess": { "action": "item.onCreationSuccess" }
  }
}
```

### Product.json — CRITICAL for Item Visibility

**Both arrays MUST be updated** when adding a new item:

```json
{
  "createExperience": {
    "cards": [
      {
        "title": "[ItemName]Item_DisplayName",
        "description": "[ItemName]Item_Description",
        "icon": { "name": "assets/images/[ItemName]Item-icon.png" },
        "availableIn": ["home", "create-hub", "workspace-plus-new"],
        "itemType": "[ItemName]",
        "createItemDialogConfig": { ... }
      }
    ]
  },
  "homePage": {
    "recommendedItemTypes": ["HelloWorld", "[ItemName]"]
  }
}
```

### Localization (Two Separate Files!)

| File | Purpose | Used By |
|------|---------|---------|
| `Workload/Manifest/assets/locales/en-US/translations.json` | Manifest strings | Product.json, [ItemName]Item.json |
| `Workload/app/assets/locales/en-US/translation.json` | React component strings | `useTranslation()` hook |

**Never mix these up** — each serves a different build-time purpose.

### Environment Variables

After creating a new item, update `ITEM_NAMES` in **all** `.env.*` files:

```bash
# .env.dev, .env.test, .env.prod
ITEM_NAMES=HelloWorld,[ItemName]
```

---

## 9. Project Structure (Full)

```
project-root/
├── .ai/
│   ├── commands/
│   │   ├── item/createItem.md            # AI procedure: create new item (15-step)
│   │   ├── item/deleteItem.md            # AI procedure: delete item
│   │   └── workload/
│   │       ├── runWorkload.md            # AI procedure: start dev environment
│   │       ├── updateWorkload.md         # AI procedure: update workload
│   │       ├── deployWorkload.md         # AI procedure: deploy to Azure
│   │       └── publishworkload.md        # AI procedure: publish to Workload Hub
│   └── context/
│       ├── fabric-workload.md            # Deep workload dev context (item patterns, components, guidelines)
│       └── fabric.md                     # General Fabric platform context
├── .env.dev / .env.test / .env.prod      # ALL committed — template vars for build
├── Workload/
│   ├── Manifest/
│   │   ├── Product.json
│   │   ├── WorkloadManifest.xml
│   │   ├── *.xsd                         # Schema validation
│   │   ├── assets/
│   │   │   ├── images/                   # Item icons
│   │   │   └── locales/en-US/translations.json
│   │   └── items/[ItemName]Item/
│   │       ├── [ItemName]Item.json
│   │       └── [ItemName]Item.xml
│   └── app/
│       ├── clients/                      # API wrappers (OneLakeStorageClient, etc.)
│       ├── controller/                   # SDK abstractions (ItemCRUDController, SettingsController, NotificationController)
│       ├── components/                   # DO NOT MODIFY — shared UX components
│       │   ├── ItemEditor/               # ItemEditor, Ribbon, RibbonToolbar, views
│       │   ├── OneLakeView/              # OneLake file/table browser
│       │   └── Wizard/                   # Multi-step wizard
│       ├── items/
│       │   └── [ItemName]Item/           # Your item implementation (4 files + ribbon + scss)
│       ├── assets/
│       │   ├── items/[ItemName]Item/EditorEmpty.svg
│       │   └── locales/en-US/translation.json
│       ├── playground/                   # Playground components (ApiVariableLibrary, etc.)
│       ├── samples/views/                # Reference samples — DO NOT import in production
│       ├── App.tsx                        # Route registration
│       ├── constants.ts
│       ├── theme.tsx
│       └── index.ts / index.ui.tsx / index.worker.ts
├── build/                                # NOT committed
│   ├── Frontend/                         # Compiled frontend
│   ├── DevGateway/                       # workload-dev-mode.json
│   └── Manifest/                         # temp/ + .nupkg
├── scripts/
│   ├── Setup/
│   │   ├── SetupWorkload.ps1             # Initialize workload name
│   │   ├── SetupDevEnvironment.ps1       # Create Entra app + configure .env
│   │   ├── CreateDevAADApp.ps1           # Entra app registration
│   │   ├── CreateNewItem.ps1             # Scaffold new item type
│   │   └── remote/                       # Remote hosting backend setup (v2026.03)
│   ├── Run/
│   │   ├── StartDevServer.ps1            # Start frontend dev server
│   │   └── StartDevGateway.ps1           # Start backend emulator
│   ├── Build/
│   │   ├── BuildFrontend.ps1 [-Environment dev]
│   │   ├── BuildManifestPackage.ps1 [-Environment prod]
│   │   └── BuildAll.ps1 [-Environment prod]
│   └── Deploy/
│       ├── DeployToAzureWebApp.ps1       # Deploy to Azure Web App
│       └── SwitchToRemoteHosting.ps1     # Switch to remote hosting (v2026.03)
└── docs/
    ├── components/
    │   ├── ItemEditor.md (+ sub-docs)
    │   ├── OneLakeView.md
    │   └── Wizard.md
    ├── items/HelloWorldItem/
    ├── ReleaseNotes/
    ├── Project_Setup.md
    └── Project_Structure.md
```

---

## 10. Scripts Reference

### Setup Phase

| Script | Purpose | Parameters |
|--------|---------|------------|
| `scripts/Setup/SetupWorkload.ps1` | Initialize workload name and config | `-WorkloadName "Org.MyWorkload"` |
| `scripts/Setup/SetupDevEnvironment.ps1` | Create Entra app, configure .env files | |
| `scripts/Setup/CreateDevAADApp.ps1` | Create Entra app registration | `-HostingType "Remote"` (for remote hosting) |
| `scripts/Setup/CreateNewItem.ps1` | Scaffold a new item type | Prompts for item name |

### Development Phase

| Script | Purpose | Notes |
|--------|---------|-------|
| `scripts/Run/StartDevGateway.ps1` | Start backend emulator | Auto-builds manifest, handles Azure auth |
| `scripts/Run/StartDevServer.ps1` | Start frontend dev server | Hot reload, auto-opens browser |

**Startup Order:** DevGateway FIRST → then DevServer (in second terminal)

### Build Phase

| Script | Purpose | Parameters |
|--------|---------|------------|
| `scripts/Build/BuildFrontend.ps1` | Build frontend only | `-Environment dev\|test\|prod` |
| `scripts/Build/BuildManifestPackage.ps1` | Create NuGet package | `-Environment dev\|test\|prod` |
| `scripts/Build/BuildAll.ps1` | Build everything | `-Environment dev\|test\|prod` |

### Deploy Phase

| Script | Purpose | Notes |
|--------|---------|-------|
| `scripts/Deploy/DeployToAzureWebApp.ps1` | Deploy to Azure Web App | Production deployment |
| `scripts/Deploy/SwitchToRemoteHosting.ps1` | Switch to remote hosting | v2026.03 — production-ready |

---

## 11. Remote Workload Hosting (v2026.03 — Production Ready)

Switch from DevGateway (local) to remote Azure hosting for production.

### Migration Steps

1. Create Entra app with remote hosting:
   ```powershell
   CreateDevAADApp.ps1 -HostingType "Remote" -ApplicationName <name> -WorkloadName <name> -TenantId <id>
   ```
2. Switch hosting:
   ```powershell
   SwitchToRemoteHosting.ps1
   ```
3. Configure and deploy

### Remote Backend Infrastructure (`scripts/Setup/remote/`)

| Component | Purpose |
|-----------|---------|
| **Item CRUD API** | Create/Read/Update/Delete item operations |
| **Endpoint Resolution** | Route requests to correct backend |
| **Authentication Service** | Validate tokens and manage auth |
| **Token Exchange** | OBO token exchange for downstream APIs |
| **OneLake Client Service** | Server-side OneLake operations |
| **Permissions API** | Manage item permissions |

---

## 12. Job Scheduling Framework (v2026.03)

### Setup

```powershell
CreateJob.ps1    # Configure job type for your item
```

### Components

| Component | Purpose |
|-----------|---------|
| **Job Scheduler Controller** | TypeScript controller managing job lifecycle |
| **Job Instance API** | Create, track, and manage job instances |
| **Job Logging** | Logs stored in OneLake |
| **Job State Management** | Track job progress and status |

### Integration Points

- Context menu actions (right-click → Run Job)
- Ribbon actions (toolbar button)
- Job details pane (view results)
- Monitoring Hub integration
- HelloWorldItem reference implementation

---

## 13. Item Lifecycle (v2026.03)

### Soft Delete + Restore

Items support soft delete with restore capability:
- Lifecycle operation notifications
- Backend receives delete/restore events
- Supports undo in UI

---

## 14. Routing

Add to `Workload/app/App.tsx`:

```tsx
import { [ItemName]ItemEditor } from "./items/[ItemName]Item/[ItemName]ItemEditor";

<Route path="/[ItemName]Item-editor/:itemObjectId">
  <[ItemName]ItemEditor {...pageProps} />
</Route>
```

Route path **must match** `editor.path` in the item JSON manifest.

---

## 15. Item Loading Optimization

Prevent unnecessary reloads by checking item ID before refetching:

```typescript
useEffect(() => {
  if (pageContext.itemObjectId && pageContext.itemObjectId !== item?.id) {
    loadDataFromUrl(pageContext, pathname);
  }
}, [pageContext, pathname]);
```

This prevents redundant API calls and UI flicker during re-renders.

---

## 16. Quick Checklist (New Item)

### Implementation Files (`Workload/app/items/[ItemName]Item/`)

- [ ] `[ItemName]ItemDefinition.ts`
- [ ] `[ItemName]ItemEditor.tsx` — uses `<ItemEditor>`
- [ ] `[ItemName]ItemEmptyView.tsx` — uses `<ItemEditorEmptyView>`
- [ ] `[ItemName]ItemDefaultView.tsx`
- [ ] `[ItemName]ItemRibbon.tsx` — uses `Ribbon` + `RibbonToolbar`
- [ ] `[ItemName]Item.scss`

### Manifest Files

- [ ] `Manifest/items/[ItemName]Item/[ItemName]Item.json`
- [ ] `Manifest/items/[ItemName]Item/[ItemName]Item.xml`

### Product Configuration

- [ ] **CRITICAL** — `createExperience.cards` entry in `Product.json`
- [ ] **CRITICAL** — `recommendedItemTypes` entry in `Product.json`
- [ ] `itemType` matches JSON manifest `name` field exactly

### Assets

- [ ] `Manifest/assets/images/[ItemName]Item-icon.png` (24×24 PNG)
- [ ] `app/assets/items/[ItemName]Item/EditorEmpty.svg`
- [ ] Manifest translations (`Manifest/assets/locales/en-US/translations.json`)
- [ ] App translations (`app/assets/locales/en-US/translation.json`)

### Code Integration

- [ ] Route in `App.tsx` matching `editor.path`
- [ ] `ITEM_NAMES` updated in `.env.dev`, `.env.test`, `.env.prod`

### Verification

- [ ] `<ItemEditor>` used (no custom layouts)
- [ ] `Ribbon` + `RibbonToolbar` used (no custom ribbons)
- [ ] SCSS file contains only item-specific styles
- [ ] No modifications to `components/` directory
- [ ] Version "1.100" (match HelloWorld)

---

## 17. AI Commands (.ai/ Folder)

The repo includes pre-built AI procedures in `.ai/commands/`:

| Command | File | Purpose |
|---------|------|---------|
| **Create Item** | `.ai/commands/item/createItem.md` | 15-step procedure to create a new item type |
| **Delete Item** | `.ai/commands/item/deleteItem.md` | Procedure to safely remove an item type |
| **Run Workload** | `.ai/commands/workload/runWorkload.md` | Start DevGateway + DevServer |
| **Update Workload** | `.ai/commands/workload/updateWorkload.md` | Apply changes and rebuild |
| **Deploy Workload** | `.ai/commands/workload/deployWorkload.md` | Deploy to Azure Web App |
| **Publish Workload** | `.ai/commands/workload/publishworkload.md` | Publish to Workload Hub |

Context files in `.ai/context/`:
- `fabric-workload.md` — Deep workload development knowledge (item patterns, components, guidelines, deployment)
- `fabric.md` — General Fabric platform context

---

## 18. Quick Start (HelloWorld Clone)

Instead of creating empty files, clone HelloWorld:

```bash
# 1. Copy implementation files
cp -r Workload/app/items/HelloWorldItem Workload/app/items/[ItemName]Item

# 2. Copy manifest files
cp -r Workload/Manifest/items/HelloWorldItem Workload/Manifest/items/[ItemName]Item

# 3. Find & replace in all copied files:
HelloWorld → [ItemName]
HelloWorldItem → [ItemName]Item
HelloWorldItemDefinition → [ItemName]ItemDefinition
HelloWorldItemEditor → [ItemName]ItemEditor
HelloWorldItemEmptyView → [ItemName]ItemEmptyView
HelloWorldItemDefaultView → [ItemName]ItemDefaultView
HelloWorldItemRibbon → [ItemName]ItemRibbon

# 4. Rename files to match new item name
# 5. Update App.tsx, Product.json, .env.*, translation files
```
