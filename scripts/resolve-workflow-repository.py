#!/usr/bin/env python3
"""Normalize short SUN repository inputs before invoking existing guarded tools."""
import argparse
import json
import os
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
OWNER = "sunstriker2009"
OTHER = "other-repository"
WORKFLOWS = {
    "repository-factory-v1.yml": "factory",
    "repository-factory-resume.yml": "maintenance",
    "register-sun-repository.yml": "registration",
    "sync-approved-sun-symbol.yml": "symbol",
    "propose-symbol-approval.yml": "symbol",
    "governance-alignment.yml": "alignment",
    "branding-zip-install.yml": "branding",
}
OPERATIONS = {
    "factory": ("create", "resume"), "maintenance": ("diagnose", "plan", "apply", "verify"),
    "registration": ("preview", "apply"), "symbol": ("preview", "apply"),
    "alignment": ("plan", "apply", "verify"), "branding": ("preview", "apply"),
}


def choices(profile):
    config = json.loads((ROOT / "config/workflow-repositories.json").read_text())
    if config.get("schemaVersion") != 1:
        raise ValueError("Unsupported repository input schema")
    if profile == "alignment":
        return [r["repository"].split("/")[1] for r in json.loads(
            (ROOT / "config/governance-alignment.json").read_text())["repositories"]]
    names = config["symbolRepositories" if profile == "symbol" else "repositories"]
    if len(set(names)) != len(names):
        raise ValueError("Duplicate repository choices")
    return names if profile == "branding" else [*names, OTHER]


def short_name(value):
    if value.startswith(OWNER + "/"):
        value = value[len(OWNER) + 1:]
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,99}", value) or value in (".", ".."):
        raise ValueError("Use a repository name without an owner, slash or whitespace")
    return value


def resolve(selection, other, confirmation, profile, operation):
    # Copy/pasted form values may carry surrounding spaces or line breaks.
    selection, other, confirmation = (value.strip() for value in (selection, other, confirmation))
    if profile not in WORKFLOWS.values():
        raise ValueError("Unknown workflow profile")
    if operation not in OPERATIONS[profile]:
        raise ValueError("Unknown workflow operation")
    if selection == OTHER:
        if profile in ("alignment", "branding") or not other:
            raise ValueError("Select an allowed repository or supply its short name")
        name = short_name(other)
    else:
        if other:
            raise ValueError("Clear the other-repository field when selecting a listed repository")
        name = short_name(selection)
        if name not in choices(profile):
            raise ValueError("Select Other repository for names outside the dropdown")
    if profile == "factory" and operation == "create" and selection != OTHER:
        raise ValueError("To create a repository select other-repository and enter its new short name")
    required = profile in ("factory", "registration", "symbol") or operation == "apply"
    confirm = short_name(confirmation) if confirmation else ""
    if required and confirm != name:
        raise ValueError("Confirmation must match the short repository name")
    if confirm and confirm != name:
        raise ValueError("Repository confirmation mismatch")
    repository = f"{OWNER}/{name}"
    return {"name": name, "repository": repository,
            "confirmation": f"{OWNER}/{confirm}" if confirm else "",
            "factory_target": name if operation == "create" else repository,
            "factory_confirmation": confirm if operation == "create" else (f"{OWNER}/{confirm}" if confirm else "")}


def check_workflows():
    for filename, profile in WORKFLOWS.items():
        text = (ROOT / ".github/workflows" / filename).read_text()
        block = re.search(r"^      repository:\n(.*?)(?=^      \w+:|^permissions:)", text, re.M | re.S)
        if block is None or "type: choice" not in block.group(1):
            raise ValueError(f"Missing repository dropdown: {filename}")
        actual = re.findall(r"^          - (\S+)$", block.group(1), re.M)
        if actual != choices(profile):
            raise ValueError(f"Repository dropdown differs from policy: {filename}")
        if "scripts/resolve-workflow-repository.py" not in text:
            raise ValueError(f"Missing repository normalizer: {filename}")
    print("All repository dropdowns match their configured scope")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--profile", choices=set(WORKFLOWS.values()))
    parser.add_argument("--check-workflows", action="store_true")
    args = parser.parse_args()
    if args.check_workflows:
        check_workflows()
        return
    result = resolve(os.getenv("SELECTION", ""), os.getenv("OTHER_REPOSITORY", ""),
                     os.getenv("CONFIRM_SHORT", ""), args.profile, os.getenv("OPERATION", ""))
    output = os.environ["GITHUB_OUTPUT"]
    with open(output, "a") as stream:
        for key, value in result.items():
            stream.write(f"{key}={value}\n")
    print(f'Repository: {result["repository"]}')


if __name__ == "__main__":
    main()
