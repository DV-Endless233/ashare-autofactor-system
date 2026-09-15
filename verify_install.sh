#!/usr/bin/env bash
set -euo pipefail
PROJECT_ROOT="${PROJECT_ROOT:-$HOME/a-share-quant}"
HERMES_HOME="${HERMES_HOME:-$HOME/.hermes}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
errors=0
warn() { printf 'WARN: %s\n' "$*"; }
fail() { printf 'FAIL: %s\n' "$*"; errors=$((errors+1)); }

[[ -d "$PROJECT_ROOT" ]] || fail "PROJECT_ROOT does not exist: $PROJECT_ROOT"
[[ -f "$PROJECT_ROOT/util/func.py" ]] || fail "missing default util/func.py"
python -m py_compile "$PROJECT_ROOT/util/func.py" || fail "func.py does not compile"

python - "$PROJECT_ROOT" <<'PY' || exit 1
import importlib.util, pathlib, sys
root=pathlib.Path(sys.argv[1])
spec=importlib.util.spec_from_file_location('portable_func', root/'util/func.py')
mod=importlib.util.module_from_spec(spec)
try:
    spec.loader.exec_module(mod)
except ModuleNotFoundError as e:
    print(f'WARN: func.py import dependency unavailable: {e.name}')
except Exception as e:
    print(f'FAIL: func.py import failed: {e}')
    raise SystemExit(1)
else:
    print('OK: func.py imported')
PY

python - "$PROJECT_ROOT" <<'PY' || exit 1
import pathlib, sqlite3, sys
root=pathlib.Path(sys.argv[1]); dbdir=root/'databases'
if not dbdir.exists():
    print('WARN: no databases directory')
for db in sorted(dbdir.glob('*.db')):
    con=sqlite3.connect(db)
    result=con.execute('PRAGMA integrity_check').fetchone()[0]
    if result != 'ok': raise SystemExit(f'FAIL: SQLite integrity {db}: {result}')
    tables=[r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")]
    print(f'OK: {db.name} integrity; tables={tables}')
    con.close()
PY

for schema in "$PROJECT_ROOT"/runtime/schemas/*.json "$PROJECT_ROOT"/runtime/policies/*.json "$PROJECT_ROOT"/runtime/capabilities/*.json; do
  [[ -f "$schema" ]] || continue
  python -m json.tool "$schema" >/dev/null || fail "invalid JSON schema/policy: $schema"
done
for profile in default dvcoder evaluator; do
  cfg="$HERMES_HOME/profiles/$profile/config.yaml"
  [[ -f "$cfg" ]] || fail "missing profile config: $cfg"
  python - "$cfg" <<'PY' || fail "invalid YAML profile config"
import sys
try:
 import yaml
 yaml.safe_load(open(sys.argv[1]))
except ImportError:
 print('WARN: PyYAML unavailable; skipped YAML parse')
except Exception as e:
 print(e); raise SystemExit(1)
PY
done

if [[ "$errors" -eq 0 ]]; then printf 'VERIFY_OK\n'; else printf 'VERIFY_FAILED (%s errors)\n' "$errors"; exit 1; fi
