#!/usr/bin/env python3
"""Initialize an opt-in SUN asset configuration without touching approved artwork."""
import argparse
import json
from pathlib import Path
import sys


def inside(root, value):
    resolved = (root / value).resolve()
    if not resolved.is_relative_to(root.resolve()):
        raise ValueError("Path escapes product root")
    return resolved


def initialize(product_root, config_path, banner, symbol, icon_sizes, overrides, banner_width):
    root = product_root.resolve()
    target = inside(root, config_path)
    if target.exists():
        raise FileExistsError(f"Configuration already exists: {target}")
    if not banner or not symbol:
        raise ValueError("Approved banner and symbol paths are required")
    sources = {"banner": banner, "symbol": symbol}
    for source in sources.values():
        path = inside(root, source)
        if path.suffix.lower() != ".png":
            raise ValueError("Master paths must reference PNG files")
        if path.is_relative_to(inside(root, "branding/generated")):
            raise ValueError("Masters cannot be generated outputs")
    allowed = {16, 24, 32, 48, 64, 128, 256, 512, 1024}
    if not icon_sizes or len(set(icon_sizes)) != len(icon_sizes) or any(s not in allowed for s in icon_sizes):
        raise ValueError("Invalid or duplicate icon size")
    if banner_width < 800 or banner_width > 4096:
        raise ValueError("banner width must be 800..4096")
    icon_overrides = {}
    for item in overrides:
        size_text, separator, path = item.partition("=")
        if not separator or not size_text.isdigit() or int(size_text) not in icon_sizes or not path:
            raise ValueError("Override format: SIZE=approved/icon.png; SIZE must be selected")
        if size_text in icon_overrides:
            raise ValueError("Duplicate override size")
        source = inside(root, path)
        if source.suffix.lower() != ".png" or source.is_relative_to(inside(root, "branding/generated")):
            raise ValueError("Override must be a PNG outside generated output")
        icon_overrides[size_text] = path
    config = {
        "schemaVersion": 1,
        "sources": sources,
        "outputDir": "branding/generated",
        "bannerWidth": banner_width,
        "iconSizes": icon_sizes,
        "transparentSymbol": False,
        "maxFileBytes": 5000000,
        "iconOverrides": icon_overrides,
    }
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("x", encoding="utf-8") as stream:
        json.dump(config, stream, indent=2)
        stream.write("\n")
    print(f"Created {target}; review paths and transparentSymbol before generation")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--product-root", type=Path, required=True)
    parser.add_argument("--config", default="branding/asset-config.json")
    parser.add_argument("--banner", required=True, help="Approved PNG banner path relative to product root")
    parser.add_argument("--symbol", required=True, help="Approved PNG symbol path relative to product root")
    parser.add_argument("--icon-sizes", default="16,24,32,48,64,128,256")
    parser.add_argument("--icon-override", action="append", default=[], help="SIZE=approved/icon.png; repeatable")
    parser.add_argument("--banner-width", type=int, default=1600)
    args = parser.parse_args()
    try:
        sizes = [int(value.strip()) for value in args.icon_sizes.split(",")]
        initialize(args.product_root, args.config, args.banner, args.symbol, sizes, args.icon_override, args.banner_width)
    except (ValueError, OSError) as exc:
        print(f"Asset config initialization failed: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
