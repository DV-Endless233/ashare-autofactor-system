import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]


def _load(name: str) -> dict[str, Any]:
    return json.loads((ROOT / "policies" / name).read_text(encoding="utf-8"))


def _actions() -> dict[str, dict[str, Any]]:
    return {x["action_code"]: x for x in _load("action_registry.v2.json")["actions"]}


def validate_action(action_code: str, phase: str, result_code: str) -> dict[str, Any]:
    action = _actions().get(action_code)
    if action is None:
        raise ValueError(f"action {action_code!r} not registered")
    allowed = action["allowed_from"]
    if not any(item in {result_code, f"{phase}:{result_code}", f"{phase}:{result_code.lower()}"} for item in allowed):
        raise ValueError(f"action {action_code} is not allowed from {phase}:{result_code}")
    return action


def validate_phase_result(phase: str, result_code: str) -> dict[str, Any]:
    policy = _load("phase_transitions.v2.json")["phase_result_protocol"]
    for result in policy.get(phase, []):
        if result["result_code"] == result_code:
            action = result["next_action"]
            if action not in {x["action_code"] for x in _load("action_registry.v2.json")["actions"]} and action not in {"USE_SHARED_FAILURE_POLICY", "CHECKPOINT_AND_FIX_VALIDATION"}:
                raise ValueError(f"phase result points to unregistered action {action}")
            return result
    raise ValueError(f"unknown result {phase}:{result_code}")
