#!/usr/bin/env python3
"""Remove only the retired title check from six explicitly identified rulesets."""
import argparse
import copy
import hashlib
import json
import os
from pathlib import Path
import subprocess

TARGETS = {
    'sun-strata': 27252100, 'sun-workbench': 27170810,
    'sun-codefolio': 27691224, 'sun-playground': 27863607,
    'sun-trypane': 28016218, 'sun-foundry-pilot': 27529174,
}
FIELDS = ('name', 'target', 'enforcement', 'conditions', 'bypass_actors', 'rules')


def api(method, path, payload=None):
    command = ['gh', 'api', '--method', method, path]
    if payload is not None:
        command += ['--input', '-']
    result = subprocess.run(command, input=json.dumps(payload) if payload is not None else None,
                            capture_output=True, text=True, timeout=45, check=False)
    if result.returncode:
        raise RuntimeError(f'GitHub {method} failed; review credential permissions and retry')
    return json.loads(result.stdout)


def normalize(detail):
    return {key: copy.deepcopy(detail[key]) for key in FIELDS}


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def proposal(detail, repository):
    short = repository.removeprefix('sunstriker2009/')
    if repository != 'sunstriker2009/' + short or short not in TARGETS:
        raise ValueError('Repository is outside the reviewed migration scope')
    if (detail.get('id') != TARGETS[short] or detail.get('source') != repository
            or detail.get('source_type') != 'Repository'
            or detail.get('name') != 'SUN Main Protection'
            or detail.get('target') != 'branch' or detail.get('enforcement') != 'active'
            or detail.get('conditions', {}).get('ref_name') != {'include': ['refs/heads/main'], 'exclude': []}):
        raise ValueError('Live ruleset identity or scope changed; review before migrating')
    before = normalize(detail)
    after = copy.deepcopy(before)
    rules = [r for r in after['rules'] if r['type'] == 'required_status_checks']
    if len(rules) != 1:
        raise ValueError('Expected exactly one required-status-check rule')
    params = rules[0]['parameters']
    checks = params['required_status_checks']
    if not any(c['context'] == 'repository-validation' for c in checks):
        raise ValueError('Required build validation is missing; refusing migration')
    params['required_status_checks'] = [c for c in checks if c['context'] != 'conventional-title']
    return before, after


def migrate(repository, operation, expected_digest='', confirmation='', request=api, output=Path('title-check-migration')):
    short = repository.removeprefix('sunstriker2009/')
    if repository != 'sunstriker2009/' + short or short not in TARGETS:
        raise ValueError('Repository is outside the reviewed migration scope')
    path = f'repos/{repository}/rulesets/{TARGETS[short]}'
    before, after = proposal(request('GET', path), repository)
    snapshot = {'repository': repository, 'rulesetId': TARGETS[short], 'before': before, 'after': after}
    fingerprint = digest(snapshot)
    if operation not in ('plan', 'apply'):
        raise ValueError('Operation must be plan or apply')
    if operation == 'apply' and (confirmation.strip() != repository or expected_digest.strip() != fingerprint):
        raise ValueError('Apply requires the exact repository and current reviewed plan digest; re-plan after drift')
    output.mkdir(parents=True, exist_ok=True)
    (output / 'plan.json').write_text(json.dumps({**snapshot, 'digest': fingerprint}, indent=2) + '\n')
    if operation == 'apply' and before != after:
        # Recheck immediately before mutation; no unreviewed drift may be overwritten.
        if normalize(request('GET', path)) != before:
            raise ValueError('Ruleset changed after planning; refusing write')
        request('PUT', path, after)
        if normalize(request('GET', path)) != after:
            raise RuntimeError('Post-apply verification failed; inspect the saved before snapshot')
    result = {'repository': repository, 'operation': operation, 'digest': fingerprint,
              'changed': before != after, 'status': 'planned' if operation == 'plan' else 'verified'}
    (output / 'result.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result, indent=2))
    summary = os.environ.get('GITHUB_STEP_SUMMARY')
    if summary:
        with open(summary, 'a') as stream:
            stream.write(f"## Title-check retirement: {repository}\n\nStatus: {result['status']}\n\nReviewed plan digest: `{fingerprint}`\n\nInspect `plan.json` in the migration artifact before Apply.\n")
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repository', required=True)
    parser.add_argument('--operation', choices=['plan', 'apply'], default='plan')
    parser.add_argument('--expected-digest', default='')
    parser.add_argument('--confirm-repository', default='')
    args = parser.parse_args()
    migrate(args.repository, args.operation, args.expected_digest, args.confirm_repository)
