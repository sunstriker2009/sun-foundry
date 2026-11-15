import copy
import importlib.util
from pathlib import Path
import unittest

SPEC = importlib.util.spec_from_file_location('align', Path(__file__).resolve().parents[1] / 'scripts/align-governance.py')
align = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(align)
POLICY = dict(repository='sunstriker2009/sun-foundry', rulesetId=123, legacyName='main', requiredChecks=['build'])


class FakeGitHub:
    def __init__(self):
        self.calls = []
        self.info = dict(full_name=POLICY['repository'], default_branch='main', **align.SETTINGS)
        self.info['allow_auto_merge'] = False
        self.ruleset = dict(id=123, name='main', target='branch', enforcement='active',
                            conditions={'ref_name': {'include': ['~DEFAULT_BRANCH'], 'exclude': []}},
                            bypass_actors=[], rules=[{'type': 'deletion'}, {'type': 'non_fast_forward'}])
        self.observed = ['build']
        self.conflict = False
        self.fail_patch = False

    def request(self, method, path, payload=None):
        self.calls.append((method, path, copy.deepcopy(payload)))
        if method == 'PUT':
            self.ruleset = dict(id=123, **copy.deepcopy(payload))
            # GitHub may include new optional default fields in the readback.
            next(r for r in self.ruleset['rules'] if r['type'] == 'pull_request')['parameters']['required_reviewers'] = []
            return copy.deepcopy(self.ruleset)
        if method == 'PATCH':
            if self.fail_patch:
                raise RuntimeError('simulated settings failure')
            self.info.update(payload)
            return copy.deepcopy(self.info)
        if path.endswith('/rulesets/123'):
            return copy.deepcopy(self.ruleset)
        if '/rulesets?' in path:
            rows = [dict(id=self.ruleset['id'], name=self.ruleset['name'])]
            if self.conflict:
                rows.append(dict(id=456, name=align.NAME))
            return rows
        if path.endswith('/branches/main'):
            return {'commit': {'sha': 'main-sha'}}
        if '/pulls?' in path:
            return []
        if '/check-runs?' in path:
            return {'check_runs': [{'name': n} for n in self.observed]}
        return copy.deepcopy(self.info)

    def writes(self):
        return [c for c in self.calls if c[0] != 'GET']


class AlignmentTests(unittest.TestCase):
    def test_plan_is_read_only_and_identifies_exact_existing_id(self):
        api = FakeGitHub()
        plan = align.make_plan(api, POLICY)
        self.assertEqual(plan['rulesetId'], 123)
        self.assertEqual(plan['after']['ruleset']['name'], align.NAME)
        self.assertEqual(api.writes(), [])

    def test_apply_updates_existing_ruleset_then_settings_and_verifies(self):
        api = FakeGitHub()
        plan = align.make_plan(api, POLICY)
        align.apply_plan(api, POLICY, plan, POLICY['repository'])
        writes = api.writes()
        self.assertEqual([c[0] for c in writes], ['PUT', 'PATCH'])
        self.assertTrue(writes[0][1].endswith('/rulesets/123'))
        self.assertEqual(writes[1][2], {'allow_auto_merge': True})
        align.verify(api, POLICY)
        self.assertFalse(any(c[0] in ('POST', 'DELETE') for c in api.calls))

    def test_wrong_confirmation_stale_plan_and_tampered_plan_never_write(self):
        for condition in ('confirmation', 'stale', 'tampered'):
            api = FakeGitHub()
            plan = align.make_plan(api, POLICY)
            confirm = POLICY['repository']
            if condition == 'confirmation':
                confirm = 'wrong'
            if condition == 'stale':
                api.info['delete_branch_on_merge'] = False
            if condition == 'tampered':
                plan['after']['ruleset']['bypass_actors'] = [{'actor_id': 1}]
            with self.assertRaises(ValueError):
                align.apply_plan(api, POLICY, plan, confirm)
            self.assertEqual(api.writes(), [])

    def test_preserves_stronger_reviews_unknown_rules_and_check_app_binding(self):
        api = FakeGitHub()
        api.ruleset['rules'] += [
            {'type': 'pull_request', 'parameters': {'required_approving_review_count': 3,
             'require_code_owner_review': True, 'require_last_push_approval': True}},
            {'type': 'required_status_checks', 'parameters': {'required_status_checks':
             [{'context': 'build', 'integration_id': 15368}]}},
            {'type': 'required_signatures'}]
        after = align.make_plan(api, POLICY)['after']['ruleset']
        pr = next(r['parameters'] for r in after['rules'] if r['type'] == 'pull_request')
        self.assertEqual(pr['required_approving_review_count'], 3)
        self.assertTrue(pr['require_code_owner_review'])
        self.assertTrue(pr['require_last_push_approval'])
        self.assertIn({'type': 'required_signatures'}, after['rules'])
        checks = next(r['parameters']['required_status_checks'] for r in after['rules'] if r['type'] == 'required_status_checks')
        self.assertEqual(checks, [{'context': 'build', 'integration_id': 15368}])

    def test_refuses_bypass_exclusions_wide_scope_unknown_checks_and_conflicts(self):
        for variant in ('bypass', 'exclude', 'scope', 'checks', 'conflict', 'identity'):
            api = FakeGitHub()
            if variant == 'bypass':
                api.ruleset['bypass_actors'] = [{'actor_id': 1}]
            if variant == 'exclude':
                api.ruleset['conditions']['ref_name']['exclude'] = ['refs/heads/main']
            if variant == 'scope':
                api.ruleset['conditions']['ref_name']['include'] = ['refs/heads/*']
            if variant == 'checks':
                api.ruleset['rules'].append({'type': 'required_status_checks', 'parameters':
                   {'required_status_checks': [{'context': 'security'}]}})
            if variant == 'conflict':
                api.conflict = True
            if variant == 'identity':
                api.info['default_branch'] = 'develop'
            with self.assertRaises(ValueError):
                align.make_plan(api, POLICY)
            self.assertEqual(api.writes(), [])

    def test_unobserved_check_fails_before_writes(self):
        api = FakeGitHub()
        api.observed = ['some-other-job']
        with self.assertRaises(ValueError):
            align.make_plan(api, POLICY)
        self.assertEqual(api.writes(), [])

    def test_idempotent_plan_apply_has_no_writes(self):
        api = FakeGitHub()
        align.apply_plan(api, POLICY, align.make_plan(api, POLICY), POLICY['repository'])
        api.calls.clear()
        align.apply_plan(api, POLICY, align.make_plan(api, POLICY), POLICY['repository'])
        self.assertEqual(api.writes(), [])

    def test_partial_failure_preserves_strengthened_rules_and_requires_new_plan(self):
        api = FakeGitHub()
        plan = align.make_plan(api, POLICY)
        api.fail_patch = True
        with self.assertRaises(RuntimeError):
            align.apply_plan(api, POLICY, plan, POLICY['repository'])
        self.assertEqual(api.ruleset['name'], align.NAME)
        self.assertFalse(api.info['allow_auto_merge'])
        api.calls.clear()
        with self.assertRaises(ValueError):
            align.apply_plan(api, POLICY, plan, POLICY['repository'])
        self.assertEqual(api.writes(), [])

    def test_verify_never_changes_drift(self):
        api = FakeGitHub()
        with self.assertRaises(ValueError):
            align.verify(api, POLICY)
        self.assertEqual(api.writes(), [])

    def test_ecosystem_uses_explicit_existing_ruleset_and_universal_check(self):
        policy = align.target_policy('sunstriker2009/sun-ecosystem')
        self.assertEqual(policy['rulesetId'], 26217070)
        self.assertEqual(policy['requiredChecks'], ['gallery'])
        with self.assertRaises(ValueError):
            align.target_policy('sunstriker2009/unlisted-repository')


if __name__ == '__main__':
    unittest.main()
