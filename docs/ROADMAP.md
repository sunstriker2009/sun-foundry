# Foundry roadmap checklist

## Finished

- [x] Provision public STRATA repositories with seed CI and governance Apply/Verify.
- [x] Require a merged product registration for Factory provisioning and manual recovery.
- [x] Assign product identities from Foundry's catalog and validate proposals against current `main`.
- [x] Verify the owner-triggered registration flow end to end. The [registration run](https://github.com/sunstriker2009/sun-foundry/actions/runs/44656473998) automatically merged the proposal, and the [Factory run](https://github.com/sunstriker2009/sun-foundry/actions/runs/44656556761) provisioned the repository, verified governance, merged the seed and proposed Ecosystem publication. The [Foundry rollback](https://github.com/sunstriker2009/sun-foundry/pull/99) and [Ecosystem rollback](https://github.com/sunstriker2009/sun-ecosystem/pull/59) restored the live registries, and the disposable repository was deleted.
- [x] Implement read-only governance fleet auditing and reviewed alignment for mapped rulesets. A previous five-repository pass was operator-reported. Use a fresh audit for current compliance.
- [x] Implement the local asset generator and scoped validation. Validate STRATA's inherited ZIP hook and its required-check dispatches in a [newly provisioned pilot](https://github.com/sunstriker2009/sun-foundry-pilot/actions/runs/44260221893). Verify snapshot rollback and restore with the installer CLI on a [product feature branch](https://github.com/sunstriker2009/sun-outpost/pull/177).
- [x] Synchronize approved symbols through single-repository and daily reconciliation.
- [x] Exercise the shared repository-rename engine through a successful [combined product and repository rename](https://github.com/sunstriker2009/sun-foundry/actions/runs/43934714433).
- [x] Replay Factory after successful provisioning and recover from a restored pre-publication checkpoint. [Factory replay](https://github.com/sunstriker2009/sun-foundry/actions/runs/44831045380) · [Registry republication](https://github.com/sunstriker2009/sun-foundry/pull/110)
- [x] Exercise seed branch and seed PR recovery in CI against controlled GitHub API responses. Verify Factory reuses matching work and stops when the seed identity or PR is unexpected.

## Remaining

- [ ] Validate recovery from a live interruption during repository creation or before seed merge. Confirm the operator experience when the administration environment requests deployment approval.
- [ ] Decide the future of pending registration for existing repositories and how incomplete product registrations will be surfaced.
- [ ] Verify a live product or repository rename across Foundry’s operational catalog, published registry, gallery, and the product manifest.
- [ ] Exercise manual ZIP installer Preview, Apply and rollback through GitHub Actions on an approved disposable target. Verify the required-check dispatches when onboarding or updating an adopter.
- [ ] Expand live governance coverage for private-plan limits and stronger review profiles when those cases are needed. Run the existing fleet audit after material governance changes.
- [ ] Review retained product display, packaging and baked-in artwork references where needed. Review legacy branding archives and recycling folders separately after migration validation.

See the [workflow handbook](WORKFLOWS.md) for procedures and the [handoff](GOVERNANCE-HANDOFF.md) for continuing work.
