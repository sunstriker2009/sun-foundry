# FOUNDRY governance handoff

Snapshot: 2026-11-15 (America/Toronto), before SUN governance thread archival and memory cleanup.

## Scope and evidence

FOUNDRY is SUN-G003, the repository factory and shared automation implementation; STRATA supplies templates and SUN Ecosystem owns policy/registry. Reviewed main: `952ab4ada17510ac60944891996d0e578da80ccd`.

Start with [roadmap](ROADMAP.md), [workflow operations](WORKFLOWS.md), [branding installer](BRANDING-ZIP-INSTALLER.md), [fleet audit](GOVERNANCE-FLEET-AUDIT.md), [alignment](GOVERNANCE-ALIGNMENT.md), and the [central handbook](https://github.com/sunstriker2009/sun-ecosystem/blob/main/docs/workflows/README.md).

- Factory v1, recovery/maintenance, raster preparation, registration and canonical-symbol synchronization are implemented. Existing documentation records the controlled public-repository factory test and its limits.
- Five-repository governance alignment and final audit were reported successful by the operator. This review did not rerun an administrative audit or independently inspect all live rulesets. Preserve that evidence distinction.
- [FOUNDRY #62](https://github.com/sunstriker2009/sun-foundry/pull/62) merged the reversible ZIP installer; [#63](https://github.com/sunstriker2009/sun-foundry/pull/63) merged the same-branch action.
- [ASTELVO #39](https://github.com/sunstriker2009/sun-workbench/pull/39) is merged. Current main contains the opt-in hook, `branding/revisions/v1.zip`, `v2.zip` and `current.json` recording installation from `workbench-w2-assets-v1.zip`. The hook pins FOUNDRY commit `c1680fc22fb35f9542b65dfb1b79449c0970a154`. The prior operator handoff reports successful follow-up installation and uploaded-symbol verification; this review independently checked the merged PR, workflow and revision metadata, not a new byte comparison or installation run.
- Live rollback remains unverified. No hook is present in the reviewed Foundry, STRATA or ecosystem trees. Do not describe broader adoption as complete.

## Durable installer decisions

Upload one unnumbered package to `branding/revisions/` on an opted-in feature branch. Successful installation makes a follow-up commit there; the initial backup is `v1.zip`, then installed snapshots are `v2.zip`, `v3.zip`, etc., regardless of the upload's original name. Numbered revisions are immutable complete asset-tree snapshots, not byte-identical renamed uploads. Invalid uploads consume no version; identical uploads remain unchanged. Main changes only through its PR.

Keep PNG banner/symbol/icons consistent with approved artwork. The installer does not rename the product, update README wording, app copies or generator configuration. Existing `branding/archive/` remains intact; replacing it with revisions is an intended future migration, not completed cleanup. Protect source provenance and historical non-asset material before any removal.

The hook uses repository GITHUB_TOKEN and explicitly dispatches required validations for an already-open PR because token commits suppress normal workflow events. Check the final branch tip and CI before merging. Manual Preview/Apply/rollback uses the protected administration environment; see the installer guide for exact inputs and recovery.

## Next work, when explicitly resumed

1. Inspect current PRs/runs and ASTELVO's current revision state. If a failure is reported, inspect branch and commit evidence before retrying; an accepted push can coexist with a failed network response.
2. Select and authorize a live rollback pilot; preview a chosen snapshot, review the restore PR, run required checks and visually inspect before squash merge. Record PR/run/commit evidence afterward. Do not perform it during this documentation handoff.
3. Review opt-in separately for each additional repository, pin a reviewed action commit and ensure dispatched CI/title workflows validate the same rules. Do not enable it fleet-wide implicitly.
4. Plan legacy archive migration separately. Preserve original artwork, concepts and provenance that asset snapshots do not cover.

## Open boundaries

Unsupported private-plan enforcement must fail closed; never silently change visibility. Stronger approval counts must be preserved even if a strict baseline verifier flags them. Alignment uses explicitly mapped existing ruleset IDs, reviewed Plan artifact and current-state checks; plans expire after seven days. There is no scheduled fleet mutation. Existing daily symbol reconciliation is distinct from manual fleet governance.

ASTELVO development has a merged paused-work handoff in [#40](https://github.com/sunstriker2009/sun-workbench/pull/40); consult its current documentation and do not resume product work from this governance note. Workbench-named artwork does not by itself establish a registry/repository rename; naming reconciliation needs explicit owner direction.

## Resume rules

Read current repository documentation and live GitHub state before acting; this snapshot is not a standing authorization to resume implementation or administrative changes. Preserve explicit pauses. Use feature branches and PRs, required checks, applicable human review and squash merges; never push directly to protected main or weaken protection to make a verifier pass. Batch related fixes, avoid duplicate CI and unnecessary reruns, and stay within the owner's free GitHub Actions budget. Never store tokens in documentation.

Before continuing, inspect open PRs, branch tips and latest workflow results. Distinguish implementation, operator-reported live validation and independently verified evidence. Re-run read-only checks when needed; do not infer current compliance from an old green report. Do not create disposable repositories, change settings, roll out hooks, migrate archives or resume paused product work just because it appears in a next-step list.
