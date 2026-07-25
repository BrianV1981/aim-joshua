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
cwd:        per-client thin workspace (AGENTS.md + data), NOT full monorepo clone
command:    opencode run --pure -m google/gemini-3.5-flash-lite …
env:        GOOGLE_GENERATIVE_AI_API_KEY=<client BYOK>   # required by OpenCode Google
            GEMINI_API_KEY / GOOGLE_API_KEY optional aliases
model:      google/gemini-3.5-flash-lite   # free default
sandbox:    bwrap; bind writable opencode state; NO master OAuth token
```

## Smoke (2026-07-25)

| Test | Result |
|------|--------|
| REST free Gemini key | PASS |
| OpenCode + key + **minimal** dir (AGENTS only) | **PASS** `JOSHUA_MIN_OK` |
| OpenCode + key + bwrap + minimal dir | **PASS** `JOSHUA_BWRAP_OK` |
| OpenCode + key + full `/home/kingb/aim-joshua` tree | **HANG** (timeout; empty stdout) |
| `./aim doctor` after local venv | PASS |

## Local path (template / DNA)

`/home/kingb/aim-joshua` — product DNA and clone of aim-opencode. **Do not use the full tree as every client cwd.**
