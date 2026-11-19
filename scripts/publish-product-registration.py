#!/usr/bin/env python3
"""Publish the verified Foundry identity through an Ecosystem pull request."""

import base64
from datetime import date
import json
import os
from pathlib import Path
import re
import subprocess
import tempfile


ECOSYSTEM = "sunstriker2009/sun-ecosystem"
AUTHORITY = Path("registry/products.json")
CATALOG = Path("registry/repositories.json")
REGISTRY_PAGE = Path("registry/PRODUCTS.md")
README = Path("README.md")
PUBLICATION_PATHS = (AUTHORITY, CATALOG, REGISTRY_PAGE, README)
FAMILIES = {
    "productivity": ("productivitySeries", "SUN-P", "Productivity", "Productivity product by Sun"),
    "application_component": ("applicationComponentSeries", "SUN-C", "Application components", "Application component by Sun"),
}


def replace_line(pattern, value, text):
    text, count = re.subn(pattern, lambda _: value, text, flags=re.MULTILINE)
    if count != 1:
        raise ValueError("An Ecosystem document marker is missing or duplicated. Review its format before publishing.")
    return text


def update_pages(root, authority, product, label):
    ident, name, slug, description = (product[key] for key in ("id", "name", "repository", "purpose"))
    url = f"https://github.com/sunstriker2009/{slug}"
    counters = authority["idPolicy"]
    productivity = counters["productivitySeries"]["nextId"]
    component = counters["applicationComponentSeries"]["nextId"]
    registry = (root / REGISTRY_PAGE).read_text(encoding="utf-8")
    registry = replace_line(r"^\*\*Updated:\*\* [0-9-]+\.",
                            f"**Updated:** {authority['updated']}.", registry)
    registry = replace_line(r"\n\nThe next IDs are \*\*SUN-P[0-9]{3}\*\* and \*\*SUN-C[0-9]{3}\*\*\.",
                            f"\n| {ident} | **{name}** | {label} | {description} | **CONFIRMED** | TBD |\n\n"
                            f"The next IDs are **{productivity}** and **{component}**.", registry)
    registry = registry.rstrip() + (
        f"\n\n## {ident} — {name}\n"
        f"- **Public identity:** {product['publicName']}.\n"
        f"- **Repository:** [{slug}]({url}) (established).\n"
        "- **Commercial clearance:** PENDING.\n"
    )
    readme = (root / README).read_text(encoding="utf-8")
    products = ", ".join(f"{row['name']} ({row['id']})" for row in authority["products"] if row["status"] == "CONFIRMED")
    readme = replace_line(r"^\*\*Confirmed products:\*\* .*?(?=\. \*\*Governance & infrastructure:\*\*)",
                          f"**Confirmed products:** {products}", readme)
    readme = replace_line(r"The next IDs are \*\*SUN-P[0-9]{3}\*\* for productivity, \*\*SUN-C[0-9]{3}\*\* for application components",
                          f"The next IDs are **{productivity}** for productivity, **{component}** for application components", readme)
    anchor = "| Independent application |"
    if readme.count(anchor) != 1:
        raise ValueError("The Ecosystem at-a-glance table has changed. Review it before publishing.")
    readme = readme.replace(anchor, f"| Confirmed product | [{name}]({url}) | {description} — {ident} |\n{anchor}")
    return registry, readme


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
        raise ValueError("The approved description is incompatible with the Ecosystem gallery.")

    authority = json.loads((root / AUTHORITY).read_text(encoding="utf-8"))
    catalog = json.loads((root / CATALOG).read_text(encoding="utf-8"))
    if catalog.get("schemaVersion") != 1:
        raise ValueError("Unsupported Ecosystem repository catalog schema.")
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
        raise ValueError("The approved identity conflicts with an existing Ecosystem entry. Review before publishing.")

    counter = authority["idPolicy"][series]
    if not re.fullmatch(re.escape(prefix) + r"[0-9]{3}", counter["nextId"]):
        raise ValueError("Invalid Ecosystem family counter.")
    counter["nextId"] = max(counter["nextId"], f"{prefix}{int(ident[-3:]) + 1:03d}")
    authority["updated"] = max(authority["updated"], announced)
    authority["products"].append(product)
    row = {**listing, "icon": None, "iconSha256": None}
    if pending:
        catalog["repositories"][catalog["repositories"].index(listings[0])] = row
    else:
        catalog["repositories"].append(row)

    registry_page, readme = update_pages(root, authority, product, label)
    for path, data in ((AUTHORITY, authority), (CATALOG, catalog)):
        (root / path).write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    (root / REGISTRY_PAGE).write_text(registry_page, encoding="utf-8")
    (root / README).write_text(readme, encoding="utf-8")
    subprocess.run(["python3", "scripts/render-repository-gallery.py"], cwd=root, check=True)
    subprocess.run(["python3", "scripts/render-repository-gallery.py", "--check"], cwd=root, check=True)
    return True


def publish(approved, confirmed_on, token):
    auth = base64.b64encode(f"x-access-token:{token}".encode()).decode()
    git_env = dict(os.environ, GIT_CONFIG_COUNT="1", GIT_CONFIG_KEY_0="http.https://github.com/.extraheader",
                   GIT_CONFIG_VALUE_0=f"AUTHORIZATION: basic {auth}")
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)

        def git(*args):
            return subprocess.check_output(["git", *args], cwd=root, env=git_env, text=True).strip()

        git("clone", "--quiet", "--depth=1", "--branch", "main", f"https://github.com/{ECOSYSTEM}.git", ".")
        if not project_registration(root, approved, confirmed_on):
            return None
        branch = f"chore/publish-product-{approved['id']}-{approved['repository']}"
        ref = f"refs/heads/{branch}"
        base = git("rev-parse", "HEAD")
        git("diff", "--check")
        git("add", "--", *map(str, PUBLICATION_PATHS))
        title = f"chore(registry): publish {approved['id']} {approved['name']}"
        git("-c", "user.name=sun-foundry[bot]", "-c", "user.email=41898282+github-actions[bot]@users.noreply.github.com",
            "commit", "-qm", title)
        if git("ls-remote", "--heads", "origin", ref):
            git("fetch", "--depth=2", "origin", ref)
            head = git("rev-parse", "FETCH_HEAD")
            if git("show", "-s", "--format=%P", head) != base or git("rev-parse", f"{head}^{{tree}}") != git("rev-parse", "HEAD^{tree}"):
                raise ValueError("The existing Ecosystem proposal differs from the current projection. Review it before retrying.")
        else:
            head = git("rev-parse", "HEAD")
            git("push", "--quiet", f"--force-with-lease={ref}:", "origin", f"{head}:{ref}")

        pr = subprocess.check_output(
            ["gh", "pr", "list", "--repo", ECOSYSTEM, "--head", branch, "--base", "main",
             "--state", "open", "--json", "url", "--jq", ".[0].url // empty"], text=True).strip()
        if not pr:
            pr = subprocess.check_output(
                ["gh", "pr", "create", "--repo", ECOSYSTEM, "--head", branch, "--base", "main",
                 "--title", title, "--body",
                 f"Publish the Foundry-approved identity for {approved['repository']} after verification on the product repository's main."],
                text=True).strip()
        if not re.fullmatch(rf"https://github\.com/{re.escape(ECOSYSTEM)}/pull/[0-9]+", pr):
            raise ValueError("GitHub did not return an Ecosystem PR URL.")
        print(f"Ecosystem PR {pr}", flush=True)
        subprocess.run(["gh", "pr", "merge", pr, "--auto", "--squash", "--match-head-commit", head], check=True)
        return pr


if __name__ == "__main__":
    try:
        pr = publish(json.loads(os.environ["APPROVED_PRODUCT"]), os.environ["APPROVED_ON"], os.environ["GH_TOKEN"])
        with Path(os.environ["GITHUB_STEP_SUMMARY"]).open("a", encoding="utf-8") as summary:
            summary.write(f"[Ecosystem publication PR]({pr}) has protected squash auto-merge requested.\n" if pr
                          else "Ecosystem already lists the approved product identity.\n")
    except (KeyError, OSError, ValueError, subprocess.CalledProcessError) as error:
        raise SystemExit(str(error))
