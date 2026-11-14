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
| `branding/concepts/foundry-f-treatment-02.png` | Owner-approved original concept, to be preserved unchanged |
| `branding/assets/readme-banner-v1.png` | Approved panoramic README image, canonical raster source |
| `branding/assets/foundry-symbol-canonical-v2.png` | Owner-approved transparent extraction; committed on PR #26 branch |\n| `branding/assets/icons/foundry-icon-{size}.png` | Nine approved V3 raster icon sizes, committed on PR #26 branch |\n| `branding/reviews/CANONICAL-RASTER-ASSET-IMPORT.md` | Exact package import and verification checklist |\n| `branding/assets/symbol-dark.svg` | Compact F symbol for dark UI |
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
