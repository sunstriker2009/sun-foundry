# Repository automation

Use two supported workflows:

- **Repository Factory** (`.github/workflows/repository-factory-v1.yml`): create a repository or resume interrupted provisioning. Initializes a seed PR, waits for CI, applies and strictly verifies governance.
- **Repository Maintenance** (`.github/workflows/repository-factory-resume.yml`): diagnose, plan, apply, or verify governance on an existing repository without creating or seeding it.

Both require owner-initiated manual dispatch on `main` and the `repository-administration` environment credential. Choose a short repository name from the dropdown; the owner is implicit. Where required, confirmation repeats only the short name. See [repository input guide](WORKFLOW-INPUTS.md) for new or unlisted repositories.

Retired workflows: original Repository Factory (create + plan only), standalone Seed CI, and legacy Provisioning. Git history retains their definitions if recovery is needed. The supported workflows above replace their functions.

For normal setup, prefer **Repository Factory**. For troubleshooting and targeted reconfiguration, use **Repository Maintenance**.

After Factory succeeds, squash merge its disposable seed PR manually to test the merge and branch-cleanup policy.

## STRATA branding isolation during repository creation

FOUNDRY creates the target from STRATA, then prepares the governance seed branch with a **product-neutral README and brand-guide scaffold** before opening the seed PR. The script `scripts/prepare-product-branding.sh` deletes STRATA-specific `branding/` assets **only on the seed branch**, never directly on `main`. It refuses to proceed if the README does not match the STRATA starter, if expected branding fingerprints are missing, or if unexpected branding files are present. This prevents silently deleting already customized product artwork.

The seed PR must be reviewed and squash-merged after governance verification; until then, the generated repository's `main` still contains the template's STRATA branding. Product-specific approved images are deliberately not fabricated or copied from other SUN products. The scaffold guide describes required banner, originals archive, compact variants and provenance. On a retry after a partial run, inspect the seed branch before rerunning; a product-neutral README is treated as already initialized.

**Validation:** Review the seed PR diff to confirm STRATA banner, SVGs, archive and template usage guide were removed, and that `README.md` plus `branding/BRAND-GUIDE.md` are product-neutral. After squash merge, confirm `main` contains no inherited STRATA logo, and then configure the approved product identity. A controlled disposable-repository provisioning test was completed in November 2026 (details below). Do not create further disposable repositories without explicit approval.

## Recovery safeguards (factory resume)

Resume now rechecks the expected seed PR's open state, target `main`, source branch, and repository identity before proceeding. A product-neutral README is not sufficient by itself to declare branding initialization complete: the script also checks that the inherited STRATA banner is absent, the product brand guide exists, and the STRATA template guide is removed. Ambiguous partial states fail closed for manual inspection.

When a seed branch exists but no PR was opened, the workflow avoids overwriting an already-created governance seed document. If required checks fail, inspect the PR and its CI logs, correct the issue on the seed branch, and rerun the factory in `resume` mode. Governance Apply/Verify requirements are unchanged.

**Known limit:** Resume may still require manual recovery for partial states that cannot be identified safely. The live test covered a normal create/resume sequence, not every possible interruption point.

## Factory v1 live validation — November 2026

A temporary public repository, `sunstriker2009/sun-foundry-validation`, was created through Repository Factory and subsequently deleted after validation. Observed results:

| Test | Outcome |
| --- | --- |
| STRATA template provisioning | Passed |
| Product-neutral branding on seed branch | Passed |
| Required PR checks | Passed |
| Governance Plan, Apply and strict Verify on initial creation | Passed |
| Resume against an already protected repository | Initially failed; fixed by FOUNDRY PR #41 |
| Repeat resume after idempotency fix | Passed (owner-reported successful workflow run) |
| Squash-merge and automatic seed branch deletion | Passed (verified: only `main` remained; seed content on `main`) |
| Disposable repository cleanup | Passed (GitHub repository lookup returned 404 after deletion) |

**Recovery defect found:** Initial resume failed because Apply rejected an existing `SUN Main Protection` ruleset unconditionally. PR #41 changed Apply to verify an existing ruleset and settings exactly, without overwriting it; policy drift still fails closed.

**Validation boundaries:** This is evidence for the exercised public-repository path, not blanket certification of private-repository ruleset availability, all failure/retry boundaries, GitHub permissions, or future API behavior. Repeat controlled integration tests after material governance changes.

## SUN governance fleet audit

The manual-only fleet audit is implemented for an explicit five-repository allowlist, with two concurrent strict verifier processes and a per-repository JSON report. It invokes only `verify`, never Apply or provisioning. Missing check policy, drift, private-plan limits and access errors cannot be reported as compliance.

See [fleet audit setup and result meanings](GOVERNANCE-FLEET-AUDIT.md) and [milestone status](ROADMAP.md). The first live report remains pending until the merged workflow is dispatched through the existing administration environment. No audit schedule or remediation is enabled.

## SUN ecosystem registration (phase 2)

After strict governance Verify succeeds, Repository Factory proposes a **pending-only** registration PR in `sunstriker2009/sun-ecosystem`. This also runs on resume, allowing recovery if an earlier registration step failed. Registration does not assign SUN IDs, approve product identities, or auto-merge.

For existing repositories, run [Register SUN Repository](https://github.com/sunstriker2009/sun-foundry/actions/workflows/register-sun-repository.yml) on `main` with a repository dropdown selection (or `other-repository` plus its short name), matching short-name confirmation, and `preview` (read-only) or `apply` (propose PR). The workflow uses the protected `repository-administration` environment and `SUN_REPO_ADMIN_TOKEN`, which must have repository read access and contents/PR write permissions on `sun-ecosystem`.

The script refuses to overwrite an existing registration branch, rejects mismatched confirmations and duplicate catalog entries, and refuses to create a pending duplicate for a repository already assigned an approved ID. Resolve existing branches or reconcile approved identities manually. The resulting PR updates `registry/repositories.json` and the generated README gallery only; it requires review and CI before squash merge.

**Limits:** This milestone does not synchronize PNG icons, install branding hooks in member repositories, or auto-merge any PR. The factory registration step is deliberately after governance Verify: if it fails, the repository may already be successfully provisioned; rerun `resume` or use manual registration to recover.

## Branding merge approval and automatic registry synchronization

Merging a branding PR that publishes or updates `branding/assets/symbol.png` on a confirmed SUN repository's `main` branch approves that artwork for the ecosystem registry. There is no second approval-ledger PR or SHA-256 allowlist. The historical `registry/symbol-approvals.json` ledger is no longer consumed.

FOUNDRY scans confirmed entries in `registry/repositories.json` daily at 08:17 UTC (03:17 Toronto standard time / 04:17 daylight time). Pending identities and repositories without the canonical asset are skipped. Changed symbols produce an ecosystem PR containing only the copied PNG, catalog metadata and generated gallery changes. Native squash auto-merge is requested; required GitHub checks and protections remain enforced. Unchanged symbols produce no PR or CI run. This is scheduled reconciliation, not an immediate cross-repository merge webhook; GitHub may delay scheduled runs.

SHA-256 remains as change-detection metadata (`iconSha256`), never as an approval restriction. PNG signature, decoded byte count, the 2,000,000-byte limit, registered identity checks, and the large-file Git Blobs API fallback remain enforced. Legacy source-path overrides require manual synchronization and manual merge.

Use **Reconcile Approved SUN Symbols** with manual dispatch to scan immediately, or **Sync Approved SUN Symbol** with a confirmed repository and preview/apply mode for a single target. The old approval-proposal entry point now delegates to canonical synchronization and no longer creates approval-ledger PRs.

### Credentials and prerequisites

The unattended workflow uses the `repository-symbol-sync` environment on `main` with secret `SUN_SYMBOL_SYNC_TOKEN`, requiring member-repository read and ecosystem contents/PR write access. Configure it without a reviewer gate for unattended execution. Owner-dispatched single-target workflows retain `repository-administration` and `SUN_REPO_ADMIN_TOKEN`.

Repositories must adopt the canonical path through their normal branding PR process. Product identity registration and governance controls are unchanged. Existing sync branches are preserved for inspection rather than overwritten; resolve a stale branch before retrying that repository. An error for one repository does not prevent subsequent sync attempts.

## Controlled governance alignment

Use [SUN Governance Alignment](GOVERNANCE-ALIGNMENT.md) for reviewed in-place changes to the explicitly mapped existing ruleset IDs. Run Plan, review the artifact, then Apply using its run ID and exact repository confirmation. Apply rechecks state and policy, strengthens the selected ruleset, updates merge settings and verifies the readback. This is separate from Factory Apply, which still refuses to overwrite an existing ruleset. The workflow uses `repository-administration` and `SUN_REPO_ADMIN_TOKEN`; no schedule or automatic fleet-wide Apply is enabled.

## Repository rename and reference migration

Use **SUN Rename Repository** with operation `execute` for automatic Plan → validate → Apply in one job. No separate plan review, Plan run ID or confirmation input is needed. Operation `plan` remains read-only. Apply prepares content writes before renaming and proposes reference updates through normal PRs; default branches and merge policy remain protected. The existing administration environment may require upfront approval to access its credential. See [rename guide](REPOSITORY-RENAME.md) for scope, recovery, live pilot evidence and external follow-ups. FOUNDRY self-renames remain excluded while it hosts shared Actions.


