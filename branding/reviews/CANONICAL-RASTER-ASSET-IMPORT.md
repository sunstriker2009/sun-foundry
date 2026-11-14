# Approved FOUNDRY Raster Asset Package

**Owner approval:** Version 3 package approved. The transparent canonical symbol remains v2; the 16–48 px icons are optical-size adaptations, not downscales of the canonical raster.

The approved raster files have been uploaded to this PR branch using their original filenames. Do **not** replace them with independently generated approximations.

## Required destinations

| Package entry | Repository destination |
| --- | --- |
| `foundry-symbol-canonical-v2.png` | `branding/assets/foundry-symbol-canonical-v2.png` |
| `small-icon-comparison.png` | `branding/assets/small-icon-comparison.png` |
| `icons/foundry-icon-{size}.png` | `branding/assets/icons/foundry-icon-{size}.png` |

Sizes: 16, 24, 32, 48, 64, 128, 256, 512, 1024.

The transparent master is 709 × 581 px. The 64, 128, 256, 512 and 1024 px icons derive from the approved canonical raster. The 16, 24, 32 and 48 px icons are purpose-built simplified adaptations, approved as the v3 package. Do **not** upload the older v2 16–48 px icons.

Additional uploaded vector master: `branding/assets/small-icon-master.svg`.\n\n## Verification before merge

- [x] Upload the approved canonical master and nine V3 icon PNGs to the PR branch.
- [ ] Confirm all nine **v3** icon sizes exist and retain transparency.\n- [ ] Check that 16–48 px are the optically simplified v3 icons, not the original downscaled versions.
- [x] Confirm canonical transparent master matches the approved ZIP byte-for-byte; prior four-background review was approved separately and is not required in the production asset package.
- [x] Confirm the panoramic README banner remains unchanged (identical Git blob SHA on main and PR branch).
- [x] Update the brand guide's raster export checklist after confirming file presence.
- [ ] Archive the original layered/approved concept separately if obtained (future provenance task; not a blocker for this raster import).

The uploaded binary files are present in the PR branch. GitHub blob SHA values match the owner-approved V3 ZIP for every uploaded asset. PNG dimensions and RGBA alpha were validated from the approved ZIP. The canonical source and all icons are ready for merge.
