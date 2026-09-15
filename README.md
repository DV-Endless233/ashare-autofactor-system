# A-Share Quant Factor System

**Author: dv**

An open, portable A-share quantitative factor research and automation system. It turns factor ideas and research requirements into a reproducible workflow covering factor construction, code execution, data processing, backtesting, independent evaluation, archival, and iterative improvement.

> This repository contains the portable code, workflow definitions, runtime contracts, profiles, and skills. Local market databases and large research outputs are intentionally kept outside the Git repository.

## What this project does

This project is designed to support the complete lifecycle of A-share factor research:

- Express a research objective or factor idea in a structured form.
- Translate the idea from the semantic space into executable operators and code.
- Reuse the shared A-share factor framework and `util/func.py` implementation.
- Generate factor values from local data and run preliminary backtests.
- Record artifacts, handoffs, verdicts, failures, and lessons learned.
- Apply independent review before a factor is accepted.
- Iterate automatically instead of stopping after a single code-generation attempt.
- Preserve a portable installation path so the system can be deployed to another machine without depending on the original workstation path.

The goal is not merely to produce a formula. The goal is a verifiable, auditable, and continuously improving research loop.

## Overall architecture

The system is organized around three cooperating roles:

### 1. `default` — controller and orchestrator

The `default` profile is the human-facing entry point. It receives the research request, decomposes it into executable tasks, dispatches work through the workflow controller, tracks dependencies, collects handoffs, and decides whether the process should continue to another iteration or be presented for human approval.

### 2. `dvcoder` — factor implementation worker

`dvcoder` converts factor semantics into the project's operator space and implements the core factor logic. It works with the shared A-share factor framework, produces runnable code and artifacts, and reports implementation or data problems. It does not independently approve its own work.

### 3. `evaluator` — independent reviewer

`evaluator` performs an independent review of factor candidates. It checks semantics, implementation correctness, data availability, leakage and timing risks, backtest evidence, duplication, and the required review dimensions. It is the profile authorized to issue pass/fail or return-for-revision judgments.

This separation prevents the factor generator from serving as its own reviewer.

## Complete Hermes Harness system

This project includes a complete **Hermes Harness** around the quant workflow, not just a collection of scripts:

- **Profiles** define durable role boundaries for `default`, `dvcoder`, and `evaluator`.
- **Skills** provide the shared factor methodology, implementation patterns, review templates, and governance rules.
- **Runtime controller** manages events, task state, reconciliation, publishing, and handoffs.
- **Policies** define allowed actions, budgets, failure handling, and phase transitions.
- **Schemas** define machine-readable contracts for events, artifacts, semantic designs, semantic verdicts, pipeline verdicts, and human review results.
- **SQLite registries** preserve factor-library and failure-review history when local databases are supplied.
- **Installation scripts** create the required directories and install only missing files without overwriting user data.

The Harness is the governance and execution layer that makes the research workflow repeatable, inspectable, and portable.

## Automatic loop

The workflow is built for an automatic closed loop:

```text
Research request
      ↓
Semantic factor design
      ↓
Task decomposition and dispatch
      ↓
Implementation by dvcoder
      ↓
Factor generation and preliminary backtest
      ↓
Independent review by evaluator
      ↓
Pass / return for revision / data-blocked decision
      ↓
Artifact and lesson archival
      ↓
Next iteration when required
```

A failed or incomplete candidate is not silently treated as successful. The controller records the state and routes the result back into the appropriate next step. This makes iteration explicit rather than relying on informal conversation memory.

## Strict schema and auditable contracts

The system emphasizes **strict schemas** rather than free-form conventions. Runtime JSON schemas and policy files provide explicit contracts for:

- semantic factor designs;
- implementation and operator-space handoffs;
- artifact manifests;
- events and state transitions;
- semantic and pipeline verdicts;
- failure reviews and human review results;
- permitted actions and phase transitions.

These contracts make outputs machine-checkable and reduce ambiguity between profiles. A result must carry structured evidence and a defined verdict; prose alone is not treated as a complete handoff.

## Repository layout

```text
HERMES.md                         Project-level workflow rules
profiles/                         default, dvcoder, and evaluator role definitions
skills/                           Shared factor and review methodology
runtime/
  controller/                     Event store, reducer, reconciliation, publishing
  policies/                       Action, budget, failure, and phase policies
  schemas/                        Strict JSON contracts
  validator/                      Handoff and schema validation tools
  tests/                          Runtime and validator tests
project/util/func.py              Shared portable utility implementation
config/                           Portable profile and provider templates
databases/                        Optional small workflow registries
install.sh                        Additive installation script
verify_install.sh                 Installation and integrity verification
```

Large A-share market databases, factor caches, and generated research outputs are not part of this repository. They should be provided locally according to the installation environment.

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/<YOUR_GITHUB_USERNAME>/<YOUR_REPOSITORY>.git
cd <YOUR_REPOSITORY>
```

### 2. Install the portable bundle

The installer is additive: it creates the required directories and does not overwrite existing user data or configuration files.

```bash
PROJECT_ROOT="$HOME/a-share-quant" \
HERMES_HOME="$HOME/.hermes" \
bash ./install.sh
```

You may choose different locations:

```bash
PROJECT_ROOT="$HOME/my-a-share-project" \
HERMES_HOME="$HOME/.hermes" \
bash ./install.sh
```

### 3. Verify the installation

Run verification using the same paths used during installation:

```bash
PROJECT_ROOT="$HOME/a-share-quant" \
HERMES_HOME="$HOME/.hermes" \
bash ./verify_install.sh
```

A successful verification ends with:

```text
VERIFY_OK
```

The verification checks the portable project path, Python compilation/import of `util/func.py`, SQLite integrity when databases are present, JSON schemas and policies, and the three profile configurations.

### 4. Configure the provider

Copy the provider template or edit the generated local environment file. Put actual credentials only in local `.env` files; never commit them.

```bash
$EDITOR "$HOME/.hermes/.env"
```

Keep API keys, database paths, and machine-specific settings outside GitHub.

### 5. Start the Harness

Run exactly one Gateway process, owned by the `default` profile:

```bash
hermes --profile default gateway
```

`dvcoder` and `evaluator` are worker profiles launched by the default dispatcher. They should not run separate Gateway processes or independent watchdogs.

## Development and validation

After making changes, run:

```bash
PROJECT_ROOT="$HOME/a-share-quant" \
HERMES_HOME="$HOME/.hermes" \
bash ./verify_install.sh
```

Runtime tests can be run from the repository checkout when the local Python test environment is available:

```bash
python -m pytest runtime/tests
```

## Security and data boundary

- Do not commit API keys, access tokens, passwords, private keys, or personal credentials.
- Do not commit local market databases or large factor caches.
- Keep the GitHub repository private unless the data and configuration boundary has been reviewed.
- Review `git status` and `git diff --cached` before every push.

## License

Add a license before making this repository public. Until then, treat the repository as private and controlled by its owner.
