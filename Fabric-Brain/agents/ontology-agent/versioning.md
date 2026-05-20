# Ontology Versioning & Lifecycle Management

## Purpose

Strategies for versioning ontologies, maintaining backward compatibility, deprecating properties, and evolving domain models without breaking downstream consumers (Semantic Models, AI Skills, Reports).

---

## Versioning Strategy

### Semantic Versioning for Ontologies

Apply semantic versioning (`MAJOR.MINOR.PATCH`) to ontology releases:

| Change Type | Version Bump | Example |
|-------------|-------------|---------|
| Add optional property | MINOR | 1.0.0 → 1.1.0 |
| Add new entity | MINOR | 1.1.0 → 1.2.0 |
| Add new relationship | MINOR | 1.2.0 → 1.3.0 |
| Fix description / typo | PATCH | 1.3.0 → 1.3.1 |
| Remove property | MAJOR | 1.3.1 → 2.0.0 |
| Rename entity / property | MAJOR | 2.0.0 → 3.0.0 |
| Change cardinality (1:N → 1:1) | MAJOR | 3.0.0 → 4.0.0 |
| Change data type of property | MAJOR | 4.0.0 → 5.0.0 |

### Version Metadata File

Every ontology release **MUST** include a `_version.yaml`:

```yaml
ontology:
  name: "Manufacturing IoT Domain"
  version: "2.1.0"
  released: "2024-12-15"
  author: "Domain Modeler Agent"
  breaking_changes: false
  changelog:
    - version: "2.1.0"
      date: "2024-12-15"
      changes:
        - type: "added"
          entity: "MaintenanceSchedule"
          description: "New entity for predictive maintenance tracking"
        - type: "added"
          property: "Machine.expectedLifetimeHours"
          description: "Optional property for lifecycle planning"
    - version: "2.0.0"
      date: "2024-11-01"
      changes:
        - type: "removed"
          property: "Sensor.legacyId"
          description: "Replaced by Sensor.globalId in v1.3.0"
        - type: "renamed"
          entity: "ProductionLine → AssemblyLine"
          description: "Align with industry terminology"
```

---

## Backward Compatibility Rules

### Rule 1: Never Remove Without Deprecation Period

A property or entity **MUST** go through a deprecation period before removal:

```
v1.0 → Property exists (active)
v1.1 → Property marked deprecated (still present, consumers warned)
v2.0 → Property removed (MAJOR version bump)
```

Minimum deprecation period: **2 version cycles** or **30 days**, whichever is longer.

### Rule 2: Deprecation Annotation Format

Add deprecation metadata directly in the ontology definition:

```yaml
entities:
  Sensor:
    properties:
      legacyId:
        type: string
        deprecated: true
        deprecated_since: "1.3.0"
        replacement: "globalId"
        removal_target: "2.0.0"
        migration_note: "Copy legacyId value to globalId. Format identical."
      globalId:
        type: string
        required: true
        since: "1.3.0"
```

### Rule 3: Additive Changes Are Always Safe

These changes **NEVER** break consumers:
- Adding a new entity
- Adding an optional property to an existing entity
- Adding a new relationship
- Adding a new enum value
- Expanding a constraint (e.g., max length 50 → 100)

### Rule 4: Restrictive Changes Are Always Breaking

These changes **ALWAYS** require a MAJOR version bump:
- Removing an entity or property
- Making an optional property required
- Changing a data type (string → int)
- Restricting a constraint (e.g., max length 100 → 50)
- Changing relationship cardinality
- Renaming anything

---

## Property Deprecation Patterns

### Pattern 1: Shadow Property (Rename)

When renaming a property, keep both for the deprecation period:

```yaml
# v1.3.0 - Add new name, deprecate old
entities:
  Machine:
    properties:
      productionLine:          # OLD name
        type: string
        deprecated: true
        deprecated_since: "1.3.0"
        replacement: "assemblyLine"
      assemblyLine:             # NEW name
        type: string
        since: "1.3.0"
        note: "Replaces productionLine"
```

**Migration script** for Lakehouse:

```python
# Backfill new column from old column
spark.sql("""
    UPDATE delta.`Tables/dim_machine`
    SET assemblyLine = productionLine
    WHERE assemblyLine IS NULL AND productionLine IS NOT NULL
""")
```

### Pattern 2: Type Evolution (String → Structured)

When a property needs richer typing:

```yaml
# v1.0 - Simple string
location:
  type: string
  example: "Building A, Floor 2, Room 201"

# v2.0 - Structured object
locationDetails:
  type: object
  properties:
    building: { type: string }
    floor: { type: integer }
    room: { type: string }
    geoCoordinates: { type: string, format: "lat,long" }
  since: "2.0.0"

# Keep 'location' as computed/deprecated during transition
location:
  type: string
  deprecated: true
  computed_from: "locationDetails"
  formula: "CONCAT(building, ', Floor ', floor, ', Room ', room)"
```

### Pattern 3: Entity Split

When one entity becomes two:

```
v1.0: Equipment (id, name, type, manufacturer, warranty_start, warranty_end, last_maintenance)
v2.0: 
  Equipment (id, name, type, manufacturer_id)     → Core identity
  EquipmentContract (id, equipment_id, warranty_start, warranty_end)  → Split out
  MaintenanceRecord (id, equipment_id, last_maintenance, next_scheduled) → Split out
```

**Migration steps**:
1. Create new entities in ontology (v1.x MINOR)
2. Create new tables in Lakehouse
3. Backfill new tables from original
4. Mark original properties as deprecated
5. Update Semantic Model relationships
6. Remove original properties (v2.0 MAJOR)

---

## Impact Analysis Before Changes

### Pre-Change Checklist

Before modifying any ontology element, check all downstream dependencies:

| Downstream System | What to Check | Risk Level |
|-------------------|--------------|------------|
| Lakehouse Tables | Column existence, data types | High |
| Semantic Model | Relationships, DAX measures referencing column | High |
| AI Skills | Instruction references, few-shot examples | Medium |
| Reports | Visuals bound to column, filters, slicers | High |
| EventStream | Schema mappings, processing nodes | Medium |
| KQL Queries | Saved queries referencing column names | Medium |
| Data Pipelines | Copy activities, parameters | Low |

### Impact Assessment Script

```python
def assess_ontology_change_impact(entity: str, property_name: str, change_type: str):
    """Generate impact report for an ontology change."""
    
    report = {
        "change": f"{change_type} {entity}.{property_name}",
        "impacts": []
    }
    
    # Check Lakehouse tables
    try:
        df = spark.read.format("delta").load(f"Tables/dim_{entity.lower()}")
        if property_name in df.columns:
            report["impacts"].append({
                "system": "Lakehouse",
                "table": f"dim_{entity.lower()}",
                "severity": "HIGH",
                "action": f"ALTER TABLE to {'drop' if change_type == 'remove' else 'modify'} column"
            })
    except Exception:
        pass
    
    # Check fact tables that might reference this entity
    tables = spark.catalog.listTables()
    for table in tables:
        if table.name.startswith("fact_"):
            fact_df = spark.read.format("delta").load(f"Tables/{table.name}")
            fk_column = f"{entity.lower()}_id"
            if fk_column in fact_df.columns:
                report["impacts"].append({
                    "system": "Lakehouse",
                    "table": table.name,
                    "severity": "MEDIUM",
                    "action": f"Verify FK {fk_column} still valid after change"
                })
    
    return report
```

---

## Ontology Release Process

### Step-by-Step Release Workflow

```
1. Draft Changes
   └── Update ontology YAML with proposed changes
   └── Mark deprecations, add 'since' annotations

2. Impact Analysis
   └── Run impact assessment script
   └── Document all affected downstream systems
   └── Estimate effort for each system update

3. Review
   └── Verify backward compatibility (MINOR) or plan migration (MAJOR)
   └── Update _version.yaml changelog

4. Publish
   └── Commit ontology files to repo
   └── Tag release with version number
   └── Notify downstream teams (Semantic Model, Reports, AI Skills)

5. Migrate Downstream (MAJOR changes only)
   └── Update Lakehouse schema
   └── Update Semantic Model
   └── Update AI Skill instructions
   └── Update Reports
   └── Backfill data if needed

6. Verify
   └── Run data quality checks
   └── Verify reports render correctly
   └── Test AI Skill answers
   └── Monitor for errors for 24 hours
```

---

## Cross-References

- [Domain Modeler Agent Instructions](../domain-modeler-agent/instructions.md) — Entity/property naming conventions
- [Semantic Model Agent Instructions](../semantic-model-agent/instructions.md) — How ontology maps to Semantic Model
- [Lakehouse Agent Instructions](../lakehouse-agent/instructions.md) — Delta table schema changes
- [AI Skills Agent Instructions](../ai-skills-agent/instructions.md) — How ontology feeds AI Skill instructions
