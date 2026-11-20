# Local asset preparation

Use a pinned Foundry checkout and Python 3.11 or later. Start with owner-approved PNG masters. Keep approved originals in the product checkout and review generated derivatives before promoting them into canonical branding paths.

```sh
python -m pip install -r assets/requirements.txt
python scripts/init-asset-config.py --product-root /path/to/product \
  --banner branding/assets/readme-banner.png \
  --symbol branding/assets/symbol.png
```

The initializer creates `branding/asset-config.json` and refuses to overwrite an existing configuration. Adjust source paths, output width and icon sizes to fit the approved masters. Set `transparentSymbol: true` only for an actually transparent PNG. Use `--icon-override 16=branding/assets/icons/icon-16.png` at initialization or add an `iconOverrides` entry for an approved size-specific rendition. Each override must match its configured square size.

```sh
python scripts/prepare-assets.py --product-root /path/to/product --config branding/asset-config.json
python scripts/prepare-assets.py --product-root /path/to/product --config branding/asset-config.json --check
```

The generator writes to `branding/generated/` by default. It produces a proportional banner without upscaling, contained PNG icons, a 48 px favicon, an optional transparent symbol, and a manifest with SHA-256 digests, dimensions and file sizes. The check command validates generated outputs without modifying them. An opaque master stays opaque inside the generated canvas.

See the [workflow handbook](WORKFLOWS.md#ci-and-developer-validation) for Foundry CI coverage or [branding installation](WORKFLOWS.md#branding-and-gallery) for approved artwork packages.
