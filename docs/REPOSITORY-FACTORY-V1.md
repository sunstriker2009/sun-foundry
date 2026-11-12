# SUN Repository Factory v1

Run **SUN Repository Factory v1** from `main` as `sunstriker2009`.

- **create**: enter a new repository name (without owner), visibility, and exact name confirmation.
- **resume**: enter `sunstriker2009/repo-name` twice to continue after partial creation or a CI failure.

The workflow creates (if requested), ensures a disposable seed PR, waits for both template CI checks, then runs Plan, Apply, and strict Verify. The administration credential remains an environment secret. Owner-only execution and main-only deployment restriction remain required.

**Private repositories:** GitHub Free personal accounts may not support rulesets. The existing provisioner intentionally fails closed on Apply/Verify when enforcement is unavailable. This workflow reports that limitation rather than silently treating it as successful governance.

**After success:** squash merge the seed PR manually to validate merge policy and automatic source branch deletion. Do not merge it earlier.

**Recovery:** rerun with mode `resume`. If a seed branch exists without an open PR, inspect and resolve it manually; the workflow will not overwrite it. A closed seed PR will not be reopened.

**Security:** removing environment reviewers trades away independent approval. Restrict writes to main and the administration secret; job-level actor checks alone are not a security boundary.
