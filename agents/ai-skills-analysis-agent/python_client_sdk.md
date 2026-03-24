# Consuming a Data Agent with the Python Client SDK

> **Source**: [Consume a Fabric data agent with the Python client SDK (preview)](https://learn.microsoft.com/en-us/fabric/data-science/consume-data-agent-python)  
> **Client Repo**: [GitHub — fabric_data_agent_client](https://github.com/microsoft/fabric_data_agent_client)  
> **SDK Docs**: [Fabric Data Agent Python SDK](https://learn.microsoft.com/en-us/fabric/data-science/fabric-data-agent-sdk)

---

## Overview

The Python client SDK lets you embed a Fabric Data Agent into web apps, automation scripts,
and custom interfaces. Unlike the evaluation SDK (which runs in Fabric notebooks only),
the client SDK runs **locally or in any Python environment**.

---

## Prerequisites

| Requirement | Details |
|-------------|---------|
| Fabric capacity | F2 or higher, or Power BI Premium P1+ with Fabric enabled |
| Tenant settings | Data Agent tenant settings enabled |
| Cross-geo AI | Cross-geo processing and storing for AI enabled |
| XMLA endpoints | Enabled (for Power BI semantic model data sources) |
| Python | >= 3.10 |
| Published agent | Agent must be published (or use sandbox stage) |
| Published URL | The Data Agent's published URL (from Fabric portal) |

---

## Step 1: Environment Setup

### Clone the Client Repository

```bash
git clone https://github.com/microsoft/fabric_data_agent_client.git
cd fabric_data_agent_client
```

### Create Virtual Environment

```bash
# Create
python -m venv .venv

# Activate (Windows)
.venv\Scripts\activate

# Activate (macOS/Linux)
source .venv/bin/activate
```

### Install Dependencies

```bash
pip install -r requirements.txt
```

**Key packages**:
- `azure-identity` — Microsoft Entra ID authentication
- `fabric-data-agent-client` — The client SDK itself

---

## Step 2: Configure the Client

Set the required values: `TENANT_ID` and `DATA_AGENT_URL`.

### Option A: Environment Variables

```bash
# Windows
set TENANT_ID=<your-azure-tenant-id>
set DATA_AGENT_URL=<your-fabric-data-agent-url>

# macOS/Linux
export TENANT_ID=<your-azure-tenant-id>
export DATA_AGENT_URL=<your-fabric-data-agent-url>
```

### Option B: .env File

Create a `.env` file in the project root:

```env
TENANT_ID=<your-azure-tenant-id>
DATA_AGENT_URL=<your-fabric-data-agent-url>
```

### Option C: Direct Configuration in Script

```python
TENANT_ID = "<your-azure-tenant-id>"
DATA_AGENT_URL = "<your-fabric-data-agent-url>"
```

### Finding the Values

| Value | Where to Find |
|-------|---------------|
| `TENANT_ID` | Azure portal → Microsoft Entra ID → Overview → Tenant ID |
| `DATA_AGENT_URL` | Fabric portal → Data Agent → Publish → Copy URL |

---

## Step 3: Authenticate

```python
from azure.identity import InteractiveBrowserCredential
from fabric_data_agent_client import FabricDataAgentClient

credential = InteractiveBrowserCredential()
```

`InteractiveBrowserCredential` opens a browser window for interactive sign-in with Microsoft Entra ID.
The data agent runs with the authenticated user's permissions.

**Note**: For automated/headless scenarios, use `ClientSecretCredential` or `ManagedIdentityCredential` instead.

---

## Step 4: Create the Client

```python
client = FabricDataAgentClient(credential=credential)
```

---

## Step 5: Ask Questions

### Simple Query

```python
response = client.ask("What were the total sales last quarter?")
print(f"Response: {response}")
```

### Get Full Run Details

```python
run_details = client.get_run_details("What were the total sales last quarter?")

# Extract assistant messages
messages = run_details.get('messages', {}).get('data', [])
assistant_messages = [msg for msg in messages if msg.get('role') == 'assistant']

print("Answer:", assistant_messages[-1])
```

---

## Step 6: Inspect Execution Steps

Walk through the tool calls the agent executed to produce the answer:

```python
for step in run_details['run_steps']['data']:
    tool_name = "N/A"
    if 'step_details' in step and step['step_details'] and 'tool_calls' in step['step_details']:
        tool_calls = step['step_details']['tool_calls']
        if tool_calls and len(tool_calls) > 0 and 'function' in tool_calls[0]:
            tool_name = tool_calls[0]['function'].get('name', 'N/A')
    
    print(f"Step ID: {step.get('id')}, Type: {step.get('type')}, Status: {step.get('status')}, Tool Name: {tool_name}")
    
    if 'error' in step:
        print(f"  Error: {step['error']}")
```

This reveals:
- Which tools were called (NL2SQL, NL2SA, NL2KQL)
- What DAX/SQL/KQL was generated
- Whether any step failed
- The data returned by each tool

---

## Complete Example

```python
from azure.identity import InteractiveBrowserCredential
from fabric_data_agent_client import FabricDataAgentClient

# 1. Authenticate
credential = InteractiveBrowserCredential()
client = FabricDataAgentClient(credential=credential)

# 2. Ask a question
response = client.ask("What is the churn rate for 2025?")
print(f"Answer: {response}")

# 3. Get full execution details
run_details = client.get_run_details("What is the churn rate for 2025?")

# 4. Extract the assistant's answer
messages = run_details.get('messages', {}).get('data', [])
assistant_msgs = [m for m in messages if m.get('role') == 'assistant']
if assistant_msgs:
    print(f"Full answer: {assistant_msgs[-1]}")

# 5. Inspect tool calls
for step in run_details.get('run_steps', {}).get('data', []):
    tool_calls = (step.get('step_details') or {}).get('tool_calls', [])
    for tc in tool_calls:
        fn = tc.get('function', {})
        print(f"  Tool: {fn.get('name')}")
        print(f"  Output: {fn.get('output', '')[:200]}...")
```

---

## Client SDK vs Evaluation SDK

| Feature | `fabric-data-agent-client` | `fabric-data-agent-sdk` |
|---------|---------------------------|------------------------|
| Environment | Any Python (local, cloud) | Fabric notebooks only |
| Purpose | Consume / embed agent | Evaluate with ground truth |
| Authentication | `InteractiveBrowserCredential` | Notebook identity |
| Key method | `client.ask()`, `client.get_run_details()` | `evaluate_data_agent()`, `get_evaluation_summary()` |
| Output | Single response + trace | Batch evaluation table |
| Stage support | Published URL (production) | `"production"` or `"sandbox"` |

---

## Use Cases

| Scenario | Approach |
|----------|----------|
| Embed in web app | Use client SDK with backend auth |
| Automate reporting | Loop `client.ask()` over question list |
| Debug wrong answers | Use `get_run_details()` to inspect tool calls |
| Batch evaluation | Use evaluation SDK in Fabric notebook |
| CI/CD quality gate | Combine evaluation SDK + notebook job |
| Interactive demo | Use client SDK in a Streamlit/Gradio app |

---

## Security Notes

- The agent runs with the **authenticated user's permissions** — it can only access data the user has access to
- `InteractiveBrowserCredential` requires a browser — not suitable for headless servers
- For production apps, use service principal auth (`ClientSecretCredential`) with appropriate RBAC
- Never hardcode credentials in scripts — use environment variables or Azure Key Vault

---

## Advanced: Batch Diagnostic Automation

Beyond simple `client.ask()` loops, you can build a **full diagnostic pipeline** that combines 3 data sources for portal-equivalent analysis:

### Architecture

```
SDK Auth (InteractiveBrowserCredential)
  ├── 1. Client SDK: get_run_details() → agent answer + tool calls + DAX
  ├── 2. REST API (reuse token): getDefinition → agent config (instructions, data sources)
  └── 3. REST API (reuse token): getDefinition?format=TMDL → model schema (tables, columns, measures, descriptions)
```

### Token Reuse Pattern

The SDK's credential token can be reused for Fabric REST API calls:

```python
from azure.identity import InteractiveBrowserCredential
from fabric_data_agent_client import FabricDataAgentClient

credential = InteractiveBrowserCredential()
client = FabricDataAgentClient(credential=credential)

# Reuse token for REST API calls
token = credential.get_token("https://api.fabric.microsoft.com/.default").token
headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
```

### TMDL Schema Extraction

Fetch the semantic model schema via the getDefinition API:

```python
import requests, base64, time

def fetch_schema(workspace_id, model_id, headers):
    url = f"https://api.fabric.microsoft.com/v1/workspaces/{workspace_id}/semanticModels/{model_id}/getDefinition?format=TMDL"
    r = requests.post(url, headers=headers)
    
    if r.status_code == 202:  # LRO
        loc = r.headers["Location"]
        while True:
            poll = requests.get(loc, headers=headers)
            body = poll.json()
            if body.get("status") == "Succeeded":
                result = requests.get(f"{loc}/result", headers=headers)
                return result.json()
            time.sleep(1)
    return r.json()
```

**TMDL parsing notes**:
- Descriptions use `///` triple-slash doc-comment lines (NOT `description:` properties)
- Collect `///` lines into a pending buffer; assign when the next `table`, `column`, or `measure` line appears
- Each table is a separate `.tmdl` part in the response

### Batch Runner Pattern

```python
import json, re
from datetime import datetime

def run_batch(client, questions_file, output_dir):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results = []
    
    with open(questions_file) as f:
        questions = [q.strip() for q in f if q.strip()]
    
    for q in questions:
        run = client.get_run_details(q)
        messages = run.get("messages", {}).get("data", [])
        assistant = [m for m in messages if m.get("role") == "assistant"]
        
        slug = re.sub(r"[^a-z0-9]+", "_", q.lower())[:40]
        diag = {"question": q, "answer": assistant[-1] if assistant else None, "run_details": run}
        
        with open(f"{output_dir}/full_diag_{slug}_{timestamp}.json", "w") as f:
            json.dump(diag, f, indent=2)
        
        results.append({"question": q, "status": "completed" if assistant else "failed"})
    
    with open(f"{output_dir}/batch_summary_{timestamp}.json", "w") as f:
        json.dump({"timestamp": timestamp, "total": len(results), "results": results}, f, indent=2)
```

### Data Agent URL Pattern

```
https://api.fabric.microsoft.com/v1/workspaces/{WORKSPACE_ID}/aiskills/{AGENT_ID}/aiassistant/openai
```

**Stage parameter**: Append `?stage=sandbox` for testing against unpublished agent changes.
