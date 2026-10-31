# CI/CD & Testing Architecture

## Overview
J.O.S.H.U.A. embraces a hardened testing and Continuous Integration (CI) pipeline that revolves around GitHub Actions and Pytest. To guarantee safe continuous delivery under the GitOps model without bleeding experimental states into the Operator's environment, tests are meticulously designed to simulate real operations dynamically.

## 1. Unit & CLI Testing (Pytest)
The `pytest` testing harness is located at the root of the repository in the `tests/` directory.

- **Wrapper Simulation:** Tests interact directly with the `./aim` CLI wrapper, asserting exit codes and output patterns (e.g. `test_cli.py` tests `--help` and `doctor`).
- **Python Module Testing:** The core Python modules (`joshua_os/.aim_core/`) such as the MCP Server (`mcp_lancedb.py`) and the vector ingestion engine (`bootstrap_brain.py`) are rigorously covered by unit tests relying on `unittest.mock` to assert correct execution paths and state management without spinning up active databases.
- **Path Considerations:** Because the `./aim` wrapper resolves the python executable by looking for `joshua_os/venv/bin/python3` (or `../../joshua_os/venv/bin/python3` inside `workspace/issue-*` worktrees), CI runners MUST execute `joshua_os/setup.sh` to construct the environment before kicking off `pytest`. Inside git worktrees where `joshua_os/venv` is gitignored, agents can execute `python3 -m pytest -q` directly.
- **Untracked File Safeguard (`git_push_changes` in `aim_cli.py`, #98):** The legacy `aim_push.sh` bash script has been superseded by pure-Python `git_push_changes()`. By default, `aim push` runs `git add -u` for surgical safety, emits a `[NOTICE]` warning on `stderr` listing any untracked files, and supports `aim push --include-untracked "msg"` (`-a`) or manual `git add <file>` prior to pushing.
- **`v1.0.0` Guardrail Assertions (`41/41` Pytest, `0` Warnings):** Beyond CLI and MCP routing, `tests/test_cli.py` and `tests/test_mcp_lancedb.py` enforce zero hardcoded host paths in engine code (`test_no_hardcoded_host_paths_in_engine_code`), zero LanceDB deprecation warnings (`test_list_lance_tables_zero_deprecation_warnings`), non-destructive `.gitignore` and `AGENTS.md` onboarding, multi-key Blackbox decryption & FTS5 `history.db` backfill, and General Availability SemVer posture (`test_semver_ga_posture`).

## 2. End-to-End (E2E) Integration Tests
J.O.S.H.U.A. automates high-risk git operations like `aim promote` through dynamic Python unit tests that mimic entire repository environments without polluting the local `.git` config or pushing to the live GitHub repository.

- **Dynamic Sandboxing:** E2E tests (like `test_promote_integration.py`) use pytest's `tmp_path` fixture to dynamically instantiate a bare "origin" git repository and a localized "clone".
- **Mocking User Input:** Critical `stdin` interventions required by Sovereign agents (such as the explicit 'yes/no' manual confirmations for promoting branches to main) are hot-patched dynamically in python (e.g., overriding `builtins.input`).

## 3. GitHub Actions & Secrets Scanning
The Continuous Integration pipeline enforces strict safety rules on every pull request or push to the main branch.
- **Smoke Tests:** The `.github/workflows/smoke-test.yml` pipeline handles Python dependency setups, CLI sanity checks, LanceDB validations, and native Pytest execution.
- **Secrets Scanning:** To prevent catastrophic access token bleed in a fully autonomous agentic system, a strict `.github/workflows/gitleaks.yml` workflow is enabled to scan the repository using `gitleaks` prior to any code integration.

## 4. Offline Environment Blindspots (CI vs Local)
When tests run in GitHub Actions, they often run in an offline or unconfigured environment relative to the developer's machine.
- **Semantic Engine Example:** If LanceDB or the embeddings engine is unconfigured in CI, the system might gracefully fallback to lexical search but print a `[NOTICE]` to standard output. 
- **JSON Parsing Failures:** Text warnings injected into stdout will catastrophically break tests asserting valid JSON payloads (`aim search ... --json`). Code must ensure such notices are strictly routed to `stderr` to maintain clean `stdout` streams for automated parsing.
- **Hermetic Testing:** Features relying on the local filesystem or operator data (like the Blackbox Vault) must be tested using hermetic, disposable fixtures (e.g. generating a temporary transcript UUID and sealing it inside `/tmp` or a mock directory) rather than depending on real active sessions.
