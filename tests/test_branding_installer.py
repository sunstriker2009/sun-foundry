import importlib.util
from io import BytesIO
import json
from pathlib import Path
import stat
import os
import shutil
import subprocess
import tempfile
import unittest
from unittest.mock import patch
import zipfile

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]


def load(name, filename):
    spec = importlib.util.spec_from_file_location(name, ROOT / 'scripts' / filename)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


installer = load('installer', 'install-branding.py')
proposal = load('proposal', 'propose-branding-install.py')


def png(size, color='navy'):
    stream = BytesIO()
    Image.new('RGBA', size, color).save(stream, format='PNG')
    return stream.getvalue()


def package(color='navy', extra=None, wrapper='export/'):
    files = {'branding/assets/symbol.png': png((128, 128), color),
             'branding/assets/readme-banner.png': png((300, 100), color),
             **{f'branding/assets/icons/icon-{size}.png': png((size, size), color)
                for size in installer.SIZES},
             'README.md': b'Package instructions, not repository README',
             'manifest.json': b'{}'}
    files.update(extra or {})
    stream = BytesIO()
    with zipfile.ZipFile(stream, 'w', zipfile.ZIP_DEFLATED) as archive:
        for name, content in files.items():
            archive.writestr(wrapper + name, content)
    return stream.getvalue()


class InstallerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.assets = self.root / 'branding/assets'
        self.assets.mkdir(parents=True)
        (self.assets / 'old.svg').write_text('<svg/>')
        (self.root / 'branding/archive').mkdir()
        (self.root / 'branding/archive/original.png').write_bytes(b'historical')
        (self.root / 'README.md').write_text('Product intro')
        self.inbox = self.root / 'branding/inbox'
        self.inbox.mkdir()
        self.zip = self.inbox / 'custom-upload.zip'
        self.zip.write_bytes(package())

    def tree(self):
        return {p.relative_to(self.root).as_posix(): p.read_bytes()
                for p in self.root.rglob('*') if p.is_file()}

    def test_preview_is_read_only_and_first_apply_captures_exact_backup(self):
        before = self.tree()
        report = installer.install(self.root, self.zip)
        self.assertEqual(before, self.tree())
        self.assertEqual(report['revision'], 'v2.zip')
        installer.install(self.root, self.zip, apply=True)
        revisions = self.root / 'branding/revisions'
        self.assertEqual(installer.restore_assets((revisions / 'v1.zip').read_bytes()), {'old.svg': b'<svg/>'})
        self.assertEqual(installer.restore_assets((revisions / 'v2.zip').read_bytes()), installer.files_under(self.assets))
        self.assertFalse(self.zip.exists())
        self.assertEqual((self.root / 'README.md').read_text(), 'Product intro')
        self.assertEqual((self.root / 'branding/archive/original.png').read_bytes(), b'historical')
        self.assertFalse((self.assets / 'manifest.json').exists())

    def test_next_revision_then_rollback_appends_and_preserves_history(self):
        installer.install(self.root, self.zip, apply=True)
        revisions = self.root / 'branding/revisions'
        original_v1 = (revisions / 'v1.zip').read_bytes()
        self.zip.write_bytes(package('red'))
        self.assertEqual(installer.install(self.root, self.zip, apply=True)['revision'], 'v3.zip')
        installer.install(self.root, revisions / 'v1.zip', rollback=True, apply=True)
        self.assertEqual(installer.files_under(self.assets), {'old.svg': b'<svg/>'})
        self.assertEqual((revisions / 'v1.zip').read_bytes(), original_v1)
        self.assertEqual(installer.restore_assets((revisions / 'v4.zip').read_bytes()), {'old.svg': b'<svg/>'})
        self.assertEqual(json.loads((revisions / 'current.json').read_text())['revision'], 'v4.zip')

    def test_noop_keeps_upload_and_does_not_allocate_revision(self):
        installer.install(self.root, self.zip, apply=True)
        self.zip.write_bytes(package())
        before = self.tree()
        self.assertIsNone(installer.install(self.root, self.zip, apply=True)['revision'])
        self.assertEqual(before, self.tree())

    def test_replaces_old_icons_preserves_refs(self):
        (self.assets / 'icons').mkdir()
        (self.assets / 'icons/old.ico').write_bytes(b'old')
        (self.assets / 'refs').mkdir()
        (self.assets / 'refs/old.txt').write_text('reference')
        installer.install(self.root, self.zip, apply=True)
        self.assertFalse((self.assets / 'icons/old.ico').exists())
        self.assertTrue((self.assets / 'refs/old.txt').exists())

    def test_invalid_packages_preserve_original_name_and_entire_tree(self):
        bad = [package(extra={'../escape': b'bad'}),
               package(extra={'branding/BRAND-GUIDE.md': b'bad'}),
               package(extra={'branding/assets/icons/icon-32.png': png((24, 24))}),
               package(extra={'branding/assets/symbol.png': b'invalid'}),
               package(extra={'branding/assets/refs/evil.py': b'exec'}),
               package(extra={'branding/assets/SYMBOL.png': png((128, 128))}),
               package(extra={'branding/assets/refs/a.png': png((1, 1)),
                              'branding/assets/refs/a.png/b.png': png((1, 1))}),
               b'not a zip']
        for data in bad:
            with self.subTest(data=data[:20]):
                self.zip.write_bytes(data)
                before = self.tree()
                with self.assertRaises(Exception):
                    installer.install(self.root, self.zip, apply=True)
                self.assertEqual(before, self.tree())

    def test_zip_duplicates_links_and_limits_rejected(self):
        stream = BytesIO()
        with zipfile.ZipFile(stream, 'w') as archive:
            info = zipfile.ZipInfo('link')
            info.external_attr = (stat.S_IFLNK | 0o777) << 16
            archive.writestr(info, '/tmp/elsewhere')
        with self.assertRaises(ValueError):
            installer.read_zip(stream.getvalue())
        with self.assertRaises(ValueError):
            installer.read_zip(package(extra={'branding/assets/SYMBOL.png': b'duplicate'}))
        with patch.object(installer, 'MAX_TOTAL', 5):
            with self.assertRaises(ValueError):
                installer.read_zip(package())
        with patch.object(installer, 'MAX_ZIP', 5):
            with self.assertRaises(ValueError):
                installer.read_zip(package())

    def test_symlink_parent_rejected_without_touching_external_files(self):
        outside = self.root / 'outside'
        outside.mkdir()
        (self.assets / 'refs').symlink_to(outside, target_is_directory=True)
        with self.assertRaises(ValueError):
            installer.install(self.root, self.zip, apply=True)
        self.assertEqual(list(outside.iterdir()), [])

    def test_swap_failure_restores_original_tree_and_version(self):
        before = self.tree()
        replace = installer.os.replace
        def fail_install(source, destination):
            if Path(source).name == 'new':
                raise OSError('simulated swap failure')
            return replace(source, destination)
        with patch.object(installer.os, 'replace', side_effect=fail_install):
            with self.assertRaises(OSError):
                installer.install(self.root, self.zip, apply=True)
        self.assertEqual(before, self.tree())

    def test_revision_gaps_and_rollback_traversal_rejected(self):
        revisions = self.root / 'branding/revisions'
        revisions.mkdir()
        (revisions / 'v2.zip').write_bytes(b'gap')
        with self.assertRaises(ValueError):
            installer.install(self.root, self.zip, apply=True)
        data = BytesIO()
        with zipfile.ZipFile(data, 'w') as archive:
            archive.writestr('README.md', 'outside assets')
        with self.assertRaises(ValueError):
            installer.restore_assets(data.getvalue())

    def test_unwrapped_package_and_optional_png_exports(self):
        files = installer.package_assets(package(wrapper='', extra={
            'branding/assets/icons/icon-192.png': png((192, 192)),
            'branding/assets/social-card.png': png((1200, 630)),
            'branding/assets/refs/master.png': png((256, 256))}))
        self.assertIn('icons/icon-192.png', files)
        self.assertIn('social-card.png', files)

    def test_preview_and_pr_proposal_with_real_git_checkout(self):
        # Exercise clone -> staged diff -> commit -> push -> PR with a local remote.
        # gh is stubbed; no live repository mutation is performed.
        remote = self.root / 'remote'
        remote.mkdir()
        subprocess.run(['git', 'init', '-q', '-b', 'main', str(remote)], check=True)
        shutil.copytree(self.root / 'branding', remote / 'branding')
        (remote / '.gitignore').write_text('branding/revisions/\n')
        subprocess.run(['git', 'add', '.'], cwd=remote, check=True)
        subprocess.run(['git', '-c', 'user.name=Test', '-c', 'user.email=test@example.com',
                        'commit', '-qm', 'fixture'], cwd=remote, check=True)
        base = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=remote, text=True).strip()
        calls = []
        original = proposal.run
        def fake_run(*args, cwd=None, env=None):
            calls.append(args)
            if args[:2] == ('git', 'clone'):
                return original('git', 'clone', '--quiet', '--single-branch', '--branch', 'main',
                                str(remote), args[-1])
            if args[:2] == ('gh', 'api'):
                if 'matching-refs' in args[2]:
                    return '[]'
                return json.dumps({'object': {'sha': base}})
            if args[:3] == ('gh', 'pr', 'create'):
                return 'https://github.com/sunstriker2009/sun-foundry/pull/123'
            # Local remote does not need credentials.
            return original(*args, cwd=cwd)
        common = ['propose', '--repository', 'sunstriker2009/sun-foundry',
                  '--filename', self.zip.name]
        summary = self.root / 'summary.md'
        with patch.object(proposal, 'run', side_effect=fake_run), patch.dict(os.environ,
                {'GH_TOKEN': 'test-token', 'GITHUB_STEP_SUMMARY': str(summary)}):
            with patch('sys.argv', common):
                proposal.main()
            self.assertFalse(any(c[:2] == ('git', 'push') for c in calls))
            with patch('sys.argv', common + ['--operation', 'apply', '--confirm',
                                           'sunstriker2009/sun-foundry']):
                proposal.main()
        files = subprocess.check_output(['git', 'ls-tree', '-r', '--name-only',
                                         proposal.BRANCH], cwd=remote, text=True)
        self.assertIn('branding/revisions/v1.zip', files)
        self.assertIn('branding/revisions/v2.zip', files)
        self.assertNotIn('branding/inbox/custom-upload.zip', files)
        self.assertEqual(subprocess.check_output(['git', 'rev-parse', 'main'],
                                                cwd=remote, text=True).strip(), base)
        self.assertIn('/pull/123', summary.read_text())

    def test_proposal_inputs_restrict_scope_confirmation_and_paths(self):
        self.assertEqual(proposal.validate('sunstriker2009/sun-foundry', '', 'preview', 'branding.zip', ''),
                         'branding/inbox/branding.zip')
        self.assertEqual(proposal.validate('sunstriker2009/sun-foundry', 'sunstriker2009/sun-foundry',
                                          'apply', '', 'v1.zip'), 'branding/revisions/v1.zip')
        cases = [('other/sun-foundry', '', 'preview', 'a.zip', ''),
                 ('sunstriker2009/sun-foundry', '', 'apply', 'a.zip', ''),
                 ('sunstriker2009/sun-foundry', '', 'preview', '../a.zip', ''),
                 ('sunstriker2009/sun-foundry', '', 'preview', '', '../v1.zip')]
        for args in cases:
            with self.assertRaises(ValueError):
                proposal.validate(*args)


if __name__ == '__main__':
    unittest.main()
