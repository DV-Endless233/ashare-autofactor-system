#!/usr/bin/env python3
"""Generate shared JSON Schema enums from the action/failure registries."""
from __future__ import annotations
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
POLICIES = ROOT / "policies"
OUT = ROOT / "schemas" / "registry_enums.v1.json"

def main() -> None:
    action = json.loads((POLICIES / "action_registry.v2.json").read_text(encoding="utf-8"))
    failure = json.loads((POLICIES / "failure_policy.v2.json").read_text(encoding="utf-8"))
    actions = sorted({item["action_code"] for item in action["actions"]})
    failures = sorted(failure["failure_classes"])
    data = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": "factor.registry_enums.v1",
        "title": "Generated Factor Registry Enums",
        "$defs": {
            "actionCode": {"enum": actions},
            "failureClass": {"enum": failures},
        },
    }
    OUT.write_text(json.dumps(data, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")
    print(f"generated {OUT} ({len(actions)} actions, {len(failures)} failures)")

if __name__ == "__main__":
    main()
