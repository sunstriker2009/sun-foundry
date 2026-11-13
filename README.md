# FOUNDRY by Sun

**Build. Standardize. Launch.**

Repository creation and governance automation for SUN products. The canonical GitHub repository is [`sunstriker2009/sun-foundry`](https://github.com/sunstriker2009/sun-foundry).

## Workflows

- **Repository Factory**: create from [sun-repo-template](https://github.com/sunstriker2009/sun-repo-template) or resume interrupted provisioning; seed CI, await required checks, plan, apply and strictly verify governance.
- **Repository Maintenance**: diagnose, plan, apply or verify governance for existing repositories.

See [workflow instructions](docs/WORKFLOWS.md) and [SUN governance policy](https://github.com/sunstriker2009/sun-ecosystem/blob/main/docs/governance/GIT-WORKFLOW.md).

## Safety

Administration workflows require owner-initiated dispatch on protected `main`, use the `repository-administration` environment secret `SUN_REPO_ADMIN_TOKEN`, and retain exact target confirmation for mutations. The rename migration temporarily recognizes both old and new GitHub repository identities. After the rename and a successful Diagnose, remove the old identity in a separate PR.

GitHub Free personal private repositories may not support enforceable rulesets; strict Apply/Verify fails closed when unavailable. Do not treat a successful Plan as enforced governance.

## Local CLI

Requires .NET 10 SDK and `GH_TOKEN`:

```sh
dotnet run --project src/Sun.RepoBootstrap -- --repo sunstriker2009/example --mode plan --checks repository-validation,conventional-title
```

The internal .NET project and namespaces remain `Sun.RepoBootstrap` for now; repository branding does not require a code namespace migration.
