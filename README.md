<div align="right">
  <a href="#中文">中文</a> | <a href="#english">English</a>
</div>

# A-Share Quant Factor System

**作者 / Author: dv**

<a id="中文"></a>

## 中文

这是一个面向 A 股量化研究的可移植因子构造与自动化系统。项目将因子想法和研究需求转化为可复现的工作流，覆盖因子构造、代码执行、数据处理、初步回测、独立审查、结果归档和持续迭代。

> 本仓库包含可移植代码、工作流定义、运行时契约、profile 和 skill。本地行情数据库、因子缓存和大型研究输出有意保留在 Git 仓库之外。

## 项目做什么

项目面向 A 股因子研究的完整生命周期：

- 将研究目标或因子想法表达为结构化设计。
- 将经济学语义从语义空间落地到可执行的算子空间和代码。
- 使用共享的 A 股因子框架和 `util/func.py` 实现基础能力。
- 基于本地数据生成因子值并执行初步回测。
- 记录产物、handoff、判定、失败原因和可复用经验。
- 在因子准入前进行独立审查。
- 对失败或不完整的候选方案自动回流并进入下一轮，而不是停留在一次代码生成。
- 通过可移植安装方式部署到其他机器，不依赖原始工作站路径。

项目目标不是只产生一个公式，而是建立一个可验证、可审计、能够持续改进的量化研究闭环。

## 总体框架

系统由三个相互协作但职责独立的角色组成：

### `default`：总控与编排

`default` 是人与系统的入口，负责接收研究需求、拆解任务、调度工作流、跟踪依赖、收集 handoff，并判断是否进入下一轮迭代或提交人工审核。

### `dvcoder`：因子实现

`dvcoder` 将因子语义转化为项目算子和可运行代码，负责因子构造、代码实现、因子值生成和初步回测，并报告数据或实现问题。`dvcoder` 不负责独立批准自己的结果。

### `evaluator`：独立审查

`evaluator` 独立检查因子语义、实现正确性、数据可用性、未来函数和时点风险、回测证据、重复因子风险以及其他审查维度，并给出通过、打回或数据阻塞等判定。

这种角色分离确保因子生成者不会为自己的工作背书。

## 完整 Hermes Harness 系统

本项目不是一组孤立脚本，而是包含完整 **Hermes Harness** 的量化工作流系统：

- **Profiles**：定义 `default`、`dvcoder` 和 `evaluator` 的长期职责边界。
- **Skills**：提供共享因子方法、实现模式、审查模板和治理规则。
- **Runtime Controller**：管理事件、任务状态、状态归并、对账、发布和 handoff。
- **Policies**：定义允许的动作、资源预算、失败处理和阶段转换。
- **Schemas**：为事件、产物、语义设计、语义判定、pipeline 判定和人工审核结果提供机器可读契约。
- **SQLite Registries**：在提供本地数据库时保存因子库和失败复盘历史。
- **安装脚本**：创建运行所需目录，并以不覆盖用户现有数据为原则执行安装。

Harness 是整个系统的治理层和执行层，使研究过程具备可重复、可检查、可追踪和可移植的特征。

## 自动闭环 Loop

工作流支持自动化的持续循环：

```text
研究需求
   ↓
语义因子设计
   ↓
任务拆解与调度
   ↓
 dvcoder 实现
   ↓
因子生成与初步回测
   ↓
 evaluator 独立审查
   ↓
通过 / 打回修改 / 数据阻塞
   ↓
产物与经验归档
   ↓
需要时自动进入下一轮
```

失败或不完整的候选方案不会被静默视为成功。控制器会记录当前状态，并把结果路由到对应的下一步，使迭代过程明确、可观察、可恢复。

## 严格 Schema 与可审计契约

系统强调 **strict schema**，而不是依赖自由格式约定。运行时 JSON schema 和 policy 文件为以下对象定义明确契约：

- 语义因子设计；
- 实现与算子空间 handoff；
- 产物清单；
- 事件与状态转换；
- 语义判定与 pipeline 判定；
- 失败复盘与人工审核结果；
- 允许的动作和阶段转换。

这些契约让 profile 之间的交接可以被机器检查，降低歧义。一个结果必须带有结构化证据和明确判定，仅有自然语言描述不能视为完整 handoff。

## 目录结构

```text
HERMES.md                         项目级工作流规则
profiles/                         default、dvcoder、evaluator 角色定义
skills/                           共享因子方法与审查方法
runtime/
  controller/                     事件存储、状态归并、对账、发布
  policies/                       动作、预算、失败、阶段策略
  schemas/                        严格 JSON 契约
  validator/                      handoff 与 schema 校验工具
  tests/                          runtime 与 validator 测试
project/util/func.py              共享的可移植工具实现
config/                           profile 与 provider 配置模板
databases/                        可选的小型工作流登记库
install.sh                        增量安装脚本
verify_install.sh                 安装与完整性验证脚本
```

大型 A 股行情数据库、因子缓存和生成式研究结果不属于本仓库，应该根据安装环境在本地提供。

## 安装

### 1. 克隆仓库

```bash
git clone https://github.com/<YOUR_GITHUB_USERNAME>/<YOUR_REPOSITORY>.git
cd <YOUR_REPOSITORY>
```

### 2. 安装可移植系统

安装脚本会创建所需目录，并尽量保留用户已有数据和配置，不覆盖已有文件：

```bash
PROJECT_ROOT="$HOME/a-share-quant" \
HERMES_HOME="$HOME/.hermes" \
bash ./install.sh
```

也可以使用自定义安装目录：

```bash
PROJECT_ROOT="$HOME/my-a-share-project" \
HERMES_HOME="$HOME/.hermes" \
bash ./install.sh
```

### 3. 验证安装

使用安装时相同的路径执行：

```bash
PROJECT_ROOT="$HOME/a-share-quant" \
HERMES_HOME="$HOME/.hermes" \
bash ./verify_install.sh
```

成功时最后会显示：

```text
VERIFY_OK
```

验证内容包括项目路径、`util/func.py` 的编译与导入、存在时的 SQLite 完整性、JSON schema 与 policy，以及三个 profile 配置。

### 4. 配置 Provider

实际 API key 只能保存在本地 `.env`，不要提交到 GitHub：

```bash
$EDITOR "$HOME/.hermes/.env"
```

数据库路径、API key 和机器相关配置都应留在本地。

### 5. 启动 Harness

只启动一个由 `default` 所有的 Gateway：

```bash
hermes --profile default gateway
```

`dvcoder` 和 `evaluator` 是由 default dispatcher 启动的 worker profile，不应各自运行独立 Gateway 或 watchdog。

## 开发与验证

修改代码后执行：

```bash
PROJECT_ROOT="$HOME/a-share-quant" \
HERMES_HOME="$HOME/.hermes" \
bash ./verify_install.sh
```

如果本地 Python 测试环境可用，可以执行：

```bash
python -m pytest runtime/tests
```

## 数据与安全边界

- 不要提交 API key、access token、密码、私钥或其他凭据。
- 不要提交本地行情数据库、大型因子缓存和大型回测输出。
- 除非完成数据边界审查，否则保持 GitHub 仓库为 Private。
- 每次推送前检查 `git status` 和 `git diff --cached`。

---

<a id="english"></a>

## English

This is a portable A-share quantitative factor research and automation system. It turns factor ideas and research requirements into a reproducible workflow covering factor construction, code execution, data processing, preliminary backtesting, independent evaluation, archival, and continuous iteration.

> This repository contains the portable code, workflow definitions, runtime contracts, profiles, and skills. Local market databases, factor caches, and large research outputs are intentionally kept outside the Git repository.

## What this project does

The project supports the complete lifecycle of A-share factor research:

- Express a research objective or factor idea as a structured design.
- Translate economic semantics from semantic space into executable operators and code.
- Reuse the shared A-share factor framework and `util/func.py` implementation.
- Generate factor values from local data and run preliminary backtests.
- Record artifacts, handoffs, verdicts, failure reasons, and reusable lessons.
- Apply independent review before a factor is accepted.
- Automatically route failed or incomplete candidates into the next iteration instead of stopping after one code-generation attempt.
- Deploy to another machine through a portable installation path without depending on the original workstation path.

The goal is not merely to produce a formula. The goal is a verifiable, auditable, and continuously improving quantitative research loop.

## Overall architecture

The system is organized around three cooperating but independent roles:

### `default`: controller and orchestrator

`default` is the human-facing entry point. It receives research requests, decomposes tasks, dispatches the workflow, tracks dependencies, collects handoffs, and decides whether to continue to another iteration or request human approval.

### `dvcoder`: factor implementation

`dvcoder` translates factor semantics into project operators and runnable code. It handles factor construction, implementation, factor generation, and preliminary backtesting, and reports data or implementation problems. `dvcoder` does not independently approve its own work.

### `evaluator`: independent review

`evaluator` independently checks factor semantics, implementation correctness, data availability, look-ahead and timing risks, backtest evidence, duplication risk, and the other required review dimensions. It issues pass, return-for-revision, or data-blocked decisions.

This separation prevents the factor generator from serving as its own reviewer.

## Complete Hermes Harness system

This repository is more than a collection of scripts. It includes a complete **Hermes Harness** around the quantitative workflow:

- **Profiles** define durable role boundaries for `default`, `dvcoder`, and `evaluator`.
- **Skills** provide shared factor methodology, implementation patterns, review templates, and governance rules.
- **Runtime Controller** manages events, task state, reduction, reconciliation, publishing, and handoffs.
- **Policies** define permitted actions, resource budgets, failure handling, and phase transitions.
- **Schemas** provide machine-readable contracts for events, artifacts, semantic designs, semantic verdicts, pipeline verdicts, and human review results.
- **SQLite Registries** preserve factor-library and failure-review history when local databases are supplied.
- **Installation scripts** create required directories and install files additively without overwriting existing user data.

The Harness is the governance and execution layer that makes the research process repeatable, inspectable, traceable, and portable.

## Automatic closed loop

The workflow supports an automatic continuous loop:

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

Failed or incomplete candidates are not silently treated as successful. The controller records their state and routes each result to the appropriate next step, making iteration explicit, observable, and recoverable.

## Strict schemas and auditable contracts

The system emphasizes **strict schemas** instead of informal free-form conventions. Runtime JSON schemas and policy files define explicit contracts for:

- semantic factor designs;
- implementation and operator-space handoffs;
- artifact manifests;
- events and state transitions;
- semantic and pipeline verdicts;
- failure reviews and human review results;
- permitted actions and phase transitions.

These contracts make profile-to-profile handoffs machine-checkable and reduce ambiguity. A result must include structured evidence and an explicit verdict; prose alone is not considered a complete handoff.

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

The installer creates the required directories and preserves existing user data and configuration files:

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

Verification covers the project path, Python compilation/import of `util/func.py`, SQLite integrity when databases are present, JSON schemas and policies, and the three profile configurations.

### 4. Configure the provider

Store actual API keys only in local `.env` files. Never commit them to GitHub:

```bash
$EDITOR "$HOME/.hermes/.env"
```

Keep database paths, API keys, and machine-specific settings outside Git.

### 5. Start the Harness

Run exactly one Gateway process owned by the `default` profile:

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

When the local Python test environment is available:

```bash
python -m pytest runtime/tests
```

## Data and security boundary

- Do not commit API keys, access tokens, passwords, private keys, or other credentials.
- Do not commit local market databases, large factor caches, or large backtest outputs.
- Keep the GitHub repository private unless the data boundary has been reviewed.
- Check `git status` and `git diff --cached` before every push.

---

## Language switch

Use the links at the top of this README to jump directly to the Chinese or English section:

- [跳转到中文](#中文)
- [Jump to English](#english)

## License

Add a license before making this repository public. Until then, treat the repository as private and controlled by its owner.
