# SUN governance fleet audit

The manual **SUN Governance Fleet Audit** workflow runs the existing .NET strict verifier in `verify` mode for the explicit allowlist in `config/governance-fleet.json`. Two repositories run concurrently, each with a 120-second limit. All targets are reported even when one fails. The allowlist is capped at 20; repository selection and exact expected check names change through PR review, never automatic discovery.

The runner cannot select Apply or an arbitrary command. It does not create repositories, change settings, add protection, request merges, or invoke the provisioning workflow. No schedule is installed.

## Setup and use

1. Review the allowlist and expected checks in this PR. These are expected policy, not certification of current protection. ORYVA includes the existing `backend`, `frontend`, and `reservation` contexts. FOUNDRY expects `build`; STRATA and ASTELVO expect `repository-validation` and `conventional-title`.
2. SUN Ecosystem expects `gallery`. Merge its paired workflow change first: the existing job must run without path filters on every PR and on `main` pushes. Confirm a green run before using alignment to require it.
3. Use FOUNDRY's existing `repository-administration` environment and `SUN_REPO_ADMIN_TOKEN`. The token must have access to the allowlisted repositories and their governance metadata. No separate environment or audit token is required. Keep the existing `main` restriction and approval gates. The runner remains fixed to read-only `verify` mode even though the shared credential also supports administrative workflows.
4. Run **SUN Governance Fleet Audit** on `main`. The workflow is owner-only and manual-only.
5. Inspect the job summary and download `governance-fleet-report` for `report.json` and `summary.md`. Artifacts expire after seven days. Resolve findings through separately reviewed changes.

## Results and limitations

| Result | Meaning |
| --- | --- |
| `compliant` | Strict verifier succeeded and emitted its positive verification result. |
| `drift` | Verifier reported a policy mismatch. |
| `unavailable` | Verifier explicitly detected private-repository plan limitations. Never considered compliance. |
| `not_configured` | Exact expected check policy is missing; verifier was not run for this target. |
| `error` | Access, API, runtime, unexpected failure or timeout prevented verification. |

Exit 0 means every target was compliant; exit 2 means at least one target was not. A red workflow with a complete report can represent valid drift detection rather than a broken audit. Missing credentials or build failure prevents a live audit and must not be represented as a fleet pass.

This reuses the current strict named `SUN Main Protection` baseline: merge settings, active main-only ruleset, no bypass actors, PR protection and exact required-check membership. A differently named ruleset is drift against this baseline, even if it provides some effective protection. Results are not a complete audit of overlapping/inherited rules, branch-protection APIs, CODEOWNERS, stronger review profiles, secrets, environments, vulnerabilities or actual failed-CI merge behavior. No governance controls are weakened automatically. Reports contain repository identifiers and verifier evidence; do not publish private-repository reports publicly.

## Local verification

```sh
python3 -m unittest discover -s tests -p 'test_governance_fleet.py' -v
dotnet build src/Sun.RepoBootstrap/Sun.RepoBootstrap.csproj --configuration Release
# Set GH_TOKEN securely in your environment first.
python3 scripts/audit-governance-fleet.py --workers 2
```

Tests mock the verifier process; they check result classification, private-plan limits, error isolation, fixed verify-only invocation, allowlist validation and credential redaction. A real fleet report remains a post-merge operator validation gate. Scheduling remains deferred until results and Actions cost are reviewed.
