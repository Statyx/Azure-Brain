"""
Deploy a Fabric Data Agent — Template Script

Creates or updates a Data Agent with full definition:
  1. AI instructions (from a markdown file)
  2. Data source binding (semantic model, lakehouse, warehouse, or KQL DB)
  3. Few-shot examples (from a JSON file)
  4. Element selection (auto-generated from model.bim for semantic models)
  5. Publishing (draft + published parts)

Usage:
    python deploy_data_agent.py                # Create or update + publish
    python deploy_data_agent.py --draft-only   # Deploy draft only (not visible to users)
    python deploy_data_agent.py --delete        # Delete the agent

IMPORTANT: Agents deployed with --draft-only are NOT visible/testable in the
Fabric portal. Always publish (default) unless you have a specific reason not to.

Customize the CONFIG section below for your project.
"""

import argparse
import base64
import json
import os
import subprocess
import sys
import time
import uuid

import requests

# ═══════════════════════════════════════════════════════════════════════════════
# CONFIG — Customize these for your project
# ═══════════════════════════════════════════════════════════════════════════════

API = "https://api.fabric.microsoft.com/v1"
WORKSPACE_ID = "YOUR_WORKSPACE_ID"                       # ← Replace
SEMANTIC_MODEL_ID = "YOUR_SEMANTIC_MODEL_ID"              # ← Replace
SEMANTIC_MODEL_NAME = "YOUR_SEMANTIC_MODEL_NAME"          # ← Replace (e.g., "SM_Finance")

AGENT_NAME = "YOUR_AGENT_NAME"                            # ← Replace (e.g., "Finance_Controller")
AGENT_DESCRIPTION = "YOUR_AGENT_DESCRIPTION"              # ← Replace (max 256 chars)

# Data source folder: {type}-{displayName} — MUST use hyphen, not underscore
DATASOURCE_FOLDER = f"semantic-model-{SEMANTIC_MODEL_NAME}"

# Path to instructions markdown file
INSTRUCTIONS_PATH = os.path.join(os.path.dirname(__file__), "..", "docs", "data_agent_instructions.md")

# Path to few-shots JSON file (optional — set None to use empty fewshots)
FEWSHOTS_PATH = os.path.join(os.path.dirname(__file__), "..", "docs", "fewshots.json")

# Path to model.bim (optional — set None to skip element auto-generation)
# When set, all tables/columns/measures from model.bim are auto-selected
MODEL_BIM_PATH = os.path.join(os.path.dirname(__file__), "..", "model.bim")

# Map model.bim dataType → datasource.json data_type
DTYPE_MAP = {
    "string": "string", "int64": "int64", "double": "double",
    "boolean": "boolean", "dateTime": "dateTime", "decimal": "decimal",
}

# ═══════════════════════════════════════════════════════════════════════════════
# AUTH
# ═══════════════════════════════════════════════════════════════════════════════

def get_token():
    """Get access token via Azure CLI."""
    result = subprocess.run(
        "az account get-access-token --resource https://api.fabric.microsoft.com --query accessToken -o tsv",
        capture_output=True, text=True, shell=True,
    )
    token = result.stdout.strip()
    if not token:
        print("ERROR: Could not get access token. Run 'az login' first.")
        sys.exit(1)
    return token


def headers(token):
    return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}


# ═══════════════════════════════════════════════════════════════════════════════
# HELPERS
# ═══════════════════════════════════════════════════════════════════════════════

def b64(obj):
    """Base64-encode a Python object as JSON."""
    return base64.b64encode(json.dumps(obj, ensure_ascii=False).encode("utf-8")).decode("ascii")


def poll_operation(token, resp, max_wait=120):
    """Poll an async Fabric operation until completion.

    IMPORTANT: For updateDefinition, do NOT fetch the result — just poll status.
    The /operations/{id}/result endpoint on api.fabric.microsoft.com may hang
    (SSL read timeout). Use the Location header redirect URL only for getDefinition.
    """
    h = headers(token)
    op_id = resp.headers.get("x-ms-operation-id")
    retry_after = int(resp.headers.get("Retry-After", "5"))
    print(f"  Async operation: {op_id}")
    for _ in range(max_wait // retry_after):
        time.sleep(retry_after)
        poll_resp = requests.get(f"{API}/operations/{op_id}", headers=h)
        op = poll_resp.json()
        status = op.get("status", "Unknown")
        print(f"  ... {status}")
        if status == "Succeeded":
            return True
        if status in ("Failed", "Cancelled"):
            print(f"  ERROR: {json.dumps(op.get('error', {}), indent=2)}")
            return False
    print("  TIMEOUT")
    return False


def find_agent(token):
    """Find an existing Data Agent by name. Returns agent ID or None."""
    h = headers(token)
    resp = requests.get(f"{API}/workspaces/{WORKSPACE_ID}/items?type=DataAgent", headers=h)
    if resp.status_code == 200:
        for item in resp.json().get("value", []):
            if item["displayName"] == AGENT_NAME:
                return item["id"]
    return None


# ═══════════════════════════════════════════════════════════════════════════════
# DEFINITION BUILDERS
# ═══════════════════════════════════════════════════════════════════════════════

def build_elements():
    """Read model.bim and build the full elements array (all tables selected).

    Returns None if MODEL_BIM_PATH is not set or file doesn't exist.
    This auto-selects ALL tables, columns, and measures from the semantic model.
    """
    if not MODEL_BIM_PATH:
        return None
    bim_path = os.path.normpath(MODEL_BIM_PATH)
    if not os.path.exists(bim_path):
        print(f"  WARNING: model.bim not found at {bim_path}, skipping elements")
        return None

    with open(bim_path, "r", encoding="utf-8") as f:
        model = json.load(f)

    elements = []
    for table in model["model"]["tables"]:
        children = []
        for col in table.get("columns", []):
            children.append({
                "id": None, "display_name": col["name"],
                "type": "semantic_model.column",
                "data_type": DTYPE_MAP.get(col.get("dataType", "string"), "string"),
                "is_selected": True, "description": None, "children": [],
            })
        for measure in table.get("measures", []):
            children.append({
                "id": None, "display_name": measure["name"],
                "type": "semantic_model.measure",
                "is_selected": True, "description": None, "children": [],
            })
        elements.append({
            "id": None, "display_name": table["name"],
            "type": "semantic_model.table",
            "is_selected": True, "description": None,
            "children": children,
        })
    return elements


def build_datasource():
    """Build datasource.json for the configured semantic model."""
    ds = {
        "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/dataAgent/definition/dataSource/1.0.0/schema.json",
        "artifactId": SEMANTIC_MODEL_ID,
        "workspaceId": WORKSPACE_ID,
        "displayName": SEMANTIC_MODEL_NAME,
        "type": "semantic_model",
        "userDescription": f"Semantic model: {SEMANTIC_MODEL_NAME}",
        "dataSourceInstructions": "Use DAX measures whenever available instead of raw column calculations.",
    }
    elements = build_elements()
    if elements:
        ds["elements"] = elements
        total_children = sum(len(e["children"]) for e in elements)
        print(f"  Elements: {len(elements)} tables, {total_children} columns/measures")
    return ds


def build_fewshots():
    """Build fewshots.json from external file or return empty."""
    base = {
        "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/dataAgent/definition/fewShots/1.0.0/schema.json",
        "fewShots": [],
    }
    if FEWSHOTS_PATH:
        path = os.path.normpath(FEWSHOTS_PATH)
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            shots = data.get("fewShots", data if isinstance(data, list) else [])
            for shot in shots:
                if "id" not in shot:
                    shot["id"] = str(uuid.uuid4())
            base["fewShots"] = shots
            print(f"  Few-shots: {len(shots)} examples from {path}")
        else:
            print(f"  WARNING: fewshots file not found at {path}")
    return base


def build_definition_parts(instructions_text, publish=True):
    """Build all definition parts.

    Args:
        publish: If True (default), include published/ parts + publish_info.json.
                 Agents MUST be published to be visible in the Fabric portal.
    """
    data_agent_json = {
        "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/dataAgent/definition/dataAgent/2.1.0/schema.json"
    }
    stage_config = {
        "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/dataAgent/definition/stageConfiguration/1.0.0/schema.json",
        "aiInstructions": instructions_text,
    }
    datasource = build_datasource()
    fewshots = build_fewshots()

    ds_stage = b64(stage_config)
    ds_datasource = b64(datasource)
    ds_fewshots = b64(fewshots)

    parts = [
        {"path": "Files/Config/data_agent.json", "payload": b64(data_agent_json), "payloadType": "InlineBase64"},
        {"path": "Files/Config/draft/stage_config.json", "payload": ds_stage, "payloadType": "InlineBase64"},
        {"path": f"Files/Config/draft/{DATASOURCE_FOLDER}/datasource.json", "payload": ds_datasource, "payloadType": "InlineBase64"},
        {"path": f"Files/Config/draft/{DATASOURCE_FOLDER}/fewshots.json", "payload": ds_fewshots, "payloadType": "InlineBase64"},
    ]

    if publish:
        publish_info = {
            "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/dataAgent/definition/publishInfo/1.0.0/schema.json",
            "description": f"{AGENT_NAME} -- Published on {time.strftime('%Y-%m-%d')}",
        }
        parts.extend([
            {"path": "Files/Config/publish_info.json", "payload": b64(publish_info), "payloadType": "InlineBase64"},
            {"path": "Files/Config/published/stage_config.json", "payload": ds_stage, "payloadType": "InlineBase64"},
            {"path": f"Files/Config/published/{DATASOURCE_FOLDER}/datasource.json", "payload": ds_datasource, "payloadType": "InlineBase64"},
            {"path": f"Files/Config/published/{DATASOURCE_FOLDER}/fewshots.json", "payload": ds_fewshots, "payloadType": "InlineBase64"},
        ])

    return parts


# ═══════════════════════════════════════════════════════════════════════════════
# ACTIONS
# ═══════════════════════════════════════════════════════════════════════════════

def create_agent(token, instructions_text, publish=True):
    """Create a new Data Agent."""
    h = headers(token)
    parts = build_definition_parts(instructions_text, publish=publish)
    body = {
        "displayName": AGENT_NAME,
        "description": AGENT_DESCRIPTION,
        "type": "DataAgent",
        "definition": {"parts": parts},
    }

    print(f"Creating Data Agent '{AGENT_NAME}'...")
    print(f"  Parts: {len(parts)} ({'published' if publish else 'draft only'})")
    resp = requests.post(f"{API}/workspaces/{WORKSPACE_ID}/items", headers=h, json=body)

    if resp.status_code == 201:
        agent = resp.json()
        print(f"  Created: {agent['id']}")
        return agent["id"]
    elif resp.status_code == 202:
        ok = poll_operation(token, resp)
        if ok:
            return find_agent(token)
    else:
        print(f"  FAILED ({resp.status_code}): {resp.text}")
    return None


def update_agent(token, agent_id, instructions_text, publish=True):
    """Update an existing Data Agent's definition."""
    h = headers(token)
    parts = build_definition_parts(instructions_text, publish=publish)
    body = {"definition": {"parts": parts}}

    mode = "publish" if publish else "draft only"
    print(f"Updating Data Agent '{AGENT_NAME}' ({agent_id}) [{mode}]...")
    print(f"  Parts: {len(parts)}")
    resp = requests.post(f"{API}/workspaces/{WORKSPACE_ID}/items/{agent_id}/updateDefinition", headers=h, json=body)

    if resp.status_code == 200:
        print("  Updated (sync)")
        return True
    elif resp.status_code == 202:
        return poll_operation(token, resp)
    else:
        print(f"  FAILED ({resp.status_code}): {resp.text}")
        return False


def update_properties(token, agent_id):
    """Update agent display name and description via PATCH."""
    h = headers(token)
    body = {"displayName": AGENT_NAME, "description": AGENT_DESCRIPTION}
    print(f"Updating properties...")
    resp = requests.patch(f"{API}/workspaces/{WORKSPACE_ID}/dataAgents/{agent_id}", headers=h, json=body)
    if resp.status_code == 200:
        print("  Properties updated")
        return True
    else:
        print(f"  FAILED ({resp.status_code}): {resp.text}")
        return False


def delete_agent(token, agent_id):
    """Delete a Data Agent."""
    h = headers(token)
    print(f"Deleting Data Agent {agent_id}...")
    resp = requests.delete(f"{API}/workspaces/{WORKSPACE_ID}/items/{agent_id}", headers=h)
    if resp.status_code in (200, 204):
        print("  Deleted")
        return True
    else:
        print(f"  FAILED ({resp.status_code}): {resp.text}")
        return False


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(description="Deploy Fabric Data Agent")
    parser.add_argument("--draft-only", action="store_true",
                        help="Deploy draft only (NOT visible in portal until published)")
    parser.add_argument("--delete", action="store_true", help="Delete the agent")
    args = parser.parse_args()

    token = get_token()

    if args.delete:
        agent_id = find_agent(token)
        if agent_id:
            delete_agent(token, agent_id)
        else:
            print(f"No agent named '{AGENT_NAME}' found.")
        return

    # Load instructions
    instructions_path = os.path.normpath(INSTRUCTIONS_PATH)
    print(f"Loading instructions from: {instructions_path}")
    with open(instructions_path, "r", encoding="utf-8") as f:
        instructions_text = f.read()
    print(f"  Instructions: {len(instructions_text)} characters")

    publish = not args.draft_only

    # Create or update
    existing = find_agent(token)
    if existing:
        print(f"Agent '{AGENT_NAME}' already exists ({existing}). Updating...")
        success = update_agent(token, existing, instructions_text, publish=publish)
        if not success:
            sys.exit(1)
        update_properties(token, existing)
    else:
        agent_id = create_agent(token, instructions_text, publish=publish)
        if not agent_id:
            sys.exit(1)

    # Summary
    agent_id = find_agent(token)
    print(f"\n{'='*60}")
    print(f"Agent: {AGENT_NAME}")
    print(f"ID: {agent_id}")
    print(f"Published: {'Yes' if publish else 'No (draft only -- NOT visible in portal)'}")
    print(f"{'='*60}")

    print(f"\nNext steps:")
    print(f"  1. Open in Fabric portal:")
    print(f"     https://app.fabric.microsoft.com/groups/{WORKSPACE_ID}/dataAgents/{agent_id}")
    print(f"  2. Test with sample questions")
    if not publish:
        print(f"  3. Re-run WITHOUT --draft-only to publish")


if __name__ == "__main__":
    main()
