# FOUNDRY self-pilot: shared asset preparation

**Pilot target:** FOUNDRY (SUN-G003). **Status:** self-pilot configured; regression hardening in progress. CI results must be checked before marking complete.

## Approved inputs

- `branding/archive/originals/readme-banner-v1.png`: exact archived owner-approved banner; do not replace.
- `branding/assets/refs/symbol-canonical-v2.png`: owner-approved transparent canonical symbol.
- `branding/assets/icons/icon-{size}.png`: already approved production icons. Small 16–48 px icons are **optical adaptations**, not expected to match generic downscales.

## How to run

```sh
python -m pip install -r assets/requirements.txt
python scripts/prepare-assets.py --product-root . --config branding/asset-config.json
python scripts/prepare-assets.py --product-root . --config branding/asset-config.json --check
```

Output goes to `branding/generated/`, separate from approved production files. Compare the generated files with existing icons and inspect 16–48 px visually. The script does **not** promote outputs into `branding/assets/` and does not create SVGs.

## Acceptance

- Sources are never modified.
- Expected PNG icon sizes, README banner, favicon and transparent symbol export are present.
- The manifest records source/output SHA-256, dimensions and bytes.
- A second `--check` validates generated assets without writing.
- Tampering with a generated file is rejected, not just missing outputs.
- No CI run is required for unrelated application code changes.

## Important limitation

Generic icon resampling cannot reproduce reviewed optical variants. Passing automated checks does **not** mean generated icons are approved replacements.

## Regression coverage

Run `python -m unittest discover -s tests -p 'test_asset_pipeline.py' -v` locally. Tests cover valid manifest generation, transparent icon output, missing/corrupted source, altered or missing output, modified manifest, attempted upscaling, nontransparent symbol rejection and output path traversal. The 16–48 px approved optical variants remain authoritative and are never overwritten.
