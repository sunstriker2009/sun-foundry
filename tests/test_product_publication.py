import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("publication", ROOT / "scripts/publish-product-registration.py")
publication = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(publication)


class ProductPublicationTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.root = Path(directory.name)
        (self.root / "registry").mkdir()
        self.write_json(publication.AUTHORITY, {
            "products": [], "infrastructure": [], "updated": "2026-11-19",
            "idPolicy": {
                "productivitySeries": {"nextId": "SUN-P003"},
                "applicationComponentSeries": {"nextId": "SUN-C002"},
            },
        })
        self.write_json(publication.CATALOG, {"schemaVersion": 1, "repositories": []})
        (self.root / publication.REGISTRY_PAGE).write_text(
            "**Updated:** 2026-11-19. Product registry.\n\n"
            "| ID | Name | Family | Purpose | Status | Technical identity |\n"
            "|---|---|---|---|---|---|\n\n"
            "The next publication counters are **SUN-P003** and **SUN-C002**.\n", encoding="utf-8")
        (self.root / publication.GALLERY).write_text(
            "<!-- SUN-REPOSITORY-GALLERY:START -->\n<!-- SUN-REPOSITORY-GALLERY:END -->\n",
            encoding="utf-8")
        self.approved = {
            "id": "SUN-P003", "name": "Data Studio", "family": "productivity",
            "repository": "sun-data-studio", "shortDescription": None, "publicName": "Data Studio by Sun",
        }
        self.write_json(Path("registry/product-catalog.json"), {"products": [self.approved]})
        renderer = patch.object(publication.subprocess, "run")
        self.render = renderer.start()
        self.addCleanup(renderer.stop)

    def write_json(self, path, data):
        (self.root / path).write_text(json.dumps(data), encoding="utf-8")

    def read_json(self, path):
        return json.loads((self.root / path).read_text(encoding="utf-8"))

    def test_projects_identity_references_and_fallback_and_is_idempotent(self):
        self.assertTrue(publication.project_registration(self.root, self.approved, "2026-11-19"))
        authority = self.read_json(publication.AUTHORITY)
        self.assertEqual(authority["products"][0]["commercialClearance"], "PENDING")
        self.assertEqual(authority["idPolicy"]["productivitySeries"]["nextId"], "SUN-P004")
        self.assertEqual(authority["idPolicy"]["applicationComponentSeries"]["nextId"], "SUN-C002")
        row, = self.read_json(publication.CATALOG)["repositories"]
        self.assertEqual((row["registryId"], row["classification"], row["summary"], row["icon"]),
                         ("SUN-P003", "product", "Productivity product by Sun", None))
        self.assertEqual(self.render.call_args_list[0].args[0], ["python3", "scripts/render-repository-gallery.py"])
        self.assertIn("## SUN-P003 — Data Studio", (self.root / publication.REGISTRY_PAGE).read_text())
        self.assertFalse(publication.project_registration(self.root, self.approved, "2026-11-19"))
        self.assertEqual(self.render.call_count, 2)

    def test_promotes_pending_row_without_rewinding_the_family_counter(self):
        authority = self.read_json(publication.AUTHORITY)
        authority["idPolicy"]["productivitySeries"]["nextId"] = "SUN-P006"
        self.write_json(publication.AUTHORITY, authority)
        self.write_json(publication.CATALOG, {"schemaVersion": 1, "repositories": [{
            "repository": "sunstriker2009/sun-data-studio", "registryId": None,
            "classification": "pending", "name": "sun-data-studio", "icon": None, "iconSha256": None,
        }]})
        self.approved["shortDescription"] = "Explore data"
        self.write_json(Path("registry/product-catalog.json"), {"products": [self.approved]})
        self.assertTrue(publication.project_registration(self.root, self.approved, "2026-11-18"))
        authority = self.read_json(publication.AUTHORITY)
        self.assertEqual(authority["idPolicy"]["productivitySeries"]["nextId"], "SUN-P006")
        self.assertEqual(authority["updated"], "2026-11-19")
        row, = self.read_json(publication.CATALOG)["repositories"]
        self.assertEqual((row["registryId"], row["summary"]), ("SUN-P003", "Explore data"))

    def test_refuses_a_conflicting_identity_without_editing_the_checkout(self):
        self.write_json(publication.CATALOG, {"schemaVersion": 1, "repositories": [{
            "repository": "sunstriker2009/sun-other-project", "registryId": "SUN-P003",
            "classification": "product", "name": "Other Project",
        }]})
        before = [(self.root / path).read_bytes() for path in publication.PUBLICATION_PATHS]
        with self.assertRaisesRegex(ValueError, "conflicts"):
            publication.project_registration(self.root, self.approved, "2026-11-19")
        self.assertEqual([(self.root / path).read_bytes() for path in publication.PUBLICATION_PATHS], before)
        self.render.assert_not_called()
