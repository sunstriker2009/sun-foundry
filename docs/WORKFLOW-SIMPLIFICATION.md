# Workflow simplification

Approved scope: reduce maintenance and low-value Actions executions while preserving product builds, functional tests and security checks.

## First phase

Completed in Foundry [#134](https://github.com/sunstriker2009/sun-foundry/pull/134), ecosystem policy [#64](https://github.com/sunstriker2009/sun-ecosystem/pull/64), and the six product cleanup PRs: Strata #25, Workbench #51, CodeFolio #80, Playground #5, TryPane #40, Foundry Pilot #10. All six targeted rulesets retain `repository-validation` and have retired `conventional-title`.

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

## Second phase: weekly symbol reconciliation

The scheduled full-catalog symbol reconciliation runs every Monday at 08:17 UTC (`17 8 * * 1`) instead of daily. Product merge-triggered targeted notifications and manual reconciliation remain available. Scheduled executions fall from seven to one per week (six fewer, approximately 86% fewer scheduled reconciliation runs). This is not a claim about total CI usage or billing.

The schedule is a recovery fallback. A missed relay or unavailable relay credentials can delay automatic symbol discovery/copy updates by up to a week. Dispatch reconciliation manually for an earlier update. Public products already using live symbol URLs continue to read the canonical product file independently of this schedule.

Validation: inspect the cron-only reconciliation workflow diff, retain dispatch inputs and the existing job unchanged, check the relay warning and current handbook/roadmap references, and run the existing required Foundry CI. A calendar-only change does not need a new test or a manual reconciliation run. To roll back, restore `17 8 * * *` and the corresponding documentation wording.

## Third phase: MarketPilot CI standardization

Consolidate the four MarketPilot CI definitions into one pipeline while preserving the existing `Build and unit tests`, `postgres-integration`, `web` and `docker-build` check identities. Scope backend/web jobs and container services to changed inputs; use full coverage for CI edits, unfamiliar paths, manual dispatch and unavailable diffs. Known documentation-only changes run the classifier's regression suite. Failed classification must fail the downstream checks rather than report success.

Retain solution/unit tests, PostgreSQL-backed API tests, production migration/idempotency validation, frontend lint/type checking/builds and actual container builds. Build API integration tests once and reuse the binaries for migrations and test execution. Keep PR and main verification; no repository settings change is included. The implementation and rollback guide belong in MarketPilot's `docs/CI.md`.

Acceptance: change-classifier regression tests, YAML/Bash validation and every retained check must pass on the consolidation PR before merge. Existing private-repository settings/check enforcement that cannot be inspected are not claimed as verified or changed. Savings depend on change scope; the small classification job adds overhead to full-coverage runs. No extra manual CI run is needed just to measure savings.

## Later candidates requiring separate changes

| Candidate | Recommendation / condition |
| --- | --- |
| Foundation file-existence checks | Move to provisioning and relevant path checks after confirming no product-specific validation is lost. |
| Asset-preparation stubs | Remove only after verifying no active operator or automation depends on them. |
| Outpost repeated service setup | Share setup where practical; preserve authentication, bootstrap, concurrency and reservation tests. |
| TryPane compiler prototypes | Establish which compiler paths are supported before retiring builds. |
| CodeFolio build and publishing | Reuse build outputs only where inputs and deployment requirements match. |
| Repeated PR/main builds | Keep deployment/release checks; remove duplicate validation only after confirming required-check and trust-boundary behavior. |

Keep security scans, meaningful unit/integration tests, deploy/release workflows and product builds. Avoid replacing several short jobs with a single larger job unless setup savings justify it. Do not consolidate unrelated privileged workflows.

## Validation and rollback

Run the existing Foundry Python suite, shell syntax checks and governance build; preserve inline workflow guard assertions as tests. The centralized asset E2E must cover configuration initialization, derivative generation, source integrity, overwrite rejection and tamper detection. Review YAML and workflow references after deletions.

If a product build regresses, revert that product cleanup PR. To restore title enforcement, restore `pr-title.yml` before re-adding its required check. Use the migration before snapshot to recover exact ruleset settings if needed; review current settings first to avoid overwriting later changes.
