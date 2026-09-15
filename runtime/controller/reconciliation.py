from typing import Any


def reconcile_downstream(round_id: str, action_code: str, existing_keys: set[str]) -> dict[str, Any]:
    key = f"{round_id}-{action_code.lower()}"
    if key in existing_keys:
        return {"created": False, "idempotency_key": key, "action_code": action_code}
    existing_keys.add(key)
    return {"created": True, "idempotency_key": key, "action_code": action_code}
