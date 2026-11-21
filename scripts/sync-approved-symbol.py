#!/usr/bin/env python3
"""Propose a synchronized approved PNG symbol via a Foundry pull request."""
import argparse
import base64
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import tempfile


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


def approved_copy(catalog, target):
    matches = [row for row in catalog["repositories"] if row["repository"] == target]
    if len(matches) != 1 or matches[0]["classification"] not in ("product", "infrastructure"):
        raise SystemExit("Only confirmed, registered repositories may sync icons")
    return matches[0] if matches[0].get("symbolMode") == "copy" else None


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--repository", required=True)
    p.add_argument("--confirm", required=True)
    p.add_argument("--mode", choices=["preview", "apply"], default="preview")
    args = p.parse_args()
    target = args.repository
    if target != args.confirm or not re.fullmatch(r"sunstriker2009/[a-z0-9][a-z0-9._-]*", target):
        raise SystemExit("Invalid repository or confirmation mismatch")
    if not os.getenv("GH_TOKEN"):
        raise SystemExit("Missing GH_TOKEN")
    foundry = "sunstriker2009/sun-foundry"
    slug = target.split("/")[1]
    catalog = json.loads(gh(f"repos/{foundry}/contents/registry/repositories.json", "-H", "Accept: application/vnd.github.raw+json"))
    current = approved_copy(catalog, target)
    if current is None:
        print(f"SKIP {target}: no approval to publish a copy")
        return
    member = json.loads(gh(f"repos/{target}"))
    if member.get("full_name") != target or member.get("visibility") != "private":
        raise SystemExit(f"Copied symbols require a private registered repository: {target}")
    # Require a canonical, reviewed source file from the default branch, not a caller-supplied SHA.
    meta = json.loads(gh(f"repos/{target}/contents/{SOURCE}?ref=main"))
    data = read_png_blob(target, SOURCE, meta)
    digest = hashlib.sha256(data).hexdigest()
    # Merging the canonical branding asset to main is artwork approval.
    gallery = catalog.get("galleryDirectory")
    if gallery != "gallery":
        raise SystemExit("Unsupported gallery directory")
    dest = current.get("icon") or f"{gallery}/{slug}.png"
    if not re.fullmatch(r"gallery/[a-z0-9][a-z0-9._-]*\.png", dest):
        raise SystemExit("Invalid gallery icon path")
    if current.get("icon") == dest and current.get("iconSha256") == digest:
        print("Already synchronized; no PR required")
        return
    print(f"Sync candidate: {target} {SOURCE} sha256={digest} destination={dest}")
    if args.mode == "preview":
        print("Preview only; no repository changes")
        return
    # The merged canonical asset is the approval source.
    branch = f"chore/sync-symbol-{slug}"
    existing = subprocess.run(["gh", "api", f"repos/{foundry}/branches/{branch}"], capture_output=True)
    if existing.returncode == 0:
        raise SystemExit("Existing symbol-sync branch; inspect its PR before retrying")
    with tempfile.TemporaryDirectory() as directory:
        repo_dir = Path(directory) / "foundry"
        token = os.environ["GH_TOKEN"]
        auth = base64.b64encode(f"x-access-token:{token}".encode()).decode()
        header = f"http.extraheader=AUTHORIZATION: basic {auth}"
        subprocess.run(["git", "-c", header, "clone", "--quiet", f"https://github.com/{foundry}.git", str(repo_dir)], check=True)
        subprocess.run(["git", "checkout", "-q", "-b", branch], cwd=repo_dir, check=True)
        live = json.loads((repo_dir / "registry/repositories.json").read_text())
        if live.get("galleryDirectory") != gallery:
            raise SystemExit("Gallery directory changed; retry against the live catalog")
        approved = approved_copy(live, target)
        if approved is None or approved.get("icon") != current.get("icon"):
            raise SystemExit("Copy approval changed; retry after review")
        path = repo_dir / dest
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        approved["icon"] = dest
        approved["iconSha256"] = digest
        (repo_dir / "registry/repositories.json").write_text(json.dumps(live, indent=2) + "\n")
        subprocess.run(["python3", "scripts/render-repository-gallery.py"], cwd=repo_dir, check=True)
        subprocess.run(["python3", "scripts/render-repository-gallery.py", "--check"], cwd=repo_dir, check=True)
        subprocess.run(["git", "add", dest, "registry/repositories.json", "registry/GALLERY.md"], cwd=repo_dir, check=True)
        changed = subprocess.check_output(["git", "diff", "--cached", "--name-only"], cwd=repo_dir, text=True).splitlines()
        expected = {dest, "registry/repositories.json", "registry/GALLERY.md"}
        if not changed or not set(changed) <= expected or dest not in changed or "registry/repositories.json" not in changed:
            raise SystemExit(f"Unexpected sync diff: {changed}; expected exactly {sorted(expected)}")
        subprocess.run(["git", "-c", "user.name=sun-foundry[bot]", "-c", "user.email=41898282+github-actions[bot]@users.noreply.github.com", "commit", "-qm", f"chore(registry): sync {slug} approved symbol"], cwd=repo_dir, check=True)
        subprocess.run(["git", "-c", header, "push", "--quiet", f"--force-with-lease=refs/heads/{branch}:", "origin", f"HEAD:refs/heads/{branch}"], cwd=repo_dir, check=True)
    body = f"Approved public copy of the canonical symbol from `{target}` main. SHA-256: `{digest}`. Only catalog, generated gallery and PNG are changed."
    number = gh("-X", "POST", f"repos/{foundry}/pulls", "-f", f"head={branch}", "-f", "base=main", "-f", f"title=chore(registry): sync {slug} approved symbol", "-f", f"body={body}", "--jq", ".number")
    print(f"PR: https://github.com/{foundry}/pull/{number}")
    # Native auto-merge continues to enforce GitHub's required checks and reviews.
    subprocess.run(["gh", "pr", "merge", number, "--repo", foundry, "--auto", "--squash", "--delete-branch"], check=True)
    print("Protected squash auto-merge requested")


if __name__ == "__main__":
    main()
