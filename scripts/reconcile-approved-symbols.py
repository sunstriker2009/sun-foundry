#!/usr/bin/env python3
"""Reconcile canonical SUN symbols merged to main; no separate approval ledger."""
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


def read_png_blob(repo, source, meta):
    """Read PNG bytes through Git blobs when Contents API omits >1 MB payloads."""
    if meta.get("type") != "file" or not 0 < meta.get("size", 0) <= 2_000_000:
        raise SystemExit(f"Canonical PNG missing or exceeds 2,000,000 bytes: {repo}/{source}")
    if meta.get("encoding") == "base64" and meta.get("content"):
        encoded = meta["content"]
    else:
        sha = meta.get("sha")
        if not sha:
            raise SystemExit("Canonical PNG response lacks blob SHA")
        blob = json.loads(subprocess.check_output(
            ["gh", "api", f"repos/{repo}/git/blobs/{sha}"], text=True))
        if blob.get("encoding") != "base64" or not blob.get("content"):
            raise SystemExit("Git blob API did not return base64 PNG content")
        encoded = blob["content"]
    data = base64.b64decode("".join(encoded.splitlines()), validate=True)
    if len(data) != meta["size"] or not data.startswith(bytes.fromhex("89504e470d0a1a0a")):
        raise SystemExit("Canonical PNG size or signature mismatch")
    return data


def main():
    catalog = json.loads(api(f"repos/{ECO}/contents/registry/repositories.json", True))
    if catalog.get("schemaVersion") != 1:
        raise SystemExit("Unsupported registry schema")
    gallery = catalog.get("galleryDirectory", "branding/registry")
    if gallery not in ("branding/registry", "gallery"):
        raise SystemExit("Unsupported gallery directory")
    seen = set()
    failures = []
    for row in catalog["repositories"]:
        repo = row["repository"]
        if repo in seen:
            raise SystemExit(f"Duplicate repository: {repo}")
        seen.add(repo)
        if row["classification"] == "pending":
            continue
        # Canonical assets on main have already passed the branding PR merge.
        result = subprocess.run(["gh", "api", f"repos/{repo}/contents/{SOURCE}?ref=main"],
                                capture_output=True, text=True)
        if result.returncode:
            if "HTTP 404" in result.stderr:
                print(f"SKIP {repo}: canonical symbol not adopted yet")
                continue
            failures.append(repo)
            print(f"ERROR {repo}: cannot read canonical symbol")
            continue
        meta = json.loads(result.stdout)
        content = read_png_blob(repo, SOURCE, meta)
        actual = hashlib.sha256(content).hexdigest()
        destination = f"{gallery}/{repo.split('/')[1]}.png"
        if row.get("icon") == destination and row.get("iconSha256") == actual:
            print(f"OK {repo}: already synchronized")
            continue
        print(f"SYNC {repo}: merged canonical symbol differs from gallery")
        outcome = subprocess.run(
            ["python3", str(Path(__file__).with_name("sync-approved-symbol.py")),
             "--repository", repo, "--confirm", repo, "--source", SOURCE, "--mode", "apply"],
            check=False,
        )
        if outcome.returncode:
            failures.append(repo)
    if failures:
        raise SystemExit(f"Symbol reconciliation failed: {failures}")


if __name__ == "__main__":
    main()
