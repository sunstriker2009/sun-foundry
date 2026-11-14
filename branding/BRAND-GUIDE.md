# FOUNDRY by Sun — Brand Guide

**Status:** Visual direction approved by owner; production asset adoption in progress  
**Approved concept:** Foundry F — second panoramic treatment (2026-11-13)  
**Tagline:** Build. Standardize. Launch.  
**Canonical SUN standard:** [Product Repository Branding Standard](https://github.com/sunstriker2009/sun-ecosystem/blob/main/docs/governance/PRODUCT-BRANDING.md)

## Approved visual direction

The approved concept is the **second treatment** of the modular F, **not** the earlier anvil concept and not an unrelated stock or search image. Its composition has a faceted gold/orange upper F and cyan/blue lower F, a luminous SUN sunrise arc with a starburst, a circular illuminated platform, and a deep navy panoramic background with sweeping blue trails. The right-hand lockup reads **FOUNDRY**, **by Sun**, and **Build. Standardize. Launch.**

The symbol expresses modular repository creation and standardization. The F is natural to the product name; the SUN arc links the product family. Do not replace this approved reference with a newly generated lookalike.

## Canonical symbol extraction policy

**Source of truth:** the exact owner-approved second-treatment panoramic PNG at `branding/assets/readme-banner-v1.png`. Preserve its original F and SUN arc (including the distinctive disconnected arms, glass-like luminosity, gradients and material). Do not recreate the high-resolution symbol from the compact SVG.

**Production sequence:** (1) archive the original approved concept unchanged when available; (2) obtain a layered/transparent source if possible, otherwise carefully isolate the F and arc from the committed banner; (3) export a transparent high-resolution standalone PNG with documented crop/mask and visual inspection; (4) derive raster app icons from that extraction, validating at 16–32 px; (5) retain the reviewed compact SVGs for scalable, monochrome and small-size needs.

A flattened banner may have baked-in navy background, glow and overlapping lighting. **An exact transparent cutout is not guaranteed** without layers; inspect edge halos and avoid claiming pixel-perfect isolation where manual masking is required. Do not replace the approved banner.

## Working palette and typography

| Role | Color | Value |
| --- | --- | --- |
| Background | Deep navy | `#081631` |
| Solar arc / upper F | Gold | `#FFB333` |
| Warm highlight | Copper orange | `#FF7D28` |
| Lower F | Cyan | `#12C8F4` |
| Lower shadow | Electric blue | `#1B66E8` |
| Text on dark | White | `#FFFFFF` |

These are **working vector approximation values**, not sampled or formally approved production color specifications. Use a bold geometric sans-serif; SVG lockups use broadly available Arial/Helvetica fallbacks pending a finalized family typeface.

## Asset manifest

| Asset | Purpose |
| --- | --- |
| `branding/archive/originals/readme-banner-v1.png` | Immutable copy of the approved original (identical to production banner); archival copy pending |
| `branding/assets/readme-banner-v1.png` | Approved panoramic README image, canonical raster source |
| `branding/assets/foundry-symbol-canonical-v2.png` | Approved canonical transparent symbol (legacy filename; standard: `symbol-canonical-v2.png`) |\n| `branding/assets/icons/foundry-icon-{size}.png` | Approved V3 icons (legacy filenames; standard: `icon-{size}.png`) |\n| `branding/reviews/CANONICAL-RASTER-ASSET-IMPORT.md` | Historical V3 import verification record |\n| `branding/archive/intermediate/small-icon-comparison.png` | V3 review sheet; move from `branding/assets/` pending |\n| `branding/assets/small-icon-master.svg` | Approved small-size vector master; retained as a production source |\n| `branding/assets/symbol-dark.svg` | Compact F symbol for dark UI |
| `branding/assets/symbol-light.svg` | Compact F symbol for light UI |
| `branding/assets/symbol-mono.svg` | Monochrome symbol |
| `branding/assets/symbol-small.svg` | Simplified small-size symbol |
| `branding/assets/lockup-dark.svg` | Full product lockup for dark UI |
| `branding/assets/lockup-light.svg` | Full product lockup for light UI |
| `branding/assets/lockup-mono.svg` | Monochrome full lockup |

The compact SVGs are **owner-reviewed vector adaptations** of the approved direction, with disconnected F arms and a thinner glass-like arc; they are not pixel-identical traces. High-resolution raster app icons must instead derive from the canonical artwork extraction. The owner-approved canonical v2 transparent symbol and V3 PNG icons (16–1024 px) are uploaded to the PR branch. The 16–48 px sizes are purpose-built optical adaptations; the 64–1024 px sizes derive from the canonical raster. See [raster import checklist](reviews/CANONICAL-RASTER-ASSET-IMPORT.md).

## Usage and revision rules

- Keep the original concept separately from production assets.
- Use the exact approved second-treatment panoramic image for the README, preserving aspect ratio and legibility.
- Use locally committed, versioned banner filenames for cache-safe replacement.
- Do not distort, recolor or substitute the approved identity without review.
- Update the asset manifest and README references together in a feature-branch PR.

## Adoption checklist

- [x] Concept direction reviewed and approved by owner.
- [x] SUN arc, purpose-led F and distinct warm/cool palette defined.
- [x] Initial compact SVG lockup and symbol variants prepared.
- [ ] Approved concept PNG committed unchanged under `branding/concepts/`.
- [x] Approved panoramic PNG committed as `branding/assets/readme-banner-v1.png`.
- [x] README updated to reference the approved panoramic PNG.
- [x] Revised compact SVG direction reviewed (disconnected F arms and glass-like arc).\n- [ ] Canonical F + arc extracted and inspected from the original approved artwork.\n- [ ] Raster app-icon exports produced from the canonical extraction.
- [ ] Final asset palette and typography approved.

## SUN naming and archival migration

Follow the [SUN Product Branding Standard](https://github.com/sunstriker2009/sun-ecosystem/blob/main/docs/governance/PRODUCT-BRANDING.md), section 5. Product identity belongs in the repository, not in every filename.

- **Approved original:** The owner confirmed the approved concept and the panoramic README image are **the same file**. Preserve an exact byte-for-byte copy of `branding/assets/readme-banner-v1.png` at `branding/archive/originals/readme-banner-v1.png`; never replace it with a recreated image.
- **Production assets:** Keep the README banner and canonical transparent symbol, icon PNGs and usable SVG masters under `branding/assets/`.
- **Intermediate work:** Move `branding/assets/small-icon-comparison.png` to `branding/archive/intermediate/small-icon-comparison.png`. Archive future reviews, extraction prototypes and rejected experiments in `branding/archive/`.
- **Legacy names:** The existing `foundry-symbol-canonical-v2.png` and `foundry-icon-{size}.png` remain supported. A later migration may rename them to `symbol-canonical-v2.png` and `icon-{size}.png` only after references are updated. No need to rename the already-standard `readme-banner-v1.png`.

### Remaining migration actions

- [ ] Copy approved banner to `branding/archive/originals/readme-banner-v1.png` with identical Git blob SHA.
- [ ] Move comparison sheet to `branding/archive/intermediate/small-icon-comparison.png` and update any references.
- [ ] Verify README banner path is unchanged and all production files remain intact.
