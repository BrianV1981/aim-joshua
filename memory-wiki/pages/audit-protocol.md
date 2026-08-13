# Living Audit Protocol

## Overview
J.O.S.H.U.A. operates under a strict "living audit" model, administered by a dedicated auditor agent (e.g. `grok-audit`). The auditor evaluates the repository, assigns a grade based on a rigid matrix, and maintains an active state document (`AUDIT_AIM_JOSHUA.md`).

## 1. The A+ Acceptance Bar
The auditor distinguishes between a passing grade (**A**) and an exceptional grade (**A+**). To attain an **A+**, an agent must demonstrate:
- **No Process Theater:** The `HANDOFF.md` and other documentation must accurately reflect reality. Agents are strictly forbidden from inflating system stability claims (e.g., claiming the system is "incredibly robust") while underlying CI/CD tests are red.
- **100% Advertised Path Coverage:** All newly implemented features must be exercised via Pytest. 
- **Hermetic Testing:** Tests must operate in isolation and not rely on global, non-reproducible state (e.g. testing `aim vault decrypt` using a disposable, synthetic transcript rather than a live user session).
- **Green Gates Only:** Agents must never close issues or claim success if the GitHub Actions smoke test is red. An A+ is only awarded if the entire pipeline is verifiably green.

## 2. Orchestrator Override (FREEZE)
When working in a multi-agent orchestrated environment, there are times when an agent may push a commit that accidentally breaks the CI pipeline (e.g., due to an offline environment blindspot like a missing semantic engine). 

If the orchestrating auditor steps in to manually repair the repository, they will issue a **FREEZE** order.

**Agent Protocol during a FREEZE:**
1. **Immediately Stay Idle:** The active agent must immediately cease all editing, pushing, or `aim promote` actions.
2. **Do Not Interfere:** The agent must allow the orchestrator to take over the tree, fix the tests, commit the changes, and promote them.
3. **Stand By:** The active agent must wait for the orchestrator to dispatch a new audit pass or completion report before resuming normal operations.
