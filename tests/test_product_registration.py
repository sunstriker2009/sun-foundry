import importlib.util
import json
from pathlib import Path
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("proposal", ROOT / "scripts/propose-product-registration.py")
proposal = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(proposal)


class ProductRegistrationTests(unittest.TestCase):
    def setUp(self):
        self.catalog = json.loads((ROOT / proposal.CATALOG).read_text(encoding="utf-8"))

    def test_derives_identity_and_advances_only_the_proposed_family(self):
        family = "application_component"
        current_id = self.catalog["families"][family]["nextId"]
        product, next_id = proposal.registration(self.catalog, "  API -Studio  ", family, "  Reusable API tools  ")
        self.assertEqual(product, {
            "id": current_id,
            "name": "API -Studio",
            "family": family,
            "repository": "sun-api-studio",
            "shortDescription": "Reusable API tools",
            "publicName": "API -Studio by Sun",
        })
        self.assertEqual(next_id, f"SUN-C{int(current_id[-3:]) + 1:03d}")
        self.assertEqual(self.catalog["families"][family]["nextId"], current_id)

    def test_preserves_compound_spelling_and_records_an_omitted_description(self):
        product, _ = proposal.registration(self.catalog, "DataStudio", "productivity", "\t ")
        self.assertEqual(product["repository"], "sun-datastudio")
        self.assertIsNone(product["shortDescription"])

    def test_rejects_names_aliases_and_normalized_slugs_already_in_the_catalog(self):
        for name in ("CODEFOLIO", "aStElVo", "Foundry--Pilot"):
            with self.subTest(name=name), self.assertRaisesRegex(ValueError, "already recorded"):
                proposal.registration(self.catalog, name, "productivity", "")

    def test_rejects_invalid_names_descriptions_and_non_product_families(self):
        for name in ("sun-new", "New by Sun", "AI/Tools", " 123 ", "A" * 97):
            with self.subTest(name=name), self.assertRaises(ValueError):
                proposal.registration(self.catalog, name, "productivity", "")
        for description in ("bad\nline", "bad|table", "A" * 181):
            with self.subTest(description=description), self.assertRaisesRegex(ValueError, "description"):
                proposal.registration(self.catalog, "Data Studio", "productivity", description)
        for family in ("governance", "unknown"):
            with self.subTest(family=family), self.assertRaisesRegex(ValueError, "product family"):
                proposal.registration(self.catalog, "Data Studio", family, "")

    def test_rejects_assigned_and_retired_ids(self):
        self.catalog["families"]["productivity"]["nextId"] = self.catalog["products"][1]["id"]
        with self.assertRaisesRegex(ValueError, "already assigned or retired"):
            proposal.registration(self.catalog, "Data Studio", "productivity", "")
        self.catalog["families"]["productivity"]["nextId"] = "SUN-P999"
        with self.assertRaisesRegex(ValueError, "cannot allocate and advance"):
            proposal.registration(self.catalog, "Data Studio", "productivity", "")

    def test_repository_lookup_fails_closed_except_on_a_not_found_response(self):
        with patch.object(proposal, "HTTPSConnection") as connect:
            connection = connect.return_value
            response = connection.getresponse.return_value
            response.status = 404
            proposal.check_repository_available("sun-data-studio", "token")
            self.assertEqual(connection.request.call_args.args, ("GET", "/repos/sunstriker2009/sun-data-studio"))
            for status in (200, 301, 401, 403, 429, 500):
                with self.subTest(status=status), self.assertRaises(ValueError):
                    response.status = status
                    proposal.check_repository_available("sun-data-studio", "token")
            connection.getresponse.side_effect = TimeoutError
            with self.assertRaisesRegex(ValueError, "could not be completed"):
                proposal.check_repository_available("sun-data-studio", "token")
