# FOUNDRY self-pilot: shared asset preparation

**Pilot target:** FOUNDRY (SUN-G003). **Status:** self-pilot configured; regression hardening in progress. CI results must be checked before marking complete.

## Approved inputs

- `branding/archive/originals/readme-banner-v1.png`: exact archived owner-approved banner; do not replace.
- `branding/assets/symbol.png`: banner-aligned transparent master proposed in the artwork PR.
- `branding/assets/icons/icon-{size}.png`: consistent exports of the active master at all nine sizes; approval is recorded by merging the artwork PR.

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

All current sizes deliberately share one master, rather than using optical variants. Automated checks verify reproducibility; visual review of the artwork PR establishes approval.

## Regression coverage

Run `python -m unittest discover -s tests -p 'test_asset_pipeline.py' -v` locally. Tests cover valid manifest generation, transparent icon output, missing/corrupted source, altered or missing output, modified manifest, attempted upscaling, nontransparent symbol rejection and output path traversal. Legacy optical variants are retained under `branding/assets/refs/icons-v3/` and are no longer active overrides.
