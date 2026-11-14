# Approved FOUNDRY Raster Asset Package

**Owner approval:** canonical transparent symbol v2 approved on 2026-11-13.

The approved raster files are packaged externally for upload to this PR branch. Do **not** replace them with independently generated approximations.

## Required destinations

| Package entry | Repository destination |
| --- | --- |
| `foundry-symbol-canonical-v2.png` | `branding/assets/foundry-symbol-canonical-v2.png` |
| `background-review.png` | `branding/reviews/foundry-symbol-background-review-v2.png` |
| `icons/foundry-icon-{size}.png` | `branding/assets/icons/png/foundry-icon-{size}.png` |

Sizes: 16, 24, 32, 48, 64, 128, 256, 512, 1024.

The transparent master is 709 × 581 px. All icons were derived from that master. For tiny interface sizes, prefer the existing compact SVG where it renders more clearly.

## Verification before merge

- [ ] Upload the **exact binary files** from the approved ZIP to the paths above on this PR branch.
- [ ] Confirm all nine icon sizes exist and retain transparency.
- [ ] Compare the transparent master with the approved four-background review.
- [ ] Confirm the panoramic README banner remains unchanged.
- [ ] Update the brand guide's raster export checklist only after the files are present.
- [ ] Archive the original layered/approved concept separately if obtained; the standalone extraction is **not** a substitute for that original.

The connector's text-file API cannot accept local binary attachments directly; this PR intentionally does not claim that the raster files are committed yet.
