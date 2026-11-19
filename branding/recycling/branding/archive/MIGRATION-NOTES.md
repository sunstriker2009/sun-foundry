# FOUNDRY asset naming migration

This repository is the SUN reference implementation of the [branding standard](https://github.com/sunstriker2009/sun-ecosystem/blob/main/docs/governance/PRODUCT-BRANDING.md).

| Old path | Canonical path |
| --- | --- |
| `branding/assets/foundry-symbol-canonical-v2.png` | `branding/assets/symbol-canonical-v2.png` |
| `branding/assets/icons/foundry-icon-{size}.png` | `branding/assets/icons/icon-{size}.png` |
| `branding/assets/small-icon-master.svg` | `branding/assets/symbol-small-master.svg` |
| `branding/assets/small-icon-comparison.png` | `branding/archive/intermediate/small-icon-comparison.png` |
| `branding/assets/readme-banner-v1.png` | Unchanged; exact copy at `branding/archive/originals/readme-banner-v1.png` |

Sizes: 16, 24, 32, 48, 64, 128, 256, 512, 1024.

**Integrity:** Binary and vector assets were moved by reusing their existing Git blob SHA values; no encoding or image recompression occurred. The archived original and live README banner share blob SHA `dbfba49871e4a27b7d72dfd62fd026973cec3be5`.

**Compatibility:** README continues to reference `branding/assets/readme-banner-v1.png`. No historical name is retained as a duplicate production asset. Git history preserves the old filenames.

**Follow-up:** Final palette/typography approval is a separate brand-design task.
