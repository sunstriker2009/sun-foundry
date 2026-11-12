# Owner-authorized provisioning

SUN administration workflows are restricted at the job level to manual `workflow_dispatch` runs initiated by `sunstriker2009` on `main` in `sunstriker2009/sun-repo-bootstrap`. Other actors cannot start the credential-bearing jobs.

## Removing repetitive approval

**GitHub does not natively auto-approve a required-reviewers environment based on workflow actor.** This PR does not remove existing environment approvals.

After reviewing and merging this change, the owner can choose to remove **Required reviewers** from `repository-administration` in GitHub Settings → Environments, while **retaining the environment and its secret**. Set **deployment branches/tags** to selected branches: `main`. Leave `SUN_REPO_ADMIN_TOKEN` environment-scoped.

Only do this if the repository is trusted: any person who can modify workflow code on `main` could otherwise use the secret. Keep `main` protected, restrict repository collaborators and Actions workflow modification, and use least-privilege credentials. A workflow actor check is a useful guard, **not an independent security boundary** against malicious changes to trusted workflow code.

The token owner and the initiating GitHub actor are different concepts. A PAT does not authorize a workflow dispatch. Owner-only dispatch is checked before the credential-bearing job begins.

## Trade-off

Removing required reviewers also removes the independent human approval gate for the environment. Exact target confirmation for create/seed/apply remains, and all operations retain audit logs. If independent review is required, retain required reviewers or implement a separate GitHub App authorization service.

## Test

1. Merge after CI.
2. Confirm owner-initiated runs on main reach the job.
3. Confirm an unauthorized actor cannot enter an administration job.
4. Only then optionally remove environment required reviewers and test a non-mutating Resume Diagnose run.
