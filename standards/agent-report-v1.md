# Borealis agent report v1 (`borealis-agent-report/1`)

**Status:** fixed. Any structural change, additive or not, requires a new identifier (`borealis-agent-report/2`). There are no minor versions.

The keywords MUST, MUST NOT and SHOULD are used as in RFC 2119.

This standard is the **contract** between independently maintained Borealis agents and anything that consumes their output, such as Borealis Node. It is not shared code. Each agent implements it itself, and consumers **validate** reports rather than trusting them.

Machine-readable structure: [`agent-report-v1.schema.json`](agent-report-v1.schema.json). The schema covers structure only. **The invariants in this document are equally normative.** [`tools/check_report.py`](tools/check_report.py) is a reference checker for both, and [`test-vectors-v1.json`](test-vectors-v1.json) is authoritative.

## 1. Output and discovery
- An agent run writes **exactly one** report, as JSON, to standard output, and nothing else to standard output. Diagnostics go to standard error.
- It exits with 0 if a report was written, whatever its `status`, and non-zero if no valid report could be produced.
- Every agent MUST support `<agent> describe`. It prints one JSON object:
  `{"standard": "borealis-agent-report/1", "name", "version", "responsibility" (at most 200 characters), "personal_data": [...]}`.
- Reports MUST follow [Canonical JSON](canonical-json-v1.md) value rules and strict parsing: no floats, NaN, Infinity or duplicate keys, and integers within ±(2^53−1). Formatting (indentation, key order) is free, except where a digest is computed.
- **Timestamps** are UTC only: `YYYY-MM-DDTHH:MM:SS[.ffffff]Z`, with at most 6 fractional digits. Times taken from source data are converted to UTC.
- **Plain text fields** MUST NOT contain control characters other than tab and newline.

## 2. The report object
The field set is **closed**. Unknown fields are permitted only inside `extensions` and evidence `details`, and consumers MUST reject them anywhere else.

| Field | Type and rule |
|---|---|
| `standard` | `"borealis-agent-report/1"` |
| `agent` | `{name, version}`. `name` matches `^[a-z][a-z0-9-]{1,39}$`; `version` is 1–32 printable ASCII characters |
| `run` | `{id, started_at, finished_at}`. `id` is a lowercase UUID v4, and `finished_at` is not earlier than `started_at` |
| `source` | `{type, description, scope}` (section 3) |
| `status` | `"ok"`, `"partial"` or `"error"` (section 4) |
| `errors` | 0–100 items of `{code, message, ref?}` (section 5) |
| `errors_total` | Integer: all errors encountered |
| `error_counts` | Object, code → count (section 5) |
| `findings` | 0–1000 findings (section 6) |
| `findings_total` | Integer: the number of findings before any truncation |
| `extensions` | Optional object, agent-specific |

## 3. Source
- `type`: an ASCII token (`^[a-z0-9][a-z0-9._-]{0,63}$`), e.g. `windows-security-events` or `file-hashes`.
- `description`: plain text, at most 500 characters.
- `scope`: at most 100 items of `{kind, id, count?}`, where `kind` and `id` are ASCII tokens and `count` is an integer of 0 or more. The limit is enforced at input: an agent whose configuration would exceed it MUST refuse to run rather than truncate.
- **`source` MUST NOT contain absolute filesystem paths, user names, host names or original file names.** Use generic identifiers, e.g. `{kind: "event-export", id: "security-event-export"}` or `{kind: "root", id: "documents"}`.

## 4. Status

| Status | Meaning | Invariant |
|---|---|---|
| `ok` | The full declared scope was analysed | `errors_total == 0` |
| `partial` | Part of the scope was not analysed, **or** a loss truncation happened (section 7) | `errors_total ≥ 1` |
| `error` | The main analysis did not complete | `errors_total ≥ 1`. `findings` MAY contain only findings that describe why, and only when that reason is itself security-relevant (e.g. tampered reference data). Otherwise `findings` is empty |

`status: "ok"` with `findings: []` means "nothing was found within the declared scope". **It is not a statement that the system is safe**, and consumers MUST NOT present it as one.

## 5. Errors
- `code` matches `^[a-z][a-z0-9-]{0,63}$`. `message` is plain text, at most 500 characters. `ref` is optional (section 6.2).
- **`other-codes` is reserved** and MUST NOT be used as an error code.
- **Report-level truncation codes** are reserved, with fixed meanings:

  | Code | Meaning |
  |---|---|
  | `findings-truncated` | Findings were dropped (count or size limit); the message gives the number |
  | `evidence-truncated-for-size` | Evidence lists were cut to 100 items to meet the size limit |
  | `details-omitted-for-size` | Evidence `details` were removed to meet the size limit |
  | `report-too-large` | The report could not be fitted within the size limit (`status: "error"`) |

- **`errors` list:** it holds exactly `min(100, errors_total)` items, in this order:
  1. report-level truncation errors, in the table's order, **always retained**;
  2. all other errors, sorted by (`code`, `ref` or empty, `message`), up to 100 items in total.
- **`error_counts`:**
  - Up to 100 distinct codes: every code with its exact count.
  - More than 100: retain the reserved codes that are present, then other codes by count descending (ties by code ascending), until 99 keys are retained. Sum all remaining codes under `other-codes`. That's at most 100 keys, and `other-codes` appears only when 99 others are retained.
  - **The values of `error_counts` MUST add up to `errors_total`.** Every listed error's code appears in `error_counts` (or is covered by `other-codes`).

## 6. Findings

### 6.1 Finding object

| Field | Rule |
|---|---|
| `finding_id` | Section 6.3 |
| `created_at` | Timestamp |
| `rule_id` | `^[a-z][a-z0-9-]{0,63}$` |
| `severity` | `"low"`, `"medium"` or `"high"`. A label assigned by the rule, **not a probability**. Numeric confidence or probability scores MUST NOT appear anywhere in a report |
| `observation` | What was observed: facts only. Plain text, at most 2000 characters |
| `assessment` | Why it may matter. At most 2000 characters |
| `recommendation` | A human review action. It is never executed. At most 2000 characters |
| `limitations` | What the rule can get wrong. At most 2000 characters |
| `evidence` | 1–500 items of `{ref, timestamp?, details?}`. Refs are unique within the list; `details` is a free-form object |
| `evidence_total` | `len(canonical_refs)` (section 6.3), so the de-duplicated count **before** truncation |
| `evidence_refs_digest` | Section 6.3 |
| `evidence_details_omitted` | Optional, `true` only: `details` were removed to meet the size limit |
| `data_warnings` | Optional, at most 50 items of `{field, refs (at most 100), refs_total, warning (at most 500 characters)}`. `field` matches `^[A-Za-z][A-Za-z0-9_.-]{0,63}$`. Requires `data_warnings_total` |
| `data_warnings_total` | Required exactly when `data_warnings` is present |

`data_warnings` flag suspicious content inside source data, such as instruction-like text in an event field. They are indicators for a human, not detections.

### 6.2 Evidence references
`ref` is `<namespace>:<value>`:
- `namespace` matches `^[a-z][a-z0-9-]{0,63}$`;
- `value` is 1–1000 characters, NFC-normalised, with no control characters.

A ref is a stable pointer into the agent's source, e.g. `windows-security:record:2001`. Agents whose identifiers can contain arbitrary characters (such as file names) MUST define an unambiguous, reversible encoding for them in their own documentation.

### 6.3 Finding identity
1. `canonical_refs` = **all** evidence refs of the finding, including any later removed by truncation, NFC-normalised, de-duplicated and sorted ascending by Unicode code point.
2. `evidence_refs_digest = hex(sha256(utf8("\n".join(canonical_refs))))`.
3. `finding_id = agent.name + ":" + rule_id + ":" + hex(sha256(utf8(rule_id + "\n" + evidence_refs_digest)))[:16]`.

- **Uniqueness:** a finding is logically identified by (`rule_id`, `canonical_refs`). An agent MUST NOT emit two findings with the same identity. If its logic would produce them, it merges them into one finding before output. **Consumers MUST reject a report containing duplicate `finding_id`s.** That also catches the negligible chance of a 64-bit collision between different identities.
- **Recomputation:** a consumer can always recompute `finding_id` from `evidence_refs_digest`. When `evidence_total == len(evidence)` it can also recompute the digest from the listed refs, and MUST reject a mismatch.

## 7. Limits and truncation
Every bounded list is either bounded at input (the producer refuses a configuration that would exceed it) or carries a `_total` count and is truncated in a defined order. **Nothing is ever dropped without a count.**

### 7.1 Disclosed truncation (not an error; status unaffected)
The analysis was complete; only the listing is shortened, and the totals disclose it.
- **Evidence over 500 items:** list the first 500 `canonical_refs`, in canonical order.
- **Data-warning refs over 100:** list the first 100 in canonical order, with `refs_total`.
- **Data warnings over 50:** keep the first 50 ordered by `field`, with `data_warnings_total`.

### 7.2 Loss truncation (always `status: "partial"` plus an error)
- **Findings over 1000:** rank findings by (severity high → medium → low, `finding_id` ascending), keep the first 1000, and add `findings-truncated` with the number dropped. The retained findings are listed in that ranking order.
- **Size limit:** a serialised report (UTF-8, as written) MUST NOT exceed **10 MiB** (10,485,760 bytes). The measurement includes the truncation errors themselves. If it's exceeded, the producer applies these steps in order, re-measuring after each, and stops as soon as the report fits:
  1. Cut every evidence list to its first 100 canonical refs. Add `evidence-truncated-for-size`.
  2. Remove `details` from all evidence and set `evidence_details_omitted: true` on every affected finding. Add `details-omitted-for-size`.
  3. Drop findings from the end of the ranking above. Add or update `findings-truncated` with the cumulative number dropped.
  4. If it still doesn't fit: `status: "error"`, an empty `findings` list, and `report-too-large`.

Throughout, `evidence_total`, `evidence_refs_digest`, `findings_total`, `errors_total` and `error_counts` describe the **complete, pre-truncation** data. Consumers MUST reject reports over 10 MiB.

## 8. Privacy
- Reports are local by default. They MUST NOT contain secrets, credentials, file contents or absolute filesystem paths.
- Every kind of personal or identifying data that can appear **anywhere** in an agent's reports, refs and `details` included, MUST be declared in `describe`'s `personal_data`. The vocabulary:

  | Value | Meaning |
  |---|---|
  | `account-names` | User or service account names |
  | `ip-addresses` | IP addresses |
  | `host-names` | Computer or host names |
  | `file-names` | Names of files or directories |
  | `relative-file-paths` | Directory structure below a configured root |

- Agents document what their reports contain and that reports should be reviewed before being shared outside the machine.

## 9. Conformance
An implementation conforms if:
- its reports pass the schema and every invariant in this document;
- it reproduces the `canonical_json`, `finding_ids` and `error_aggregation` test vectors;
- its own tests demonstrate the truncation rules.
