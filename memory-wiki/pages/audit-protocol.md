# Living Audit Protocol

## Overview
J.O.S.H.U.A. operates under a strict "living audit" model (`aim-audit` skill), administered by a dedicated auditor Co-Agent (`aim-auditor`, succeeding legacy `grok-audit`) and reinforced on major milestones by Google's Elephant-Goldfish Model (`egm@0.1.0` parallel zero-history cold-reader subagents). The auditor evaluates product truth against `README.md` and `AGENTS.md`, assigns a grade on a strict matrix, and updates a single living audit document (`artifacts/AUDIT_AIM_JOSHUA.md`) in place across baseline, delta, event, and closeout passes.

## 1. The A+ Acceptance Bar
The auditor distinguishes between a passing grade (**A**) and an exceptional grade (**A+**). To attain an **A+**, an agent must demonstrate:
- **No Process Theater:** `HANDOFF.md`, `README.md`, and `joshua_os_docs/` must accurately reflect shipped code (`#131`). Agents are strictly forbidden from inflating stability or threat-model claims while underlying CI/CD or live CLI paths fail.
- **Unmocked Subprocess CLI Verification (Pass 13 -> Pass 14 Lesson):** Unit tests that mock `subprocess.run` can hide constructor keyword mismatches or missing return values in live CLI entrypoints (such as `./aim health` or `./aim clean`, `#134`). All advertised CLI verbs and Day-0 onboarding flows (`install -> fix -> promote -> uninstall`, `#135`) must be exercised via real unmocked subprocess Pytest tests (`tests/test_v1_1_3_remediation.py`) under `-W error::DeprecationWarning`.
- **Hermetic Cross-Platform Testing:** Tests must operate in disposable `tmp_path` sandboxes without mutating `$HOME` or caller git state, passing identically on both `ubuntu-latest` and `windows-latest` CI legs (`smoke-test.yml` + `gitleaks.yml`).
- **Consumer Fleet Rollout Hold Gate & 1-Hop Loop Closure:** Downstream consumer `./aim update` rollouts are held until `aim-auditor` certifies `A+` on the tagged upstream release (`Pass 14` on `v1.1.3`), and final closeout reports enforce 1-hop `aim-communicate` loop prevention (`DO NOT reply`) so tmux sessions never enter ping-pong loops.

## 2. Orchestrator Override (FREEZE)
When working in a multi-agent orchestrated environment, there are times when an agent may push a commit that accidentally breaks the CI pipeline (e.g., due to an offline environment blindspot like a missing semantic engine). 

If the orchestrating auditor steps in to manually repair the repository, they will issue a **FREEZE** order.

**Agent Protocol during a FREEZE:**
1. **Immediately Stay Idle:** The active agent must immediately cease all editing, pushing, or `aim promote` actions.
2. **Do Not Interfere:** The agent must allow the orchestrator to take over the tree, fix the tests, commit the changes, and promote them.
3. **Stand By:** The active agent must wait for the orchestrator to dispatch a new audit pass or completion report before resuming normal operations.
