# Repository selection in FOUNDRY workflows

The owner is always `sunstriker2009`; workflow forms use short repository names. Choose a known repository from the dropdown and leave `repository_name` empty. Where a confirmation is required, type only the same short name, such as `sun-foundry`. Existing backend scripts still receive the full `sunstriker2009/sun-foundry` target and confirmation.

| Workflow | Repository selection |
| --- | --- |
| Repository Factory — create | Select `other-repository`, enter the new short name in `repository_name`, repeat that short name as confirmation. |
| Repository Factory — resume | Choose a listed repository, or `other-repository` plus its short name; repeat the short name. |
| Repository Maintenance | Choose a listed repository or another existing short name; confirmation is required for Apply. |
| Register SUN Repository | Choose a listed repository or another existing short name; repeat the short name. Registration still validates live access and registry identity. |
| Sync Approved SUN Symbol / legacy approval entry | Choose a listed symbol repository or another registered short name; repeat the short name. Backend registry and PNG checks still apply. |
| SUN Governance Alignment | Restricted dropdown of four configured repositories. Apply needs the short-name confirmation and reviewed Plan run ID. |
| Governance Fleet Audit / reconciliation / asset validation | No repository input; existing configured scope is unchanged. |

For example, alignment Plan uses `repository: sun-foundry`, `operation: plan`, with the Apply fields empty. Apply uses `repository: sun-foundry`, the successful Plan run ID and `confirm_repository: sun-foundry`. Plan artifacts retain fully qualified repository identities, so reviewed-plan matching is unchanged.

Known choices are versioned in `config/workflow-repositories.json` and the workflow YAML. Alignment choices come from its separate explicit ruleset-ID policy. These are curated dropdowns, not a live account inventory. Update the list and affected dropdowns together when adding a repository; `python3 scripts/resolve-workflow-repository.py --check-workflows` detects mismatches. The `other-repository` route avoids needing a dropdown update before creating or registering a new repository.

The shared resolver rejects foreign owners, slashes in short names, whitespace, mismatched confirmation and stale custom fields. Same-owner fully qualified values remain accepted by the resolver for compatibility, but operators no longer need to enter them. Existing direct CLI commands continue to use fully qualified repository names. No administrative permissions, environment gates, backend allowlists or source validation checks are changed.

Factory runs are serialized to avoid different selections or aliases provisioning the same repository concurrently. The other-repository name field never accepts an owner override.
