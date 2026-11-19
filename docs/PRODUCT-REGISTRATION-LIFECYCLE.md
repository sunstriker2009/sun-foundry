# Foundry product registration lifecycle

**Status:** Working draft for discussion. The existing factory and registration workflows remain in use until an approved rollout.

## Ownership

| Component | Responsibility |
|---|---|
| SUN Ecosystem | Defines naming, family and ID conventions, governance, and branding standards. Publishes the product registry and gallery using metadata supplied by Foundry. |
| Foundry | Owns the operational product catalog, the implemented family mappings and next IDs, registration validation, repository provisioning, and metadata publication. |
| Product repository | Stores its identity in `branding/manifest.json` and maintains its own artwork and revision history. |

CodeFolio's [registration](https://github.com/sunstriker2009/sun-ecosystem/pull/55) illustrates the current handoff. The factory created the repository, then the Ecosystem PR was updated separately to confirm its family and ID. The proposed lifecycle makes the Foundry registry PR the point of owner approval.

## Registration inputs

| Field | Behavior |
|---|---|
| Product name | Required text. Preserve the approved display spelling, such as CodeFolio. |
| Product family | Required dropdown. Start with Productivity (`productivity`, `SUN-PNNN`) and Application component (`application_component`, `SUN-CNNN`). The published repository catalog classifies either family as `product`. |
| Family ID | Derived from the selected family's next available ID. Show it as read-only wherever there is a live preview. |
| Repository name | Derived by applying the naming policy's kebab-case rules and adding the `sun-` prefix. Show it as read-only wherever there is a live preview. |
| Short description | Optional text. Decide how to represent an omitted value in the manifest and the Ecosystem catalog, whose gallery validator currently requires a summary. |

The initial GitHub Actions form can provide text fields and a fixed dropdown. Since it cannot calculate live read-only labels, show the derived values in the workflow summary and approval PR. A dedicated Foundry form could preview them before submission. See [GitHub Actions workflow input syntax](https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax#onworkflow_dispatchinputs).

## Workflow sequence

1. **Propose registration.** Validate the product name against SUN policy, resolve the family and candidate ID, and derive the repository slug. Check for duplicate names, IDs, and slugs in Foundry and check that the target repository is available on GitHub. Open a Foundry registry PR containing the exact identity and next-ID update. Keep auto-merge disabled.
2. **Approve registration.** The owner reviews and squash-merges the Foundry PR. The merge commits the ID allocation and authorizes provisioning. Validate uniqueness and the next ID against current Foundry `main` before merge. An outdated proposal must refresh and show any changed ID for review.
3. **Provision and verify.** Trigger provisioning from a merged registration PR on Foundry `main`. Read the approved metadata from the merge commit and reuse [Repository Factory v1](REPOSITORY-FACTORY-V1.md) and Strata. Include `branding/manifest.json` in the seed PR with `family-id`, `product-name`, and `short-description`, subject to the description decision above. Keep the revision directory marker. Enable squash auto-merge for the seed PR after required CI and strict governance verification pass.
4. **Publish to Ecosystem.** Once the seed PR lands and Foundry verifies the manifest on the new repository's `main`, open a generated Ecosystem PR with the confirmed metadata and updated references. Enable squash auto-merge after the required checks pass. The branding upload workflow can recognize the product once the entry is on Ecosystem `main`. Publish approved artwork and the gallery icon through the existing branding flow.

GitHub supports [triggering Actions when a PR merges](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows#running-your-pull_request-workflow-when-a-pull-request-merges). Confirm which authorized credential the factory and publisher will use so downstream PR checks run automatically. See [GitHub's workflow-trigger guidance](https://docs.github.com/en/actions/how-tos/write-workflows/choose-when-workflows-run/trigger-a-workflow#triggering-a-workflow-from-a-workflow).

## Recovery and compatibility

- Track progress by approved family ID and repository slug. A retry after a partial failure should resume that registration and preserve its ID. If an existing repository cannot be linked to the approved provisioning attempt, stop for owner review.
- Verify repository governance and the expected manifest before publishing. If Ecosystem publication fails, resume publication using the approved identity.
- Seed Foundry from current registrations, preserving assigned IDs and current family counters. Keep Ecosystem's published catalog format compatible with existing branding installers during the transition.
- Limit auto-merge to the generated seed and Ecosystem PRs within their existing checks and permissions. Keep the Foundry registration PR as the manual approval gate.

## Open decisions

- Define the slug normalization rules for spacing, punctuation, acronyms, and multiword names.
- Decide how the optional description is represented in the manifest and the required Ecosystem summary.
- Decide how the post-merge workflow satisfies the existing `repository-administration` environment approval. Document whether a second owner action is expected.
- Define how Foundry reports incomplete registrations and how operators resume them.
- Confirm the cutover point for registry updates and how the existing pending-registration path behaves during migration.
