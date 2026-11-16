#!/usr/bin/env python3
"""Preview a target-main ZIP or propose its asset-only installation via a PR."""
import argparse
import base64
import importlib.util
import json
import os
from pathlib import Path
import re
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location('installer', ROOT / 'scripts/install-branding.py')
installer = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(installer)
BRANCH = 'chore/branding-install'


def run(*args, cwd=None, env=None):
    return subprocess.check_output(args, cwd=cwd, env=env, text=True).strip()


def validate(repository, confirmation, operation, filename, revision):
    allowed = json.loads((ROOT / 'config/workflow-repositories.json').read_text())['repositories']
    if repository not in [f'sunstriker2009/{name}' for name in allowed]:
        raise ValueError('Repository must be in the SUN dropdown')
    if operation not in ('preview', 'apply'):
        raise ValueError('Invalid operation')
    if operation == 'apply' and confirmation != repository:
        raise ValueError('Apply requires matching repository confirmation')
    if revision:
        if not re.fullmatch(r'v[1-9][0-9]*\.zip', revision):
            raise ValueError('Rollback revision must be v1.zip, v2.zip, ...')
        return 'branding/revisions/' + revision
    if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._-]{0,119}\.zip', filename):
        raise ValueError('Supply a ZIP basename from branding/inbox, without directories')
    return 'branding/inbox/' + filename


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repository', required=True)
    parser.add_argument('--confirm', default='')
    parser.add_argument('--operation', choices=('preview', 'apply'), default='preview')
    parser.add_argument('--filename', default='branding.zip')
    parser.add_argument('--rollback-revision', default='')
    args = parser.parse_args()
    args.filename = args.filename.strip()
    args.rollback_revision = args.rollback_revision.strip()
    relative = validate(args.repository, args.confirm, args.operation, args.filename, args.rollback_revision)
    if not os.environ.get('GH_TOKEN'):
        raise ValueError('Missing GH_TOKEN')
    # Keep credentials out of clone URLs, persisted git config and error messages.
    auth = base64.b64encode(('x-access-token:' + os.environ['GH_TOKEN']).encode()).decode()
    git_env = dict(os.environ, GIT_CONFIG_COUNT='1', GIT_CONFIG_KEY_0='http.extraheader',
                   GIT_CONFIG_VALUE_0='AUTHORIZATION: basic ' + auth, GIT_TERMINAL_PROMPT='0')
    with tempfile.TemporaryDirectory() as directory:
        repo = Path(directory) / 'target'
        run('git', 'clone', '--quiet', '--single-branch', '--branch', 'main',
            f'https://github.com/{args.repository}.git', str(repo), env=git_env)
        base = run('git', 'rev-parse', 'HEAD', cwd=repo)
        report = installer.install(repo, repo / relative, bool(args.rollback_revision), apply=False)
        print(json.dumps(report, indent=2))
        summary = ['## SUN branding ZIP', f'Target: `{args.repository}`', f'Source: `{relative}`',
                   f'Base: `{base}`', f"Proposed revision: `{report['revision']}`",
                   '', *[f'- `{name}`' for name in report['changed']]]
        if args.operation == 'apply' and report['changed']:
            existing = run('gh', 'api', f'repos/{args.repository}/git/matching-refs/heads/{BRANCH}')
            if json.loads(existing):
                raise ValueError('Existing branding-install branch: review/merge or close/delete it before retrying')
            installer.install(repo, repo / relative, bool(args.rollback_revision), apply=True)
            run('git', 'checkout', '-q', '-b', BRANCH, cwd=repo)
            run('git', 'add', '-f', '--', 'branding/assets', 'branding/revisions', cwd=repo)
            if not args.rollback_revision:
                run('git', 'add', '--', relative, cwd=repo)
            changed = run('git', 'diff', '--cached', '--name-only', cwd=repo).splitlines()
            allowed = ('branding/assets/', 'branding/revisions/')
            if not changed or any(not (p.startswith(allowed) or p == relative) for p in changed):
                raise ValueError('Unexpected installation diff')
            title = f"chore(branding): {report['operation']} {report['revision']}"
            run('git', '-c', 'user.name=sun-foundry[bot]', '-c',
                'user.email=41898282+github-actions[bot]@users.noreply.github.com',
                'commit', '-qm', title, cwd=repo)
            live = json.loads(run('gh', 'api', f'repos/{args.repository}/git/ref/heads/main'))['object']['sha']
            if live != base:
                raise ValueError('Target main changed during preparation; retry against current assets')
            run('git', 'push', '--quiet', 'origin', BRANCH, cwd=repo, env=git_env)
            body = '\n'.join(summary) + ('\n\nReview the banner, symbol and icons before squash merge. '
                    'This PR records immutable asset snapshots; main changes only on merge. '
                    'If branding or revisions change on main, close/delete this branch and prepare a fresh PR. '
                    'After merge, the normal daily/manual symbol reconciliation updates the registry. '
                    'No separate digest approval is required.')
            # If creation fails after push, keep the branch for manual recovery; never force-push it.
            url = run('gh', 'pr', 'create', '--repo', args.repository, '--base', 'main',
                      '--head', BRANCH, '--title', title, '--body', body)
            summary += ['', f'PR: {url}']
            print(url)
        elif not report['changed']:
            summary += ['', 'Already matches: no PR, revision or inbox rename created.']
        else:
            summary += ['', 'Preview only: no branch, revision or PR created.']
        if os.getenv('GITHUB_STEP_SUMMARY'):
            with open(os.environ['GITHUB_STEP_SUMMARY'], 'a') as stream:
                stream.write('\n'.join(summary) + '\n')


if __name__ == '__main__':
    main()
