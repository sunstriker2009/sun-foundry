import importlib.util
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

SPEC = importlib.util.spec_from_file_location(
    "fleet", Path(__file__).resolve().parents[1] / "scripts/audit-governance-fleet.py")
fleet = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(fleet)
TARGET = {"repository": "sunstriker2009/sun-foundry", "requiredChecks": ["build"]}


class FleetTests(unittest.TestCase):
    def run_result(self, code, output):
        with patch.object(fleet.subprocess, "run", return_value=
                          subprocess.CompletedProcess([], code, output, "")) as call:
            result = fleet.verify(TARGET)
            args = call.call_args.args[0]
            self.assertEqual(args, ["dotnet", str(fleet.VERIFIER), "--repo",
                                   TARGET["repository"], "--mode", "verify", "--checks", "build"])
            self.assertNotIn("--confirm", args)
            self.assertFalse(call.call_args.kwargs.get("shell", False))
            self.assertEqual(call.call_args.kwargs["timeout"], 120)
            return result

    def test_compliant_requires_success_and_positive_verification(self):
        self.assertEqual(self.run_result(0, "Verified: exact required checks")['status'], "compliant")
        self.assertEqual(self.run_result(0, "unexpected early return")['status'], "error")
        self.assertEqual(self.run_result(1, "Verified: exact required checks")['status'], "error")

    def test_drift_is_separate_from_api_access_failure(self):
        self.assertEqual(self.run_result(134, "Policy verification failed: missing checks")['status'], "drift")
        self.assertEqual(self.run_result(134, "GitHub GET repos/example: 403 forbidden")['status'], "error")

    def test_private_plan_limitation_never_becomes_compliant(self):
        output = "GOVERNANCE CAPABILITY: repository rulesets unavailable for this private repository"
        for code in (0, 134):
            self.assertEqual(self.run_result(code, output)['status'], "unavailable")

    def test_token_is_redacted_from_saved_evidence(self):
        with patch.dict(os.environ, {"GH_TOKEN": "sensitive-fixture-token"}):
            result = self.run_result(1, "error sensitive-fixture-token")
        self.assertNotIn("sensitive-fixture-token", result['detail'])
        self.assertIn("[REDACTED]", result['detail'])

    def test_missing_check_policy_never_runs_verifier(self):
        with patch.object(fleet.subprocess, "run") as call:
            self.assertEqual(fleet.verify({**TARGET, "requiredChecks": None})['status'], "not_configured")
            call.assert_not_called()

    def test_timeout_and_missing_runtime_report_error(self):
        for error in (subprocess.TimeoutExpired([], 120), FileNotFoundError()):
            with patch.object(fleet.subprocess, "run", side_effect=error):
                self.assertEqual(fleet.verify(TARGET)['status'], "error")

    def test_mixed_fleet_reports_every_target_and_preserves_order(self):
        targets = [{**TARGET, "repository": f"sunstriker2009/sun-{i}"} for i in range(4)]
        statuses = ["compliant", "drift", "unavailable", "error"]
        def verify(t):
            return {**t, "status": statuses[int(t['repository'][-1])]}
        with patch.object(fleet, "verify", side_effect=verify), patch.object(
                fleet, "ThreadPoolExecutor", wraps=fleet.ThreadPoolExecutor) as pool:
            report = fleet.audit(targets, 2)
            pool.assert_called_once_with(max_workers=2)
        self.assertEqual([r['repository'] for r in report['results']], [t['repository'] for t in targets])
        self.assertEqual(report['counts'], dict(compliant=1, drift=1, unavailable=1, not_configured=0, error=1))
        self.assertTrue(report['readOnly'])
        self.assertIn("sunstriker2009/sun-3 | error", fleet.summary(report))

    def test_allowlist_rejects_duplicates_external_owners_and_bad_checks(self):
        invalid = [[TARGET, TARGET], [{**TARGET, "repository": "other/sun-foundry"}],
                   [{**TARGET, "requiredChecks": ["build", "build"]}],
                   [{**TARGET, "requiredChecks": ["build,apply"]}],
                   [{**TARGET, "requiredChecks": []}], []]
        with tempfile.TemporaryDirectory() as directory:
            p = Path(directory) / 'targets.json'
            for rows in invalid:
                p.write_text(json.dumps(dict(schemaVersion=1, repositories=rows)))
                with self.assertRaises(ValueError):
                    fleet.load_targets(p)
            p.write_text(json.dumps(dict(schemaVersion=1, repositories=[TARGET])))
            self.assertEqual(fleet.load_targets(p), [TARGET])


if __name__ == '__main__':
    unittest.main()
