"""
Deploy a Fabric Data Agent — Template Script

This template creates a Data Agent with:
  1. AI instructions (from a markdown file)
  2. Data source binding (semantic model)
  3. Few-shot examples (from a JSON file or inline)

Usage:
    python deploy_data_agent.py                    # Create new agent
    python deploy_data_agent.py --update           # Update existing agent
    python deploy_data_agent.py --update --publish  # Update + publish

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
WORKSPACE_ID = "YOUR_WORKSPACE_ID"                      # ← Replace
SEMANTIC_MODEL_ID = "YOUR_SEMANTIC_MODEL_ID"             # ← Replace
SEMANTIC_MODEL_NAME = "YOUR_SEMANTIC_MODEL_NAME"         # ← Replace (e.g., "SM_Finance")

AGENT_NAME = "YOUR_AGENT_NAME"                           # ← Replace (e.g., "Finance_Controller")
AGENT_DESCRIPTION = "YOUR_AGENT_DESCRIPTION"             # ← Replace (max 256 chars)

# Path to instructions markdown file
INSTRUCTIONS_PATH = os.path.join(os.path.dirname(__file__), "..", "docs", "data_agent_instructions.md")

# Path to few-shots JSON file (optional — set None to skip)
FEWSHOTS_PATH = None  # e.g., os.path.join(os.path.dirname(__file__), "..", "docs", "fewshots.json")

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


def poll_operation(token, op_id, max_wait=120):
    """Poll an async Fabric operation until completion."""
    h = headers(token)
    for _ in range(max_wait // 5):
        time.sleep(5)
        resp = requests.get(f"{API}/operations/{op_id}", headers=h)
        op = resp.json()
        status = op.get("status", "Unknown")
        print(f"  ... {status}")
        if status == "Succeeded":
            return op
        if status in ("Failed", "Cancelled"):
            print(f"  ERROR: {json.dumps(op.get('error', {}), indent=2)}")
            return op
    print("  TIMEOUT waiting for operation")
    return None


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
# DEFINITION BUILDER
# ═══════════════════════════════════════════════════════════════════════════════

def build_data_agent_json():
    """Build the top-level data_agent.json."""
    return {
        "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/dataAgent/definition/dataAgent/2.1.0/schema.json"
    }


def build_stage_config(instructions_text):
    """Build stage_config.json with AI instructions."""
    return {
        "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/dataAgent/definition/stageConfiguration/1.0.0/schema.json",
        "aiInstructions": instructions_text,
    }


def build_datasource():
    """Build datasource.json for semantic model binding."""
    return {
        "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/dataAgent/definition/dataSource/1.0.0/schema.json",
        "artifactId": SEMANTIC_MODEL_ID,
        "workspaceId": WORKSPACE_ID,
        "displayName": SEMANTIC_MODEL_NAME,
        "type": "semantic_model",
        "userDescription": f"Semantic model: {SEMANTIC_MODEL_NAME}",
        "dataSourceInstructions": "Use DAX measures whenever available instead of raw column calculations.",
    }


def build_fewshots(fewshots_path=None):
    """Build fewshots.json from file or return empty."""
    base = {
        "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/dataAgent/definition/fewShots/1.0.0/schema.json",
        "fewShots": [],
    }
    if fewshots_path and os.path.exists(fewshots_path):
        with open(fewshots_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        base["fewShots"] = data.get("fewShots", data if isinstance(data, list) else [])
        # Ensure all examples have IDs
        for shot in base["fewShots"]:
            if "id" not in shot:
                shot["id"] = str(uuid.uuid4())
    return base


def build_publish_info():
    """Build publish_info.json."""
    return {
        "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/dataAgent/definition/publishInfo/1.0.0/schema.json",
        "description": f"{AGENT_NAME} — Published on {time.strftime('%Y-%m-%d')}",
    }


def build_definition_parts(instructions_text, publish=False):
    """Build all definition parts."""
    ds_folder = f"semantic_model-{SEMANTIC_MODEL_NAME}"

    parts = [
        {"path": "Files/Config/data_agent.json", "payload": b64(build_data_agent_json()), "payloadType": "InlineBase64"},
        {"path": "Files/Config/draft/stage_config.json", "payload": b64(build_stage_config(instructions_text)), "payloadType": "InlineBase64"},
        {"path": f"Files/Config/draft/{ds_folder}/datasource.json", "payload": b64(build_datasource()), "payloadType": "InlineBase64"},
        {"path": f"Files/Config/draft/{ds_folder}/fewshots.json", "payload": b64(build_fewshots(FEWSHOTS_PATH)), "payloadType": "InlineBase64"},
    ]

    if publish:
        parts.extend([
            {"path": "Files/Config/published/stage_config.json", "payload": b64(build_stage_config(instructions_text)), "payloadType": "InlineBase64"},
            {"path": f"Files/Config/published/{ds_folder}/datasource.json", "payload": b64(build_datasource()), "payloadType": "InlineBase64"},
            {"path": f"Files/Config/published/{ds_folder}/fewshots.json", "payload": b64(build_fewshots(FEWSHOTS_PATH)), "payloadType": "InlineBase64"},
            {"path": "Files/Config/publish_info.json", "payload": b64(build_publish_info()), "payloadType": "InlineBase64"},
        ])

    return parts


# ═══════════════════════════════════════════════════════════════════════════════
# ACTIONS
# ═══════════════════════════════════════════════════════════════════════════════

def create_agent(token, instructions_text, publish=False):
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
    print(f"  Parts: {len(parts)}")
    resp = requests.post(f"{API}/workspaces/{WORKSPACE_ID}/items", headers=h, json=body)

    if resp.status_code == 201:
        agent = resp.json()
        print(f"  Created: {agent['id']}")
        return agent["id"]
    elif resp.status_code == 202:
        op_id = resp.headers.get("x-ms-operation-id")
        print(f"  Async operation: {op_id}")
        result = poll_operation(token, op_id)
        if result and result.get("status") == "Succeeded":
            r2 = requests.get(f"{API}/operations/{op_id}/result", headers=h)
            if r2.status_code == 200:
                agent = r2.json()
                print(f"  Created: {agent.get('id', 'unknown')}")
                return agent.get("id")
            # If result endpoint doesn't return the agent, find it by name
            return find_agent(token)
    else:
        print(f"  FAILED ({resp.status_code}): {resp.text}")
    return None


def update_agent(token, agent_id, instructions_text, publish=False):
    """Update an existing Data Agent's definition."""
    h = headers(token)
    parts = build_definition_parts(instructions_text, publish=publish)
    body = {"definition": {"parts": parts}}

    print(f"Updating Data Agent '{AGENT_NAME}' ({agent_id})...")
    print(f"  Parts: {len(parts)}")
    resp = requests.post(f"{API}/workspaces/{WORKSPACE_ID}/items/{agent_id}/updateDefinition", headers=h, json=body)

    if resp.status_code == 200:
        print("  Updated (sync)")
        return True
    elif resp.status_code == 202:
        op_id = resp.headers.get("x-ms-operation-id")
        result = poll_operation(token, op_id)
        return result and result.get("status") == "Succeeded"
    else:
        print(f"  FAILED ({resp.status_code}): {resp.text}")
        return False


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(description="Deploy Fabric Data Agent")
    parser.add_argument("--update", action="store_true", help="Update existing agent")
    parser.add_argument("--publish", action="store_true", help="Also publish the agent")
    args = parser.parse_args()

    token = get_token()

    # Load instructions
    instructions_path = os.path.normpath(INSTRUCTIONS_PATH)
    print(f"Loading instructions from: {instructions_path}")
    with open(instructions_path, "r", encoding="utf-8") as f:
        instructions_text = f.read()
    print(f"  Instructions: {len(instructions_text)} characters")

    if args.update:
        agent_id = find_agent(token)
        if not agent_id:
            print("ERROR: Agent not found. Run without --update to create it.")
            sys.exit(1)
        success = update_agent(token, agent_id, instructions_text, publish=args.publish)
        if not success:
            sys.exit(1)
    else:
        existing = find_agent(token)
        if existing:
            print(f"Agent '{AGENT_NAME}' already exists ({existing}). Updating instead.")
            success = update_agent(token, existing, instructions_text, publish=args.publish)
            if not success:
                sys.exit(1)
        else:
            agent_id = create_agent(token, instructions_text, publish=args.publish)
            if not agent_id:
                sys.exit(1)

    # Summary
    agent_id = find_agent(token)
    print(f"\n{'='*60}")
    print(f"Agent: {AGENT_NAME}")
    print(f"ID: {agent_id}")
    print(f"Published: {'Yes' if args.publish else 'No (draft only)'}")
    print(f"{'='*60}")
    print(f"\nNext steps:")
    print(f"  1. Open in Fabric portal:")
    print(f"     https://app.fabric.microsoft.com/groups/{WORKSPACE_ID}/dataAgents/{agent_id}")
    print(f"  2. Verify data source is connected")
    print(f"  3. Test with sample questions")
    if not args.publish:
        print(f"  4. When ready, re-run with --publish flag")


if __name__ == "__main__":
    main()
