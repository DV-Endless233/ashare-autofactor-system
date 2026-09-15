import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VALIDATOR = ROOT / "validator" / "handoff_validator.py"


def run(*args):
    return subprocess.run([sys.executable, str(VALIDATOR), *map(str, args)], text=True, capture_output=True)


def test_invalid_handoff_is_rejected(tmp_path):
    p = tmp_path / "handoff.json"
    p.write_text(json.dumps({"schema_version": "wrong"}), encoding="utf-8")
    result = run("handoff", p)
    assert result.returncode == 1
    assert "INVALID" in result.stdout


def test_artifact_hash_and_status_are_checked(tmp_path):
    artifact = tmp_path / "metrics.json"
    artifact.write_text("{}", encoding="utf-8")
    digest = hashlib.sha256(artifact.read_bytes()).hexdigest()
    manifest = tmp_path / "manifest.json"
    manifest.write_text(json.dumps({
        "artifact_id": "metrics", "artifact_schema": "factor.backtest_metrics.v1",
        "path": "metrics.json", "sha256": f"sha256:{digest}", "bytes": artifact.stat().st_size,
        "producer_profile": "dvcoder", "producer_run_id": "run1", "input_refs": [], "status": "published"
    }), encoding="utf-8")
    result = run("artifact", tmp_path, manifest)
    assert result.returncode == 0
    assert result.stdout.strip() == "VALID"


def test_artifact_traversal_is_rejected(tmp_path):
    manifest = tmp_path / "manifest.json"
    manifest.write_text(json.dumps({"path": "../secret", "status": "published"}), encoding="utf-8")
    result = run("artifact", tmp_path, manifest)
    assert result.returncode == 1
    assert "confined" in result.stdout
