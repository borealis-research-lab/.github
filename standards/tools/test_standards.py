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
    replacements = [None, 1, "x", [], {}, True, -5, chr(0xE4) * 600, [1, [2]], {"a": {}},
                    chr(0xD800), "x" + chr(0xDC00), "x" + chr(10), "DELETE"]
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


# --- Strict identifiers and Unicode scalar values -----------------------------------------------

NL = chr(10)


@pytest.mark.parametrize("regex_name", [
    "RE_AGENT_NAME", "RE_CONFIG_NAME", "RE_CODE", "RE_TOKEN", "RE_FIELD", "RE_NAMESPACE",
    "RE_UUID4", "RE_TIMESTAMP", "RE_HEX64",
])
def test_identifier_patterns_reject_trailing_newline(regex_name):
    samples = {
        "RE_AGENT_NAME": "nyyrikki", "RE_CONFIG_NAME": "ilmarinen", "RE_CODE": "file-changed",
        "RE_TOKEN": "security-event-export", "RE_FIELD": "TargetUserName", "RE_NAMESPACE": "file",
        "RE_UUID4": "3f2b8c1e-5d4a-4b6f-9e2d-1a2b3c4d5e6f", "RE_TIMESTAMP": "2026-11-20T14:00:00Z",
        "RE_HEX64": "0" * 64,
    }
    regex = getattr(c, regex_name)
    assert regex.fullmatch(samples[regex_name])
    assert not regex.fullmatch(samples[regex_name] + NL)


def test_printable_ascii_rejects_trailing_newline():
    assert c.RE_PRINTABLE_ASCII.fullmatch("0.2.0")
    assert not c.RE_PRINTABLE_ASCII.fullmatch("0.2.0" + NL)


@pytest.mark.parametrize("text, valid", [
    (rb'{"v":"\ud83d\ude00"}', True),
    (rb'{"v":"\ud800"}', False),
    (rb'{"v":"\udc00"}', False),
    (rb'{"v":"\ude00\ud83d"}', False),
    (rb'{"\udbff":1}', False),
])
def test_strict_parsing_requires_unicode_scalar_values(text, valid):
    if valid:
        assert c.strict_loads(text) == {"v": chr(0x1F600)}
    else:
        with pytest.raises(c.StrictJsonError):
            c.strict_loads(text)


def test_canonical_json_rejects_surrogates_with_controlled_error():
    with pytest.raises(c.CanonicalJsonError):
        c.canonical_json({"k": chr(0xD800)})
    assert c.canonical_json([chr(0x1F600)]) == ('["' + chr(0x1F600) + '"]').encode("utf-8")


def test_validators_reject_surrogates_without_crashing():
    report = c.strict_loads((EXAMPLES / "agent-report-nyyrikki.json").read_bytes())
    report["findings"][0]["evidence"][0]["ref"] = "windows-security:record:" + chr(0xD800)
    report["findings"][0]["observation"] = "x" + chr(0xDC00)
    problems = c.validate_agent_report(report)
    assert any("surrogate" in p for p in problems)


@pytest.mark.parametrize("payload", [
    rb'{"standard": "borealis-agent-report/1", "agent": {"name": "\ud800", "version": "1"}}',
    rb'{"value": "\udc00"}',
    b'{"a": 1, "a": 2}',
    b"[NaN]",
    bytes([0xFF, 0xFE]),
    b"[" * 100000,
])
def test_cli_handles_malformed_input_without_crashing(tmp_path, payload):
    import subprocess

    path = tmp_path / "report.json"
    path.write_bytes(payload)
    result = subprocess.run(
        [sys.executable, "-I", str(TOOLS / "check_report.py"), "agent", str(path)],
        capture_output=True, text=True, timeout=60,
    )
    assert result.returncode == 1
    assert "INVALID" in result.stdout
    assert "Traceback" not in result.stderr


def test_cli_rejects_trailing_newline_identifier(tmp_path):
    import subprocess

    report = c.strict_loads((EXAMPLES / "agent-report-nyyrikki.json").read_bytes())
    report["agent"]["name"] = "nyyrikki" + NL
    path = tmp_path / "report.json"
    path.write_text(json.dumps(report), encoding="utf-8")
    result = subprocess.run(
        [sys.executable, "-I", str(TOOLS / "check_report.py"), "agent", str(path)],
        capture_output=True, text=True, timeout=60,
    )
    assert result.returncode == 1 and "agent name" in result.stdout
