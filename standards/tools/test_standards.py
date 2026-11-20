"""Tests for the Borealis reporting standards v1.

Run from the repository root:  python -m pytest standards/tools
Standard library only (schema cross-checks are in test_schemas.py).
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


def test_all_vectors_pass():
    assert c.verify_vectors(STANDARDS / "test-vectors-v1.json") == []


@pytest.mark.parametrize("name", ["agent-report-nyyrikki.json", "agent-report-ilmarinen-partial.json"])
def test_agent_examples_are_valid(name):
    data = (EXAMPLES / name).read_bytes()
    assert c.validate_agent_report(c.strict_loads(data), len(data)) == []


def test_node_example_is_valid():
    data = (EXAMPLES / "node-report-degraded.json").read_bytes()
    assert c.validate_node_report(c.strict_loads(data), len(data)) == []


def test_examples_match_vector_reports():
    by_name = {v["name"]: v["report"] for v in VECTORS["reports"]}
    assert c.strict_loads((EXAMPLES / "agent-report-nyyrikki.json").read_bytes()) == by_name["valid-agent-ok"]
    assert c.strict_loads((EXAMPLES / "node-report-degraded.json").read_bytes()) == by_name["valid-node-degraded"]


def test_max_envelope_fits_reserve_and_is_valid():
    envelope = c.max_envelope_node_report()
    size = len(json.dumps(envelope, ensure_ascii=False).encode("utf-8"))
    assert size <= c.NODE_ENVELOPE_RESERVE
    assert c.validate_node_report(envelope) == []
    assert len(envelope["agents"]) == 32


def test_oversized_agent_report_is_rejected():
    report = c.strict_loads((EXAMPLES / "agent-report-nyyrikki.json").read_bytes())
    problems = c.validate_agent_report(report, size_bytes=c.MAX_AGENT_REPORT_BYTES + 1)
    assert any("10 MiB" in p for p in problems)


def test_problems_are_bounded_ascii():
    report = {"standard": "x", "unexpected": chr(0xE4) * 1000}
    for problem in c.validate_agent_report(report):
        assert problem.isascii() and len(problem) <= 300


@pytest.mark.parametrize("bad", [b'{"a":1,"a":2}', b"[NaN]", b"[1.0]", b"\xef\xbb\xbf{}", b"{} {}"])
def test_strict_parsing_rejects(bad):
    with pytest.raises(c.StrictJsonError):
        c.strict_loads(bad)


def test_aggregation_sum_always_equals_total():
    for v in VECTORS["error_aggregation"]:
        counts = v.get("counts") or c._generated_counts(v["generate"])
        aggregated = c.aggregate_error_counts(counts)
        assert sum(aggregated.values()) == sum(counts.values())
        assert len(aggregated) <= 100


def test_reserved_errors_are_listed_first():
    errors = [{"code": "a", "message": "m"}, {"code": "findings-truncated", "message": "3 dropped"}]
    assert c.order_errors(errors)[0]["code"] == "findings-truncated"


def _paths(obj, prefix=()):
    yield prefix
    if isinstance(obj, dict):
        for key, value in obj.items():
            yield from _paths(value, prefix + (key,))
    elif isinstance(obj, list):
        for index, value in enumerate(obj):
            yield from _paths(value, prefix + (index,))


@pytest.mark.parametrize(
    "example, kind",
    [("agent-report-ilmarinen-partial.json", "agent"), ("agent-report-nyyrikki.json", "agent"),
     ("node-report-degraded.json", "node")],
)
def test_validators_never_crash_on_mutated_reports(example, kind):
    """Consumers must report problems, never crash, whatever an agent emits."""
    import copy

    base = json.loads((EXAMPLES / example).read_text(encoding="utf-8"))
    validate = c.validate_agent_report if kind == "agent" else c.validate_node_report
    replacements = [None, 1, "x", [], {}, True, -5, chr(0xE4) * 600, [1, [2]], {"a": {}}, "DELETE"]
    for path in (p for p in _paths(base) if p):
        for replacement in replacements:
            mutated = copy.deepcopy(base)
            parent = mutated
            for key in path[:-1]:
                parent = parent[key]
            if replacement == "DELETE":
                if not isinstance(parent, dict):
                    continue
                del parent[path[-1]]
            else:
                parent[path[-1]] = replacement
            problems = validate(mutated)
            assert all(p.isascii() and len(p) <= 300 for p in problems)
