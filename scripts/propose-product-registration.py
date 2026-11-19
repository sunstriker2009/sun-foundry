#!/usr/bin/env python3
"""Validate a Foundry product proposal and prepare the catalog change."""

import argparse
from contextlib import closing
from copy import deepcopy
from http.client import HTTPSConnection, HTTPException
import json
import os
from pathlib import Path
import re


CATALOG = Path("registry/product-catalog.json")
OWNER = "sunstriker2009"
PROPOSAL_PREFIX = "chore/propose-product-"


def registration(catalog, name, family, description):
    name = name.strip(" ")
    if not re.fullmatch(r"[A-Za-z0-9](?:[A-Za-z0-9 -]*[A-Za-z0-9])?", name) or not re.search(r"[A-Za-z]", name):
        raise ValueError("Use ASCII letters, digits, spaces, and hyphens. Include a letter and start and end with a letter or digit.")
    if name.lower().startswith("sun-") or re.search(r" +by +sun$", name, re.IGNORECASE):
        raise ValueError("Enter the base product name without the sun- prefix or by Sun endorsement.")
    slug = "sun-" + re.sub(r"[ -]+", "-", name.lower())
    if len(slug) > 100:
        raise ValueError("The derived repository name exceeds 100 characters.")

    description = description.strip() or None
    if description and (len(description) > 180 or re.search(r"[<>|\[\]\r\n]", description) or len(description.splitlines()) != 1):
        raise ValueError("Use a single-line description of up to 180 characters without <, >, |, [ or ].")
    if catalog.get("schemaVersion") != 1:
        raise ValueError("Unsupported Foundry catalog schema.")

    families = catalog["families"]
    family_policy = families.get(family, {})
    if family_policy.get("repositoryClassification") != "product":
        raise ValueError("Select a product family.")
    series = family_policy["format"]
    candidate = family_policy["nextId"]
    if not re.fullmatch(r"SUN-[A-Z]NNN", series) or not re.fullmatch(re.escape(series[:-3]) + r"[0-9]{3}", candidate):
        raise ValueError("The catalog has an invalid next ID for this family.")
    number = int(candidate[-3:])
    if not 1 <= number < 999:
        raise ValueError("The catalog cannot allocate and advance this family ID.")

    records = catalog["products"] + catalog["infrastructure"]
    for record in records:
        names = [record["name"], *record.get("previousNames", [])]
        if any(name.casefold() == previous.casefold() for previous in names):
            raise ValueError("The product name is already recorded in the Foundry catalog.")
        if slug == record["repository"].lower():
            raise ValueError(f"The repository name {slug} is already recorded in the Foundry catalog.")
        if candidate in [record["id"], *record.get("previousIds", [])]:
            raise ValueError("The proposed family ID is already assigned or retired.")

    product = {
        "id": candidate,
        "name": name,
        "family": family,
        "repository": slug,
        "shortDescription": description,
        "publicName": f"{name} by Sun",
    }
    return product, f"{series[:-3]}{number + 1:03d}"


def check_repository_available(slug, token):
    target = f"{OWNER}/{slug}"
    try:
        with closing(HTTPSConnection("api.github.com", timeout=15)) as connection:
            connection.request("GET", f"/repos/{target}", headers={
                "Accept": "application/vnd.github+json",
                "Authorization": f"Bearer {token}",
                "User-Agent": "sun-foundry",
            })
            status = connection.getresponse().status
    except (HTTPException, OSError) as error:
        raise ValueError("GitHub repository lookup could not be completed.") from error
    if status == 404:
        return
    if status == 200 or 300 <= status < 400:
        raise ValueError(f"GitHub already has or redirects repository name {target}.")
    raise ValueError(f"GitHub repository lookup failed (HTTP {status}).")


def add_registration(catalog, product, next_id):
    catalog["products"].append(product)
    catalog["families"][product["family"]]["nextId"] = next_id


def validate_pull_request(base, proposed, head_ref):
    if not head_ref.startswith(PROPOSAL_PREFIX):
        base_ids = {record["id"] for record in base["products"]}
        proposed_ids = [record["id"] for record in proposed["products"]]
        if set(proposed_ids) - base_ids or len(proposed_ids) != len(set(proposed_ids)):
            raise ValueError("Use the Foundry proposal workflow to register a product.")
        return

    match = re.fullmatch(r"(SUN-[A-Z][0-9]{3})-(sun-[a-z0-9]+(?:-[a-z0-9]+)*)", head_ref[len(PROPOSAL_PREFIX):])
    if match is None:
        raise ValueError("Run the Foundry proposal workflow again to open an ID-bound proposal.")
    branch_id, slug = match.groups()
    records = [record for record in proposed["products"] if record["repository"] == slug]
    if len(records) != 1:
        raise ValueError("The proposal must contain exactly one product for its repository.")
    record = records[0]
    product, next_id = registration(base, record["name"], record["family"], record["shortDescription"] or "")
    if branch_id != product["id"]:
        raise ValueError(
            f"Proposed ID {branch_id} is stale. Current main proposes {product['id']}. "
            "Run the proposal workflow again and review the new PR."
        )
    expected = deepcopy(base)
    add_registration(expected, product, next_id)
    if proposed != expected:
        raise ValueError("The catalog must match the generated proposal and advance only its family's counter.")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--validate-pr", type=Path, metavar="BASE_CATALOG")
    args = parser.parse_args()
    catalog = json.loads(CATALOG.read_text(encoding="utf-8"))
    if args.validate_pr:
        base = json.loads(args.validate_pr.read_text(encoding="utf-8"))
        validate_pull_request(base, catalog, os.environ["GITHUB_HEAD_REF"])
        return
    product, next_id = registration(
        catalog, os.environ["PRODUCT_NAME"], os.environ["PRODUCT_FAMILY"], os.environ["SHORT_DESCRIPTION"]
    )
    token = os.environ.get("GH_TOKEN")
    if not token:
        raise ValueError("A GitHub credential is required to check repository availability.")
    check_repository_available(product["repository"], token)

    add_registration(catalog, product, next_id)
    CATALOG.write_text(json.dumps(catalog, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    with Path(os.environ["GITHUB_OUTPUT"]).open("a", encoding="utf-8") as output:
        output.write(f"repository={product['repository']}\nfamily_id={product['id']}\n")


if __name__ == "__main__":
    try:
        main()
    except (KeyError, OSError, ValueError) as error:
        raise SystemExit(str(error))
