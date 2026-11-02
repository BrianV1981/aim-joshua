# J.O.S.H.U.A. Hooks Index (`joshua_os/hooks/`)

This directory contains lifecycle hook scripts dispatched via `joshua_os/.aim_core/aim_router.py` when registered in Antigravity (`settings.json`).

## Active Hooks
- **[cognitive_mantra.py](./cognitive_mantra.py) (`AfterTool`):** The Anti-Drift Shield. Tracks autonomous tool-call counts in `joshua_os/.aim_core/temp/turn_counter.json` and periodically injects a `<MANTRA>` reminder reinforcing root `AGENTS.md` mandates during extended execution loops.
