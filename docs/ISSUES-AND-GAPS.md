# Open issues and gaps

Checkpoint: 2026-11-16. This file records work remaining after the merged OUTPOST migration. No listed follow-up is permission to run a live mutation or resume development.

| ID | Status / evidence | Next action |
| --- | --- | --- |
| GAP-01 | Complete. OUTPOST #176 added dispatch coverage, #177 verified backend, frontend and reservation on install commit `d3d4903`, and #178 merged the tested Foundry pin. | Verify equivalent checks when adding adopters. |
| GAP-02 | Branch pilot complete in OUTPOST #177. Installer CLI produced byte-identical v3/v1 and v4/v2 pairs and preserved v1/v2. All five workflows passed at `07cdabd`. | The manual Foundry Actions Preview/Apply path was outside this pilot. |
| GAP-03 | All five hooks use Foundry `8d8c0d9`. Audited dispatch coverage against the active main rulesets. The live catalog accepted the five current repositories and rejected retired and unregistered names in a local smoke test. | Validate that a newly registered repository can use the inherited hook after registration approval during the next authorized factory run. |
| GAP-04 | Product rename deliberately preserves compatibility identifiers. Unrecognized display literals, native packaging/resource metadata and baked-in raster wordmarks may retain old names. | Classify retained matches in target + governance repositories; propose focused display/artwork fixes. Preserve Sun.Security/Sun.Workspace, package/env/profile/wire/storage identifiers unless separately approved. |
| GAP-05 | Multi-repository rename is non-atomic. Prepared content writes cannot guarantee later branch/PR access or credential lifetime. | Inspect result artifact and existing PRs after a failure. Reuse matching proposals only; refuse edited/unrelated branches. After registry merge, finish outstanding PRs rather than repeat the old rename request. |
| GAP-06 | First OUTPOST attempt failed 403 at content-write preflight; successful retry followed token permission correction. Actions permission does not substitute for Workflows permission when editing workflow files. Secret permissions/expiry are not independently visible. | Keep access to target and governance repos with Contents, Pull requests, Actions, Administration and Workflows permissions needed by the selected operation. Rotate through Actions secrets only; diagnose the actual failed endpoint. Success certifies that run, not future token state. |
| GAP-07 | Five-repository governance pass is operator-reported historical evidence. Cleanup independently read only FOUNDRY/Ecosystem required checks. | Use existing manual read-only fleet audit after governance changes; do not claim a continuously refreshed full pass. |
| GAP-08 | Legacy archives and historical ledgers remain intentionally intact. Snapshot ZIPs represent complete resulting asset trees, not original upload bytes/provenance. | Separate reviewed archive/provenance migration if needed; no cleanup by installer. |
| GAP-09 | Factory live testing covers normal public create/resume, not every interruption/private-plan boundary. Rename tests cover logic, not all native/interactive display surfaces. | Expand integration coverage only for a concrete change or authorized pilot; avoid mutation-heavy repeated tests. |
| GAP-10 | Cleanup PRs must merge to become the default-branch handoff. Retired workflows may remain visible in Actions history. | Merge the paired cleanup/doc PRs after checks; no run-history deletion is needed. |

## New-repository branding pilot

- [Factory run 44258089909](https://github.com/sunstriker2009/sun-foundry/actions/runs/44258089909) succeeded for `sun-foundry-pilot`. The governance Apply, strict Verify, and Ecosystem proposal steps passed. GitHub reports the owner account as the dispatch actor.
- [Seed PR #1](https://github.com/sunstriker2009/sun-foundry-pilot/pull/1) is open. `repository-validation` and `conventional-title` both passed on `a33830ca011ffe9b6adbb50f80649e9330ba71ec`.
- [Ecosystem PR #44](https://github.com/sunstriker2009/sun-ecosystem/pull/44) proposes a pending registration. Ecosystem `main` had no pilot entry at this checkpoint. The owner must approve the identity and classification before installer verification.
- The [inherited hook](https://github.com/sunstriker2009/sun-foundry-pilot/blob/main/.github/workflows/branding-auto-install.yml) pins `8d8c0d908ad7d242c34ab4c2f28a43ce18ee79ae`. The owner-push ZIP test, installer run, and checks on the resulting revision commit are pending.

## Operational boundaries

FOUNDRY repository self-rename is blocked while it hosts shared Actions. Rename reference scope is the target + STRATA + FOUNDRY + Ecosystem only, deduplicated; never enumerate every owner repository. The rename pipelines automatically Plan → validate → Apply/propose in one job; any existing upfront administration-environment credential gate remains. Governance alignment is a different controlled workflow and still requires a reviewed Plan run ID.

Daily symbol reconciliation remains 08:17 UTC plus manual dispatch. Merge of a canonical branding PR is the artwork approval; SHA-256 is integrity/change detection only. No separate signature/ledger approval is required. Functional-development schedules for the former ASTELVO/ORYVA products remain paused under their current WORKBENCH/OUTPOST identities. No cleanup item resumes them.
