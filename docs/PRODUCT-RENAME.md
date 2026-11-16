# Rename a SUN product

Use **SUN Rename Product** (`rename-product.yml`) in FOUNDRY. This pipeline changes a registered product's public display name first, with an optional repository rename in the same operation. It does not create a new product or assign a new SUN ID.

## Inputs

| Input | Meaning |
| --- | --- |
| `repository` | Current short repository name of a confirmed/established Ecosystem entry |
| `new_product_name` | New public name without the “by Sun” endorsement; 2–60 letters/digits/single spaces |
| `rename_repository` | Optional boolean, default **false** |
| `new_repository_name` | New short repository name; required only when repository rename is selected; otherwise empty |
| `operation` | **execute** (default): Plan → validate/write preflight → propose; **plan**: read-only |

One dispatch runs the complete operation. No Plan run ID or separate plan review is required. The existing `repository-administration` environment and `SUN_REPO_ADMIN_TOKEN` are reused; any upfront credential approval configured there still applies.

## Exact reference scope

The scope is **target repository + sun-strata + sun-foundry + sun-ecosystem**, deduplicated if the target itself is a governance repository. No owner repository listing, owner-wide search, other product scan or independent-project scan occurs.

Both pipelines use the shared `reference_scope` helper. The standalone repository-rename workflow now uses this same bounded scope instead of scanning every configured product. Its source still must be in its configured allowlist; the product pipeline derives eligibility from the authoritative Ecosystem registry.

## What Execute does

1. Snapshot numeric repository IDs/default-branch heads for the explicit scope.
2. Resolve the existing product/infrastructure entry from Ecosystem `registry/products.json`; require confirmed/established status, a stable SUN ID and a matching catalog entry.
3. Plan public-name updates in current documentation, Mermaid labels, recognized source display literals/HTML or JSX text, and JSON display metadata. Structured registry edits match the stable ID, preserve technical metadata, record `supersedes`/`previousNames`, and add a naming decision under `decisions/product-renames/`.
4. If repository rename is selected, include its reference updates in this same plan and call the existing repository-rename engine (`rename-repository.py:apply_plan`). This is an in-process reuse of that pipeline engine, not a second workflow dispatch. It avoids a second scan, approval or competing PR set.
5. Check identities, heads and existing proposal branches; prepare content trees/commits across affected repositories before any requested repository rename. Missing content access fails before the name changes.
6. Rename the repository only when selected, then create one combined reference/product PR per changed repository under a deterministic product-migration branch. Existing normal checks/review/squash policy remains; no direct main writes or auto-merge are added.

Product-only mode never calls GitHub's repository-rename PATCH. Product identity becomes active when the PRs merge, not merely because the pipeline opened them. Optional repository renaming happens during Execute, before reference PR merges, so that migration is not atomic.

## Preserved identities and limits

Keep the SUN ID, purpose, tagline, namespaces, package IDs, repository technical names unless separately selected, status and commercial-clearance state. Existing profile locations, env names, IPC/wire identifiers, storage formats, executable/file paths and saved-data compatibility are deliberately not globally renamed.

Source rewriting is conservative: recognized display fields and human text are updated, not arbitrary identifiers. Exact bare-name source literals without a display context may be technical and remain intact. Unusual frameworks, multiline/minified source, packaging executables, native Windows resource metadata and unsupported display patterns may need a follow-up PR. The run reports retained name matches rather than claiming complete technical migration.

Historical naming decisions/ADRs, validation evidence, approval ledger, archived artwork and numbered branding revisions stay intact. New public-name decisions preserve the old record and identify the superseded name. Binary PNG artwork is not regenerated: a wordmark baked into an old banner needs a separately approved branding package. Icon filenames and hashes remain unchanged by a product-name operation.

Registered/current or historical identity collisions are rejected. Naming approval does not establish trademark/domain/package clearance. FOUNDRY's public product name may change, but repository self-renaming stays blocked while it hosts shared Actions.

## Results and recovery

The `product-rename-run` artifact contains `plan.json`, `references.diff`, `summary.md` and `result.json`. The result distinguishes proposed PRs from a performed repository rename; inspect it after failures.

Before PRs merge, rerunning with the same inputs/default heads can reuse matching proposals via the shared engine. It never force-pushes or overwrites an unrelated/edited branch. If a head changes, inspect stale proposals before retrying. After the registry PR merges, its canonical name changes; a repeat request for that same name is rejected to avoid inferring a different historical migration. Finish any remaining already-created PRs through normal governance rather than guessing a reverse rename.

Content-write checks cannot guarantee later branch/PR permissions, token lifetime or an atomic multi-repository change. Existing partial-failure reporting/recovery applies. No deployment, release, schedule activation or resumption of paused functional development is authorized by this pipeline.

## Validation

Mock API/temporary Git tests cover exact scope and deduplication, registry/catalog consistency, preserved IDs/technical aliases/history, read-only Plan, product-only execution without repository mutation, optional shared-engine rename and write-denial handling. The combined ORYVA → OUTPOST pilot succeeded in [run 43934714433](https://github.com/sunstriker2009/sun-foundry/actions/runs/43934714433). Its target [OUTPOST #175](https://github.com/sunstriker2009/sun-outpost/pull/175), [FOUNDRY #70](https://github.com/sunstriker2009/sun-foundry/pull/70) and [Ecosystem #37](https://github.com/sunstriker2009/sun-ecosystem/pull/37) PRs are merged. STRATA had no changes, so no PR was created there. The earlier run 43926894692 failed at content-write preflight before renaming; the successful retry followed a credential permission correction. This verifies the exercised combined path, not every retry boundary or display surface. See [remaining gaps](ISSUES-AND-GAPS.md).
