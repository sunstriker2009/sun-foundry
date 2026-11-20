#!/usr/bin/env python3
"""Install one pending revision ZIP and fast-forward the same feature branch."""
import argparse
import importlib.util
import json
import os
from pathlib import Path
import re
import subprocess
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
VERSION = re.compile(r'v[1-9][0-9]*\.zip')
UPLOAD = re.compile(r'[A-Za-z0-9][A-Za-z0-9._-]{0,119}\.zip')


def git(root, *args, env=None):
    return subprocess.check_output(['git', *args], cwd=root, env=env, text=True).strip()


def pending(root):
    directory = Path(root) / 'branding/revisions'
    if directory.is_symlink() or (Path(root) / 'branding').is_symlink():
        raise ValueError('Symlinked branding paths are unsupported')
    candidates = sorted(p for p in directory.glob('*.zip') if not VERSION.fullmatch(p.name))
    if any(not UPLOAD.fullmatch(p.name) or p.is_symlink() or not p.is_file() for p in candidates):
        raise ValueError('Upload a regular ZIP with a simple basename')
    if len(candidates) > 1:
        raise ValueError('Commit one pending ZIP at a time; remove other pending ZIPs before retrying')
    return candidates[0] if candidates else None


def guard(repository, branch, expected):
    if not re.fullmatch(r'sunstriker2009/[a-z0-9][a-z0-9._-]*', repository):
        raise ValueError('Repository is outside the SUN owner scope')
    if not branch or branch == 'main' or branch.startswith('-') or '\n' in branch:
        raise ValueError('Use a feature branch; protected main stays PR-only')
    if not re.fullmatch(r'[0-9a-f]{40}', expected):
        raise ValueError('Expected an exact triggering commit SHA')


REGISTRY_OWNER = 'sunstriker2009/sun-foundry'
REGISTRY_URL = f'https://raw.githubusercontent.com/{REGISTRY_OWNER}/main/registry/repositories.json'


def read_registry():
    with urllib.request.urlopen(REGISTRY_URL, timeout=15) as response:
        return json.loads(response.read(1_000_001))


def require_registration(repository):
    registry = read_registry()
    if registry.get('schemaVersion') != 1 or not isinstance(registry.get('repositories'), list):
        raise ValueError('Unsupported SUN repository registry schema')
    # The SUN parent brand is intentionally omitted from the gallery catalog.
    if repository == 'sunstriker2009/sun-ecosystem':
        return
    matches = [row for row in registry['repositories'] if row.get('repository') == repository]
    patterns = {'product': r'SUN-[PC]?[0-9]{3}', 'infrastructure': r'SUN-G[0-9]{3}'}
    row = matches[0] if len(matches) == 1 else {}
    pattern = patterns.get(row.get('classification'))
    ident = row.get('registryId')
    if pattern is None or not isinstance(ident, str) or not re.fullmatch(pattern, ident):
        raise ValueError('Repository needs a confirmed registration in the Foundry registry')


def output(**values):
    if os.getenv('GITHUB_OUTPUT'):
        with open(os.environ['GITHUB_OUTPUT'], 'a') as stream:
            for key, value in values.items():
                stream.write(f'{key}={str(value).lower() if isinstance(value, bool) else value}\n')


def install_branch(root, repository, branch, expected):
    guard(repository, branch, expected)
    root = Path(root).resolve()
    if git(root, 'rev-parse', 'HEAD') != expected or git(root, 'status', '--porcelain'):
        raise ValueError('Installation requires a clean checkout of the triggering commit')
    source = pending(root)
    if source is None:
        return {'installed': False, 'reason': 'No unnumbered revision ZIP; snapshots are ignored'}
    require_registration(repository)
    # Load Pillow and the shared validator only once a candidate is present.
    spec = importlib.util.spec_from_file_location('installer', ROOT / 'scripts/install-branding.py')
    installer = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(installer)
    report = installer.install_with_revision(root, source, apply=True)
    if not report['changed']:
        return {'installed': False, 'reason': 'Already identical; upload retained'}
    git(root, 'add', '-f', '--', 'branding/assets', 'branding/revisions')
    changed = git(root, 'diff', '--cached', '--name-only', '-z').split('\0')
    if any(p and not p.startswith(('branding/assets/', 'branding/revisions/')) for p in changed):
        raise ValueError('Unexpected installation diff')
    git(root, '-c', 'user.name=sun-foundry[bot]', '-c',
        'user.email=41898282+github-actions[bot]@users.noreply.github.com',
        'commit', '-qm', f"chore(branding): install {report['revision']} from {source.name}")
    # checkout supplies a short-lived GITHUB_TOKEN header only for the push.
    live = git(root, 'ls-remote', 'origin', 'refs/heads/' + branch).split()
    if not live or live[0] != expected:
        raise ValueError('Branch advanced during installation; no push made. Retry at the new tip')
    git(root, 'push', 'origin', 'HEAD:refs/heads/' + branch)
    return {'installed': True, 'revision': report['revision'], 'commit': git(root, 'rev-parse', 'HEAD')}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repository-root', type=Path, required=True)
    parser.add_argument('--detect', action='store_true')
    args = parser.parse_args()
    guard(os.environ['GITHUB_REPOSITORY'], os.environ['GITHUB_REF_NAME'], os.environ['GITHUB_SHA'])
    if args.detect:
        found = pending(args.repository_root) is not None
        output(has_upload=found)
        print('Pending branding ZIP detected' if found else 'No pending ZIP; numbered snapshots ignored')
        return
    report = install_branch(args.repository_root, os.environ['GITHUB_REPOSITORY'],
                            os.environ['GITHUB_REF_NAME'], os.environ['GITHUB_SHA'])
    output(**report)
    print(json.dumps(report, indent=2))
    if os.getenv('GITHUB_STEP_SUMMARY'):
        with open(os.environ['GITHUB_STEP_SUMMARY'], 'a') as stream:
            stream.write('## Branding branch installation\n\n```json\n' + json.dumps(report, indent=2) + '\n```\n')


if __name__ == '__main__':
    main()
