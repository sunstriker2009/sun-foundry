# SUN Product Registry v1.1

**Updated:** 2026-11-22. Each family numbers its products independently. **SUN-PNNN** identifies productivity products and **SUN-CNNN** identifies application components. Foundry allocates IDs through an approved registration. See [the operational catalog](product-catalog.json) for the current allocation counters. IDs remain stable across renames and repository moves. Proposals do not reserve IDs or authorize repository creation.

| ID | Name | Family | Purpose | Status | Technical identity |
|---|---|---|---|---|---|
| SUN-C001 | **Outpost** | Application components | Identity, authentication, authorization, security | **CONFIRMED** | Sun.Security |
| SUN-P001 | **Workbench** | Productivity | Interactive scripting workspace and saved connections | **CONFIRMED** | Sun.Workspace |
| SUN-P002 | **CodeFolio** | Productivity | A searchable reference for browsing, testing, and saving regular expressions. | **CONFIRMED** | TBD |
| SUN-P003 | **Playground** | Productivity | Customize and reuse Git, JavaScript, C#, and XPath snippets. | **CONFIRMED** | TBD |

The next publication counters are **SUN-P004** and **SUN-C002**. The [ID migration decision](https://github.com/sunstriker2009/sun-ecosystem/blob/main/decisions/sun-family-ids.md) records the previous IDs.

## Unnumbered product proposals

| Candidate | Purpose | Status | Suggested technical identity |
|---|---|---|---|
| ORBIT | Workflow orchestration and coordination | PROPOSED | Sun.Orchestration (suggested) |
| NOVA | AI agents and intelligent automation | PROPOSED | Sun.Agents (suggested) |
| PRISM | AI intelligence, research, insights | PROPOSED | TBD |
| PULSAR | Event processing and messaging | PROPOSED | TBD |
| LUMEN | Analytics and visualization | PROPOSED | Sun.Analytics (suggested) |
| BEACON | Monitoring and observability | PROPOSED | TBD |
| FORGE | Developer tools and utilities | PROPOSED | TBD |

These names are **unapproved and unnumbered**. Approve a Foundry registration to reserve the next ID before provisioning. Proposed names may be revised, withdrawn or approved later.

SUN Ecosystem (SUN-G001), Strata (SUN-G002), Foundry (SUN-G003), and Foundry Pilot (SUN-G004) are tracked in the separate [governance and infrastructure registry](INFRASTRUCTURE.md). They use the independent SUN-G series. MarketPilot AI remains an independent application and is not part of the SUN product registry.

## SUN-C001 — Outpost
- **Public identity:** Outpost by Sun
- **Tagline:** Identity. Trust. Protection.
- **Repository:** [sun-outpost](https://github.com/sunstriker2009/sun-outpost) (established).
- **Backend packages:** Sun.Security.*
- **Frontend packages:** @sun-security/*
- **Initial integration target:** MarketPilot AI, an independent application.
- **Visual accent:** Solar Gold (provisional).
- **Commercial clearance:** PENDING; confirmation is internal, not trademark clearance.

## Naming risk notes
The proposed names ORBIT, NOVA, PRISM, PULSAR, LUMEN, BEACON and FORGE have potential existing-software associations and require fresh conflict research before approval. PULSAR in particular overlaps with Apache Pulsar in messaging; FORGE overlaps with Atlassian Forge in developer tools.

## SUN-P001 — Workbench
- **Public identity:** Workbench by Sun
- **Tagline:** Organize. Script. Explore.
- **Name:** Confirmed by product owner 2026-11-12 ("Sounds good, kick off").
- **Technical identity:** Sun.Workspace; Sun.Workspace.*; @sun-workspace/*.
- **Repository:** [sun-workbench](https://github.com/sunstriker2009/sun-workbench) (established).
- **Initial scope:** Local code and scripting workspace with folders, tags, smart collections and planned language-aware JavaScript, Python and C# execution adapters. Database connections and Kubernetes support are future extensions; see the product roadmap.
- **Extension direction:** Additional execution providers and transports; implementation planning belongs in the product repository.
- **Commercial clearance:** PENDING. Preliminary exact-name web screening only; trademarks, domains and package availability have not been cleared.

## SUN-P002 — CodeFolio
- **Public identity:** CodeFolio by Sun.
- **Repository:** [sun-codefolio](https://github.com/sunstriker2009/sun-codefolio) (established).
- **Commercial clearance:** PENDING.

## SUN-P003 — Playground
- **Public identity:** Playground by Sun.
- **Repository:** [sun-playground](https://github.com/sunstriker2009/sun-playground) (established).
- **Commercial clearance:** PENDING.
