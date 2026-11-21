import importlib.util
import json
import os
from copy import deepcopy
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("proposal", ROOT / "scripts/propose-product-registration.py")
proposal = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(proposal)


class ProductRegistrationTests(unittest.TestCase):
    def setUp(self):
        self.catalog = {
            "schemaVersion": 1,
            "families": {
                "productivity": {"format": "SUN-PNNN", "nextId": "SUN-P002", "repositoryClassification": "product"},
                "application_component": {"format": "SUN-CNNN", "nextId": "SUN-C002", "repositoryClassification": "product"},
                "governance": {"format": "SUN-GNNN", "nextId": "SUN-G002", "repositoryClassification": "infrastructure"},
            },
            "products": [
                {"id": "SUN-C001", "name": "Ledger", "repository": "sun-ledger",
                 "family": "application_component", "shortDescription": None},
                {"id": "SUN-P001", "name": "Script Case", "repository": "sun-script-case",
                 "family": "productivity", "previousNames": ["Script Vault"]},
            ],
            "infrastructure": [
                {"id": "SUN-G001", "name": "Factory Pilot", "repository": "sun-factory-pilot", "family": "governance"},
            ],
        }

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
        for name in ("SCRIPT CASE", "sCrIpT VaUlT", "Factory--Pilot"):
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

    def test_merge_validation_accepts_the_exact_proposal_and_family_increment(self):
        product, next_id = proposal.registration(self.catalog, "Data Studio", "productivity", "")
        proposed = deepcopy(self.catalog)
        proposal.add_registration(proposed, product, next_id)
        ref = f"{proposal.PROPOSAL_PREFIX}{product['id']}-{product['repository']}"
        proposal.validate_pull_request(self.catalog, proposed, ref)

        proposed["families"]["application_component"]["nextId"] = "SUN-C999"
        with self.assertRaisesRegex(ValueError, "match the generated proposal"):
            proposal.validate_pull_request(self.catalog, proposed, ref)

    def test_merge_validation_requires_a_new_branch_when_the_id_changes(self):
        product, next_id = proposal.registration(self.catalog, "Data Studio", "productivity", "")
        proposed = deepcopy(self.catalog)
        proposal.add_registration(proposed, product, next_id)
        stale_ref = f"{proposal.PROPOSAL_PREFIX}{product['id']}-{product['repository']}"

        winner, following_id = proposal.registration(self.catalog, "Query Pad", "productivity", "")
        base = deepcopy(self.catalog)
        proposal.add_registration(base, winner, following_id)
        with self.assertRaisesRegex(ValueError, f"{product['id']} is stale.*{following_id}"):
            proposal.validate_pull_request(base, proposed, stale_ref)

        revised, next_id = proposal.registration(base, "Data Studio", "productivity", "")
        refreshed = deepcopy(base)
        proposal.add_registration(refreshed, revised, next_id)
        with self.assertRaisesRegex(ValueError, "is stale"):
            proposal.validate_pull_request(base, refreshed, stale_ref)
        new_ref = f"{proposal.PROPOSAL_PREFIX}{revised['id']}-{revised['repository']}"
        proposal.validate_pull_request(base, refreshed, new_ref)

    def test_merge_validation_keeps_regular_work_and_rejects_an_unbound_registration(self):
        updated = deepcopy(self.catalog)
        updated["products"][0]["shortDescription"] = "Updated description"
        proposal.validate_pull_request(self.catalog, updated, "docs/update-product")

        product, next_id = proposal.registration(self.catalog, "Data Studio", "productivity", "")
        proposal.add_registration(updated, product, next_id)
        with self.assertRaisesRegex(ValueError, "Use the Foundry proposal workflow"):
            proposal.validate_pull_request(self.catalog, updated, "chore/edit-catalog")
        with self.assertRaisesRegex(ValueError, "ID-bound proposal"):
            proposal.validate_pull_request(self.catalog, updated, "chore/propose-product-sun-data-studio")

    def test_approved_merge_can_resume_only_while_its_identity_is_active(self):
        product, next_id = proposal.registration(self.catalog, "Data Studio", "productivity", "")
        approved = deepcopy(self.catalog)
        proposal.add_registration(approved, product, next_id)
        head = f"{proposal.PROPOSAL_PREFIX}{product['id']}-{product['repository']}"
        self.assertEqual(proposal.resolve_active_registration(self.catalog, approved, approved, head), product)
        with self.assertRaisesRegex(ValueError, "no longer active"):
            proposal.resolve_active_registration(self.catalog, approved, self.catalog, head)

    def test_private_symbol_approval_is_bound_to_the_merged_registration(self):
        for approval in (False, True):
            with self.subTest(approval=approval):
                product, next_id = proposal.registration(self.catalog, "Data Studio", "productivity", "", "private", approval)
                catalog = deepcopy(self.catalog)
                proposal.add_registration(catalog, product, next_id)
                ref = f"{proposal.PROPOSAL_PREFIX}{product['id']}-{product['repository']}"
                self.assertEqual(product["repositoryVisibility"], "private")
                self.assertIs(product["publishPrivateSymbol"], approval)
                self.assertEqual(proposal.resolve_active_registration(self.catalog, catalog, catalog, ref), product)
                active = deepcopy(catalog)
                active["products"][-1]["publishPrivateSymbol"] = not approval
                with self.assertRaisesRegex(ValueError, "no longer active"):
                    proposal.resolve_active_registration(self.catalog, catalog, active, ref)

        for visibility, approval in (("public", True), ("private", "true"), ("internal", False)):
            with self.subTest(visibility=visibility, approval=approval), self.assertRaises(ValueError):
                proposal.registration(self.catalog, "Data Studio", "productivity", "", visibility, approval)

    def test_automatic_squash_requires_owner_credential_exact_head_and_successful_build(self):
        repo = "sunstriker2009/sun-foundry"
        head = "a" * 40
        branch = "chore/propose-product-SUN-P002-sun-data-studio"
        pull = {
            "state": "open", "draft": False, "merged": False, "mergeable_state": "clean",
            "base": {"ref": "main", "repo": {"full_name": repo}},
            "head": {"sha": head, "ref": branch, "repo": {"full_name": repo}},
        }
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "gh").write_text("""#!/usr/bin/env bash
case "$2" in
  user) printf '%s\n' "$MOCK_ACTOR" ;;
  */check-runs) printf '%s\n' "$MOCK_BUILD" ;;
  -X)
    [[ "$3" == PUT && "$4" == */pulls/95/merge &&
       "$6" == "sha=$REGISTRATION_HEAD" && "$8" == merge_method=squash ]] || exit 1
    printf '{"merged":true}\n' ;;
  */pulls/95) printf '%s\n' "$MOCK_PULL" ;;
  *) exit 1 ;;
esac
""", encoding="utf-8")
            (root / "gh").chmod(0o755)
            env = dict(os.environ, PATH=f"{root}:{os.environ['PATH']}", GITHUB_REPOSITORY=repo,
                       GITHUB_STEP_SUMMARY=str(root / "summary"), REGISTRATION_PR="95",
                       REGISTRATION_HEAD=head, REGISTRATION_BRANCH=branch, MOCK_PULL=json.dumps(pull),
                       MOCK_ACTOR="sunstriker2009", MOCK_BUILD="success")
            script = ROOT / "scripts/merge-owner-approved-registration.sh"
            result = subprocess.run(["bash", script], env=env, text=True, capture_output=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("squash-merged", (root / "summary").read_text(encoding="utf-8"))

            (root / "summary").unlink()
            changed_pull = {**pull, "head": {**pull["head"], "sha": "b" * 40}}
            for name, changes, expected in (
                ("failed build", {"MOCK_BUILD": "failure"}, "required build check"),
                ("foreign credential", {"MOCK_ACTOR": "other"}, "owner's credential"),
                ("changed head", {"MOCK_PULL": json.dumps(changed_pull)}, "no longer matches"),
                ("behind main", {"MOCK_PULL": json.dumps({**pull, "mergeable_state": "behind"})}, "is stale"),
            ):
                with self.subTest(name=name):
                    result = subprocess.run(["bash", script], env=dict(env, **changes), text=True, capture_output=True)
                    self.assertNotEqual(result.returncode, 0)
                    self.assertIn(expected, result.stdout)
                    self.assertFalse((root / "summary").exists())
