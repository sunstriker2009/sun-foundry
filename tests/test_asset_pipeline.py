"""Regression tests for SUN asset generation and fail-closed validation."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from PIL import Image

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "prepare-assets.py"


class AssetPipelineTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / "masters").mkdir()
        Image.new("RGB", (1800, 600), "navy").save(self.root / "masters/banner.png")
        image = Image.new("RGBA", (512, 512), (0, 0, 0, 0))
        image.paste((240, 150, 20, 255), (64, 64, 448, 448))
        image.save(self.root / "masters/symbol.png")
        self.config = {
            "schemaVersion": 1,
            "sources": {"banner": "masters/banner.png", "symbol": "masters/symbol.png"},
            "outputDir": "generated",
            "bannerWidth": 1600,
            "iconSizes": [16, 48, 256],
            "transparentSymbol": True,
            "maxFileBytes": 5000000,
        }
        self.write_config()

    def write_config(self):
        (self.root / "config.json").write_text(json.dumps(self.config), encoding="utf-8")

    def run_pipeline(self, check=False, success=True):
        args = [sys.executable, str(SCRIPT), "--product-root", str(self.root), "--config", "config.json"]
        if check:
            args.append("--check")
        result = subprocess.run(args, capture_output=True, text=True)
        self.assertEqual(result.returncode == 0, success, result.stderr)
        return result

    def test_round_trip_manifest_and_transparency(self):
        self.run_pipeline()
        self.run_pipeline(check=True)
        manifest = json.loads((self.root / "generated/asset-manifest.json").read_text())
        self.assertEqual(len(manifest["outputs"]), 6)
        self.assertEqual(manifest["outputs"]["icons/icon-256.png"]["width"], 256)
        with Image.open(self.root / "generated/icons/icon-256.png") as icon:
            self.assertEqual(icon.getpixel((0, 0))[3], 0)

    def test_missing_source_rejected(self):
        (self.root / "masters/symbol.png").unlink()
        self.run_pipeline(success=False)

    def test_corrupt_source_rejected(self):
        (self.root / "masters/symbol.png").write_bytes(b"not a png")
        self.run_pipeline(success=False)

    def test_modified_output_rejected(self):
        self.run_pipeline()
        target = self.root / "generated/icons/icon-48.png"
        with Image.open(target) as original:
            edited = original.copy()
        edited.putpixel((0, 0), (1, 2, 3, 4))
        edited.save(target)
        self.run_pipeline(check=True, success=False)

    def test_missing_output_rejected(self):
        self.run_pipeline()
        (self.root / "generated/favicon.ico").unlink()
        self.run_pipeline(check=True, success=False)

    def test_manifest_tampering_rejected(self):
        self.run_pipeline()
        manifest = self.root / "generated/asset-manifest.json"
        manifest.write_text(manifest.read_text().replace('"schemaVersion": 1', '"schemaVersion": 2'))
        self.run_pipeline(check=True, success=False)

    def test_no_upscale(self):
        self.config["iconSizes"] = [1024]
        self.write_config()
        self.run_pipeline(success=False)

    def test_transparency_requirement(self):
        Image.new("RGB", (512, 512), "orange").save(self.root / "masters/symbol.png")
        self.run_pipeline(success=False)

    def test_optical_override_preserved(self):
        source = self.root / "masters/optical-16.png"
        Image.new("RGBA", (16, 16), (12, 34, 56, 255)).save(source)
        self.config["iconOverrides"] = {"16": "masters/optical-16.png"}
        self.write_config()
        self.run_pipeline()
        self.run_pipeline(check=True)
        with Image.open(self.root / "generated/icons/icon-16.png") as image:
            self.assertEqual(image.getpixel((0, 0)), (12, 34, 56, 255))
        manifest = json.loads((self.root / "generated/asset-manifest.json").read_text())
        self.assertIn("16", manifest["iconOverrides"])

    def test_invalid_override_dimensions_rejected(self):
        Image.new("RGBA", (32, 32), (0, 0, 0, 0)).save(self.root / "masters/wrong.png")
        self.config["iconOverrides"] = {"16": "masters/wrong.png"}
        self.write_config()
        self.run_pipeline(success=False)

    def test_override_can_supply_larger_size_without_upscale(self):
        Image.new("RGBA", (1024, 1024), (0, 0, 0, 0)).save(self.root / "masters/large.png")
        self.config["iconSizes"] = [16, 1024]
        self.config["iconOverrides"] = {"1024": "masters/large.png"}
        self.write_config()
        self.run_pipeline()
        self.run_pipeline(check=True)

    def test_path_escape_rejected(self):
        self.config["outputDir"] = "../outside"
        self.write_config()
        self.run_pipeline(success=False)


if __name__ == "__main__":
    unittest.main()
