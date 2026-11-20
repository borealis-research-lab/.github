"""JSON Schema cross-checks for the Borealis reporting standards v1.

Needs the test-only `jsonschema` package; skipped without it. Checks that the schemas
accept every valid vector and example, reject every structural violation, and accept
the invariant-only violations that only the normative text (and the checker) catch.
"""

import json
import sys
from pathlib import Path

import pytest

TOOLS = Path(__file__).resolve().parent
STANDARDS = TOOLS.parent
sys.path.insert(0, str(TOOLS))

import check_report as c  # noqa: E402

VECTORS = c.strict_loads((STANDARDS / "test-vectors-v1.json").read_bytes())
EXAMPLES = STANDARDS / "examples"

# Invalid report vectors that JSON Schema alone can detect (plus every "trailing-newline-*"
# vector: identifier patterns must reject a final newline in every regex engine).
SCHEMA_DETECTABLE = {
    "unknown-field", "unknown-finding-field", "timestamp-with-offset", "severity-not-label",
    "ref-without-namespace", "other-codes-used-as-code", "unknown-node-field", "saved-as-is-a-path",
}

jsonschema = pytest.importorskip("jsonschema")
referencing = pytest.importorskip("referencing")


def _validators():
    agent_schema = json.loads((STANDARDS / "agent-report-v1.schema.json").read_text(encoding="utf-8"))
    node_schema = json.loads((STANDARDS / "node-report-v1.schema.json").read_text(encoding="utf-8"))
    registry = referencing.Registry().with_resources([
        (agent_schema["$id"], referencing.Resource.from_contents(agent_schema)),
        (node_schema["$id"], referencing.Resource.from_contents(node_schema)),
    ])
    cls = jsonschema.Draft202012Validator
    cls.check_schema(agent_schema)
    cls.check_schema(node_schema)
    return cls(agent_schema, registry=registry), cls(node_schema, registry=registry)


AGENT_V, NODE_V = _validators()


@pytest.mark.parametrize("vector", VECTORS["reports"], ids=lambda v: v["name"])
def test_schema_agrees_with_checker(vector):
    validator = AGENT_V if vector["kind"] == "agent" else NODE_V
    schema_errors = list(validator.iter_errors(vector["report"]))
    if vector["valid"]:
        assert schema_errors == []
    elif vector["name"] in SCHEMA_DETECTABLE or vector["name"].startswith("trailing-newline-"):
        assert schema_errors, "schema should reject this structural violation"
    else:
        assert schema_errors == [], "invariant-only violation: schema accepts, checker rejects"


def test_schema_accepts_max_envelope():
    assert list(NODE_V.iter_errors(c.max_envelope_node_report())) == []


@pytest.mark.parametrize("name", sorted(p.name for p in EXAMPLES.glob("*.json")))
def test_schema_accepts_examples(name):
    report = json.loads((EXAMPLES / name).read_text(encoding="utf-8"))
    validator = NODE_V if name.startswith("node") else AGENT_V
    assert list(validator.iter_errors(report)) == []
