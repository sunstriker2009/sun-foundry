#!/usr/bin/env bash
# Create or update a pending SUN ecosystem registration PR.
set -euo pipefail
: "${GH_TOKEN:?SUN_REPO_ADMIN_TOKEN required}"
TARGET="${TARGET:?TARGET required}"
CONFIRM="${CONFIRM:?CONFIRM required}"
[[ "$TARGET" == "$CONFIRM" ]] || { echo "::error::Repository confirmation mismatch"; exit 1; }
[[ "$TARGET" =~ ^sunstriker2009/[a-z0-9][a-z0-9._-]*$ ]] || { echo "::error::Invalid SUN repository"; exit 1; }
[[ "$TARGET" != sunstriker2009/sun-ecosystem ]] || { echo "::error::Ecosystem is its own registry authority"; exit 1; }
MODE="${MODE:-preview}"
[[ "$MODE" == preview || "$MODE" == apply ]] || exit 1
gh api "repos/$TARGET" --jq '.full_name' | grep -Fx "$TARGET" >/dev/null
ECO=sunstriker2009/sun-ecosystem
# No implicit identity assignment: only a new, unconfirmed repository is eligible.
slug="${TARGET#*/}"
branch="chore/register-$slug"
tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT
gh api "repos/$ECO/contents/registry/repositories.json" -H 'Accept: application/vnd.github.raw+json' > "$tmp/catalog.json"
gh api "repos/$ECO/contents/registry/products.json" -H 'Accept: application/vnd.github.raw+json' > "$tmp/authority.json"
python3 - "$tmp/catalog.json" "$tmp/authority.json" "$TARGET" "$tmp/next.json" <<'PY'
import json,sys
catalog,authority,target,out=sys.argv[1:]
c=json.load(open(catalog)); a=json.load(open(authority))
if c.get("schemaVersion") != 1: raise SystemExit("Unsupported registry schema")
if any(row["repository"] == target for row in c["repositories"]):
    print("Already registered: no changes")
    open(out,"w").write("")
    raise SystemExit(0)
slug=target.split("/")[1]
if any(row.get("repository")==slug for group in ("products","infrastructure") for row in a[group]):
    raise SystemExit("Repository already has an approved SUN identity; reconcile manually, do not create pending duplicate")
c["repositories"].append({"repository":target,"registryId":None,"classification":"pending","name":slug,"summary":"Repository registration pending owner review","icon":None,"iconSha256":None})
with open(out,"w") as f: json.dump(c,f,indent=2); f.write("\n")
PY
if [[ ! -s "$tmp/next.json" ]]; then
  echo "Repository already registered; no PR required" >> "$GITHUB_STEP_SUMMARY"
  exit 0
fi
echo "Pending registration proposed for $TARGET" >> "$GITHUB_STEP_SUMMARY"
if [[ "$MODE" == preview ]]; then
  echo "Preview only: no branch or PR created" >> "$GITHUB_STEP_SUMMARY"
  exit 0
fi
# Work from an isolated checkout. Never push to protected main.
git -c http.extraheader="AUTHORIZATION: basic $(printf 'x-access-token:%s' "$GH_TOKEN" | base64 -w0)" clone --quiet "https://github.com/$ECO.git" "$tmp/ecosystem"
cd "$tmp/ecosystem"
if git ls-remote --exit-code --heads origin "$branch" >/dev/null 2>&1; then
  echo "::error::Existing registration branch $branch; inspect its PR and resolve manually"
  exit 1
fi
git checkout -q -b "$branch"
cp "$tmp/next.json" registry/repositories.json
python3 scripts/render-repository-gallery.py
git add registry/repositories.json README.md
git -c user.name='sun-foundry[bot]' -c user.email='41898282+github-actions[bot]@users.noreply.github.com' commit -qm "chore(registry): propose $slug registration"
git -c http.extraheader="AUTHORIZATION: basic $(printf 'x-access-token:%s' "$GH_TOKEN" | base64 -w0)" push --quiet -u origin "$branch"
pr=$(gh api "repos/$ECO/pulls?state=open&head=sunstriker2009:$branch" --jq '.[0].number // empty')
if [[ -z "$pr" ]]; then
  pr=$(gh api -X POST "repos/$ECO/pulls" -f head="$branch" -f base=main -f title="chore(registry): propose $slug registration" -f body="FOUNDRY pending-only repository registration for $TARGET. Review repository identity and classification before confirming. No SUN ID is assigned. Do not auto-merge this identity-registration PR." --jq .number)
fi
echo "Registration PR: https://github.com/$ECO/pull/$pr" >> "$GITHUB_STEP_SUMMARY"
