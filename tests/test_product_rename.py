import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

SPEC = importlib.util.spec_from_file_location('product', Path(__file__).resolve().parents[1] / 'scripts/rename-product.py')
product = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(product)


class API:
    def __init__(self):
        self.calls = []
        self.renamed = False
        self.deny = None

    def call(self, endpoint, method='GET', data=None, missing=False):
        self.calls.append((method, endpoint, data))
        name, _, resource = endpoint.removeprefix('repos/sunstriker2009/').partition('/')
        ids = {'sun-widget': 1, 'sun-next': 1, 'sun-strata': 2, 'sun-foundry': 3, 'sun-ecosystem': 4}
        if not resource:
            if name == 'sun-next' and not self.renamed:
                return None
            if method == 'PATCH':
                self.renamed = True
                name = data['name']
            if name == 'sun-widget' and self.renamed:
                name = 'sun-next'
            return {'id': ids[name], 'full_name': f'sunstriker2009/{name}', 'archived': False, 'default_branch': 'main'}
        if resource == 'git/ref/heads/main':
            return {'object': {'sha': 'base'}}
        if resource.startswith('git/ref/heads/'):
            return None
        if resource == 'git/commits/base':
            return {'tree': {'sha': 'base-tree'}}
        if resource == 'git/trees':
            if name == self.deny:
                raise product.repository.ApiError(403, endpoint)
            return {'sha': f'tree-{name}'}
        if resource == 'git/commits':
            return {'sha': f'commit-{name}'}
        if resource == 'git/refs':
            return {}
        if resource.startswith('pulls?'):
            return []
        if resource == 'pulls':
            return {'html_url': f'https://github.com/{name}/pull/1'}
        raise AssertionError(endpoint)


class ProductTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.source = self.root / 'fixture'
        self.source.mkdir()
        authority = {'products': [{'id': 'SUN-P001', 'family': 'productivity', 'name': 'WIDGET', 'publicName': 'WIDGET by Sun',
                                 'repository': 'sun-widget', 'namespace': 'Sun.Widget', 'status': 'CONFIRMED',
                                 'backendPackages': 'Sun.Widget.*', 'frontendPackages': '@sun-widget/*',
                                 'tagline': 'Work. Together.', 'supersedes': 'ANCIENT'}],
                     'infrastructure': [{'id': 'SUN-G003', 'name': 'FOUNDRY', 'repository': 'sun-foundry', 'status': 'ESTABLISHED'}]}
        catalog = {'schemaVersion': 1, 'galleryDirectory': 'gallery', 'repositories': [
            {'registryId': 'SUN-P001', 'repository': 'sunstriker2009/sun-widget', 'name': 'WIDGET',
             'classification': 'product', 'summary': 'Local workspace', 'icon': None, 'iconSha256': None},
            {'registryId': 'SUN-G003', 'repository': 'sunstriker2009/sun-foundry', 'name': 'FOUNDRY',
             'classification': 'infrastructure', 'summary': 'Repository Factory'}]}
        files = {'registry/products.json': json.dumps(authority),
                 'registry/repositories.json': json.dumps(catalog),
                 'registry/product-catalog.json': json.dumps(authority),
                 'registry/GALLERY.md': product.gallery.START + '\n' + product.gallery.END + '\n',
                 'README.md': '# WIDGET by Sun\n[WIDGET](https://github.com/sunstriker2009/sun-widget)\n',
                 'desktop/main.mjs': "app.setName('WIDGET by Sun');\nconst profile = app.getPath('userData') + '/WIDGET by Sun';\nconst title = 'WIDGET';\nconst format = 'widget-workspace';\n",
                 'ui/main.tsx': 'const ORYVA = 1; const WIDGET = 2;\n<h1>WIDGET by Sun</h1>\n<div>{WIDGET}</div>\n',
                 'docs/adr/0001.md': '# WIDGET original decision\n',
                 'decisions/original.md': '# WIDGET original identity\n',
                 'branding/revisions/history.txt': 'WIDGET by Sun',
                 'branding/archive/history.txt': 'WIDGET by Sun'}
        for path, content in files.items():
            target = self.source / path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content)
        subprocess.run(['git', 'init', '-q'], cwd=self.source, check=True)
        subprocess.run(['git', 'add', '.'], cwd=self.source, check=True)
        subprocess.run(['git', '-c', 'user.name=test', '-c', 'user.email=test@example.invalid',
                        'commit', '-qm', 'fixture'], cwd=self.source, check=True)
        self.scans = []

    def tearDown(self):
        self.temp.cleanup()

    def scanner(self, repo, branch, head, destination):
        self.scans.append(repo)
        shutil.copytree(self.source, destination)
        if repo != 'sunstriker2009/sun-foundry':
            subprocess.run(['git', 'rm', '-qr', 'registry'], cwd=destination, check=True)
            subprocess.run(['git', '-c', 'user.name=test', '-c', 'user.email=test@example.invalid',
                            'commit', '-qm', 'fixture without registry'], cwd=destination, check=True)

    def build(self, api=None, **options):
        return product.make_plan(api or API(), 'sun-widget', 'GATEHOUSE', scanner=self.scanner, **options)

    def test_plan_reads_only_target_and_governance(self):
        api = API()
        plan = self.build(api)
        expected = ['sun-widget', 'sun-strata', 'sun-foundry', 'sun-ecosystem']
        self.assertEqual(plan['scope'], expected)
        self.assertEqual(self.scans, ['sunstriker2009/' + name for name in expected])
        self.assertTrue(all(method == 'GET' for method, _, _ in api.calls))
        self.assertFalse(any('/user/' in endpoint or endpoint.endswith('/repos') for _, endpoint, _ in api.calls))

    def test_registry_identity_technical_names_and_history_are_preserved(self):
        plan = self.build()
        changes = {c['path']: c['content'] for c in next(r['changes'] for r in plan['repositories'] if r['name'] == 'sun-foundry')}
        entry = json.loads(changes['registry/products.json'])['products'][0]
        self.assertEqual(entry['name'], 'GATEHOUSE')
        self.assertEqual(entry['publicName'], 'GATEHOUSE by Sun')
        self.assertEqual(entry['id'], 'SUN-P001')
        self.assertEqual(entry['namespace'], 'Sun.Widget')
        self.assertEqual(entry['backendPackages'], 'Sun.Widget.*')
        self.assertEqual(entry['frontendPackages'], '@sun-widget/*')
        self.assertEqual(entry['tagline'], 'Work. Together.')
        self.assertEqual(entry['repository'], 'sun-widget')
        self.assertEqual(entry['supersedes'], 'WIDGET')
        self.assertEqual(entry['previousNames'], ['ANCIENT', 'WIDGET'])
        self.assertNotIn('decisions/original.md', changes)
        self.assertNotIn('docs/adr/0001.md', changes)
        self.assertIn('GATEHOUSE', changes['registry/GALLERY.md'])
        operational = json.loads(changes['registry/product-catalog.json'])['products'][0]
        self.assertEqual((operational['name'], operational['previousNames']), ('GATEHOUSE', ['ANCIENT', 'WIDGET']))
        self.assertIn('decisions/product-renames/sun-p001-gatehouse.md',
                      [c['path'] for c in plan['repositories'][-1]['changes']])

    def test_resolves_family_ids_and_legacy_product_ids(self):
        authority = json.loads((self.source / 'registry/products.json').read_text())
        entry = authority['products'][0]
        for ident in ('SUN-001', 'SUN-P001', 'SUN-C001'):
            with self.subTest(ident=ident):
                entry['id'] = ident
                result = product.resolve_product(authority, 'sun-widget', 'sun-widget', 'GATEHOUSE')
                self.assertEqual(result['id'], ident)
        self.assertEqual(product.resolve_product(authority, 'sun-foundry', 'sun-foundry', 'GATEHOUSE')['id'],
                         'SUN-G003')
        entry['id'] = 'SUN-G001'
        with self.assertRaisesRegex(ValueError, 'stable SUN ID'):
            product.resolve_product(authority, 'sun-widget', 'sun-widget', 'GATEHOUSE')

    def test_product_only_execute_never_renames_repository(self):
        api = API()
        plan = self.build(api)
        report = {}
        product.repository.apply_plan(api, plan, report)
        self.assertFalse(report['renamed'])
        self.assertFalse(any(method == 'PATCH' for method, _, _ in api.calls))
        self.assertEqual(len(report['pullRequests']), 4)

    def test_cli_plan_is_read_only_and_execute_automatically_proposes(self):
        for operation in ['plan', 'execute']:
            api = API()
            output = self.root / operation
            argv = ['rename-product.py', '--repository', 'sun-widget', '--new-name', 'GATEHOUSE',
                    '--operation', operation, '--output', str(output)]
            with patch.object(product.repository, 'GitHub', return_value=api), \
                 patch.object(product.repository, 'checkout_snapshot', side_effect=self.scanner), \
                 patch.object(sys, 'argv', argv):
                self.assertEqual(product.main(), 0)
            result = json.loads((output / 'result.json').read_text())
            self.assertEqual(result['status'], 'planned' if operation == 'plan' else 'proposed')
            self.assertFalse(result['renamed'])
            self.assertEqual(json.loads((output / 'plan.json').read_text())['kind'], 'product-rename')
            if operation == 'plan':
                self.assertTrue(all(method == 'GET' for method, _, _ in api.calls))

    def test_invalid_product_source_identity_prevents_any_writes(self):
        api = API()
        plan = self.build(api)
        plan['sourceId'] = 999
        api.calls.clear()
        with self.assertRaises(ValueError):
            product.repository.apply_plan(api, plan, {})
        self.assertEqual(api.calls, [])

    def test_optional_repository_rename_uses_same_engine_and_exact_scope(self):
        api = API()
        plan = self.build(api, rename_repo=True, new_repository='sun-next')
        report = {}
        product.repository.apply_plan(api, plan, report)
        self.assertTrue(report['renamed'])
        writes = [(endpoint, data) for method, endpoint, data in api.calls if method == 'PATCH']
        self.assertEqual(writes, [('repos/sunstriker2009/sun-widget', {'name': 'sun-next'})])
        entries = [r for r in plan['repositories'] if r['name'] == 'sun-foundry'][0]
        registry = json.loads(next(c['content'] for c in entries['changes'] if c['path'] == 'registry/products.json'))
        self.assertEqual(registry['products'][0]['repository'], 'sun-next')
        self.assertEqual(len(report['pullRequests']), 4)

    def test_write_failure_stops_optional_repository_rename(self):
        api = API()
        api.deny = 'sun-foundry'
        plan = self.build(api, rename_repo=True, new_repository='sun-next')
        with self.assertRaises(product.repository.ApiError):
            product.repository.apply_plan(api, plan, {})
        self.assertFalse(api.renamed)
        self.assertFalse(any(method == 'PATCH' for method, _, _ in api.calls))

    def test_source_identifiers_profile_and_jsx_expressions_are_untouched(self):
        changes = {c['path']: c['content'] for c in self.build()['repositories'][0]['changes']}
        code = changes['desktop/main.mjs']
        self.assertIn("app.setName('GATEHOUSE by Sun')", code)
        self.assertIn("'/WIDGET by Sun'", code)
        self.assertIn("const format = 'widget-workspace'", code)
        self.assertIn('<h1>GATEHOUSE by Sun</h1>', changes['ui/main.tsx'])
        self.assertIn('<div>{WIDGET}</div>', changes['ui/main.tsx'])
        self.assertIn('const WIDGET = 2', changes['ui/main.tsx'])

    def test_product_rename_rejects_stale_optional_inputs(self):
        with self.assertRaises(ValueError):
            self.build(new_repository='sun-next')
        with self.assertRaises(ValueError):
            self.build(rename_repo=True)

    def test_governance_target_is_scanned_once(self):
        plan = product.make_plan(API(), 'sun-foundry', 'OUTPOST', scanner=self.scanner)
        self.assertEqual(plan['scope'], ['sun-foundry', 'sun-strata', 'sun-ecosystem'])
        self.assertEqual(len(set(self.scans)), 3)

    def test_invalid_names_and_legacy_alias_are_rejected(self):
        for value in ['x', 'Bad/Name', 'Bad;Name', 'GATEHOUSE by Sun']:
            with self.assertRaises(ValueError):
                product.product_name(value)
        with self.assertRaises(ValueError):
            product.make_plan(API(), 'sun-widget', 'ANCIENT', scanner=self.scanner)

    def test_unconfirmed_or_ambiguous_registry_entries_are_rejected(self):
        authority = json.loads((self.source / 'registry/products.json').read_text())
        authority['products'][0]['status'] = 'PENDING'
        with self.assertRaises(ValueError):
            product.resolve_product(authority, 'sun-widget', 'sun-widget', 'GATEHOUSE')
        authority['products'][0]['status'] = 'CONFIRMED'
        authority['products'].append(dict(authority['products'][0]))
        with self.assertRaises(ValueError):
            product.resolve_product(authority, 'sun-widget', 'sun-widget', 'GATEHOUSE')

    def test_markdown_code_and_qualified_names_are_not_rewritten(self):
        text = '# WIDGET by Sun\n`WIDGET_KEY` `Sun.WIDGET` `widget-workspace`\n[WIDGET](https://github.com/org/WIDGET)'
        updated = product.prose(text, 'WIDGET', 'GATEHOUSE')
        self.assertIn('# GATEHOUSE by Sun', updated)
        self.assertIn('`WIDGET_KEY` `Sun.WIDGET` `widget-workspace`', updated)
        self.assertIn('[GATEHOUSE](https://github.com/org/WIDGET)', updated)


if __name__ == '__main__':
    unittest.main()
