import importlib.util
from pathlib import Path
import subprocess
import tempfile
import os
import textwrap
import unittest
from unittest.mock import patch

from test_branding_installer import installer, package

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location('branch_installer', ROOT / 'scripts/install-branding-branch.py')
branch = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(branch)


class BranchInstallerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        root = Path(self.temp.name)
        self.remote = root / 'remote.git'
        self.repo = root / 'checkout'
        subprocess.run(['git', 'init', '-q', '--bare', str(self.remote)], check=True)
        subprocess.run(['git', 'init', '-q', '-b', 'branding/pilot', str(self.repo)], check=True)
        self.revisions = self.repo / 'branding/revisions'
        self.revisions.mkdir(parents=True)
        self.upload = self.revisions / 'my-package.zip'
        self.upload.write_bytes(package())
        (self.repo / 'README.md').write_text('Keep product introduction')
        branch.git(self.repo, 'config', 'user.name', 'Test')
        branch.git(self.repo, 'config', 'user.email', 'test@example.com')
        branch.git(self.repo, 'add', '.')
        branch.git(self.repo, 'commit', '-qm', 'Upload')
        branch.git(self.repo, 'remote', 'add', 'origin', str(self.remote))
        branch.git(self.repo, 'push', '-q', 'origin', 'HEAD')
        self.sha = branch.git(self.repo, 'rev-parse', 'HEAD')

    def apply(self):
        return branch.install_branch(self.repo, 'sunstriker2009/sun-astelvo', 'branding/pilot', self.sha)

    def test_follow_up_commit_on_same_branch_consumes_upload_and_ignores_versions(self):
        result = self.apply()
        self.assertTrue(result['installed'])
        self.assertEqual(result['revision'], 'v2.zip')
        self.assertEqual(branch.git(self.repo, 'rev-parse', 'HEAD^'), self.sha)
        self.assertEqual(branch.git(self.repo, 'ls-remote', 'origin', 'refs/heads/branding/pilot').split()[0], result['commit'])
        self.assertFalse(self.upload.exists())
        self.assertTrue((self.revisions / 'v1.zip').exists())
        self.assertTrue((self.revisions / 'v2.zip').exists())
        self.assertIsNone(branch.pending(self.repo))
        self.assertFalse(branch.install_branch(self.repo, 'sunstriker2009/sun-astelvo',
                                               'branding/pilot', result['commit'])['installed'])
        self.assertEqual((self.repo / 'README.md').read_text(), 'Keep product introduction')

    def test_invalid_upload_creates_no_commit_or_version(self):
        self.upload.write_bytes(b'invalid ZIP')
        branch.git(self.repo, 'add', '.')
        branch.git(self.repo, 'commit', '-qm', 'Bad package')
        self.sha = branch.git(self.repo, 'rev-parse', 'HEAD')
        with self.assertRaises(Exception):
            self.apply()
        self.assertEqual(branch.git(self.repo, 'rev-parse', 'HEAD'), self.sha)
        self.assertEqual(list(self.revisions.iterdir()), [self.upload])

    def test_multiple_pending_zips_fail_before_any_install(self):
        (self.revisions / 'another.zip').write_bytes(package('red'))
        with self.assertRaises(ValueError):
            branch.pending(self.repo)
        self.assertFalse((self.revisions / 'v1.zip').exists())

    def test_rejects_main_unknown_repository_dirty_checkout_and_wrong_tip(self):
        for repository, name, sha in [('sunstriker2009/sun-astelvo', 'main', self.sha),
                                     ('other/sun-astelvo', 'branding/pilot', self.sha),
                                     ('sunstriker2009/sun-astelvo', 'branding/pilot', '0' * 40)]:
            with self.assertRaises(ValueError):
                branch.install_branch(self.repo, repository, name, sha)
        (self.repo / 'unrelated.txt').write_text('uncommitted')
        with self.assertRaises(ValueError):
            self.apply()

    def test_advanced_remote_never_overwritten(self):
        original = branch.git
        def changed_tip(root, *args, **kwargs):
            if args[:1] == ('ls-remote',):
                return '0' * 40 + '\trefs/heads/branding/pilot'
            return original(root, *args, **kwargs)
        with patch.object(branch, 'git', side_effect=changed_tip):
            with self.assertRaises(ValueError):
                self.apply()
        self.assertEqual(original(self.repo, 'ls-remote', 'origin', 'refs/heads/branding/pilot').split()[0], self.sha)

    def test_numbered_zip_is_not_an_upload_and_cannot_be_overwritten(self):
        self.apply()
        history = self.revisions / 'v2.zip'
        before = history.read_bytes()
        with self.assertRaises(ValueError):
            installer.install(self.repo, history, apply=True)
        self.assertEqual(history.read_bytes(), before)

    def test_action_dispatches_checks_only_for_an_existing_pr(self):
        action = (ROOT / 'actions/install-branding-zip/action.yml').read_text()
        shell = textwrap.dedent(action.split('      run: |\n', 1)[1])
        tool = Path(self.temp.name) / 'bin'
        tool.mkdir()
        gh = tool / 'gh'
        gh.write_text('#!/bin/bash\nif [[ "$1 $2" == "pr list" ]]; then echo "$PR_COUNT"; else echo "$*" >> "$CALL_LOG"; fi\n')
        gh.chmod(0o755)
        log = tool / 'calls'
        env = dict(os.environ, PATH=str(tool) + ':' + os.environ['PATH'], CALL_LOG=str(log),
                   GITHUB_REPOSITORY='sunstriker2009/sun-astelvo', GITHUB_REF_NAME='branding/pilot',
                   VALIDATION_WORKFLOWS='ci.yml,pr-title.yml')
        for count, expected in [('0', 0), ('1', 2)]:
            log.write_text('')
            result = subprocess.run(['bash', '-c', shell], env=dict(env, PR_COUNT=count),
                                    capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(len(log.read_text().splitlines()), expected)
        result = subprocess.run(['bash', '-c', shell], env=dict(env, PR_COUNT='1',
                                VALIDATION_WORKFLOWS=''), capture_output=True)
        self.assertNotEqual(result.returncode, 0)
        result = subprocess.run(['bash', '-c', shell], env=dict(env, PR_COUNT='1',
                                VALIDATION_WORKFLOWS='../bad.yml'), capture_output=True)
        self.assertNotEqual(result.returncode, 0)

    def test_detect_rejects_symlinked_upload(self):
        self.upload.unlink()
        self.upload.symlink_to(self.repo / 'README.md')
        with self.assertRaises(ValueError):
            branch.pending(self.repo)


if __name__ == '__main__':
    unittest.main()
