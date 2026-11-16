import datetime as dt
import importlib.util
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

SPEC = importlib.util.spec_from_file_location('rename', Path(__file__).resolve().parents[1] / 'scripts/rename-repository.py')
rename = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(rename)


def plan():
    return {'schemaVersion': 1, 'old': 'sun-old', 'new': 'sun-new', 'sourceId': 7,
            'createdAt': dt.datetime.now(dt.timezone.utc).isoformat(),
            'workflowCommit': '', 'scope': ['sun-old', 'sun-ecosystem'],
            'repositories': [
                {'name': name, 'id': identity, 'branch': 'main', 'head': 'base', 'tree': 'base-tree',
                 'changes': [{'path': 'README.md', 'mode': '100644', 'before': 'old-blob', 'content': 'new'}]}
                for name, identity in [('sun-old', 7), ('sun-ecosystem', 8)]]}


class FakeAPI:
    def __init__(self):
        self.renamed = False
        self.head = 'base'
        self.calls = []
        self.refs = {}
        self.prs = {}
        self.conflict = False

    def call(self, endpoint, method='GET', data=None, missing=False):
        self.calls.append((method, endpoint, data))
        name, _, resource = endpoint.removeprefix('repos/sunstriker2009/').partition('/')
        if not resource:
            if name == 'sun-new' and not self.renamed:
                return None
            if method == 'PATCH':
                self.renamed = True
                name = data['name']
            if name == 'sun-old' and self.renamed:
                name = 'sun-new'
            return {'id': 8 if name == 'sun-ecosystem' else 7, 'full_name': f'sunstriker2009/{name}',
                    'default_branch': 'main', 'archived': False}
        if resource == 'git/ref/heads/main':
            return {'object': {'sha': self.head}}
        if resource.startswith('git/ref/heads/'):
            if self.conflict:
                return {'object': {'sha': 'unrelated'}}
            return {'object': {'sha': 'proposed'}} if name in self.refs else None
        if resource.startswith('git/commits/'):
            return {'message': 'unrelated' if self.conflict else 'chore: update references for sun-old -> sun-new',
                    'parents': [{'sha': 'base'}], 'tree': {'sha': 'proposed-tree'}}
        if resource == 'git/trees':
            return {'sha': 'proposed-tree'}
        if resource.startswith('git/trees/'):
            content = b'new'
            digest = rename.hashlib.sha1(b'blob 3\0' + content).hexdigest()
            return {'tree': [{'path': 'README.md', 'mode': '100644', 'type': 'blob',
                              'sha': digest if 'proposed-tree' in resource else 'old-blob'}]}
        if resource == 'git/commits':
            return {'sha': 'proposed'}
        if resource == 'git/refs':
            self.refs[name] = data['sha']
            return {}
        if resource.startswith('pulls?'):
            return [self.prs[name]] if name in self.prs else []
        if resource == 'pulls':
            self.prs[name] = {'html_url': f'https://github.com/{name}/pull/1', 'state': 'open'}
            return self.prs[name]
        raise AssertionError(endpoint)


class RenameTests(unittest.TestCase):
    def test_repository_rename_refreshes_generated_gallery_order(self):
        source = ('header\n<!-- SUN-REPOSITORY-GALLERY:START -->\n<table>\n<tr>\n'
                  '<td><a href="https://github.com/sunstriker2009/sun-alpha">Product</a></td>\n'
                  '<td><a href="https://github.com/sunstriker2009/sun-middle">Other</a></td>\n'
                  '</tr>\n</table>\n<!-- SUN-REPOSITORY-GALLERY:END -->\nfooter')
        result = rename.refresh_gallery(rename.rewrite(source, 'sun-alpha', 'sun-zeta'))
        self.assertLess(result.index('sun-middle'), result.index('sun-zeta'))
        self.assertEqual(rename.refresh_gallery(result), result)
        self.assertTrue(result.startswith('header\n'))
        self.assertTrue(result.endswith('\nfooter'))

    def test_reference_boundaries(self):
        text = 'https://github.com/sunstriker2009/sun-old.git\nuses: sunstriker2009/sun-old/actions/install@abc\nrepository: "sun-old"\n  - sun-old\nbranding/registry/sun-old.png\nhttps://github.com/sunstriker2009/sun-old-extra\n'
        updated = rename.rewrite(text, 'sun-old', 'sun-new')
        self.assertIn('sunstriker2009/sun-new.git', updated)
        self.assertIn('sunstriker2009/sun-new/actions/install@abc', updated)
        self.assertIn('repository: "sun-new"', updated)
        self.assertIn('  - sun-new\n', updated)
        self.assertIn('branding/registry/sun-old.png', updated)
        self.assertIn('sunstriker2009/sun-old-extra', updated)

    def test_scan_preserves_history_binaries_and_symlinks(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            subprocess.run(['git', 'init', '-q', str(root)], check=True)
            files = {'README.md': b'"sun-old"\r\n', 'branding/revisions/v1.zip': b'"sun-old"',
                     'branding/archive/old.md': b'"sun-old"', 'binary.bin': b'\x00"sun-old"',
                     'large.txt': b'x' * (rename.MAX_TEXT + 1)}
            for name, content in files.items():
                path = root / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(content)
            (root / 'link').symlink_to('README.md')
            subprocess.run(['git', 'add', '.'], cwd=root, check=True)
            subprocess.run(['git', '-c', 'user.name=test', '-c', 'user.email=test@example.invalid',
                            'commit', '-qm', 'fixture'], cwd=root, check=True)
            changes, _, skipped = rename.scan_checkout(root, 'sun-old', 'sun-new')
            self.assertEqual([c['path'] for c in changes], ['README.md'])
            self.assertEqual(changes[0]['content'], '"sun-new"\r\n')
            self.assertEqual(set(skipped), {'link', 'large.txt'})

    def test_invalid_names(self):
        for name in ['../evil', 'other/repo', 'Repo', ' repo', 'repo.git', '-repo', 'a;echo']:
            with self.assertRaises(ValueError):
                rename.short(name)

    @patch.dict(os.environ, {'GITHUB_SHA': ''})
    def test_reviewed_plan_validation(self):
        p = plan()
        rename.validate_plan(p, 'sun-old', 'sun-new', p['scope'], 'sun-old -> sun-new')
        for change in [{'workflowCommit': 'stale'}, {'sourceId': 999}, {'scope': ['foreign']},
                       {'createdAt': '2000-01-01T00:00:00+00:00'}, {'new': 'another'}]:
            with self.assertRaises(ValueError):
                rename.validate_plan(dict(p, **change), 'sun-old', 'sun-new', p['scope'], 'sun-old -> sun-new')
        with self.assertRaises(ValueError):
            rename.validate_plan(p, 'sun-old', 'sun-new', p['scope'], '')

    def test_stale_head_refuses_before_any_write(self):
        api = FakeAPI()
        api.head = 'changed'
        with self.assertRaises(ValueError):
            rename.apply_plan(api, plan(), {})
        self.assertTrue(all(method == 'GET' for method, _, _ in api.calls))

    def test_collision_refuses_before_any_write(self):
        api = FakeAPI()
        api.renamed = True
        p = plan()
        p['sourceId'] = 999
        with self.assertRaises(ValueError):
            rename.apply_plan(api, p, {})
        self.assertTrue(all(method == 'GET' for method, _, _ in api.calls))

    def test_branch_conflict_refuses_before_rename(self):
        api = FakeAPI()
        api.conflict = True
        with self.assertRaises(ValueError):
            rename.apply_plan(api, plan(), {})
        self.assertTrue(all(method == 'GET' for method, _, _ in api.calls))

    def test_apply_and_retry_never_write_main_or_duplicate_pr(self):
        api = FakeAPI()
        report = {}
        rename.apply_plan(api, plan(), report)
        self.assertTrue(report['renamed'])
        self.assertEqual(len(report['pullRequests']), 2)
        rename.apply_plan(api, plan(), {})
        writes = [(method, endpoint, data) for method, endpoint, data in api.calls if method != 'GET']
        self.assertEqual(sum(method == 'PATCH' for method, _, _ in writes), 1)
        self.assertEqual(sum(endpoint.endswith('/pulls') for _, endpoint, _ in writes), 2)
        refs = [data['ref'] for _, endpoint, data in writes if endpoint.endswith('/git/refs')]
        self.assertEqual(len(refs), 2)
        self.assertTrue(all(ref.startswith('refs/heads/chore/rename-') for ref in refs))

    def test_controller_rename_is_blocked(self):
        api = FakeAPI()
        with self.assertRaises(ValueError):
            rename.make_plan(api, 'sun-foundry', 'new-name', ['sun-foundry'])
        self.assertEqual(api.calls, [])

    def test_plan_is_read_only_and_supports_interrupted_rename(self):
        def scanner(repo, branch, head, directory):
            directory.mkdir()
            subprocess.run(['git', 'init', '-q'], cwd=directory, check=True)
            (directory / 'README.md').write_text('https://github.com/sunstriker2009/sun-old')
            subprocess.run(['git', 'add', '.'], cwd=directory, check=True)
            subprocess.run(['git', '-c', 'user.name=test', '-c', 'user.email=test@example.invalid',
                            'commit', '-qm', 'fixture'], cwd=directory, check=True)
        for recovering in [False, True]:
            api = FakeAPI()
            api.renamed = recovering
            result = rename.make_plan(api, 'sun-old', 'sun-new', ['sun-old', 'sun-ecosystem'], scanner)
            self.assertEqual(result['alreadyRenamed'], recovering)
            self.assertEqual(result['sourceId'], 7)
            self.assertEqual(len(result['repositories']), 2)
            self.assertTrue(all(method == 'GET' for method, _, _ in api.calls))

    def test_modified_retry_branch_refuses_before_mutation(self):
        api = FakeAPI()
        api.refs['sun-old'] = 'proposed'
        p = plan()
        p['repositories'][0]['changes'][0]['content'] = 'different proposal'
        with self.assertRaises(ValueError):
            rename.apply_plan(api, p, {})
        self.assertTrue(all(method == 'GET' for method, _, _ in api.calls))

    def test_all_content_writes_are_checked_before_rename(self):
        class Denied(FakeAPI):
            def call(self, endpoint, method='GET', data=None, missing=False):
                if endpoint == 'repos/sunstriker2009/sun-ecosystem/git/trees' and method == 'POST':
                    self.calls.append((method, endpoint, data))
                    raise rename.ApiError(403, endpoint)
                return super().call(endpoint, method, data, missing)
        api = Denied()
        with self.assertRaises(rename.ApiError):
            rename.apply_plan(api, plan(), {})
        self.assertFalse(api.renamed)
        self.assertFalse(any(method == 'PATCH' or endpoint.endswith('/git/refs')
                             for method, endpoint, _ in api.calls))

    def test_head_drift_during_object_preparation_stops_rename(self):
        class Drift(FakeAPI):
            def call(self, endpoint, method='GET', data=None, missing=False):
                result = super().call(endpoint, method, data, missing)
                if endpoint.endswith('/git/commits') and method == 'POST':
                    self.head = 'changed'
                return result
        api = Drift()
        with self.assertRaises(ValueError):
            rename.apply_plan(api, plan(), {})
        self.assertFalse(api.renamed)

    @patch.dict(os.environ, {'GITHUB_SHA': ''})
    def test_execute_uses_generated_plan_without_confirmation_or_run_id(self):
        p = plan()
        for entry in p['repositories']:
            entry.update(retained=[], skipped=[])
            for change in entry['changes']:
                change['diff'] = 'fixture diff\n'
        for operation in ['execute', 'plan']:
            api = FakeAPI()
            with tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary)
                (root / 'config').mkdir()
                (root / 'config/workflow-repositories.json').write_text(
                    rename.json.dumps({'repositories': p['scope']}))
                output = root / 'output'
                argv = ['rename-repository.py', '--operation', operation, '--repository', p['old'],
                        '--new-name', p['new'], '--output', str(output)]
                with patch.object(rename, 'ROOT', root), patch.object(rename, 'GitHub', return_value=api), \
                     patch.object(rename, 'make_plan', return_value=p), patch.object(sys, 'argv', argv):
                    self.assertEqual(rename.main(), 0)
                self.assertEqual(rename.json.loads((output / 'plan.json').read_text()), p)
                result = rename.json.loads((output / 'result.json').read_text())
                self.assertEqual(result['status'], 'proposed' if operation == 'execute' else 'planned')
                self.assertEqual(api.renamed, operation == 'execute')
                if operation == 'plan':
                    self.assertEqual(api.calls, [])


if __name__ == '__main__':
    unittest.main()

