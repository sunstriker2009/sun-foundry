# Shared SUN asset preparation — v1 pilot

**Owner:** FOUNDRY (SUN-G003). **Status:** initial local-first implementation; product rollout is opt-in.

## Contract

- The owner chooses and approves the original **PNG** banner and symbol. This tool **never generates artwork**, guesses a transparent background, vectorizes raster art or alters the originals.
- Keep originals in the product's established `branding/archive/originals/` or approved master locations. A product-local JSON configuration selects the sources.
- Generated output goes into a **separate directory** (default `branding/generated/`), not the canonical `branding/assets/` paths. Review derivatives before copying/promoting them into production paths. Do not silently overwrite approved live artwork.
- The generated banner is proportionally resized to configured width, without upscaling. PNG icons are contained within square transparent canvases, preserving proportions. The favicon is a 48 px ICO. Transparent symbol export is optional and requires an actually transparent approved master.
- Raster/vector decisions remain product-specific: **SVG assets are not generated or replaced** by this tool. Use optional `iconOverrides` (a size-to-approved-PNG-path map) to copy manually approved optical icons without resampling; each override must match its configured square size. Overrides are hashed in the manifest and remain outside the generated directory. Only non-overridden sizes require a sufficiently large canonical symbol. Product-specific optical variants still need manual approval.
- Manifest records SHA-256 of each approved source and each output, output dimensions and byte size. `--check` checks outputs against the manifest without modifying files.

## Local pilot

Install Python 3.11+ and dependencies:

```sh
python -m pip install -r assets/requirements.txt
cp assets/asset-config.example.json /path/to/product/branding/asset-config.json
python scripts/prepare-assets.py --product-root /path/to/product --config branding/asset-config.json
python scripts/prepare-assets.py --product-root /path/to/product --config branding/asset-config.json --check
```

Adapt source paths, target sizes and `transparentSymbol` to the approved product masters. Do not use a flattened opaque banner as a symbol source. If no transparent symbol master exists, set `transparentSymbol: false`; a transparent icon canvas does **not** remove an opaque source background.

**Pilot target:** FOUNDRY itself, using the checked-in `branding/asset-config.json`. See [self-pilot acceptance criteria](FOUNDRY-ASSET-PILOT.md). WORKBENCH and ORYVA are intentionally excluded while their automated development workflows are active.

## CI and GitHub minutes

The [asset validation workflow](../.github/workflows/asset-validation.yml) runs on manual dispatch or changes to the FOUNDRY asset script, config example, requirements or workflow itself. It performs a synthetic smoke test and FOUNDRY self-pilot against the approved master artwork, without modifying approved production assets. Product repositories can adopt a similar **path-filtered** check for their own approved source/config/output files after the pilot. Do not trigger generation on every application commit.

## Limits

- Requires Pillow, installed locally or in CI.
- Transparent background removal from opaque artwork is **not supported**.
- No lossy image optimization, SVG conversion, image generation or approval automation.
- The manifest is provenance metadata, not a cryptographic signature or proof of human approval.
