#!/usr/bin/env bash
# Merge only the proposed head from an owner-approved registration dispatch.
set -euo pipefail

[[ "$GITHUB_REPOSITORY" == sunstriker2009/sun-foundry ]]
[[ "$REGISTRATION_PR" =~ ^[1-9][0-9]*$ ]]
[[ "$REGISTRATION_HEAD" =~ ^[0-9a-f]{40}$ ]]
[[ "$REGISTRATION_BRANCH" =~ ^chore/propose-product-SUN-[PC][0-9]{3}-sun-[a-z0-9]+(-[a-z0-9]+)*$ ]]
if [[ "$(gh api user --jq .login)" != sunstriker2009 ]]; then
  echo "::error::The registration PR is open. Automatic merge requires the Foundry owner's credential."
  exit 1
fi

pull_path="repos/$GITHUB_REPOSITORY/pulls/$REGISTRATION_PR"
pr_url="https://github.com/$GITHUB_REPOSITORY/pull/$REGISTRATION_PR"
for attempt in {1..60}; do
  pull=$(gh api "$pull_path")
  if ! jq -e --arg repo "$GITHUB_REPOSITORY" --arg head "$REGISTRATION_HEAD" --arg branch "$REGISTRATION_BRANCH" '
      .base.ref == "main" and .base.repo.full_name == $repo and .head.repo.full_name == $repo and
      .head.ref == $branch and .head.sha == $head
    ' <<< "$pull" >/dev/null; then
    echo "::error::The registration PR no longer matches the owner-approved proposal."
    exit 1
  fi
  if jq -e '.merged == true and .merged_by.login == "sunstriker2009"' <<< "$pull" >/dev/null; then
    printf '[Registration PR](%s) was already squash-merged by the owner.\n' "$pr_url" >> "$GITHUB_STEP_SUMMARY"
    exit 0
  fi
  if ! jq -e '.state == "open" and .draft == false' <<< "$pull" >/dev/null; then
    echo "::error::The registration PR is closed or in draft."
    exit 1
  fi

  merge_state=$(jq -r '.mergeable_state' <<< "$pull")
  if [[ "$merge_state" == behind || "$merge_state" == dirty ]]; then
    echo "::error::The proposal is stale or conflicts with main. Review the PR and rerun registration if its identity changed."
    exit 1
  fi
  build=$(gh api "repos/$GITHUB_REPOSITORY/commits/$REGISTRATION_HEAD/check-runs" --method GET -f check_name=build \
    --jq '[.check_runs[] | select(.app.slug == "github-actions")] | .[0].conclusion // ""')
  if [[ -n "$build" && "$build" != success ]]; then
    echo "::error::The required build check finished with $build. The registration PR is open."
    exit 1
  fi
  if [[ "$build" == success && ( "$merge_state" == clean || "$merge_state" == unstable ) ]]; then
    result=$(gh api -X PUT "$pull_path/merge" -f sha="$REGISTRATION_HEAD" -f merge_method=squash)
    jq -e '.merged == true' <<< "$result" >/dev/null
    printf '[Registration PR](%s) squash-merged. Repository Factory is triggered by the merge.\n' \
      "$pr_url" >> "$GITHUB_STEP_SUMMARY"
    exit 0
  fi
  sleep 5
done

echo "::error::Timed out waiting for required checks and merge readiness. The registration PR is open."
exit 1
