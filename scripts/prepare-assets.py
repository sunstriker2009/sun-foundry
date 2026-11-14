#!/usr/bin/env python3
"""Prepare reproducible raster derivatives from owner-approved PNG artwork."""
import argparse
import hashlib
import io
import json
from pathlib import Path
import sys

from PIL import Image, ImageOps

ICON_SIZES = (16, 24, 32, 48, 64, 128, 256, 512, 1024)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def within(root, value):
    path = (root / value).resolve()
    if not path.is_relative_to(root.resolve()):
        raise ValueError(f"Path escapes product root: {value}")
    return path


def prepare(root, config_file, check=False):
    cfg = json.loads(config_file.read_text(encoding="utf-8"))
    if cfg.get("schemaVersion") != 1:
        raise ValueError("Unsupported configuration schemaVersion")
    output = within(root, cfg.get("outputDir", "branding/generated"))
    sources = cfg["sources"]
    banner_source = within(root, sources["banner"])
    symbol_source = within(root, sources["symbol"])
    for source in (banner_source, symbol_source):
        if not source.is_file() or source.suffix.lower() != ".png":
            raise ValueError(f"Approved PNG master missing: {source}")
        if source.is_relative_to(output):
            raise ValueError("Master source must be outside generated output directory")
    banner_width = int(cfg.get("bannerWidth", 1600))
    if banner_width < 800 or banner_width > 4096:
        raise ValueError("bannerWidth must be 800..4096")
    sizes = cfg.get("iconSizes", list(ICON_SIZES))
    if not sizes or any(type(s) is not int or s not in ICON_SIZES for s in sizes) or len(set(sizes)) != len(sizes):
        raise ValueError("iconSizes must be distinct supported sizes")
    max_bytes = int(cfg.get("maxFileBytes", 5_000_000))
    if max_bytes <= 0:
        raise ValueError("maxFileBytes must be positive")

    with Image.open(banner_source) as image:
        image.load()
        banner = image.convert("RGBA" if "A" in image.getbands() else "RGB")
    with Image.open(symbol_source) as image:
        image.load()
        symbol = image.convert("RGBA" if "A" in image.getbands() else "RGB")
    if banner.width < banner_width:
        raise ValueError("Banner source is smaller than target width; refusing to upscale")
    if symbol.width < max(sizes) or symbol.height < max(sizes):
        raise ValueError("Symbol source is smaller than largest icon; refusing to upscale")
    banner = banner.resize((banner_width, round(banner.height * banner_width / banner.width)), Image.Resampling.LANCZOS)

    results = {}
    def add(relative, image, fmt="PNG"):
        destination = within(output, relative)
        if not destination.is_relative_to(output):
            raise ValueError("Output path escapes generated directory")
        expected_buffer = io.BytesIO()
        image.save(expected_buffer, format=fmt, optimize=True)
        expected_bytes = expected_buffer.getvalue()
        if not check:
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(expected_bytes)
        if not destination.is_file():
            raise ValueError(f"Missing output: {destination}")
        with Image.open(destination) as actual:
            actual.load()
            if actual.size != image.size:
                raise ValueError(f"Incorrect dimensions: {destination}")
            if fmt == "PNG" and actual.format != "PNG":
                raise ValueError(f"Incorrect format: {destination}")
            if fmt == "ICO" and actual.format != "ICO":
                raise ValueError(f"Incorrect format: {destination}")
            if "A" in image.getbands() and "A" not in actual.getbands():
                raise ValueError(f"Transparency lost: {destination}")
        if check and destination.read_bytes() != expected_bytes:
            raise ValueError(f"Output content differs from deterministic generation: {destination}")
        if destination.stat().st_size > max_bytes:
            raise ValueError(f"Output exceeds file-size limit: {destination}")
        results[relative] = {"width": image.width, "height": image.height, "bytes": destination.stat().st_size, "sha256": digest(destination)}

    add("readme-banner.png", banner)
    for size in sizes:
        icon = ImageOps.contain(symbol, (size, size), Image.Resampling.LANCZOS)
        canvas = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        canvas.alpha_composite(icon.convert("RGBA"), ((size - icon.width) // 2, (size - icon.height) // 2))
        add(f"icons/icon-{size}.png", canvas)
    favicon = ImageOps.contain(symbol, (48, 48), Image.Resampling.LANCZOS)
    canvas = Image.new("RGBA", (48, 48), (0, 0, 0, 0))
    canvas.alpha_composite(favicon.convert("RGBA"), ((48 - favicon.width) // 2, (48 - favicon.height) // 2))
    add("favicon.ico", canvas, "ICO")
    if cfg.get("transparentSymbol", False):
        if "A" not in symbol.getbands() or symbol.getextrema()[-1][0] == 255:
            raise ValueError("Transparent symbol requested, but approved source has no transparent pixels")
        add("symbol-transparent.png", symbol)
    manifest = {
        "schemaVersion": 1,
        "generator": "sun-foundry/scripts/prepare-assets.py",
        "sources": {key: {"path": sources[key], "sha256": digest(path)} for key, path in (("banner", banner_source), ("symbol", symbol_source))},
        "outputs": results,
    }
    manifest_path = output / "asset-manifest.json"
    serialized = json.dumps(manifest, indent=2, sort_keys=True) + "\n"
    if check:
        if not manifest_path.is_file() or manifest_path.read_text(encoding="utf-8") != serialized:
            raise ValueError("Asset manifest missing or differs from source/config/output; regenerate")
    else:
        manifest_path.write_text(serialized, encoding="utf-8")
    print(f"{'Validated' if check else 'Prepared'} {len(results)} assets at {output}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--product-root", type=Path, default=Path("."))
    parser.add_argument("--config", type=Path, required=True, help="JSON config relative to product root")
    parser.add_argument("--check", action="store_true", help="Validate committed outputs and manifest without modifying them")
    args = parser.parse_args()
    try:
        root = args.product_root.resolve()
        prepare(root, within(root, args.config), args.check)
    except (OSError, ValueError, KeyError, json.JSONDecodeError) as error:
        print(f"Asset preparation failed: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
