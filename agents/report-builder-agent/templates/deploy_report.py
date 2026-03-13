"""
Template: Deploy or update a Power BI Report via Fabric REST API.

Usage:
    1. Customize report_json (or load from templates/report_json_template.json)
    2. Set environment (PATH, az login)
    3. Run: python deploy_report.py

Actions:
    - Creates a new report if REPORT_ID is None
    - Updates existing report if REPORT_ID is set
    - Validates format before deployment
"""
import base64, json, requests, time, subprocess, sys, os

# ── CONFIG ─────────────────────────────────────────────────────
WS_ID       = "133c6c70-2e26-4d97-aac1-8ed423dbbf34"
WS_NAME     = "CDR - Demo Finance Fabric"
MODEL_NAME  = "SM_Finance"
MODEL_ID    = "236080b8-3bea-4c14-86df-d1f9a14ac7a8"
REPORT_ID   = None  # Set to existing report ID to update, or None to create
REPORT_NAME = "RPT_Finance_Dashboard"
API         = "https://api.fabric.microsoft.com/v1"

# Paths
REPORT_JSON_PATH = "templates/report_json_template.json"  # Or set to None for inline
THEME_B64_PATH   = None  # Path to base64-encoded theme file, or None to skip
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


def encode(obj) -> str:
    """Base64-encode a dict or string."""
    if isinstance(obj, dict):
        content = json.dumps(obj, ensure_ascii=False)
    else:
        content = str(obj)
    return base64.b64encode(content.encode("utf-8")).decode("ascii")


def build_definition_pbir() -> dict:
    """Build the definition.pbir V2 schema."""
    conn_str = (
        f'Data Source="powerbi://api.powerbi.com/v1.0/myorg/{WS_NAME}";'
        f"initial catalog={MODEL_NAME};"
        f"integrated security=ClaimsToken;"
        f"semanticmodelid={MODEL_ID}"
    )
    return {
        "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definitionProperties/2.0.0/schema.json",
        "version": "4.0",
        "datasetReference": {
            "byConnection": {
                "connectionString": conn_str
            }
        }
    }


def validate_report(report_json: dict) -> list[str]:
    """Validate report.json structure. Returns list of errors."""
    errors = []

    if "layoutOptimization" not in report_json:
        errors.append("Missing 'layoutOptimization' (must be integer 0)")
    elif report_json["layoutOptimization"] != 0:
        errors.append(f"layoutOptimization is {report_json['layoutOptimization']}, expected 0")

    if "sections" not in report_json:
        errors.append("Missing 'sections' array")
    else:
        for i, section in enumerate(report_json["sections"]):
            if "visualContainers" not in section:
                errors.append(f"Section {i} missing 'visualContainers'")
            if isinstance(section.get("config"), dict):
                errors.append(f"Section {i}: 'config' must be stringified, not a dict")
            if isinstance(section.get("filters"), list):
                errors.append(f"Section {i}: 'filters' must be stringified '[]', not a list")

    if "config" not in report_json:
        errors.append("Missing report-level 'config'")
    elif isinstance(report_json["config"], dict):
        errors.append("Report 'config' must be stringified, not a dict")

    # Check for PBIR folder format (common mistake)
    config_str = report_json.get("config", "")
    if "definition/pages" in str(report_json):
        errors.append("DETECTED PBIR folder format paths — use Legacy PBIX format instead!")

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


def extract_theme_from_report(report_id: str, headers: dict) -> str | None:
    """Extract base theme b64 from an existing report via getDefinition."""
    print("   Extracting theme from existing report...")
    resp = requests.post(f"{API}/workspaces/{WS_ID}/reports/{report_id}/getDefinition", headers=headers)

    if resp.status_code == 202:
        op_id = resp.headers["x-ms-operation-id"]
        result = poll_operation(op_id, headers)
    elif resp.status_code == 200:
        result = resp.json()
    else:
        print(f"   Could not get definition: {resp.status_code}")
        return None

    for part in result.get("definition", {}).get("parts", []):
        if "BaseThemes" in part.get("path", ""):
            return part["payload"]

    return None


def main():
    print("=== Report Deployer ===\n")

    # 1. Load report.json
    if REPORT_JSON_PATH:
        print(f"1. Loading report from {REPORT_JSON_PATH}...")
        with open(REPORT_JSON_PATH, "r", encoding="utf-8") as f:
            report_json = json.load(f)
    else:
        print("1. Using inline report definition...")
        report_json = {}

    # 2. Validate
    print("2. Validating report structure...")
    errors = validate_report(report_json)
    if errors:
        print("   ✗ Validation failed:")
        for e in errors:
            print(f"     - {e}")
        sys.exit(1)
    sections = report_json.get("sections", [])
    total_visuals = sum(len(s.get("visualContainers", [])) for s in sections)
    print(f"   ✓ Valid ({len(sections)} pages, {total_visuals} visuals)\n")

    # 3. Auth
    print("3. Authenticating...")
    token = get_token()
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    print("   ✓ Token acquired\n")

    # 4. Build parts
    print("4. Building definition parts...")
    pbir = build_definition_pbir()
    parts = [
        {"path": "report.json", "payload": encode(report_json), "payloadType": "InlineBase64"},
        {"path": "definition.pbir", "payload": encode(pbir), "payloadType": "InlineBase64"},
    ]

    # Add theme if available
    if THEME_B64_PATH and os.path.exists(THEME_B64_PATH):
        with open(THEME_B64_PATH, "r") as f:
            theme_b64 = f.read().strip()
        parts.append({"path": "StaticResources/SharedResources/BaseThemes/CY26SU02.json",
                       "payload": theme_b64, "payloadType": "InlineBase64"})
        print("   ✓ Theme included")
    elif REPORT_ID:
        # Try to extract theme from existing report
        theme_b64 = extract_theme_from_report(REPORT_ID, headers)
        if theme_b64:
            parts.append({"path": "StaticResources/SharedResources/BaseThemes/CY26SU02.json",
                           "payload": theme_b64, "payloadType": "InlineBase64"})
            print("   ✓ Theme extracted from existing report")
    print(f"   ✓ {len(parts)} parts ready\n")

    # 5. Deploy
    if REPORT_ID:
        print(f"5. Updating existing report {REPORT_ID}...")
        resp = requests.post(
            f"{API}/workspaces/{WS_ID}/reports/{REPORT_ID}/updateDefinition",
            headers=headers,
            json={"definition": {"parts": parts}}
        )
    else:
        print(f"5. Creating new report '{REPORT_NAME}'...")
        resp = requests.post(
            f"{API}/workspaces/{WS_ID}/reports",
            headers=headers,
            json={
                "displayName": REPORT_NAME,
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
