#!/usr/bin/env bash
# aim_turn_chime.sh — short audio cue when an agent turn ends.
#
# Wired by:
#   - Grok: Stop / StopFailure hooks (~/.grok/hooks/aim-turn-chime.json)
#   - OpenCode: session.idle in aim-hooks plugin
#   - Manual: aim_turn_chime.sh [reason]
#
# Env:
#   AIM_TURN_CHIME=0          disable entirely
#   AIM_TURN_CHIME_CMD=...    full custom play command (overrides backends)
#   AIM_TURN_CHIME_SOUND=path custom wav/oga
#   AIM_TURN_CHIME_DEBOUNCE_MS=1500  min gap between chimes (default 1500)
#   AIM_TURN_CHIME_FORCE=1    ignore debounce
#   AIM_TURN_CHIME_BELL=1     also ring terminal BEL
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
  # Prefer python ms (portable); date %3N is GNU-only and can be literal on busybox
  if command -v python3 >/dev/null 2>&1; then
    python3 -c 'import time; print(int(time.time()*1000))' 2>/dev/null && return
  fi
  echo $(( $(date +%s) * 1000 ))
}

now="$(now_ms)"
# Debounce (shared stamp — multi-pane agents won't machine-gun the speaker)
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
# Reserve the slot before playing (avoid concurrent double-chime)
echo "$now" >"$STAMP_FILE" 2>/dev/null || true

# Resolve sound file
SOUND=""
for cand in "${SOUND_DEFAULTS[@]}"; do
  [ -n "$cand" ] && [ -f "$cand" ] && SOUND="$cand" && break
done

play_ok=1

if [ -n "${AIM_TURN_CHIME_CMD:-}" ]; then
  # shellcheck disable=SC2086
  eval $AIM_TURN_CHIME_CMD >/dev/null 2>&1 || play_ok=0
elif [ -n "$SOUND" ]; then
  if command -v paplay >/dev/null 2>&1; then
    paplay "$SOUND" >/dev/null 2>&1 || play_ok=0
  elif command -v pw-play >/dev/null 2>&1; then
    pw-play "$SOUND" >/dev/null 2>&1 || play_ok=0
  elif command -v ffplay >/dev/null 2>&1; then
    # -t caps hang risk; -autoexit returns when done
    timeout 3 ffplay -nodisp -autoexit -loglevel quiet -t 1 "$SOUND" >/dev/null 2>&1 || play_ok=0
  elif command -v aplay >/dev/null 2>&1 && [[ "$SOUND" == *.wav ]]; then
    aplay -q "$SOUND" >/dev/null 2>&1 || play_ok=0
  elif command -v canberra-gtk-play >/dev/null 2>&1; then
    canberra-gtk-play -f "$SOUND" >/dev/null 2>&1 || play_ok=0
  else
    play_ok=0
  fi
else
  play_ok=0
fi

# Fallback: terminal bell (works over most ssh/tmux if bell-pass-through on)
if [ "$play_ok" -ne 1 ] || [ "${AIM_TURN_CHIME_BELL:-0}" = "1" ]; then
  # Ring BEL on every pane of current tmux session if possible; else stdout
  if [ -n "${TMUX:-}" ] && command -v tmux >/dev/null 2>&1; then
    tmux display-message -d 1 "AIM turn done ($REASON)" 2>/dev/null || true
    # BEL into this client
    printf '\a' >/dev/tty 2>/dev/null || printf '\a' || true
  else
    printf '\a' >/dev/tty 2>/dev/null || printf '\a' || true
  fi
fi

# Optional debug log
if [ "${AIM_TURN_CHIME_DEBUG:-0}" = "1" ]; then
  echo "[aim_turn_chime] reason=$REASON sound=${SOUND:-none} play_ok=$play_ok" \
    >>"$STATE_DIR/turn_chime.log" 2>/dev/null || true
fi

exit 0
