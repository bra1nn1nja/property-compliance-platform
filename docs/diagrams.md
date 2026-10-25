# Diagrams

Visual overview of what we're building. Details and reasoning are in [design.md](design.md).

1. [System context](#1-system-context)
2. [Runtime containers](#2-runtime-containers)
3. [Bounded contexts and integration events](#3-bounded-contexts-and-integration-events)
4. [Module dependency rules](#4-module-dependency-rules)
5. [Hazard case lifecycle](#5-hazard-case-lifecycle)
6. [A concern from report to dashboard](#6-a-concern-from-report-to-dashboard)
7. [Statutory clocks: a worked example](#7-statutory-clocks-a-worked-example)
8. [Azure deployment at £0](#8-azure-deployment-at-0)

---

## 1. System context

Who uses the platform and what it talks to.

```mermaid
flowchart LR
    tenant["👤 Tenant / household"]
    advocate["👤 Advocate<br/>(family, support worker, MP)"]
    staff["👥 Landlord staff<br/>(contact centre, investigators,<br/>schedulers, compliance)"]
    contractor["👷 Contractors"]

    pcp(["Property Compliance Platform"])

    bankHolidays["GOV.UK<br/>bank holidays API"]
    oversight["Regulator, Ombudsman,<br/>courts"]

    tenant -- "reports concerns,<br/>follows case, gets letters" --> pcp
    advocate -- "reports on tenant's behalf" --> pcp
    staff -- "triage, investigate,<br/>schedule, monitor clocks" --> pcp
    contractor -- "attend, make safe,<br/>record no access" --> pcp
    pcp -- "working-day calendar" --> bankHolidays
    pcp -. "evidence trail, reports" .-> oversight
```

---

## 2. Runtime containers

What actually runs. Locally everything starts with Aspire; in Azure each box maps to a free-tier service.

```mermaid
flowchart TB
    subgraph browser["Browser"]
        portal["Tenant portal<br/>React + TS (public)"]
        staffApp["Staff app<br/>React + TS (internal)"]
    end

    subgraph api["Repairs.Api: modular monolith (ASP.NET Core)"]
        tenantBff["Tenant BFF<br/>/tenant/*"]
        staffEndpoints["Staff endpoints<br/>/staff/*"]
        hub["SignalR hub"]
        modules["Modules: Tenancies · Repairs · Hazard Compliance ·<br/>Contractors · Communications · Oversight"]
        wolverine["Wolverine<br/>handlers, outbox, inbox"]
        sweeper["Deadline sweeper<br/>(TimeProvider)"]
    end

    simulator["Repairs.Simulator<br/>outside API client"]

    subgraph db["SQL Server / Azure SQL"]
        schemas[("Schema per module")]
        eventStore[("compliance.hazard_case_events<br/>event store")]
        outbox[("wolverine schema<br/>outbox / inbox")]
    end

    bankHolidays["GOV.UK bank holidays API"]
    mail["Mailpit (local)<br/>Letters view (Azure)"]

    portal -- HTTPS --> tenantBff
    staffApp -- HTTPS --> staffEndpoints
    hub -- "live updates" --> staffApp
    simulator -- HTTPS --> tenantBff
    simulator -- HTTPS --> staffEndpoints
    tenantBff --> modules
    staffEndpoints --> modules
    modules --> wolverine
    sweeper --> modules
    modules -- "EF Core" --> schemas
    modules -- "append-only" --> eventStore
    wolverine --> outbox
    modules --> hub
    modules --> bankHolidays
    modules --> mail
```

---

## 3. Bounded contexts and integration events

Each context owns its data and schema. Contexts talk only through integration events published via the outbox.

```mermaid
flowchart LR
    tenancies["<b>Tenancies & Property</b><br/>supporting<br/>Property · Tenancy · Household"]
    repairs["<b>Repairs</b><br/>core<br/>Concern · RepairRequest · WorkOrder"]
    compliance["<b>Hazard Compliance</b><br/>core, event-sourced<br/>HazardCase · Investigation · Finding"]
    contractors["<b>Contractors</b><br/>supporting<br/>Contractor · Appointment"]
    comms["<b>Communications</b><br/>generic<br/>Letter · Notification"]
    oversight["<b>Oversight</b><br/>read models<br/>clocks at risk · breaches"]

    tenancies -- "VulnerabilityFlagsChanged" --> compliance
    repairs -- "RepairReported" --> compliance
    compliance -- "MakeSafeRequired<br/>FurtherWorksRequired" --> repairs
    repairs -- "WorkOrderIssued" --> contractors
    contractors -- "ContractorAttended<br/>NoAccessRecorded<br/>WorkCompleted" --> repairs
    contractors -- "WorkCompleted<br/>NoAccessRecorded" --> compliance
    compliance -- "WrittenSummaryDue<br/>DeadlineBreached" --> comms
    comms -- "WrittenSummarySent" --> compliance
    compliance -- "AlternativeAccommodationRequired" --> tenancies

    repairs -. "all events" .-> oversight
    compliance -. "all events" .-> oversight
    contractors -. "all events" .-> oversight
    comms -. "all events" .-> oversight
```

---

## 4. Module dependency rules

Inside a module, dependencies point inwards to the domain. Between modules, only `Contracts` may be referenced.
Architecture tests fail the build if these rules are broken.

```mermaid
flowchart TB
    subgraph hc["Hazard Compliance module"]
        hcInfra["Infrastructure<br/>EF Core, event store, endpoints"]
        hcApp["Application<br/>commands, handlers, queries"]
        hcDomain["Domain<br/>aggregates, value objects, policies"]
        hcContracts["Contracts<br/>integration events"]
        hcInfra --> hcApp --> hcDomain
        hcApp --> hcContracts
    end

    subgraph rp["Repairs module"]
        rpApp["Application"]
        rpDomain["Domain"]
        rpApp --> rpDomain
    end

    blocks["BuildingBlocks<br/>Domain · EventSourcing · Messaging · Time"]

    rpApp -- "✅ handles events from" --> hcContracts
    rpDomain -. "❌ never" .-> hcDomain
    hcDomain --> blocks
    rpDomain --> blocks
```

---

## 5. Hazard case lifecycle

The `HazardCase` process manager, simplified. Every transition is an event in the case's stream.
The written summary (3 working days after any investigation) and tenant updates run alongside these states.

```mermaid
stateDiagram-v2
    [*] --> Reported: ConcernReported

    Reported --> EmergencyInvestigation: Triage finds grounds for emergency (24 hour clock)
    Reported --> StandardInvestigation: Standard triage (10 working day clock)

    StandardInvestigation --> StandardInvestigation: Tenant asks for physical inspection (clock restarts)
    StandardInvestigation --> EmergencyInvestigation: Emergency grounds arise later

    state finding <<choice>>
    EmergencyInvestigation --> finding: InvestigationConcluded
    StandardInvestigation --> finding: InvestigationConcluded

    finding --> NoHazard: Not relevant
    finding --> FurtherInvestigation: Hazard found, work not yet known
    finding --> MakingSafe: Emergency (24 hours) or significant (5 working days)

    FurtherInvestigation --> MakingSafe: Safety work identified

    MakingSafe --> Rehousing: Cannot make safe in time
    Rehousing --> MadeSafe: Safety work completed
    MakingSafe --> MadeSafe: Safety work completed
    MakingSafe --> DutyEnded: Consent refused after reasonable endeavours

    MadeSafe --> PreventativeWork: Start within 5 working days, or within 12 weeks
    MadeSafe --> Closed: No preventative work needed
    PreventativeWork --> Closed: Work completed

    NoHazard --> Closed: Written summary sent
    DutyEnded --> Closed: No further action letter sent
    Closed --> [*]
```

---

## 6. A concern from report to dashboard

How one damp report flows through the modules. The state change and its outgoing messages always commit
in **one transaction** (the outbox), so nothing is lost if the process crashes.

```mermaid
sequenceDiagram
    autonumber
    actor Tenant
    participant Portal as Tenant portal
    participant Repairs as Repairs module
    participant DB as SQL Server
    participant Bus as Wolverine (outbox relay)
    participant HC as Hazard Compliance
    participant Sweeper as Deadline sweeper
    participant Comms as Communications
    participant Oversight
    actor Staff as Compliance manager

    Tenant->>Portal: Report mould in child's bedroom
    Portal->>Repairs: POST /tenant/concerns
    Repairs->>DB: Save Concern + RepairReported to outbox (one transaction)
    Bus->>DB: Read outbox
    Bus->>HC: RepairReported
    HC->>DB: Append HazardCaseOpened, StandardTriage to event stream<br/>+ insert deadline row (one transaction)
    Bus->>Oversight: HazardCaseOpened
    Oversight-->>Staff: SignalR: new case, clock started

    Note over Sweeper: Time passes (accelerated in demo mode)
    Sweeper->>DB: Deadlines due as of TimeProvider.GetUtcNow()?
    Sweeper->>HC: Investigation deadline 80% elapsed
    HC->>DB: Append DeadlineApproaching
    Bus->>Comms: DeadlineApproaching
    Bus->>Oversight: DeadlineApproaching
    Oversight-->>Staff: SignalR: clock at risk (amber)
```

---

## 7. Statutory clocks: a worked example

A significant damp hazard reported on **Friday 18 December 2026**, with the investigation concluded on
**Monday 21 December**. Working days skip weekends, Christmas Day, the Boxing Day substitute (Mon 28 Dec)
and New Year's Day (WD = working days). This is the case the `StatutoryPeriod` tests are built around.
If preventative work can't start within 5 working days, it must start within 12 weeks (by Mon 15 Mar 2027).

```mermaid
gantt
    title Significant hazard: reported Fri 18 Dec 2026
    dateFormat YYYY-MM-DD
    axisFormat %a %d %b
    excludes weekends, 2026-12-25, 2026-12-28, 2027-01-01

    section Investigate
    10 WD window, due 6 Jan  :inv, 2026-12-21, 10d
    Concluded                :milestone, 2026-12-21, 0d

    section Summary
    3 WD, due 24 Dec         :sum, 2026-12-22, 3d

    section Make safe
    5 WD, due 30 Dec         :safe, 2026-12-22, 5d

    section Prevent
    Start in 5 WD            :prev, 2026-12-22, 5d
```

---

## 8. Azure deployment at £0

Two resource groups so tearing down the apps can never touch the data. GitHub Actions deploys with Terraform
and signs in to Azure with OIDC, so no secrets are stored.

```mermaid
flowchart TB
    subgraph gh["GitHub"]
        repo["Repo<br/>property-compliance-platform"]
        actions["GitHub Actions<br/>ci · deploy · teardown"]
        ghcr["GHCR<br/>container images"]
        repo --> actions --> ghcr
    end

    subgraph data["rg-pcp-data (kept)"]
        sql[("Azure SQL<br/>free offer, auto-pause")]
        tfstate[("Storage account<br/>Terraform state")]
    end

    subgraph apps["rg-pcp-apps (torn down freely)"]
        env["Container Apps environment<br/>consumption plan"]
        apiApp["Container App: Repairs.Api<br/>min replicas 0"]
        simJob["Container Apps Job: Simulator<br/>manual, time-limited"]
        swaPortal["Static Web App<br/>tenant portal"]
        swaStaff["Static Web App<br/>staff app"]
        signalr["Azure SignalR<br/>free tier"]
        insights["App Insights + Log Analytics<br/>daily cap"]
        env --> apiApp
        env --> simJob
    end

    actions -- "terraform apply / destroy<br/>(OIDC)" --> data
    actions -- "terraform apply / destroy<br/>(OIDC)" --> apps
    actions -. "state" .-> tfstate
    ghcr -- "pull image" --> apiApp
    ghcr -- "pull image" --> simJob
    apiApp --> sql
    apiApp --> signalr
    apiApp --> insights
    swaPortal --> apiApp
    swaStaff --> apiApp
```
