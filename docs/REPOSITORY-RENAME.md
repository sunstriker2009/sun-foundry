# Rename a SUN repository

Use **SUN Rename Repository** (`rename-repository.yml`) on FOUNDRY main. One owner dispatch defaults to **execute**: generate the plan, validate it and apply it automatically in the same job. There is no separate plan review, copied Plan run ID or second dispatch. Merging the implementation PR does not run a rename.

## Run once

1. Enter the current and new short repository names. The source must appear in `config/workflow-repositories.json`. Names are lowercase; owner transfers and FOUNDRY self-renames are outside scope.
2. Leave **operation = execute** for automatic Plan → Apply, or select **plan** for a read-only preview.
3. The existing `repository-administration` environment still controls access to `SUN_REPO_ADMIN_TOKEN`. If it requires an upfront approval, GitHub waits before starting the job. No additional approval occurs between Plan and Apply. This workflow change does not alter environment settings or credentials.
4. Execute generates `plan.json`, `references.diff` and `summary.md`, then automatically consumes that exact in-memory plan after validating identity, scope, commit and current repository heads.
5. Inspect the final `repository-rename-run` artifact and `result.json`. Apply renames the repository and opens reference-update PRs. It does not write protected default branches, merge PRs or request auto-merge. Required checks and existing merge policy continue to apply.
6. Squash-merge the reference PRs and verify the new URL/ID, CI, gallery, guards and workflow dropdowns. Rename and multiple PR merges are not atomic; avoid branding uploads or concurrent feature changes until references are updated. Product development stays paused.

A Plan-only run makes no external writes. Choosing Execute later generates a fresh plan from current state; it does not rely on a previously previewed plan.

## Reference scope

Tracked regular UTF-8 files on the target and deduplicated STRATA/FOUNDRY/Ecosystem default branches are scanned for exact owner/repository references, quoted short-name values/keys and whole YAML scalar/dropdown values. Generated Ecosystem gallery tiles are reordered as repository URLs change. FOUNDRY allowlists, ruleset mappings, workflow guards, registry mappings and documentation links are proposed together.

Product display names, SUN IDs, namespaces, asset names and binary artwork are not renamed by this repository workflow. A package identifier exactly equal to the repository short name is mechanically matched; inspect resulting PRs. Public-product renaming remains an explicitly authorized migration.

Archive/revision ZIPs, binary files, symlinks, submodules and files over 1 MB are preserved; skipped files and retained old-name matches are reported. The plan is limited to 12 MB. Independent repositories outside the configured SUN allowlist are not scanned.

## Access checks and partial failures

The existing token needs Administration write on the target and Contents/PR write on affected repositories, including permission for workflow-file updates. No token is created, copied or expanded by this workflow.

Before the name changes, Execute checks IDs, heads and proposal branch conflicts across the scope, then prepares the exact Git trees and commits in every affected repository. These unattached objects exercise actual content writes without creating/updating branch refs. A content-write 403 stops before renaming. Heads and identities are checked again after preparation.

This is not a guarantee that every later operation is permitted: branch creation, PR creation, rulesets, token expiry or concurrent changes can still fail after rename. `result.json` records rename status and created PR URLs. Unattached Git objects may remain if preparation fails; default branches and source repository names remain unchanged in that case.

## Recovery

Inspect live state and the result artifact before retrying. Re-running Execute with the original names can recognize an already-renamed target by numeric ID while the old URL still redirects to it. It plans from current heads and reuses matching proposal branches/open PRs. Unrelated or edited branches are refused; there is no force-push or automatic rename-back.

If previous PRs or default branches changed, review/merge or close/delete obsolete proposal branches through normal governance before retrying. Once the source is removed from the configured allowlist, finish remaining work through targeted PRs or an explicitly reviewed scope update. Do not reuse the old repository name.

The script retains direct CLI `plan` / `apply --reviewed-plan ... --confirm 'old -> new'` support for controlled recovery, but the dispatch form does not require those inputs.

## External follow-ups

Inspect Pages/custom domains, packages/container images, deployment/OIDC trust, secrets/variables containing URLs, webhooks, installations, local remotes, repositories outside scope and open feature branches. Old commits are not rewritten. GitHub does not redirect Action calls from a renamed Action-hosting repository; FOUNDRY self-renames remain blocked pending a separate coordinated consumer migration.

Reference: https://docs.github.com/en/repositories/creating-and-managing-repositories/renaming-a-repository

## Validation evidence

The live ASTELVO → WORKBENCH repository rename preserved repository ID 1456026269. Its Apply subsequently received a 403 preparing the FOUNDRY tree; reference PRs were recovered through the connected GitHub integration. The automatic path now prepares content writes before renaming and refreshes gallery ordering to cover the failures observed in that pilot.

Local mock/API and temporary-Git tests cover automatic execution, Plan-only immutability, failed content writes before rename, head drift, collisions, retries and gallery ordering. The automatic shared-engine path subsequently passed the combined OUTPOST pilot described below. The standalone workflow was not separately rerun during cleanup. No disposable repository or paused schedule is started by this change.


## Bounded product/governance scope

Reference scanning now uses the selected target plus `sun-strata`, `sun-foundry` and `sun-ecosystem`, deduplicating a governance target. It does not scan other product or owner repositories. The [product rename pipeline](PRODUCT-RENAME.md) uses this same scope and can reuse this engine for an optional repository rename, producing a single combined PR per affected repository.



## Combined automatic pilot checkpoint — 2026-11-16

The product pipeline reused this engine successfully for ORYVA → OUTPOST in [run 43934714433](https://github.com/sunstriker2009/sun-foundry/actions/runs/43934714433). OUTPOST #175, FOUNDRY #70 and Ecosystem #37 are merged; STRATA needed no change. This supersedes earlier automatic-execution-pending notes for the shared engine. See [issues and recovery limits](ISSUES-AND-GAPS.md) and the [handoff](GOVERNANCE-HANDOFF.md). The standalone workflow was not separately rerun during cleanup.
