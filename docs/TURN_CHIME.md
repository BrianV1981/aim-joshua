# Turn-done alert (agent finished responding)

Operator cue when an agent **ends a turn** so you can look back without staring at every pane.

**Primary:** desktop / on-screen notification  
**Optional:** short sound (and terminal BEL if audio is unavailable)

## What fires it

| Vessel | Event | Wiring |
|--------|--------|--------|
| **Grok** | `Stop` / `StopFailure` | `~/.grok/hooks/aim-turn-chime.json` (+ project `.grok/hooks/`) |
| **OpenCode** | `session.idle` | `aim-hooks.ts` shells out to `aim_turn_chime.sh` |
| **AGY** | `AfterAgent` | `~/.gemini/settings.json` → `aim_turn_chime.sh after_agent` |
| **Codex** | deferred | same host script; host adapter TBD |

## Install (this host)

```bash
mkdir -p ~/.aim/bin ~/.aim/sounds
cp aim-agy_os/scripts/aim_turn_chime.sh ~/.aim/bin/
cp aim-agy_os/assets/sounds/turn_done.wav ~/.aim/sounds/   # optional audio
chmod +x ~/.aim/bin/aim_turn_chime.sh
cp .grok/hooks/aim-turn-chime.json ~/.grok/hooks/
```

**Grok:** restart the TUI (or `/hooks` to confirm `Stop` is loaded). Project hooks need `/hooks-trust` once.

### Real desktop notifications (recommended)

This machine needs a FreeDesktop notification stack:

```bash
sudo apt install libnotify-bin dunst   # or your DE’s notifier
# start dunst once per graphical session if not auto-started:
dunst &
```

Without that, the script falls back to:

1. `xmessage` popup (if `DISPLAY` is set)
2. `tmux display-message`
3. terminal BEL (when sound is on and no audio backend worked)

## Operator controls

| Env | Effect |
|-----|--------|
| `AIM_TURN_CHIME=0` | disable **everything** |
| `AIM_TURN_NOTIFY=0` | desktop/popup only off (default **on**) |
| `AIM_TURN_SOUND=0` | audio only off (default **on**) |
| `AIM_TURN_NOTIFY_CMD='…'` | custom notify command |
| `AIM_TURN_NOTIFY_EXPIRE_MS=5000` | notify-send / popup lifetime |
| `AIM_TURN_CHIME_CMD='…'` | custom play command |
| `AIM_TURN_CHIME_SOUND=/path/to.wav` | custom sound file |
| `AIM_TURN_CHIME_DEBOUNCE_MS=1500` | min gap between alerts |
| `AIM_TURN_CHIME_FORCE=1` | ignore debounce (tests) |
| `AIM_TURN_CHIME_BELL=1` | always ring terminal BEL too |
| `AIM_TURN_CHIME_DEBUG=1` | append `~/.aim/state/turn_chime.log` |
| `AIM_TURN_VESSEL=name` | force title vessel name |

**Notify only (no sound):**

```bash
export AIM_TURN_SOUND=0
```

**Sound only (no popup):**

```bash
export AIM_TURN_NOTIFY=0
```

## Test

```bash
AIM_TURN_CHIME_FORCE=1 AIM_TURN_CHIME_DEBUG=1 \
  bash aim-agy_os/scripts/aim_turn_chime.sh manual_test
# or after install:
AIM_TURN_CHIME_FORCE=1 bash ~/.aim/bin/aim_turn_chime.sh test
```

## Non-goals

- Alert on every tool call (too noisy)
- Subagent stop by default (enable later if wanted)
- Making alerts part of reincarnate PASS gates
