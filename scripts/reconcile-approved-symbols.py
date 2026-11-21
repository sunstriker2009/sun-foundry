#!/usr/bin/env python3
"""Reconcile approved public symbol copies for private SUN members."""
import argparse
import json
import subprocess
from pathlib import Path


FOUNDRY = "sunstriker2009/sun-foundry"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repository', default='', help='Only reconcile this confirmed owner/repository')
    args = parser.parse_args()
    catalog = json.loads(subprocess.check_output([
        "gh", "api", f"repos/{FOUNDRY}/contents/registry/repositories.json",
        "-H", "Accept: application/vnd.github.raw+json",
    ], text=True))
    if catalog.get("schemaVersion") != 1:
        raise SystemExit("Unsupported registry schema")
    rows = catalog["repositories"]
    if args.repository:
        rows = [row for row in rows if row["repository"] == args.repository]
        if len(rows) != 1 or rows[0]["classification"] not in ("product", "infrastructure"):
            raise SystemExit("Target must be a confirmed Foundry repository")
    seen = set()
    failures = []
    for row in rows:
        repo = row["repository"]
        if repo in seen:
            raise SystemExit(f"Duplicate repository: {repo}")
        seen.add(repo)
        if row["classification"] not in ("product", "infrastructure") or row.get("symbolMode") != "copy":
            continue
        outcome = subprocess.run(
            ["python3", str(Path(__file__).with_name("sync-approved-symbol.py")),
             "--repository", repo, "--confirm", repo, "--mode", "apply"],
            check=False,
        )
        if outcome.returncode:
            failures.append(repo)
    if failures:
        raise SystemExit(f"Symbol reconciliation failed: {failures}")


if __name__ == "__main__":
    main()
