# Branding ZIP installer

The manual **SUN Branding ZIP Installer** lives in FOUNDRY. The owner is implicit (`sunstriker2009`); choose one of the five existing SUN repositories. It uses `repository-administration` and the existing `SUN_REPO_ADMIN_TOKEN`, with target Contents read/write and Pull requests read/write access. It never changes governance or merges artwork automatically.

## Preferred: install on the upload branch

Repositories opt in with `.github/workflows/branding-auto-install.yml`, which invokes the shared FOUNDRY `actions/install-branding-zip` action pinned to a reviewed commit. WORKBENCH is the first adopter; other repositories are unchanged until their own opt-in PRs are reviewed.

1. On any feature branch containing that workflow, upload **one** ZIP under its original name to `branding/revisions/`, for example `branding/revisions/workbench-w2-assets-v1.zip`. Commit the upload to that branch. No inbox or manual Preview dispatch is needed.
2. The push workflow validates the package, backs up current assets as `v1.zip` if needed, installs assets, records `v2.zip` (then `v3.zip`, etc.) and removes the original upload in a **follow-up commit on the same branch**. Existing repository text, legacy archives and non-asset configuration are untouched.
3. Review the branch’s installed banner, symbol, icons and checks, then squash-merge its PR. This merge approves artwork for the existing daily/manual registry synchronization.

`v1.zip`, `v2.zip`, etc. are immutable snapshots, not upload names. Numbered snapshots are ignored by automatic detection, so the follow-up commit cannot recursively reinstall them. Invalid or ambiguous uploads (more than one pending ZIP) leave remote assets and the original filenames unchanged. Fix/remove the invalid package and commit again, or rerun the workflow after fixing an infrastructure failure. Already-identical packages remain under their original names and create no version or commit.

The hook runs for owner pushes to feature branches. It deliberately does not write directly to protected `main`; branches created before adoption must include the workflow before an upload can trigger it. The target branch must still be at the triggering commit when installation pushes. Concurrent updates fail without force-pushing; retry at the new tip. A failed network response after an accepted push may report failure despite a completed follow-up commit, so inspect the branch before retrying.

### Token and CI behavior

The hook uses the repository’s short-lived `GITHUB_TOKEN`, with Contents write, Actions write and Pull requests read permissions. It does not require a new PAT or an administration-environment approval. No repository settings are changed.

GitHub suppresses normal push/PR workflow events caused by `GITHUB_TOKEN` commits. If a PR is already open, the action explicitly dispatches the configured CI/title workflows on the new branch tip. Adopters must enable `workflow_dispatch` on those workflows and perform the same required validations on dispatch. If no PR exists yet, opening it later triggers the normal checks. A dispatch failure is reported; it must be retried before merging. No fabricated status or CI bypass is used.

## Manual fallback: Preview / Apply from FOUNDRY

1. In the **target repository**, upload your ZIP using GitHub **Add file → Upload files** under `branding/revisions/` (legacy `branding/inbox/` is also accepted by this manual fallback). Keep its original filename, for example `strata.zip`. Commit through the normal PR process and merge the upload to `main`. Uploading the package alone does not install or approve the artwork.
2. Open [SUN Branding ZIP Installer](https://github.com/sunstriker2009/sun-foundry/actions/workflows/branding-zip-install.yml) on FOUNDRY `main`. Choose the target dropdown, leave operation `preview`, and enter the ZIP basename. The default is `branding.zip`. Leave rollback and confirmation empty.
3. Review the successful preview’s changed asset paths, target commit and proposed revision in the run summary. Preview creates no target branch or revisions. It can run with defaults when `branding/revisions/branding.zip` (or the legacy inbox equivalent) exists in FOUNDRY; an absent upload fails with no changes.
4. Run again with operation `apply` and the short target name as confirmation. Apply revalidates the current target-main package and opens `chore/branding-install` as a PR. There is no Plan run ID or SHA-256 approval field.
5. Visually review the banner, symbol, icons and any other changed assets, wait for required checks, and squash-merge. The merge installs and approves the artwork. The normal daily (08:17 UTC) or manual symbol reconciliation subsequently synchronizes the canonical symbol with the ecosystem registry.

GitHub’s dispatch form cannot attach files; a committed ZIP is the upload mechanism. ZIPs must be at most **20 MB compressed**, with at most 256 entries, 12 MB per entry and 64 MB expanded. Use the basename only; paths, URLs and arbitrary-owner repositories are rejected. Uploads and snapshots are ordinary Git blobs, so repeated packages increase repository history size.

## Accepted package layout

A package contains `branding/assets/`, either at the ZIP root or beneath one enclosing export folder, as in `workbench-w2-v1/branding/assets/`. Required files:

- `readme-banner.png`: landscape PNG, at most 8192 pixels wide.
- `symbol.png`: square PNG, 128–4096 pixels per side.
- `icons/icon-{size}.png`: exact square dimensions for 16, 24, 32, 48, 64, 128, 256, 512 and 1024.

Additional PNG icons up to 1024 pixels, `social-card.png`, `social-preview.png`, and PNG references beneath `refs/` are supported. Package-root `README.md`, `PREVIEW.png` and `manifest.json` are informational and ignored. Other files are rejected. The installer decodes static PNGs, checks image and ZIP limits, rejects traversal, duplicate names, links and encrypted entries, and never executes package contents. It does not compare artwork visually or treat an export manifest digest as approval.

Canonical destinations remain `branding/assets/readme-banner.png`, `branding/assets/symbol.png` and **`branding/assets/icons/`**. The icons directory is replaced with the package’s PNG icon set, including removal of obsolete icon files. Other existing assets and references are retained unless the package replaces the same path. Repository README text, app asset copies, asset-generator configuration, brand guides and legacy archives are outside the installation scope. If an application needs non-PNG icons or copies elsewhere, handle that adoption explicitly in the branding PR. A generated-output pipeline is separate; its old master/configuration must be updated explicitly before using it to export new artwork.

## Revision behavior

| Event | Outcome on merged target `main` |
| --- | --- |
| First installation | Existing complete `branding/assets/` backed up as `branding/revisions/v1.zip`; resulting assets stored as `v2.zip` |
| Later installation | Next integer version (`v3.zip`, etc.); original upload replaced by the numbered snapshot in the installation commit/PR |
| Invalid ZIP / failed preview / failed preparation | Original upload filename and active assets retained; no version consumed |
| Already identical | No PR or revision; original upload retained |
| Rollback | Restores a selected snapshot as another new revision; previous ZIPs stay immutable |

A revision ZIP is a complete **asset-tree snapshot**, including retained references, rather than a verbatim copy of the uploaded ZIP. `current.json` records the operation, source, changed paths and resulting version. On the first install into an empty asset tree, `v1.zip` is an empty snapshot. Feature branches show proposed versions; only merging records them on main. Closing a proposal does not consume its version on main.

## Rollback and recovery

Run `preview` with **Rollback revision** set to an existing `v1.zip`, `v2.zip`, etc.; filename is ignored. Inspect the summary, then run `apply` with the same revision and target confirmation. Review and merge the rollback PR. Rollback restores the full snapshot, including deletion of assets absent from that snapshot; it does not rewrite old revision ZIPs.

There is one pending installer branch per target, with serialized manual runs. An existing branch blocks another Apply. Review/merge it, or close its PR and delete its branch before retrying. If PR creation fails after push, recover the existing branch by opening its PR manually. Never force-push it. If branding, inbox or revisions change on main after a proposal, close/delete it and re-preview/re-apply against current main. Revision gaps fail closed for inspection. The branch hook does not use this separate proposal branch; it updates the original feature branch directly.

Validation and staging failures occur before publishing a branch; local replacement restores the original tree if the directory swap fails. Remote push/PR failures leave main unchanged. A failed upload remains under its original name. Legacy `branding/archive/` remains intact; migration or cleanup requires a separate reviewed change after the pilot.

Local use: install `assets/requirements.txt`, then run `python3 scripts/install-branding.py --repository-root /path/to/checkout --zip /path/to/package.zip`. This previews only; `--apply` writes the local checkout, and `--rollback` interprets the ZIP as an existing revision snapshot. The local CLI does not create or merge PRs.

## Validation and rollout gate

Regression coverage exercises preview immutability, exact initial backup, monotonic versions, rollback, no-op behavior, rejected archives, symlinks, dimension failures and interrupted replacement. A local read-only check also accepted the existing Workbench export layout. The first live installation pilot merged in [WORKBENCH #39](https://github.com/sunstriker2009/sun-workbench/pull/39); its main records the original asset backup as v1.zip and the installed Workbench package as v2.zip. The same-branch hook and revision metadata were checked during the governance handoff. Live rollback remains pending; validate it on one explicitly selected repository before broad adoption. See [handoff evidence and resume boundaries](GOVERNANCE-HANDOFF.md).
