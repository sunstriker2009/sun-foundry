#!/usr/bin/env bash
# Check the approved identity and empty revision marker at a specific target ref.
set -euo pipefail
repo="${1:?owner/repository required}"
ref="${2:?ref required}"
: "${APPROVED_MANIFEST:?approved manifest required}"
manifest=$(gh api -H 'Accept: application/vnd.github.raw+json' \
  "repos/$repo/contents/branding/manifest.json" --method GET -f ref="$ref")
jq -e --argjson expected "$APPROVED_MANIFEST" '. == $expected' <<< "$manifest" >/dev/null
marker=$(gh api "repos/$repo/contents/branding/revisions/.gitkeep" --method GET -f ref="$ref" --jq .sha)
[[ "$marker" == e69de29bb2d1d6434b8b29ae775ad8c2e48c5391 ]]
