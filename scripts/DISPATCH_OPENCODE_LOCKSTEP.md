# DISPATCH: aim-opencode → lockstep with aim-agy / aim-grok

**From:** aim-grok orchestrator / Operator  
**To:** aim-opencode agent  
**Soul:** aim-agy (`origin/main` is source of truth for shared engine)  
**Peer:** aim-grok (vendored nested OS + Grok overlays; already closer to agy)

---

## Mission

Bring **aim-opencode** toward engine lockstep with aim-agy without destroying OpenCode-specific features.

### 1. Measure drift (do this first)

```bash
python3 /home/kingb/aim-grok/scripts/vessel_core_diff.py --report-only
# focus:
python3 /home/kingb/aim-grok/scripts/vessel_core_diff.py --pair agy,opencode --report-only
```

Save summary into `planning-artifacts/LOCKSTEP_DIFF_$(date +%Y%m%d).md` in aim-opencode.

### 2. Priority port list (host-agnostic)

From agy (nested `aim-agy_os/.aim_core/`) → opencode flat `aim_core/`:

| Priority | Item | Why |
|----------|------|-----|
| P0 | `aim_doctor.py` (+ wire `aim doctor`) | doctor currently broken without it |
| P0 | CI `PYTHONPATH` → `aim_core` (not `src/`) | CI invalid today |
| P1 | Session naming (`session_naming` / vessel+role+project+ts) | multi-vessel tmux safety (#10) |
| P1 | Reincarnation package / prefix `opencode_reincarnation_*` (#9) | parity with agy #93 / grok #3 |
| P1 | Lance FTS INVERTED index fix (agy #94 when merged) | search correctness |
| P2 | prune-remote, traceback hardening, path-root fixes as applicable | hygiene |

**Do not** delete OpenCode-only modules: `daemon.py`, `aim_crash.py`, `session_bridge.py`, `aim_opencode_update.py`, etc.

### 3. Rules

- **No parallel re-invention:** if agy already has the module, port/adapt it; do not invent a third API.
- **No blind `rsync --delete`** of entire trees (flat vs nested).
- GitOps: branch via issues; do not force-push main.
- After each port chunk: run tests you can; re-run `vessel_core_diff.py`.

### 4. Pin

Create or update `SOURCE.md` in aim-opencode:

```markdown
| Upstream | aim-agy |
| Commit   | <sha after you ported> |
| Date     | ... |
| Notes    | modules ported: ... |
```

### 5. Reply structure (one shot; no chat loop)

Write `planning-artifacts/REPLY_LOCKSTEP.md`:

1. **AGREED**
2. **DIFF SNAPSHOT** (counts from vessel_core_diff)
3. **DONE** (PRs / commits / issues closed)
4. **STILL DRIFT** (top 10 modules)
5. **QUESTIONS** (only if blocked)

---

## Sibling tickets

- aim-opencode #9 reincarnation prefix, #10 agent session namespace  
- aim-agy #93/#95 (and #92/#94 when relevant)  
- aim-grok #3 merged (naming contract reference)

— Operator / aim-grok
