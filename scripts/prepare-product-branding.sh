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
manifest=
manifest_sha=
if [[ -n "${APPROVED_MANIFEST:-}" ]]; then
  manifest=$(jq . <<< "$APPROVED_MANIFEST")
  manifest_sha=$(printf '%s\n' "$manifest" | git hash-object --stdin)
fi
sha=$(gh api "repos/$REPO/git/ref/heads/$BRANCH" --jq .object.sha)
readme=$(gh api -H "Accept: application/vnd.github.raw+json" "repos/$REPO/contents/README.md?ref=$BRANCH")
clean_readme=$(cat <<'EOF'
# SUN Product Repository

Product name, description and approved visual identity pending initialization.

This repository was provisioned from STRATA by Sun through FOUNDRY. It must not use STRATA's logo or tagline as its own brand.

See the [setup checklist](docs/REPOSITORY-SETUP.md) for product metadata and branding.
EOF
)
base_tree=$(gh api "repos/$REPO/git/commits/$sha" --jq .tree.sha)
tree=$(gh api "repos/$REPO/git/trees/$base_tree?recursive=1")
if ! jq -e '.truncated == false' <<< "$tree" >/dev/null; then
  echo "::error::Incomplete repository tree; refusing branding cleanup"
  exit 1
fi
if ! grep -q '^# STRATA by Sun$' <<< "$readme"; then
  if [[ "$readme" == "$clean_readme" ]]; then
    if jq -e --arg manifest_sha "$manifest_sha" 'any(.tree[];
      .path == "docs/TEMPLATE-GUIDE.md"
      or (.type != "tree" and (.path == "branding" or (.path | startswith("branding/")))
        and (.type != "blob" or .mode != "100644" or (
          (.path != "branding/revisions/.gitkeep" or .sha != "e69de29bb2d1d6434b8b29ae775ad8c2e48c5391")
          and (.path != "branding/manifest.json" or .sha != $manifest_sha))))
    )' <<< "$tree" >/dev/null; then
      echo "::error::Product README exists but cleaned STRATA template files remain; manual inspection required"
      exit 1
    fi
    if [[ -n "$manifest" ]]; then
      bash scripts/verify-approved-product-seed.sh "$REPO" "$sha"
    fi
    echo "Product-neutral README already initialized"
    exit 0
  fi
  [[ -z "$manifest" ]] || { echo "::error::Unexpected approved product seed baseline"; exit 1; }
  if grep -q '^# SUN Product Repository$' <<< "$readme"; then
    echo "Product README already initialized; checking remaining branding cleanup"
    # A prior attempt may have stopped after writing README but before removing
    # the STRATA template guide. Continue only with safe, explicit cleanup.
    if gh api "repos/$REPO/contents/branding/assets/readme-banner-v1.png?ref=$BRANCH" >/dev/null 2>&1; then
      echo "::error::Product README exists but STRATA banner remains; manual inspection required"
      exit 1
    fi
    if guide_sha=$(gh api "repos/$REPO/contents/docs/TEMPLATE-GUIDE.md?ref=$BRANCH" --jq .sha 2>/dev/null); then
      gh api -X DELETE "repos/$REPO/contents/docs/TEMPLATE-GUIDE.md" -f message="docs: remove STRATA template authoring guide" -f sha="$guide_sha" -f branch="$BRANCH" >/dev/null
    fi
    if ! gh api "repos/$REPO/contents/branding/BRAND-GUIDE.md?ref=$BRANCH" >/dev/null 2>&1; then
      echo "::error::Product README exists without brand guide; manual inspection required"
      exit 1
    fi
    echo "Product-neutral branding already initialized"
    exit 0
  fi
  echo "::error::README does not match STRATA template; refusing destructive cleanup"
  exit 1
fi
if jq -e 'any(.tree[]; .path == "branding/manifest.json" or .path == "branding/recycling")' <<< "$tree" >/dev/null; then
  # Review exact blobs for the cleaned STRATA template, including recycled material.
  clean_fingerprint='{
  "branding/assets/icons/icon-1024.png": "a502ccae1c5268eaf26afc792a7894e5b6426f21",
  "branding/assets/icons/icon-128.png": "779ec539db9cabf1c3bbbb08355392c1fa71759a",
  "branding/assets/icons/icon-16.png": "5b1c315b2694203afd233166750aca744f1c2c7b",
  "branding/assets/icons/icon-24.png": "9691cb5b31847443c60469acbd36b45e6cf5e2ff",
  "branding/assets/icons/icon-256.png": "cc71c20851669a72ce0aeb31c37ecdedfe08808b",
  "branding/assets/icons/icon-32.png": "854e0d998f4d55ad46daf87a7395f6cd086c625e",
  "branding/assets/icons/icon-48.png": "3bf2af1534d3ff52bf8d1b87d8af0daa39792f45",
  "branding/assets/icons/icon-512.png": "d44603ab15025f85d9f8f374262dd2148b5e87ee",
  "branding/assets/icons/icon-64.png": "8f001b6d5485e602acab4b2576d83fbed9978eea",
  "branding/assets/readme-banner.png": "c2b9bc2c6c6f47c893d113279c9dfed7fa3f5d2f",
  "branding/assets/symbol.png": "cd4f051c65f3a6e8915929a5f291954dd591aba2",
  "branding/manifest.json": "48d298a94fa6b0da053b9ba70a970b45c284697f",
  "branding/recycling/branding/BRAND-GUIDE.md": "03ff5795a2e104fee3d273578f96a14af580b808",
  "branding/recycling/branding/archive/README.md": "373abf3692a99321acca376b499f6d5658721bb1",
  "branding/recycling/branding/archive/concepts/concept-banner-v1.png": "a07559cb4394e12ca5055485b8f4382f4a877768",
  "branding/recycling/branding/archive/originals/readme-banner-v1.png": "c2b9bc2c6c6f47c893d113279c9dfed7fa3f5d2f",
  "branding/recycling/branding/archive/originals/symbol-reference-v1.png": "895d2df59291d4b9a84fbeda71c66d6ccd09d5bc",
  "branding/recycling/branding/assets/refs/lockup-dark.svg": "b316564654c88afefa648d10dae3d511a50749b2",
  "branding/recycling/branding/assets/refs/symbol-dark.svg": "a114ef82426fd69261302b9ba64b2ff4973f4be2",
  "branding/recycling/branding/assets/refs/symbol-light.svg": "bdb79aad023afb002fe73eebc6862c3a35decd70",
  "branding/recycling/branding/assets/refs/symbol-small.svg": "8f2f4f8db6edfc0eaef19523e4692fd862650d38",
  "branding/revisions/.gitkeep": "e69de29bb2d1d6434b8b29ae775ad8c2e48c5391"
}'
  if ! jq -e --argjson expected "$clean_fingerprint" --arg guide "b2f8d841571575bd731e10211070733a94bb7b43" '
    [.tree[] | select(.type != "tree" and (.path | startswith("branding/")))] as $branding
    | ($branding | all(.mode == "100644" and .type == "blob"))
    and (($branding | map({key: .path, value: .sha}) | from_entries) as $actual
      | ($actual == $expected or $actual == ($expected | with_entries(select(.key | startswith("branding/recycling/") | not)))))
    and any(.tree[]; .path == "docs/TEMPLATE-GUIDE.md" and .mode == "100644" and .sha == $guide)
  ' <<< "$tree" >/dev/null; then
    echo "::error::Cleaned STRATA template has unexpected or modified branding; refusing cleanup"
    exit 1
  fi
  # Publish the neutral README and remove reviewed template branding, retaining the empty revision marker.
  payload=$(jq -c --arg base "$base_tree" --arg readme "$clean_readme"$'\n' --arg manifest "$manifest" '
    {base_tree:$base, tree:([
      .tree[] | select(.type == "blob" and ((.path | startswith("branding/")) or .path == "docs/TEMPLATE-GUIDE.md")
        and .path != "branding/revisions/.gitkeep" and (.path != "branding/manifest.json" or $manifest == ""))
      | {path, mode, type, sha:null}
    ] + [{path:"README.md",mode:"100644",type:"blob",content:$readme}]
      + (if $manifest == "" then [] else [{path:"branding/manifest.json",mode:"100644",type:"blob",content:($manifest + "\n")}] end))}
  ' <<< "$tree")
  new_tree=$(gh api -X POST "repos/$REPO/git/trees" --input - --jq .sha <<< "$payload")
  new_commit=$(gh api -X POST "repos/$REPO/git/commits" -f message="chore: initialize product-neutral repository from STRATA" -f tree="$new_tree" -f parents[]="$sha" --jq .sha)
  gh api -X PATCH "repos/$REPO/git/refs/heads/$BRANCH" -f sha="$new_commit" -F force=false >/dev/null
  echo "Product-neutral README prepared; inherited STRATA branding removed on $BRANCH"
  exit 0
fi
[[ -z "$manifest" ]] || { echo "::error::Approved registrations require the current STRATA branding baseline"; exit 1; }
# Only delete exact known template-brand paths, not arbitrary product assets.
mapfile -t paths < <(jq -r '.tree[] | select(.type == "blob") | .path | select(startswith("branding/"))' <<< "$tree")
if (( ${#paths[@]} > 0 )); then
  if printf '%s\n' "${paths[@]}" | grep -Fxq branding/assets/readme-banner.png; then
    # Exact reviewed STRATA raster baseline; refuse changed or extra product files.
    template_fingerprint='{"branding/BRAND-GUIDE.md":"03ff5795a2e104fee3d273578f96a14af580b808","branding/archive/README.md":"373abf3692a99321acca376b499f6d5658721bb1","branding/archive/concepts/concept-banner-v1.png":"a07559cb4394e12ca5055485b8f4382f4a877768","branding/archive/originals/readme-banner-v1.png":"c2b9bc2c6c6f47c893d113279c9dfed7fa3f5d2f","branding/archive/originals/symbol-reference-v1.png":"895d2df59291d4b9a84fbeda71c66d6ccd09d5bc","branding/assets/icons/icon-1024.png":"a502ccae1c5268eaf26afc792a7894e5b6426f21","branding/assets/icons/icon-128.png":"779ec539db9cabf1c3bbbb08355392c1fa71759a","branding/assets/icons/icon-16.png":"5b1c315b2694203afd233166750aca744f1c2c7b","branding/assets/icons/icon-24.png":"9691cb5b31847443c60469acbd36b45e6cf5e2ff","branding/assets/icons/icon-256.png":"cc71c20851669a72ce0aeb31c37ecdedfe08808b","branding/assets/icons/icon-32.png":"854e0d998f4d55ad46daf87a7395f6cd086c625e","branding/assets/icons/icon-48.png":"3bf2af1534d3ff52bf8d1b87d8af0daa39792f45","branding/assets/icons/icon-512.png":"d44603ab15025f85d9f8f374262dd2148b5e87ee","branding/assets/icons/icon-64.png":"8f001b6d5485e602acab4b2576d83fbed9978eea","branding/assets/readme-banner.png":"c2b9bc2c6c6f47c893d113279c9dfed7fa3f5d2f","branding/assets/refs/lockup-dark.svg":"b316564654c88afefa648d10dae3d511a50749b2","branding/assets/refs/symbol-dark.svg":"a114ef82426fd69261302b9ba64b2ff4973f4be2","branding/assets/refs/symbol-light.svg":"bdb79aad023afb002fe73eebc6862c3a35decd70","branding/assets/refs/symbol-small.svg":"8f2f4f8db6edfc0eaef19523e4692fd862650d38","branding/assets/symbol.png":"cd4f051c65f3a6e8915929a5f291954dd591aba2","branding/revisions/.gitkeep":"e69de29bb2d1d6434b8b29ae775ad8c2e48c5391"}'
    for path in "${paths[@]}"; do
      actual=$(jq -r --arg path "$path" '.tree[] | select(.path == $path) | .sha' <<< "$tree")
      expected=$(jq -r --arg path "$path" '.[$path] // empty' <<< "$template_fingerprint")
      [[ -n "$expected" && "$actual" == "$expected" ]] || { echo "::error::Unexpected or modified branding file $path; refusing cleanup"; exit 1; }
    done
  else
  allowed=(branding/BRAND-GUIDE.md branding/archive/README.md branding/archive/concepts/concept-banner-v1.png branding/archive/originals/readme-banner-v1.png branding/archive/originals/symbol-reference-v1.png branding/assets/lockup-dark.svg branding/assets/readme-banner-v1.png branding/assets/symbol-dark.svg branding/assets/symbol-light.svg branding/assets/symbol-small.svg)
  for path in "${paths[@]}"; do
    printf '%s\n' "${allowed[@]}" | grep -Fxq "$path" || { echo "::error::Unexpected branding file $path; refusing to remove potentially approved product artwork"; exit 1; }
  done
  for required in branding/BRAND-GUIDE.md branding/assets/readme-banner-v1.png; do
    printf '%s\n' "${paths[@]}" | grep -Fxq "$required" || { echo "::error::Missing STRATA branding fingerprint: $required"; exit 1; }
  done
  fi
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

- Confirm the product name, tagline and SUN product ID in the Foundry registry.
- Obtain owner-approved panoramic artwork; save as `branding/assets/readme-banner.png`.
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
