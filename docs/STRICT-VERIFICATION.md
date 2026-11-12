# Strict governance verification

Run `verify` against a disposable repository with **exact expected check names**:

```sh
dotnet run --project src/Sun.RepoBootstrap -- --mode verify --repo sunstriker2009/sun-repo-test --checks repository-validation,conventional-title
```

Verification must fail for missing/extra checks, inactive or wrongly scoped rulesets, bypass actors, missing required rules, disabled strict checks, unresolved review conversations, or repository merge/branch-cleanup setting drift.

**Important:** This verifies the GitHub `delete_branch_on_merge` setting, not whether GitHub actually deletes a merged branch.

## Post-merge deletion integration test

1. In `sun-repo-test`, create a disposable branch from `main` and commit a harmless documentation file.
2. Open a PR titled `test: verify automatic branch deletion`; wait for all required checks.
3. Squash-merge through GitHub without manually deleting the branch.
4. Check that GitHub automatically removes the source branch. Confirm via the branch list or a GitHub branch API lookup returning 404.
5. Record the result. If the branch remains, check repository settings and ruleset constraints; do not manually delete it until after the observation.

The integration test deliberately requires an actual merge and should not be executed on production repositories.

## Remaining limitations

This verifier checks the named SUN ruleset, not all possible inherited or additional rulesets. It does not enforce CODEOWNERS approvals (baseline policy currently requires zero reviews). Audit/Plan remain non-mutating summaries, not equivalent to strict Verify.
