# AGENTS Guide for tests/
This guide defines how coding agents should design, create, and run tests in `tidylake`.
Use it together with the root `AGENTS.md`.

## 1) Testing purpose in this project
- `tidylake` is a public, agnostic library, so tests must protect both usability and architectural neutrality.
- Tests should validate behavior, not implementation trivia.
- Every feature change should verify:
  - correct user-facing CLI behavior
  - manifest/script/context workflow integrity
  - plugin-based extensibility without hardcoded framework coupling

## 2) Current test structure and what each layer owns

### `tests/unit/`
- Fast, isolated tests for pure logic and small module behavior.
- Typical targets: parser helpers, commons, plugin utility logic, scaffold helpers, CLI command functions via `CliRunner` and mocks.
- No real subprocess orchestration required unless explicitly unavoidable.

### `tests/integration/`
- Verifies interaction between modules and real runtime wiring.
- Typical targets:
  - context bootstrap and path resolution
  - demo loading and execution flow
  - CLI-level behavior across components
- Uses realistic configuration/filesystem arrangements and may execute CLI through subprocess.

### `tests/acceptance/`
- End-to-end workflows from the user point of view.
- Builds disposable workspaces and runs complete commands (`list`, `run`, `init`) to validate outcomes.
- Confirms observable artifacts and expected terminal behavior.

## 3) Shared test fixtures and patterns
- `tests/conftest.py` provides common fixtures for temp workspace, environment setup, and context singleton reset.
- Many integration modules use an `autouse` fixture that wraps `reset_context_instance`; keep this pattern for isolation.
- Acceptance fixtures build temporary project files and execute CLI with controlled environment/cache settings.
- Prefer `tmp_path`, `monkeypatch`, and deterministic local files over global machine state.

## 4) How to add tests for a new feature (required order)
1. **Map change surface first**
   - Identify which layer changed: core logic, CLI orchestration, plugin integration, or end-to-end behavior.
2. **Write/extend unit tests first**
   - Add focused tests for pure behavior and edge cases.
   - Mock boundaries rather than relying on full runtime where possible.
3. **Add integration tests second**
   - Cover wiring across modules (context/CLI/plugins/path resolution) when behavior spans components.
4. **Add acceptance tests last (when user workflow changes)**
   - Add or extend acceptance scenarios only for user-visible command flows or workflow contracts.
5. **Run the full suite before finishing**
   - A change is not complete until full repository tests pass.

## 5) Command policy for tests

Primary execution path (preferred): Taskfile commands
- `task test:unit`
- `task test:integration`
- `task test:acceptance`
- `task test:run`
- `task test:run PARALLEL=true`

Single-test development exception (allowed):
- While developing or debugging tests, running `uv run pytest ...` in isolation is allowed for fast iteration.
- Use this only as a local feedback loop while authoring tests.
- Before finishing any change, always run the complete suite via Taskfile (`task test:run`).

If a task command fails or behaves incorrectly:
- Inspect `Taskfile.yml` and troubleshoot the task definition.
- Report the flaw to the user with:
  - likely root cause
  - impacted commands
  - concrete task-level fix proposal

## 6) Scope selection rules
- Choose the smallest test scope that proves behavior.
- Add unit tests for deterministic logic changes even if integration tests exist.
- Add integration tests when contract boundaries are crossed (CLI <-> core, core <-> plugins, config/path behavior).
- Add acceptance tests when end-user flows, output artifacts, or command UX are affected.
- Avoid overusing acceptance tests for logic that is already proven at lower layers.

## 7) Test quality standards
- Keep tests deterministic and environment-independent.
- Use explicit, behavior-driven test names (`test_<behavior>`).
- Assert meaningful outcomes (state, files, output), not incidental internals.
- Keep fixtures reusable and local; avoid hidden global state.
- When touching context singleton behavior, ensure reset/isolation is present.

## 8) Minimum verification before handoff
- For small/internal changes:
  - run relevant unit tests during development
  - run `task test:unit`
- For CLI/core/plugin or multi-module changes:
  - run `task test:unit`
  - run `task test:integration`
- For user-visible workflow changes:
  - run `task test:unit`
  - run `task test:integration`
  - run `task test:acceptance`
- For all completed changes (mandatory final gate):
  - run `task test:run`

## 9) Architecture safety checks in tests
- Ensure new tests reinforce agnostic behavior (no hidden dependency on one framework in shared core tests).
- Verify plugin contracts instead of hardcoding framework-specific assumptions in `core` tests.
- Prefer adapter-focused tests for platform specifics, keeping domain tests generic.
