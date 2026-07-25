# Vessel card — aim-joshua

| | |
|--|--|
| **Name** | aim-joshua |
| **Kind** | Specialized product vessel (not a GitHub fork) |
| **CLI** | `opencode` |
| **Default model** | `google/gemini-3.5-flash-lite` |
| **Sibling vessels** | aim-opencode, aim-agy, aim-grok, aim-codex |
| **Gateway** | aim-connect (future: `runtime=opencode`) |
| **Product monorepo** | aim-ld |

## Spawn contract (for aim-connect)

```text
cwd:        /home/kingb/aim-joshua   # or per-client workspace bind
command:    opencode   # or opencode run / attach policy TBD
env:        GEMINI_API_KEY=<client BYOK>
model:      google/gemini-3.5-flash-lite   # free default
sandbox:    bwrap; NO master antigravity-oauth-token
```

## Local path

`/home/kingb/aim-joshua`
