# Visibility-aware SUN governance

The provisioner checks repository visibility and attempts to read repository rulesets.

When GitHub responds with the specific plan restriction **"Upgrade to GitHub Pro or make this repository public"** for a private repository:

- **audit / plan:** exit successfully with an explicit **GOVERNANCE CAPABILITY** warning and **NOT ENFORCED** message. This is a capability assessment, **not** proof of governance compliance.
- **apply / verify:** fail closed with a clear error. No partial fallback is silently treated as equivalent to enforced branch protection.
- **Other 403 / 404 responses:** remain errors; these may indicate permissions, missing resources, or another problem.

This does not change repository visibility or configure alternate branch protection. Repository merge settings alone do not substitute for ruleset enforcement.

Test matrix: public repository with rulesets; private repository with rulesets; private repository receiving the plan-restriction 403; private repository receiving unrelated 403; repository inaccessible (404).