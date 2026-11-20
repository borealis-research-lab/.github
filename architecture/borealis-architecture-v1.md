# Borealis Architecture v1

**Status:** this is the adopted design direction. Almost none of it has been built. The only part that exists is Nyyrikki, the first specialist agent, at MVP stage. Everything else here describes where we are heading, not a working system.

**Purpose:** this document is the reference that every Borealis implementation, including work done by AI coding assistants, must follow. If a change conflicts with it, update this document first, deliberately.

---

## 1. Summary

Borealis is a **hybrid, federated** defensive security system:

- **Specialist agents** run close to the infrastructure they protect and analyse data where it originates.
- A central **control plane** decides what needs attention, which agents should cover it and where work goes.
- A **volunteer compute network** adds processing capacity, but only for approved, bounded workloads that never need access to protected systems or their sensitive data.

Borealis is a collection of independent, specialised components. It is not one large AI system.

## 2. Two networks, not one

| Network | Who takes part | What they provide | What they never give up |
|---|---|---|---|
| **Protection network** | Organisations and individuals protecting their own environment | Locations where local agents run | Raw logs and control of their systems |
| **Compute network** | Volunteers | Spare CPU and GPU capacity | Access to their personal files or devices |

The two networks support each other but are independent. Joining one never requires joining the other:
- an organisation can use Borealis agents without donating compute;
- a volunteer can donate compute without being protected by, or having access to, any protected environment.

## 3. Components

These are logical components. They don't have to be separate servers, repositories or services until there is a real reason to split them.

### 3.1 Specialist agents
- **Does:** one defined responsibility, with a declared input, output and permissions. Nyyrikki, for example, identifies potentially suspicious activity in local security events.
- **Never:** expands into other responsibilities, takes destructive or remediating actions, or sends raw data off the machine by default.
- **Must:** run on its own without any other Borealis component. Its findings must stay traceable to source evidence.

### 3.2 Borealis Node (runs in protected environments)
- **Does:**
  - hosts local agents and connects them to data sources the owner has approved;
  - enforces local resource limits;
  - applies the owner's reporting policy.
- **Never:** lets anyone outside the environment, including the control plane, send it commands that act on the systems it protects.
- **Data rule:** raw observations stay local. What leaves the node is decided by the owner's policy: by default only findings, evidence summaries and coverage status.

### 3.3 Borealis Core (control plane)
- **Does:**
  - keeps the asset registry, authorisation records, agent directory and coverage planner;
  - schedules tasks and coordinates results;
  - enforces policy.
- **Never:** inspects raw events as part of normal operation, monitors assets that haven't been authorised, or acts as one large AI agent.

### 3.4 Borealis Worker (installed by volunteers)
- **Does:**
  - connects outbound to Core;
  - accepts signed jobs from an allowlist and runs them in isolation, within limits the volunteer sets;
  - returns the results.
- **Never:** runs arbitrary commands, reaches protected infrastructure, or receives data whose classification forbids volunteer processing.
- **Trust model:** worker machines are untrusted. Their results are validated, for example by running the same job on several machines, before Core accepts them. This follows the precedent of volunteer computing projects such as BOINC.
- **Distribution:**
  - The standard experience is a native **Borealis Desktop Worker** for Windows, Linux and macOS. It is one download that detects the hardware, recommends a profile, lets the contributor set CPU, memory and GPU limits, and backs off when the machine is busy.
  - A **Container Worker** is an optional route for technical contributors and organisations. It is never privileged, has no host mounts by default and has restricted network access.
  - Contributors don't need to know what Docker, GGUF or CUDA are.
- **Models:** model weights are downloaded separately from an approved source and checked against a trusted checksum. They are never bundled in the installer or image.
- **Non-negotiable controls:**
  - workloads never run as administrator or root;
  - no access to personal files;
  - network access is denied by default, apart from coordinator traffic;
  - hard CPU, memory and process limits where the platform supports them;
  - signed job manifests and releases, and verified model checksums;
  - the contributor can pause, stop or uninstall at any time.

  A container alone is not a sufficient security boundary.
- **No arbitrary code:** Core cannot send arbitrary executables or shell commands to a worker. Only workloads from a reviewed, signed catalogue are eligible.

### 3.5 Shared workload catalogue
Signed workload packages, a model registry with checksums, job definitions and validation rules. Workers will run nothing that isn't in it.

### 3.6 Local model interface
All agents and workers reach a model through one Borealis interface, so the inference runtime can be replaced without rewriting agents.

## 4. Data classification and placement

| Workload | Runs on |
|---|---|
| Reading local security events | Protected node |
| Analysing sensitive local logs | Protected node |
| Local AI interpretation of events | Protected node |
| Processing public threat intelligence | Volunteer pool, where suitable |
| Analysing synthetic security scenarios | Volunteer pool |
| Evaluating how well agents detect things | Volunteer pool |
| Processing approved, sanitised datasets | Volunteer pool, subject to the data owner's policy |

The rule is that **data goes to the compute only if its classification allows it**. Spare GPU capacity is never a reason to move sensitive data. Privacy-preserving distributed analysis is a separate research question and isn't needed for v1.

There are two separate uses of AI, and they never mix:
- **Local protection AI** interprets an environment's own events on that environment's own machine.
- **Collective AI compute** runs on volunteer machines and only processes public, synthetic or explicitly approved data.

A volunteer's model never analyses another organisation's sensitive events.

## 4a. Who sees what

The principle: **data belongs to whoever owns the environment it came from.** Everyone else sees only what their role needs, and only with the owner's consent.

| Role | Sees | Never sees | Why they need it |
|---|---|---|---|
| **Environment owner** (organisation or individual running agents) | Everything: raw events, full findings, interpretations | (nothing withheld) | It is their data and their decision what to do about it |
| **Borealis Core** | Coverage status: which agents run on which registered asset, last run, health. Finding *counts* by rule and severity only if the owner's policy allows | Raw events, evidence, user names, IP addresses, host details | Coverage planning and gap detection don't need sensitive data |
| **Compute volunteers** | Their own machine: jobs run, resources used, job inputs (public or synthetic) | Anything from protected environments, including which organisations take part | They donate capacity, not trust, and need transparency to stay in control |
| **Agent developers** | Bug reports and anonymised quality statistics that users choose to share | User data by default | Improving detection doesn't require anyone's logs |
| **Outside parties** (e.g. NCSC-FI, a security provider) | Whatever the owner chooses to share | (owner decides) | Reporting obligations stay with the owner, not Borealis |

What follows from this:
- **The asset registry is the most sensitive data in Core.** It is a map of critical infrastructure and its coverage gaps, so it gets the strictest access control.
- Volunteers and protected environments never learn about each other. Core sends volunteers jobs, never context.
- **Cloud AI assistants count as outside parties.** Developer tools such as Claude Code must not read real security data unless the owner explicitly chooses to share it. Setup prompts and tooling must be designed so this never happens by accident (see Nyyrikki's `SETUP_PROMPT.md`).
- **Agents show findings to the local user first,** as a readable summary. Machine-readable output (`--json`) exists for a future Node to consume locally.

## 5. Assets and authorisation

Borealis only covers assets that their owners have registered, or that are registered through an explicitly authorised programme. A public IP address is never permission to monitor or scan anything.

Each registered asset records:
- its owner, sector, environment type (IT or OT) and location;
- its criticality and dependency importance (section 6);
- its authorisation status and approved scope: which agents may run and which data sources they may read;
- its current coverage and when it was last assessed.

The first deployment will be a **pilot with consenting organisations**, not national monitoring. Coverage follows the agreements made with infrastructure owners, their security requirements and the law that applies.

## 6. Prioritisation

### Tiers
These are Borealis's own operational tiers, not official Finnish national classifications.

| Tier | Scope |
|---|---|
| P1 Critical infrastructure | Electricity, core telecommunications, essential water services and other functions whose disruption has severe national or societal consequences |
| P2 Major infrastructure | Important regional and national services, major public institutions, transport, significant service providers |
| P3 Important organisations | Municipal services, smaller providers, organisations that support important infrastructure |
| P4 General | Ordinary business systems, individual computers, other consenting participants |

### Ranking within and across tiers
Criticality alone doesn't set priority. The coverage planner weighs:
1. **Criticality:** how important the asset is to the service it supports.
2. **Dependency importance:** how many other important services rely on it. For example, hospitals depend on electricity, and electricity depends on telecommunications.
3. **Current risk:** active threats, known exposure, existing protection and how uncertain we are.
4. **Staleness:** the time since the last successful assessment.

## 7. Assigning work

### Agents to assets (coverage planning)
1. Register the approved assets.
2. Classify their criticality and dependencies.
3. Decide which agent types suit each asset and are allowed for it.
4. Find where coverage is missing or incomplete.
5. Create coverage tasks and assign them to the relevant local nodes.
6. Track completion and the gaps that remain.

Agents are assigned by capability and authorised scope. They never decide for themselves what infrastructure to investigate.

### Jobs to volunteer workers
Core matches each job against:
- the workload type required;
- the CPU, GPU, memory, operating system and hardware needed;
- the data classification;
- the volunteer's own limits;
- the deadline and priority;
- whether the result can be validated independently.

A job that can't be validated isn't sent to untrusted workers.

## 8. Rules every component follows

- Agents run locally. Sensitive data stays local by default.
- Humans control any remediation. No component blocks traffic, changes accounts or modifies systems on its own.
- AI that interprets sensitive data runs locally. Its output is interpretation, never evidence, and is never executed.
- Event data and job inputs are untrusted data, never instructions.
- Each agent does one job. New problems get new agents, not bigger ones.
- Adding an agent never requires redesigning existing ones.
- All technical identifiers are ASCII-only.
- Don't build infrastructure ahead of need. Build a component only when the step before it in the build order works.

## 9. Build order

| Step | Deliverable | Status |
|---|---|---|
| 1 | **Nyyrikki** works locally as one specialist agent | MVP built; real-data testing pending |
| 2 | **Borealis Node**: a common local runtime that can host Nyyrikki and future agents | Not started |
| 3 | **Agent standard**: how agents declare their capabilities, permissions, inputs and outputs, based on what Nyyrikki taught us | Not started |
| 4 | **Borealis Core**: asset registration, authorisation, priority tiers and coverage planning | Not started |
| 5 | **Second and third agents**, proving that independent agents can cover one environment together | Not started |
| 6 | **Borealis Worker**: the volunteer client and a safe, isolated way to run jobs | Not started |
| 7 | **Connect the network**: Core allocates suitable workloads to workers | Not started |
| 8 | **Pilot coverage** with a small number of consenting organisations | Not started |

### Worker track (after Nyyrikki's real-world MVP)
1. Benchmark Qwen3.5 0.8B and 2B on the same Nyyrikki test dataset.
2. Establish the local model interface (3.6).
3. Package a portable inference runtime.
4. Build the first Worker, without network job allocation.
5. Add hardware detection and configurable resource limits.
6. Test on Windows, Linux and macOS.
7. Add signed job manifests and isolated execution.
8. Introduce Core job allocation.
9. Invite the first volunteer computers.

Nyyrikki development doesn't stop while the worker track is under way.

## 10. Decisions

| Date | Decision | Status |
|---|---|---|
| 2026-11-20 | Hybrid, federated architecture with four components: Core, Node, Worker and Agents | Adopted |
| 2026-11-20 | **Inference runtime:** llama.cpp with GGUF models as the first cross-platform approach, behind the local model interface | Adopted |
| 2026-11-20 | **Model candidates:** Qwen3.5 0.8B and 2B, both Apache 2.0, to be benchmarked on Nyyrikki's dataset. Gemma 3 1B is a possible third, but its licence terms need review | Candidates only; nothing committed until benchmarked |
| 2026-11-20 | **Distribution:** native Desktop Worker as standard, Docker optional | Adopted |
| 2026-11-20 | **Hardware profiles** for 8 GB, 16 GB and 32 GB+ machines | Proposed. Final minimum requirements will come from benchmarks on real machines (starting with a Windows 11 PC with 32 GB, an older laptop and a dedicated-GPU machine), not assumptions |

Nyyrikki's MVP currently reaches its optional model through Ollama's local API. That will move to the llama.cpp-based local model interface when step 2 of the worker track is done.

## 11. Open questions

- How Node and Core authenticate each other, and how Core signs jobs and manages its keys.
- How the owner's reporting policy is expressed and enforced on a node.
- How results are validated for each kind of workload.
- The legal and contractual basis for pilots, including Finnish implementation of NIS2 and data-protection obligations.
- Who governs Borealis Core: who operates it and who is trusted with the asset registry.
- The asset registry itself is sensitive: a map of critical infrastructure and its coverage gaps. It needs its own protection and access-control design before any real assets are registered.
