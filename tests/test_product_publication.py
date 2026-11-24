import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from subprocess import CompletedProcess
from unittest.mock import MagicMock, call, patch
from urllib.error import HTTPError

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
        self.assertEqual((row["registryId"], row["classification"], row["summary"], row["symbolMode"]),
                         ("SUN-P003", "product", "Productivity product by Sun", "text"))
        self.assertNotIn("iconSha256", row)
        self.assertIs(row["autoLiveSymbol"], True)
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

    def test_only_approved_private_symbol_gets_copy_mode(self):
        self.approved.update(repositoryVisibility="public", publishPrivateSymbol=True)
        self.write_json(Path("registry/product-catalog.json"), {"products": [self.approved]})
        with self.assertRaisesRegex(ValueError, "copy approval"):
            publication.project_registration(self.root, self.approved, "2026-11-19")

        self.approved["repositoryVisibility"] = "private"
        self.write_json(Path("registry/product-catalog.json"), {"products": [self.approved]})
        self.assertTrue(publication.project_registration(self.root, self.approved, "2026-11-19"))
        catalog = self.read_json(publication.CATALOG)
        row, = catalog["repositories"]
        self.assertEqual(row["symbolMode"], "copy")
        self.assertNotIn("icon", row)
        self.assertNotIn("autoLiveSymbol", row)

        # Replaying this registration cannot restore a later-revoked copy approval.
        row["symbolMode"] = "text"
        self.write_json(publication.CATALOG, catalog)
        self.assertFalse(publication.project_registration(self.root, self.approved, "2026-11-19"))
        self.assertEqual(self.read_json(publication.CATALOG), catalog)

    def test_public_symbol_activation_only_updates_eligible_ready_products_once(self):
        def row(slug, mode="text", *, waiting=False):
            item = dict(repository=f"sunstriker2009/{slug}", classification="product", symbolMode=mode)
            if waiting:
                item["autoLiveSymbol"] = True
            return item

        ready = row("sun-ready", waiting=True)
        missing = row("sun-missing", waiting=True)
        others = [row("sun-text"), row("sun-private", "copy"), row("sun-live", "live")]
        self.write_json(publication.CATALOG, {"schemaVersion": 1, "repositories": [ready, missing, *others]})
        with patch.object(publication, "public_symbol_available", side_effect=[True, False, False]) as available:
            self.assertTrue(publication.project_public_symbols(self.root))
            self.assertFalse(publication.project_public_symbols(self.root))
        self.assertEqual(available.call_args_list, [call(ready["repository"]), call(missing["repository"]),
                                                   call(missing["repository"])])
        ready["symbolMode"] = "live"
        del ready["autoLiveSymbol"]
        self.assertEqual(self.read_json(publication.CATALOG)["repositories"], [ready, missing, *others])
        self.assertEqual(self.render.call_count, 2)

    def test_targeted_public_activation_leaves_other_ready_products_pending(self):
        first = dict(repository="sunstriker2009/sun-first", classification="product",
                     symbolMode="text", autoLiveSymbol=True)
        target = dict(first, repository="sunstriker2009/sun-target")
        self.write_json(publication.CATALOG, {"schemaVersion": 1, "repositories": [first, target]})
        with patch.object(publication, "public_symbol_available", return_value=True) as available:
            self.assertTrue(publication.project_public_symbols(self.root, target["repository"]))
            self.assertFalse(publication.project_public_symbols(self.root, target["repository"]))
            available.assert_called_once_with(target["repository"])
        target["symbolMode"] = "live"
        del target["autoLiveSymbol"]
        self.assertEqual(self.read_json(publication.CATALOG)["repositories"], [first, target])

    def test_public_symbol_requires_live_public_visibility_and_anonymous_png(self):
        repository = 'sunstriker2009/sun-example'
        image = MagicMock()
        image.__enter__.return_value.headers.get_content_type.return_value = 'image/png'
        image.__enter__.return_value.read.return_value = b'\x89PNG\r\n\x1a\n'
        url = f'https://raw.githubusercontent.com/{repository}/main/branding/assets/symbol.png'
        with patch.object(publication, 'urlopen', return_value=image) as fetch:
            for visibility in ('public', 'private'):
                api = CompletedProcess([], 0, stdout=json.dumps(dict(full_name=repository, visibility=visibility)))
                with patch.object(publication.subprocess, 'run', return_value=api):
                    self.assertEqual(publication.public_symbol_available(repository), visibility == 'public')
            fetch.assert_called_once_with(url, timeout=15)

        with patch.object(publication.subprocess, 'run', return_value=CompletedProcess(
                [], 0, stdout=json.dumps(dict(full_name=repository, visibility='public')))):
            with patch.object(publication, 'urlopen', side_effect=HTTPError(url, 404, 'Not found', None, None)):
                self.assertFalse(publication.public_symbol_available(repository))
            image.__enter__.return_value.read.return_value = b'not a PNG'
            with patch.object(publication, 'urlopen', return_value=image):
                self.assertFalse(publication.public_symbol_available(repository))
