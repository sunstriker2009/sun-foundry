# Workflow simplification

Approved scope: reduce maintenance and low-value Actions executions while preserving product builds, functional tests and security checks.

## Completed cleanup and closeout audit

Status: the higher-value cleanup is complete. Current `main` workflow directories were re-read across all ten repositories on November 28, 2026. There are **54 workflow files**, down from the original audit's **78** (24 fewer). File counts are an inventory measure, not runner executions, runner minutes or a billing estimate.

| Completed change | Implementation |
| --- | --- |
| Shared validation, title-check retirement and provisioning defaults | [Foundry #134](https://github.com/sunstriker2009/sun-foundry/pull/134), [Ecosystem #64](https://github.com/sunstriker2009/sun-ecosystem/pull/64), plus the six product cleanup PRs listed below |
| Weekly symbol recovery fallback | [Foundry #135](https://github.com/sunstriker2009/sun-foundry/pull/135) |
| MarketPilot component-scoped CI | [MarketPilot #39](https://github.com/sunstriker2009/sun-marketpilot-ai/pull/39) |
| Outpost shared Keycloak fixture | [Outpost #184](https://github.com/sunstriker2009/sun-outpost/pull/184) |
| TryPane shared local runner setup | [TryPane #41](https://github.com/sunstriker2009/sun-trypane/pull/41) |

Required and explicitly retained optional checks passed before those implementation PRs merged. The current post-merge MarketPilot CI, Outpost backend/frontend/reservation/full-stack E2E and TryPane CI also completed successfully. The weekly recovery schedule removes six scheduled reconciliation runs per week; event-driven and manual recovery remain available.

| Repository | Original workflow files | Current workflow files |
| --- | ---: | ---: |
| sun-ecosystem | 2 | 2 |
| sun-foundry | 24 | 16 |
| sun-strata | 6 | 4 |
| sun-outpost | 7 | 6 |
| sun-workbench | 5 | 4 |
| sun-codefolio | 8 | 6 |
| sun-playground | 7 | 5 |
| sun-trypane | 9 | 6 |
| sun-foundry-pilot | 6 | 4 |
| sun-marketpilot-ai | 4 | 1 |
| **Total** | **78** | **54** |

### CodeFolio audit: retain the existing stages

CodeFolio's PR preview and main publishing workflows already call the same `tools/regex-preview/build-preview.sh` entry point with matching Node 24, .NET 10 and the pinned Go SDK configuration. Their automatic events are complementary: preview validates a PR; publishing builds current main for Pages. Each uses one site-build invocation per execution. The fast required `repository-validation` check runs the repository's Node tests.

No CodeFolio workflow or runtime is retired in this audit. Reusing PR output for publication would require a separate design for provenance, exact merged inputs and trust boundaries; it is not justified as a routine maintenance cleanup. Keep the Chromium suites, current owner-controlled preview deferral, main build and deployment permissions unchanged.

### Stop condition and retained tools

The five optional asset-preparation workflows share the same manual-only definition and do not run on pushes, PRs or a schedule. Their ongoing operator usage has not been established; retaining them adds no recurring runner executions. The targeted title-check migration is also manual-only and remains a controlled repair/rollback aid. Do not remove optional operator tools solely to reduce the sidebar/file count.

Foundation existence checks are inexpensive steps within the existing required baseline, rather than separate heavyweight pipelines. Preserve them until provisioning/template validation offers an equivalent agreed contract. Preserve PR/main validation when it checks different trusted revisions or supports publishing. The remaining decisions below are deferred unless measured duration/usage identifies a material maintenance or cost problem. Avoid more refactoring solely to reduce the number of YAML files.

## First phase

Completed in Foundry [#134](https://github.com/sunstriker2009/sun-foundry/pull/134), ecosystem policy [#64](https://github.com/sunstriker2009/sun-ecosystem/pull/64), and the six product cleanup PRs: Strata #25, Workbench #51, CodeFolio #80, Playground #5, TryPane #40, Foundry Pilot #10. All six targeted rulesets retain `repository-validation` and have retired `conventional-title`.

| Change | Repositories | Result |
| --- | --- | --- |
| Retire PR-title enforcement | Strata, Workbench, CodeFolio, Playground, TryPane, Foundry Pilot | Conventional Commit titles remain guidance; remove the dedicated workflow and its required check. |
| Centralize synthetic asset-adoption integration coverage | Foundry plus Strata, CodeFolio, Playground, TryPane, Foundry Pilot | Foundry tests the current shared implementation; products retain their builds and branding installers. |
| Consolidate lightweight validation | Foundry | Run existing Python and shell checks in the required `build` job; retain asset integration coverage in the asset workflow. |
| Update provisioning defaults | Foundry | New repositories require `repository-validation`, without recreating title enforcement. |

The audit found 78 workflow files across 10 accessible repositories, including 15 manual-only workflows and one scheduled workflow. Counts describe files, not billable executions. Manual workflows incur no runner execution until dispatched. Savings depend on event frequency and runner duration; no monetary estimate is implied.

## First-phase rollout order (completed)

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

## Fourth phase: Outpost shared Keycloak fixture

Run the existing role-mapping integration exercise immediately after the full-stack suite's fresh Keycloak instance becomes ready, before any profile/bootstrap setup. Retire only the independent `keycloak-integration.yml` workflow. Both workflows used the same image and realm; this removes one duplicate Keycloak startup and hosted runner per PR/main event.

Preserve every original role-mapping assertion. Add explicit empty-fixture preconditions and finally-based cleanup of the two exact test identities, verifying their absence and empty master membership before subsequent tests. Unexpected pre-existing fixture identities or master membership must fail without deleting them; cleanup failure must fail the test. Other identities are preserved. Keep separate PostgreSQL fixtures, backend/frontend/reservation checks and all original full-stack security tests unchanged. No required-check or repository-setting migration is needed.

Acceptance: fixture-lifecycle regression tests, workflow syntax/ordering checks, all existing required checks and the full `master-bootstrap-e2e` must pass before merge. Do not rely on auto-merge while that longer E2E is optional in the live ruleset. Outpost `docs/CI.md` records the retained scenarios, manual recovery entry point, cost limits and revert path.

## Fifth phase: TryPane local runner CI

The public browser compiler, fixed execution probe, editable hosting candidate, browser Go tools and local Docker runners are distinct supported use cases. Keep their functional builds and test coverage. The duplicate setup is in the two local C#/Go container workflows: combine those into `local-runners.yml` so shared-source PRs use one runner, npm installation, TypeScript build and Chromium setup.

Keep each language's original image, CLI smoke suite and browser smoke script. Language-only paths select only that runner; shared/unknown inputs, unavailable diffs and cross-language renames receive both suites. Manual dispatch offers both or either language, while automatic checks remain PR-only. The existing browser compiler, required `repository-validation` and Pages workflow remain unchanged. The two optional standalone `smoke` checks need no required-check migration.

Acceptance: selection regression tests, existing npm tests, preserved-command/setup checks, required repository validation and both local-language CLI/browser suites must pass on the consolidation PR before merge. One sequential job can take longer in wall time than two parallel jobs; savings come from removing duplicate setup on shared changes, not from retiring supported runtimes. TryPane `docs/CI.md` records scope, tradeoffs and rollback.

## Later candidates requiring separate changes

| Candidate | Recommendation / condition |
| --- | --- |
| Foundation file-existence checks | Retain the inexpensive current baseline. Move only after agreeing equivalent provisioning/template coverage. |
| Asset-preparation stubs | Retain pending operator-usage evidence; they are manual-only and create no recurring runner executions. |
| CodeFolio build and publishing | Audited: already share the build entry point and matching toolchains. Retain PR verification and trusted-main publication. |
| Repeated PR/main builds | Retain where revisions, publishing or trust boundaries differ; investigate only with measured duration/usage evidence. |

Keep security scans, meaningful unit/integration tests, deploy/release workflows and product builds. Avoid replacing several short jobs with a single larger job unless setup savings justify it. Do not consolidate unrelated privileged workflows.

## Validation and rollback

Run the existing Foundry Python suite, shell syntax checks and governance build; preserve inline workflow guard assertions as tests. The centralized asset E2E must cover configuration initialization, derivative generation, source integrity, overwrite rejection and tamper detection. Review YAML and workflow references after deletions.

If a product build regresses, revert that product cleanup PR. To restore title enforcement, restore `pr-title.yml` before re-adding its required check. Use the migration before snapshot to recover exact ruleset settings if needed; review current settings first to avoid overwriting later changes.
