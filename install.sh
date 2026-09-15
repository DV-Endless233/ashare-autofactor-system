#!/usr/bin/env bash
set -euo pipefail

# Install the portable A-share quant bundle without overwriting user data.
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="${PROJECT_ROOT:-$HOME/a-share-quant}"
HERMES_HOME="${HERMES_HOME:-$HOME/.hermes}"
PROFILE_ROOT="${PROFILE_ROOT:-$HERMES_HOME/profiles}"

mkdir -p "$PROJECT_ROOT" "$PROJECT_ROOT/database" "$PROJECT_ROOT/databases" "$PROJECT_ROOT/util" "$PROJECT_ROOT/docs/session_handoffs" "$PROJECT_ROOT/factor_replicate_outputs/review_queue" "$PROJECT_ROOT/factor_replicate_outputs/evaluator_passed" \
  "$PROFILE_ROOT/default" "$PROFILE_ROOT/dvcoder" "$PROFILE_ROOT/evaluator"

copy_if_missing() {
  local src="$1" dst="$2"
  if [[ -e "$dst" ]]; then
    printf 'preserve %s\n' "$dst"
  else
    mkdir -p "$(dirname "$dst")"
    cp -R "$src" "$dst"
    printf 'install  %s\n' "$dst"
  fi
}

merge_dir_if_missing() {
  local src="$1" dst="$2" item rel
  mkdir -p "$dst"
  while IFS= read -r -d '' item; do
    rel="${item#"$src"/}"
    copy_if_missing "$item" "$dst/$rel"
  done < <(find "$src" -mindepth 1 -print0)
}

# Project code and default shared function are immutable defaults; user data wins.
copy_if_missing "$SCRIPT_DIR/HERMES.md" "$PROJECT_ROOT/HERMES.md"
copy_if_missing "$SCRIPT_DIR/project/util/func.py" "$PROJECT_ROOT/util/func.py"
for item in databases runtime skills; do merge_dir_if_missing "$SCRIPT_DIR/$item" "$PROJECT_ROOT/$item"; done
for item in profiles/default profiles/dvcoder profiles/evaluator; do
  copy_if_missing "$SCRIPT_DIR/$item/SOUL.md" "$PROFILE_ROOT/${item#profiles/}/SOUL.md"
done
for item in docs; do
  [[ -d "$SCRIPT_DIR/$item" ]] && copy_if_missing "$SCRIPT_DIR/$item" "$PROJECT_ROOT/$item"
done
for item in session_handoffs review_queue evaluator_passed; do
  mkdir -p "$PROJECT_ROOT/$( [[ "$item" == session_handoffs ]] && printf docs/ || printf factor_replicate_outputs/ )$item"
done

# Profile templates are rendered with installation paths; existing configs remain untouched.
for profile in default dvcoder evaluator; do
  cfg="$PROFILE_ROOT/$profile/config.yaml"
  if [[ ! -e "$cfg" ]]; then
    sed -e "s#\${PROJECT_ROOT}#${PROJECT_ROOT}#g" -e "s#\${HERMES_HOME}#${HERMES_HOME}#g" \
      "$SCRIPT_DIR/config/profile-${profile}.yaml" > "$cfg"
  else
    printf 'preserve %s\n' "$cfg"
  fi
  if [[ ! -e "$PROFILE_ROOT/$profile/.env" ]]; then
    cp "$SCRIPT_DIR/config/profile.env.example" "$PROFILE_ROOT/$profile/.env"
  fi
done

copy_if_missing "$SCRIPT_DIR/config/provider.env.example" "$HERMES_HOME/.env"
printf '\nInstalled portable bundle at %s\n' "$PROJECT_ROOT"
printf 'Run: PROJECT_ROOT=%q HERMES_HOME=%q bash %q\n' "$PROJECT_ROOT" "$HERMES_HOME" "$SCRIPT_DIR/verify_install.sh"
printf 'Only start the default gateway: hermes --profile default gateway\n'