# Vessel lockstep (agy · grok · opencode)

**Orchestration (how to run multi-vessel work):** see `scripts/FLEET_ORCHESTRATION.md` — triage → dispatch → audit → merge → pin-sync, plus FROM/REPLY_TO tmux contract and surgical vs full sync.

## Policy

| Layer | Owner | Rule |
|-------|--------|------|
| Shared engine | **aim-agy** | Implement host-agnostic fixes here first |
| Grok overlays | **aim-grok** | See `SYNC_FROM_AIM_AGY.md` denylist |
| OpenCode host | **aim-opencode** | Port from agy; keep OpenCode-only modules local |

**Layout goal (Operator 2026-07-12):** all vessels use **nested** `aim-agy_os/` (same shape as agy/grok). Identical soul tree as far as practical; **harness overlays only** where the CLI differs (spawn binary, transcript paths, skills dir). aim-opencode migrates off flat `aim_core/`.

**Never** open parallel “same feature” PRs on two vessels. File sibling tickets, implement once on soul, sync/port.

## Diff check (all three)

From aim-grok (or any checkout that has the script):

```bash
# Human report (always exit 0)
python3 /home/kingb/aim-grok/scripts/vessel_core_diff.py --report-only

# CI-style: exit 1 if shared-module content drifts or lockstep modules disagree
python3 /home/kingb/aim-grok/scripts/vessel_core_diff.py

# Pair focus
python3 /home/kingb/aim-grok/scripts/vessel_core_diff.py --pair agy,opencode --report-only
python3 /home/kingb/aim-grok/scripts/vessel_core_diff.py --pair agy,grok --json | head

# Override roots
AIM_OPENCODE_ROOT=/path/to/aim-opencode python3 scripts/vessel_core_diff.py --report-only
```

## Sync rituals

### agy → grok (vendor nested OS)

See `SYNC_FROM_AIM_AGY.md` + bump `SOURCE.md`.

### agy → opencode (flat `aim_core/`)

**Do not** `rsync --delete` the whole tree (layout + OpenCode-only modules differ).

1. Run `vessel_core_diff.py --pair agy,opencode --report-only`
2. Port **by module**: prefer shared names (`aim_doctor.py`, `reincarnation/`, session naming, wiki, doctor, FTS fix)
3. Keep OpenCode-only: `daemon.py`, `aim_crash.py`, `session_bridge.py`, …
4. Record pin in opencode `SOURCE.md` (create if missing) with agy SHA
5. `pytest` / `doctor` on opencode

### Naming contract (all three)

Spawned tmux agents:

```text
{vessel}_{role}_{project_slug}_{timestamp}
```

Vessel defaults: `agy` | `grok` | `opencode` via `AIM_VESSEL_CLI`.

Canonical module should live on **aim-agy** once (#95); vessels re-export or sync the same file.

## Orchestrating an OpenCode agent

1. Open tmux in `/home/kingb/aim-opencode` with opencode CLI.
2. Paste a **short** pointer to the dispatch chalkboard (below).
3. Require structured reply: AGREED / DONE / DIFF / QUESTIONS.
4. Operator (or aim-grok) re-runs `vessel_core_diff.py` after their PR.

Dispatch template: `scripts/DISPATCH_OPENCODE_LOCKSTEP.md`

## Cadence

| Trigger | Action |
|---------|--------|
| agy merges engine PR | grok sync ritual; opencode port or ticket |
| Weekly | `vessel_core_diff.py --report-only` → file tickets for unexpected diffs |
| Before multi-vessel release | lockstep modules all `SYNC` or documented overlay |
