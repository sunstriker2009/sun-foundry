# SUN asset preparation: opt-in adoption kit

FOUNDRY owns the shared generator. **STRATA provides repository structure**, not an approval to replace product branding. No ORYVA/WORKBENCH changes are made by this kit.

## New product or existing repository

1. Confirm owner-approved PNG banner and canonical symbol, their source paths, and whether the symbol actually has transparency.
2. Copy `scripts/prepare-assets.py`, `scripts/init-asset-config.py`, and `assets/requirements.txt` from a pinned FOUNDRY revision into the product repository (or run the scripts from a pinned FOUNDRY checkout using `--product-root`).
3. Initialize a configuration (never overwrites an existing one):

```sh
python scripts/init-asset-config.py --product-root . \
  --banner branding/archive/originals/readme-banner-v1.png \
  --symbol branding/assets/symbol-canonical-v1.png \
  --icon-override 16=branding/assets/icons/icon-16.png
```

4. Review `branding/asset-config.json`. Set `transparentSymbol: true` **only** for a transparent approved master; adjust icon sizes to source resolution. Explicitly map approved optical variants using `iconOverrides`.
5. Install dependencies and run:

```sh
python -m pip install -r assets/requirements.txt
python scripts/prepare-assets.py --product-root . --config branding/asset-config.json
python scripts/prepare-assets.py --product-root . --config branding/asset-config.json --check
```

6. Inspect generated banner, favicon, icons and manifest; **do not automatically promote** `branding/generated/` into live `branding/assets/`.

## STRATA integration contract

A future STRATA adoption PR may include a *disabled-by-default* asset workflow and a link to this guide. Do not ship FOUNDRY-specific masters or hardcoded symbol versions in STRATA. Product-local configuration is created only after artwork approval. Keep product setup optional and do not modify active hourly workflows in OUTPOST or WORKBENCH.

## CI / free-tier cost

Use a path-filtered workflow for `branding/asset-config.json`, approved sources and overrides, and generator/tests. Run asset validation separately from .NET/Next.js application builds. Run the generation and `--check` steps on the same runner so generated outputs are available. Avoid committing generated outputs until explicitly approved.

## Boundaries

The initializer creates only a JSON configuration, does not read/alter production artwork, and refuses to overwrite existing configurations. It validates path shapes, **not artwork approval or actual source dimensions**; generation performs source validation. The example requires paths to be adapted to each product.
