"""
Template: Full orchestration script — Upload CSVs, create pipeline, run and monitor.

Usage:
    1. Set PATH: $env:PATH = "C:\\Users\\<user>\\AppData\\Local\\Programs\\Python\\Python312;..."
    2. Ensure az login is done
    3. Run: python orchestrate_ingestion.py

Customize the CONFIG section for your use case.
"""
import requests, json, base64, time, os, subprocess, sys

# ── CONFIG ─────────────────────────────────────────────────────
WS_ID      = "133c6c70-2e26-4d97-aac1-8ed423dbbf34"
LH_ID      = "f2c42d3b-d402-43e7-b8fb-a9aa395c14e1"
NB_ID      = "86729c39-33a4-454a-8170-0ac363ee809c"
PL_ID      = "7fdd5622-9313-4a5f-a769-dccef65a5015"  # Existing pipeline, or None to create
API        = "https://api.fabric.microsoft.com/v1"
ONELAKE    = f"https://onelake.dfs.fabric.microsoft.com/{WS_ID}/{LH_ID}/Files"
LOCAL_DATA = "data/raw"  # Local folder with CSV subfolders
# ───────────────────────────────────────────────────────────────


def get_token(resource: str) -> str:
    """Get Azure AD token via az CLI."""
    result = subprocess.run(
        ["az", "account", "get-access-token", "--resource", resource,
         "--query", "accessToken", "-o", "tsv"],
        capture_output=True, text=True, shell=True
    )
    token = result.stdout.strip()
    if not token:
        raise RuntimeError(f"Failed to get token for {resource}: {result.stderr}")
    return token


def upload_to_onelake(local_path: str, remote_path: str, headers: dict) -> int:
    """Upload a single file to OneLake using 3-step ADLS protocol."""
    url = f"{ONELAKE}/{remote_path}"
    
    requests.put(f"{url}?resource=file", headers=headers)
    
    with open(local_path, "rb") as f:
        data = f.read()
    
    requests.patch(
        f"{url}?action=append&position=0",
        headers={**headers, "Content-Type": "application/octet-stream"},
        data=data,
    )
    
    requests.patch(f"{url}?action=flush&position={len(data)}", headers=headers)
    return len(data)


def poll_operation(op_id: str, headers: dict, timeout: int = 300) -> dict:
    """Poll async operation until completion."""
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
            raise RuntimeError(f"Operation {status}: {error}")
        
        print(f"  [{elapsed:.0f}s] {status}...")
        time.sleep(5)
    
    raise TimeoutError(f"Operation did not complete in {timeout}s")


def main():
    print("=== Fabric Ingestion Orchestrator ===\n")
    
    # 1. Get tokens
    print("1. Authenticating...")
    fabric_token = get_token("https://api.fabric.microsoft.com")
    storage_token = get_token("https://storage.azure.com")
    fabric_h = {"Authorization": f"Bearer {fabric_token}", "Content-Type": "application/json"}
    storage_h = {"Authorization": f"Bearer {storage_token}"}
    print("   ✓ Tokens acquired\n")
    
    # 2. Upload CSVs to OneLake
    print("2. Uploading files to OneLake...")
    if os.path.isdir(LOCAL_DATA):
        total_bytes = 0
        file_count = 0
        for root, dirs, files in os.walk(LOCAL_DATA):
            for fname in files:
                local = os.path.join(root, fname)
                relative = os.path.relpath(local, LOCAL_DATA).replace("\\", "/")
                remote = f"raw/{relative}"
                size = upload_to_onelake(local, remote, storage_h)
                total_bytes += size
                file_count += 1
                print(f"   ✓ {relative} ({size:,} bytes)")
        print(f"   Uploaded {file_count} files ({total_bytes:,} bytes)\n")
    else:
        print(f"   Skipping upload (no local data at {LOCAL_DATA})\n")
    
    # 3. Run pipeline
    print(f"3. Running pipeline {PL_ID}...")
    resp = requests.post(
        f"{API}/workspaces/{WS_ID}/items/{PL_ID}/jobs/instances?jobType=Pipeline",
        headers=fabric_h,
        json={"executionData": {}}
    )
    
    if resp.status_code == 202:
        op_id = resp.headers["x-ms-operation-id"]
        print(f"   Operation: {op_id}")
        result = poll_operation(op_id, fabric_h, timeout=600)
        print("   ✓ Pipeline completed!\n")
    elif resp.status_code == 200:
        print("   ✓ Pipeline completed (sync)\n")
    else:
        print(f"   ✗ Failed: {resp.status_code} {resp.text}\n")
        sys.exit(1)
    
    print("=== Done ===")


if __name__ == "__main__":
    main()
