# Borealis standards

These standards are the **contracts** that let independently developed Borealis components work together **without trusting each other's output**. Each component implements them itself; none of this is a shared runtime dependency.

| Document | Identifier | Purpose |
|---|---|---|
| [Canonical JSON v1](canonical-json-v1.md) | — | Byte-exact serialisation for digests and fingerprints, plus strict parsing rules |
| [Agent report v1](agent-report-v1.md) ([schema](agent-report-v1.schema.json)) | `borealis-agent-report/1` | What every agent outputs for one run |
| [Node report v1](node-report-v1.md) ([schema](node-report-v1.schema.json)) | `borealis-node-report/1` | What Borealis Node outputs after running several agents |
| [Test vectors v1](test-vectors-v1.json) | — | **Authoritative** expected results that implementations must reproduce |
| [Examples](examples/) | — | Valid example reports |

**Versioning:** each identifier is fixed. Any structural change gets a new identifier; there are no minor versions.

**Schemas and invariants:** the JSON Schemas describe structure. The documents also define invariants (status and error consistency, digests, uniqueness, truncation, outcome aggregation) that JSON Schema can't express. Both are normative.

## Reference checker
`tools/check_report.py` is a standard-library reference implementation of the checks. It is used to test these standards, not as a dependency of agents.

```bash
python standards/tools/check_report.py agent path/to/report.json
python standards/tools/check_report.py node  path/to/node-report.json
python standards/tools/check_report.py vectors
```

Tests: `python -m pytest standards/tools`. The schema cross-checks additionally need the test-only `jsonschema` package.
