#!/usr/bin/env python3
"""Generate FOUNDRY PNG app icons from the approved compact SVG master.

Usage: python scripts/export-brand-icons.py
Requires: pip install cairosvg
"""
from pathlib import Path
import argparse

ROOT = Path(__file__).resolve().parents[1]
MASTER = ROOT / "branding/assets/icons/app-icon.svg"
OUTPUT = ROOT / "branding/assets/icons/png"
SIZES = (16, 24, 32, 48, 64, 128, 256, 512, 1024)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=OUTPUT)
    args = parser.parse_args()
    try:
        import cairosvg
    except ImportError as exc:
        raise SystemExit("Install CairoSVG first: python -m pip install cairosvg") from exc
    args.output.mkdir(parents=True, exist_ok=True)
    source = MASTER.read_bytes()
    for size in SIZES:
        target = args.output / f"foundry-app-icon-{size}.png"
        cairosvg.svg2png(bytestring=source, write_to=str(target),
                        output_width=size, output_height=size)
        print(f"Generated {target.relative_to(ROOT) if target.is_relative_to(ROOT) else target}")


if __name__ == "__main__":
    main()
