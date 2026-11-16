# Workflow cleanup — 2026-11-16

This is a retirement record for the paired FOUNDRY/Ecosystem cleanup PRs. Definitions leave the default branch only when those PRs merge. Existing Actions history and archived artwork are not deleted.

| Retired file | Replacement / reason |
| --- | --- |
| FOUNDRY `.github/workflows/propose-symbol-approval.yml` | Manual compatibility alias duplicated `sync-approved-sun-symbol.yml`; use that or `reconcile-approved-symbols.yml` |
| FOUNDRY `scripts/propose-symbol-approval.py` | Wrapper only; canonical sync script remains |
| FOUNDRY `.github/workflows/repository-rename-validation.yml` | Repository and product rename tests already run together in `product-rename-validation.yml`, now displayed as Rename pipeline validation; both workflow definitions are path triggers |
| Ecosystem `.github/workflows/symbol-approval-validation.yml` | Historical ledger is no longer an approval gate; validation against current catalog can make legitimate renames depend on historical membership |

`registry/symbol-approvals.json` remains unchanged as historical data. Canonical symbol safety/PNG checks and universal gallery validation remain active.

## Retained coverage and operations

Factory and maintenance, read-only fleet audit, controlled governance alignment, registration, manual ZIP installation/rollback, automatic product/repository rename, manual canonical symbol sync and daily reconciliation remain supported. Factory recovery, governance alignment/fleet/idempotency, asset, registration, installer, repository-input and symbol-sync validators retain distinct coverage. They are not obsolete because their matching operational workflow exists.

Universal required checks were read live before editing: FOUNDRY `build`; Ecosystem `gallery`. Their workflows and rulesets are unchanged. STRATA and product CI/deployment workflows are not removed: their product-specific coverage is outside this shared-workflow cleanup. The combined rename validator retains both test modules and responds to changes in either rename workflow. Manual installer remains necessary for preview and rollback.

No settings, schedules, secrets, workflow-run histories, branches from earlier work, numbered ZIPs or legacy archives are deleted. Auxiliary validation remains path-filtered to conserve quota; required universal checks remain universal.

See [the central handbook](https://github.com/sunstriker2009/sun-ecosystem/blob/main/docs/workflows/README.md), [issues](ISSUES-AND-GAPS.md) and [resumption handoff](GOVERNANCE-HANDOFF.md).

## Cleanup validation

The cleanup passed 29 rename tests, 17 repository-input tests, repository dropdown consistency, workflow YAML/embedded shell syntax checks, canonical symbol safety invariants and PNG behavior checks. The combined validator responds to both rename workflow paths. Required build/gallery run through the cleanup PRs; no live rename, rollback, settings change or new fleet audit was dispatched.
