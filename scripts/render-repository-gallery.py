#!/usr/bin/env python3
"""Validate the SUN repository catalog and render its gallery (stdlib only)."""
import argparse
import hashlib
import json
import re
from pathlib import Path

START = "<!-- SUN-REPOSITORY-GALLERY:START -->"
END = "<!-- SUN-REPOSITORY-GALLERY:END -->"
REPO_RE = re.compile(r"^sunstriker2009/[a-z0-9][a-z0-9._-]*$")
ID_RE = re.compile(r"SUN-([GPC])[0-9]{3}")
PRODUCT_FAMILIES = {"P": "productivity", "C": "application_component"}
SHA_RE = re.compile(r"^[0-9a-f]{64}$")


def render(root: Path, catalog=None, authority=None) -> str:
    if catalog is None:
        catalog = json.loads((root / "registry/repositories.json").read_text(encoding="utf-8"))
    if authority is None:
        authority = json.loads((root / "registry/products.json").read_text(encoding="utf-8"))
    if catalog.get("schemaVersion") != 1 or not isinstance(catalog.get("repositories"), list):
        raise ValueError("Unsupported repository catalog schema")
    if catalog.get("galleryDirectory") != "gallery":
        raise ValueError("Repository catalog must use the top-level gallery directory")
    identities = authority["products"] + authority["infrastructure"]
    known = {item["id"]: item for item in identities}
    if len(known) != len(identities):
        raise ValueError("Duplicate approved registry ID")
    rows = catalog["repositories"]
    if not rows:
        raise ValueError("Repository catalog must not be empty")
    seen_repos, seen_ids = set(), set()
    groups = {"product": [], "infrastructure": [], "pending": []}
    for item in rows:
        repo, ident, category = item["repository"], item.get("registryId"), item["classification"]
        if not REPO_RE.fullmatch(repo) or repo in seen_repos:
            raise ValueError(f"Invalid or duplicate repository: {repo}")
        seen_repos.add(repo)
        if category not in groups:
            raise ValueError(f"Invalid classification: {category}")
        if category == "pending":
            if ident is not None:
                raise ValueError("Pending repository cannot claim a confirmed ID")
        else:
            match = ID_RE.fullmatch(ident) if isinstance(ident, str) else None
            if match is None or ident in seen_ids:
                raise ValueError(f"Invalid or duplicate registry ID: {ident}")
            seen_ids.add(ident)
            expected = known.get(ident)
            if expected is None or f"sunstriker2009/{expected['repository']}" != repo:
                raise ValueError(f"Unapproved registry identity: {ident} / {repo}")
            status = "ESTABLISHED" if category == "infrastructure" else "CONFIRMED"
            if expected.get("status") != status:
                raise ValueError(f"Identity lacks required status for {ident}")
            series = match.group(1)
            if (series == "G") != (category == "infrastructure"):
                raise ValueError(f"Classification does not match registry ID: {ident}")
            if category == "product" and expected.get("family") != PRODUCT_FAMILIES[series]:
                raise ValueError(f"Product family does not match registry ID: {ident}")
            if item["name"] != expected["name"]:
                raise ValueError(f"Name mismatch for approved identity: {ident}")
        name, summary = item["name"], item["summary"]
        if not all(isinstance(v, str) and v.strip() and len(v) <= 180 for v in (name, summary)):
            raise ValueError(f"Missing or invalid display metadata for {repo}")
        if any(c in name + summary for c in "<>\n\r|[]"):
            raise ValueError(f"Unsafe Markdown metadata for {repo}")
        icon, digest = item.get("icon"), item.get("iconSha256")
        mode = item.get("symbolMode", "text")
        if mode not in ("text", "live", "copy") or (category == "pending" and mode != "text"):
            raise ValueError(f"Invalid gallery symbol mode for {repo}: {mode}")
        if mode != "copy" and (icon is not None or digest is not None):
            raise ValueError(f"Only copied symbols may have a local image or digest: {repo}")
        if mode == "live":
            source = f"https://raw.githubusercontent.com/{repo}/main/branding/assets/symbol.png"
            tile = f'<img src="{source}" alt="{name} icon" width="72" height="72">'
        elif icon is None:
            if digest is not None:
                raise ValueError(f"Icon digest without icon for {repo}")
            tile = f"<strong>{name}</strong>"
        else:
            if not isinstance(icon, str) or not re.fullmatch(r"gallery/[a-z0-9][a-z0-9._-]*\.png", icon):
                raise ValueError(f"Unsafe icon path for {repo}")
            path = root / icon
            if not path.is_file() or path.read_bytes()[:8] != b"\x89PNG\r\n\x1a\n":
                raise ValueError(f"Missing or invalid PNG for {repo}")
            if not isinstance(digest, str) or not SHA_RE.fullmatch(digest) or hashlib.sha256(path.read_bytes()).hexdigest() != digest:
                raise ValueError(f"Icon hash mismatch for {repo}")
            tile = f'<img src="../{icon}" alt="{name} icon" width="72" height="72">'
        url = f"https://github.com/{repo}"
        groups[category].append(f'<td align="center" width="180"><a href="{url}">{tile}</a><p><strong>{name}</strong></p><small>{ident or "Pending"} · {summary}</small></td>')
    out = ["# SUN Repository Gallery", "", "Generated from [the repository catalog](repositories.json). Approved identities remain governed by [products.json](products.json).", ""]
    for category, label in (("product", "Products"), ("infrastructure", "Infrastructure"), ("pending", "Pending registration")):
        if not groups[category]:
            continue
        out += [f"## {label}", "", "<table>", "<tr>"]
        for index, cell in enumerate(sorted(groups[category])):
            if index and index % 3 == 0:
                out += ["</tr>", "<tr>"]
            out.append(cell)
        out += ["</tr>", "</table>", ""]
    return "\n".join(out).rstrip() + "\n"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parent.parent)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    root = args.root.resolve()
    readme = root / "registry/GALLERY.md"
    source = readme.read_text(encoding="utf-8")
    if source.count(START) != 1 or source.count(END) != 1 or source.index(START) > source.index(END):
        raise ValueError("Gallery must have exactly one ordered gallery marker pair")
    rendered = render(root)
    expected = source[:source.index(START) + len(START)] + "\n" + rendered + source[source.index(END):]
    if args.check:
        if expected != source:
            raise SystemExit("Gallery is stale: run python scripts/render-repository-gallery.py")
        print("Registry and gallery validated")
    else:
        readme.write_text(expected, encoding="utf-8")


if __name__ == "__main__":
    main()
