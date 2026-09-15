import pytest

from runtime.controller.reducer import apply_event
from runtime.controller.event_store import EventStore
from runtime.controller.publish import validate_action, validate_phase_result
from runtime.controller.reconciliation import reconcile_downstream
from runtime.controller.kanban_adapter import publish_and_schedule


def test_shared_failure_requires_registered_action():
    with pytest.raises(ValueError, match="not registered"):
        validate_action("does_not_exist", "semantic_pre_review", "x")


def test_operator_metric_pass_routes_to_pipeline_review():
    result = validate_phase_result("operator_build", "METRICS_PASS")
    assert result["next_action"] == "REQUEST_PIPELINE_REVIEW"


def test_operator_backtest_execution_failure_routes_to_retry_backtest():
    result = validate_phase_result("operator_build", "BACKTEST_EXECUTION_FAILED")
    assert result["next_action"] == "RETRY_BACKTEST"


def test_reducer_replays_phase_completion_and_action():
    state = {}
    state = apply_event(state, {"event_type": "round_created", "round_id": "R1", "payload": {}})
    state = apply_event(state, {"event_type": "phase_completed", "round_id": "R1", "payload": {"phase": "operator_build", "result_code": "METRICS_PASS"}})
    state = apply_event(state, {"event_type": "action_applied", "round_id": "R1", "payload": {"action_code": "REQUEST_PIPELINE_REVIEW"}})
    assert state["round_id"] == "R1"
    assert state["phases"]["operator_build"]["status"] == "completed"
    assert state["last_action"] == "REQUEST_PIPELINE_REVIEW"


def test_event_store_is_append_only(tmp_path):
    store = EventStore(tmp_path / "events.jsonl")
    event = store.append("round_created", "R1", "runtime", {"x": 1})
    assert event["sequence"] == 1
    assert store.read_all()[0]["event_type"] == "round_created"
    with pytest.raises(FileExistsError):
        store.append("round_created", "R1", "runtime", {"x": 2}, event_id=event["event_id"])


def test_reconciliation_is_idempotent():
    existing = set()
    first = reconcile_downstream("R1", "REQUEST_PIPELINE_REVIEW", existing)
    second = reconcile_downstream("R1", "REQUEST_PIPELINE_REVIEW", existing)
    assert first["created"] is True
    assert second["created"] is False
    assert first["idempotency_key"] == second["idempotency_key"]


def test_kanban_adapter_validates_before_creating_task(tmp_path):
    store = EventStore(tmp_path / "events.jsonl")
    calls = []

    def create(**kwargs):
        calls.append(kwargs)
        return {"task_id": "t1"}

    result = publish_and_schedule(
        store=store, round_id="R1", phase="operator_build", result_code="METRICS_PASS",
        action_code="REQUEST_PIPELINE_REVIEW", task_creator=create, task_body="review",
    )
    assert result["task"]["task_id"] == "t1"
    assert calls[0]["idempotency_key"] == "R1-request_pipeline_review"
    assert [e["event_type"] for e in store.read_all()] == ["handoff_published", "downstream_task_scheduled"]


def test_kanban_adapter_rejects_invalid_action_without_side_effect(tmp_path):
    store = EventStore(tmp_path / "events.jsonl")
    calls = []
    with pytest.raises(ValueError):
        publish_and_schedule(
            store=store, round_id="R1", phase="operator_build", result_code="METRICS_PASS",
            action_code="RESTART_SEMANTIC_DIRECTION", task_creator=lambda **kw: calls.append(kw), task_body="x",
        )
    assert calls == []
    assert store.read_all() == []
