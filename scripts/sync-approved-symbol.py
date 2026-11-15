#!/usr/bin/env python3
"""Propose a synchronized approved PNG symbol via an ecosystem pull request."""
import argparse
import base64
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import tempfile


def gh(*args):
    return subprocess.check_output(["gh", "api", *args], text=True).strip()


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
    p = argparse.ArgumentParser()
    p.add_argument("--repository", required=True)
    p.add_argument("--confirm", required=True)
    p.add_argument("--source", required=True)
    p.add_argument("--mode", choices=["preview", "apply"], default="preview")
    args = p.parse_args()
    target = args.repository
    if target != args.confirm or not re.fullmatch(r"sunstriker2009/[a-z0-9][a-z0-9._-]*", target):
        raise SystemExit("Invalid repository or confirmation mismatch")
    if not re.fullmatch(r"branding/assets/(?:symbol|symbol-canonical-v[0-9]+|icons/icon-(?:128|256|512))\.png", args.source):
        raise SystemExit("Source must be an explicitly approved canonical symbol or approved icon export")
    if not os.getenv("GH_TOKEN"):
        raise SystemExit("Missing GH_TOKEN")
    eco = "sunstriker2009/sun-ecosystem"
    slug = target.split("/")[1]
    catalog = json.loads(gh(f"repos/{eco}/contents/registry/repositories.json", "-H", "Accept: application/vnd.github.raw+json"))
    matching = [r for r in catalog["repositories"] if r["repository"] == target]
    if len(matching) != 1 or matching[0]["classification"] == "pending":
        raise SystemExit("Only confirmed, registered repositories may sync icons")
    # Require a canonical, reviewed source file from the default branch, not a caller-supplied SHA.
    meta = json.loads(gh(f"repos/{target}/contents/{args.source}?ref=main"))
    data = read_png_blob(target, args.source, meta)
    digest = hashlib.sha256(data).hexdigest()
    # A reviewed governance digest, not a filename or member-repo commit, grants approval.
    ledger = json.loads(gh(f"repos/{eco}/contents/registry/symbol-approvals.json", "-H", "Accept: application/vnd.github.raw+json"))
    if ledger.get("schemaVersion") != 1:
        raise SystemExit("Unsupported symbol approval ledger")
    approvals = [a for a in ledger.get("approvedSymbols", []) if a.get("repository") == target and a.get("source") == args.source]
    if len(approvals) != 1 or approvals[0].get("sha256") != digest:
        raise SystemExit("Source SHA-256 is not approved in ecosystem symbol-approvals.json")
    dest = f"branding/registry/{slug}.png"
    current = matching[0]
    if current.get("icon") == dest and current.get("iconSha256") == digest:
        print("Already synchronized; no PR required")
        return
    print(f"Sync candidate: {target} {args.source} sha256={digest} destination={dest}")
    if args.mode == "preview":
        print("Preview only; no repository changes")
        return
    # The ecosystem approval ledger is the explicit branding gate for apply.
    branch = f"chore/sync-symbol-{slug}"
    existing = subprocess.run(["gh", "api", f"repos/{eco}/branches/{branch}"], capture_output=True)
    if existing.returncode == 0:
        raise SystemExit("Existing symbol-sync branch; inspect its PR before retrying")
    with tempfile.TemporaryDirectory() as directory:
        repo_dir = Path(directory) / "ecosystem"
        token = os.environ["GH_TOKEN"]
        auth = base64.b64encode(f"x-access-token:{token}".encode()).decode()
        header = f"http.extraheader=AUTHORIZATION: basic {auth}"
        subprocess.run(["git", "-c", header, "clone", "--quiet", f"https://github.com/{eco}.git", str(repo_dir)], check=True)
        subprocess.run(["git", "checkout", "-q", "-b", branch], cwd=repo_dir, check=True)
        path = repo_dir / dest
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        live = json.loads((repo_dir / "registry/repositories.json").read_text())
        matches = [r for r in live["repositories"] if r["repository"] == target]
        if len(matches) != 1 or matches[0]["classification"] == "pending":
            raise SystemExit("Registry changed; retry after review")
        matches[0]["icon"] = dest
        matches[0]["iconSha256"] = digest
        (repo_dir / "registry/repositories.json").write_text(json.dumps(live, indent=2) + "\n")
        subprocess.run(["python3", "scripts/render-repository-gallery.py"], cwd=repo_dir, check=True)
        subprocess.run(["python3", "scripts/render-repository-gallery.py", "--check"], cwd=repo_dir, check=True)
        subprocess.run(["git", "add", dest, "registry/repositories.json", "README.md"], cwd=repo_dir, check=True)
        changed = subprocess.check_output(["git", "diff", "--cached", "--name-only"], cwd=repo_dir, text=True).splitlines()
        expected = {dest, "registry/repositories.json", "README.md"}
        if set(changed) != expected:
            raise SystemExit(f"Unexpected sync diff: {changed}; expected exactly {sorted(expected)}")
        subprocess.run(["git", "-c", "user.name=sun-foundry[bot]", "-c", "user.email=41898282+github-actions[bot]@users.noreply.github.com", "commit", "-qm", f"chore(registry): sync {slug} approved symbol"], cwd=repo_dir, check=True)
        subprocess.run(["git", "-c", header, "push", "--quiet", "-u", "origin", branch], cwd=repo_dir, check=True)
    body = f"Approved symbol synchronization from \`{target}/blob/main/{args.source}\`. SHA-256: \`{digest}\`. Only catalog, generated README and PNG are changed. Confirm source approval and review before merging."
    number = gh("-X", "POST", f"repos/{eco}/pulls", "-f", f"head={branch}", "-f", "base=main", "-f", f"title=chore(registry): sync {slug} approved symbol", "-f", f"body={body}", "--jq", ".number")
    print(f"PR: https://github.com/{eco}/pull/{number}")
    # Only the canonical, owner-selected source is eligible for automatic merge.
    # Native auto-merge continues to enforce GitHub's required checks and reviews.
    if args.source == "branding/assets/symbol.png":
        subprocess.run(["gh", "pr", "merge", number, "--repo", eco, "--auto", "--squash", "--delete-branch"], check=True)
        print("Protected squash auto-merge requested")
    else:
        print("Legacy source path: manual merge required")


if __name__ == "__main__":
    main()
