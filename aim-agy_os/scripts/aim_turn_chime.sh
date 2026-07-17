#!/usr/bin/env bash
# aim_turn_chime.sh — Operator alert when an agent turn ends.
#
# Primary: desktop / on-screen notification
# Optional: short sound (+ terminal BEL fallback)
#
# Wired by:
#   - Grok: Stop / StopFailure hooks (~/.grok/hooks/aim-turn-chime.json)
#   - OpenCode: session.idle in aim-hooks plugin
#   - AGY: AfterAgent in ~/.gemini/settings.json
#   - Manual: aim_turn_chime.sh [reason]
#
# Env (kill switch + toggles):
#   AIM_TURN_CHIME=0          disable everything
#   AIM_TURN_NOTIFY=0         disable desktop/popup notify (default on)
#   AIM_TURN_SOUND=0          disable audio (default on)
#   AIM_TURN_CHIME_CMD=...    full custom play command (overrides sound backends)
#   AIM_TURN_CHIME_SOUND=path custom wav/oga
#   AIM_TURN_NOTIFY_CMD=...   full custom notify command (overrides notify backends)
#   AIM_TURN_NOTIFY_EXPIRE_MS expire time for notify-send (default 5000)
#   AIM_TURN_CHIME_DEBOUNCE_MS=1500  min gap between alerts
#   AIM_TURN_CHIME_FORCE=1    ignore debounce
#   AIM_TURN_CHIME_BELL=1     always ring terminal BEL too
#   AIM_TURN_CHIME_DEBUG=1    append ~/.aim/state/turn_chime.log
#   AIM_TURN_VESSEL / AIM_VESSEL / TMUX session used for title when set
#
# Always exits 0 (never blocks agent hooks). Drains stdin if present.
set -u

# Drain hook JSON on stdin so Grok/Claude stop-hooks never block on a full pipe.
if [ ! -t 0 ]; then
  cat >/dev/null 2>&1 || true
fi

enabled="${AIM_TURN_CHIME:-1}"
case "${enabled,,}" in
  0|false|no|off|disabled) exit 0 ;;
esac

REASON="${1:-turn_end}"
HOME_DIR="${HOME:-/home/kingb}"
STATE_DIR="${AIM_STATE_DIR:-$HOME_DIR/.aim/state}"
SOUND_DEFAULTS=(
  "${AIM_TURN_CHIME_SOUND:-}"
  "$HOME_DIR/.aim/sounds/turn_done.wav"
  "$(cd "$(dirname "${BASH_SOURCE[0]}")/.." 2>/dev/null && pwd)/assets/sounds/turn_done.wav"
  "/usr/share/sounds/freedesktop/stereo/message.oga"
  "/usr/share/sounds/freedesktop/stereo/complete.oga"
  "/usr/share/sounds/freedesktop/stereo/dialog-information.oga"
)

mkdir -p "$STATE_DIR" 2>/dev/null || true
STAMP_FILE="$STATE_DIR/turn_chime_last_ms"
DEBOUNCE_MS="${AIM_TURN_CHIME_DEBOUNCE_MS:-1500}"

now_ms() {
  if command -v python3 >/dev/null 2>&1; then
    python3 -c 'import time; print(int(time.time()*1000))' 2>/dev/null && return
  fi
  echo $(( $(date +%s) * 1000 ))
}

now="$(now_ms)"
# Debounce (shared stamp — multi-pane agents won't machine-gun alerts)
if [ "${AIM_TURN_CHIME_FORCE:-0}" != "1" ]; then
  last=0
  if [ -f "$STAMP_FILE" ]; then
    last="$(tr -cd '0-9' <"$STAMP_FILE" 2>/dev/null || echo 0)"
  fi
  if [ -n "${last:-}" ] && [ "$last" -eq "$last" ] 2>/dev/null; then
    delta=$(( now - last ))
    if [ "$delta" -ge 0 ] && [ "$delta" -lt "$DEBOUNCE_MS" ]; then
      exit 0
    fi
  fi
fi
echo "$now" >"$STAMP_FILE" 2>/dev/null || true

# ── Who finished? ─────────────────────────────────────────────
vessel="${AIM_TURN_VESSEL:-${AIM_VESSEL_NAME:-}}"
if [ -z "$vessel" ] && [ -n "${AIM_VESSEL:-}" ]; then
  vessel="$(basename "${AIM_VESSEL}" 2>/dev/null || true)"
fi
if [ -z "$vessel" ] && [ -n "${TMUX:-}" ] && command -v tmux >/dev/null 2>&1; then
  vessel="$(tmux display-message -p '#S' 2>/dev/null || true)"
fi
if [ -z "$vessel" ]; then
  vessel="agent"
fi

title="A.I.M. · ${vessel}"
body="Turn done (${REASON})"
case "$REASON" in
  stop|Stop) body="Finished responding" ;;
  stop_failure|StopFailure) body="Turn ended with an error" ;;
  session_idle) body="Session idle — ready for you" ;;
  after_agent) body="Agent finished this turn" ;;
  *) body="Turn done (${REASON})" ;;
esac

notify_on="${AIM_TURN_NOTIFY:-1}"
sound_on="${AIM_TURN_SOUND:-1}"
case "${notify_on,,}" in 0|false|no|off|disabled) notify_on=0 ;; *) notify_on=1 ;; esac
case "${sound_on,,}" in 0|false|no|off|disabled) sound_on=0 ;; *) sound_on=1 ;; esac

notify_ok=0
play_ok=0

# ── Desktop / on-screen notification ──────────────────────────
if [ "$notify_on" = "1" ]; then
  expire_ms="${AIM_TURN_NOTIFY_EXPIRE_MS:-5000}"
  if [ -n "${AIM_TURN_NOTIFY_CMD:-}" ]; then
    # shellcheck disable=SC2086
    if eval $AIM_TURN_NOTIFY_CMD >/dev/null 2>&1; then
      notify_ok=1
    fi
  fi

  # 1) libnotify (preferred — needs notification daemon: dunst, gnome, etc.)
  if [ "$notify_ok" -ne 1 ] && command -v notify-send >/dev/null 2>&1; then
    if notify-send \
      -a "A.I.M." \
      -u normal \
      -t "$expire_ms" \
      -h "string:desktop-entry:aim" \
      -- "$title" "$body" >/dev/null 2>&1; then
      notify_ok=1
    fi
  fi

  # 2) FreeDesktop Notifications over session bus (python-dbus)
  if [ "$notify_ok" -ne 1 ] && command -v python3 >/dev/null 2>&1; then
    if python3 - "$title" "$body" "$expire_ms" <<'PY' >/dev/null 2>&1
import sys
try:
    import dbus
except Exception:
    sys.exit(1)
title, body, expire = sys.argv[1], sys.argv[2], int(sys.argv[3])
try:
    bus = dbus.SessionBus()
    proxy = bus.get_object(
        "org.freedesktop.Notifications",
        "/org/freedesktop/Notifications",
    )
    iface = dbus.Interface(proxy, "org.freedesktop.Notifications")
    iface.Notify("A.I.M.", 0, "dialog-information", title, body, [], {}, expire)
    sys.exit(0)
except Exception:
    sys.exit(1)
PY
    then
      notify_ok=1
    fi
  fi

  # 3) X11 popup fallback (xmessage) — works without a notification daemon
  if [ "$notify_ok" -ne 1 ] && [ -n "${DISPLAY:-}" ] && command -v xmessage >/dev/null 2>&1; then
    # Non-blocking; auto-dismiss after ~5s
    timeout_s=$(( (expire_ms + 999) / 1000 ))
    [ "$timeout_s" -lt 2 ] && timeout_s=2
    # background so hooks never block
    (
      xmessage -timeout "$timeout_s" -center -buttons "OK:0" \
        -title "$title" "$body" >/dev/null 2>&1 || true
    ) &
    notify_ok=1
  fi

  # 4) tmux status flash if still nothing (useful on headless)
  if [ "$notify_ok" -ne 1 ] && [ -n "${TMUX:-}" ] && command -v tmux >/dev/null 2>&1; then
    tmux display-message -d "$((expire_ms))" "$title: $body" 2>/dev/null || true
    notify_ok=1
  fi
fi

# ── Optional sound ────────────────────────────────────────────
if [ "$sound_on" = "1" ]; then
  SOUND=""
  for cand in "${SOUND_DEFAULTS[@]}"; do
    [ -n "$cand" ] && [ -f "$cand" ] && SOUND="$cand" && break
  done

  if [ -n "${AIM_TURN_CHIME_CMD:-}" ]; then
    # shellcheck disable=SC2086
    eval $AIM_TURN_CHIME_CMD >/dev/null 2>&1 && play_ok=1 || play_ok=0
  elif [ -n "$SOUND" ]; then
    if command -v paplay >/dev/null 2>&1; then
      paplay "$SOUND" >/dev/null 2>&1 && play_ok=1 || play_ok=0
    elif command -v pw-play >/dev/null 2>&1; then
      pw-play "$SOUND" >/dev/null 2>&1 && play_ok=1 || play_ok=0
    elif command -v ffplay >/dev/null 2>&1; then
      timeout 3 ffplay -nodisp -autoexit -loglevel quiet -t 1 "$SOUND" >/dev/null 2>&1 && play_ok=1 || play_ok=0
    elif command -v aplay >/dev/null 2>&1 && [[ "$SOUND" == *.wav ]]; then
      aplay -q "$SOUND" >/dev/null 2>&1 && play_ok=1 || play_ok=0
    elif command -v canberra-gtk-play >/dev/null 2>&1; then
      canberra-gtk-play -f "$SOUND" >/dev/null 2>&1 && play_ok=1 || play_ok=0
    else
      play_ok=0
    fi
  fi
fi

# BEL only if sound wanted and nothing played, or forced
if { [ "$sound_on" = "1" ] && [ "$play_ok" -ne 1 ]; } || [ "${AIM_TURN_CHIME_BELL:-0}" = "1" ]; then
  if [ -n "${TMUX:-}" ] && command -v tmux >/dev/null 2>&1; then
    tmux display-message -d 1 "AIM turn done ($REASON)" 2>/dev/null || true
  fi
  { printf '\a' >/dev/tty; } 2>/dev/null || { printf '\a'; } 2>/dev/null || true
fi

if [ "${AIM_TURN_CHIME_DEBUG:-0}" = "1" ]; then
  echo "[aim_turn_chime] reason=$REASON vessel=$vessel notify_ok=$notify_ok play_ok=$play_ok" \
    >>"$STATE_DIR/turn_chime.log" 2>/dev/null || true
fi

exit 0
