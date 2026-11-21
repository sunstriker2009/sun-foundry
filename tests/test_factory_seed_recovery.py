"""Exercise Factory's preparation step with an isolated GitHub API stub."""

import hashlib
import json
import os
from pathlib import Path
import subprocess
from tempfile import TemporaryDirectory
from textwrap import dedent
import unittest


ROOT = Path(__file__).resolve().parents[1]
TARGET = "sun-seed-recovery-fixture"
REPO = f"sunstriker2009/{TARGET}"
MANIFEST = {"family-id": "SUN-P003", "product-name": "Seed Recovery Fixture", "short-description": None}
EMPTY_BLOB = "e69de29bb2d1d6434b8b29ae775ad8c2e48c5391"
SEED_BRANCH = "chore/sun-governance-ci-seed"

# Match the GitHub CLI calls made by the preparation step and the real seed helpers.
GITHUB_STUB = r'''
import os
import sys
from pathlib import Path

args = sys.argv[1:]
endpoint = next(a for a in args if a.startswith("repos/"))
route = endpoint.removeprefix("repos/" + os.environ["TEST_REPO"])
state = os.environ["TEST_STATE"]
fixture = Path(os.environ["TEST_FIXTURE"])
if "-X" in args:
    with (fixture / "writes").open("a") as log:
        print(args[args.index("-X") + 1], route, file=log)
    if route == "/pulls":
        print("17")
    elif not route.startswith("/contents/docs/SUN-GOVERNANCE-CI-SEED.md"):
        raise SystemExit(2)
elif route == "":
    print("main" if "--jq" in args else "{}")
elif route.startswith("/contents/branding/"):
    ref = args[args.index("-f") + 1]
    if ref == "ref=main" or state == "unseeded":
        raise SystemExit(1)
    if route.endswith(".gitkeep"):
        print(os.environ["TEST_EMPTY_BLOB"])
    else:
        print((fixture / "manifest").read_text())
elif route in ("/git/ref/heads/main", "/git/ref/heads/chore/sun-governance-ci-seed"):
    print("a" * 40)
elif route.startswith("/contents/.github/workflows/"):
    print(route)
elif route.startswith("/pulls?"):
    print("17" if state in ("open", "unrelated") else "")
elif route == "/pulls/17":
    head = "unrelated" if state == "unrelated" else os.environ["TEST_BRANCH"]
    print(f"open|main|{head}|{os.environ['TEST_REPO']}")
elif route == "/branches/chore/sun-governance-ci-seed":
    print("{}")
elif route.startswith("/contents/docs/SUN-GOVERNANCE-CI-SEED.md"):
    raise SystemExit(1)
elif route.startswith("/contents/README.md"):
    print((fixture / "readme").read_text())
elif route.startswith("/git/commits/"):
    print("b" * 40)
elif route.startswith("/git/trees/"):
    print((fixture / "tree").read_text())
else:
    raise SystemExit(f"Unexpected GitHub API route: {endpoint}")
'''


class FactorySeedRecoveryTests(unittest.TestCase):
    def run_preparation(self, state):
        workflow = (ROOT / ".github/workflows/repository-factory-v1.yml").read_text()
        step = workflow.split("      - name: Create or locate repository and seed PR\n", 1)[1]
        step = step.split("\n      - name:", 1)[0]
        shell = dedent(step.split("        run: |\n", 1)[1])
        branding = (ROOT / "scripts/prepare-product-branding.sh").read_text()
        readme = branding.split("clean_readme=$(cat <<'EOF'\n", 1)[1].split("\nEOF", 1)[0]
        manifest = json.dumps(MANIFEST, indent=2) + "\n"
        data = manifest.encode()
        manifest_sha = hashlib.sha1(f"blob {len(data)}\0".encode() + data).hexdigest()

        with TemporaryDirectory() as directory:
            fixture = Path(directory)
            (fixture / "manifest").write_text(manifest)
            (fixture / "readme").write_text(readme)
            (fixture / "tree").write_text(json.dumps({"truncated": False, "tree": [
                {"path": path, "sha": sha, "mode": "100644", "type": "blob"}
                for path, sha in (
                    ("branding/manifest.json", manifest_sha),
                    ("branding/revisions/.gitkeep", EMPTY_BLOB),
                )
            ]}))
            gh = fixture / "gh"
            gh.write_text("#!/usr/bin/env python3\n" + GITHUB_STUB)
            gh.chmod(0o755)
            output = fixture / "output"
            output.touch()
            writes = fixture / "writes"
            writes.touch()
            env = dict(os.environ, PATH=f"{fixture}{os.pathsep}{os.environ['PATH']}",
                       GH_TOKEN="fixture", TARGET=TARGET, APPROVED_MANIFEST=manifest,
                       GITHUB_OUTPUT=str(output), GITHUB_STEP_SUMMARY=str(fixture / "summary"),
                       TEST_REPO=REPO, TEST_BRANCH=SEED_BRANCH, TEST_STATE=state,
                       TEST_EMPTY_BLOB=EMPTY_BLOB, TEST_FIXTURE=directory)
            result = subprocess.run(["bash", "-c", shell], cwd=ROOT, env=env,
                                    capture_output=True, text=True, timeout=15)
            return result, output.read_text().splitlines(), writes.read_text().splitlines()

    def test_seed_branch_without_pr_gets_one_pr(self):
        result, outputs, writes = self.run_preparation("ready")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(outputs, [f"repository={REPO}", "pr=17"])
        self.assertEqual(writes, ["PUT /contents/docs/SUN-GOVERNANCE-CI-SEED.md", "POST /pulls"])

    def test_open_seed_pr_is_reused_without_writes(self):
        result, outputs, writes = self.run_preparation("open")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(outputs, [f"repository={REPO}", "pr=17"])
        self.assertEqual(writes, [])

    def test_existing_repository_without_approved_seed_stops_without_writes(self):
        result, outputs, writes = self.run_preparation("unseeded")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Existing repository has no matching approved seed", result.stdout)
        self.assertEqual((outputs, writes), ([], []))

    def test_unrelated_open_pr_stops_without_writes(self):
        result, outputs, writes = self.run_preparation("unrelated")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("does not match expected seed PR", result.stdout)
        self.assertEqual(outputs, [f"repository={REPO}"])
        self.assertEqual(writes, [])
