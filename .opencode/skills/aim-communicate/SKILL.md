---
name: aim-communicate
description: >
  Inter-agent communication via tmux with permission gates, chalkboard + short-paste
  protocol (Grok/AGY-hardened). MUST declare sender session and REPLY_TO session on every
  message. Use when messaging another AI agent in tmux, board-room/swarm chat, or when
  the user asks to talk to another agent. Updated 2026-07-12 (reply-to routing + Grok submit).
---

# AIM-Communicate: Inter-Agent Tmux Protocol

You may operate where multiple AI agents run in different tmux sessions (board room / swarm).
Common sessions: `aim-agy`, `aim-grok`, `grok-audit`, `aim-connect`, `aim-youtube`, reincarnation vessels (`agy_reincarnation_*`, `grok_reincarnation_*`), etc.

---

## 0. MANDATORY: Session identity + reply routing (do not skip)

**Every inter-agent message MUST state:**

1. **FROM** — the **exact** tmux session **you are running in now**  
2. **REPLY_TO** — the **exact** tmux session the peer must answer (almost always = the orchestrator’s FROM)  

### 0a. Discover your own session (always run first)

```bash
# Preferred (when your pane is the active one in a known session):
tmux display-message -p '#{session_name}'

# If that is empty/wrong (nested/detached), find by cwd or list:
tmux list-panes -a -F '#{session_name} #{pane_current_command} #{pane_current_path}'
```

Record that name. **Do not guess** `aim-grok` vs `grok-audit`. They are different orchestrators.

### 0b. Required short-message envelope

```text
[FROM:<your_session>] [REPLY_TO:<session_they_must_answer>] [REPORT|DISPATCH from <role>] <one-line body>
```

**Examples (correct):**

```text
[FROM:grok-audit] [REPLY_TO:agy_reincarnation_1783842559] [DISPATCH] Merge #92-95 — read /path/DISPATCH.md
[FROM:agy_reincarnation_1783842559] [REPLY_TO:grok-audit] [REPORT from aim-agy] Merged #92-#95 — read /path/REPORT.md
```

**Wrong (causes misdelivery):**

```text
[REPORT from aim-agy] Merged #92-#95 — read /path/REPORT.md
# Missing REPLY_TO → agent often picks aim-grok by habit while orchestrator is on grok-audit
```

### 0c. Dispatch files MUST include

In every chalkboard dispatch:

```markdown
**FROM (sender tmux session):** `grok-audit`
**REPLY_TO (mandatory reply session):** `grok-audit`
**Also notify (optional secondary):** `aim-grok`   # only if Operator wants a CC
```

Peer agents **must** paste reports to **REPLY_TO only** unless Operator adds a CC list.  
If both `aim-grok` and `grok-audit` are listed, **primary is always REPLY_TO**.

### 0d. Incident (2026-07-12)

Orchestrator on **`grok-audit`** ordered aim-agy to report to `grok-audit`. The agent reported only to **`aim-grok`**, so the live orchestrator did not see the paste. Fix: mandatory `[FROM:…] [REPLY_TO:…]` on every short paste + dispatch header.

---

## 1. Permission mandate

You are **forbidden** from unilaterally messaging another agent's tmux session unless the Operator explicitly approves.

- Operator text like "tell aim-agy …" / "communicate with …" **is** approval for that target and intent.
- Do not open open-ended multi-hop chat without Operator in the loop.

## 2. Discover targets first

```bash
tmux list-sessions
tmux list-panes -a -F '#{session_name} #{pane_current_command} #{pane_current_path}'
tmux capture-pane -t <session> -p -J -S -20
```

Wait for idle prompt when possible.

| `pane_current_command` | Vessel | Submit |
|------------------------|--------|--------|
| `grok` | Grok TUI | **Enter only** (§4a) |
| `opencode` | OpenCode TUI | **Enter only** (same as Grok; §4a) |
| `agy` | Antigravity | **Escape, then Enter** (§4b) |

**Note:** Project name ≠ session name. An aim-agy agent may run in `agy_reincarnation_*` or `aim-agy`. Always use the **tmux session string**, not the repo name alone.

## 3. Chalkboard + short paste

### 3a. Write full content to disk

Prefer paths under the target or sender project (`planning-artifacts/`, `docs/`).

### 3b. Helper script (recommended)

```bash
# Auto-detect FROM session; force REPLY_TO into the message prefix if missing:
bash /home/kingb/grok-audit/.grok/skills/aim-communicate/scripts/tmux_send.sh \
  --target grok-audit \
  --from "$(tmux display-message -p '#{session_name}')" \
  --reply-to grok-audit \
  --message 'Merged #92-#95 — read /home/kingb/aim-agy/aim-agy_os/planning-artifacts/REPORT_TO_GROK_MERGE_92_95.md'
```

The script prefixes `[FROM:…] [REPLY_TO:…]` when missing and uses the correct submit sequence.

Canonical script path (copy into each vessel if needed):

- `/home/kingb/grok-audit/.grok/skills/aim-communicate/scripts/tmux_send.sh`
- `/home/kingb/aim-grok/.grok/skills/aim-communicate/scripts/tmux_send.sh`
- `/home/kingb/aim-agy/.gemini/skills/aim-communicate/scripts/tmux_send.sh`

### 3c. Manual short paste

```bash
FROM=$(tmux display-message -p '#{session_name}')
REPLY_TO=grok-audit   # from the dispatch — never invent
SHORT="[FROM:${FROM}] [REPLY_TO:${REPLY_TO}] [REPORT from ${FROM}] Closed #N — read /abs/path/REPORT.md"

tmux set-buffer -b aim_comm_short "$SHORT"
tmux send-keys -t "$REPLY_TO" C-u
sleep 0.2
tmux paste-buffer -b aim_comm_short -p -t "$REPLY_TO"
sleep 0.5
# vessel-specific submit — §4
```

### 3d. Verify delivery

```bash
sleep 1.2
tmux capture-pane -t <target> -p -J -S -30 | tail -35
```

Grok success: message is a **submitted user turn**, not stuck in composer.  
AGY success: `Loading...` / tool use.  
Grok failure: text only in bottom bar → Enter did not fire.

## 4. Submit rules (vessel-specific)

### 4a. Grok (`grok`) — Enter only

```bash
tmux send-keys -t <target> Enter
# optional fallback: C-m
```

**Never** send Escape before Enter on Grok (Esc clears/cancels; does not send).

### 4b. AGY (`agy`) — Escape then Enter (separate calls)

```bash
tmux send-keys -t <target> Escape
sleep 0.3
tmux send-keys -t <target> Enter
```

### 4c. Do / Don't

| Do | Don't |
|----|--------|
| Declare FROM + REPLY_TO every time | Assume “aim-grok” is the orchestrator |
| Detect vessel before submit | One submit recipe for all CLIs |
| `paste-buffer -p` | Long `send-keys` novels |
| Capture-pane verify | Assume delivery |
| Write report file first | Rely only on paste |

## 5. Loop prevention

```text
Structure:
1. AGREED / MERGED (issue #s, SHAs)
2. DISAGREE / NOTES
3. QUESTIONS
4. NEXT
No open-ended chat loop.
```

## 6. Host map (re-check live with list-sessions)

| Session | Typical CLI | Typical cwd | Submit |
|---------|-------------|-------------|--------|
| `grok-audit` | `grok` | `/home/kingb/grok-audit` | Enter |
| `aim-grok` | `grok` | `/home/kingb/aim-grok` | Enter |
| `aim-agy` | `agy` | `/home/kingb/aim-agy` | Esc→Enter |
| `agy_reincarnation_*` | `agy` | aim-agy worktrees | Esc→Enter |
| `aim-connect` | `agy` | `/home/kingb/aim-connect` | Esc→Enter |
| `aim-opencode` | `opencode` | `/home/kingb/aim-opencode` | Enter only |

**Orchestrator on this host often lives in `grok-audit`, not `aim-grok`.** Read REPLY_TO from the dispatch.

OpenCode vessel skill (extra notes):  
`/home/kingb/aim-opencode/.opencode/skills/aim-communicate/SKILL.md`

## 7. Anti-patterns

- Reporting to `aim-grok` when REPLY_TO was `grok-audit`  
- Omitting FROM/REPLY_TO  
- Using project nickname (`aim-agy`) as session name when you are actually `agy_reincarnation_*`  
- AGY Escape→Enter on Grok  
- Secrets in pastes  
- Force-push / destructive ops without Operator  

## 8. Incident log

1. **2026-07-12 Grok submit:** Escape→Enter left pastes unsent on Grok. Fix: Enter only.  
2. **2026-07-12 Wrong reply session:** aim-agy reported merge of #92–#95 to `aim-grok` instead of orchestrator `grok-audit`. Fix: mandatory FROM + REPLY_TO (§0).
