# Borealis Roadmap v1

**Status:** proposed for review (2026-11-20). This is the reference for *what to build in which order*. [Borealis Architecture v1](borealis-architecture-v1.md) remains the reference for *how components relate*. Where they disagree, update one of them deliberately.

## Objective

**Protect the organisations that keep Finland running.** Build an open-source network of specialised defensive agents that organisations operate themselves, and that can later connect to a shared, privacy-preserving intelligence collective.

**First measurable milestone:** Borealis provides useful, repeatable security findings for **one real Finnish organisation**, without that organisation's raw security data leaving its systems.

**Founding principle: designed around organisational trust, not centralised visibility.**
- An organisation never has to give up control of its infrastructure or sensitive data to take part.
- Agents run locally.
- Anything shared is explicitly approved by the organisation.
- Borealis doesn't replace an organisation's own security responsibilities, Traficom's National Cyber Security Centre, or existing incident-response arrangements.

## Where we are (2026-11-20)

| Component | Repository | What it does today | What it does not do |
|---|---|---|---|
| Reporting standards | `.github/standards` | Contracts, schemas, a reference checker and test vectors for agent and Node reports | |
| **Nyyrikki** | `security-event-analysis` | Five deterministic rules over **exported** Windows Security events (XML), with traceable evidence and data warnings. Validated once on one real Windows 11 PC | Live monitoring, other operating systems or log sources, calibrated thresholds |
| **Ilmarinen** | `file-integrity` | SHA-256 integrity of chosen files against a protected baseline. Windows and Linux, read-only, race-aware | Permissions, ACLs, metadata, scheduling, restoring files |
| **Borealis Node** | `borealis-node` | Runs the configured agents on demand, validates them strictly, combines their reports | Scheduling, alerting, central reporting, sandboxing untrusted agents |

**What Borealis can honestly claim today:** for systems where it is installed and run, it can find a **narrow set of problems**: suspicious account and log activity in exported Security events, and unexpected changes to chosen files. Each finding comes with evidence a human can check, and nothing leaves the machine.

**What it cannot claim:**
- continuous or comprehensive protection;
- network detection, vulnerability management or incident response;
- any national-level capability.

## Phases

Each phase ends with a **gate**: concrete evidence that must exist before the next phase starts. Phases build on each other. Work outside the current phase is research only.

### Phase 0: First experimental release (existing components)
- **Tagged pre-releases** of the standards and the three components, each with a compatibility statement, install steps and known limitations. A **"what is and isn't protected"** document.
- **Gate:** a person who wasn't involved can install and run all three from the release notes alone.

### Phase 1: Integration and reliability (existing components)
- **Clean installs** on Windows and Linux.
- **One documented setup path** for a normal IT administrator.
- **Repeated runs** on unchanged data give identical findings (finding IDs are deterministic, so this can be compared automatically).
- **Failure drills:** missing agents, a corrupted or tampered baseline, interrupted runs, oversized output, an agent timeout. Each must fail **visibly** and recover cleanly.
- **Gate:** a written reliability report covering every drill and its result, with no unexplained differences between runs.

### Phase 2: Operational usefulness (mostly existing components, some new code)
Make the existing agents usable on a schedule, not just once by hand. Still deterministic and local.

| Work | Component | New or existing |
|---|---|---|
| **Scheduled runs** of Borealis Node (via the OS scheduler, not a daemon), with retention of past reports | Node | Existing; small additions |
| **Live Windows Security events** for Nyyrikki: read the event log directly (with the necessary privilege) instead of a hand-made export, with a bookmark so each run analyses only new events | Nyyrikki | Existing agent; new input module |
| **Rule calibration** against real (consenting) environments: thresholds and documented false-positive rates | Nyyrikki | Existing |
| **Baseline operations** for Ilmarinen: guided baseline review and replacement, and recommended file sets (e.g. scheduled tasks and startup locations on Windows) | Ilmarinen | Existing |
| **Comparing a run with the previous one** ("new since last run") in the Node's view, without changing findings | Node | Existing; presentation only |

- **Gate:** one week of unattended, scheduled operation on a test machine, with every finding explained.

### Phase 3: A third specialist agent: configuration and hygiene (new component)
- A narrowly scoped, **read-only** agent for local security configuration and basic hygiene. Examples: missing security updates, disabled security controls, unexpected privileged accounts, insecure settings.
- Checks are deterministic, each finding cites the evidence, and nothing is ever changed.
- **New repository**, following the naming convention: the repository describes the capability; the agent gets its own identity.
- **Gate:** the agent passes the same standard, conformance and failure-drill bar as the first two.

### Phase 4: Pilot with one consenting organisation (existing components, plus a pilot package)
- **Target:** one university, municipality or small infrastructure supplier, on a limited set of **non-critical** systems.
- **Prerequisites (new, non-code work):**
  - signed releases and an installation package;
  - an **independent security review** of the three components;
  - a written pilot agreement: scope, what Borealis may access, data handling, who acts on findings, how to stop;
  - the organisation's own security team stays in charge.
- **Measures:**
  - useful findings, and false positives per week;
  - operational effort;
  - any disruption, which must be none.
- **Gate:** the first measurable milestone above is met and documented, with the organisation's agreement on what is published.

### Phase 5: Shared defensive intelligence (new components)
Only after Phase 4.
- **Start with one direction only:** Borealis publishes **signed detection-rule updates** that Nodes can verify and apply locally.
- **Then voluntary sharing of approved, sanitised findings**, with:
  - a sharing format;
  - organisation-side approval;
  - privacy review;
  - participant authentication and revocation;
  - protection against false or poisoned reports;
  - human review before any rule is published.
- **Never:** remote control of Nodes, collection of raw logs, or access to participants' systems.
- **Gate:** an external review of the protocol, and a pilot exchange between at least two consenting organisations.

### Phase 6: Volunteer computing (new component: Borealis Worker)
- Built separately, as described in Architecture v1 §3.4.
- **First workloads:** public threat intelligence and **synthetic** datasets only, such as evaluating detection rules at scale.
- Results must be independently verifiable before any result is trusted.
- **Volunteers never receive** raw security logs, access to protected networks, the ability to scan third-party systems, or arbitrary jobs.
- **Gate:** verified distributed runs on synthetic workloads, with the security model reviewed.

## Who to help first

These are proposed Borealis priorities for **where to pilot**, not official classifications. Each step happens only with the organisation's consent, and under its own security team.

| Order | Organisations | Why |
|---|---|---|
| 1 | Municipalities and local public services | Often limited monitoring; locally operated agents fit their constraints |
| 2 | Universities and research institutions | Diverse systems, open to research collaboration |
| 3 | Smaller suppliers to infrastructure operators | Supply-chain weak points with smaller security teams |
| 4 | Energy, water and telecom suppliers | Only as a supplement under their security teams; IT systems first, not operational technology |
| 5 | Major infrastructure operators | Only after independent validation and successful pilots |

Critical infrastructure, operational technology and defence environments are **out of scope** until the earlier phases and independent reviews are complete.

## What existing components can and cannot deliver

| Goal | Existing components (Nyyrikki, Ilmarinen, Node) | Needs new components or work |
|---|---|---|
| Local, evidence-based findings | ✅ Today, for the covered problems | |
| Repeatable, unattended operation | ✅ With Phase 1 and 2 work | |
| Live Windows security events | ✅ Nyyrikki, new input module | |
| Configuration and hygiene checks | | ❌ The Phase 3 agent |
| Pilot readiness | Partly (the software) | ❌ Signed releases, packaging, independent review, agreements |
| Shared detection rules | | ❌ Signed rule distribution, rule format, verification in Node |
| Shared findings across organisations | | ❌ Sharing protocol, approval workflow, participant trust and revocation, poisoning resistance |
| Volunteer computing | | ❌ Borealis Worker, job signing, isolation, result verification |
| National-scale coordination | | ❌ Out of scope. Borealis supports existing national arrangements and doesn't replace them |

## Rules for every phase

- **No new agent until the previous phase's gate is met.** Each agent earns its place by doing one job well.
- **AI stays parked** unless an agent can show a measurable advantage over deterministic methods (Architecture v1 decision).
- **Claims follow evidence.** Borealis doesn't claim to protect Finnish infrastructure until pilots and independent reviews show it.
- **Raw data stays where it is.**
- **Isolation is not a sandbox.** Agents run only after an administrator deliberately installs and trusts them.
