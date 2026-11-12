# SUN Repository Factory (Phase 1)

The manually dispatched `SUN Repository Factory` workflow creates a repository from `sun-repo-template`, then runs a non-mutating governance Plan.

## Prerequisites

- `repository-administration` environment approval is required before repository creation.
- `SUN_REPO_ADMIN_TOKEN` must have repository creation rights and access to the new repository for the Plan operation.
- **Fine-grained PATs limited to selected existing repositories generally cannot access a newly created repository.** For this phase, configure a credential whose repository access includes newly created repositories (such as an appropriately authorized all-repositories token). Prefer a dedicated GitHub App with scoped installation permissions for future automation. Do not weaken permissions silently or expose the token.
- The account must be permitted to generate repositories from `sun-repo-template`. The target name must be unused.

## Run

Actions → SUN Repository Factory → Run workflow → enter new repository name, visibility, and exact name confirmation. Approve the protected `repository-administration` deployment.

Creation is **not automatically rolled back** if the Plan job fails. The workflow refuses to overwrite an existing repository.

## Why this is phased

The existing Apply CLI deliberately validates that required check names have already run on main or an open PR. A freshly generated repository may not have any check runs. Therefore Phase 1 intentionally stops after creation and Plan rather than pretending that Apply and Verify succeeded.

After creation:
1. Trigger the template CI through an initial documentation-only PR, and ensure both `repository-validation` and `conventional-title` appear.
2. Run the existing provisioning workflow: Apply (with explicit confirmation and approval), then Verify with exact check names.
3. Validate merge blocking and branch deletion on a disposable repository before wider rollout.

Phase 2 can automate CI seeding, Apply and Verify after the required check contexts exist, ideally using a GitHub App and a central audit trail. Keep all mutations behind an explicit authorization gate.
