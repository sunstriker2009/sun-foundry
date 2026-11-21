# Foundry workflow handbook

## Access and inputs

Run owner-dispatched administration workflows from `main` in `sunstriker2009/sun-foundry` as `sunstriker2009`. The protected jobs use the `repository-administration` environment and its `SUN_REPO_ADMIN_TOKEN`. Scope the credential to the target repositories and API operations the workflow uses. Workflow-file updates during renames require Workflows permission in addition to Contents and pull request access. Repository creation, rulesets, settings, and renames require the relevant administration access.

A workflow authorization check and a GitHub environment approval are separate gates. If a job waits, inspect the run for a deployment review prompt, then check the environment's reviewers, self-review policy, allowed branches, and wait timer. If the job skipped, inspect its actor, branch, repository, and triggering event. For a credential or access error, inspect the failing step and use [Repository Maintenance](#repository-maintenance) with `diagnose` when appropriate. Check existing runs before retrying.

Forms use short names such as `sun-codefolio`. Where a dropdown offers `other-repository`, enter the short name in `repository_name`. Repeat the short name in `confirm_repository` when required. Dropdowns are curated in [workflow repository configuration](../config/workflow-repositories.json) and the workflow files. Alignment and the fleet audit use their own policies. Validate input changes with `python3 scripts/resolve-workflow-repository.py --check-workflows`.

## Repository provisioning and maintenance

### Propose SUN Product Registration

Run [Propose SUN Product Registration](https://github.com/sunstriker2009/sun-foundry/actions/workflows/propose-product-registration.yml) for a new SUN product.

| Input | Meaning |
| --- | --- |
| `product_name` | Base display name, using ASCII letters, digits, spaces or hyphens, starting and ending with a letter or digit and containing at least one letter. Omit `sun-` and `by Sun`. |
| `product_family` | `productivity` assigns the next `SUN-PNNN`; `application_component` assigns the next `SUN-CNNN`. Governance IDs are outside this form. |
| `short_description` | Optional single line, up to 180 characters after trimming. Exclude `<`, `>`, `\|`, `[`, and `]`. |

Foundry checks availability and uses the next ID in its [product catalog](../registry/product-catalog.json). The repository slug is the lowercased name prefixed with `sun-`, with runs of spaces and hyphens collapsed to a single hyphen. `CodeFolio` becomes `sun-codefolio` and publishes as **CodeFolio by Sun**. Assigned IDs stay stable across renames. An omitted description is stored as JSON `null` in Foundry and the product manifest, with a family-specific fallback used for the published gallery summary.

1. The owner dispatch opens and approves the Foundry catalog PR. After the required `build` validates the proposal against current `main`, Foundry squash-merges the tested PR head using the owner's credential.
2. The merged registration triggers the Factory relay, which dispatches [Repository Factory](#repository-factory) on `main`. The factory verifies the approved registration, provisions a public repository from STRATA, and adds `branding/manifest.json` and `branding/revisions/.gitkeep` in the seed PR. The manifest carries `family-id`, `product-name`, and `short-description`.
3. The factory waits for seed CI, applies and strictly verifies governance, checks the tested seed head, and squash-merges it. After verifying the manifest and revision marker on product `main`, it opens a separate Foundry publication PR and requests protected squash auto-merge. Once the published entry is on Foundry `main`, inherited branding can recognize the product.

If a proposal is stale because another registration advanced the counter, run a fresh owner dispatch for the new ID and close the superseded PR. For provisioning failures after approval, use the Factory recovery dispatch below.

### Repository Factory

[Repository Factory](https://github.com/sunstriker2009/sun-foundry/actions/workflows/repository-factory-v1.yml) provisions an owner-approved product registration. The proposal merge triggers the Factory relay. If the relay fails or provisioning is interrupted, the owner can dispatch Factory on `main` using the same merged Foundry PR number as `approved_registration_pr` and the exact short slug as `confirm_repository`. Both dispatch paths validate the merged approval and the current catalog before entering the administration environment.

The seed replaces STRATA artwork and the template README with a product-neutral README. If `repository-validation` or `conventional-title` fails, fix the seed branch and retry the approved registration. Factory resumes a matching seed or continues from a matching product `main`. Inspect an existing repository that lacks either verified match. Factory can reuse an identical publication PR. Inspect changed or stale publication branches before retrying.

### Repository Maintenance

Run [Repository Maintenance](https://github.com/sunstriker2009/sun-foundry/actions/workflows/repository-factory-resume.yml) on an existing repository.

| Operation | Purpose |
| --- | --- |
| `diagnose` | Check authenticated access and basic repository identity. |
| `plan` | Read live settings and report proposed governance changes or capability limits. |
| `apply` | Apply supported settings and protection. Requires exact check names and short-name confirmation. |
| `verify` | Read-only strict verification. Requires exact check names. |

Use comma-separated check job names from the target policy; the form defaults to STRATA's `repository-validation,conventional-title`. For example, use those checks and `other-repository` / `sun-codefolio` to verify CodeFolio. Use controlled alignment for a supported existing ruleset that needs changes.

### Register SUN Repository

Use [Register SUN Repository](https://github.com/sunstriker2009/sun-foundry/actions/workflows/register-sun-repository.yml) to propose a Foundry catalog entry for an existing repository through the pending-registration path. Choose the repository, repeat its short name, and use `preview` for a read-only check or `apply` to open a pending PR. This path leaves ID assignment and identity confirmation to separate review. Use [Propose SUN Product Registration](#propose-sun-product-registration) for the automated new-product lifecycle.

## Governance

### Strict verification and fleet audit

The strict baseline checks repository merge and branch-cleanup settings, the active `SUN Main Protection` ruleset restricted to `main`, its bypass list, PR protections and exact required checks with up-to-date enforcement. Coverage is limited to the named baseline; additional rulesets, stronger review profiles, secrets and operational merge behavior need separate evidence. The branch-deletion setting can be read back; observing deletion requires a real squash merge.

If GitHub reports the applicable private-repository plan restriction, Plan/Audit reports that enforcement is unavailable and Apply/Verify fails closed. Investigate other access errors separately.

[SUN Governance Fleet Audit](https://github.com/sunstriker2009/sun-foundry/actions/workflows/governance-fleet-audit.yml) is a manual read-only run over the explicit [allowlist](../config/governance-fleet.json). It reports each target's strict result and publishes JSON evidence. A failed run with a complete report can indicate drift. Missing credentials or an incomplete report cannot establish compliance.

For local verification, use the .NET 10 SDK and set `GH_TOKEN` securely in the shell.

```sh
dotnet run --project src/Sun.RepoBootstrap -- --repo sunstriker2009/sun-codefolio --mode verify --checks repository-validation,conventional-title
```

### SUN Governance Alignment

[SUN Governance Alignment](https://github.com/sunstriker2009/sun-foundry/actions/workflows/governance-alignment.yml) updates an existing ruleset identified by ID in the [alignment policy](../config/governance-alignment.json). It retains the ruleset ID, stronger supported reviews and existing check app bindings. Conflicting rulesets, unexpected check names, bypass actors or wider branch scopes require separate review.

1. Run `plan` for the selected repository. Review the summary and `governance-alignment-plan` artifact containing `plan.json` and `result.json`.
2. Run `apply` for the same repository with the successful `plan_run_id` and its short name in `confirm_repository`. Apply recomputes the plan and refuses expired artifacts or policy and live-state drift. Plan artifacts expire after seven days.
3. Inspect the readback, or run `verify` independently. If the ruleset write succeeds and the settings write fails, keep the stronger ruleset and make a fresh Plan from live state.

## Branding and gallery

### Install branding ZIP on this branch

The [branch hook](../.github/workflows/branding-auto-install.yml) calls the [shared installer](../actions/install-branding-zip/action.yml) at a pinned Foundry commit. STRATA supplies the hook to newly generated repositories. Existing repositories and older branches need the hook present before the upload push.

Commit one ZIP under its original, unnumbered filename directly in `branding/revisions/` on a feature branch. An owner push triggers the installation. Member repositories must be confirmed in the live Foundry catalog. The hook adds an installation commit on the same branch and removes the upload only after successful preparation. Review the output and required checks before squash-merging the artwork PR.

The hook uses the repository `GITHUB_TOKEN` with Contents write, Actions write, and Pull requests read. For an existing PR, it explicitly dispatches the configured validation workflows on the new tip; those workflows must support dispatch and perform equivalent checks. Opening a PR after installation triggers the normal PR checks. Inspect the branch tip and validation results before retrying a failed push or dispatch.

Products can opt in to `update-readme` and `publish-pr` on the shared action. The README option initializes the stock product README from `branding/manifest.json` and links the installed banner. Later installs update the section between `<!-- SUN BRANDING START -->` and `<!-- SUN BRANDING END -->`. Existing custom READMEs without these markers are preserved.

PR publication requires a full-history checkout (`fetch-depth: 0`). It opens or reuses the branch's PR against `main` and requests squash auto-merge for a ready PR limited to README, assets and revisions. GitHub enforces the repository's required checks and reviews. Pass a repository-scoped GitHub App installation token as `publication-token` with Contents and Pull requests write access to trigger normal checks for a new PR. The repository token fallback needs Pull requests write and **Allow GitHub Actions to create and approve pull requests** enabled in the target's Actions settings. The fallback explicitly dispatches validation workflows, as does reuse of an existing PR. If publication fails after the installation push, rerun the original failed workflow to resume from the same installed commit.

### SUN Branding ZIP Installer

Use the [manual installer](https://github.com/sunstriker2009/sun-foundry/actions/workflows/branding-zip-install.yml) for a listed target, including snapshot rollback. For installation, merge the uploaded ZIP to target `main` under `branding/revisions/`. This fallback also accepts the legacy `branding/inbox/` path. Select the target and use `operation: preview` with the ZIP basename in `filename` (default `branding.zip`). Inspect the changed paths and proposed revision. Run `apply` with the same inputs and the short target name in `confirm_repository` to open an installation PR. For rollback, set `rollback_revision` to an existing snapshot such as `v2.zip`; the filename is ignored.

Review and squash-merge the installer PR. Only one `chore/branding-install` proposal branch can be pending per target. If the push succeeded but PR creation failed, open its PR from the existing branch. If main's assets or revision history changed, close the stale proposal, remove its branch and preview again.

#### Packages and revisions

Put `branding/assets/` directly at the root of a newly generated installation ZIP. Export only the approved banner, symbol, concept artwork and icons listed below. The installer also accepts one enclosing export directory.

- Include a landscape `readme-banner.png` up to 8192 px wide, a square `symbol.png` from 128 to 4096 px, and exact square `icons/icon-{size}.png` for 16, 24, 32, 48, 64, 128, 256, 512 and 1024 px.
- Include the approved artwork reference as `branding/assets/concept-artwork.png`. When the banner is the approved artwork reference, include a copy under this filename. The installer continues to accept older ZIPs without concept artwork and maps a legacy `preview.png` to `concept-artwork.png`. See the [SUN branding standard](https://github.com/sunstriker2009/sun-ecosystem/blob/main/docs/governance/PRODUCT-BRANDING.md#5-branding-package-layout).
- Exclude design handoff documents, repository metadata, revision snapshots, nested ZIPs, `__MACOSX/` and `.DS_Store` from the installation ZIP. ZIP limits are 20 MB compressed, 64 MB expanded, 12 MB per entry and 256 entries.
- Imagery writes stay under `branding/assets/`. Revision bookkeeping is under `branding/revisions/`; product metadata stays in `branding/manifest.json`. The first installation snapshots the prior asset tree as `v1.zip` (empty if no prior assets) and the installed tree as `v2.zip`. `current.json` records the result. Later installs and rollbacks create the next numbered snapshot. Rollback restores the full selected asset tree.
- Keep numbered snapshots immutable. Invalid or ambiguous uploads consume no revision; identical assets produce no commit or revision and leave the upload in place. Revision gaps and stale branch tips require inspection before retrying.

Local preview uses `python3 scripts/install-branding.py --repository-root /path/to/checkout --zip /path/to/package.zip` after installing [dependencies](../assets/requirements.txt). Use `--apply` to write assets, `--rollback` to interpret a ZIP as a snapshot, and `--record-revision` for workflow-style revision bookkeeping.

### Symbol synchronization

Set a confirmed member's `symbolMode` in `registry/repositories.json` through a reviewed Foundry PR. Run `python3 scripts/render-repository-gallery.py` and include the generated gallery in the same PR.

| Mode | When to use it | How the gallery reads the symbol |
| --- | --- | --- |
| `live` | Public repository with approved artwork at `branding/assets/symbol.png` on `main`. Verify the raw URL loads without authentication before enabling it. | Derives the raw URL from the registered repository. Subsequent artwork changes need only the product's usual branding PR. GitHub image caching can delay display updates. |
| `copy` | Confirmed private repository whose owner explicitly approved the canonical PNG for public display. | The copy workflow verifies current visibility and reads only the canonical file on the member's `main`. It publishes the PNG under `gallery/` and records its SHA-256. |
| `text` | New or pending registrations, members awaiting artwork, and private members without public display approval. | Shows the repository name as a text tile. |

Review each private canonical symbol update as public artwork while the member is in `copy` mode. When revoking copy approval, set the mode to `text`, remove the catalog's `icon` and `iconSha256` fields and delete its gallery PNG in the same PR. Previously published copies can remain in public Git history or caches. For a visibility change, update the gallery mode as part of the change.

- STRATA supplies **Notify Foundry of a symbol update**. For private members, it dispatches targeted reconciliation when the canonical symbol changes on `main`. The source can also dispatch the relay manually from `main`.
- Install a dedicated relay GitHub App on Foundry with Actions write permission. In Foundry's `repository-administration` environment, set `SUN_SYMBOL_RELAY_APP_ID` and `SUN_SYMBOL_RELAY_APP_PRIVATE_KEY`. Factory copies the pair only to verified private products with the relay, using a credential with Secrets write. Existing private members can receive the pair as repository Actions secrets.
- [Sync Approved SUN Symbol](https://github.com/sunstriker2009/sun-foundry/actions/workflows/sync-approved-sun-symbol.yml) previews or applies a copy for one approved private member. Apply proposes a Foundry PR and requests protected squash auto-merge. [Reconcile Approved SUN Symbols](https://github.com/sunstriker2009/sun-foundry/actions/workflows/reconcile-approved-symbols.yml) handles approved copies daily at 08:17 UTC or on demand. On manual dispatch, a confirmed `owner/repository` target limits the run to that member. The publication credential is `SUN_SYMBOL_SYNC_TOKEN` in `repository-symbol-sync`, with member Contents read and Foundry Contents and Pull requests write. An unattended run requires an environment without a reviewer gate. Inspect existing proposal branches before retrying a conflict.

## Renames

| Workflow | Inputs and effect |
| --- | --- |
| [SUN Rename Repository](https://github.com/sunstriker2009/sun-foundry/actions/workflows/rename-repository.yml) | Enter a configured short `repository` and unused lowercase `new_name`. Renames the GitHub repository and proposes exact reference updates. |
| [SUN Rename Product](https://github.com/sunstriker2009/sun-foundry/actions/workflows/rename-product.yml) | Enter a registered short `repository` and `new_product_name` without the endorsement. Set `rename_repository` and enter `new_repository_name` only for a combined rename. The product ID and technical identity are preserved. |

Both offer read-only `plan`; `execute` prepares and validates a fresh plan in the same job. They scan the target plus STRATA, Foundry and Ecosystem, deduplicated. Workflows prepare content writes before any GitHub repository rename and open reference PRs through normal review and squash merge. Cross-repository renames and PR merges are separate operations. Foundry's own repository rename is blocked while it hosts shared Actions.

Inspect the `repository-rename-run` or `product-rename-run` artifact, including `result.json`, before retrying. Resume matching proposals and resolve edited or stale branches through review. After the registry PR merges, finish outstanding PRs against the recorded migration. Review retained display or packaging references, artwork, deployments, integrations and local remotes where applicable. Avoid global replacement of namespaces, package IDs, environment variables or persisted data identifiers.

## CI and developer validation

[CI](../.github/workflows/ci.yml) publishes Foundry's required `build` check. Scoped validation workflows exercise [workflow inputs](../.github/workflows/workflow-input-validation.yml), [factory recovery](../.github/workflows/factory-recovery-validation.yml), [Foundry registration](../.github/workflows/ecosystem-registration-validation.yml), [governance alignment](../.github/workflows/governance-alignment-validation.yml), [fleet audit](../.github/workflows/governance-fleet-validation.yml), [governance idempotency](../.github/workflows/governance-idempotency-validation.yml), [ZIP installation](../.github/workflows/branding-installer-validation.yml), [symbol sync](../.github/workflows/symbol-sync-validation.yml), and the [rename pipeline](../.github/workflows/product-rename-validation.yml).

[Asset preparation validation](../.github/workflows/asset-validation.yml) runs manually or on relevant paths. It runs generator and initializer regression tests, then generates and checks synthetic fixtures and Foundry's own configured assets. See the [local asset preparation guide](ASSET-ADOPTION.md) for inputs and outputs.
