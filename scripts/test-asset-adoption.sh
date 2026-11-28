#!/usr/bin/env bash
set -euo pipefail
ROOT=$(mktemp -d)
trap 'rm -rf "$ROOT"' EXIT
export ASSET_E2E_ROOT="$ROOT"
mkdir -p "$ROOT/scripts" "$ROOT/assets" "$ROOT/branding/assets/icons"
cp scripts/prepare-assets.py scripts/init-asset-config.py "$ROOT/scripts/"

python - <<'PY'
import os
from pathlib import Path
from PIL import Image
root = Path(os.environ["ASSET_E2E_ROOT"])
Image.new("RGB", (1800, 600), "#1c3450").save(root / "branding/assets/readme-banner.png")
symbol = Image.new("RGBA", (512, 512), (0, 0, 0, 0))
symbol.paste((255, 140, 60, 255), (60, 60, 452, 452))
symbol.save(root / "branding/assets/symbol.png")
Image.new("RGBA", (16, 16), (30, 210, 150, 255)).save(root / "branding/assets/icons/icon-16.png")
PY

set -euo pipefail
ROOT="$ASSET_E2E_ROOT"
python "$ROOT/scripts/init-asset-config.py" --product-root "$ROOT" \
  --banner branding/assets/readme-banner.png \
  --symbol branding/assets/symbol.png \
  --icon-override 16=branding/assets/icons/icon-16.png
if python "$ROOT/scripts/init-asset-config.py" --product-root "$ROOT" \
  --banner branding/assets/readme-banner.png \
  --symbol branding/assets/symbol.png; then
  echo "::error::Initializer unexpectedly overwrote existing config"
  exit 1
fi
python "$ROOT/scripts/prepare-assets.py" --product-root "$ROOT" --config branding/asset-config.json
python "$ROOT/scripts/prepare-assets.py" --product-root "$ROOT" --config branding/asset-config.json --check
python - <<'PY'
import hashlib, json, os
from pathlib import Path
from PIL import Image
root = Path(os.environ["ASSET_E2E_ROOT"])
manifest = json.loads((root / "branding/generated/asset-manifest.json").read_text())
assert "16" in manifest["iconOverrides"]
assert len(manifest["outputs"]) >= 9
with Image.open(root / "branding/generated/icons/icon-16.png") as icon:
    assert icon.getpixel((0, 0)) == (30, 210, 150, 255)
for source in ("branding/assets/readme-banner.png", "branding/assets/symbol.png"):
    assert hashlib.sha256((root / source).read_bytes()).hexdigest() == manifest["sources"]["banner" if "banner" in source else "symbol"]["sha256"]
target = root / "branding/generated/icons/icon-16.png"
target.write_bytes(b"tampered")
PY
if python "$ROOT/scripts/prepare-assets.py" --product-root "$ROOT" --config branding/asset-config.json --check; then
  echo "::error::Tampered output was accepted"
  exit 1
fi
python "$ROOT/scripts/prepare-assets.py" --product-root "$ROOT" --config branding/asset-config.json
python "$ROOT/scripts/prepare-assets.py" --product-root "$ROOT" --config branding/asset-config.json --check
