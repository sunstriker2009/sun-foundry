#!/usr/bin/env python3
"""Owner-gated proposal of a SUN symbol approval ledger update; never auto-merge."""
import argparse
import base64
import hashlib
import json
import os
import re
import subprocess
import tempfile
from pathlib import Path

ECO = "sunstriker2009/sun-ecosystem"
SOURCE = "branding/assets/symbol.png"


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
    parser = argparse.ArgumentParser()
    parser.add_argument("--repository", required=True)
    parser.add_argument("--confirm", required=True)
    parser.add_argument("--mode", choices=("preview", "apply"), default="preview")
    args = parser.parse_args()
    repo = args.repository
    if repo != args.confirm or not re.fullmatch(r"sunstriker2009/sun-[a-z0-9-]+", repo):
        raise SystemExit("Repository confirmation mismatch or unsupported SUN repository")
    if not os.getenv("GH_TOKEN"):
        raise SystemExit("Missing GH_TOKEN")
    catalog = json.loads(gh(f"repos/{ECO}/contents/registry/repositories.json", "-H", "Accept: application/vnd.github.raw+json"))
    rows = [r for r in catalog["repositories"] if r["repository"] == repo and r["classification"] != "pending"]
    if len(rows) != 1:
        raise SystemExit("Repository must have one confirmed SUN registry identity")
    meta = json.loads(gh(f"repos/{repo}/contents/{SOURCE}?ref=main"))
    data = read_png_blob(repo, SOURCE, meta)
    digest = hashlib.sha256(data).hexdigest()
    ledger = json.loads(gh(f"repos/{ECO}/contents/registry/symbol-approvals.json", "-H", "Accept: application/vnd.github.raw+json"))
    if ledger.get("schemaVersion") != 1:
        raise SystemExit("Unsupported approval ledger schema")
    entries = [x for x in ledger["approvedSymbols"] if x["repository"] == repo]
    if len(entries) > 1:
        raise SystemExit("Duplicate approvals; resolve manually")
    if entries and entries[0]["sha256"] == digest and entries[0]["source"] == SOURCE:
        print("Already approved; no PR needed")
        return
    print(f"Candidate: {repo} source={SOURCE} sha256={digest}")
    if args.mode == "preview":
        print("Preview only. Inspect the canonical PNG visually before approving a PR.")
        return
    slug = repo.split("/")[1]
    branch = f"chore/propose-symbol-approval-{slug}"
    if subprocess.run(["gh", "api", f"repos/{ECO}/branches/{branch}"], capture_output=True).returncode == 0:
        raise SystemExit("Approval proposal branch already exists; review it first")
    with tempfile.TemporaryDirectory() as directory:
        folder = Path(directory) / "ecosystem"
        token = os.environ["GH_TOKEN"]
        auth = base64.b64encode(f"x-access-token:{token}".encode()).decode()
        header = f"http.extraheader=AUTHORIZATION: basic {auth}"
        subprocess.run(["git", "-c", header, "clone", "--quiet", f"https://github.com/{ECO}.git", str(folder)], check=True)
        subprocess.run(["git", "checkout", "-q", "-b", branch], cwd=folder, check=True)
        path = folder / "registry/symbol-approvals.json"
        live = json.loads(path.read_text())
        approved = live["approvedSymbols"]
        matches = [i for i, x in enumerate(approved) if x["repository"] == repo]
        if len(matches) > 1:
            raise SystemExit("Duplicate live approvals")
        entry = {
            "repository": repo,
            "source": SOURCE,
            "sha256": digest,
            "approval": f"Owner approval recorded by merging this manually reviewed proposal for {repo}"
        }
        if matches:
            approved[matches[0]] = entry
        else:
            approved.append(entry)
        path.write_text(json.dumps(live, indent=2) + "\n")
        subprocess.run(["git", "add", "registry/symbol-approvals.json"], cwd=folder, check=True)
        changed = subprocess.check_output(["git", "diff", "--cached", "--name-only"], cwd=folder, text=True).splitlines()
        if changed != ["registry/symbol-approvals.json"]:
            raise SystemExit(f"Unexpected files: {changed}")
        subprocess.run(["git", "-c", "user.name=sun-foundry[bot]", "-c", "user.email=41898282+github-actions[bot]@users.noreply.github.com", "commit", "-qm", f"chore(branding): propose {slug} symbol approval"], cwd=folder, check=True)
        subprocess.run(["git", "-c", header, "push", "--quiet", "-u", "origin", branch], cwd=folder, check=True)
    body = (
        f"**MANUAL ARTWORK APPROVAL REQUIRED — DO NOT AUTO-MERGE**\n\n"
        f"Review the canonical symbol visually: https://github.com/{repo}/blob/main/{SOURCE}\n\n"
        f"SHA-256: \`{digest}\`\n\n"
        f"This PR updates only the approval ledger. Confirm artwork approval and its source provenance before merging. "
        f"After merge, scheduled FOUNDRY reconciliation can synchronize it automatically."
    )
    number = gh("-X", "POST", f"repos/{ECO}/pulls", "-f", f"head={branch}", "-f", "base=main",
                "-f", f"title=chore(branding): propose {slug} symbol approval", "-f", f"body={body}", "--jq", ".number")
    print(f"Manual approval PR: https://github.com/{ECO}/pull/{number}")


if __name__ == "__main__":
    main()
