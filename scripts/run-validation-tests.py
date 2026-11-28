#!/usr/bin/env python3
"""Run lightweight validation together; asset regressions use asset-validation.yml."""
from pathlib import Path
import unittest

root = Path(__file__).resolve().parents[1]
suite = unittest.TestSuite()
for path in sorted((root / "tests").glob("test_*.py")):
    if path.name not in {"test_asset_adoption.py", "test_asset_pipeline.py"}:
        suite.addTests(unittest.defaultTestLoader.discover(str(root / "tests"), pattern=path.name))
result = unittest.TextTestRunner(verbosity=2).run(suite)
raise SystemExit(0 if result.wasSuccessful() else 1)
