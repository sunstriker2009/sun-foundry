"""Safety assertions retained from the consolidated workflow wrappers."""
import unittest


class WorkflowGuards(unittest.TestCase):
    def test_ecosystem_registration(self):
        from pathlib import Path
        script=Path('scripts/register-foundry-repository.sh').read_text()
        factory=Path('.github/workflows/repository-factory-v1.yml').read_text()
        manual=Path('.github/workflows/register-sun-repository.yml').read_text()
        for required in ('"classification":"pending"', '"registryId":None', 'Repository confirmation mismatch', 'Existing registration branch', 'python3 scripts/render-repository-gallery.py'):
            assert required in script, required
        assert factory.index('Strict verify governance') < factory.index('Squash merge the verified product seed')
        assert 'register-foundry-repository.sh' not in factory
        assert factory.index('Squash merge the verified product seed') < factory.index('Verify main and publish the approved identity to Foundry')
        assert 'options: [preview, apply]' in manual
        assert 'github.actor == ' in manual

    def test_factory_recovery(self):
        from pathlib import Path
        import re
        factory = Path(".github/workflows/repository-factory-v1.yml").read_text()
        branding = Path("scripts/prepare-product-branding.sh").read_text()
        assert '[[ "$valid" == "open|main|$branch|$REPO" ]]' in factory
        assert 'if ! gh api "repos/$REPO/contents/docs/SUN-GOVERNANCE-CI-SEED.md?ref=$branch"' in factory
        assert 'Product README exists but STRATA banner remains' in branding
        assert 'Product README exists without brand guide' in branding
        assert 'docs/TEMPLATE-GUIDE.md?ref=$BRANCH' in branding
        assert 'github.event.pull_request.merged == true' in factory
        assert 'github.event.pull_request.head.repo.full_name == github.repository' in factory
        relay = factory.split('  relay-approved-registration:', 1)[1].split('  authorize-approved-registration:', 1)[0]
        assert 'actions: write' in relay and 'environment:' not in relay
        assert 'ref:"main"' in relay and '/dispatches" --input -' in relay
        inputs = factory.split('    inputs:', 1)[1].split('\npermissions:', 1)[0]
        assert re.findall(r'^      (\w+):\s*$', inputs, re.M) == ['approved_registration_pr', 'confirm_repository']
        assert inputs.count('required: true') == 2
        job = factory.split('  factory:\n', 1)[1]
        gate = job.split('    runs-on:', 1)[0]
        assert 'needs: authorize-approved-registration' in gate
        assert "needs.authorize-approved-registration.result == 'success'" in gate
        assert '||' not in gate
        assert 'needs.authorize-approved-registration.outputs.factory_target' in job
        assert 'bash scripts/verify-approved-product-seed.sh "$REPO" "$VERIFIED_HEAD"' in factory
        assert '-f sha="$VERIFIED_HEAD" -f merge_method=squash' in factory
        print("Recovery guards present; no remote GitHub mutations performed")

    def test_governance_idempotency(self):
        from pathlib import Path
        source = Path("src/Sun.RepoBootstrap/Program.cs").read_text()
        branch = source.split("if (rulePresent)", 1)[1].split("else", 1)[0]
        assert "verifying exact governance without mutations" in branch
        assert 'await Api("POST", $"repos/{repo}/rulesets", ruleset)' in source
        assert 'if (violations.Count > 0) throw new InvalidOperationException' in source
        assert 'if (confirmation != repo)' in source
        print("Existing ruleset path is verification-only; policy drift remains fatal.")
