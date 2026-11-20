# Borealis node report v1 (`borealis-node-report/1`)

**Status:** fixed. Any structural change requires a new identifier. There are no minor versions.

The keywords MUST, MUST NOT and SHOULD are used as in RFC 2119.

Borealis Node runs explicitly configured local agents and presents their reports together. **It never performs detection itself.** This standard defines its combined report.

Machine-readable structure: [`node-report-v1.schema.json`](node-report-v1.schema.json). The invariants below are equally normative. See [`tools/check_report.py`](tools/check_report.py) and [`test-vectors-v1.json`](test-vectors-v1.json).

General rules ([Canonical JSON](canonical-json-v1.md) values, strict parsing, UTC timestamps, plain text) are as in the [agent report standard](agent-report-v1.md). The field set is closed.

## 1. Structure
```
{
  "standard": "borealis-node-report/1",
  "node":    {"name": "borealis-node", "version": <1-32 printable ASCII>},
  "run":     {"id": <lowercase UUID v4>, "started_at": <timestamp>, "finished_at": <timestamp>},
  "outcome": "ok" | "degraded" | "failed",
  "complete": <boolean>,
  "agents":  [ <agent entry>, ... ]        // 1-32 entries, in configuration order
}
```

**Agent entry** (every field required):

| Field | Rule |
|---|---|
| `config_name` | `^[a-z][a-z0-9-]{0,31}$`, unique within the report. This is the name from the Node configuration |
| `expected_name` | The agent identity the administrator configured (the agent-name pattern) |
| `outcome` | `"ok"`, `"degraded"` or `"failed"` (section 2) |
| `execution` | `{started_at, finished_at, exit_code (integer or null), timed_out, killed, stdout_bytes, output_too_large (booleans and integer), launch_error}`. `launch_error` is `null` or one of `not-found`, `not-a-file`, `spawn-failed`, `isolation-failed`, `describe-failed`, `describe-mismatch` |
| `validation` | `{result, problems, problems_total}`. `result` is `valid`, `invalid` or `not-run`. `problems` holds exactly `min(50, problems_total)` Node-generated messages of 1–300 printable ASCII characters (JSON paths and rule names only; **never quoted agent output**). A `valid` result has `problems_total == 0`; an `invalid` one has at least 1 |
| `diagnostic` | `null`, or at most 2000 characters (section 4) |
| `report_embedding` | `"embedded"`, `"omitted-for-size"` or `"none"` (section 3) |
| `report` | The agent's validated report, or `null` |
| `report_summary` | `null`, or `{bytes, status, findings_total, counts_by_severity {low, medium, high}, finding_ids (at most 200, each at most 98 printable ASCII characters), finding_ids_total, saved_as}` |

**Attribution** comes from the enclosing agent entry. The embedded `report` keeps its validated structure and values, and **the Node never modifies, adds to or removes an agent's findings.** It may be re-serialised, so byte-for-byte identity with the agent's output is not guaranteed.

A Node MUST validate every agent report against the agent standard, including all of its invariants. It MUST also check identity: the agent's `describe` output and its report's `agent.name` must both equal `expected_name`, and `standard` must be `borealis-agent-report/1`. Any failure makes the report `invalid`.

## 2. Outcomes
**Agent outcome:**

| Situation | `outcome` |
|---|---|
| Valid report with `status: "ok"` | `ok` |
| Valid report with `status: "partial"` | `degraded` |
| Valid report with `status: "error"` | `failed` (the report is still embedded, so any findings it contains are shown) |
| Not run, launch failure, timeout, crash, too much output, or an invalid report | `failed` |

**Usable analysis** means an agent outcome of `ok` or `degraded`.

**Node outcome:**
- `ok`: every agent's outcome is `ok`.
- `failed`: no agent produced usable analysis, including when every agent returned a valid `error` report.
- `degraded`: at least one agent produced usable analysis, and at least one agent is not `ok`.

## 3. Embedding and size
- **`embedded`:** `validation.result == "valid"`, `report` is present, `report_summary` is `null`.
- **`omitted-for-size`:** the report was valid but didn't fit its budget. `report` is `null` and `report_summary` is present. The agent's outcome is unchanged.
- **`none`:** there is no valid report. Both `report` and `report_summary` are `null`.
- **`complete`** is `false` exactly when at least one entry is `omitted-for-size`.

**Size limit: the serialised Node report MUST NOT exceed 64 MiB** (67,108,864 bytes).
- **Envelope reserve:** 8 MiB is reserved for everything other than embedded reports. Every non-report field is bounded (section 1). The worst case (32 entries, every field at its limit, every character at its maximum UTF-8 or escape length) is about 0.85 MB; see `max_envelope_node_report` in the test vectors.
- **Embedded budget:** 56 MiB. Each agent's budget is `floor(56 MiB / number of configured agents)`, measured on the CJ serialisation of its report. A larger report is `omitted-for-size`.
- **Final guarantee:** after serialising, if the Node report is still over 64 MiB, embedded reports are converted to `omitted-for-size` in **reverse configuration order** until it fits.
- **Sidecars:** when the Node writes its report to a file, it also saves every omitted report in full, as `<config_name>.json` in a sibling directory `<report file>.agents/`. The directory and files are created exclusively and existing files are never overwritten. `report_summary.saved_as` is that **file name only**, never a path; `null` if nothing was saved.

**Nothing is discarded silently.** Every configured agent always has an entry with its outcome, and either its full report, a summary (plus a saved copy where possible), or the reason there is no report.

## 4. Diagnostics and privacy
- Agent standard error can contain local paths, user names, environment details and tracebacks. **By default the Node MUST NOT include it in the report** (`diagnostic: null`), and MAY show a sanitised snippet on the local terminal only.
- A Node MAY offer an explicit option to include diagnostics. When it's used, the snippet is limited to 2000 characters, has control characters and escape sequences removed, and has the user's profile path and user name redacted. Such reports must be reviewed before being shared, and redaction is best-effort.
- Agent-supplied text is data, never instructions. A Node MUST strip control characters and terminal escape sequences from agent strings before displaying them.
- `saved_as` and all other Node fields MUST NOT contain absolute paths.
