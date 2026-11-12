# Repository automation

Use two supported workflows:

- **Repository Factory** (`.github/workflows/repository-factory-v1.yml`): create a repository or resume interrupted provisioning. Initializes a seed PR, waits for CI, applies and strictly verifies governance.
- **Repository Maintenance** (`.github/workflows/repository-factory-resume.yml`): diagnose, plan, apply, or verify governance on an existing repository without creating or seeding it.

Both require owner-initiated manual dispatch on `main` and the `repository-administration` environment credential. Exact repository confirmation remains required for mutations.

Retired workflows: original Repository Factory (create + plan only), standalone Seed CI, and legacy Provisioning. Git history retains their definitions if recovery is needed. The supported workflows above replace their functions.

For normal setup, prefer **Repository Factory**. For troubleshooting and targeted reconfiguration, use **Repository Maintenance**.

After Factory succeeds, squash merge its disposable seed PR manually to test the merge and branch-cleanup policy.
