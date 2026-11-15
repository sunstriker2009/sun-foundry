#!/usr/bin/env python3
"""Run strict, read-only governance verification for an explicit SUN allowlist."""
import argparse
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[1]
VERIFIER = ROOT / "src/Sun.RepoBootstrap/bin/Release/net10.0/Sun.RepoBootstrap.dll"


def load_targets(path):
    data = json.loads(path.read_text())
    if data.get("schemaVersion") != 1:
        raise ValueError("Unsupported allowlist schema")
    targets = data.get("repositories")
    if not isinstance(targets, list) or not 1 <= len(targets) <= 20:
        raise ValueError("Allowlist must contain 1..20 repositories")
    seen = set()
    for target in targets:
        repo = target.get("repository", "")
        if not re.fullmatch(r"sunstriker2009/[a-z0-9][a-z0-9._-]*", repo) or repo in seen:
            raise ValueError("Invalid or duplicate allowlist repository")
        seen.add(repo)
        checks = target.get("requiredChecks")
        if checks is not None and (not isinstance(checks, list) or not checks or
                any(not isinstance(c, str) or not c.strip() or c != c.strip() or
                    len(c) > 200 or any(ch in c for ch in ",\r\n") for c in checks) or
                len(set(checks)) != len(checks)):
            raise ValueError(f"Invalid exact required check names: {repo}")
    return targets


def verify(target):
    repo, checks = target["repository"], target.get("requiredChecks")
    result = {"repository": repo, "requiredChecks": checks}
    if not checks:
        return {**result, "status": "not_configured", "detail":
                "Exact required check policy must be reviewed before strict verification"}
    # Fixed executable and mode. No shell, Apply, confirmation, or arbitrary command input.
    command = ["dotnet", str(VERIFIER), "--repo", repo, "--mode", "verify",
               "--checks", ",".join(checks)]
    try:
        completed = subprocess.run(command, capture_output=True, text=True, timeout=120,
                                   cwd=ROOT, check=False)
        output = completed.stdout + completed.stderr
        token = os.getenv("GH_TOKEN")
        if token:
            output = output.replace(token, "[REDACTED]")
        if "GOVERNANCE CAPABILITY:" in output and "rulesets unavailable" in output:
            status = "unavailable"
        elif completed.returncode == 0 and "Verified: exact required checks" in output:
            status = "compliant"
        elif "Policy verification failed:" in output:
            status = "drift"
        else:
            status = "error"
        return {**result, "status": status, "exitCode": completed.returncode,
                "detail": output[-20000:]}
    except subprocess.TimeoutExpired:
        return {**result, "status": "error", "detail": "Verification timed out after 120 seconds"}
    except OSError:
        return {**result, "status": "error", "detail": "Unable to start the compiled verifier"}


def audit(targets, workers):
    with ThreadPoolExecutor(max_workers=workers) as pool:
        results = list(pool.map(verify, targets))
    return {"schemaVersion": 1, "policy": "SUN strict named-ruleset baseline",
            "generatedAt": datetime.now(timezone.utc).isoformat(),
            "readOnly": True, "results": results,
            "counts": {s: sum(r["status"] == s for r in results) for s in
                       ("compliant", "drift", "unavailable", "not_configured", "error")}}


def summary(report):
    lines = ["# SUN governance fleet audit", "", "Read-only strict baseline verification; no settings changed.",
             "", "| Repository | Result |", "| --- | --- |"]
    lines += [f'| {r["repository"]} | {r["status"]} |' for r in report["results"]]
    lines += ["", "See the JSON artifact for exact check policy and per-repository evidence.",
              "Compliance covers the existing verifier baseline, not every governance control or live merge behavior."]
    return "\n".join(lines) + "\n"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--allowlist", type=Path, default=ROOT / "config/governance-fleet.json")
    parser.add_argument("--output", type=Path, default=ROOT / "artifacts/governance-fleet")
    parser.add_argument("--workers", type=int, choices=range(1, 4), default=2)
    args = parser.parse_args()
    targets = load_targets(args.allowlist)
    if not os.getenv("GH_TOKEN"):
        raise SystemExit("GH_TOKEN is required; use a repository Administration-read credential")
    if not VERIFIER.is_file():
        raise SystemExit("Build src/Sun.RepoBootstrap in Release before running fleet audit")
    report = audit(targets, args.workers)
    args.output.mkdir(parents=True, exist_ok=True)
    (args.output / "report.json").write_text(json.dumps(report, indent=2) + "\n")
    rendered = summary(report)
    (args.output / "summary.md").write_text(rendered)
    print(rendered)
    return 0 if all(r["status"] == "compliant" for r in report["results"]) else 2


if __name__ == "__main__":
    raise SystemExit(main())
