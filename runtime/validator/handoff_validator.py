#!/usr/bin/env python3
"""Zero-LLM validator for portable factor harness artifacts and handoffs."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, RefResolver

ROOT = Path(__file__).resolve().parents[1]
SCHEMAS = ROOT / "schemas"


def load_json(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as f:
        value = json.load(f)
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def schema_errors(data: dict[str, Any], schema_name: str) -> list[str]:
    schema_path = SCHEMAS / schema_name
    schema = load_json(schema_path)
    resolver = RefResolver(schema_path.as_uri(), schema)
    return [error.message for error in Draft202012Validator(schema, resolver=resolver).iter_errors(data)]


def validate_basic_handoff(path: Path) -> list[str]:
    try:
        data = load_json(path)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        return [str(exc)]
    return schema_errors(data, "handoff_envelope.v2.json")


def validate_artifact(root: Path, manifest_path: Path) -> list[str]:
    errors: list[str] = []
    try:
        data = load_json(manifest_path)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        return [str(exc)]
    errors.extend(schema_errors(data, "artifact_manifest.v1.json"))
    rel = Path(str(data.get("path", "")))
    if rel.is_absolute() or ".." in rel.parts:
        errors.append("artifact path must be relative and confined")
        return errors
    actual = root / rel
    if not actual.is_file():
        errors.append(f"artifact does not exist: {rel}")
        return errors
    digest = hashlib.sha256(actual.read_bytes()).hexdigest()
    if data.get("sha256") != f"sha256:{digest}":
        errors.append("artifact sha256 does not match file")
    if data.get("bytes") != actual.stat().st_size:
        errors.append("artifact byte count does not match file")
    if data.get("status") != "published":
        errors.append("only published artifacts may be used as evidence")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    h = sub.add_parser("handoff"); h.add_argument("path", type=Path)
    a = sub.add_parser("artifact"); a.add_argument("root", type=Path); a.add_argument("manifest", type=Path)
    args = parser.parse_args()
    errors = validate_basic_handoff(args.path) if args.command == "handoff" else validate_artifact(args.root, args.manifest)
    if errors:
        print("INVALID")
        print("\n".join(f"- {e}" for e in errors))
        return 1
    print("VALID")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
