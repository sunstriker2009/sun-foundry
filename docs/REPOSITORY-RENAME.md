# Rename a SUN repository

Use **SUN Rename Repository** (`rename-repository.yml`) on FOUNDRY main. This is a manual, owner-initiated workflow through `repository-administration`, using `SUN_REPO_ADMIN_TOKEN`. It does not rename any repository when the implementation PR is merged.

## Plan, review, Apply, merge, verify

1. Select operation `plan`. Enter the current short repository name and proposed new short name, without an owner. The current name must appear in `config/workflow-repositories.json`. Names are lowercase; owner transfers are outside scope.
2. Inspect the successful run's `repository-rename-plan` artifact: `summary.md`, `references.diff`, `plan.json` and `result.json`. It captures numeric repository IDs, default-branch heads and exact proposed text changes across every configured SUN repository. Plan only reads repositories. Any inaccessible member fails the plan rather than silently reducing scope.
3. Run operation `apply` with the same names, the reviewed Plan run ID, and confirmation exactly `old-name -> new-name`. The Plan must come from this workflow on current FOUNDRY main, be successful, and be less than seven days old. The existing administration environment approval remains required.
4. Apply checks all repository IDs, default-branch heads and proposal branch conflicts before changing the repository name. It verifies the rename response, then creates reference-update branches and PRs in affected repositories. It never writes a protected default branch or requests auto-merge.
5. Review and squash-merge the reference PRs promptly. Rename and multi-repository PR merges are not atomic: the repository name changes during Apply, while reference changes take effect only when their PRs merge. Coordinate a maintenance window, leave functional development paused, and avoid uploading branding packages until workflow guards and configuration are updated.
6. Verify the new repository URL and numeric ID, required CI, registry/gallery rendering, workflow dropdowns and repository guards. Run a read-only governance fleet audit after configuration PRs merge. Follow the external checklist below before declaring migration complete.

## What is updated

The scanner reads tracked regular UTF-8 files on each configured default branch. It replaces exact owner/repository references (URLs, git remotes, API paths, Action references and repository guards), exact quoted short-name values/keys, and whole YAML scalar/dropdown values. Thus FOUNDRY allowlists, ruleset mappings and choices, Ecosystem product/repository mappings and generated gallery links, member workflow guards and documentation links are proposed together. Existing numeric ruleset IDs remain unchanged.

Product display names, SUN IDs, .NET namespaces, package names distinct from the exact repository short name, asset filenames and PNG artwork are not renamed. Reference updates are mechanical: inspect the diff for any package identifier exactly equal to the repository short name before merging.

The scan preserves `branding/archive/` and `branding/revisions/`, binary files, symbolic links and submodules. Files over 1 MB are reported as unscanned. Remaining old-name matches are listed for inspection, including intentional historical/asset-path matches. An empty remaining-match list does not certify external services. The plan is limited to 12 MB; oversized plans fail before Apply.

## Credentials and scope

The existing administration token needs Administration write on the target, read/Contents write/Pull requests write across affected repositories, and permission to update workflow files. Plan needs read access across the configured scope. Do not paste credentials into workflow inputs. Missing access fails; no alternate credentials or new PAT are created by this workflow.

FOUNDRY cannot rename itself in v1 because it hosts shared Actions. GitHub does not redirect calls to Actions hosted in renamed repositories; migrate Action consumers through separately reviewed work before considering a controller rename. The five-core-repository configured scope excludes independent repositories such as MarketPilot AI unless explicitly added through review. No schedules are activated or resumed.

## Recovery

`result.json` records whether rename completed and PR URLs created before a failure. A GitHub rename and cross-repository proposals cannot be rolled back atomically. Inspect live state before retrying; never automatically rename back or overwrite a branch.

If the rename succeeded but proposal creation failed, rerun Apply with the same reviewed plan while all planned default-branch heads remain unchanged. Numeric ID validation recognizes the new name, and matching proposal branches/open PRs are reused. Unrelated or edited proposal branches are refused.

If a default branch changed, or a reference PR already merged, create a fresh Plan with the original old/new names while the old URL still redirects to the same repository ID. Recovery scanning recognizes the renamed target. Before replanning, review/merge or close/delete any prior proposal branches through normal governance; old proposals are never overwritten. Once the source name has been removed from the configured allowlist, remaining work requires normal targeted PRs or a separately reviewed scope update. Do not reuse the old repository name: doing so can break redirects and recovery identity checks.

## External checklist

Manually inspect Pages URLs/custom domains, published packages and container images, deployment/OIDC trust policies, secrets and variables containing URLs, webhooks, installations, local git remotes, other repositories, open feature branches, pinned historical Action references and services outside GitHub. Existing branch content and historical commits are not rewritten. Updating a workflow consumer PR does not fix an old pinned commit; inspect consumers before any repository that hosts Actions is renamed.

GitHub reference: https://docs.github.com/en/repositories/creating-and-managing-repositories/renaming-a-repository

## Validation status

Mock API and temporary local Git tests cover preview/reference rewriting, collision/staleness checks, immutable archives, retries and protected-branch boundaries. Live repository renaming has not been exercised. A real rename requires its own reviewed Plan and explicit Apply; no disposable live repository was created for testing.
