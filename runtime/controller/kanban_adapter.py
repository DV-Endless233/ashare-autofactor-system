from typing import Any, Callable

from .event_store import EventStore
from .publish import validate_action


def publish_and_schedule(
    *,
    store: EventStore,
    round_id: str,
    phase: str,
    result_code: str,
    action_code: str,
    task_creator: Callable[..., dict[str, Any]],
    task_body: str,
) -> dict[str, Any]:
    """Controlled boundary for Kanban: validate before creating downstream work.

    The creator is injected so unit tests do not touch a live Kanban DB. In production
    it should be a thin adapter around the default profile's controlled task creation.
    """
    validate_action(action_code, phase, result_code)
    published = store.append("handoff_published", round_id, "publish", {
        "phase": phase, "result_code": result_code, "action_code": action_code,
    })
    key = f"{round_id}-{action_code.lower()}"
    task = task_creator(title=f"{round_id} {action_code}", assignee="default", body=task_body, idempotency_key=key)
    store.append("downstream_task_scheduled", round_id, "controller", {
        "action_code": action_code, "idempotency_key": key, "task_id": task.get("task_id"),
    })
    return {"published_event": published, "task": task, "idempotency_key": key}
