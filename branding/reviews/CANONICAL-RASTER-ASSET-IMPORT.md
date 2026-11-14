# Approved FOUNDRY Raster Asset Package

**Owner approval:** Version 3 package approved. The transparent canonical symbol remains v2; the 16–48 px icons are optical-size adaptations, not downscales of the canonical raster.

The V3 raster files were approved and imported in PR #26. This file is a historical import record; current canonical locations are documented in the brand guide and migration notes. Do **not** replace them with independently generated approximations.

## Original import destinations (historical)

| Package entry | Repository destination |
| --- | --- |
| `foundry-symbol-canonical-v2.png` | `branding/assets/foundry-symbol-canonical-v2.png` |
| `small-icon-comparison.png` | `branding/assets/small-icon-comparison.png` |
| `icons/foundry-icon-{size}.png` | `branding/assets/icons/foundry-icon-{size}.png` |

Sizes: 16, 24, 32, 48, 64, 128, 256, 512, 1024.

The transparent master is 709 × 581 px. The 64, 128, 256, 512 and 1024 px icons derive from the approved canonical raster. The 16, 24, 32 and 48 px icons are purpose-built simplified adaptations, approved as the v3 package. Do **not** upload the older v2 16–48 px icons.

Additional uploaded vector master: `branding/assets/small-icon-master.svg`.

## Verification before merge

- [x] Upload the approved canonical master and nine V3 icon PNGs to the PR branch.
- [x] Confirm all nine **v3** icon sizes exist and retain transparency (approved ZIP dimensions and RGBA alpha validated; canonical destination hashes verified).
- [x] Confirm approved 16–48 px optical V3 variants match the owner-approved package byte-for-byte.
- [x] Confirm canonical transparent master matches the approved ZIP byte-for-byte; prior four-background review was approved separately and is not required in the production asset package.
- [x] Confirm the panoramic README banner remains unchanged (identical Git blob SHA on main and PR branch).
- [x] Update the brand guide's raster export checklist after confirming file presence.
- [x] Archive the owner-approved original artwork as an exact copy of the README banner (owner confirmed they are the same image); no separate layered source was supplied.

The approved binaries were imported in PR #26 and subsequently migrated to generic production filenames. GitHub blob SHA values match the owner-approved V3 ZIP for every uploaded asset. PNG dimensions and RGBA alpha were validated from the approved ZIP. The canonical source and all icons are ready for merge.

## Post-import verification (after PRs #28 and #29)

Current paths: `branding/assets/symbol-canonical-v2.png`, `branding/assets/symbol-small-master.svg`, and `branding/assets/icons/icon-{size}.png`. The comparison sheet is at `branding/archive/intermediate/small-icon-comparison.png`. The retired SVG app icon is at `branding/archive/retired/app-icon.svg` and is not the V3 icon source. All production destinations and archived original were rechecked on `main` with GitHub blob SHAs. The original and active banner both have SHA `dbfba49871e4a27b7d72dfd62fd026973cec3be5`.
