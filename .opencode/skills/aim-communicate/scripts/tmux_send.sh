#!/usr/bin/env bash
# aim-communicate: paste short message into a tmux session with correct submit
# for Grok vs AGY, and mandatory FROM / REPLY_TO envelope.
#
# Usage:
#   tmux_send.sh --target <session> --message 'body'
#   tmux_send.sh --target <session> --file /path/to/short.txt
#   tmux_send.sh --target <session> --from <session> --reply-to <session> --message '...'
#   tmux_send.sh --target <session> --message '...' --force-vessel grok|agy
#   tmux_send.sh --target <session> --message '...' --no-envelope   # only if already prefixed
#
set -euo pipefail

TARGET=""
MESSAGE=""
FILE=""
FORCE_VESSEL=""
FROM_SESSION=""
REPLY_TO=""
NO_ENVELOPE=0
BUF="aim_comm_short_$$"

usage() {
  cat <<'EOF'
Usage:
  tmux_send.sh --target <session> --message 'text'
  tmux_send.sh --target <session> --from <session> --reply-to <session> --message 'text'
  tmux_send.sh --target <session> --file /path/to/msg.txt
  --force-vessel grok|agy|opencode
  --no-envelope   # do not auto-prefix FROM/REPLY_TO
EOF
  exit 1
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --target|-t) TARGET="${2:-}"; shift 2 ;;
    --message|-m) MESSAGE="${2:-}"; shift 2 ;;
    --file|-f) FILE="${2:-}"; shift 2 ;;
    --force-vessel) FORCE_VESSEL="${2:-}"; shift 2 ;;
    --from) FROM_SESSION="${2:-}"; shift 2 ;;
    --reply-to) REPLY_TO="${2:-}"; shift 2 ;;
    --no-envelope) NO_ENVELOPE=1; shift ;;
    -h|--help) usage ;;
    *) echo "Unknown arg: $1" >&2; usage ;;
  esac
done

[[ -n "$TARGET" ]] || { echo "error: --target required" >&2; exit 1; }
if [[ -n "$FILE" ]]; then
  MESSAGE="$(cat "$FILE")"
fi
[[ -n "$MESSAGE" ]] || { echo "error: --message or --file required" >&2; exit 1; }

if ! tmux has-session -t "$TARGET" 2>/dev/null; then
  echo "error: tmux session not found: $TARGET" >&2
  exit 1
fi

# Resolve FROM session (who is sending)
if [[ -z "$FROM_SESSION" ]]; then
  FROM_SESSION="$(tmux display-message -p '#{session_name}' 2>/dev/null || true)"
fi
if [[ -z "$FROM_SESSION" ]]; then
  FROM_SESSION="unknown"
  echo "[tmux_send] warning: could not detect FROM session; set --from explicitly" >&2
fi

# Default REPLY_TO to FROM (orchestrator pattern: "reply to me")
if [[ -z "$REPLY_TO" ]]; then
  REPLY_TO="$FROM_SESSION"
fi

# Envelope: always include FROM + REPLY_TO unless already present or disabled
if [[ "$NO_ENVELOPE" -eq 0 ]]; then
  if ! grep -q '\[FROM:' <<<"$MESSAGE"; then
    MESSAGE="[FROM:${FROM_SESSION}] [REPLY_TO:${REPLY_TO}] ${MESSAGE}"
  fi
  # If FROM present but REPLY_TO missing, inject REPLY_TO after FROM
  if grep -q '\[FROM:' <<<"$MESSAGE" && ! grep -q '\[REPLY_TO:' <<<"$MESSAGE"; then
    MESSAGE="${MESSAGE/\[FROM:${FROM_SESSION}\]/[FROM:${FROM_SESSION}] [REPLY_TO:${REPLY_TO}]}"
    if ! grep -q '\[REPLY_TO:' <<<"$MESSAGE"; then
      MESSAGE="[REPLY_TO:${REPLY_TO}] ${MESSAGE}"
    fi
  fi
fi

# Detect vessel from TARGET pane command
CMD="$(tmux list-panes -t "$TARGET" -F '#{pane_current_command}' 2>/dev/null | head -1 || true)"
VESSEL="$FORCE_VESSEL"
if [[ -z "$VESSEL" ]]; then
  case "$CMD" in
    grok) VESSEL=grok ;;
    opencode) VESSEL=opencode ;;
    agy|gemini) VESSEL=agy ;;
    *)
      case "$TARGET" in
        *grok*|grok-audit) VESSEL=grok ;;
        *opencode*) VESSEL=opencode ;;
        *) VESSEL=agy ;;
      esac
      ;;
  esac
fi

echo "[tmux_send] from=$FROM_SESSION reply_to=$REPLY_TO target=$TARGET cmd=$CMD vessel=$VESSEL"
echo "[tmux_send] message=${MESSAGE:0:200}..."

tmux set-buffer -b "$BUF" "$MESSAGE"
tmux send-keys -t "$TARGET" C-u 2>/dev/null || true
sleep 0.2
tmux paste-buffer -b "$BUF" -p -t "$TARGET"
sleep 0.5

if [[ "$VESSEL" == "grok" || "$VESSEL" == "opencode" ]]; then
  # Grok + OpenCode: Enter = send. Do NOT send Escape first (cancels/blurs).
  tmux send-keys -t "$TARGET" Enter
  sleep 0.35
else
  # AGY: Escape then Enter as separate events
  tmux send-keys -t "$TARGET" Escape
  sleep 0.3
  tmux send-keys -t "$TARGET" Enter
fi

sleep 1.0
echo "[tmux_send] capture (tail):"
tmux capture-pane -t "$TARGET" -p -J -S -25 | tail -30

tmux delete-buffer -b "$BUF" 2>/dev/null || true
echo "[tmux_send] done — verify submitted turn; reports must hit REPLY_TO=$REPLY_TO"
