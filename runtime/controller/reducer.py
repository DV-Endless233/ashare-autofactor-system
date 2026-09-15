from copy import deepcopy
from typing import Any


def apply_event(state: dict[str, Any], event: dict[str, Any]) -> dict[str, Any]:
    state = deepcopy(state)
    event_type = event["event_type"]
    payload = event.get("payload", {})
    state.setdefault("phases", {})
    if event_type == "round_created":
        state["round_id"] = event["round_id"]
        state["status"] = "active"
    elif event_type == "phase_completed":
        phase = payload["phase"]
        state["phases"][phase] = {"status": "completed", "result_code": payload["result_code"]}
    elif event_type == "action_applied":
        state["last_action"] = payload["action_code"]
    elif event_type == "round_closed":
        state["status"] = "closed"
    state["last_sequence"] = event.get("sequence", state.get("last_sequence", 0))
    return state


def replay(events: list[dict[str, Any]]) -> dict[str, Any]:
    state: dict[str, Any] = {}
    for event in events:
        state = apply_event(state, event)
    return state
