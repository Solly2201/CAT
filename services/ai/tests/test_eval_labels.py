"""Evaluation-label integrity.

The labelled query sets are the project's only measurement of whether
the legal-answer pipeline is getting better or worse, so a wrong label
is worse than a wrong answer: it hides the wrong answer. Three labels
were reconciled when the RTI Act was ingested and the child-safety
emergency route was added, and these tests pin down both the shape that
makes such a reconciliation auditable and the harness behaviour that
makes a safety-routing expectation real rather than decorative.

Deliberately index-free -- these read the label files and exercise the
harness's own logic with a stub, so they run on a clean checkout and in
CI where no index has been built.
"""
import importlib.util
import json
import os
import sys

HERE = os.path.dirname(__file__)
EVAL_DIR = os.path.join(HERE, "..", "eval")
sys.path.insert(0, os.path.join(HERE, ".."))

VALID_SEVERITIES = {"normal", "serious", "emergency", "harmful_request"}


def _load(name):
    path = os.path.join(EVAL_DIR, name)
    with open(path, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


ALL_ROWS = _load("queries.jsonl") + _load("queries_human.jsonl")
BY_ID = {row["id"]: row for row in ALL_ROWS}


def _harness():
    """Import eval/run_eval.py by path; it is a script, not a package."""
    spec = importlib.util.spec_from_file_location(
        "_run_eval_under_test", os.path.join(EVAL_DIR, "run_eval.py")
    )
    module = importlib.util.module_from_spec(spec)
    sys.modules["_run_eval_under_test"] = module
    spec.loader.exec_module(module)
    return module


class _StubAnswer:
    def __init__(self, abstained, severity="normal", reason=None):
        self.abstained = abstained
        self.severity = severity
        self.reason = reason


def _run(monkeypatch, rows, answer):
    module = _harness()
    monkeypatch.setattr(module, "handle_legal_query", lambda _q: answer)
    return module.evaluate_abstention(rows, "hybrid")


# --- label-file integrity ------------------------------------------------

def test_every_row_has_the_required_fields():
    for row in ALL_ROWS:
        for key in ("id", "category", "query", "relevant_chunk_ids", "expect_abstain"):
            assert key in row, f"{row.get('id')} missing {key}"
        assert isinstance(row["expect_abstain"], bool), row["id"]
        assert row["query"].strip(), row["id"]


def test_ids_are_unique_across_both_sets():
    ids = [row["id"] for row in ALL_ROWS]
    assert len(ids) == len(set(ids))


def test_an_answerable_row_names_its_gold_and_an_abstaining_row_does_not():
    """The two must not drift apart: a row expected to answer with no
    gold chunks cannot be scored, and a row expected to abstain that
    still carries gold chunks is a half-finished edit."""
    for row in ALL_ROWS:
        if row["expect_abstain"]:
            assert row["relevant_chunk_ids"] == [], row["id"]
        else:
            assert row["relevant_chunk_ids"], row["id"]


def test_reconciled_rows_record_what_they_superseded():
    """A changed expectation must stay auditable. Anyone reading the set
    later should be able to see what it used to assert and why, without
    going through git history."""
    for query_id in ("q35", "h286", "h029"):
        row = BY_ID[query_id]
        assert "superseded_expectation" in row, query_id
        assert row["notes"].strip(), query_id
        assert len(row["notes"]) > 80, f"{query_id}: reason too thin to audit"


def test_rti_rows_expect_the_provision_that_governs_them():
    # s.6 is "Request for obtaining information" -- the provision that
    # actually governs making a request, chosen from the Act rather than
    # from whatever the system happens to return.
    assert BY_ID["q35"]["relevant_chunk_ids"] == ["rti:6"]
    assert BY_ID["h286"]["relevant_chunk_ids"] == ["rti:6"]
    assert BY_ID["q35"]["expect_abstain"] is False
    assert BY_ID["h286"]["expect_abstain"] is False


def test_child_abduction_row_expects_the_emergency_route_not_a_bare_abstention():
    row = BY_ID["h029"]
    assert row["expect_abstain"] is True
    assert row["expect_severity"] == "emergency"
    assert row["expect_reason"] == "risk_child_safety"
    # The retrieval expectation is superseded, not discarded.
    assert row["superseded_expectation"]["relevant_chunk_ids"] == ["bns:137"]


def test_declared_severities_are_real_severities():
    for row in ALL_ROWS:
        if "expect_severity" in row:
            assert row["expect_severity"] in VALID_SEVERITIES, row["id"]
            assert row["expect_abstain"] is True, (
                f"{row['id']}: a severity expectation only means something "
                f"on a row where the pipeline withholds an answer"
            )


# --- harness behaviour ---------------------------------------------------

def test_routing_expectation_catches_the_right_call_for_the_wrong_reason(monkeypatch):
    """The point of expect_severity: withholding an answer is not by
    itself correct. A child-abduction query that abstains because the
    corpus lacks the law has failed, even though it abstained."""
    row = {"id": "x", "category": "c", "query": "q", "relevant_chunk_ids": [],
           "expect_abstain": True, "expect_severity": "emergency",
           "expect_reason": "risk_child_safety"}

    right = _run(monkeypatch, [row],
                 _StubAnswer(True, "emergency", "risk_child_safety"))
    assert right["accuracy"] == 1.0
    assert right["wrong_routing_ids"] == []

    wrong_severity = _run(monkeypatch, [row],
                          _StubAnswer(True, "normal", "insufficient_evidence"))
    assert wrong_severity["accuracy"] == 0.0
    assert wrong_severity["wrong_routing_ids"], "a wrong route must be reported"

    wrong_reason = _run(monkeypatch, [row],
                        _StubAnswer(True, "emergency", "risk_threat_to_life"))
    assert wrong_reason["accuracy"] == 0.0
    assert wrong_reason["wrong_routing_ids"]


def test_rows_without_a_routing_expectation_behave_exactly_as_before(monkeypatch):
    row = {"id": "y", "category": "c", "query": "q", "relevant_chunk_ids": [],
           "expect_abstain": True}
    result = _run(monkeypatch, [row], _StubAnswer(True, "normal", "whatever"))
    assert result["accuracy"] == 1.0
    assert result["wrong_routing_ids"] == []


def test_false_answer_and_false_abstain_still_separate(monkeypatch):
    answerable = {"id": "a", "category": "c", "query": "q",
                  "relevant_chunk_ids": ["bns:1"], "expect_abstain": False}
    abstaining = {"id": "b", "category": "c", "query": "q",
                  "relevant_chunk_ids": [], "expect_abstain": True}

    abstained = _run(monkeypatch, [answerable], _StubAnswer(True))
    assert abstained["false_abstain_ids"] == ["a"]
    assert abstained["false_answer_ids"] == []

    answered = _run(monkeypatch, [abstaining], _StubAnswer(False))
    assert answered["false_answer_ids"] == ["b"]
    assert answered["false_abstain_ids"] == []
