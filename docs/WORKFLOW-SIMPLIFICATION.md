# Workflow simplification

Approved scope: reduce maintenance and low-value Actions executions while preserving product builds, functional tests and security checks.

## First phase

| Change | Repositories | Result |
| --- | --- | --- |
| Retire PR-title enforcement | Strata, Workbench, CodeFolio, Playground, TryPane, Foundry Pilot | Conventional Commit titles remain guidance; remove the dedicated workflow and its required check. |
| Centralize synthetic asset-adoption integration coverage | Foundry plus Strata, CodeFolio, Playground, TryPane, Foundry Pilot | Foundry tests the current shared implementation; products retain their builds and branding installers. |
| Consolidate lightweight validation | Foundry | Run existing Python and shell checks in the required `build` job; retain asset integration coverage in the asset workflow. |
| Update provisioning defaults | Foundry | New repositories require `repository-validation`, without recreating title enforcement. |

The audit found 78 workflow files across 10 accessible repositories, including 15 manual-only workflows and one scheduled workflow. Counts describe files, not billable executions. Manual workflows incur no runner execution until dispatched. Savings depend on event frequency and runner duration; no monetary estimate is implied.

## Rollout order

1. Merge the Foundry documentation and implementation PR.
2. Run the targeted title-check retirement migration in plan mode for each of the six repositories. Review the live ruleset and its digest.
3. Apply using that digest and exact repository confirmation. The migration removes only `conventional-title`; it preserves every other ruleset setting and verifies the result. Retain its before snapshot for rollback.
4. Merge the product workflow-removal PRs only after the migration succeeds. Keep `repository-validation` required. Update the ecosystem naming policy to describe titles as guidance.
5. Observe the next normal product PR and Foundry CI runs. Do not trigger paid workflows solely to measure savings.

The GitHub connection used for this change cannot write repository administration settings or dispatch Actions. Those migration runs require an owner with access to the existing `repository-administration` environment and `SUN_REPO_ADMIN_TOKEN`.

## Later candidates requiring separate changes

| Candidate | Recommendation / condition |
| --- | --- |
| Foundation file-existence checks | Move to provisioning and relevant path checks after confirming no product-specific validation is lost. |
| Daily approved-symbol reconciliation | Consider weekly; retain event-driven sync and manual repair. |
| Asset-preparation stubs | Remove only after verifying no active operator or automation depends on them. |
| MarketPilot overlapping CI | Design one build/test pipeline with shared outputs before removing existing jobs. |
| Outpost repeated service setup | Share setup where practical; preserve authentication, bootstrap, concurrency and reservation tests. |
| TryPane compiler prototypes | Establish which compiler paths are supported before retiring builds. |
| CodeFolio build and publishing | Reuse build outputs only where inputs and deployment requirements match. |
| Repeated PR/main builds | Keep deployment/release checks; remove duplicate validation only after confirming required-check and trust-boundary behavior. |

Keep security scans, meaningful unit/integration tests, deploy/release workflows and product builds. Avoid replacing several short jobs with a single larger job unless setup savings justify it. Do not consolidate unrelated privileged workflows.

## Validation and rollback

Run the existing Foundry Python suite, shell syntax checks and governance build; preserve inline workflow guard assertions as tests. The centralized asset E2E must cover configuration initialization, derivative generation, source integrity, overwrite rejection and tamper detection. Review YAML and workflow references after deletions.

If a product build regresses, revert that product cleanup PR. To restore title enforcement, restore `pr-title.yml` before re-adding its required check. Use the migration before snapshot to recover exact ruleset settings if needed; review current settings first to avoid overwriting later changes.
