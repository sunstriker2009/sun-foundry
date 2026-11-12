# Approval and waiting-run troubleshooting

The workflow's `apply` job uses the protected `repository-administration` environment. A waiting job can be an approval gate, deployment-branch restriction, or runner availability issue. GitHub may show only "Waiting" in some views.

## Diagnose

1. Open the manual workflow run and check whether `validate-dispatch` passed.
2. Check the `provision` job for environment approval requests; use the desktop GitHub Actions UI.
3. Check repository Settings → Environments → `repository-administration`: reviewers, self-review policy, branch restrictions, wait timer.
4. Check repository Actions settings and available runners.
5. Avoid launching duplicate Apply runs. Cancel obsolete waiting runs only after confirming they are not running.

**Never remove required reviewers merely to make Apply start.**

## Local manual fallback (no GitHub environment approval involved)

If GitHub's deployment approval UI remains blocked, execute the CLI **locally**, only after reviewing the plan and token permissions. Local execution is a distinct manual authorization path, not a workaround that silently weakens GitHub environment controls.

1. Install .NET 10 SDK and clone `sun-repo-bootstrap` after merging the fix.
2. Create a fine-grained token scoped **only** to `sun-repo-test` with repository Administration write and Checks read. Keep it in your shell environment as `GH_TOKEN` (do not paste into logs, files, or chat).
3. Run `dotnet run --project src/Sun.RepoBootstrap -- --repo sunstriker2009/sun-repo-test --mode plan`.
4. Ensure CI has run on main and on an open PR. For the generated template, check names are `repository-validation,conventional-title`.
5. Explicitly approve the changes yourself and run:

```sh
dotnet run --project src/Sun.RepoBootstrap -- --repo sunstriker2009/sun-repo-test --mode apply --checks repository-validation,conventional-title --confirm sunstriker2009/sun-repo-test
```

6. Run `--mode verify` and inspect repository rulesets manually. The first implementation does not yet prove full governance compliance.

Do not run Apply on production repositories until a disposable repository has passed positive and negative protection tests.
