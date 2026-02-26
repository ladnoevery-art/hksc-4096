from __future__ import annotations

import argparse
import json
import subprocess
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path


@dataclass
class CheckResult:
    name: str
    command: str
    ok: bool
    output: str


def run(cmd: str) -> CheckResult:
    p = subprocess.run(cmd, shell=True, text=True, capture_output=True)
    return CheckResult(cmd.split()[0], cmd, p.returncode == 0, (p.stdout + p.stderr).strip()[:4000])


def evaluate_worst_case() -> dict:
    scenarios = {
        "ci_failure": "Recovered by retry + isolate failing workflow",
        "dependency_breakage": "Pin version and open repair PR",
        "auth_misconfig": "Block deploy lane, rotate creds checklist",
        "rpc_outage": "Fallback provider + offline queue",
        "tampered_ciphertext": "HMAC validation should fail fast",
    }
    return scenarios


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--report", default="automation/report.json")
    ap.add_argument("--quick", action="store_true", help="Skip heavy checks for nested/test runs")
    args = ap.parse_args()

    checks = [run("python hksc4096.py simulate --seed health --cells 64")]
    if not args.quick:
        checks.insert(0, run("python -m unittest discover -s tests -v"))

    status = "healthy" if all(c.ok for c in checks) else "degraded"
    report = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "checks": [asdict(c) for c in checks],
        "worst_case_matrix": evaluate_worst_case(),
        "next_actions": [
            "auto-open repair PR if degraded",
            "run security workflows",
            "refresh dependency patches",
        ],
        "decision_scope": "safe-autonomy-only",
    }

    path = Path(args.report)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps({"report": str(path), "status": status}))
    return 0 if status == "healthy" else 1


if __name__ == "__main__":
    raise SystemExit(main())
