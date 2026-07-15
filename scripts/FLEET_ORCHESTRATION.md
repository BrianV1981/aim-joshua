# Fleet Orchestration Playbook

**Audience:** The next reincarnated **orchestrator** agent (usually on aim-grok / a `grok_reincarnate_*` session) and any Operator who needs to run multi-vessel work without thrashing.

**Related docs (do not reinvent):**

| Doc | Purpose |
|-----|---------|
| `scripts/VESSEL_LOCKSTEP.md` | What stays identical vs overlay across vessels |
| `SYNC_FROM_AIM_AGY.md` | Safe rsync denylist + pin ritual (agy → grok) |
| `.grok/skills/aim-communicate/SKILL.md` | Tmux paste protocol, FROM/REPLY_TO, submit keys |
| `SOURCE.md` (each vessel) | Soul pin SHA for that checkout |
| `scripts/vessel_core_diff.py` | Empirical drift report |

**Worked example (2026-07-13):** Close #57+#5, implement #53 HITL promote lock on soul, audit, merge, pin-sync grok + opencode. Soul tip: `8f25fe6`.

---

## 1. The three-exoskeleton model

```text
┌─────────────────────────────────────────────────────────────┐
│  Operator (human)                                           │
│    intent, approvals, "yes" on HITL, product direction      │
└───────────────────────────┬─────────────────────────────────┘
                            │
              ┌─────────────▼──────────────┐
              │  ORCHESTRATOR (usually     │
              │  aim-grok / reincarnation) │
              │  triage · dispatch · audit │
              │  pin-sync · report         │
              └──────┬──────────┬──────────┘
                     │          │
         ┌───────────▼──┐   ┌───▼──────────────┐
         │  SOUL        │   │  PEER (optional) │
         │  aim-agy     │   │  aim-opencode    │
         │  host-agnostic│  │  OpenCode host   │
         │  engine first │  │  port / wake     │
         └──────────────┘   └──────────────────┘
```

| Role | Typical session | Repo | Does |
|------|-----------------|------|------|
| **Orchestrator** | `aim-grok`, `grok_reincarnate_*`, sometimes `grok-audit` | `/home/kingb/aim-grok` | Triage, write dispatches, audit, pin-sync, Operator interface |
| **Soul** | `aim-agy` | `/home/kingb/aim-agy` | Host-agnostic engine fixes, GitHub issues on BrianV1981/aim-agy, merge to soul main |
| **Peer host** | `aim-opencode` | `/home/kingb/aim-opencode` | OpenCode-specific ports; same soul modules when possible |

**Rule of one implementer:** Never open parallel “same feature” PRs on two vessels. Implement **once on soul**, then **port/sync**.

**Rule of one orchestrator reply target:** Every inter-agent paste must declare exact tmux `FROM` and `REPLY_TO`. Project nickname ≠ session name.

---

## 2. How alignment is actually maintained

Alignment is **not** “all three trees are byte-identical.” It is four layers:

### 2a. Soul pin (`SOURCE.md`)

Each vessel records the aim-agy commit it claims to track:

| Field | Meaning |
|-------|---------|
| Commit / Short | aim-agy `main` SHA after intentional sync |
| Previous | Last pin (for rollback narrative) |
| Note | What was synced, what was *surgical*, what overlays were preserved |

**After every intentional soul merge that matters to the fleet, bump pins on grok + opencode** (even if the port was surgical, not full rsync).

### 2b. Overlay boundary

Host-agnostic code lives on **aim-agy** first. Vessel-specific files must not be clobbered:

- **Grok overlays** (examples): `vessel_paths.py`, `wiki_compiler.py`, Grok patches in pulse/extract/porter/recover, root `AGENTS.md` / skills under `.grok/`
- **OpenCode overlays** (examples): `daemon.py`, `aim_crash.py`, `session_bridge.py`, OpenCode spawn paths

See denylist in `SYNC_FROM_AIM_AGY.md` and `KNOWN_OVERLAYS` in `vessel_core_diff.py`.

### 2c. Empirical drift check

```bash
cd /home/kingb/aim-grok
python3 scripts/vessel_core_diff.py --report-only
# pair focus:
python3 scripts/vessel_core_diff.py --pair agy,grok --report-only
python3 scripts/vessel_core_diff.py --pair agy,opencode --report-only
```

Expect **differ** on known overlays. Unexpected differ on `aim_cli.py` / `lance_backend.py` / etc. after a soul merge = port debt.

### 2d. Behavioral lockstep (the real acceptance)

For a shared feature (e.g. HITL promote):

1. Soul has the behavior on `main`.
2. Grok and OpenCode either rsync safely **or** receive a **surgical port** of the same hunks.
3. Abort-path (or unit) test passes on each vessel.
4. `./aim doctor` (or equivalent) green on each vessel.

---

## 3. Orchestrator loop (the recipe)

Use this whenever work spans vessels or needs soul GitOps.

```text
1. TRIAGE     → Is this host-agnostic? Done already? Priority?
2. DISPATCH   → Chalkboard file + short tmux paste (FROM/REPLY_TO)
3. WAIT       → Peer works; you do not thrash the pane
4. AUDIT      → Independent re-verify (do not trust report alone)
5. MERGE      → Explicit authorization paste; HITL yes only if Operator intent
6. PIN-SYNC   → Orchestrator ports to other vessels + SOURCE.md
7. ACK        → Short paste to soul: pin-sync done; standby
```

### Phase 1 — Triage (orchestrator only)

- Read issue bodies (`gh issue view N`).
- Check **code reality** vs ticket prose (tickets often describe work as if already shipped).
- Classify: **close as done** | **implement on soul** | **backlog** | **vessel-only**.
- Prefer Engram / `./aim search` / wiki before inventing project facts.

### Phase 2 — Dispatch (orchestrator → soul)

1. Discover **your** session (never guess):

```bash
tmux display-message -p '#{session_name}'
tmux list-panes -a -F '#{session_name} #{pane_current_command} #{pane_current_path}'
tmux capture-pane -t aim-agy -p -J -S -20   # idle?
```

2. Write a **chalkboard** under soul planning artifacts, e.g.:

`/home/kingb/aim-agy/aim-agy_os/planning-artifacts/DISPATCH_FROM_GROK_<topic>.md`

**Mandatory headers in every dispatch:**

```markdown
**FROM (sender tmux session):** `grok_reincarnate_…`
**REPLY_TO (mandatory reply session):** `grok_reincarnate_…`   # almost always = FROM
**Also notify (optional secondary):** none
```

**Dispatch body should include:**

- Operator intent (close / implement / do not merge until audit)
- Why / evidence for closes
- Exact acceptance criteria for code
- Out of scope (other tickets, force-push, reinstall vessels)
- Report path the peer must write
- Exact short-paste template for REPORT and MERGED phases

3. Short-paste with helper (recommended):

```bash
FROM=$(tmux display-message -p '#{session_name}')
bash /home/kingb/aim-grok/.grok/skills/aim-communicate/scripts/tmux_send.sh \
  --target aim-agy \
  --from "$FROM" \
  --reply-to "$FROM" \
  --message "DISPATCH: <one line>. Full orders: /home/kingb/aim-agy/aim-agy_os/planning-artifacts/DISPATCH_….md"
```

**Submit keys by vessel** (wrong key = silent failure):

| `pane_current_command` | Vessel | Submit |
|------------------------|--------|--------|
| `grok` | Grok TUI | **Enter only** (never Esc first) |
| `opencode` | OpenCode | **Enter only** |
| `agy` | Antigravity | **Escape, then Enter** (separate events) |

4. Verify delivery: `tmux capture-pane -t aim-agy -p -J -S -30` shows a **submitted** turn (`Working…` / tool use), not stuck composer text.

### Phase 3 — Wait without thrashing

- Prefer a lightweight monitor (issue state + report file existence) over spamming the peer pane.
- Do **not** paste status checks every minute; soul context is expensive.
- Parallel prep: re-read sync docs, dry-run rsync, draft audit checklist.

### Phase 4 — Audit (orchestrator, independent)

When peer reports ready:

1. Read their report file.
2. Re-check GitHub issue states.
3. Inspect **branch/worktree** and `git diff main...fix/issue-N`.
4. Re-run critical tests yourself (e.g. `echo no | aim promote` on the worktree).
5. Confirm gates sit **before** destructive git ops, not after.

**PASS →** write `AUDIT_PASS_….md` + short paste **MERGE AUTHORIZED**.  
**FAIL →** write gaps + short paste **AUDIT FAIL — do not merge**.

Never merge on peer self-report alone.

### Phase 5 — Merge authorization

- Operator “if it passes, merge” **is** authorization for that ticket.
- Soul may use `aim promote` which now has **HITL stdin**. Streaming `yes` is allowed **only** when Operator/orchestrator already authorized this specific audited merge — not for YOLO deploys.
- Require final report: main SHA + closed issue + short paste:

```text
[FROM:aim-agy] [REPLY_TO:<orchestrator>] [REPORT from aim-agy] MERGED #N — main=<sha> — read <REPORT.md>
```

### Phase 6 — Pin-sync (orchestrator owns this)

**Do not** ask soul to edit aim-grok or aim-opencode unless Operator scopes that.

#### Prefer surgical port when overlays diverge

Full `rsync --delete` of `aim-agy_os/` often shows drift on `aim_cli.py` and pulse modules because **Grok already carries intentional overlays**. Blind rsync loses them.

**Surgical path (used for #53):**

1. Extract the soul hunks (or re-apply the same `input()` gates by hand).
2. Patch grok `aim-agy_os/.aim_core/<module>.py`.
3. Patch opencode nested `aim-agy_os/.aim_core/<module>.py` (canonical layout).
4. Mirror AGENTS rule text if the change is GitOps/behavior for agents.
5. Bump **both** `SOURCE.md` pins to soul SHA + note “surgical port of #N”.
6. Verify behavior + `./aim doctor` on each vessel.
7. Optional: `vessel_core_diff.py --report-only` and note remaining expected overlay differ.

#### Full rsync path (when pin is far behind and you accept re-applying overlays)

Follow `SYNC_FROM_AIM_AGY.md`: dry-run → real rsync with excludes → re-check overlays → doctor → bump pin.

OpenCode: **never** full-tree delete-rsync; port by module per `VESSEL_LOCKSTEP.md`.

### Phase 7 — ACK and stop

Short paste to soul: pin-sync done, pins, doctors, **standby**.  
Inquiry from Operator about old pastes → acknowledge and **stop** (no re-open of finished work).

---

## 4. Communication contract (non-negotiable)

### Envelope

```text
[FROM:<exact_tmux_session>] [REPLY_TO:<exact_reply_session>] [REPORT|DISPATCH from <role>] <one line> — read /abs/path.md
```

### Anti-patterns (production incidents)

| Failure | Fix |
|---------|-----|
| Report went to `aim-grok` while orchestrator is `grok-audit` / reincarnation | Always use **REPLY_TO from dispatch**, not habit |
| Paste stuck in Grok composer | Enter only; never Esc→Enter on Grok |
| Long novels in tmux send-keys | Chalkboard file + one-line pointer |
| Open-ended multi-agent chat | AGREED / DISAGREE / QUESTIONS / NEXT only |
| Parallel feature PRs on two vessels | Soul first, then port |

### Session map (re-check live)

```bash
tmux list-sessions
tmux list-panes -a -F '#{session_name} #{pane_current_command} #{pane_current_path}'
```

Typical:

| Session | CLI | Cwd |
|---------|-----|-----|
| `aim-agy` | `agy` | `/home/kingb/aim-agy` |
| `aim-grok` | `grok` | `/home/kingb/aim-grok` |
| `grok_reincarnate_*` | `grok` | aim-grok (fresh vessel) |
| `aim-opencode` | `opencode` | `/home/kingb/aim-opencode` |
| `grok-audit` | `grok` | `/home/kingb/grok-audit` (often historical orchestrator) |

---

## 5. Decision tree: who does the work?

```text
Is the change host-agnostic engine / CLI / memory / GitOps?
  YES → aim-agy implements on worktree; orchestrator audits + pin-syncs
  NO  → vessel-local only (skills, SOURCE, vessel_paths, OpenCode wake)

Is the ticket already true in code/product?
  YES → close with factual comment (orchestrator can close OR dispatch soul to close)
  NO  → implement

Is full rsync safe?
  Overlays would be clobbered? → surgical port
  Clean pin lag on shared modules only? → rsync with denylist

Do we need the third agent (opencode) in the chat loop?
  Pure engine port after soul merge → orchestrator ports files; optional ACK only
  OpenCode-specific behavior / wake path → dispatch aim-opencode with chalkboard
```

**Speed tip:** For pure engine features after soul merge, **orchestrator pin-syncs both vessels** without a third chat loop. Use aim-opencode agent only when judgment on OpenCode harness is required.

---

## 6. Chalkboard templates

### 6a. Dispatch (orchestrator → soul)

Path: `aim-agy/aim-agy_os/planning-artifacts/DISPATCH_FROM_GROK_<TOPIC>.md`

```markdown
# DISPATCH: <title>

**FROM (sender tmux session):** `<orchestrator_session>`
**REPLY_TO (mandatory reply session):** `<orchestrator_session>`
**Also notify:** none

## Operator intent
1. …
2. Do NOT merge until orchestrator audits.

## Phase A — board hygiene (if any)
Close #N because: <evidence>

## Phase B — implement
Acceptance criteria:
- …
Out of scope: …

## Phase C — report for audit
Write: `…/REPORT_TO_GROK_<N>.md`
Short paste template: …
```

### 6b. Audit pass / merge orders

```markdown
# AUDIT PASS — #<N>
**Result:** PASS — merge authorized
## Independent checks
| Check | Result |
## MERGE ORDERS
1. Merge fix/issue-N → main (promote HITL: yes allowed for this audited merge)
2. Close issue if needed
3. Report main SHA to REPLY_TO
```

### 6c. Peer report structure

```markdown
# REPORT: Issue #N
1. Board hygiene
2. Branch + worktree
3. Diff summary
4. Verification method
5. Residual risk / questions
6. MERGED (append only after merge) — main=<sha>
```

---

## 7. Worked example: #53 HITL lock (2026-07-13)

| Step | Who | What |
|------|-----|------|
| Triage | Orchestrator (grok reincarnation) | #57 done (aim-connect product); #5 done (mkdir in install); #53 body claimed HITL but `cmd_promote` had no gate |
| Dispatch | → `aim-agy` | Close 57+5; implement 53; no merge until audit |
| Implement | Soul | Worktree `fix/issue-53`; gates on promote + merge-batch; AGENTS Rule 5 |
| Audit | Orchestrator | Re-ran abort path; structure OK |
| Merge | Soul | `echo yes \| promote` under authorization → main `8f25fe6` |
| Pin-sync | Orchestrator | Surgical port into grok + opencode `aim_cli.py` + AGENTS + SOURCE; **not** full rsync |
| ACK | → Soul | Pins 8f25fe6; doctors green; standby |

**Lesson:** Ticket text can lie; **diff and abort tests** decide. Overlay-aware pin-sync is part of orchestration, not optional cleanup.

---

## 8. Operator friction and how to reduce it

Three live agents are powerful but slow if every byte goes through chat.

| Pattern | Cost | Prefer when |
|---------|------|-------------|
| Soul implement + orchestrator pin-sync | Medium | Default for engine features |
| Soul + opencode both in chat | High | OpenCode harness judgment required |
| Orchestrator implements on soul | Medium-high | Soul pane dead / Operator scopes grok to edit aim-agy |
| Full fleet rsync every time | High + overlay risk | Rare; large pin lag with planned overlay re-apply |

**Operator approvals that unblock:**

- “Talk to aim-agy …” → permission to message that session
- “If audit passes, merge” → merge auth after **your** PASS
- “Update grok and opencode” → pin-sync without another debate

---

## 9. Wake checklist for a new orchestrator

1. Read `AGENTS.md` (this vessel) + this playbook + `VESSEL_LOCKSTEP.md`.
2. `tmux display-message -p '#{session_name}'` → lock your FROM/REPLY_TO identity.
3. `./aim doctor` green; note `SOURCE.md` pin.
4. `tmux list-sessions` + capture soul/opencode idle state.
5. `python3 scripts/vessel_core_diff.py --report-only` (baseline drift).
6. `gh issue list --repo BrianV1981/aim-agy --state open` (or local tracker).
7. Stand by for Operator product work — **do not** invent alignment churn.

---

## 10. Hard constraints (fleet GitOps)

- No force-push main; no vessel reinstalls unless Operator orders.
- Feature work off main via `aim fix <id>` / worktrees.
- Surgical staging — never blind `git add .`.
- Do not modify `/home/kingb/aim-agy` from grok unless Operator scopes it (prefer dispatching soul).
- Inquiry → answer and **stop**. Directive → execute in scope only.
- HITL promote/merge-batch: never guess `yes` without Operator/orchestrator auth for that merge.

---

## 11. Quick command card

```bash
# Who am I?
tmux display-message -p '#{session_name}'

# Who is alive?
tmux list-panes -a -F '#{session_name} #{pane_current_command} #{pane_current_path}'

# Message soul
FROM=$(tmux display-message -p '#{session_name}')
bash /home/kingb/aim-grok/.grok/skills/aim-communicate/scripts/tmux_send.sh \
  --target aim-agy --from "$FROM" --reply-to "$FROM" \
  --message "DISPATCH: … — read /abs/path.md"

# Soul health / issues
cd /home/kingb/aim-agy && gh issue list --state open
cd /home/kingb/aim-agy && git rev-parse HEAD && git log -1 --oneline

# Drift + pin
cd /home/kingb/aim-grok && python3 scripts/vessel_core_diff.py --report-only
grep -E 'Commit|Short|8f25|6191' SOURCE.md /home/kingb/aim-opencode/SOURCE.md

# Doctors
cd /home/kingb/aim-grok && ./aim doctor
cd /home/kingb/aim-opencode && python3 aim-agy_os/.aim_core/aim_cli.py doctor
```

---

*Maintained by aim-grok orchestrator practice. Update this file when a fleet ritual changes (new submit rules, layout migration, or pin-sync automation).*
