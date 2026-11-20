# SUN Governance & Infrastructure Registry v1.1

**Updated:** 2026-11-18

Governance and shared engineering infrastructure use the **SUN-GNNN** identifier series. Productivity products use **SUN-PNNN**, and application components use **SUN-CNNN**. IDs are assigned sequentially only when a repository/component is formally established; proposed entries do not reserve numbers.

| ID | Component | Public identity | Purpose | Repository | Classification |
|---|---|---|---|---|---|
| SUN-G001 | **SUN Ecosystem** | SUN — The Product Ecosystem | Parent governance, branding and standards | [sun-ecosystem](https://github.com/sunstriker2009/sun-ecosystem) | Governance authority |
| SUN-G002 | **Strata** | Strata by Sun — Structure. Foundation. Growth. | Reusable repository template and standard starting structure | [sun-strata](https://github.com/sunstriker2009/sun-strata) | Repository template |
| SUN-G003 | **Foundry** | Foundry by Sun — Build. Standardize. Launch. | Repository creation, governance application, CI seeding and verification | [sun-foundry](https://github.com/sunstriker2009/sun-foundry) | Repository factory |
| SUN-G004 | **Foundry Pilot** | Foundry Pilot | Isolated repository for validating Foundry provisioning and inherited branding | [sun-foundry-pilot](https://github.com/sunstriker2009/sun-foundry-pilot) | Validation repository |

**Next governance/infrastructure ID:** SUN-G005.

## Numbering governance

1. **SUN-GNNN** identifies established governance, templates, tooling, and shared ecosystem infrastructure. Each [product family](PRODUCTS.md) maintains its own sequence.
2. Assign the next sequential ID **upon confirmation/establishment**, never when a candidate is merely proposed.
3. Keep IDs permanent across renaming or repository relocation; do not reuse retired IDs. Corrections require an explicit documented decision.
4. SUN-G classification does **not** imply a runtime dependency on the SUN Ecosystem repository. Strata and Foundry remain independently versioned repositories.
5. Do not introduce additional prefix series without an explicit governance decision.

Foundry allocates SUN-P and SUN-C IDs in its [operational catalog](product-catalog.json). The [machine-readable registry](products.json) contains all three series. Implementation and releases remain in each component's own repository.
