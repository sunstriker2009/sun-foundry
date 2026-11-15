#!/usr/bin/env python3
"""Reconcile approved SUN symbol digests without trusting unreviewed asset changes."""
import base64
import hashlib
import json
import subprocess
from pathlib import Path


ECO = "sunstriker2009/sun-ecosystem"
SOURCE = "branding/assets/symbol.png"


def api(path, raw=False):
    args = ["gh", "api", path]
    if raw:
        args += ["-H", "Accept: application/vnd.github.raw+json"]
    return subprocess.check_output(args, text=True)


def main():
    approvals = json.loads(api(f"repos/{ECO}/contents/registry/symbol-approvals.json", True))
    catalog = json.loads(api(f"repos/{ECO}/contents/registry/repositories.json", True))
    if approvals.get("schemaVersion") != 1 or catalog.get("schemaVersion") != 1:
        raise SystemExit("Unsupported registry schema")
    rows = {r["repository"]: r for r in catalog["repositories"]}
    seen = set()
    for approval in approvals.get("approvedSymbols", []):
        repo = approval["repository"]
        if repo in seen:
            raise SystemExit(f"Duplicate approval: {repo}")
        seen.add(repo)
        if repo not in rows or rows[repo]["classification"] == "pending":
            raise SystemExit(f"Unregistered or pending repository in approvals: {repo}")
        if approval.get("source") != SOURCE:
            raise SystemExit(f"Noncanonical approved source: {repo}")
        expected = approval["sha256"]
        if len(expected) != 64 or any(ch not in "0123456789abcdef" for ch in expected):
            raise SystemExit(f"Invalid digest: {repo}")
        meta = json.loads(api(f"repos/{repo}/contents/{SOURCE}?ref=main"))
        if meta.get("type") != "file" or meta.get("size", 0) > 2_000_000:
            raise SystemExit(f"Invalid symbol: {repo}")
        content = base64.b64decode(meta["content"].replace("\n", ""), validate=True)
        actual = hashlib.sha256(content).hexdigest()
        if actual != expected:
            print(f"SKIP {repo}: changed symbol is not approved; update governance ledger through review")
            continue
        row = rows[repo]
        destination = f"branding/registry/{repo.split('/')[1]}.png"
        if row.get("icon") == destination and row.get("iconSha256") == actual:
            print(f"OK {repo}: already synchronized")
            continue
        print(f"SYNC {repo}: approved digest differs from gallery")
        subprocess.run(
            ["python3", str(Path(__file__).with_name("sync-approved-symbol.py")),
             "--repository", repo, "--confirm", repo, "--source", SOURCE, "--mode", "apply"],
            check=True,
        )


if __name__ == "__main__":
    main()
