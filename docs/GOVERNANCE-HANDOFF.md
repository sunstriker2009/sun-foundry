# SUN automation resumption handoff

Checkpoint: 2026-11-16. This repository document supersedes the archived conversation as the operational checkpoint. Verify current branches, PRs, workflow runs and registry before changing anything. Read [issues and gaps](ISSUES-AND-GAPS.md), [roadmap](ROADMAP.md), [cleanup record](WORKFLOW-CLEANUP.md) and the [central handbook](https://github.com/sunstriker2009/sun-ecosystem/blob/main/docs/workflows/README.md).

## Current identities and roles

| SUN ID | Public identity | Repository | Stable technical identity / role |
| --- | --- | --- | --- |
| SUN-001 | OUTPOST by Sun | sun-outpost | Sun.Security / Sun.Security.* / @sun-security/*; Identity. Trust. Protection.; HALO → ORYVA → OUTPOST |
| SUN-002 | WORKBENCH by Sun | sun-workbench | Sun.Workspace / Sun.Workspace.* / @sun-workspace/*; Organize. Script. Explore.; formerly ASTELVO |
| SUN-G001 | Ecosystem | sun-ecosystem | Registry, governance policy, gallery and central workflow handbook |
| SUN-G002 | STRATA | sun-strata | Repository template |
| SUN-G003 | FOUNDRY | sun-foundry | Repository factory and shared automation |

Registry files in Ecosystem are authoritative. Do not revive WORKBENCH's superseded SUN-009 assignment. Commercial name clearance is separate from approval. MarketPilot AI is independent and outside these rename scans unless explicitly targeted.

## Verified outcomes

The automatic combined ORYVA → OUTPOST product/repository pilot succeeded in [FOUNDRY run 43934714433](https://github.com/sunstriker2009/sun-foundry/actions/runs/43934714433). [OUTPOST #175](https://github.com/sunstriker2009/sun-outpost/pull/175), [FOUNDRY #70](https://github.com/sunstriker2009/sun-foundry/pull/70) and [Ecosystem #37](https://github.com/sunstriker2009/sun-ecosystem/pull/37) are merged; STRATA had no diff. Scope was target + the three governance repos. The earlier run 43926894692 failed 403 during content-write preflight, before rename. The operator corrected token permissions and retried successfully. Rename implementation: FOUNDRY #66/#68/#69. WORKBENCH reference/product migration was merged through product #41, FOUNDRY #67, Ecosystem #34 and STRATA #12.

At this audit, merged default heads were FOUNDRY `e412e3b51a7d69c726ecaa5e5e46b676aad62a74`, Ecosystem `f9feb225a090abc8c32fee3db1fae8051bd55081`, STRATA `abfeadab245fca4706a0744a40f25a79bd7cf461` and OUTPOST `d91fc8cf88d400846de4db04acdab22fb1f633be`. These are evidence anchors, not future expected heads. No open PRs were found in those four repos before cleanup. New cleanup PRs must be merged separately.

Shared branding installer/action are merged (FOUNDRY #62/#63). WORKBENCH's real same-branch installation succeeded in [run 43791300416](https://github.com/sunstriker2009/sun-workbench/actions/runs/43791300416), installation commit `04cbbf6db97ec48509f78457c823dfca5e0e9f3b`, merged artwork PR #39. Its canonical symbol matched the original package and v2 snapshot: 691,340 bytes, SHA-256 `74510e6401e69cf3096d8869cc08ffc2d018a1afca000ebd67965511a83577d7`; Ecosystem #34 includes the current WORKBENCH symbol. Original package: `workbench-w2-assets-v1.zip` (Library ID `libfile_67076a2f8abc8191837db3116d49da49`). OUTPOST adoption was product PR #173. Both product hooks pin shared action `c1680fc22fb35f9542b65dfb1b79449c0970a154`.

Governance alignment across five core repos was operator-reported complete. This cleanup read live required rules: FOUNDRY `build` and Ecosystem `gallery`; neither changed. No fresh full-fleet audit is claimed.

## Operating rules to preserve

Feature branch → PR → required checks/review → squash merge; no direct protected-main writes. Branding PRs do not auto-merge. Commit one originally named, unnumbered ZIP directly under `branding/revisions/` on a feature branch containing the hook. The action appends a same-branch installation commit, keeps immutable vN ZIP history, and removes upload only after success. Invalid/multiple uploads fail without consuming a version; identical assets make no install commit/version and retain upload; concurrent changes cause refusal. Initial assets become v1; first installed tree v2. Rollback creates another revision. Icons stay in `branding/assets/icons/`, references in `branding/assets/refs/`; approved raster PNGs stay canonical. Do not reconstruct them as SVG.

Hooks use repository GITHUB_TOKEN, not a new PAT. Token-authored commits require explicit equivalent validation dispatches for already-open PRs; OUTPOST verified these dispatches in pilot #177. Manual installer remains supported through `repository-administration` / `SUN_REPO_ADMIN_TOKEN`. Manual fallback supports revisions and legacy inbox uploads; it proposes a separate PR. Repository intro text, app copies/configuration, product identity and archive cleanup are outside automatic branding scope.

Merged canonical branding approves daily/manual gallery synchronization. Daily reconciliation stays at 08:17 UTC, not hourly; SHA metadata is not a second approval gate. Retain the historical ledger and legacy archives. Renames scan target + governance only and preserve stable compatibility identifiers. Automatic rename Execute has no separate Plan review; controlled governance alignment still does.

## Resume sequence

1. Verify cleanup PRs are merged and read current registry, guides and [gap list](ISSUES-AND-GAPS.md). Recheck external state rather than trusting this timestamp.
2. OUTPOST existing-PR install and branch rollback/restore passed in [OUTPOST #177](https://github.com/sunstriker2009/sun-outpost/pull/177), which was closed. [OUTPOST #178](https://github.com/sunstriker2009/sun-outpost/pull/178) merged the tested Foundry pin. The rollback pilot used the installer CLI on the draft branch.
3. Audit adopter pins and required-check dispatch coverage before proposing individual opt-in changes.
4. Review retained OUTPOST/WORKBENCH display/packaging/artwork names only where needed; do not globally replace namespaces or scan owner-wide.
5. Update roadmap and central handbook with verified results, keep quota discipline, and leave functional development/recurring product schedules paused until explicitly resumed.

This checkpoint does not authorize live rollback, another rename, new repositories, fleet-wide hook activation, archive deletion, identity changes or schedule resumption. Archiving the thread or clearing assistant memory does not alter repository state; these committed documents carry the handoff.
