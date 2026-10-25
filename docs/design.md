# Property Compliance Platform: design

A portfolio project to learn and demonstrate **domain-driven design** and **event-driven architecture**
with React + TypeScript, ASP.NET Core, EF Core and Azure, running at £0.

This repo holds **Repairs**: social housing repairs and Awaab's Law hazard compliance.

A second project, **Elections** (replay of a UK general election night from open results data), will live in
**its own repo** and reuse this repo's platform code (building blocks, Aspire defaults, Terraform modules, CI workflows).

> Repo: `property-compliance-platform`.

---

## 1. Domain primer: Awaab's Law

Awaab's Law (in force for social landlords in England from **27 October 2025**) sets legal deadlines
for dealing with hazards in tenants' homes.

Primary source: *The Hazards in Social Housing (Prescribed Requirements) (England) Regulations 2025*,
as amended from 30 November 2026 (regulation numbers below refer to it). The legal basis is
section 10A of the Landlord and Tenant Act 1985 (inserted by section 42 of the Social Housing (Regulation) Act 2023):
the duties are an **implied term of the tenancy**, so tenants can sue for breach and a court can order the work done.

| Rule | Deadline | Reg |
|---|---|---|
| Emergency hazard: investigate **and** complete safety work | 24 **hours** from reasonable grounds to believe there's an emergency hazard | 5 |
| Standard investigation | 10 working days, starting the day after the landlord becomes aware | 6 |
| Tenant asks for a physical inspection mid-investigation | clock **restarts**: 10 working days from the day after the request | 6(2)(b) |
| Tenant asks for a physical inspection after a desk-based investigation | renewed investigation within 10 working days of the request | 7 |
| Further investigation needed to scope the work | "as soon as reasonably practicable" | 8 |
| Written summary to tenant | 3 working days after any investigation, **unless** the work is completed within that time | 9 |
| Significant hazard: complete safety work | 5 working days after the investigation | 11 |
| Supplementary preventative work (stop it recurring) | begin within 5 working days, or if not practicable, within **12 weeks**; complete within a reasonable period | 13 |
| Keep tenant updated on required work, and tell them when it's done | ongoing | 14 |
| Safety work won't be done in time | **suitable alternative accommodation at no cost** from the end of the period, unless refused; plus written safety advice | 15–17 |
| Entry to the home without consent | reasonable times, with at least 24 hours' written notice | 20 |

"Working day" excludes weekends, Christmas Day, Good Friday and bank holidays in England and Wales.

**Definitions are themselves time-based (reg 3):** a *significant* hazard is one a reasonable landlord, knowing the
occupier's health and circumstances, would make safe within 15 working days (but not 24 hours); an *emergency*
hazard is one they'd make safe within 24 hours. So **vulnerability data from the tenancy affects classification**.

**Not a relevant hazard** if it's wholly or mainly caused by the tenant's breach of the tenancy, or is a fire hazard
in common parts covered by the Fire Safety Order. Duties **stop** when the landlord has exhausted reasonable
endeavours to get a third party's consent, or a later investigation finds no hazard or no safety work.

**Scope by phase.** Since 27 October 2025: emergency hazards of any HHSRS type (except lack of space), and
significant hazards from damp and mould. From 30 November 2026 (Phase 2): significant hazards also include
excess cold and heat, falls, fire, electrical, structural collapse and explosions, and others. Phase 3 (expected 2027):
the remaining HHSRS hazards except overcrowding.
This is a perfect DDD showcase: **a regulation change becomes a dated policy in the domain model**
(`HazardScopePolicy` effective from a date), not a rewrite.

**Transitional rule (reg 21):** for a problem the landlord already knew about before the relevant start date,
the clock starts when it is *first reported after* that date, or on a material change. That's a data-migration rule
the model has to support.

### What this means for the model

- **Two kinds of statutory period:** clock hours (24h, from an instant) and working days/weeks (from the *day after* an event).
  A `StatutoryPeriod` value object with `Start(trigger)` → `Deadline`, tested heavily.
- **Investigation is an entity with a type** (emergency, standard, renewed, further). Each type has its own clock and outcome.
- **Clocks restart and stop.** A physical-inspection request restarts one; "reasonable endeavours exhausted" or a
  "no hazard" finding stops others. Model these as events on the case, never as edits to a date field.
- **`HazardCase` should be event-sourced.** The case history is the landlord's legal evidence in a disrepair claim or
  an Ombudsman complaint. An append-only event stream is the natural audit trail, and gives a strong reason to use
  event sourcing here (and only here).
- **Appointment invariant:** a forced-entry appointment can't be booked with under 24 hours' written notice.
- **Written-summary exemption:** the `WrittenSummaryDue` deadline is cancelled if the required work completes inside 3 working days.
- **Temporary rehousing** is a branch of the process: `RehousingRequired` → offer → accepted/refused → ended.

Sources: [The regulations as they apply from 30 November 2026 (GOV.UK)](https://assets.publishing.service.gov.uk/media/6a54d0862467584757371e07/Awaab_s_Law_Regulations_as_they_apply_from_30_November_2026.pdf),
[legislation.gov.uk](https://www.legislation.gov.uk/ukdsi/2025/9780348273083),
[Procurement for Housing](https://procurementforhousing.co.uk/awaabs-law-requirements-and-deadlines-the-complete-breakdown/),
[Chesterfield BC](https://chesterfield.gov.uk/housing/health-and-safety-at-home/awaabs-law),
[OTS Solicitors on Phase 2](https://www.otssolicitors.co.uk/news/awaabs-law-phase-2-new-social-housing-repair-deadlines-from-30-november-2026/),
[Bevan Brittan on Phase 2](https://www.bevanbrittan.com/insights/articles/2026/awaab-s-law-phase-2-what-social-housing-landlords-need-to-do-before-november-2026/).
The README will say the model is simplified and not legal advice.

---

## 2. Stakeholders and personas

### The household

| Stakeholder | Role | In the system |
|---|---|---|
| **Tenant (lessee)** | Reports problems, gives access, can request a physical inspection, can refuse temporary accommodation | **Tenant portal** persona; legal party to the tenancy |
| **Other occupants** | Children, elderly or disabled relatives; their health decides severity | Vulnerability flags on the household; no login |
| **Advocates** | Family, support workers, councillors, MPs, tenant associations reporting on the tenant's behalf | "Reported by third party" route into concern intake |

### Inside the landlord

| Stakeholder | Role | In the system |
|---|---|---|
| **Contact centre / repairs desk** | Takes reports; makes the first triage decision | **Contact centre** persona; their triage can start the 24-hour clock |
| **Competent investigators** | Surveyors and damp and mould specialists who investigate and record the legal finding | **Investigator** persona; competence tracked per hazard category |
| **Repairs schedulers** | Turn required work into work orders; book appointments with 24 hours' notice where needed | **Scheduler** persona; Repairs context |
| **In-house repair teams** | Do the work; may spot hazards on site, which starts a clock | Contractor app (internal) |
| **Housing officers** | Know the household and hold vulnerability information; can raise concerns | Tenancies context; a source of concerns |
| **Temporary accommodation team** | Provides alternative accommodation when the home can't be made safe in time | Rehousing branch of the process |
| **Compliance manager** | Watches clocks at risk and steps in before a breach | **Compliance manager** persona; Oversight dashboard |
| **Complaints team** | Handles complaints under the Housing Ombudsman's code | Reads case history |
| **Legal / disrepair team** | Defends claims using the evidence trail | Reads and exports the event-sourced case history |
| **Board / senior leadership** | Accountable for consumer-standard compliance | Aggregate reports: breach rates, trends |

### Outside the landlord

| Stakeholder | Role | In the system |
|---|---|---|
| **External contractors** | Attend, make safe, complete, record no-access | **Contractor** persona; simulated in the demo |
| **Third parties needing to consent** | Freeholders, neighbours, utilities, planning; refusal can end a duty once reasonable endeavours are exhausted | "Consent sought / refused" events |
| **Regulator of Social Housing** | Inspects against consumer standards; collects Tenant Satisfaction Measures | Report outputs |
| **Housing Ombudsman** | Rules on complaints, orders compensation | Evidence trail |
| **County Court** | Hears disrepair claims; can order specific performance | Evidence trail; reason the history is immutable |
| **Claims management firms / tenant solicitors** | Pursue claims, sometimes advising tenants to refuse access | Detailed no-access records |
| **Local authority environmental health** | Can enforce housing standards against housing associations | Source of concerns |
| **NHS / GPs / health visitors** | Supply health evidence | Evidence attached to the household or case |
| **Information Commissioner's Office** | Health data is special category data under UK GDPR | Design constraint |
| **MHCLG** | Sets the rules and changes them by phase | Dated policies (`HazardScopePolicy`) |

### Design consequences

1. **Six v1 personas**, switchable in the demo with no real auth: Tenant, Contact centre, Investigator, Scheduler,
   Contractor, Compliance manager. Each maps to one bounded context's screens.
2. **"Becoming aware" has many sources** (tenant, advocate, operative, housing officer, environmental health, GP letter),
   so **concern intake** is a distinct step that records source and time, and any source starts the same clock.
3. **Health data minimisation.** Only Tenancies stores health details. Hazard Compliance receives **flags**
   (`ChildUnder5`, `RespiratoryCondition`), never medical notes.
4. **Readers of the event log** (legal, complaints, Ombudsman, courts) read and never write: CQRS with an immutable history.
5. **Future change:** the Renters' Rights Act 2025 lets government extend Awaab's Law to private landlords (no date set).
   Keep "landlord" generic; record it in an ADR.

---

## 3. Ubiquitous language

| Term | Meaning |
|---|---|
| **Repair request** | A tenant reports a problem (leak, boiler, damp, broken stair rail) |
| **Hazard case** | A repair request that may be an Awaab's Law hazard; it owns the regulatory clock |
| **Concern** | Anything that makes the landlord aware of a possible hazard, from any source; starts the clock |
| **Triage** | Decision at intake (or later): are there reasonable grounds to believe it's an emergency? |
| **Investigation** | Visit or virtual assessment (emergency, standard, renewed or further) by a competent investigator |
| **Finding** | The investigator's professional conclusion: Emergency, Significant, or Not relevant, with reasons |
| **Competent investigator** | Someone the landlord reasonably believes has the skills to classify that type of hazard |
| **Vulnerability flag** | A minimal marker (e.g. `ChildUnder5`) shared from Tenancies; never medical detail |
| **Written summary** | Statutory letter to the tenant explaining findings and next steps |
| **Work order** | A unit of work issued to a contractor |
| **Make safe** | Work that removes the immediate risk (may be followed by further works) |
| **No access** | Contractor attended but couldn't get in; clocks have rules for this |
| **Working day** | Mon–Fri excluding bank holidays in England and Wales |
| **Breach** | A statutory deadline passed without the required action |

---

## 4. Triage vs finding: who decides severity

**Principle: a person decides; the system makes sure they decide properly, and records how.**

The regulations give the decision to people: only a *competent investigator* can conclude an investigation (reg 2),
the test is what a *reasonable landlord with the relevant knowledge* would do (reg 3), and the investigation *must take
into account* what the tenant or others say about the impact on health (regs 5–7). A rules engine can't do that, and
"the system said so" is a weak defence in a disrepair claim.

### Two separate decisions

| Decision | When | Who | Legal effect |
|---|---|---|---|
| **Triage**: reasonable grounds to believe it's an emergency? | At intake, or **any time later** | Contact centre / duty officer | If yes, a 24-hour clock starts now (reg 5, Condition 1) |
| **Finding**: what did the investigation conclude? | When the investigation completes | Competent investigator | Sets make-safe clocks, written summary deadline, possibly rehousing |

The system may **suggest** a triage outcome from simple rules (e.g. mould in a bedroom + child under 2 → suggest
emergency), always showing why. A person confirms it.

### Rules the domain model enforces

- **Competence:** only an investigator competent for the hazard category can conclude the investigation.
- **Everything known is considered:** every vulnerability flag and tenant statement must be acknowledged before a finding is accepted (reg 6(3)(d) as an invariant).
- **Downgrades need reasons:** a finding less severe than the triage or the system's suggestion needs a written rationale; both are kept.
- **"Caused by the tenant" needs evidence and a second sign-off:** this is how Awaab's case was dismissed ("lifestyle"), so it is never a free dropdown choice.
- **Lean towards safety:** when unsure, the default is the more severe classification.
- **Reclassification is an event, not an edit:** new information produces a material change, renewed or further investigation; clocks follow. Grounds for an emergency on day 6 start a new 24-hour clock from that moment.

```csharp
public sealed record Finding(
    HazardSeverity Severity,            // Emergency | Significant | NotRelevant
    HhsrsCategory Category,
    InvestigatorId Investigator,
    string Rationale,
    IReadOnlyList<ConsiderationId> ConsideredItems,   // vulnerability flags, tenant statements
    IReadOnlyList<EvidenceId> Evidence,               // photos, moisture readings
    Exclusion? Exclusion);                            // e.g. TenantBreach (needs second sign-off)

public void Conclude(Finding finding, IInvestigatorRegister register, TimeProvider clock)
{
    if (!register.IsCompetentFor(finding.Investigator, finding.Category))
        throw new DomainException("Investigator is not competent for this hazard category.");

    var unconsidered = _knownConsiderations.Except(finding.ConsideredItems);
    if (unconsidered.Any())
        throw new DomainException("All vulnerabilities and tenant information must be considered.");

    if (finding.Severity < _triage.Severity && string.IsNullOrWhiteSpace(finding.Rationale))
        throw new DomainException("A downgrade from triage needs a rationale.");

    Raise(new InvestigationConcluded(Id, finding, clock.GetUtcNow()));
}
```

Each rule becomes a unit test with a name a lawyer could read, e.g. `Cannot_conclude_without_considering_tenant_statements`.

**Investigator screen:** vulnerability panel, tenant statements as a checklist, suggested triage with reasons,
photo and moisture-reading upload, rationale box that becomes mandatory on a downgrade.

**Later (not v1):** an AI assistant that *drafts* a suggested finding from photos and notes, with a person deciding
and the suggestion stored alongside the decision.

---

## 5. Context map

```
                 ┌────────────────────────┐
                 │  Tenancies & Property  │  (supporting: who lives where, vulnerability flags)
                 └───────────┬────────────┘
                             │ published language: TenantId, PropertyId, VulnerabilityFlags
          ┌──────────────────┼────────────────────┐
          ▼                  ▼                    ▼
 ┌─────────────────┐  RepairReported  ┌──────────────────────┐
 │     Repairs     │ ───────────────▶ │  Hazard Compliance   │  (CORE: the regulatory clock)
 │ (requests, work │ ◀─────────────── │  HazardCase saga,    │
 │  orders)        │  MakeSafeRequired│  deadlines, breaches │
 └────────┬────────┘  WorksRequired   └──────────┬───────────┘
          │ WorkOrderIssued                      │ WrittenSummaryDue, DeadlineBreached
          ▼                                      ▼
 ┌─────────────────┐                  ┌──────────────────────┐
 │   Contractors   │                  │ Tenant Communications│  (generic: letters, SMS, email)
 │ (assign, attend,│                  └──────────────────────┘
 │  complete)      │
 └─────────────────┘
          all events ──────────────▶ ┌──────────────────────┐
                                     │  Oversight (read     │  (CQRS read model, live dashboard)
                                     │  model + SignalR)    │
                                     └──────────────────────┘
```

| Context | Type | Key aggregates | Notes |
|---|---|---|---|
| Tenancies & Property | Supporting | `Property`, `Tenancy`, `Household` | Seeded from realistic open data; the only context holding health data, publishes vulnerability flags only |
| Repairs | Core | `Concern`, `RepairRequest`, `WorkOrder` | Concern intake from any source, triage, work orders |
| Hazard Compliance | **Core** | `HazardCase` (process manager) | Owns statutory deadlines; the most interesting rules |
| Contractors | Supporting | `Contractor`, `Appointment` | Simulated contractors attend and complete jobs |
| Tenant Communications | Generic | `Notification` | Sends to Mailpit locally; templates for the written summary |
| Oversight | Read model | projections | "Clocks at risk", breaches, performance per contractor |

Each context is a **module** in one deployable app (modular monolith) with its **own database schema**.
Modules talk to each other **only through integration events** (no shared tables, no cross-module calls).
Architecture tests enforce this.

---

## 6. Event catalogue (first cut)

**Integration events** (cross-module, through the outbox):

| Event | Published by | Consumed by |
|---|---|---|
| `RepairReported` | Repairs | Hazard Compliance, Oversight |
| `HazardCaseOpened` | Hazard Compliance | Oversight |
| `InvestigationScheduled` / `InvestigationConcluded` | Hazard Compliance | Communications, Oversight |
| `HazardClassified` (Emergency / Significant / None) | Hazard Compliance | Repairs, Oversight |
| `MakeSafeRequired` / `FurtherWorksRequired` | Hazard Compliance | Repairs |
| `WorkOrderIssued` | Repairs | Contractors, Oversight |
| `ContractorAttended` / `NoAccessRecorded` / `WorkCompleted` | Contractors | Repairs, Hazard Compliance |
| `WrittenSummaryDue` / `WrittenSummarySent` | Hazard Compliance / Communications | each other, Oversight |
| `DeadlineApproaching` / `DeadlineBreached` | Hazard Compliance | Communications, Oversight |
| `AlternativeAccommodationRequired` | Hazard Compliance | Tenancies, Oversight |

**Time is an event source.** When a `HazardCase` starts a clock it records a deadline; the deadline sweeper
(section 8.6) raises `DeadlineApproaching` at 80% and `DeadlineBreached` at 100% unless the case has met or
stopped the clock. Deadlines are computed by a `WorkingDayCalendar` domain service, which loads bank holidays from the
free [GOV.UK bank holidays API](https://www.gov.uk/bank-holidays.json).

---

## 7. Architecture

- **Modular monolith**: `Repairs.Api` host loads modules; each module has `Contracts`, `Domain`, `Application`, `Infrastructure`.
- **Domain model**: aggregates protect rules (a `HazardCase` can't close with an open safety work order;
  a written summary can't be sent before the investigation concludes). Value objects for `Deadline`,
  `WorkingDays`, `HazardSeverity`, `Address`.
- **Domain events** inside a module; **integration events** between modules (separate types, explicit mapping).
- **Transactional outbox**: state change and outgoing messages saved in one EF Core transaction.
- **Idempotent consumers**, retries with back-off, dead-letter queue.
- **CQRS-lite**: Oversight projections built from events, pushed live to the dashboard via SignalR.
- **Event sourcing for `HazardCase` only**; everything else is current-state EF Core (section 8.5).
- **Simulator**: an outside API client that plays every actor on an accelerated clock, so the demo is alive (section 8.4).

### Tech stack (defaults: confirm or change)

| Concern | Choice | Why |
|---|---|---|
| Runtime | .NET 10 (LTS), ASP.NET Core minimal APIs | Current LTS |
| Persistence | EF Core + **SQL Server** locally (Developer container) / **Azure SQL free offer** in cloud | Free for the lifetime of the subscription |
| Messaging | **Wolverine** (MIT) with its SQL Server transport and outbox; RabbitMQ optional locally | No paid broker in the cloud; MassTransit v9 and MediatR are now commercial |
| Local orchestration | **Aspire** AppHost + ServiceDefaults; docker-compose as fallback | One-command local run, built-in OpenTelemetry dashboard |
| Frontend | React + TypeScript + Vite, TanStack Query, SignalR client; pnpm workspace | Two apps (tenant portal, staff) sharing a UI package |
| Tests | xUnit, Testcontainers, NetArchTest, Playwright (later) | Real SQL Server in integration tests; boundaries enforced |
| Observability | OpenTelemetry → Aspire dashboard locally, Application Insights (capped) in Azure | Traces follow a message across modules |
| Auth (later) | Fake personas first; Entra External ID free tier later | Keep v1 focused on the domain |
| IaC / deploy | **Terraform**, GitHub Actions (OIDC sign-in to Azure, no stored secrets) | Most requested IaC tool in UK job adverts; `terraform apply` / `terraform destroy` |
| Event store | Hand-rolled on EF Core + SQL Server (`HazardCase` only) | Marten needs Postgres; KurrentDB is extra infrastructure |
| Test data | Bogus (MIT) | Fake households, fictional streets |

---

## 8. System components

### 8.1 Runtime components

```
 Browser
 ┌──────────────────────────┐   ┌──────────────────────────────────────┐
 │ tenant-portal (React+TS) │   │ staff (React+TS)                     │
 │ report, timeline, letters│   │ contact centre · investigator ·      │
 └────────────┬─────────────┘   │ scheduler · contractor · compliance  │
              │ /tenant/*       └──────┬────────────────────▲──────────┘
              │                        │ /staff/*           │ SignalR
 ┌────────────▼────────────────────────▼────────────────────┴──────────┐     ┌──────────────────────┐
 │ Repairs.Api (modular monolith)                                      │◀────│ Repairs.Simulator    │
 │  Tenant BFF endpoints · Staff endpoints · SignalR hub               │REST │ (outside API client: │
 │  Modules: Tenancies · Repairs · Hazard Compliance · Contractors ·   │     │  tenants, triage,    │
 │           Communications · Oversight                                │     │  investigators,      │
 │  Wolverine handlers + outbox · Deadline sweeper (TimeProvider)      │     │  contractors)        │
 └────────────┬────────────────────────────────────────────────────────┘     └──────────────────────┘
              │ EF Core + Wolverine                      ──────▶ GOV.UK bank holidays API (cached daily)
 ┌────────────▼────────────────────────────────────────────────────────┐
 │ SQL Server / Azure SQL: one database, a schema per module,          │
 │ compliance.hazard_case_events (event store), wolverine (outbox)     │
 └─────────────────────────────────────────────────────────────────────┘
```

| Component | What it is | Local | Azure (£0) |
|---|---|---|---|
| **tenant-portal** | Public, mobile-first React app: report a concern, case timeline, request inspection, letters | Vite | Static Web Apps (free) |
| **staff** | Internal React app with an area per staff persona (contractor area stands in for a field app) | Vite | Static Web Apps (free) |
| **Repairs.Api** | Modular monolith: tenant BFF and staff endpoints, SignalR hub, message handlers, deadline sweeper | Aspire | Container App, min replicas 0 |
| **Repairs.Simulator** | Outside API client playing every actor (see 8.4) | Aspire | **Container Apps Job**, started by hand, max run time ~20 min |
| **Database** | One DB; schemas `tenancies`, `repairs`, `compliance`, `contractors`, `comms`, `oversight`, `wolverine` | SQL Server Developer container | Azure SQL free offer |
| **Messaging** | Wolverine transactional outbox/inbox stored in SQL | SQL (RabbitMQ optional) | SQL |
| **Real-time** | SignalR hub pushing changes to staff screens | In-process | Azure SignalR Service (free) |
| **Mail** | Written summaries, safety advice, updates | **Mailpit** container | **Letters view** in the apps (no paid email) |
| **Evidence** | Photos, moisture readings, behind `IEvidenceStore` | In the DB | In the DB (32 GB free; Blob isn't free after 12 months) |
| **Telemetry** | OpenTelemetry traces, metrics, logs | Aspire dashboard | Application Insights (capped) |

### 8.2 Why two front-end apps

Tenants and staff are different audiences, so the apps are split as a real landlord would split them:

| Concern | Tenant portal | Staff app |
|---|---|---|
| Exposure | Public internet | Staff only, often network-restricted |
| Identity (later) | Customer identity (Entra External ID) | Workforce identity (Entra ID, MFA) |
| Code shipped to the browser | Tenant screens only, so no map of staff APIs for the public | Everything staff need |
| Data | Own home and cases only, enforced by a **tenant BFF** | All cases |
| Priorities | Mobile first, plain English, WCAG 2.2 AA | Dense desk screens |
| Load | Spiky (cold snaps) | Steady, office hours |

Both live in one **pnpm workspace** sharing `packages/ui` (components, tokens, API client types). The API exposes
`/tenant/*` and `/staff/*` endpoint groups with separate authorisation policies.

### 8.3 Code components

**Platform** (reused later by the Elections repo):

| Project | Contents |
|---|---|
| `BuildingBlocks.Domain` | `AggregateRoot`, `Entity`, `ValueObject`, `DomainEvent`, `DomainException` |
| `BuildingBlocks.EventSourcing` | Hand-rolled event store on EF Core (see 8.5), `EventSourcedAggregate`, Given/When/Then test base |
| `BuildingBlocks.Messaging` | Wolverine setup, integration-event conventions, idempotency helpers |
| `BuildingBlocks.Time` | `StatutoryPeriod`, `WorkingDayCalendar`, `IBankHolidaySource` (GOV.UK implementation), accelerated `TimeProvider` |
| `ServiceDefaults`, `AppHost` | Aspire |

**Each module** has four projects:

```
Modules/HazardCompliance/
  HazardCompliance.Contracts/       integration events: the module's only public surface
  HazardCompliance.Domain/          aggregates, value objects, policies (no framework references)
  HazardCompliance.Application/     commands, handlers, queries
  HazardCompliance.Infrastructure/  EF Core mappings, event store, endpoints
```

Other modules may reference **only `.Contracts`**; architecture tests fail the build otherwise.

| Module | Main contents | Persistence |
|---|---|---|
| Tenancies | `Property`, `Tenancy`, `Household`; publishes vulnerability flags only | EF Core (state) |
| Repairs | `Concern`, `RepairRequest`, `WorkOrder`; triage suggestion rules | EF Core (state) |
| Hazard Compliance | `HazardCase`, `Investigation`, `Finding`, `HazardScopePolicy`, deadlines | **Event-sourced** |
| Contractors | `Contractor` (competencies), `Appointment` (24-hour notice rule) | EF Core (state) |
| Communications | `Letter` (written summary, safety advice, no further action), `Notification` | EF Core (state) |
| Oversight | Projections: clocks at risk, breaches, contractor performance, case timeline | Read tables, rebuildable from events |

### 8.4 Simulator

**Purpose:** a demo that's already moving, edge cases on demand, realistic dashboard data, and reproducible end-to-end tests.

**Rule: it's an outside client.** It uses only the public APIs, signed in as personas, and never touches the database,
so every simulated action goes through real validation, domain rules, outbox and events. Every action is tagged
`source: simulator` in event metadata.

| Actor | Behaviour |
|---|---|
| Tenants | Report concerns weighted by season, property age and energy rating; some request inspections, refuse access or refuse rehousing |
| Contact centre | Triage, accepting or overriding the suggestion |
| Investigators | Findings by probability (e.g. 70% significant, 10% emergency, 20% not relevant), always with a rationale |
| Contractors | Accept, attend late or on time, no access, complete |
| Third parties | Freeholders granting or refusing consent |

**Modes**
- **Ambient:** steady random load from a seeded generator.
- **Scenario:** scripted, seeded, repeatable stories:
  1. Emergency: exposed wiring, child under 5, made safe within 24 hours.
  2. Winter damp surge: 40 concerns in a week; contractor capacity runs out.
  3. No access three times: reasonable endeavours recorded; duty paused lawfully.
  4. Freeholder refuses consent: duty ends; "no further action" letter.
  5. Can't make safe in 5 working days: rehousing, safety advice, return home.

**Simulated time.** Everything reads the clock through .NET `TimeProvider`, never `DateTime.UtcNow`. In demo mode
the API uses an **accelerated clock** (e.g. 1 real minute = 1 working day) that the simulator can pause, speed up or skip.

**Data.** Bogus households and **fictional street names** with real-looking postcode districts: no invented
damp cases attached to real addresses.

**Running it.** Locally as part of Aspire. In Azure as a Container Apps Job started by hand with a maximum run time,
so it can't be left running or keep the database awake.

### 8.5 Event store (`HazardCase` only)

Only `HazardCase` is event-sourced, because its history is the landlord's legal evidence. Everything else is plain EF Core.

```sql
CREATE TABLE compliance.hazard_case_events (
    global_position  BIGINT IDENTITY      NOT NULL,  -- total order, for rebuilding projections
    stream_id        UNIQUEIDENTIFIER     NOT NULL,  -- the HazardCase id
    version          INT                  NOT NULL,  -- 1, 2, 3… within the stream
    event_type       NVARCHAR(200)        NOT NULL,  -- stable name e.g. "investigation-concluded.v1"
    payload          NVARCHAR(MAX)        NOT NULL,  -- JSON
    metadata         NVARCHAR(MAX)        NOT NULL,  -- who, source, correlation/causation ids
    occurred_at      DATETIMEOFFSET       NOT NULL,  -- business time (when the tenant phoned)
    recorded_at      DATETIMEOFFSET       NOT NULL,  -- system time (when it was entered)
    CONSTRAINT pk_hazard_case_events PRIMARY KEY (stream_id, version)
);
```

- **Optimistic concurrency:** append at `expected version + 1`; a duplicate key means someone else wrote first → `ConcurrencyException`.
- **Atomic with the outbox:** events and Wolverine outbox messages commit in one transaction.
- **Loading:** read the stream by version and replay into the aggregate's `Apply` methods.
- **No snapshots:** a case has tens of events. Recorded as a deliberate ADR decision.
- **Rebuildable projections:** `global_position` lets Oversight read models be deleted and rebuilt.
- **Two timestamps:** legal clocks run from `occurred_at` (becoming aware), not `recorded_at`.
- **Insert-only:** the app's database login has INSERT and SELECT only on this table. Stretch: each event stores a hash of the previous one, so tampering is detectable.
- **Events never change:** new shape → new versioned event type plus an upcaster. Type names are stable strings, not CLR names.
- **GDPR:** no personal data in events, only IDs and flags. Free-text tenant statements live in an erasable table, so an erasure request leaves the legal history intact.

Tests read like the regulations:

```csharp
[Fact]
public void Significant_hazard_safety_work_due_5_working_days_after_investigation()
{
    Given(new ConcernReported(caseId, reportedOn: Fri("2026-12-18")),
          new InvestigationConcluded(caseId, Significant, on: Mon("2026-12-21")));

    When(c => c.IdentifySafetyWork(workId));

    Then(new SafetyWorkDeadlineSet(caseId, due: Wed("2026-12-30")));
    // 22, 23, 24 Dec; 25 & 26 skipped (Christmas, weekend); 28 Dec is the Boxing Day substitute bank holiday; 29, 30 Dec
}
```

### 8.6 Deadlines: table and sweeper

Wolverine's scheduled messages fire on wall-clock time, which breaks with an accelerated clock. Instead:

1. When a clock starts, the case writes a row to `compliance.deadlines` (case, deadline type, due time, status).
2. A background **sweeper** asks "what's due as of `TimeProvider.GetUtcNow()`?" and raises `DeadlineApproaching`
   (at 80%) or `DeadlineBreached` (at 100%) unless the case has already met or stopped the clock.
3. Clock restarts and stops update the row through case events, never by editing dates directly.

This works with any clock, survives restarts, and gives Oversight a simple "clocks at risk" query. ADR to record it.

---

## 9. Azure at £0

| Resource | Tier | Idle cost |
|---|---|---|
| Azure Container Apps (API) | Consumption plan, min replicas 0 | £0 within the monthly free grant |
| Container Apps Job (simulator) | Manual trigger, max run time ~20 min | £0 within the free grant; nothing when not running |
| Azure SQL Database | Free offer: 100,000 vCore-seconds, 32 GB per month, **auto-pause until next month when used up** | £0, can't overcharge |
| Azure Static Web Apps (tenant portal, staff) | Free | £0 |
| Azure SignalR Service | Free tier | £0 |
| Container images | GitHub Container Registry (not ACR) | £0 |
| Logs | Log Analytics with a daily cap | £0 within the free 5 GB/month |
| Terraform state | Blob in a small Storage account in `rg-pcp-data` | A few KB: well under 1p/month |

**Watch-outs**
- 100,000 vCore-seconds is roughly 55 hours a month at 0.5 vCore. Wolverine polls the database while the
  app is awake, which keeps SQL awake too. That's fine because the app scales to zero; the simulator runs as a time-limited
  job so it can't be left on. Disconnect query tools when you finish.
  Set an alert on the "Free amount remaining" metric.
- Two resource groups: `rg-pcp-data` (SQL and Terraform state, kept) and `rg-pcp-apps` (everything else, torn down freely).
  Two Terraform root modules to match, so `terraform destroy` on apps can never touch the data.
- GitHub Actions workflows run by hand: **Deploy** (`terraform apply`) and **Tear down** (`terraform destroy`).
- A budget alert at £1 (it only sends an email; the SQL auto-pause setting is the real safeguard).

Source: [Azure SQL Database free offer](https://learn.microsoft.com/en-us/azure/azure-sql/database/free-offer).

---

## 10. Repository layout

```
property-compliance-platform/
  src/
    BuildingBlocks/            Domain, EventSourcing, Messaging, Time (reused by the Elections repo)
    AppHost/                   Aspire orchestration
    ServiceDefaults/           OpenTelemetry, health checks, resilience
    Repairs/
      Repairs.Api/             host: composes modules, HTTP endpoints, SignalR hub
      Modules/
        Tenancies/  Repairs/  HazardCompliance/  Contractors/  Communications/  Oversight/
      Repairs.Simulator/
  web/                         pnpm workspace
    packages/ui/               shared components, design tokens, API client types
    tenant-portal/             React + TS, public
    staff/                     React + TS, internal
  tests/
    *.UnitTests  *.IntegrationTests  ArchitectureTests
  infra/                       Terraform: modules/ (reusable), data/ and apps/ root modules
  docs/
    design.md  adr/  context-map/  event-catalogue/
  .github/workflows/           ci.yml, deploy.yml, teardown.yml
```

---

## 11. Phased plan

Each phase ends with a working, demoable app, a tagged release and the ADRs written up.

| Phase | Deliverable | What you learn |
|---|---|---|
| **0. Foundations** | Repo, Aspire AppHost, SQL Server container, BuildingBlocks, CI (build + test), architecture tests, ADR-001 (modular monolith), ADR-002 (Wolverine) | Solution structure, Aspire, CI |
| **1. Repairs core** | Tenant reports a concern → staff triage → work order issued → completed. Tenant portal + staff app, persona switcher | Aggregates, value objects, EF Core mapping per schema |
| **2. Hazard compliance** | Event-sourced `HazardCase` with Awaab's Law clocks, `WorkingDayCalendar` + bank holidays API, deadline table + sweeper, triage vs finding rules, written summary, rehousing branch | Event sourcing, process managers, time as events, domain services, policies |
| **3. Contractors + messaging hardening** | Contractor module, no-access flows, outbox, idempotency, retries, dead-letter queue | Integration events, reliability patterns |
| **4. Oversight + simulator** | Live dashboard (clocks at risk, breaches), projection rebuilds, simulator with ambient and scenario modes on an accelerated clock; Phase 2 hazard-scope policy | CQRS read models, SignalR, policy versioning |
| **5. Azure** | Terraform (remote state, OIDC from GitHub Actions), Container Apps, Azure SQL free, Static Web Apps, deploy/teardown workflows, App Insights | IaC, cloud cost control |
| **6. Elections (new repo)** | Replay the 2024 general election from open results data, live seat map. Platform code reused by publishing BuildingBlocks as NuGet packages on GitHub Packages, or copying them | Event sourcing (recounts as events), packaging and reusing a platform |

---

## 12. Open decisions

1. Public from day one? (Recommended: yes, with a roadmap README, OIDC and push protection.)

**Decided**
- Repo name: `property-compliance-platform`. Leaves room for the wider landlord compliance areas
  (gas, electrical, fire, asbestos, water, lifts) and for private landlords if Awaab's Law is extended to them.
- Wolverine from the start for outbox, inbox, retries and dead-lettering (no hand-written spike). ADR-002.
- Terraform for infrastructure, run directly from GitHub Actions (no `azd`). ADR-003.
- Elections goes in its own repo; this repo is housing-only.
- Two front-end apps (tenant portal, staff) in a pnpm workspace, with a tenant BFF.
- Simulator as an outside API client; Container Apps Job in Azure.
- Hand-rolled event store on EF Core for `HazardCase` only.
- Deadlines via a table and sweeper on `TimeProvider`, not scheduled messages.
- Severity is a human finding with enforced safeguards; the system only suggests triage.
