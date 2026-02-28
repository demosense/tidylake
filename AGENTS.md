# AGENTS Guide for tidylake
This guide is for coding agents operating in this repository.
It documents the practical command set and coding conventions inferred from repo config and source.

## 0) Product intent (read first)
- `tidylake` is a public library intended for real-world usability across mixed data teams.
- The goal is a common ground between code execution, metadata governance, and operational workflows.
- Every change must protect the project promise: organization and automation without forcing a specific stack.
- Keep developer ergonomics high: clear CLI behavior, readable APIs, actionable errors, and sensible defaults.

Design principles:
- Tool/framework agnostic by default; users keep their preferred compute/storage stack.
- Metadata and code must stay in sync (manifest + script + context model).
- Same script should work in interactive and batch contexts with safe behavior.
- The framework should organize and orchestrate, not interfere with transformation logic.

Architecture guardrails (hexagonal style):
- Treat `core` as domain/application logic and keep it independent from concrete data frameworks. That is, logic that is directly callable from the CLI commands or CLI classes.
- Treat compute engines, catalogs, storage, and platform specifics as adapters behind plugin interfaces.
- New framework/platform integrations belong behind `plugins` contracts, not hardcoded in core flows.
- CLI should orchestrate use cases; framework-specific logic should stay out of command handlers.
- Prefer dependency inversion: core defines ports/expectations, adapters implement them.
- If a change reduces agnosticism, stop and redesign before merging.

## 1) Project overview
- Language: Python 3.12+
- Package root: `src/tidylake`
- CLI entry point: `tidylake` -> `tidylake.cli:app`
- Tooling interface for agents: `task` commands from `Taskfile.yml`
- Docs stack: MkDocs Material

### Source structure (important)
The package is intentionally organized to preserve agnosticism and hexagonal boundaries.

- `src/tidylake/core/`
  - Domain/application center of the library.
  - Owns context loading, data product modeling, dependency graph construction, execution ordering, and schema orchestration use cases.
  - Must remain framework/platform agnostic: no direct pandas/spark/cloud vendor coupling in shared core flows.
  - Should depend on plugin contracts and abstractions, not concrete engine implementations.

- `src/tidylake/plugins/`
  - Adapter contracts and adapter-oriented logic for compute engines and external systems.
  - This is where framework/platform specifics belong (storage/catalog/compute integration behavior behind interfaces).
  - New integrations must be added as plugin implementations/contracts, not as branches inside `core` or CLI handlers.
  - Keep plugin interfaces explicit so core can stay stable and extensible.

- `src/tidylake/cli/`
  - Thin orchestration layer for user commands.
  - Parses options, validates command inputs, invokes core use cases, and renders user-facing output.
  - Must not embed framework-specific business logic; delegate behavior to `core` and plugin-backed services.
  - CLI is part of the public API surface: prioritize predictable UX and actionable error messages.

- `src/tidylake/demo/`
  - First-class package code, not disposable examples.
  - Demonstrates canonical usage patterns across supported stacks and validates the framework promise in realistic scenarios.
  - Demos are actively exercised in integration/end-to-end testing; broken demos indicate reduced package reliability for users.
  - Any new feature that affects user workflows should be reflected in demos so behavior is proven in practical, runnable projects.

- `src/tidylake/scaffold/`
  - Project bootstrap logic (`tidylake init`) based on demo templates.
  - Must stay aligned with demo quality and current best-practice project structure.

- `src/tidylake/utils/`
  - Focused utility helpers (for example AST/code parsing), kept small and reusable.

- `src/tidylake/visualization/`
  - Rendering helpers for lineage and dependency views (Mermaid/Textual).
  - Presentation layer only; avoid moving core orchestration logic here.

Task-only policy:
- Agents must use `task ...` commands for setup, lint, test, docs, and other operations.
- Do not instruct or rely on direct underlying commands in guidance (no raw `uv`, `pytest`, `ruff`, etc.).
- If a task command fails or behaves unexpectedly, inspect `Taskfile.yml`, identify the flaw, and report it clearly to the user.
- Include the likely root cause and a concrete task-level fix proposal when reporting the issue.

## 2) Setup commands
Preferred one-shot setup:
- `task deps:install`

What it does:
- creates the virtual environment
- syncs dependency groups
- installs pre-commit hooks

Editable package install (often useful before tests/CLI checks):
- `task pack:install`

## 3) Build, lint, and test commands

### Lint/format
Primary task commands:
- `task lint:check`
- `task lint:format`

### Tests
- All testing strategy, structure, and execution guidance lives in `tests/AGENTS.md`.
- Follow that file for test scope selection, test creation order, and command usage.

### Build commands
Documentation:
- `task docs:serve`
- `task docs:build`
- `task docs:build:github-pages`

Package artifact build:
- No package build task is currently defined in `Taskfile.yml`.
- Treat this as a Taskfile gap; if packaging is required, report the gap and propose/add a dedicated task command.

## 4) Pre-commit and quality gates
- `.pre-commit-config.yaml` runs `task lint:check` as a local hook.
- Additional hooks check merge conflicts, private keys, and AWS credentials.
- Recommended minimum before commit:
  - `task lint:check && task test:unit`

## 5) Code style guidelines
These guidelines are based on `pyproject.toml`, lint settings, and existing code patterns.

### Project-specific engineering rules
- Prioritize usability and backwards-compatible behavior for public APIs and CLI commands.
- Keep changes small and explicit; avoid hidden side effects across execution modes.
- Preserve the manifest-first workflow (`manifest` + `script` + `context`) in new features.
- Keep transformations framework-native (pandas/spark/etc.) and keep tidylake helpers lightweight.
- Prefer extensibility through plugins over adding stack-specific branches in shared code.

### Formatting and linting
- Ruff line length is 110.
- Enabled Ruff rule families: `E`, `F`, `UP`, `B`, `SIM`, `I`.
- `I` means import ordering is enforced.
- `SIM108` is globally ignored; do not add extra ignores casually.
- Keep code Ruff-clean; run lint after edits.

### Imports
- Import order: standard library, third-party, local package.
- Prefer absolute package imports (e.g., `from tidylake.core import ...`).
- Remove unused imports.
- Use deferred/local imports only when required (e.g., optional dependency or cycle break).

### Type usage
- Use Python 3.12 type syntax (`str | None`, `dict[str, Any]`, etc.).
- Add type hints on public functions/methods and key internal APIs.
- Prefer concrete containers where known (`list[str]`, `dict[str, tuple[str, ...]]`).
- Use `collections.abc` interfaces for callable/iterable protocol typing.
- Keep `Any` narrow and localized.

### Naming conventions
- modules/files/functions/variables: `snake_case`
- classes: `PascalCase`
- constants: `UPPER_SNAKE_CASE`
- test modules: `test_*.py`
- test functions: `test_<behavior>`

### Docstrings and comments
- Follow current docstring style with short summary and optional `Args`/`Returns` blocks.
- Write comments only for non-obvious intent.
- Prefer readable names and small functions over comment-heavy code.

### Error handling
- Raise specific exceptions for invalid states:
  - `FileNotFoundError` for missing files/paths
  - `ValueError` for bad values or invalid configuration
  - `ImportError` for plugin/module loading failures
- In CLI code, use `typer.BadParameter` for invalid options/args.
- Use `typer.Exit(code=1)` for controlled command failure after user-facing error output.
- Keep error messages concise and actionable.

### Testing conventions
- See `tests/AGENTS.md` for complete testing conventions and workflow.
