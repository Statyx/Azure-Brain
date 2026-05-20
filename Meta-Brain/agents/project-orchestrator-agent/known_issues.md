# Known Issues — Project Orchestration

## Pipeline Ordering Issues

### 1. Semantic Model Before Data Exists
- **Symptom**: Direct Lake model shows "no data" or refresh fails
- **Cause**: Gold Lakehouse tables not populated yet when semantic model is deployed
- **Fix**: Always run Step 5 (ETL notebooks) before Step 7 (semantic model). Use `RefreshType=Calculate` after relationships are set.

### 2. Data Agent Without Descriptions
- **Symptom**: Agent picks wrong measures, low accuracy
- **Cause**: Semantic model deployed without `///` TMDL descriptions
- **Fix**: Ensure Step 7 includes descriptions on all measures and key columns. Models with <50% description coverage show significantly more errors.

### 3. Report Points to Wrong Semantic Model
- **Symptom**: Report shows "can't connect to data source"
- **Cause**: Semantic model ID changed between deployments
- **Fix**: Use `definition.pbism` with `{"version": "1.0"}` only. Bind via REST API after deployment.

### 4. RTI Steps Blocked by Capacity
- **Symptom**: Eventhouse creation fails (403 or capacity error)
- **Cause**: F2/F4 capacity doesn't support Eventhouse
- **Fix**: Eventhouse requires minimum F16. Data Agent requires F64.

### 5. Pipeline Cold Start
- **Symptom**: Step 11 pipeline shows "NotStarted" for 1-2 minutes
- **Cause**: Normal Spark cold-start behavior on F16
- **Fix**: Just wait — total pipeline run ~4 minutes. Don't cancel and retry.

## Config Issues

### 6. Missing Domains in Config
- **Symptom**: Generation produces partial output (some CSVs missing)
- **Cause**: `industry.json` domains list doesn't match `sample-data.json` table domains
- **Fix**: Validate domain list is consistent across all config files before starting pipeline.

### 7. Circular FK References
- **Symptom**: Sample data generation hangs or produces inconsistent IDs
- **Cause**: Table A references Table B which references Table A
- **Fix**: Ensure FK dependency graph is a DAG (no cycles). Generate parent tables first.

## Handoff Issues

### 8. Agent Skips Reading Config
- **Symptom**: Agent produces generic output instead of industry-specific
- **Cause**: Specialized agent wasn't given the config file path
- **Fix**: Always pass config file paths in the handoff. Example: "Use `industries/contoso-energy/semantic-model.json` for measure definitions."
