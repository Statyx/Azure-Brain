# Components Reference — Fabric Extensibility Toolkit

> Source: Starter Kit component docs (`docs/components/`) and `.ai/context/fabric-workload.md`

## Component Architecture

```
Foundation Layer     →  Specialized Layer         →  Extensible Layer
(Fluent UI v9)          (Fabric Toolkit Components)   (Your Item Code)

Button, Input,         ItemEditor (MANDATORY),      [ItemName]ItemEditor,
Text, Card,            Ribbon + RibbonToolbar,       [ItemName]ItemDefaultView,
Dialog, Menu           ItemEditorDefaultView,        [ItemName]ItemEmptyView,
                       ItemEditorDetailView,         [ItemName]ItemRibbon
                       ItemEditorEmptyView,
                       OneLakeView,
                       WizardControl
```

**Rules:**
- Use Fluent UI v9 (`@fluentui/react-components`) — **NEVER** v8 (`@fluentui/react`)
- Support all themes (light / dark / high contrast)
- **NEVER modify** files in `Workload/app/components/` — they are shared across all items
- All item-specific styles go in `[ItemName]Item.scss` in your item folder

---

## 1. ItemEditor (MANDATORY)

**Location**: `Workload/app/components/ItemEditor/ItemEditor.tsx`  
**Sub-docs**: `docs/components/ItemEditor/` (README, Ribbon, RibbonToolbar, DefaultView, DetailView, EmptyView, Architecture, Implementation, QuickReference)

Every item editor **must** use `<ItemEditor>` as the root container. It provides:
- Fixed ribbon + scrollable content layout
- View registration system with navigation history
- Automatic loading state handling
- MessageBar notification slots
- Full-height iFrame rendering

### Props API

```typescript
interface ItemEditorPropsWithViews {
  ribbon: React.ReactNode;                          // Ribbon component (fixed at top)
  views: RegisteredView[] | ((setCurrentView: (view: string) => void) => RegisteredView[]);
  initialView: string;                              // Starting view name
  viewSetter?: (setCurrentView: (view: string) => void) => void;  // Post-load programmatic control
  messageBar?: RegisteredNotification[];            // Notification bar slots
  onViewChange?: (view: string) => void;            // View change callback
  className?: string;
  contentClassName?: string;
}
```

### Core Types

```typescript
interface RegisteredView {
  name: string;
  component: React.ReactNode;
  isDetailView?: boolean;          // true → enables automatic back navigation
}

interface RegisteredNotification {
  name: string;
  component: React.ReactNode;
  showInViews?: string[];          // Only show in specific views
}

interface ViewContext {
  currentView: string;
  setCurrentView: (view: string) => void;
  isDetailView: boolean;
  goBack: () => void;
  viewHistory: string[];
}

const EDITOR_VIEW_TYPES = { EMPTY: 'empty', DEFAULT: 'default', DETAILS: 'details' };
```

### Usage Pattern (Actual Starter Kit)

```tsx
import { ItemEditor, ItemEditorEmptyView } from "../../components/ItemEditor";

<ItemEditor
  ribbon={<MyItemRibbon {...ribbonProps} />}
  views={(setCurrentView) => [
    {
      name: EDITOR_VIEW_TYPES.EMPTY,
      component: (
        <ItemEditorEmptyView
          title={t('Welcome')}
          description={t('Get started')}
          imageSrc="/assets/items/MyItem/EditorEmpty.svg"
          tasks={[{ id: 'start', label: t('Start'), onClick: () => setCurrentView('default'), appearance: 'primary' }]}
        />
      )
    },
    {
      name: EDITOR_VIEW_TYPES.DEFAULT,
      component: <MyItemDefaultView workloadClient={workloadClient} item={item} />
    },
    {
      name: 'record-detail',
      component: <ItemEditorDetailView left={{...}} center={{...}} actions={[...]} />,
      isDetailView: true  // ← Enables automatic back navigation
    }
  ]}
  initialView={!item?.definition?.state ? EDITOR_VIEW_TYPES.EMPTY : EDITOR_VIEW_TYPES.DEFAULT}
  messageBar={[
    { name: 'warning', component: <MessageBar intent="warning">Unsaved</MessageBar>, showInViews: ['default'] }
  ]}
/>
```

### CSS Architecture

```
.base-item-editor                    (root flex column)
├── .base-item-editor__ribbon        (flex-shrink: 0 — fixed at top)
└── .base-item-editor__content       (flex: 1, overflow-y: auto — scrolls)
```

**CRITICAL — Content Padding Rule:**  
ItemEditor panels have **ZERO padding**. Views MUST add their own:
```css
.my-item-view {
  padding: var(--spacingVerticalM, 12px);
  box-sizing: border-box;
  overflow: hidden;
}
```

### Do's and Don'ts

| Do | Don't |
|----|-------|
| Use `<ItemEditor>` as root container | Create custom `<Stack>` / `<div>` layouts |
| Register views via `views` prop | Use manual if/else in children |
| Use `initialView` for starting view | Import or use `ItemEditorLoadingView` |
| Use Fabric design tokens | Hard-code colors, spacing, fonts |
| Test scrolling with long content | Set `overflow: scroll` on outer container |
| Implement keyboard navigation | Use `height: 100vh` or fixed heights |
| Use `ItemEditorDefaultView` for multi-panel | Use `position: absolute` inside panels |

---

## 2. Ribbon + RibbonToolbar (MANDATORY)

**Location**: `Workload/app/components/ItemEditor/`

### Imports

```typescript
import {
  Ribbon, RibbonToolbar, RibbonAction,
  createSaveAction, createSettingsAction, createRibbonTabs
} from '../../components/ItemEditor';
```

### Usage Pattern

```tsx
export function MyItemRibbon(props: MyItemRibbonProps) {
  const translate = (key: string, fallback?: string) => t(key, fallback);

  // MANDATORY: createRibbonTabs ensures Home tab is always present
  const tabs = createRibbonTabs(
    t("ItemEditor_Ribbon_Home_Label")
    // Optional extra tabs as second parameter
  );

  const actions: RibbonAction[] = [
    // STANDARD FACTORIES (use these, don't rebuild):
    createSaveAction(props.saveItemCallback, !props.isSaveButtonEnabled, translate),
    createSettingsAction(props.openSettingsCallback, translate),
    // CUSTOM ACTIONS (inline):
    {
      key: 'run',
      icon: Rocket24Regular,
      label: t("Run"),
      onClick: props.onRun,
      testId: 'ribbon-run-btn',
      disabled: false,
      hidden: props.currentView !== EDITOR_VIEW_TYPES.DEFAULT
    }
  ];

  return (
    <Ribbon tabs={tabs}>
      <RibbonToolbar actions={actions} />
    </Ribbon>
  );
}
```

### Rules

- `homeToolbarActions` is **mandatory** — every ribbon must have a Home tab via `createRibbonTabs()`
- `RibbonToolbar` auto-wraps every `ToolbarButton` in a `Tooltip` — never implement manually
- Use `createSaveAction()` / `createSettingsAction()` factories — never build custom save/settings
- Custom actions: define inline as `RibbonAction` objects with `key`, `icon`, `label`, `onClick`, `testId`
- Optional: `disabled`, `hidden` for conditional visibility

### WRONG Patterns

```tsx
// ❌ Custom ribbon layout
<div className="ribbon"><TabList><Tab>Home</Tab></TabList><Toolbar>...</Toolbar></div>

// ❌ Manual Tooltip + ToolbarButton
<Toolbar><Tooltip content="Save"><ToolbarButton icon={<Save24Regular />} /></Tooltip></Toolbar>

// ❌ Custom action factories
export function createCustomSaveAction() { ... }  // Use standard factories
```

---

## 3. ItemEditorDefaultView (Multi-Panel Layout)

**Location**: `Workload/app/components/ItemEditor/`

Standard two-panel layout: optional left (explorer/nav) + required center (main content).

### Props API

```typescript
interface ItemEditorDefaultViewProps {
  left?: {
    content: React.ReactNode;        // Panel content
    title?: string;                  // Panel header
    width?: number;                  // Initial width (px)
    minWidth?: number;               // Min resize width
    maxWidth?: number;               // Max resize width
    collapsible?: boolean;           // Enable collapse toggle
    enableUserResize?: boolean;      // Enable drag-to-resize
    onCollapseChange?: (collapsed: boolean) => void;
  };
  center: {                          // REQUIRED
    content: React.ReactNode;
    ariaLabel?: string;
    className?: string;
  };
}
```

### Usage

```tsx
<ItemEditorDefaultView
  left={{
    content: <ExplorerPanel />,
    title: "Explorer",
    width: 260,
    minWidth: 180,
    maxWidth: 400,
    collapsible: true,
    enableUserResize: true
  }}
  center={{
    content: <MainEditor />,
    ariaLabel: "Main Content"
  }}
/>
```

---

## 4. ItemEditorDetailView (L2 Drill-Down)

For sub-pages, record details, settings, or any view users navigate **to** from the main view.

### Props API

```typescript
interface ItemEditorDetailViewProps {
  left?: { content, title, width, collapsible };   // Same as DefaultView
  center: { content };                              // Required
  actions?: Array<{                                 // Context-specific toolbar actions
    key: string;
    label: string;
    icon: React.ComponentType;
    onClick: () => void;
  }>;
}
```

### Usage — Register with `isDetailView: true`

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
  isDetailView: true   // ← Enables automatic back navigation in ribbon
}
```

**When to use:**
- Record details or drill-down pages
- Settings and configuration pages
- Edit/view individual items
- Any focused single-entity view

**Benefits over custom layouts:**
- Automatic back navigation via `isDetailView: true`
- Context-specific actions in ribbon
- Optional left panel for properties
- Consistent layout, accessibility, and responsive behavior

---

## 5. ItemEditorEmptyView (First-Time Experience)

Shown when an item is first created and has no data.

### Props API

```typescript
interface ItemEditorEmptyViewProps {
  title: string;
  description: string;
  imageSrc: string;              // Path to empty state illustration
  imageAlt?: string;
  tasks: EmptyStateTask[];       // Action buttons
}

interface EmptyStateTask {
  id: string;
  label: string;
  description?: string;
  icon?: React.ComponentType;
  onClick: () => void;
  appearance?: 'primary' | 'secondary';
}
```

### Usage

```tsx
<ItemEditorEmptyView
  title={t('Welcome to My Item!')}
  description={t('Get started by configuring your first data source')}
  imageSrc="/assets/items/MyItem/EditorEmpty.svg"
  imageAlt="Empty state"
  tasks={[
    { id: 'start', label: t('Get Started'), onClick: () => setCurrentView('default'), appearance: 'primary' },
    { id: 'import', label: t('Import Data'), description: t('From CSV or JSON'), onClick: handleImport }
  ]}
/>
```

---

## 6. OneLakeView

**Location**: `Workload/app/components/OneLakeView`  
**Import**: `import { OneLakeView } from '../../../components/OneLakeView'`  
**NEVER** copy from `samples/views/SampleOneLakeView` — always import from `components/OneLakeView`.

### Props API

```typescript
interface OneLakeViewProps {
  workloadClient: WorkloadClientAPI;
  config: OneLakeViewConfig;
  callbacks: OneLakeViewCallbacks;
}

interface OneLakeViewConfig {
  mode: "edit" | "view";                  // Edit allows CRUD, view is read-only
  initialItem: {
    id: string;                           // ALL 3 REQUIRED or control shows empty
    workspaceId: string;
    displayName: string;
  };
  allowItemSelection?: boolean;           // Show Add button for DataHub selection
  allowedItemTypes?: string[];            // ["Lakehouse", "Warehouse", "KQLDatabase"]
  refreshTrigger?: number;                // Increment to force re-fetch
}

interface OneLakeViewCallbacks {
  onFileSelected?: (fileName: string, oneLakeLink: string) => void;
  onTableSelected?: (tableName: string, oneLakeLink: string) => void;
  onItemChanged?: (item: { id: string; workspaceId: string; displayName: string }) => void;
}
```

### Usage

```tsx
<OneLakeView
  workloadClient={props.workloadClient}
  config={{
    mode: "edit",
    initialItem: { id: item.id, workspaceId: item.workspaceId, displayName: item.displayName },
    allowItemSelection: true,
    allowedItemTypes: ["Lakehouse", "Warehouse", "KQLDatabase"],
    refreshTrigger: refreshCount
  }}
  callbacks={{
    onFileSelected: (fileName, link) => { /* handle */ },
    onTableSelected: (tableName, link) => { /* handle */ },
    onItemChanged: (newItem) => { /* handle item switch */ }
  }}
/>
```

### Features

- Empty state with "Add" button when no `initialItem`
- Tree navigation (Files + Tables folders)
- CRUD in edit mode (create folder, upload, delete, rename)
- Context menus and keyboard shortcuts
- Loading states during operations

### Common Issues

| Problem | Cause | Fix |
|---------|-------|-----|
| Empty control, no tree | Missing `initialItem` | Provide all 3 fields: `id`, `workspaceId`, `displayName` |
| No "Add" button | `allowItemSelection` not set | Set `allowItemSelection: true` |
| Permission errors | Missing scope | Request `OneLake.Read.All` via `acquireAccessToken()` |
| Using sample code | Imported from samples/ | Always import from `components/OneLakeView` |

---

## 7. WizardControl

**Location**: `Workload/app/components/Wizard/Wizard.tsx`

### Props API

```typescript
interface WizardControlProps {
  steps: WizardStep[];
  initialStepId?: string;
  onStepChange?: (stepId: string) => void;
  onComplete: () => void;
  onCancel?: () => void;
  canFinish?: boolean;
  initialContext?: any;
  showNavigation?: boolean;
  className?: string;
  allowStepNavigation?: boolean;
  navigationLabels?: { next: string; previous: string; finish: string; cancel: string };
}

interface WizardStep {
  id: string;
  title: string;
  description?: string;
  component: React.ComponentType<WizardStepProps>;   // Receives injected props
  validate?: () => boolean;                          // Gate before advancing
  onEnter?: () => void;
  onExit?: () => void;
}

// Injected into each step component automatically:
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

### Layout

```
┌──────────────────────────────────────────────────┐
│ ┌───────────┐ ┌──────────────────────────────┐   │
│ │ Steps     │ │ Content Panel                │   │
│ │ Panel     │ │                              │   │
│ │ (180px)   │ │ (renders step.component)     │   │
│ │           │ │                              │   │
│ │ ✓ Step 1  │ │                              │   │
│ │ ● Step 2  │ │                              │   │
│ │ ○ Step 3  │ │                              │   │
│ └───────────┘ └──────────────────────────────┘   │
│ ┌────────────────────────────────────────────┐   │
│ │ Footer (Previous / Next / Finish / Cancel) │   │
│ └────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────┘
```

- Step states: ✓ Completed (green, clickable), ● Current (green), ○ Upcoming (gray)
- Responsive: 180px steps panel on desktop (≥769px), 140px on mobile (≤768px)
- BEM CSS: `.wizard-control`
- Best practice: 3-5 steps ideal

### Usage

```tsx
import { WizardControl } from '../../components/Wizard';

const steps: WizardStep[] = [
  {
    id: 'info', title: 'Basic Info', description: 'Name and description',
    component: BasicInfoStep,
    validate: () => !!formData.name
  },
  {
    id: 'source', title: 'Data Source', description: 'Choose your data',
    component: DataSourceStep,
    validate: () => !!formData.sourcePath
  },
  {
    id: 'review', title: 'Review', description: 'Confirm settings',
    component: ReviewStep
  }
];

<WizardControl
  steps={steps}
  initialStepId="info"
  onComplete={handleCreate}
  onCancel={handleCancel}
  canFinish={isValid}
  showNavigation={true}
  allowStepNavigation={true}
/>
```

---

## 8. Host API Integration

### Authentication

```typescript
import { WorkloadClientAPI } from "@ms-fabric/workload-client";

// Acquire OBO token
const token = await workloadClient.authentication.acquireAccessToken({
  additionalScopesToConsent: ["https://storage.azure.com/.default"]
});
```

| Target API | Scope |
|-----------|-------|
| OneLake DFS | `https://storage.azure.com/.default` |
| Fabric REST API | `https://api.fabric.microsoft.com/.default` |
| Spark Livy | `https://api.fabric.microsoft.com/.default` |
| Custom external API | `api://your-api-app-id/.default` |

### Notifications

```typescript
import { callNotificationOpen } from "../../controller/NotificationController";

callNotificationOpen(workloadClient, title, message);
```

### Settings

```typescript
import { callGetItem } from "../../controller/ItemCRUDController";
import { callOpenSettings } from "../../controller/SettingsController";

const item_res = await callGetItem(workloadClient, item.id);
await callOpenSettings(workloadClient, item_res.item, 'About');
```

### Item CRUD

```typescript
import { getWorkloadItem, saveItemDefinition, ItemWithDefinition } from "../../controller/ItemCRUDController";

// Load item with definition
const item = await getWorkloadItem<MyItemDefinition>(workloadClient, itemObjectId);

// Save definition
await saveItemDefinition<MyItemDefinition>(workloadClient, item.id, { state: 'default', ...data });
```

---

## 9. Theming & Accessibility

### Mandatory Requirements

1. **Fluent UI v9**: `@fluentui/react-components` — never import from `@fluentui/react`
2. **Fabric design tokens**: Use `var(--colorBrandForeground1)`, `var(--spacingVerticalL)`, etc. in SCSS
3. **All 3 themes**: light, dark, high contrast — never hard-code colors
4. **Accessibility**: ARIA labels, keyboard navigation, screen reader support, WCAG 2.1 AA contrast ratios
5. **Focus management**: Proper focus trapping in dialogs, restore focus on close

### Import Paths

```typescript
// Toolkit components
import { ItemEditor, ItemEditorEmptyView, ItemEditorDefaultView } from '../../components/ItemEditor';
import { Ribbon, RibbonToolbar, createSaveAction, createSettingsAction, createRibbonTabs } from '../../components/ItemEditor';
import { OneLakeView } from '../../../components/OneLakeView';
import { WizardControl } from '../../components/Wizard';

// Fluent UI v9
import { Button, Input, Text, Card, CardHeader, MessageBar, MessageBarBody } from '@fluentui/react-components';
import { Save24Regular, Settings24Regular, Rocket24Regular } from '@fluentui/react-icons';

// Fabric SDK
import { WorkloadClientAPI } from "@ms-fabric/workload-client";

// Controllers
import { getWorkloadItem, saveItemDefinition } from "../../controller/ItemCRUDController";
import { callOpenSettings } from "../../controller/SettingsController";
import { callNotificationOpen } from "../../controller/NotificationController";
```

---

## Component Summary

| Component | Required? | Location | When to Use |
|-----------|-----------|----------|-------------|
| **ItemEditor** | **YES** | `components/ItemEditor` | Root container for every item editor |
| **Ribbon + RibbonToolbar** | **YES** | `components/ItemEditor` | Toolbar with standard + custom actions |
| **ItemEditorDefaultView** | Recommended | `components/ItemEditor` | Multi-panel layout (left + center) |
| **ItemEditorDetailView** | For drill-down | `components/ItemEditor` | L2 pages with auto-back navigation |
| **ItemEditorEmptyView** | Recommended | `components/ItemEditor` | First-time empty state with tasks |
| **OneLakeView** | Optional | `components/OneLakeView` | Browse OneLake files/tables |
| **WizardControl** | Optional | `components/Wizard` | Multi-step guided workflows |
