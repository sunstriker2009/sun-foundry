#!/usr/bin/env python3
"""Rename registered product display references, optionally chaining repository rename."""
import argparse
import difflib
import importlib.util
import json
import os
from pathlib import Path
import re
import subprocess
import tempfile

SPEC = importlib.util.spec_from_file_location('repository_rename', Path(__file__).with_name('rename-repository.py'))
repository = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(repository)
ROOT = Path(__file__).resolve().parents[1]
HISTORY = ('branding/archive/', 'branding/revisions/', 'branding/assets/refs/',
           'decisions/', 'docs/adr/', 'docs/brand/000')
CODE = {'.cs', '.mjs', '.cjs', '.js', '.ts', '.tsx', '.jsx', '.html', '.csproj', '.yml', '.yaml'}
DISPLAY = re.compile(r'\b(title|productName|displayName|brand|applicationName|aria-label|alt|placeholder)\b|\bsetName\s*\(')
COMPATIBILITY = re.compile(r'legacy|profile|userData|appData|setPath|AppUserModelId|format\s*[:=]|'
                           r'process\.env|GetEnvironmentVariable|localStorage|sessionStorage', re.I)


def product_name(value):
    value = value.strip()
    if not re.fullmatch(r'[A-Za-z][A-Za-z0-9]*(?: [A-Za-z0-9]+)*', value) or not 2 <= len(value) <= 60:
        raise ValueError('Use a 2–60 character product name containing letters, digits and single spaces')
    if value.lower().endswith(' by sun'):
        raise ValueError('Enter the product name without the by Sun endorsement')
    return value


def display_text(text, old, new):
    # Whole display words only: do not touch repo/package paths, env names,
    # qualified identifiers, protocol channels or filename extensions.
    pattern = r'(?<![\w/@.-])' + re.escape(old) + r'(?![\w/@-]|\.[A-Za-z0-9]|:[A-Za-z0-9])'
    return re.sub(pattern, lambda _: new, text, flags=re.I)


def prose(text, old, new):
    parts = re.split(r'(```[^\n]*\n[\s\S]*?```|`[^`\n]+`|https?://[^\s)<>]+)', text)
    for index, part in enumerate(parts):
        if part.startswith('```mermaid'):
            parts[index] = re.sub(r'"([^"\n]*)"', lambda m: '"' + display_text(m[1], old, new) + '"', part)
        elif not part.startswith(('`', 'http://', 'https://')):
            parts[index] = display_text(part, old, new)
    return ''.join(parts)


def rewrite_product(path, text, old, new):
    if path.startswith(HISTORY) or path == 'CHANGELOG.md' or re.match(r'docs/operations/M\d', path):
        return text
    suffix = Path(path).suffix.lower()
    if suffix == '.md':
        return prose(text, old, new)
    if suffix == '.json':
        # Only human display fields. Technical identifiers and history are left intact.
        if path in ('registry/products.json', 'registry/repositories.json', 'registry/symbol-approvals.json'):
            return text
        data = json.loads(text)
        changed = False
        def visit(value):
            nonlocal changed
            if isinstance(value, dict):
                for key, item in value.items():
                    if key in ('title', 'productName', 'displayName', 'brand', 'applicationName', 'short_name', 'description') and isinstance(item, str):
                        replacement = display_text(item, old, new)
                        changed |= replacement != item
                        value[key] = replacement
                    else:
                        visit(item)
            elif isinstance(value, list):
                for item in value:
                    visit(item)
        visit(data)
        return json.dumps(data, indent=2, ensure_ascii=False) + '\n' if changed else text
    if suffix not in CODE:
        return text
    lines = []
    for line in text.splitlines(True):
        if COMPATIBILITY.search(line):
            lines.append(line)
            continue
        def literal(match):
            quote, body = match[1], match[2]
            # Exact bare-name literals are technical unless explicitly labelled as display data.
            if old.casefold() == body.casefold() and not DISPLAY.search(line):
                return match[0]
            if ' ' not in body and not DISPLAY.search(line):
                return match[0]
            return quote + display_text(body, old, new) + quote
        line = re.sub(r'([\'"`])([^\n]*?)\1', literal, line)
        if suffix in ('.tsx', '.jsx', '.html'):
            line = re.sub(r'>([^<>{}\n]+)<', lambda m: '>' + display_text(m[1], old, new) + '<', line)
        if suffix in ('.yml', '.yaml') and re.match(r'\s*name:\s', line):
            line = display_text(line, old, new)
        lines.append(line)
    return ''.join(lines)


def read_entry(root, path):
    return subprocess.check_output(['git', 'rev-parse', 'HEAD:' + path], cwd=root, text=True).strip()


def change(root, path, content):
    existing = root / path
    before = existing.read_text() if existing.is_file() else ''
    return {'path': path, 'mode': '100644', 'before': read_entry(root, path) if existing.is_file() else None,
            'content': content, 'diff': ''.join(difflib.unified_diff(before.splitlines(True),
                content.splitlines(True), fromfile=path, tofile=path))}


def scan(root, old, new, old_repo, new_repo):
    records = subprocess.check_output(['git', 'ls-tree', '-rz', 'HEAD'], cwd=root).split(b'\0')
    changes, retained, skipped = [], [], []
    for record in filter(None, records):
        meta, raw_path = record.split(b'\t', 1)
        mode, kind, sha = meta.decode().split()
        path = raw_path.decode('utf-8')
        if path.startswith(HISTORY) or path == 'registry/symbol-approvals.json':
            continue
        file = root / path
        if mode not in ('100644', '100755') or file.stat().st_size > repository.MAX_TEXT:
            skipped.append(path)
            continue
        try:
            text = file.read_bytes().decode('utf-8')
        except UnicodeDecodeError:
            continue
        if '\0' in text:
            continue
        updated = rewrite_product(path, text, old, new)
        if old_repo != new_repo:
            updated = repository.rewrite(updated, old_repo, new_repo)
        if path == 'README.md':
            updated = repository.refresh_gallery(updated)
        if updated != text:
            item = change(root, path, updated)
            item['mode'] = mode
            changes.append(item)
        if re.search(re.escape(old), updated, re.I):
            retained.append(path)
    return changes, retained, skipped


def resolve_product(authority, target, actual, new_name):
    if new_name.casefold() == authority.get('parentBrand', '').casefold():
        raise ValueError('The SUN parent-brand name cannot be adopted by a product')
    rows = [item for group in ('products', 'infrastructure') for item in authority[group]]
    matches = [item for item in rows if item.get('repository') in (target, actual)]
    if len(matches) != 1:
        raise ValueError('Target must uniquely identify one registered SUN product/infrastructure entry')
    item = matches[0]
    if not re.fullmatch(r'SUN-(?:G)?[0-9]{3}', item.get('id', '')):
        raise ValueError('Registry identity must be a stable SUN ID')
    product_name(item['name'])
    if item.get('status') not in ('CONFIRMED', 'ESTABLISHED'):
        raise ValueError('Only confirmed/established identities can be renamed')
    if new_name.casefold() == item['name'].casefold():
        raise ValueError('Registry already uses this product name; inspect existing migration PRs')
    for row in rows:
        names = [row['name'], row.get('supersedes', ''), *row.get('previousNames', [])]
        if new_name.casefold() in [name.casefold() for name in names if isinstance(name, str)]:
            raise ValueError('Name collides with a registered or historical SUN identity')
    return item


def make_plan(api, target, new_name, rename_repo=False, new_repository='', scanner=None):
    repository.short(target)
    new_name = product_name(new_name)
    if rename_repo:
        repository.short(new_repository)
        if new_repository == target or target == repository.CONTROLLER:
            raise ValueError('Choose a distinct destination; controller repository renames are unsupported')
    elif new_repository:
        raise ValueError('Clear new repository name unless repository rename is selected')
    new_repo = new_repository if rename_repo else target
    scope = repository.reference_scope(target)
    info = api.call(f'repos/{repository.OWNER}/{target}')
    actual = info['full_name'].removeprefix(repository.OWNER + '/')
    if info['full_name'] != f'{repository.OWNER}/{actual}' or actual not in (target, new_repo):
        raise ValueError('Target redirects outside the requested migration')
    if rename_repo:
        destination = api.call(f'repos/{repository.OWNER}/{new_repo}', missing=True)
        if destination is not None and (actual != new_repo or destination['id'] != info['id']):
            raise ValueError('Repository destination is already occupied')
    scanner = scanner or repository.checkout_snapshot
    plan = {'schemaVersion': 1, 'kind': 'product-rename', 'old': target, 'new': new_repo,
            'renameRepository': rename_repo, 'sourceId': info['id'], 'scope': scope,
            'workflowCommit': os.environ.get('GITHUB_SHA', ''), 'repositories': []}
    with tempfile.TemporaryDirectory() as temporary:
        roots = {}
        for name in scope:
            live_name = actual if name == target else name
            meta = repository.metadata(api, live_name)
            branch = meta['default_branch']
            head = api.call(f'repos/{repository.OWNER}/{live_name}/git/ref/heads/{branch}')['object']['sha']
            commit = api.call(f'repos/{repository.OWNER}/{live_name}/git/commits/{head}')
            root = Path(temporary) / name
            scanner(f'{repository.OWNER}/{live_name}', branch, head, root)
            roots[name] = root
            plan['repositories'].append({'name': name, 'id': meta['id'], 'branch': branch,
                'head': head, 'tree': commit['tree']['sha']})
        if next(row for row in plan['repositories'] if row['name'] == target)['id'] != plan['sourceId']:
            raise ValueError('Target repository identity changed during planning')
        ecosystem = roots['sun-ecosystem']
        authority = json.loads((ecosystem / 'registry/products.json').read_text())
        identity = resolve_product(authority, target, actual, new_name)
        old_name, ident = identity['name'], identity['id']
        plan.update(productId=ident, oldProductName=old_name, newProductName=new_name)
        slug = new_name.lower().replace(' ', '-')
        plan['proposalBranch'] = f'chore/product-rename-{ident.lower()}-{slug}'
        plan['proposalMessage'] = f'chore(branding): rename {ident} from {old_name} to {new_name}'
        plan['proposalTitle'] = f'chore(branding): rename {ident} to {new_name} by Sun'
        plan['proposalBody'] = (f'Owner-requested product migration: {old_name} → {new_name} '
            f'for {ident}. Reference scope is only {", ".join(scope)}. '
            f'Repository rename requested: {rename_repo}. SUN ID, capabilities, packages, '
            'data/protocol identifiers and archived artwork are preserved. '
            'Review required CI and squash merge. Retained matches and limits are in the run artifact. '
            'This does not resume product development or schedules. No auto-merge requested.')
        for entry in plan['repositories']:
            root = roots[entry['name']]
            entry['changes'], entry['retained'], entry['skipped'] = scan(root, old_name, new_name, target, new_repo)
        entry = next(row for row in plan['repositories'] if row['name'] == 'sun-ecosystem')
        # Registry authority is matched by stable SUN ID, never a global JSON substitution.
        prior_names = list(dict.fromkeys([*identity.get('previousNames', []), identity.get('supersedes', ''), old_name]))
        identity.update(name=new_name, supersedes=old_name, previousNames=[n for n in prior_names if n])
        if 'publicName' in identity:
            identity['publicName'] = new_name + ' by Sun'
        if rename_repo:
            identity['repository'] = new_repo
        catalog = json.loads((ecosystem / 'registry/repositories.json').read_text())
        rows = [row for row in catalog['repositories'] if row.get('registryId') == ident]
        if len(rows) != 1 or rows[0]['repository'] not in (f'{repository.OWNER}/{target}', f'{repository.OWNER}/{actual}'):
            raise ValueError('Product registry and repository catalog disagree')
        rows[0]['name'] = new_name
        if rename_repo:
            rows[0]['repository'] = f'{repository.OWNER}/{new_repo}'
        replacements = {c['path']: c for c in entry['changes']}
        for path, value in [('registry/products.json', authority), ('registry/repositories.json', catalog)]:
            replacements[path] = change(ecosystem, path, json.dumps(value, indent=2, ensure_ascii=False) + '\n')
        decision = f'decisions/product-renames/{ident.lower()}-{slug}.md'
        if (ecosystem / decision).exists():
            raise ValueError('Naming decision already exists; inspect previous migration before retrying')
        text = (f'# {old_name} → {new_name} by Sun\n\n'
                f'The owner dispatched the product-name migration for **{ident}**. '
                f'The new display name is **{new_name}**; the previous name is {old_name}. '
                f'The resulting repository is `{repository.OWNER}/{new_repo}`.\n\n'
                'SUN ID, capability namespaces, package IDs, purpose and tagline are unchanged. '
                'Original naming decisions and historical artwork remain preserved. '
                'This naming approval does not establish commercial clearance or resume paused development.\n')
        replacements[decision] = change(ecosystem, decision, text)
        entry['changes'] = list(replacements.values())
    return plan


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repository', required=True)
    parser.add_argument('--new-name', required=True)
    parser.add_argument('--operation', choices=['execute', 'plan'], default='execute')
    parser.add_argument('--rename-repository', action='store_true')
    parser.add_argument('--new-repository', default='')
    parser.add_argument('--output', type=Path, default=Path('artifacts/product-rename'))
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    report = {'operation': args.operation, 'status': 'failed', 'renamed': False}
    try:
        api = repository.GitHub()
        plan = make_plan(api, args.repository.strip(), args.new_name, args.rename_repository, args.new_repository.strip())
        encoded = json.dumps(plan, indent=2, ensure_ascii=False)
        if len(encoded.encode()) > repository.MAX_PLAN:
            raise ValueError('Plan exceeds 12 MB')
        (args.output / 'plan.json').write_text(encoded + '\n')
        summary = [f'# Product rename: {plan["oldProductName"]} → {plan["newProductName"]}',
                   f'SUN identity: {plan["productId"]}', f'Repository rename: {plan["renameRepository"]}',
                   'Scope: ' + ', '.join(plan['scope']),
                   'Binary artwork, data/protocol identifiers and historical evidence remain unchanged.']
        for entry in plan['repositories']:
            summary += [f'## {entry["name"]}', f'Files to update: {len(entry["changes"])}',
                        'Retained matches: ' + ', '.join(entry['retained']),
                        'Unscanned files: ' + ', '.join(entry['skipped'])]
        (args.output / 'summary.md').write_text('\n\n'.join(summary) + '\n')
        (args.output / 'references.diff').write_text(''.join(
            f'\n# {entry["name"]}\n' + ''.join(c['diff'] for c in entry['changes'])
            for entry in plan['repositories']))
        if args.operation == 'execute':
            repository.apply_plan(api, plan, report)
            report['status'] = 'proposed'
        else:
            report['status'] = 'planned'
        return 0
    except (ValueError, RuntimeError, OSError, KeyError, subprocess.TimeoutExpired) as error:
        report.update(status='failed', error=str(error))
        print(str(error))
        return 1
    finally:
        (args.output / 'result.json').write_text(json.dumps(report, indent=2) + '\n')


if __name__ == '__main__':
    raise SystemExit(main())
