# Repository automation

Use two supported workflows:

- **Repository Factory** (`.github/workflows/repository-factory-v1.yml`): create a repository or resume interrupted provisioning. Initializes a seed PR, waits for CI, applies and strictly verifies governance.
- **Repository Maintenance** (`.github/workflows/repository-factory-resume.yml`): diagnose, plan, apply, or verify governance on an existing repository without creating or seeding it.

Both require owner-initiated manual dispatch on `main` and the `repository-administration` environment credential. Exact repository confirmation remains required for mutations.

Retired workflows: original Repository Factory (create + plan only), standalone Seed CI, and legacy Provisioning. Git history retains their definitions if recovery is needed. The supported workflows above replace their functions.

For normal setup, prefer **Repository Factory**. For troubleshooting and targeted reconfiguration, use **Repository Maintenance**.

After Factory succeeds, squash merge its disposable seed PR manually to test the merge and branch-cleanup policy.

## STRATA branding isolation during repository creation

FOUNDRY creates the target from STRATA, then prepares the governance seed branch with a **product-neutral README and brand-guide scaffold** before opening the seed PR. The script `scripts/prepare-product-branding.sh` deletes STRATA-specific `branding/` assets **only on the seed branch**, never directly on `main`. It refuses to proceed if the README does not match the STRATA starter, if expected branding fingerprints are missing, or if unexpected branding files are present. This prevents silently deleting already customized product artwork.

The seed PR must be reviewed and squash-merged after governance verification; until then, the generated repository's `main` still contains the template's STRATA branding. Product-specific approved images are deliberately not fabricated or copied from other SUN products. The scaffold guide describes required banner, originals archive, compact variants and provenance. On a retry after a partial run, inspect the seed branch before rerunning; a product-neutral README is treated as already initialized.

**Validation:** Review the seed PR diff to confirm STRATA banner, SVGs, archive and template usage guide were removed, and that `README.md` plus `branding/BRAND-GUIDE.md` are product-neutral. After squash merge, confirm `main` contains no inherited STRATA logo, and then configure the approved product identity. Do not create a disposable repository without explicit approval; a controlled provisioning test is still pending.
