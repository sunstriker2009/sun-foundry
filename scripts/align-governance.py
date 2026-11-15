#!/usr/bin/env python3
"""Plan, apply and verify explicit in-place SUN ruleset migrations."""
import argparse
import copy
import difflib
import json
import os
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
SETTINGS = dict(allow_squash_merge=True, allow_merge_commit=False, allow_rebase_merge=False,
                allow_auto_merge=True, delete_branch_on_merge=True,
                squash_merge_commit_title="PR_TITLE", squash_merge_commit_message="PR_BODY")
FIELDS = ("name", "target", "enforcement", "conditions", "bypass_actors", "rules")
NAME = "SUN Main Protection"


class GitHub:
    def request(self, method, path, payload=None):
        command = ["gh", "api", "--method", method, path]
        if payload is not None:
            command += ["--input", "-"]
        result = subprocess.run(command, input=json.dumps(payload) if payload is not None else None,
                                capture_output=True, text=True, timeout=45, check=False)
        if result.returncode:
            # API response bodies and credentials are not echoed into published reports.
            raise RuntimeError(f"GitHub {method} {path} failed; check access, capability and Actions logs")
        return json.loads(result.stdout) if result.stdout.strip() else None


def target_policy(repo):
    fleet = json.loads((ROOT / "config/governance-fleet.json").read_text())
    migrations = json.loads((ROOT / "config/governance-alignment.json").read_text())
    if fleet.get("schemaVersion") != 1 or migrations.get("schemaVersion") != 1:
        raise ValueError("Unsupported policy schema")
    rows = [r for r in migrations["repositories"] if r["repository"] == repo]
    checks = [r.get("requiredChecks") for r in fleet["repositories"] if r["repository"] == repo]
    if len(rows) != 1 or len(checks) != 1 or not checks[0]:
        raise ValueError("Repository needs explicit ruleset identity and exact required check policy")
    if not isinstance(rows[0]["rulesetId"], int) or rows[0]["rulesetId"] <= 0:
        raise ValueError("Invalid ruleset ID")
    if len(set(checks[0])) != len(checks[0]) or any(not isinstance(c, str) or not c.strip() for c in checks[0]):
        raise ValueError("Invalid required checks")
    return {**rows[0], "requiredChecks": checks[0]}


def snapshot(api, policy):
    repo = policy["repository"]
    info = api.request("GET", f"repos/{repo}")
    if info.get("full_name", "").lower() != repo.lower() or info.get("default_branch") != "main":
        raise ValueError("Repository identity or default branch differs from reviewed policy")
    rulesets = api.request("GET", f"repos/{repo}/rulesets?includes_parents=false&per_page=100")
    if len(rulesets) >= 100:
        raise ValueError("Ruleset listing may be incomplete; review manually")
    selected = [r for r in rulesets if r["id"] == policy["rulesetId"]]
    if len(selected) != 1 or any(r["name"] == NAME and r["id"] != policy["rulesetId"] for r in rulesets):
        raise ValueError("Selected ruleset missing or conflicting named ruleset exists")
    detail = api.request("GET", f'repos/{repo}/rulesets/{policy["rulesetId"]}')
    if detail.get("id") != policy["rulesetId"] or detail.get("name") not in (policy["legacyName"], NAME):
        raise ValueError("Ruleset identity changed; review before retrying")
    return {"settings": {k: info.get(k) for k in SETTINGS},
            "ruleset": {k: copy.deepcopy(detail.get(k)) for k in FIELDS}}


def desired_ruleset(current, checks):
    desired = copy.deepcopy(current)
    ref = current.get("conditions", {}).get("ref_name", {})
    if current.get("target") != "branch" or ref.get("include") not in (["refs/heads/main"], ["~DEFAULT_BRANCH"]):
        raise ValueError("Ruleset has broader or unknown scope; manual review required")
    if ref.get("exclude") != [] or current.get("bypass_actors") != []:
        raise ValueError("Exclusions or bypass actors require separate review")
    if set(current.get("conditions", {})) != {"ref_name"}:
        raise ValueError("Unknown ruleset conditions require manual review")
    desired.update(name=NAME, enforcement="active", conditions={
        "ref_name": {"include": ["refs/heads/main"], "exclude": []}})
    rules = desired.get("rules")
    if not isinstance(rules, list) or len({r["type"] for r in rules}) != len(rules):
        raise ValueError("Missing or duplicate rules require manual review")
    def rule(kind):
        existing = next((r for r in rules if r["type"] == kind), None)
        if existing is None:
            existing = {"type": kind}
            rules.append(existing)
        return existing
    rule("deletion")
    rule("non_fast_forward")
    pr = rule("pull_request").setdefault("parameters", {})
    pr.setdefault("required_approving_review_count", 0)
    pr.setdefault("require_code_owner_review", False)
    pr.setdefault("require_last_push_approval", False)
    pr.update(dismiss_stale_reviews_on_push=True, required_review_thread_resolution=True,
              allowed_merge_methods=["squash"])
    status = rule("required_status_checks").setdefault("parameters", {})
    existing = status.get("required_status_checks", [])
    contexts = [c["context"] for c in existing]
    if len(set(contexts)) != len(contexts) or set(contexts) - set(checks):
        raise ValueError("Unexpected existing required checks; refusing to remove protection")
    by_context = {c["context"]: c for c in existing}
    status.update(strict_required_status_checks_policy=True, do_not_enforce_on_create=False,
                  required_status_checks=[by_context.get(c, {"context": c}) for c in checks])
    return desired


def confirm_emitted_checks(api, policy):
    repo = policy["repository"]
    branch = api.request("GET", f"repos/{repo}/branches/main")
    heads = [branch["commit"]["sha"]]
    prs = api.request("GET", f"repos/{repo}/pulls?state=all&per_page=10&sort=updated&direction=desc")
    heads += [p["head"]["sha"] for p in prs]
    known = set()
    for sha in dict.fromkeys(heads):
        runs = api.request("GET", f"repos/{repo}/commits/{sha}/check-runs?per_page=100")
        known.update(r["name"] for r in runs.get("check_runs", []))
        if set(policy["requiredChecks"]) <= known:
            return
    raise ValueError("Required check names have not been observed on main/recent PRs; run CI before aligning")


def make_plan(api, policy):
    before = snapshot(api, policy)
    after = {"settings": SETTINGS.copy(), "ruleset": desired_ruleset(before["ruleset"], policy["requiredChecks"])}
    confirm_emitted_checks(api, policy)
    return {"schemaVersion": 1, "repository": policy["repository"], "rulesetId": policy["rulesetId"],
            "requiredChecks": policy["requiredChecks"], "before": before, "after": after}


def normalize(state):
    value = copy.deepcopy(state)
    rules = value["ruleset"]["rules"]
    rules.sort(key=lambda r: r["type"])
    for r in rules:
        if r["type"] == "required_status_checks":
            r["parameters"]["required_status_checks"].sort(key=lambda c: c["context"])
    return value


def contains(actual, expected):
    """Accept API-added default fields while verifying every planned value."""
    if isinstance(expected, dict):
        return isinstance(actual, dict) and all(k in actual and contains(actual[k], v) for k, v in expected.items())
    if isinstance(expected, list):
        return isinstance(actual, list) and len(actual) == len(expected) and all(
            contains(a, e) for a, e in zip(actual, expected))
    return type(actual) is type(expected) and actual == expected


def apply_plan(api, policy, reviewed, confirm):
    if confirm != policy["repository"]:
        raise ValueError("Apply requires exact repository confirmation")
    current = make_plan(api, policy)
    if current != reviewed:
        raise ValueError("Live state or policy differs from reviewed plan; run Plan again")
    repo, rid = policy["repository"], policy["rulesetId"]
    # Re-read immediately before writing. GitHub does not provide an atomic multi-endpoint transaction.
    if snapshot(api, policy) != current["before"]:
        raise ValueError("Concurrent governance change detected; run Plan again")
    after = current["after"]
    # Strengthen protection first. Never create, delete, disable or replace a different ruleset.
    if normalize(current["before"])["ruleset"] != normalize(after)["ruleset"]:
        api.request("PUT", f"repos/{repo}/rulesets/{rid}", after["ruleset"])
    delta = {k: v for k, v in after["settings"].items() if current["before"]["settings"].get(k) != v}
    if delta:
        api.request("PATCH", f"repos/{repo}", delta)
    actual = snapshot(api, policy)
    if not contains(normalize(actual), normalize(after)):
        raise ValueError("Post-apply verification differs; changes may be partially applied; inspect report and replan")
    return actual


def verify(api, policy):
    actual = snapshot(api, policy)
    desired = {"settings": SETTINGS.copy(), "ruleset": desired_ruleset(actual["ruleset"], policy["requiredChecks"])}
    if normalize(actual) != normalize(desired):
        raise ValueError("Governance drift remains; run Plan to inspect differences")
    return actual


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", required=True)
    parser.add_argument("--operation", choices=("plan", "apply", "verify"), default="plan")
    parser.add_argument("--reviewed-plan", type=Path)
    parser.add_argument("--confirm", default="")
    parser.add_argument("--output", type=Path, default=ROOT / "artifacts/governance-alignment")
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    report = {"repository": args.repository, "operation": args.operation, "status": "error"}
    try:
        if not os.getenv("GH_TOKEN"):
            raise ValueError("GH_TOKEN is required")
        policy, api = target_policy(args.repository), GitHub()
        plan = make_plan(api, policy)
        (args.output / "plan.json").write_text(json.dumps(plan, indent=2) + "\n")
        diff = "\n".join(difflib.unified_diff(json.dumps(plan["before"], indent=2).splitlines(),
                     json.dumps(plan["after"], indent=2).splitlines(), fromfile="before", tofile="after"))
        (args.output / "summary.md").write_text(f"# Governance alignment: {args.repository}\n\nOperation: {args.operation}\n\n```diff\n{diff}\n```\n")
        if args.operation == "apply":
            if args.reviewed_plan is None:
                raise ValueError("Apply requires a reviewed Plan artifact")
            reviewed = json.loads(args.reviewed_plan.read_text())
            apply_plan(api, policy, reviewed, args.confirm)
        elif args.operation == "verify":
            verify(api, policy)
        report["status"] = "planned" if args.operation == "plan" else "verified"
        return 0
    except (ValueError, RuntimeError, OSError, KeyError, subprocess.TimeoutExpired) as error:
        report["error"] = str(error)
        print(str(error))
        return 1
    finally:
        (args.output / "result.json").write_text(json.dumps(report, indent=2) + "\n")


if __name__ == "__main__":
    raise SystemExit(main())
