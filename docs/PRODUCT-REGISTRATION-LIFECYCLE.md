# Foundry product registration lifecycle

**Status:** Working draft for discussion. The existing factory and registration workflows remain in use until an approved rollout.

## Ownership

| Component | Responsibility |
|---|---|
| SUN Ecosystem | Defines naming, family and ID conventions, governance, and branding standards. Publishes the product registry and gallery using metadata supplied by Foundry. |
| Foundry | Owns the operational product catalog, the implemented family mappings and next IDs, registration validation, repository provisioning, and metadata publication. |
| Product repository | Stores its identity in `branding/manifest.json` and maintains its own artwork and revision history. |

CodeFolio's [original registration](https://github.com/sunstriker2009/sun-ecosystem/pull/55) illustrates the earlier handoff. The factory created the repository, then the Ecosystem PR was updated separately to confirm its family and ID. In the Foundry lifecycle, the owner's dispatch approves the registration and the merged registry PR records the assignment.

## Registration inputs

| Field | Behavior |
|---|---|
| Product name | Required text. Preserve the approved display spelling, such as CodeFolio. |
| Product family | Required dropdown. Choose Productivity or Application component. |
| Family ID | Derived from the selected family's next available ID. Show it as read-only wherever there is a live preview. |
| Repository name | Derived by applying the naming policy's kebab-case rules and adding the `sun-` prefix. Show it as read-only wherever there is a live preview. |
| Short description | Optional single-line text. See [description handling](#description-handling). |

### Propose a registration

As the repository owner, open [Propose SUN Product Registration](https://github.com/sunstriker2009/sun-foundry/actions/workflows/propose-product-registration.yml) and run it on `main`. Enter the base name, select the product family, and optionally enter a short description. Dispatching approves the proposed registration. The workflow opens a catalog PR and shows the derived ID, slug, and PR link in its summary. It uses the owner's credential to squash-merge the exact proposal after the required build passes. The existing `repository-administration` environment applies to both proposal and provisioning and may prompt for approval.

The native GitHub Actions form presents text fields and a fixed dropdown. A dedicated Foundry form could show live previews before submission. See [GitHub Actions workflow input syntax](https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax#onworkflow_dispatchinputs).

The owner-approved squash merge dispatches Foundry's Repository Factory on `main`. The factory publishes to Ecosystem after the seed is verified.

### Merge-time validation

The required `build` check validates the proposed catalog against the base of GitHub's PR merge preview. Foundry's existing strict status-check rule requires the PR to be up to date with `main` when it merges. The check recomputes the identity, verifies the next ID for the selected family, and checks that the catalog changes match that one proposal.

Each proposal branch includes the candidate ID and repository slug. If an earlier merge advances the same family's counter, check the current catalog for the revised ID and run the workflow again to authorize a new PR. Close the superseded PR. Proposals created before the ID was added to branch names also need a fresh run.

## Registration rules

### Display name and repository slug

Use the [SUN naming guidelines](https://github.com/sunstriker2009/sun-ecosystem/blob/main/branding/NAMING-GUIDELINES.md) for owner review. Enter the base product name, then derive the endorsed name by appending ` by Sun`. Strip outer spaces and retain the chosen capitalization and word spacing in the display name. For the initial workflow, accept ASCII letters, digits, spaces, and hyphens, with at least one letter and an alphanumeric character at each end after trimming. If the name contains other characters, explain which characters the workflow accepts so the owner can revise the proposal.

To derive the repository slug, lowercase the base name and replace each run of spaces or hyphens with one hyphen. Add `sun-` once. Treat casing within a word as part of its spelling, so CodeFolio stays a single slug segment. Ask for the base name if the input already includes the `sun-` prefix or the `by Sun` endorsement. The complete slug must fit the current factory's 100-character limit.

| Base product name | Endorsed display name | Repository slug |
|---|---|---|
| CodeFolio | CodeFolio by Sun | `sun-codefolio` |
| Data Studio | Data Studio by Sun | `sun-data-studio` |
| API-Workbench | API-Workbench by Sun | `sun-api-workbench` |

Check proposed names case-insensitively against recorded current and historical names. Check the resulting slug against the catalog and the target GitHub owner. A name or slug collision requires a revised proposal. Source existing names and slugs as recorded when seeding the catalog.

### Product families

| Dropdown label | Product registry family | ID format | Ecosystem catalog classification |
|---|---|---|---|
| Productivity | `productivity` | `SUN-PNNN` | `product` |
| Application component | `application_component` | `SUN-CNNN` | `product` |

Governance and shared infrastructure use the separate `SUN-GNNN` series and stay outside the product registration dropdown. Each product family uses its own next ID from Foundry's catalog. The proposed ID becomes assigned on owner merge. Assigned IDs remain stable across renames and repository moves.

### Description handling

Trim outer whitespace. Treat empty or whitespace-only input as omitted. For a supplied description, accept a single line of up to 180 characters and reject `<`, `>`, `|`, `[`, and `]` to match the [Ecosystem gallery validator](https://github.com/sunstriker2009/sun-ecosystem/blob/main/scripts/render-repository-gallery.py). Use the trimmed text in Foundry, the manifest, and the Ecosystem summary.

When omitted, store JSON `null` in Foundry and in the manifest's `short-description` field. Publish a family-specific summary in Ecosystem so its gallery has a nonempty value. Use `Productivity product by Sun` for Productivity and `Application component by Sun` for Application component.

## Workflow sequence

1. **Approve and propose registration.** The owner dispatches the workflow to approve the registration. Foundry checks the name, family and candidate ID, derives the repository slug, and checks uniqueness and GitHub availability. It opens a registry PR with the identity and next-ID update.
2. **Verify and merge the registration.** Required CI validates the proposed ID against Foundry `main`. Foundry automatically squash-merges the exact verified PR head using the owner's credential. A failed check or stale proposal leaves the PR open. The merge commits the ID allocation and starts the factory relay.
3. **Provision and verify.** A relay dispatches [Repository Factory v1](REPOSITORY-FACTORY-V1.md) on `main` after the owner squash-merges the registration. Before the protected administration job can start, a read-only check verifies the merge and confirms the identity is still active in Foundry. The factory uses the current Strata template and creates a public repository. The seed PR includes `branding/manifest.json` with `family-id`, `product-name`, and `short-description`, and retains the revision marker. After CI and strict governance verification pass, the factory checks the manifest and marker at the tested head SHA and automatically squash-merges that exact SHA through GitHub's protected PR merge.
4. **Publish to Ecosystem.** After the seed PR lands, Foundry verifies the manifest and revision marker at the new repository's `main` commit. It opens an Ecosystem PR with the confirmed identity, repository catalog entry, registry documentation, and regenerated README gallery. Foundry requests protected squash auto-merge, so GitHub merges after the required checks pass. The branding upload workflow can recognize the product once the entry is on Ecosystem `main`. Publish approved artwork and the gallery icon through the existing branding flow.

GitHub supports [triggering Actions when a PR merges](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows#running-your-pull_request-workflow-when-a-pull-request-merges). Confirm which authorized credential the factory and publisher will use so downstream PR checks run automatically. See [GitHub's workflow-trigger guidance](https://docs.github.com/en/actions/how-tos/write-workflows/choose-when-workflows-run/trigger-a-workflow#triggering-a-workflow-from-a-workflow).

## Recovery and compatibility

- Track progress by approved family ID and repository slug. A retry after a partial failure should resume that registration and preserve its ID. If an existing repository cannot be linked to the approved provisioning attempt, stop for owner review.
- If the merge relay fails, dispatch [Repository Factory](https://github.com/sunstriker2009/sun-foundry/actions/workflows/repository-factory-v1.yml) on `main` with the merged Foundry PR number in `approved_registration_pr` and the exact slug in `confirm_repository`. Leave the other inputs at their defaults. The same verification and administration environment apply.
- Re-running the approved factory job can resume a matching seed branch or verify an already seeded repository. If creation succeeded before the approved manifest was written, the next run stops for inspection because it cannot establish the repository's identity.
- A rerun can reuse an identical Ecosystem publication branch and PR. If the projection has changed or the branch no longer matches the live Ecosystem base, the publisher stops for inspection. An already published matching identity needs no new PR.
- [Foundry's product catalog](../registry/product-catalog.json) is seeded from the [Ecosystem identity registry](https://github.com/sunstriker2009/sun-ecosystem/blob/756599cd7650b1c6d32cbe2a35b2e20de90c1062/registry/products.json) and [repository catalog](https://github.com/sunstriker2009/sun-ecosystem/blob/756599cd7650b1c6d32cbe2a35b2e20de90c1062/registry/repositories.json). The seed preserves current IDs, counters, names, repository slugs and recorded product aliases and retired IDs. It uses the published repository summary as the short description, with the registered purpose used for SUN Ecosystem itself. Unnumbered proposals stay in Ecosystem.
- During the transition, Ecosystem remains the live registry for the existing registration and branding workflows. Keep its published catalog format compatible when Foundry takes over publication.
- Automated merges use their existing required checks and permissions. Foundry's owner-only dispatch authorizes the registry PR.

## Open decisions

- Decide how the post-merge workflow satisfies the existing `repository-administration` environment approval. Document whether a second owner action is expected.
- Define how Foundry reports incomplete registrations and how operators resume them.
- Confirm the cutover point for registry updates and how the existing pending-registration path behaves during migration.
