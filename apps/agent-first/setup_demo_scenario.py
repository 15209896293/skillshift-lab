"""快速创建补正场景，用于前端验证。"""
import json
import uuid
import urllib.request

BASE = "http://127.0.0.1:8000/api/v1/demo"
SCHEMA = "skillshift-api/v1"


def post(path, role, data, idemp_key=None, if_match=None):
    url = f"{BASE}/{role}{path}"
    body = json.dumps({"schema_version": SCHEMA, **data}).encode("utf-8")
    req = urllib.request.Request(url, data=body, method="POST")
    req.add_header("Content-Type", "application/json")
    req.add_header("Idempotency-Key", idemp_key or str(uuid.uuid4()))
    if if_match is not None:
        req.add_header("If-Match", str(if_match))
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode("utf-8"))


# 1. Create assignment
r = post(
    "/assignments",
    "teacher",
    {
        "title": "Order Data Cleaning",
        "goal": "Use Python to clean order CSV data, identify missing values and anomalies.",
        "student_responsibility": "Verify cleaning rules, check results, explain your reasoning.",
        "submission_requirement": "Submit main.py script and README documentation.",
        "starter_project_id": "orders-audit-v1",
        "collaboration_mode": "PROPOSE_WITH_STUDENT_CONFIRMATION",
    },
)
aid = r["data"]["id"]
arev = r["data"]["revision"]
print(f"Created: {aid} rev={arev}")

# 2. Publish (needs If-Match with assignment revision)
r = post(
    f"/assignments/{aid}/publish",
    "teacher",
    {},
    idemp_key=f"publish-{aid}",
    if_match=arev,
)
wid = r["data"]["workspace"]["id"]
wrev = r["data"]["workspace"]["revision"]
print(f"Published: workspace={wid} wrev={wrev}")

# 3. Start workspace (needs If-Match with workspace revision)
r = post(
    f"/workspaces/{wid}/start",
    "student",
    {},
    idemp_key=f"start-{wid}",
    if_match=wrev,
)
wrev = r["data"]["workspace"]["revision"]
print(f"Started: wrev={wrev}")

# 4. Submit
r = post(
    f"/workspaces/{wid}/submissions",
    "student",
    {
        "artifact_refs": ["main.py", "orders.csv", "README.md"],
        "artifact_contents": {
            "main.py": "print('hello')\n",
            "orders.csv": "id,name\n1,test\n",
            "README.md": "# Demo\n",
        },
        "student_explanation": "I completed the basic version of the data cleaning script, including the framework. I will continue to improve the anomaly detection.",
    },
    idemp_key=f"submit-{wid}-1",
    if_match=wrev,
)
sid = r["data"]["submission"]["id"]
sver = r["data"]["submission"]["version"]
wrev = r["data"]["workspace_revision"]
print(f"Submitted: {sid} v{sver} wrev={wrev}")

# 5. Request remediation
r = post(
    f"/submissions/{sid}/review-actions",
    "teacher",
    {
        "kind": "REQUEST_REMEDIATION",
        "reason": "The code lacks actual data cleaning logic and anomaly detection. Please supplement the complete implementation.",
    },
    idemp_key=f"review-{sid}-1",
    if_match=wrev,
)
wrev = r["data"]["workspace_revision"]
print(f"Remediation requested: wrev={wrev}")

print(f"\nDONE - assignment={aid}, workspace={wid}, submission={sid}")
