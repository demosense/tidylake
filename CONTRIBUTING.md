# Contributing to tidylake

Thanks for your interest in contributing.

We actively use `tidylake` in day-to-day data platform work, and we continuously extend it based on real project needs. Contributions from the community are welcome, including bug fixes, documentation improvements, plugins, demos, and feature proposals.

## Development Overview

This project uses a standard Python toolchain:
- `uv` for virtual environments and dependency management
- `Taskfile` (`task`) as the main automation entry point
- `pytest` for unit, integration, and acceptance tests
- `ruff` for linting and formatting
- `pre-commit` for local quality gates
- Material for MkDocs for documentation

In practice, most local development starts with `task ...` commands.

## Clone and Install Development Dependencies

1. Clone the repository:

```bash
git clone <repo-url>
cd tidylake
```

2. Install development dependencies:

```bash
task deps:install
```

This task:
- Creates a fresh `.venv`
- Syncs dependencies with `uv` (`--all-groups`)
- Installs `pre-commit` hooks

3. Optional: activate the environment manually:

```bash
source .venv/bin/activate
```

## Taskfile Commands

Use `task` to list all commands:

```bash
task
```

Common commands:

```bash
task deps:install
task pack:install
task lint:check
task lint:format
task docs:serve
task docs:build
task docs:build:github-pages
task test:unit
task test:integration
task test:acceptance
task test:run
task demo:pandas:local
task demo:pandas:iceberg:local
task demo:spark
task spark:start
task spark:stop
```

Notes:
- `task test:run BADGE=true` also updates `docs/img/coverage.svg`
- `task demo:spark` starts and stops Spark Connect automatically; it is used during demos and testing.

## Project Structure (High-Level)

This is the contributor-oriented shape of the repository:

- `src/`: Python package source code
- `tests/`: automated test suites
- `docs/`: documentation source for MkDocs

First-level package layout in `src/tidylake/`:

- `core/`: core framework abstractions and runtime behavior
- `cli/`: Typer-based CLI commands and entry points
- `plugins/`: built-in extension points (for example compute engine integration)
- `demo/`: runnable examples used for learning and validation
- `scaffold/`: project/template scaffolding support
- `utils/`, `visualization/`: shared helpers and visualization output

`src/` contains both the framework internals and the user-facing CLI. Because `tidylake` is designed to be user-friendly and extensible, demos, plugins, and other CLI-exposed capabilities are organized into dedicated modules.

## Testing Strategy

Testing is organized by scope:
- `tests/unit`: isolated behavior and module-level logic
- `tests/integration`: interactions between components and CLI flows
- `tests/acceptance`: end-to-end user-facing behavior

Run tests with Taskfile:

```bash
task test:unit
task test:integration
task test:acceptance
task test:run
```

A dedicated testing guide can be added later for deeper conventions, fixtures, and patterns.

## Documentation Contributions

The `docs/` directory contains project documentation written in Markdown and built with Material for MkDocs.

You can preview docs locally with:

```bash
task docs:serve
```

Build the static documentation site:

```bash
task docs:build
```

This generates the publishable site in `site/`.

For GitHub Pages-oriented builds (strict mode enabled):

```bash
task docs:build:github-pages
```

Documentation contributions are encouraged: clarify concepts, improve examples, and add missing guides.

## Closing Notes

Before implementing major changes, align with the framework proposal and design direction.

The best way to propose improvements is to build a real use case, share it, and discuss the outcome. Plugins and extensions can also be contributed as community packages.
