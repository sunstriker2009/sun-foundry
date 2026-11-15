# Controlled governance alignment

**SUN Governance Alignment** is an owner-only, manual workflow on FOUNDRY's `main`. It uses the existing `repository-administration` environment and `SUN_REPO_ADMIN_TOKEN`, retaining its approval gates. There is no schedule, fleet-wide Apply or automatic remediation.

## Reviewed scope

| Repository | Existing ruleset ID | Expected previous name |
| --- | --- | --- |
| FOUNDRY | 27158357 | main |
| STRATA | 27252100 | protected main |
| ORYVA | 26219449 | Protected main |
| ASTELVO | 27170810 | SUN Main Protection |

IDs are explicit in `config/governance-alignment.json`; expected required checks come from `config/governance-fleet.json`. Renamed canonical rulesets remain eligible at the same ID. A missing, conflicting, replaced or unexpectedly renamed ruleset stops the operation. No rulesets are created or deleted. SUN Ecosystem is excluded until its universal check policy is established.

## Plan → Apply → Verify

1. Run **SUN Governance Alignment**, choose one repository, operation `plan`. Leave the Apply-only inputs empty. The environment may require approval.
2. Read the job summary's before/after diff and download `governance-alignment-plan` for `plan.json` and `result.json`. Record the successful Plan run ID from its Actions URL. A Plan reads GitHub only; it changes no repository settings.
3. Run the workflow again with the same repository, operation `apply`, that `plan_run_id`, and the short repository name (for example `sun-foundry`) repeated in `confirm_repository`.
4. Apply downloads the selected Plan artifact, checks that it was a successful Plan for that target, recomputes the plan from current policy/live state, and refuses any mismatch. It rechecks live governance immediately before writing.
5. Apply strengthens the existing ruleset first, patches only changed merge settings second, then reads back both and verifies every planned value. The independent `verify` operation is read-only and checks the current alignment policy. Rerun the fleet audit afterward for the consolidated baseline report.

Artifacts expire after seven days; make a new Plan after expiry or policy/state drift. Apply/Verify also publish their local plan and outcome, but only a successful **Plan** artifact is accepted as input to Apply. A previously applied Plan normally becomes stale; an already aligned no-op Plan can be applied without any write.

## What changes

- Rename the selected ruleset to `SUN Main Protection` and keep its ID.
- Normalize `~DEFAULT_BRANCH` to `refs/heads/main` only when the actual default branch is `main` and the existing scope is exactly that branch, with no exclusions.
- Keep protection active, ensure deletion and force-push protection, require PRs, stale-review dismissal and review-thread resolution, and allow only squash PR merges.
- Preserve stronger approval counts, CODEOWNERS/last-push requirements, extra rules, extra PR parameters and existing check app bindings. Unexpected existing check names are never removed; they require separate policy review.
- Add only configured check contexts after observing those names on `main` or the ten most recently updated PR heads; enforce strict/up-to-date checks including branch creation.
- Standardize squash-only repository settings, auto-merge, branch deletion, PR-title squash messages and PR-body squash descriptions.

Bypass actors, exclusions, broad branch scopes, duplicate rules and conflicting canonical rulesets are refused for separate review. Check observation establishes the context name exists, not that it is universal or sufficient; check policy remains a reviewed repository decision. The workflow never merges code, edits files in target repositories, or changes secrets or environments.

## Failure and recovery

The ruleset and repository settings APIs are not one atomic transaction. If settings fail after the ruleset update, the stronger ruleset remains in place. Do not automatically roll back protection. Inspect `result.json`, make a fresh Plan from the actual state, review it and retry. Concurrent administrative changes after the final pre-write read cannot be eliminated by GitHub's API; coordinate administrative changes and verify afterward. The workflow serializes its own runs, not unrelated administrative tools.

The existing fleet verifier still expects zero required approvals in its strict baseline; stronger preserved review counts may remain flagged there. Alignment never lowers those counts to make a report green. Additional governance profile support is separate work.

## Validation

```sh
python3 -m unittest discover -s tests -p 'test_governance_alignment.py' -v
```

Tests use a fake GitHub API and assert no writes during Plan/Verify, fixed ruleset identity, preservation of stronger protections and check app bindings, stale/tampered-plan rejection, no-op idempotency, failure recovery and expected write ordering. No live administrative settings have been changed by the implementation tests. Perform the first Plan/Apply/Verify on one selected repository after merge, then inspect the fleet audit before expanding usage.

Workflow dropdowns and implicit owner behavior: [Repository input guide](WORKFLOW-INPUTS.md). Backend plans retain fully qualified repository identities.
