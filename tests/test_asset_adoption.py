"""Test safe, opt-in asset configuration initialization."""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts/init-asset-config.py"
spec = importlib.util.spec_from_file_location("asset_init", MODULE_PATH)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class AdoptionTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)

    def init(self, overrides=None):
        module.initialize(
            self.root, "branding/asset-config.json",
            "branding/archive/originals/banner.png",
            "branding/assets/symbol.png",
            [16, 32, 256], overrides or [], 1600,
        )

    def test_create_opt_in_config(self):
        self.init(["16=branding/assets/icons/icon-16.png"])
        config = json.loads((self.root / "branding/asset-config.json").read_text())
        self.assertEqual(config["iconOverrides"]["16"], "branding/assets/icons/icon-16.png")
        self.assertFalse(config["transparentSymbol"])

    def test_no_overwrite(self):
        self.init()
        with self.assertRaises(FileExistsError):
            self.init()

    def test_reject_escape(self):
        with self.assertRaises(ValueError):
            module.initialize(self.root, "../escape.json", "banner.png", "symbol.png", [16], [], 1600)

    def test_reject_duplicate_override(self):
        with self.assertRaises(ValueError):
            self.init(["16=one.png", "16=two.png"])

    def test_reject_unselected_override(self):
        with self.assertRaises(ValueError):
            self.init(["48=other.png"])

    def test_reject_generated_master(self):
        with self.assertRaises(ValueError):
            module.initialize(self.root, "branding/asset-config.json", "branding/generated/banner.png", "symbol.png", [16], [], 1600)


if __name__ == "__main__":
    unittest.main()
