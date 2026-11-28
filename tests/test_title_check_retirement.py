"""Narrow migration tests: preserve protections and fail closed on stale plans."""
import copy
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

SPEC = importlib.util.spec_from_file_location('retire', Path(__file__).resolve().parents[1] / 'scripts/retire-pr-title-check.py')
retire = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(retire)
REPO = 'sunstriker2009/sun-strata'


def fixture():
    return {'id': retire.TARGETS['sun-strata'], 'source': REPO, 'source_type': 'Repository',
            'name': 'SUN Main Protection', 'target': 'branch', 'enforcement': 'active',
            'conditions': {'ref_name': {'include': ['refs/heads/main'], 'exclude': []}},
            'bypass_actors': [], 'rules': [{'type': 'deletion'}, {'type': 'non_fast_forward'},
                {'type': 'pull_request', 'parameters': {'required_approving_review_count': 1}},
                {'type': 'required_status_checks', 'parameters': {
                    'strict_required_status_checks_policy': True, 'do_not_enforce_on_create': False,
                    'required_status_checks': [{'context': 'repository-validation', 'integration_id': 123},
                        {'context': 'conventional-title'}, {'context': 'security'}]}}]}


class RetirementTests(unittest.TestCase):
    def test_only_title_entry_changes(self):
        detail = fixture()
        before, after = retire.proposal(detail, REPO)
        expected = copy.deepcopy(before)
        del expected['rules'][-1]['parameters']['required_status_checks'][1]
        self.assertEqual(after, expected)
        self.assertEqual(before, retire.normalize(detail))
        self.assertEqual(retire.proposal({**detail, **after}, REPO)[1], after)

    def test_unexpected_identity_scope_or_missing_build_is_rejected(self):
        for key, value in [('id', 1), ('source', 'other/repo'), ('enforcement', 'disabled'),
                           ('conditions', {'ref_name': {'include': ['~ALL'], 'exclude': []}})]:
            with self.assertRaises(ValueError):
                retire.proposal({**fixture(), key: value}, REPO)
        detail = fixture()
        detail['rules'][-1]['parameters']['required_status_checks'].pop(0)
        with self.assertRaises(ValueError):
            retire.proposal(detail, REPO)
        with self.assertRaises(ValueError):
            retire.proposal(fixture(), 'other/sun-strata')

    def test_plan_is_read_only_and_apply_requires_reviewed_digest_and_confirmation(self):
        detail = fixture()
        calls = []
        def api(method, path, payload=None):
            calls.append(method)
            if method == 'PUT':
                detail.update(copy.deepcopy(payload))
            return copy.deepcopy(detail)
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            result = retire.migrate(REPO, 'plan', request=api, output=output)
            self.assertEqual(calls, ['GET'])
            for digest, confirm in [('', REPO), (result['digest'], ''), ('stale', REPO)]:
                with self.assertRaises(ValueError):
                    retire.migrate(REPO, 'apply', digest, confirm, request=api, output=output)
            self.assertNotIn('PUT', calls)
            retire.migrate(REPO, 'apply', result['digest'], REPO, request=api, output=output)
            self.assertEqual(calls.count('PUT'), 1)
            self.assertEqual(json.loads((output / 'plan.json').read_text())['before'], retire.normalize(fixture()))

    def test_drift_before_write_prevents_mutation(self):
        detail = fixture()
        before, after = retire.proposal(detail, REPO)
        digest = retire.digest({'repository': REPO, 'rulesetId': detail['id'], 'before': before, 'after': after})
        calls = []
        def api(method, path, payload=None):
            calls.append(method)
            if len(calls) == 2:
                detail['bypass_actors'] = [{'actor_id': 7}]
            return copy.deepcopy(detail)
        with tempfile.TemporaryDirectory() as directory, self.assertRaises(ValueError):
            retire.migrate(REPO, 'apply', digest, REPO, request=api, output=Path(directory))
        self.assertEqual(calls, ['GET', 'GET'])

    def test_failed_verification_is_reported(self):
        detail = fixture()
        before, after = retire.proposal(detail, REPO)
        digest = retire.digest({'repository': REPO, 'rulesetId': detail['id'], 'before': before, 'after': after})
        with tempfile.TemporaryDirectory() as directory, self.assertRaises(RuntimeError):
            retire.migrate(REPO, 'apply', digest, REPO, request=lambda *args: copy.deepcopy(detail), output=Path(directory))
