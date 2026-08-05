# Active Memory Protocol

## Context
Previously, the A.I.M. system used a complex set of detached crons and background daemons (`wiki_batch`, `wiki_compiler`, `session_summarizer`) to "vacuum" up previous sessions from the transcript and write them into the memory wiki. This resulted in the wiki becoming polluted with Pytest fixture artifacts, E2E test runs, and general scratchpad noise, because the background agent lacked the live context to differentiate a test from a real operational breakthrough.

## The Pivot
On July 26, 2026, the architecture was drastically simplified:
- The entire background vacuum system was deprecated (PR #122).
- Replaced by the `aim-memory-wiki` skill.
- The wiki is now explicitly "opt-in" and strictly maintained by the **active agent** while the session context is still fresh in its context window.

This returns agency to the operator and drastically increases the signal-to-noise ratio in the persistent long-term memory.
