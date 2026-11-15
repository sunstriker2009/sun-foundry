import importlib.util
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

SPEC = importlib.util.spec_from_file_location('inputs', Path(__file__).resolve().parents[1] /
                                              'scripts/resolve-workflow-repository.py')
inputs = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(inputs)


class RepositoryInputTests(unittest.TestCase):
    def test_known_repository_and_short_confirmation_expand_for_backend(self):
        result = inputs.resolve('sun-foundry', '', 'sun-foundry', 'alignment', 'apply')
        self.assertEqual(result['repository'], 'sunstriker2009/sun-foundry')
        self.assertEqual(result['confirmation'], result['repository'])

    def test_alignment_plan_needs_no_confirmation(self):
        result = inputs.resolve('sun-strata', '', '', 'alignment', 'plan')
        self.assertEqual(result['confirmation'], '')

    def test_missing_or_mismatched_confirmation_is_rejected_for_mutations(self):
        for confirmation in ('', 'sun-strata'):
            with self.assertRaises(ValueError):
                inputs.resolve('sun-foundry', '', confirmation, 'alignment', 'apply')

    def test_custom_repository_and_create_target_are_short_but_owner_is_fixed(self):
        result = inputs.resolve(inputs.OTHER, 'sun-example', 'sun-example', 'factory', 'create')
        self.assertEqual(result['factory_target'], 'sun-example')
        self.assertEqual(result['factory_confirmation'], 'sun-example')
        self.assertEqual(result['repository'], 'sunstriker2009/sun-example')

    def test_resume_target_and_confirmation_remain_fully_qualified_in_backend(self):
        result = inputs.resolve('sun-foundry', '', 'sun-foundry', 'factory', 'resume')
        self.assertEqual(result['factory_target'], 'sunstriker2009/sun-foundry')
        self.assertEqual(result['factory_confirmation'], result['factory_target'])

    def test_known_create_accidental_other_field_and_empty_custom_are_rejected(self):
        cases = [('sun-foundry', '', 'sun-foundry', 'factory', 'create'),
                 ('sun-foundry', 'sun-other', '', 'maintenance', 'plan'),
                 (inputs.OTHER, '', '', 'maintenance', 'plan')]
        for args in cases:
            with self.assertRaises(ValueError):
                inputs.resolve(*args)

    def test_foreign_owner_traversal_shell_and_newline_inputs_are_rejected(self):
        for bad in ('other/sun-foundry', '../sun-foundry', 'sun-one/two', 'sun-one\nx=bad',
                    'sun-$(echo bad)', ' sun-foundry', '-sun-foundry'):
            with self.assertRaises(ValueError):
                inputs.resolve(inputs.OTHER, bad, bad, 'registration', 'apply')

    def test_same_owner_full_inputs_remain_compatible(self):
        result = inputs.resolve('sunstriker2009/sun-foundry', '',
                                'sunstriker2009/sun-foundry', 'maintenance', 'apply')
        self.assertEqual(result['name'], 'sun-foundry')

    def test_alignment_scope_cannot_be_expanded_using_custom_input(self):
        for args in [(inputs.OTHER, 'sun-other', '', 'alignment', 'plan'),
                     ('sun-ecosystem', '', '', 'alignment', 'plan')]:
            with self.assertRaises(ValueError):
                inputs.resolve(*args)

    def test_read_only_maintenance_can_use_an_unlisted_name(self):
        result = inputs.resolve(inputs.OTHER, 'marketpilot-ai', '', 'maintenance', 'diagnose')
        self.assertEqual(result['repository'], 'sunstriker2009/marketpilot-ai')

    def test_dropdowns_and_resolver_are_present_in_every_target_workflow(self):
        inputs.check_workflows()

    def test_raw_repository_inputs_are_consumed_only_by_the_resolver(self):
        for filename in inputs.WORKFLOWS:
            text = (inputs.ROOT / '.github/workflows' / filename).read_text()
            self.assertEqual(text.count('${{ inputs.repository }}'), 1, filename)
            self.assertEqual(text.count('${{ inputs.confirm_repository }}'), 1, filename)
            self.assertIn('id: target', text, filename)
            self.assertIn('steps.target.outputs.', text, filename)
            self.assertIn("github.actor == 'sunstriker2009'", text, filename)
            self.assertIn('environment: repository-administration', text, filename)

    def test_cli_outputs_do_not_implicitly_confirm_an_empty_confirmation(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / 'outputs'
            with patch.dict(os.environ, {'SELECTION': 'sun-foundry', 'OTHER_REPOSITORY': '',
                            'CONFIRM_SHORT': '', 'OPERATION': 'plan', 'GITHUB_OUTPUT': str(output)}), \
                 patch('sys.argv', ['resolve', '--profile', 'alignment']):
                inputs.main()
            text = output.read_text()
            self.assertIn('repository=sunstriker2009/sun-foundry\n', text)
            self.assertIn('confirmation=\n', text)


if __name__ == '__main__':
    unittest.main()
