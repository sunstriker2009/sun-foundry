#!/usr/bin/env bash
# Prepare a STRATA-generated repository for product-specific branding.
# Run only against the governance seed branch, never main.
set -euo pipefail
REPO="${1:?owner/repository required}"
BRANCH="${2:-chore/sun-governance-ci-seed}"
[[ "$REPO" =~ ^sunstriker2009/[A-Za-z0-9._-]+$ ]] || exit 1
[[ "$BRANCH" == chore/sun-governance-ci-seed ]] || { echo "::error::Refusing non-seed branch"; exit 1; }
[[ "$REPO" != sunstriker2009/sun-strata ]] || exit 1
: "${GH_TOKEN:?GH_TOKEN required}"
sha=$(gh api "repos/$REPO/git/ref/heads/$BRANCH" --jq .object.sha)
readme=$(gh api -H "Accept: application/vnd.github.raw+json" "repos/$REPO/contents/README.md?ref=$BRANCH")
if ! grep -q '^# STRATA by Sun$' <<< "$readme"; then
  if grep -q '^# SUN Product Repository$' <<< "$readme"; then
    echo "Product README already initialized; leaving branding unchanged"
    exit 0
  fi
  echo "::error::README does not match STRATA template; refusing destructive cleanup"
  exit 1
fi
# Only delete exact known template-brand paths, not arbitrary product assets.
base_tree=$(gh api "repos/$REPO/git/commits/$sha" --jq .tree.sha)
tree=$(gh api "repos/$REPO/git/trees/$base_tree?recursive=1")
mapfile -t paths < <(jq -r '.tree[] | select(.type == "blob") | .path | select(startswith("branding/"))' <<< "$tree")
if (( ${#paths[@]} > 0 )); then
  allowed=(branding/BRAND-GUIDE.md branding/archive/README.md branding/archive/concepts/concept-banner-v1.png branding/archive/originals/readme-banner-v1.png branding/archive/originals/symbol-reference-v1.png branding/assets/lockup-dark.svg branding/assets/readme-banner-v1.png branding/assets/symbol-dark.svg branding/assets/symbol-light.svg branding/assets/symbol-small.svg)
  for path in "${paths[@]}"; do
    printf '%s\n' "${allowed[@]}" | grep -Fxq "$path" || { echo "::error::Unexpected branding file $path; refusing to remove potentially approved product artwork"; exit 1; }
  done
  for required in branding/BRAND-GUIDE.md branding/assets/readme-banner-v1.png; do
    printf '%s\n' "${paths[@]}" | grep -Fxq "$required" || { echo "::error::Missing STRATA branding fingerprint: $required"; exit 1; }
  done
  payload=$(printf '%s\n' "${paths[@]}" | jq -R '{path:.,mode:"100644",type:"blob",sha:null}' | jq -sc --arg base "$base_tree" '{base_tree:$base,tree:.}')
  new_tree=$(gh api -X POST "repos/$REPO/git/trees" --input - --jq .sha <<< "$payload")
  new_commit=$(gh api -X POST "repos/$REPO/git/commits" -f message="chore: remove inherited STRATA artwork" -f tree="$new_tree" -f parents[]="$sha" --jq .sha)
  gh api -X PATCH "repos/$REPO/git/refs/heads/$BRANCH" -f sha="$new_commit" -F force=false >/dev/null
else
  echo "STRATA branding already removed; resuming product-neutral initialization"
fi
# Product-neutral placeholder and setup checklist; actual artwork requires owner approval.
readme_text=$(cat <<'EOF'
# SUN Product Repository

Product name, description and approved visual identity pending initialization.

This repository was provisioned from STRATA by Sun through FOUNDRY. It must not use STRATA's logo or tagline as its own brand.

See [product branding guide](branding/BRAND-GUIDE.md) and [setup checklist](docs/REPOSITORY-SETUP.md).
EOF
)
guide_text=$(cat <<'EOF'
# Product Brand Guide — Pending Approval

This is a product-neutral scaffold, **not** an approved visual identity.

- Confirm the product name, tagline and SUN product ID in the ecosystem registry.
- Obtain owner-approved panoramic artwork; save as `branding/assets/readme-banner-v1.png`.
- Keep byte-identical approved originals under `branding/archive/originals/`.
- Prepare compact symbol/lockup/icon exports in appropriate SVG/PNG variants.
- Document provenance and palette; never reuse STRATA artwork as the new product's identity.

Reference: https://github.com/sunstriker2009/sun-ecosystem/blob/main/docs/governance/PRODUCT-BRANDING.md
EOF
)
for entry in "README.md" "branding/BRAND-GUIDE.md"; do
  if [[ "$entry" == README.md ]]; then data="$readme_text"; else data="$guide_text"; fi
  encoded=$(printf '%s' "$data" | base64 -w0)
  existing_sha=$(gh api "repos/$REPO/contents/$entry?ref=$BRANCH" --jq .sha 2>/dev/null || true)
  if [[ -n "$existing_sha" ]]; then
    gh api -X PUT "repos/$REPO/contents/$entry" -f message="docs: initialize product-neutral branding" -f content="$encoded" -f branch="$BRANCH" -f sha="$existing_sha" >/dev/null
  else
    gh api -X PUT "repos/$REPO/contents/$entry" -f message="docs: initialize product-neutral branding" -f content="$encoded" -f branch="$BRANCH" >/dev/null
  fi
done
# Remove STRATA-specific usage guide copied from the template.
if guide_sha=$(gh api "repos/$REPO/contents/docs/TEMPLATE-GUIDE.md?ref=$BRANCH" --jq .sha 2>/dev/null); then
  gh api -X DELETE "repos/$REPO/contents/docs/TEMPLATE-GUIDE.md" -f message="docs: remove STRATA template authoring guide" -f sha="$guide_sha" -f branch="$BRANCH" >/dev/null
fi
echo "Product-neutral README and brand guide prepared; inherited STRATA assets removed on $BRANCH"
