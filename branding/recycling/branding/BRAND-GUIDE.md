# FOUNDRY by Sun — Brand Guide

**Status:** Banner-aligned raster master approved by owner; consistent icon exports prepared for review; existing banner remains approved. Palette and typography specifications remain provisional  
**Approved concept:** Foundry F — second panoramic treatment (2026-11-13)  
**Tagline:** Build. Standardize. Launch.  
**Canonical SUN standard:** [Product Repository Branding Standard](https://github.com/sunstriker2009/sun-ecosystem/blob/main/docs/governance/PRODUCT-BRANDING.md)

## Approved visual direction

The approved concept is the **second treatment** of the modular F, **not** the earlier anvil concept and not an unrelated stock or search image. Its composition has a faceted gold/orange upper F and cyan/blue lower F, a luminous SUN sunrise arc with a starburst, a circular illuminated platform, and a deep navy panoramic background with sweeping blue trails. The right-hand lockup reads **FOUNDRY**, **by Sun**, and **Build. Standardize. Launch.**

The symbol expresses modular repository creation and standardization. The F is natural to the product name; the SUN arc links the product family. Do not replace this approved reference with a newly generated lookalike.

## Canonical symbol extraction policy

**Source of truth:** the exact owner-approved second-treatment panoramic PNG at `branding/assets/readme-banner.png`. Preserve its original F and SUN arc (including the distinctive disconnected arms, glass-like luminosity, gradients and material). Do not recreate the high-resolution symbol from the compact SVG.

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

## Asset manifest (production)

| Asset | Purpose |
| --- | --- |
| `branding/assets/readme-banner.png` | Approved panoramic README banner, unchanged |
| `branding/assets/symbol.png` | Active owner-approved banner-aligned transparent raster master |
| `branding/assets/refs/symbol-canonical-v2.png` | Retained versioned approved transparent canonical master |
| `branding/assets/refs/symbol-small-master.svg` | Approved optical small-icon vector source |
| `branding/assets/icons/icon-{size}.png` | Current consistent PNG exports, sizes 16, 24, 32, 48, 64, 128, 256, 512 and 1024 |
| `branding/assets/refs/symbol-{dark,light,mono,small}.svg` | Purpose-built compact vector adaptations |
| `branding/assets/refs/lockup-{dark,light,mono}.svg` | Full product lockup variants |

## Archive manifest (nonproduction)

| Asset | Purpose |
| --- | --- |
| `branding/archive/originals/readme-banner-v1.png` | Byte-identical, immutable approved original artwork |
| `branding/archive/intermediate/small-icon-comparison.png` | V3 small-icon review comparison |
| `branding/reviews/CANONICAL-RASTER-ASSET-IMPORT.md` | Historical V3 package import and verification record |
| `branding/archive/README.md` | Archive conventions and provenance |
| `branding/archive/MIGRATION-NOTES.md` | Old-to-new asset path mapping |

The original approved concept **is the same image** as the production README banner, as confirmed by the owner. Both copies share Git blob SHA `dbfba49871e4a27b7d72dfd62fd026973cec3be5`. No independent concept was fabricated.

The historical canonical transparent symbol remains in refs as version 2. Historical V3 small PNG icons (16–48 px) are approved optical-size adaptations; the 64–1024 px sizes derive from the canonical raster. No binary artwork was regenerated in this naming migration.

## Usage and revision rules

- Keep the original concept separately from production assets.
- Use the exact approved second-treatment panoramic image for the README, preserving aspect ratio and legibility.
- Use the stable production banner and symbol paths; retain versioned reference artwork under `branding/assets/refs/`.
- Do not distort, recolor or substitute the approved identity without review.
- Update the asset manifest and README references together in a feature-branch PR.

## Adoption checklist

- [x] Concept direction reviewed and approved by owner.
- [x] SUN arc, purpose-led F and distinct warm/cool palette defined.
- [x] Initial compact SVG lockup and symbol variants prepared.
- [x] Approved original archived unchanged under `branding/archive/originals/`.
- [x] Approved panoramic PNG committed as `branding/assets/readme-banner.png`.
- [x] README updated to reference the approved panoramic PNG.
- [x] Revised compact SVG direction reviewed (disconnected F arms and glass-like arc).
- [x] Owner-approved transparent canonical V2 symbol delivered and validated against the approved asset package (not a claim of pixel-perfect extraction from a layered source).
- [x] Nine owner-approved V3 PNG icon exports delivered and validated (16–48 px are optical adaptations; 64–1024 px derive from the canonical raster).
- [ ] Final asset palette and typography formally approved (separate design task).

## SUN naming and archival migration

The approved SUN standard uses generic filenames within product repositories, without redundant product prefixes. This migration reuses original Git blob hashes to rename the canonical symbol and all nine icons, moves the review comparison to `archive/intermediate/`, and archives an exact copy of the original banner. All live README references remain unchanged.

See [migration notes](archive/MIGRATION-NOTES.md) for old-to-new paths and verification.

## Ecosystem registry synchronization

The stable canonical path is `branding/assets/symbol.png`. The initial canonical-path adoption reused the exact Git blob `06ad4f6a79eef95ae04ae439c9ff44ba088eccba` from the earlier approved `symbol-canonical-v2.png` before the banner-aligned revision below. The active source remains within the registry's 2,000,000-byte limit.

Merging this branding alignment PR approves the canonical source for FOUNDRY (SUN-G003) registry synchronization. FOUNDRY's daily reconciliation or manual **Reconcile Approved SUN Symbols** run copies it into SUN Ecosystem's gallery through a protected squash-auto-merge PR. No separate digest-approval PR is required. Future canonical updates must follow the normal branding PR process.

## Active asset layout

Only `readme-banner.png` and `symbol.png` remain as active files directly under `branding/assets/`. Versioned masters and SVG variants are retained unchanged under `branding/assets/refs/`. Production icon exports remain in `branding/assets/icons/`. The repository README stays at the repository root and uses the stable banner path. Historical import/archive records describe prior layouts.

## Banner-aligned raster revision

The active `branding/assets/symbol.png` is a transparent raster adaptation made with image generation using the exact approved `readme-banner.png` as the editing reference. It follows the banner’s separated warm upper arm, cool lower arm and stem, sunrise arc and star. It is an image-assisted reconstruction, not a byte-exact cutout or layered original. The banner is unchanged. The owner approved this master in the continuation thread; merging the artwork PR publishes it and the reviewed icon family.

All nine `branding/assets/icons/icon-{size}.png` files (16 through 1024) now derive from this one square RGBA master through `scripts/prepare-assets.py` with no optical overrides. Geometry, framing and colors are consistent across sizes; fine highlights naturally become less visible at small sizes. The square master supplies the padding for every export.

Previous V3 icons remain under `branding/assets/refs/icons-v3/`; the earlier transparent master remains `branding/assets/refs/symbol-canonical-v2.png`. Those are historical references and must not override active icon generation. The configuration points to `branding/assets/symbol.png`; the new manifest is `branding/assets/refs/banner-aligned-asset-manifest.json`. Hashes record provenance/change detection, not a separate approval gate. Earlier V3 approval statements above describe the retained historical set.
