#!/usr/bin/env python3
"""Publish verified product registrations and activate their public gallery symbols."""

import argparse
import base64
from datetime import date
import json
import os
from pathlib import Path
import re
import subprocess
import tempfile
from urllib.error import HTTPError
from urllib.request import urlopen


FOUNDRY = "sunstriker2009/sun-foundry"
AUTHORITY = Path("registry/products.json")
CATALOG = Path("registry/repositories.json")
REGISTRY_PAGE = Path("registry/PRODUCTS.md")
GALLERY = Path("registry/GALLERY.md")
PUBLICATION_PATHS = (AUTHORITY, CATALOG, REGISTRY_PAGE, GALLERY)
FAMILIES = {
    "productivity": ("productivitySeries", "SUN-P", "Productivity", "Productivity product by Sun"),
    "application_component": ("applicationComponentSeries", "SUN-C", "Application components", "Application component by Sun"),
}


def replace_line(pattern, value, text):
    text, count = re.subn(pattern, lambda _: value, text, flags=re.MULTILINE)
    if count != 1:
        raise ValueError("An Foundry document marker is missing or duplicated. Review its format before publishing.")
    return text


def update_registry_page(root, authority, product, label):
    ident, name, slug, description = (product[key] for key in ("id", "name", "repository", "purpose"))
    url = f"https://github.com/sunstriker2009/{slug}"
    counters = authority["idPolicy"]
    productivity = counters["productivitySeries"]["nextId"]
    component = counters["applicationComponentSeries"]["nextId"]
    registry = (root / REGISTRY_PAGE).read_text(encoding="utf-8")
    registry = replace_line(r"^\*\*Updated:\*\* [0-9-]+\.",
                            f"**Updated:** {authority['updated']}.", registry)
    registry = replace_line(r"\n\nThe next publication counters are \*\*SUN-P[0-9]{3}\*\* and \*\*SUN-C[0-9]{3}\*\*\.",
                            f"\n| {ident} | **{name}** | {label} | {description} | **CONFIRMED** | TBD |\n\n"
                            f"The next publication counters are **{productivity}** and **{component}**.", registry)
    registry = registry.rstrip() + (
        f"\n\n## {ident} — {name}\n"
        f"- **Public identity:** {product['publicName']}.\n"
        f"- **Repository:** [{slug}]({url}) (established).\n"
        "- **Commercial clearance:** PENDING.\n"
    )
    return registry


def project_registration(root, approved, confirmed_on):
    announced = date.fromisoformat(confirmed_on).isoformat()
    family = approved["family"]
    series, prefix, label, fallback = FAMILIES[family]
    ident, name, slug = (approved[key] for key in ("id", "name", "repository"))
    if not re.fullmatch(re.escape(prefix) + r"[0-9]{3}", ident) or not 1 <= int(ident[-3:]) < 999:
        raise ValueError("Invalid approved product ID.")
    if not re.fullmatch(r"sun-[a-z0-9]+(?:-[a-z0-9]+)*", slug):
        raise ValueError("Invalid approved repository slug.")
    description = approved["shortDescription"] or fallback
    if not isinstance(description, str) or len(description) > 180 or re.search(r"[<>|\[\]\r\n]", description):
        raise ValueError("The approved description is incompatible with the Foundry gallery.")
    visibility = approved.get("repositoryVisibility", "public")
    copy_approved = approved.get("publishPrivateSymbol", False)
    if visibility not in ("public", "private") or not isinstance(copy_approved, bool) or (copy_approved and visibility != "private"):
        raise ValueError("Invalid approved visibility or public symbol copy approval.")

    authority = json.loads((root / AUTHORITY).read_text(encoding="utf-8"))
    catalog = json.loads((root / CATALOG).read_text(encoding="utf-8"))
    operational = json.loads((root / "registry/product-catalog.json").read_text(encoding="utf-8"))
    if approved not in operational["products"]:
        raise ValueError("The approved registration is no longer active in Foundry.")
    if catalog.get("schemaVersion") != 1:
        raise ValueError("Unsupported Foundry repository catalog schema.")
    product = {
        "id": ident, "name": name, "status": "CONFIRMED", "purpose": description,
        "publicName": approved["publicName"], "repository": slug,
        "commercialClearance": "PENDING", "confirmedOn": announced, "family": family,
    }
    target = f"sunstriker2009/{slug}"
    listing = {"repository": target, "registryId": ident, "classification": "product",
               "name": name, "summary": description}
    identities = [
        row for row in authority["products"] + authority["infrastructure"]
        if ident in (row["id"], *row.get("previousIds", [])) or row["repository"] == slug
        or any(name.casefold() == alias.casefold() for alias in (row["name"], *row.get("previousNames", [])))
    ]
    listings = [
        row for row in catalog["repositories"]
        if row["repository"] == target or row["registryId"] == ident or row["name"].casefold() == name.casefold()
    ]
    if len(identities) == len(listings) == 1 and all(
        identities[0].get(key) == product[key]
        for key in ("id", "name", "family", "repository", "status", "publicName", "purpose")
    ) and all(listings[0].get(key) == listing[key] for key in listing):
        return False
    pending = (len(listings) == 1 and listings[0]["repository"] == target
               and listings[0]["classification"] == "pending" and listings[0]["registryId"] is None
               and listings[0].get("icon") is None and listings[0].get("iconSha256") is None)
    if identities or (listings and not pending):
        raise ValueError("The approved identity conflicts with an existing Foundry entry. Review before publishing.")

    counter = authority["idPolicy"][series]
    if not re.fullmatch(re.escape(prefix) + r"[0-9]{3}", counter["nextId"]):
        raise ValueError("Invalid Foundry family counter.")
    counter["nextId"] = max(counter["nextId"], f"{prefix}{int(ident[-3:]) + 1:03d}")
    authority["updated"] = max(authority["updated"], announced)
    authority["products"].append(product)
    row = {**listing, "symbolMode": "copy" if copy_approved else "text"}
    if visibility == "public":
        row["autoLiveSymbol"] = True
    if pending:
        catalog["repositories"][catalog["repositories"].index(listings[0])] = row
    else:
        catalog["repositories"].append(row)

    registry_page = update_registry_page(root, authority, product, label)
    for path, data in ((AUTHORITY, authority), (CATALOG, catalog)):
        (root / path).write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    (root / REGISTRY_PAGE).write_text(registry_page, encoding="utf-8")
    subprocess.run(["python3", "scripts/render-repository-gallery.py"], cwd=root, check=True)
    subprocess.run(["python3", "scripts/render-repository-gallery.py", "--check"], cwd=root, check=True)
    return True


def public_symbol_available(repository):
    if not re.fullmatch(r"sunstriker2009/[a-z0-9][a-z0-9._-]*", repository):
        raise ValueError(f"Invalid product repository: {repository}")
    response = subprocess.run(["gh", "api", f"repos/{repository}"], capture_output=True, text=True, timeout=30)
    if response.returncode:
        if "HTTP 404" in response.stderr:
            return False
        raise ValueError(f"Could not verify repository visibility for {repository}: {response.stderr.strip()}")
    metadata = json.loads(response.stdout)
    if metadata.get("full_name") != repository or metadata.get("visibility") != "public":
        return False
    url = f"https://raw.githubusercontent.com/{repository}/main/branding/assets/symbol.png"
    try:
        # The gallery will use this same URL without a repository credential.
        with urlopen(url, timeout=15) as image:
            return image.headers.get_content_type() == "image/png" and image.read(8) == b"\x89PNG\r\n\x1a\n"
    except HTTPError as error:
        if error.code != 404:
            raise
        return False


def project_public_symbols(root, repository=""):
    catalog = json.loads((root / CATALOG).read_text(encoding="utf-8"))
    if catalog.get("schemaVersion") != 1:
        raise ValueError("Unsupported Foundry repository catalog schema.")
    activated = []
    for row in catalog["repositories"]:
        if repository and row["repository"] != repository:
            continue
        if (row.get("classification") == "product" and row.get("symbolMode") == "text"
                and row.get("autoLiveSymbol") is True and public_symbol_available(row["repository"])):
            row["symbolMode"] = "live"
            del row["autoLiveSymbol"]
            activated.append(row["repository"])
    if not activated:
        return False
    (root / CATALOG).write_text(json.dumps(catalog, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    subprocess.run(["python3", "scripts/render-repository-gallery.py"], cwd=root, check=True)
    subprocess.run(["python3", "scripts/render-repository-gallery.py", "--check"], cwd=root, check=True)
    print("Ready for live gallery symbols: " + ", ".join(activated), flush=True)
    return True


def publish_changes(project, token, branch, paths, title, body):
    auth = base64.b64encode(f"x-access-token:{token}".encode()).decode()
    git_env = dict(os.environ, GIT_CONFIG_COUNT="1", GIT_CONFIG_KEY_0="http.https://github.com/.extraheader",
                   GIT_CONFIG_VALUE_0=f"AUTHORIZATION: basic {auth}")
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)

        def git(*args):
            return subprocess.check_output(["git", *args], cwd=root, env=git_env, text=True).strip()

        git("clone", "--quiet", "--depth=1", "--branch", "main", f"https://github.com/{FOUNDRY}.git", ".")
        if not project(root):
            return None
        ref = f"refs/heads/{branch}"
        base = git("rev-parse", "HEAD")
        git("diff", "--check")
        git("add", "--", *map(str, paths))
        git("-c", "user.name=sun-foundry[bot]", "-c", "user.email=41898282+github-actions[bot]@users.noreply.github.com",
            "commit", "-qm", title)
        if git("ls-remote", "--heads", "origin", ref):
            git("fetch", "--depth=2", "origin", ref)
            head = git("rev-parse", "FETCH_HEAD")
            if git("show", "-s", "--format=%P", head) != base or git("rev-parse", f"{head}^{{tree}}") != git("rev-parse", "HEAD^{tree}"):
                raise ValueError("The existing Foundry proposal differs from the current projection. Review it before retrying.")
        else:
            head = git("rev-parse", "HEAD")
            git("push", "--quiet", f"--force-with-lease={ref}:", "origin", f"{head}:{ref}")

        pr = subprocess.check_output(
            ["gh", "pr", "list", "--repo", FOUNDRY, "--head", branch, "--base", "main",
             "--state", "open", "--json", "url", "--jq", ".[0].url // empty"], text=True).strip()
        if not pr:
            pr = subprocess.check_output(
                ["gh", "pr", "create", "--repo", FOUNDRY, "--head", branch, "--base", "main",
                 "--title", title, "--body", body],
                text=True).strip()
        if not re.fullmatch(rf"https://github\.com/{re.escape(FOUNDRY)}/pull/[0-9]+", pr):
            raise ValueError("GitHub did not return an Foundry PR URL.")
        print(f"Foundry PR {pr}", flush=True)
        subprocess.run(["gh", "pr", "merge", pr, "--auto", "--squash", "--match-head-commit", head], check=True)
        return pr


def publish(approved, confirmed_on, token):
    return publish_changes(
        lambda root: project_registration(root, approved, confirmed_on), token,
        f"chore/publish-product-{approved['id']}-{approved['repository']}", PUBLICATION_PATHS,
        f"chore(registry): publish {approved['id']} {approved['name']}",
        f"Publish the Foundry-approved identity for {approved['repository']} after verification on the product repository's main.",
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--activate-public-symbols", action="store_true")
    parser.add_argument("--repository", default="", help="Limit public activation to an owner/repository")
    args = parser.parse_args()
    if args.repository and (not args.activate_public_symbols or not re.fullmatch(
        r"sunstriker2009/[a-z0-9][a-z0-9._-]*", args.repository
    )):
        parser.error("--repository requires public activation and a valid SUN owner/repository")
    token = os.environ["GH_TOKEN"]
    if not token:
        raise ValueError("A Foundry publication token is required.")
    if args.activate_public_symbols:
        branch = "chore/activate-public-gallery-symbols"
        if args.repository:
            branch += "-" + args.repository.split("/", 1)[1]
        pr = publish_changes(
            lambda root: project_public_symbols(root, args.repository), token, branch, (CATALOG, GALLERY),
            "chore(gallery): activate first public symbols",
            "Enable direct gallery links for registered public products with a canonical PNG available on main.",
        )
        no_changes = "No first-time public symbols were ready for the gallery."
    else:
        pr = publish(json.loads(os.environ["APPROVED_PRODUCT"]), os.environ["APPROVED_ON"], token)
        no_changes = "Foundry already lists the approved product identity."
    with Path(os.environ["GITHUB_STEP_SUMMARY"]).open("a", encoding="utf-8") as summary:
        summary.write(f"[Foundry publication PR]({pr}) has protected squash auto-merge requested.\n" if pr
                      else f"{no_changes}\n")


if __name__ == "__main__":
    try:
        main()
    except (KeyError, OSError, ValueError, subprocess.CalledProcessError) as error:
        raise SystemExit(str(error))
