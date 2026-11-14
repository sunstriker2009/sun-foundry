# SUN product branding adoption checklist

Use this checklist when migrating ASTELVO, ORYVA or any SUN product to the [SUN branding standard](https://github.com/sunstriker2009/sun-ecosystem/blob/main/docs/governance/PRODUCT-BRANDING.md). FOUNDRY is the reference for **file organization and process**, not for other products' imagery or palette.

## 1. Identify approved sources

- [ ] Confirm the owner-approved artwork and any layered or transparent masters; do not regenerate or substitute it.
- [ ] Record product purpose, SUN arc, optional initial-letter motif, approved tagline and distinct palette.
- [ ] Determine whether the original concept and live README banner are identical. Archive an exact copy only when they are the same.
- [ ] Record any unavailable originals or provisional palette/typography values honestly.

## 2. Normalize production assets

- [ ] Keep the active panoramic image at `branding/assets/readme-banner-v1.png` (increment version on replacement).
- [ ] Place transparent master at `branding/assets/symbol-canonical-vN.png`.
- [ ] Place reviewed optical-size vector master at `branding/assets/symbol-small-master.svg`, if applicable.
- [ ] Use `branding/assets/icons/icon-{size}.png` for reviewed PNG sizes; do not assume all sizes are downscales.
- [ ] Keep approved `symbol-*.svg` and `lockup-*.svg` variants in `branding/assets/`.
- [ ] Remove product-name prefixes from generic asset filenames, updating all consumers in the same PR.

## 3. Separate history

- [ ] Preserve original artwork under `branding/archive/originals/` with Git blob SHA comparison.
- [ ] Move nonproduction comparisons and experiments to `branding/archive/intermediate/` or `concepts/`.
- [ ] Retire superseded artwork under `branding/archive/retired/` only if historically useful; otherwise rely on Git history.
- [ ] Remove obsolete artwork from the repository root and production directories.
- [ ] Maintain `branding/archive/README.md` and old-to-new mappings when migrating filenames.

## 4. Verify and deliver

- [ ] Verify each destination path and blob SHA; check PNG dimensions/transparency and optical readability where applicable.
- [ ] Confirm README links and all live code/documentation references resolve after renames.
- [ ] Keep the production README banner unchanged unless its replacement is explicitly approved.
- [ ] Update `branding/BRAND-GUIDE.md` manifest, approval status, provenance and outstanding design work.
- [ ] Open a feature-branch PR; run required CI once after batching changes, then squash merge.

## FOUNDRY baseline (verified)

- Banner and exact archived original: `dbfba49871e4a27b7d72dfd62fd026973cec3be5`.
- Canonical transparent V2 symbol: `branding/assets/symbol-canonical-v2.png`.
- V3 PNG icons: 16, 24, 32, 48, 64, 128, 256, 512, 1024.
- Optical vector master: `branding/assets/symbol-small-master.svg`.
- Retired older app icon: `branding/archive/retired/app-icon.svg`.
- **Still provisional:** formally approved palette color values and family typography.
