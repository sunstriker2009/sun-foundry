#!/usr/bin/env python3
"""Plan a same-owner rename and propose reference updates without writing main."""
import argparse
import base64
import datetime as dt
import difflib
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import tempfile

OWNER = 'sunstriker2009'
CONTROLLER = 'sun-foundry'
ROOT = Path(__file__).resolve().parents[1]
MAX_TEXT = 1_000_000
MAX_PLAN = 12_000_000


def short(value):
    if (not re.fullmatch(r'[a-z0-9][a-z0-9._-]{0,99}', value)
            or value.endswith('.git') or value == 'other-repository'):
        raise ValueError('Use a lowercase short repository name, without owner or .git suffix')
    return value


class ApiError(RuntimeError):
    def __init__(self, status, endpoint):
        self.status = status
        super().__init__(f'GitHub request failed ({status}): {endpoint}')


class GitHub:
    def call(self, endpoint, method='GET', data=None, missing=False):
        command = ['gh', 'api', endpoint, '--method', method]
        if data is not None:
            command += ['--input', '-']
        result = subprocess.run(command, input=json.dumps(data) if data is not None else None,
                                text=True, capture_output=True, timeout=120)
        if result.returncode:
            match = re.search(r'HTTP (\d+)', result.stderr)
            status = int(match[1]) if match else 0
            if missing and status == 404:
                return None
            raise ApiError(status, endpoint)
        return json.loads(result.stdout) if result.stdout.strip() else None


def rewrite(text, old, new):
    # URLs, owner/repo Action references, API paths, git remotes and guards.
    text = re.sub(re.escape(OWNER + '/' + old) + r'(?![A-Za-z0-9_-]|\.(?!git\b))',
                  OWNER + '/' + new, text)
    # Exact quoted configuration keys/values and curated YAML dropdown choices.
    # Keep icon filenames, product names, namespaces and archive paths intact.
    text = re.sub(r'([\'\"])' + re.escape(old) + r'\1',
                  lambda m: m[1] + new + m[1], text)
    text = re.sub(r'(?m)^(\s*-\s+)' + re.escape(old) + r'(\s*(?:#.*)?)$',
                  lambda m: m[1] + new + m[2], text)
    return re.sub(r'(?m)^(\s*[A-Za-z_][\w-]*:\s*)' + re.escape(old) + r'([ \t]*(?:#.*)?)$',
                  lambda m: m[1] + new + m[2], text)


def refresh_gallery(text):
    """Keep generated tile ordering valid when repository URLs change."""
    start, end = '<!-- SUN-REPOSITORY-GALLERY:START -->', '<!-- SUN-REPOSITORY-GALLERY:END -->'
    if text.count(start) != 1 or text.count(end) != 1 or text.index(start) > text.index(end):
        return text
    first, last = text.index(start), text.index(end)
    def table(match):
        cells = re.findall(r'<td\b[^>]*>.*?</td>', match[1], re.S)
        if not cells:
            return match[0]
        rows = ['<tr>\n' + '\n'.join(sorted(cells)[i:i + 3]) + '\n</tr>'
                for i in range(0, len(cells), 3)]
        return '<table>\n' + '\n'.join(rows) + '\n</table>'
    gallery = re.sub(r'<table>\n(.*?)\n</table>', table, text[first:last], flags=re.S)
    return text[:first] + gallery + text[last:]


def scan_checkout(root, old, new):
    records = subprocess.check_output(['git', 'ls-tree', '-rz', 'HEAD'], cwd=root).split(b'\0')
    changes, retained, skipped = [], [], []
    for record in filter(None, records):
        metadata, raw_path = record.split(b'\t', 1)
        mode, kind, sha = metadata.decode().split()
        path = raw_path.decode('utf-8')
        if mode != '100644' and mode != '100755':
            skipped.append(path)
            continue
        if path.startswith(('branding/archive/', 'branding/revisions/')):
            continue
        file = root / path
        if file.stat().st_size > MAX_TEXT:
            skipped.append(path)
            continue
        content = file.read_bytes()
        try:
            text = content.decode('utf-8')
        except UnicodeDecodeError:
            continue
        if '\0' in text:
            continue
        updated = rewrite(text, old, new)
        if path == 'README.md':
            updated = refresh_gallery(updated)
        if updated != text:
            changes.append({'path': path, 'mode': mode, 'before': sha, 'content': updated,
                            'diff': ''.join(difflib.unified_diff(text.splitlines(True),
                                updated.splitlines(True), fromfile=path, tofile=path))})
        if old in updated:
            retained.append(path)
    return changes, retained, skipped


def checkout_snapshot(repo, branch, head, directory):
    token = os.environ['GH_TOKEN']
    auth = base64.b64encode(('x-access-token:' + token).encode()).decode()
    env = dict(os.environ, GIT_CONFIG_COUNT='1', GIT_CONFIG_KEY_0='http.extraheader',
               GIT_CONFIG_VALUE_0='AUTHORIZATION: basic ' + auth, GIT_TERMINAL_PROMPT='0')
    result = subprocess.run(['git', 'clone', '--quiet', '--depth', '1', '--single-branch',
                             '--branch', branch, f'https://github.com/{repo}.git', str(directory)],
                            env=env, capture_output=True, timeout=180)
    if result.returncode:
        raise RuntimeError(f'Cannot clone {repo}; check repository access')
    actual = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=directory, text=True).strip()
    if actual != head:
        raise ValueError(f'{repo} changed while planning; run Plan again')


def metadata(api, name):
    data = api.call(f'repos/{OWNER}/{name}')
    if data['full_name'] != f'{OWNER}/{name}' or data['archived'] or data.get('disabled'):
        raise ValueError(f'{name} must be an accessible, active canonical repository')
    return data


def make_plan(api, old, new, scope, scanner=checkout_snapshot):
    short(old), short(new)
    if old not in scope or old == new or new in scope:
        raise ValueError('Source must be configured; destination must be a distinct new name')
    if old == CONTROLLER:
        raise ValueError('FOUNDRY hosts shared Actions; migrate its Action consumers before renaming the controller')
    source = api.call(f'repos/{OWNER}/{old}')
    destination = api.call(f'repos/{OWNER}/{new}', missing=True)
    recovering = source['full_name'] == f'{OWNER}/{new}'
    if recovering:
        if destination is None or destination['id'] != source['id']:
            raise ValueError('Cannot establish renamed repository identity')
    elif source['full_name'] != f'{OWNER}/{old}' or destination is not None:
        raise ValueError('Destination exists or source redirects to another identity')
    metadata(api, new if recovering else old)
    plan = {'schemaVersion': 1, 'old': old, 'new': new, 'sourceId': source['id'],
            'createdAt': dt.datetime.now(dt.timezone.utc).isoformat(),
            'workflowCommit': os.environ.get('GITHUB_SHA', ''), 'scope': scope,
            'alreadyRenamed': recovering, 'repositories': []}
    with tempfile.TemporaryDirectory() as temporary:
        for name in scope:
            live_name = new if recovering and name == old else name
            info = metadata(api, live_name)
            branch = info['default_branch']
            ref = api.call(f'repos/{OWNER}/{live_name}/git/ref/heads/{branch}')
            head = ref['object']['sha']
            commit = api.call(f'repos/{OWNER}/{live_name}/git/commits/{head}')
            directory = Path(temporary) / name
            scanner(f'{OWNER}/{live_name}', branch, head, directory)
            changes, retained, skipped = scan_checkout(directory, old, new)
            plan['repositories'].append({'name': name, 'id': info['id'], 'branch': branch,
                'head': head, 'tree': commit['tree']['sha'], 'changes': changes,
                'retained': retained, 'skipped': skipped})
    return plan


def validate_plan(plan, old, new, scope, confirmation, now=None):
    now = now or dt.datetime.now(dt.timezone.utc)
    age = now - dt.datetime.fromisoformat(plan['createdAt'])
    if (plan['schemaVersion'] != 1 or plan['old'] != old or plan['new'] != new or
            confirmation != f'{old} -> {new}' or plan['scope'] != scope or
            plan['workflowCommit'] != os.environ.get('GITHUB_SHA', '') or
            not dt.timedelta(0) <= age <= dt.timedelta(days=7)):
        raise ValueError('Plan expired, changed, or confirmation does not match old -> new')
    if old == CONTROLLER or old not in scope or new in scope or old == new:
        raise ValueError('Invalid rename scope')
    if [entry['name'] for entry in plan['repositories']] != scope:
        raise ValueError('Plan repository scope mismatch')
    source = next(entry for entry in plan['repositories'] if entry['name'] == old)
    if source['id'] != plan['sourceId']:
        raise ValueError('Plan source identity mismatch')


def preflight(api, plan):
    """Read every identity and head before the first mutation; also permits partial retries."""
    old, new = plan['old'], plan['new']
    destination = api.call(f'repos/{OWNER}/{new}', missing=True)
    renamed = destination is not None
    if renamed and (destination['id'] != plan['sourceId'] or destination['full_name'] != f'{OWNER}/{new}'):
        raise ValueError('Destination identity mismatch')
    live = []
    for entry in plan['repositories']:
        name = new if renamed and entry['name'] == old else entry['name']
        info = metadata(api, name)
        if info['id'] != entry['id'] or info['default_branch'] != entry['branch']:
            raise ValueError(f'{name}: repository identity/default branch changed')
        head = api.call(f'repos/{OWNER}/{name}/git/ref/heads/{entry["branch"]}')['object']['sha']
        if head != entry['head']:
            raise ValueError(f'{name}: default branch changed; create a fresh Plan')
        live.append((entry, name))
    return renamed, live


def apply_plan(api, plan, report):
    renamed, live = preflight(api, plan)
    report['renamed'] = renamed
    old, new = plan['old'], plan['new']
    branch = f'chore/rename-{old}-to-{new}'
    # Refuse unrelated existing branches across the fleet before renaming.
    trees = {}
    for entry, name in live:
        if not entry['changes']:
            continue
        existing = api.call(f'repos/{OWNER}/{name}/git/ref/heads/{branch}', missing=True)
        if existing:
            commit = api.call(f'repos/{OWNER}/{name}/git/commits/{existing["object"]["sha"]}')
            if (commit['message'] != f'chore: update references for {old} -> {new}' or
                    [p['sha'] for p in commit['parents']] != [entry['head']]):
                raise ValueError(f'{name}: rename branch already exists; inspect it before retrying')
            def leaves(tree_sha):
                result = api.call(f'repos/{OWNER}/{name}/git/trees/{tree_sha}?recursive=1')
                if result.get('truncated'):
                    raise ValueError('Cannot verify a truncated proposal tree')
                return {item['path']: (item['mode'], item['type'], item['sha'])
                        for item in result['tree'] if item['type'] != 'tree'}
            expected = leaves(entry['tree'])
            for change in entry['changes']:
                raw = change['content'].encode('utf-8')
                digest = hashlib.sha1(f'blob {len(raw)}\0'.encode() + raw).hexdigest()
                expected[change['path']] = (change['mode'], 'blob', digest)
            if leaves(commit['tree']['sha']) != expected:
                raise ValueError(f'{name}: proposal contents differ; inspect before retrying')
        trees[name] = existing
    # Exercise real content/workflow writes in every affected repository before
    # renaming. These are unattached Git objects, never branch/default-ref writes.
    prepared = {}
    for entry, name in live:
        if not entry['changes']:
            continue
        repo = f'{OWNER}/{name}'
        entries = [{'path': c['path'], 'mode': c['mode'], 'type': 'blob', 'content': c['content']}
                   for c in entry['changes']]
        tree = api.call(f'repos/{repo}/git/trees', 'POST', {'base_tree': entry['tree'], 'tree': entries})
        if trees[name]:
            commit = api.call(f'repos/{repo}/git/commits/{trees[name]["object"]["sha"]}')
            if commit['tree']['sha'] != tree['sha']:
                raise ValueError(f'{name}: rename branch contents changed; refusing overwrite')
            commit['sha'] = trees[name]['object']['sha']
        else:
            commit = api.call(f'repos/{repo}/git/commits', 'POST', {'tree': tree['sha'],
                'parents': [entry['head']], 'message': f'chore: update references for {old} -> {new}'})
        prepared[name] = commit
    # Object preparation can take time; refuse head/identity changes before rename.
    preflight(api, plan)
    report['writePreflightCompleted'] = True
    if not renamed:
        result = api.call(f'repos/{OWNER}/{old}', 'PATCH', {'name': new})
        if result['id'] != plan['sourceId'] or result['full_name'] != f'{OWNER}/{new}':
            raise ValueError('Rename readback mismatch; inspect live state before retrying')
    report['renamed'] = True
    for entry, original_name in live:
        name = new if entry['name'] == old else original_name
        if not entry['changes']:
            continue
        repo = f'{OWNER}/{name}'
        head = api.call(f'repos/{repo}/git/ref/heads/{entry["branch"]}')['object']['sha']
        if head != entry['head']:
            raise ValueError(f'{name}: default branch changed after rename; stop and replan')
        existing = trees[original_name]
        commit = prepared[original_name]
        if not existing:
            api.call(f'repos/{repo}/git/refs', 'POST', {'ref': f'refs/heads/{branch}', 'sha': commit['sha']})
        # Existing matching branch/PR can be reused after an interrupted Apply.
        prs = api.call(f'repos/{repo}/pulls?state=all&head={OWNER}:{branch}&base={entry["branch"]}')
        if prs:
            if len(prs) != 1 or prs[0]['state'] != 'open':
                raise ValueError(f'{name}: prior rename PR closed; inspect before retrying')
            pr = prs[0]
        else:
            pr = api.call(f'repos/{repo}/pulls', 'POST', {'head': branch, 'base': entry['branch'],
                'title': f'chore: update repository references to {new}',
                'body': f'Repository ID {plan["sourceId"]} renamed from {OWNER}/{old} to {OWNER}/{new}. '
                        'Update reviewed text references only; product identity and asset paths are unchanged. '
                        'Review the diff and required checks, then squash merge. No auto-merge requested. '
                        'Retained references and external follow-ups are listed in the rename run artifact.'})
        report.setdefault('pullRequests', []).append(pr['html_url'])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--operation', choices=['plan', 'apply', 'execute'], required=True)
    parser.add_argument('--repository', required=True)
    parser.add_argument('--new-name', required=True)
    parser.add_argument('--confirm', default='')
    parser.add_argument('--reviewed-plan', type=Path)
    parser.add_argument('--output', type=Path, default=Path('artifacts/repository-rename'))
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    report = {'operation': args.operation, 'status': 'failed', 'renamed': False}
    try:
        old, new = short(args.repository.strip()), short(args.new_name.strip())
        scope = json.loads((ROOT / 'config/workflow-repositories.json').read_text())['repositories']
        if len(scope) != len(set(scope)) or any(short(name) != name for name in scope):
            raise ValueError('Invalid configured scope')
        api = GitHub()
        if args.operation in ('plan', 'execute'):
            plan = make_plan(api, old, new, scope)
            encoded = json.dumps(plan, indent=2)
            if len(encoded.encode()) > MAX_PLAN:
                raise ValueError('Plan too large; reduce scope through reviewed configuration')
            (args.output / 'plan.json').write_text(encoded + '\n')
            description = ('Automatic Plan → Apply; no separate plan review.' if args.operation == 'execute'
                           else 'Plan only: no external changes.')
            summary = [f'# Repository rename: {old} → {new}', '', description, '']
            for entry in plan['repositories']:
                summary += [f'## {entry["name"]}', f'Base: `{entry["head"]}`',
                            f'Files to update: {len(entry["changes"])}',
                            'Retained matches (inspect): ' + ', '.join(entry['retained']),
                            'Unscanned files (inspect): ' + ', '.join(entry['skipped'])]
            summary += ['', '## External follow-ups',
                        'Review Pages/custom domains, packages/container image paths, webhooks, OIDC trust, '
                        'secrets/variables, local remotes, other repositories and open branches. '
                        'These are not changed by this workflow. Archive ZIPs and binary assets are preserved.']
            (args.output / 'summary.md').write_text('\n\n'.join(summary) + '\n')
            (args.output / 'references.diff').write_text(''.join(
                f'\n# {entry["name"]}\n' + ''.join(c['diff'] for c in entry['changes'])
                for entry in plan['repositories']))
            report['status'] = 'planned'
            if args.operation == 'execute':
                validate_plan(plan, old, new, scope, f'{old} -> {new}')
                apply_plan(api, plan, report)
                report['status'] = 'proposed'
        else:
            if args.reviewed_plan is None or args.reviewed_plan.stat().st_size > MAX_PLAN:
                raise ValueError('Apply requires a reviewed Plan')
            plan = json.loads(args.reviewed_plan.read_text())
            validate_plan(plan, old, new, scope, args.confirm.strip())
            apply_plan(api, plan, report)
            report['status'] = 'proposed'
        return 0
    except (ValueError, RuntimeError, OSError, KeyError, subprocess.TimeoutExpired) as error:
        report['status'] = 'failed'
        report['error'] = str(error)
        print(str(error))
        return 1
    finally:
        (args.output / 'result.json').write_text(json.dumps(report, indent=2) + '\n')


if __name__ == '__main__':
    raise SystemExit(main())

