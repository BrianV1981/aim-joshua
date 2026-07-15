# Goal: Reincarnation → Memory-Wiki that actually works

**Owner:** Operator  
**Status:** Active acceptance bar (do not lower)  
**Updated:** 2026-07-15  

This document exists so we stop re-explaining the same requirement every session.

---

## One-sentence goal

**After a real session with Operator directives, reincarnation (pulse/handoff) must leave those directives findable in that vessel’s memory-wiki — without manual paste, without false “SUCCESS”, and without depending on a still-open chat window.**

---

## Why this exists

Reincarnation has been the Achilles heel since the Gemini CLI rug-pull. Multiple “PASS” reports measured fixtures, CONFIG loads, or daemon log lines while **Operator content never reached the wiki**.

False greens are worse than failures. The bar is **operator outcome**, not pipeline cosmetics.

---

## Non-negotiable acceptance bar (all vessels)

For **each** of: `aim-grok`, `aim-agy`, `aim-opencode`:

| Step | Requirement |
|------|-------------|
| 1. Headless install | Fresh tree (clone from GitHub `main` preferred) + `setup`/`venv` + `./aim doctor` usable |
| 2. Test session | Plant a **unique marker** and **≥3 Operator directives** in that vessel’s **native** session store |
| 3. Reincarnate / pulse | Run handoff with **exclusive `--session-id`** for that session (not “newest live agent”) |
| 4. Verify | **All** of: archive contains marker; flight recorder contains marker; **wiki `pages/`** contains marker; daemon logged real SUCCESS after non-empty content; pulse exit 0 |

**Hard fail if any of:**

- Silent `exit 0` on missing CONFIG  
- Session id becomes log basename (`chat_history`, `transcript`)  
- Empty skeleton still prints HANDOFF READY / SUCCESS  
- `--session-id` ignored (mtime steals another session)  
- “E2E PASS” without grepping **wiki pages** for the marker  

---

## Vessel-native session sources (do not cross-copy paths)

| Vessel | Session source for plant + pulse |
|--------|----------------------------------|
| **aim-grok** | `~/.grok/sessions/<urlencode(cwd)>/<uuid>/{updates,chat_history}.jsonl` |
| **aim-agy** | `~/.gemini/antigravity-cli/brain/<uuid>/.system_generated/logs/transcript.jsonl` |
| **aim-opencode** | Vessel `archive/raw/session-*.json` (bridged exports / flat message JSON) |

Shared *lessons* port. Shared *path strings* do not.

---

## Canonical commands (do not invent new gates without updating this file)

### Operator E2E harnesses (fast, hard)

```bash
# Grok
cd /home/kingb/aim-grok && AIM_VESSEL=/home/kingb/aim-grok AIM_WIKI_SKIP_LANCE=1 \
  aim-agy_os/venv/bin/python3 aim-agy_os/scripts/operator_reincarnate_wiki_e2e.py

# AGY
cd /home/kingb/aim-agy && AIM_WIKI_SKIP_LANCE=1 PYTHONPATH=aim-agy_os/.aim_core \
  python3 aim-agy_os/scripts/operator_reincarnate_wiki_e2e_agy.py

# OpenCode
cd /home/kingb/aim-opencode && PYTHONPATH=aim-agy_os/.aim_core \
  python3 aim-agy_os/scripts/operator_reincarnate_wiki_e2e_oc.py
```

Exit **0** only = PASS.

### Full fleet gate (install + session + pulse + verify)

```bash
# From aim-grok (orchestrates all three)
bash /home/kingb/aim-grok/scripts/fleet_full_reincarnate_gate.sh
# or one vessel:
AIM_VESSEL=grok|agy|opencode bash /home/kingb/aim-grok/scripts/fleet_full_reincarnate_gate.sh
```

Uses GitHub `main` by default (`AIM_LIFE_USE_LOCAL=1` only for offline debug).

---

## Definition of “flagship”

Flagship is **earned by this gate on `main`**, not by historical default.

As of 2026-07-15: aim-grok was first to merge operator-proven reincarnation memory to `main`. AGY and OpenCode follow the same bar.

---

## Out of scope (for this goal)

- Perfect LanceDB embeddings / vault keyring  
- Interactive LLM wiki scribe agents  
- Disabling Grok auto-compact forever  
- Cross-CLI chat without aim-communicate  

Those may matter later; they do **not** redefine this goal.

---

## When someone claims “reincarnation works”

Demand:

1. Unique marker string  
2. Path to wiki **page** containing it  
3. Command + exit code of the harness or fleet gate  
4. Vessel name + git SHA of `main` under test  

If they cannot produce those four, it is **not** done.

---

## Related

- Issue: aim-grok #10 / PR #11  
- AGY PR #101 · OpenCode PR #22  
- Fleet scoreboard: `aim-agy_os/planning-artifacts/FLEET_STATUS_REINCARNATE_OPERATOR_E2E.md`  
- Harness scripts under each vessel: `aim-agy_os/scripts/operator_reincarnate_wiki_e2e*.py`  
