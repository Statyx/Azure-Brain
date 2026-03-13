"""
Template: Deploy or update a Semantic Model via Fabric REST API.

Usage:
    1. Customize model_bim dict (or load from templates/model_bim_template.json)
    2. Set environment (PATH, az login)
    3. Run: python deploy_semantic_model.py

Actions:
    - Creates a new model if MODEL_ID is None
    - Updates existing model if MODEL_ID is set
    - Validates model structure before deployment
"""
import base64, json, requests, time, subprocess, sys

# ── CONFIG ─────────────────────────────────────────────────────
WS_ID    = "133c6c70-2e26-4d97-aac1-8ed423dbbf34"
MODEL_ID = None  # Set to existing model ID to update, or None to create
MODEL_NAME = "SM_Finance"
API      = "https://api.fabric.microsoft.com/v1"

# Load model.bim from file or define inline
MODEL_BIM_PATH = "templates/model_bim_template.json"  # Or set to None to use inline
# ───────────────────────────────────────────────────────────────


def get_token() -> str:
    result = subprocess.run(
        ["az", "account", "get-access-token", "--resource", "https://api.fabric.microsoft.com",
         "--query", "accessToken", "-o", "tsv"],
        capture_output=True, text=True, shell=True
    )
    token = result.stdout.strip()
    if not token:
        raise RuntimeError(f"Token failed: {result.stderr}")
    return token


def validate_model(bim: dict) -> list[str]:
    """Validate model.bim structure. Returns list of errors (empty = valid)."""
    errors = []
    
    if "compatibilityLevel" not in bim:
        errors.append("Missing 'compatibilityLevel'")
    elif bim["compatibilityLevel"] < 1604:
        errors.append(f"compatibilityLevel {bim['compatibilityLevel']} < 1604 (required for Direct Lake)")
    
    model = bim.get("model", {})
    
    if model.get("defaultMode") != "directLake":
        errors.append(f"defaultMode is '{model.get('defaultMode')}', expected 'directLake'")
    
    tables = model.get("tables", [])
    if not tables:
        errors.append("No tables defined")
    
    table_names = {t["name"] for t in tables}
    
    # Check relationships
    for rel in model.get("relationships", []):
        if rel["fromTable"] not in table_names:
            errors.append(f"Relationship '{rel['name']}': fromTable '{rel['fromTable']}' not found")
        if rel["toTable"] not in table_names:
            errors.append(f"Relationship '{rel['name']}': toTable '{rel['toTable']}' not found")
    
    # Check columns
    for table in tables:
        for col in table.get("columns", []):
            if "name" not in col:
                errors.append(f"Table '{table['name']}': column missing 'name'")
            if "dataType" not in col:
                errors.append(f"Table '{table['name']}': column '{col.get('name', '?')}' missing 'dataType'")
            if "sourceColumn" not in col:
                errors.append(f"Table '{table['name']}': column '{col.get('name', '?')}' missing 'sourceColumn'")
    
    # Check partitions
    for table in tables:
        partitions = table.get("partitions", [])
        if not partitions:
            errors.append(f"Table '{table['name']}': no partitions defined")
        for p in partitions:
            source = p.get("source", {})
            if source.get("type") != "entity":
                errors.append(f"Table '{table['name']}': partition type should be 'entity' for Direct Lake")
    
    # Check expressions
    expressions = model.get("expressions", [])
    if not expressions:
        errors.append("No M expressions (data source) defined")
    
    return errors


def poll_operation(op_id: str, headers: dict, timeout: int = 300) -> dict:
    start = time.time()
    for _ in range(timeout // 5):
        op = requests.get(f"{API}/operations/{op_id}", headers=headers).json()
        status = op.get("status", "Unknown")
        elapsed = time.time() - start
        
        if status == "Succeeded":
            result_resp = requests.get(f"{API}/operations/{op_id}/result", headers=headers)
            return result_resp.json() if result_resp.status_code == 200 else op
        
        if status in ("Failed", "Cancelled"):
            error = op.get("error", {})
            raise RuntimeError(f"Operation {status}: {json.dumps(error, indent=2)}")
        
        print(f"  [{elapsed:.0f}s] {status}...")
        time.sleep(5)
    
    raise TimeoutError(f"Did not complete in {timeout}s")


def main():
    print("=== Semantic Model Deployer ===\n")
    
    # 1. Load model.bim
    if MODEL_BIM_PATH:
        print(f"1. Loading model from {MODEL_BIM_PATH}...")
        with open(MODEL_BIM_PATH, "r") as f:
            model_bim = json.load(f)
    else:
        print("1. Using inline model definition...")
        model_bim = {}  # Define inline here
    
    # 2. Validate
    print("2. Validating model structure...")
    errors = validate_model(model_bim)
    if errors:
        print("   ✗ Validation failed:")
        for e in errors:
            print(f"     - {e}")
        sys.exit(1)
    print(f"   ✓ Valid ({len(model_bim['model']['tables'])} tables, "
          f"{len(model_bim['model'].get('relationships', []))} relationships)\n")
    
    # 3. Auth
    print("3. Authenticating...")
    token = get_token()
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    print("   ✓ Token acquired\n")
    
    # 4. Encode
    bim_b64 = base64.b64encode(json.dumps(model_bim).encode()).decode()
    pbism_b64 = base64.b64encode(b'{"version": "1.0"}').decode()
    
    parts = [
        {"path": "definition.pbism", "payload": pbism_b64, "payloadType": "InlineBase64"},
        {"path": "model.bim", "payload": bim_b64, "payloadType": "InlineBase64"},
    ]
    
    # 5. Deploy
    if MODEL_ID:
        print(f"4. Updating existing model {MODEL_ID}...")
        resp = requests.post(
            f"{API}/workspaces/{WS_ID}/semanticModels/{MODEL_ID}/updateDefinition",
            headers=headers,
            json={"definition": {"parts": parts}}
        )
    else:
        print(f"4. Creating new model '{MODEL_NAME}'...")
        resp = requests.post(
            f"{API}/workspaces/{WS_ID}/items",
            headers=headers,
            json={
                "displayName": MODEL_NAME,
                "type": "SemanticModel",
                "definition": {"parts": parts}
            }
        )
    
    if resp.status_code in (200, 201):
        result = resp.json() if resp.text else {}
        print(f"   ✓ Completed (sync). ID: {result.get('id', 'N/A')}\n")
    elif resp.status_code == 202:
        op_id = resp.headers.get("x-ms-operation-id")
        print(f"   Operation: {op_id}")
        result = poll_operation(op_id, headers)
        print(f"   ✓ Completed!\n")
    else:
        print(f"   ✗ Failed: {resp.status_code}")
        print(f"   {resp.text}\n")
        sys.exit(1)
    
    print("=== Done ===")


if __name__ == "__main__":
    main()
