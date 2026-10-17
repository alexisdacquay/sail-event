"""On-call responder — stdlib HTTP server that receives Grafana alert webhooks,
collects evidence, launches a headless Claude Code agent, and records a verdict.
"""

import json
import os
import subprocess
import sys
import threading
from datetime import datetime, timezone
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
INCIDENTS_DIR = REPO_ROOT / "incidents"
INCIDENT_RESPONSE_DIR = REPO_ROOT / "incident-response"
CLAUDE_BIN = os.environ.get("CLAUDE_BIN", "claude")
PORT = int(os.environ.get("RESPONDER_PORT", "8001"))


def _log(msg: str) -> None:
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    print(f"[{ts}] {msg}", flush=True)


def _handle_alert(alert: dict) -> None:
    """Process one firing alert end-to-end in a background thread."""
    status = alert.get("status", "")
    labels = alert.get("labels", {})
    alertname = labels.get("alertname", "unknown")

    if status != "firing":
        _log(f"ignoring {status} alert: {alertname}")
        return

    # Create incident directory
    ts = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    incident_id = f"{ts}-{alertname}"
    incident_dir = INCIDENTS_DIR / incident_id
    incident_dir.mkdir(parents=True, exist_ok=True)
    _log(f"created incident: {incident_id}")

    # Write raw alert
    (incident_dir / "alert.json").write_text(json.dumps(alert, indent=2))

    # Collect evidence
    _log(f"collecting evidence for {incident_id}")
    evidence_script = INCIDENT_RESPONSE_DIR / "collect-evidence.sh"
    subprocess.run(
        ["bash", str(evidence_script), str(incident_dir)],
        cwd=str(REPO_ROOT),
        timeout=60,
    )

    # Read evidence and task prompt
    evidence = (incident_dir / "evidence.md").read_text()
    task_template = (INCIDENT_RESPONSE_DIR / "responder-task.md").read_text()
    prompt = task_template.replace("{evidence}", evidence).replace("{incident_id}", incident_id)

    # Create git worktree
    worktree_path = REPO_ROOT.parent / f"sail-incident-{incident_id}"
    _log(f"creating worktree at {worktree_path}")
    subprocess.run(
        ["git", "worktree", "add", str(worktree_path), "HEAD"],
        cwd=str(REPO_ROOT),
        check=True,
    )

    # Launch claude agent in the worktree
    _log(f"launching agent for {incident_id}")
    agent_log = incident_dir / "agent.log"
    # Clear env vars that force desktop-app auth path; the CLI falls back to
    # its key helper, which works in headless subprocesses.
    agent_env = {k: v for k, v in os.environ.items()
                 if k not in ("CLAUDE_CODE_ENTRYPOINT", "CLAUDE_AGENT_SDK_VERSION",
                              "__CFBundleIdentifier")}
    try:
        with open(agent_log, "w") as log_fh:
            subprocess.run(
                [
                    CLAUDE_BIN, "-p",
                    "--model", "sonnet",
                    "--allowedTools",
                    "Read", "Edit",
                    "Bash(make test)", "Bash(cat *)", "Bash(grep *)", "Bash(find *)",
                    "Bash(ls *)", "Bash(head *)", "Bash(tail *)",
                    "Bash(git log *)", "Bash(git diff *)", "Bash(git status)",
                    "Bash(git add *)", "Bash(git commit *)", "Bash(git checkout -b *)",
                    "--max-budget-usd", "1",
                    prompt,
                ],
                cwd=str(worktree_path),
                env=agent_env,
                stdout=log_fh,
                stderr=subprocess.STDOUT,
                timeout=300,
            )
    except subprocess.TimeoutExpired:
        _log(f"agent timed out for {incident_id}")

    # Copy verdict
    verdict_src = worktree_path / "verdict.json"
    if verdict_src.exists():
        verdict_text = verdict_src.read_text()
        (incident_dir / "verdict.json").write_text(verdict_text)
        _log(f"agent finished with verdict: {incident_id}")
    else:
        _log(f"no verdict.json produced for {incident_id}")

    # Clean up worktree but leave the branch
    _log(f"removing worktree for {incident_id}")
    subprocess.run(
        ["git", "worktree", "remove", "--force", str(worktree_path)],
        cwd=str(REPO_ROOT),
    )


class AlertHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        if self.path != "/alerts":
            self.send_response(404)
            self.end_headers()
            return

        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length)
        self.send_response(202)
        self.end_headers()

        try:
            payload = json.loads(body)
        except json.JSONDecodeError:
            _log("invalid JSON in webhook")
            return

        # Grafana sends {"alerts": [...]} or a bare array
        alerts = payload if isinstance(payload, list) else payload.get("alerts", [])
        _log(f"received {len(alerts)} alert(s)")

        for alert in alerts:
            thread = threading.Thread(
                target=_handle_alert, args=(alert,), daemon=True
            )
            thread.start()

    def do_GET(self):
        self.send_response(404)
        self.end_headers()

    def log_message(self, format, *args):
        pass  # suppress default access log


def main():
    INCIDENTS_DIR.mkdir(parents=True, exist_ok=True)
    server = HTTPServer(("", PORT), AlertHandler)
    _log(f"listening on :{PORT}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        _log("shutting down")
        server.server_close()


if __name__ == "__main__":
    main()
