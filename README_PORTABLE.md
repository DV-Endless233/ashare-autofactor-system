# Portable A-share quant bundle

## Installation

```bash
PROJECT_ROOT="$HOME/a-share-quant" HERMES_HOME="$HOME/.hermes" ./install.sh
```

The installer is additive. It never overwrites an existing `database/` file, `util/` file, profile config, or `.env`. The shipped `util/func.py` is the default shared-function implementation and is also preserved once installed. Users may replace database files under `database/` and any `util/*.py` except `util/func.py`; replacing `func.py` is intentionally not part of the supported customization path.

`PROJECT_ROOT` is the installed project root. `${HERMES_HOME}/profiles/{default,dvcoder,evaluator}` are the three profile configuration directories. All project and Hermes paths in this release are relative or parameterized; it has no dependency on the original source workstation path.

## Model and credentials

Each `config/profile-*.yaml` contains a model name, provider, and API base URL placeholder. Set the actual API key in `${HERMES_HOME}/.env` or the profile `.env` file. Do not commit keys. The current reference setup uses provider `custom` with an OpenAI-compatible `base_url`; users can replace `provider`, `model.default`, and `base_url` with their provider's values. Keep the three profiles independently configurable.

## Gateway rule

Run exactly one Gateway process, owned by `default`. `dvcoder` and `evaluator` are worker profiles launched by the default dispatcher and must not run their own Gateway or watchdog. Before starting, stop any stale Gateway process and verify only the default instance is active.

```bash
hermes --profile default gateway
```

## Verification

```bash
PROJECT_ROOT="$HOME/a-share-quant" HERMES_HOME="$HOME/.hermes" ./verify_install.sh
```

Verification covers: portable path residue, Python compilation/import of `util/func.py`, SQLite integrity and schema inventory for databases, runtime schema checks where the shipped checker exists, and profile configuration parsing. A missing optional database or runtime dependency is reported with a clear warning; an installed corrupt database or invalid schema fails the check.
