# Ontology Versioning and Lifecycle

## Scope

This file applies to the **new TMDL-based ontology experience**. The Fabric definition parts,
not a parallel YAML model, are the deployable source of truth.

Do not inject an undocumented `_version.yaml`, `deprecated_since`, or other custom property into
the Fabric ontology definition. If a repository needs release metadata, keep it beside the
artifact as repository metadata and exclude it from the `updateDefinition` payload.

---

## Product version history

Fabric Ontology has a built-in **Version history** pane. Use **New Version** to create a named
snapshot with a required name and optional description before a significant edit or restore.

- Versions record name, date/time, creator, and description.
- Read-only users can view versions; Read/Write access is required to create, edit, restore, or
  delete them.
- **Restore** replaces the entire current ontology definition with the selected snapshot.
- Create a snapshot of the current state before restoring when it might need to be recovered.
- Deleting a version is permanent.

Product version history is the quickest item-level rollback mechanism. Git integration and
Deployment Pipelines remain the ALM path for reviewable diffs and environment promotion; use both
when the ontology is managed as code.

---

## Source control model

Store the definition returned by `getDefinition` with its paths preserved:

```text
.platform
database.tmdl
model.tmdl
tables/*.tmdl
entities/*.tmdl
entityRelationships.tmdl
namespaces.tmdl
metrics.tmdl
rules.tmdl
```

The exact set of parts is product-generated and can evolve. Never manufacture a missing part
from this example alone:

1. Configure or generate the ontology in a non-production workspace.
2. Call `getDefinition`.
3. Commit the emitted parts without reformatting away meaningful TMDL structure.
4. Modify only documented TMDL/TMSL++ objects.
5. Round-trip with `updateDefinition`, then retrieve the definition again.

Use Fabric Git integration and Deployment Pipelines for environment promotion when available.
Keep environment IDs and connections outside reusable content or replace them through the
repository's normal environment-parameter process.

---

## Identity and rename safety

`lineageTag` is the stable identity for TMDL objects. Preserve it across display-name or logical
renames.

| Change | Required handling |
| --- | --- |
| Rename an entity, table, property, or relationship | Preserve its existing `lineageTag` |
| Add an object | Generate a stable new lineage tag |
| Copy an object as a genuinely new concept | Give the copy a new lineage tag |
| Delete and recreate under the same name | Treat as identity-breaking unless continuity is proven |
| Change an entity key | Revalidate instance identity and any Graph projection |
| Change a source binding | Revalidate source permissions, mappings, and Data Agent routing |

Never replace all lineage tags during generation. A textually similar definition with new tags
can be a destructive identity change for downstream consumers.

---

## Release numbering

Semantic versioning can be used as a **repository convention**, but it is not a Fabric Ontology
API contract. Record the release in a changelog, Git tag, or deployment manifest outside the
definition payload.

Suggested classification:

| Change | Repository release |
| --- | --- |
| Description, synonym, or example clarification | PATCH |
| Add an optional entity/property/relationship/metric/rule | MINOR |
| Add a new source binding without changing existing meaning | MINOR |
| Remove or rename a consumed concept | MAJOR |
| Change property type, entity key, relationship cardinality, or metric semantics | MAJOR |
| Replace a source in a way that changes security or query semantics | MAJOR |

The version number does not make a change safe. Validate the actual downstream consumers.

---

## Compatibility review

Before changing a published ontology, inspect:

| Consumer | What can break |
| --- | --- |
| Bound source | Table/column names, data types, keys, relationships, timestamps, measures |
| Fabric Data Agent | Context routing, associated source access, instructions, example queries |
| Semantic model | DAX measures, relationships, Prep for AI, Verified Answers |
| Optional Graph Model | Eligible keys, selected entities/relationships, node/edge refresh |
| Ontology MCP clients | Entity/property names, rules, namespaces, resource links |
| Deployment pipeline | Definition-part compatibility and environment-specific connections |

Data Agent context can lag an ontology change by up to 10 minutes. Use its manual refresh action
when validating a new release. A materialized Graph requires its own refresh and count checks.

### Breaking changes

Treat these as breaking until proven otherwise:

- removing or renaming a consumed entity, property, relationship, metric, or rule;
- changing a property type or the meaning of a metric;
- changing `keyProperty`, source identity, or relationship cardinality;
- replacing a SQL/KQL/DAX source with a different execution engine;
- removing a source that a Data Agent can select;
- changing permissions so the requesting user can no longer access the underlying source.

When a deprecation period is needed, keep the old concept in the ontology while consumers move,
describe the replacement in supported descriptions/rules, and track the removal in the external
release manifest. Do not invent unsupported TMDL annotations.

---

## Promotion workflow

1. **Retrieve** the current definition with `getDefinition`.
2. **Diff** every emitted part and confirm lineage tags are stable.
3. **Review** source bindings, keys, relationships, metrics, rules, and permissions.
4. **Apply** in a non-production workspace with `updateDefinition`.
5. **Read back** the definition and compare it with the intended payload.
6. **Exercise** one representative SQL, KQL, and DAX route that the ontology exposes.
7. **Refresh** Data Agent ontology context and optional Graph materialization.
8. **Promote** through Git integration or a Deployment Pipeline.
9. **Verify** the production definition and consumer answers after promotion.

For a migration from the old JSON experience, use `migration_old_to_new.md`. That migration
creates a new item and therefore also requires reconnecting downstream consumers to the new item
ID.

---

## Cross-references

- `new_experience_tmdl.md` - definition parts and authoring rules
- `data_agent_context.md` - Data Agent routing and refresh behavior
- `migration_old_to_new.md` - old-to-new generation migration
- `known_issues.md` - current product limitations
- `../graph-agent/instructions.md` - optional Graph lifecycle
- [Microsoft Learn: Manage Ontology version history](https://learn.microsoft.com/fabric/iq/ontology/how-to-use-version-history)
