# DEPRECATED — flat `aim_core/`

Canonical engine path (fleet lockstep):

```text
aim-agy_os/.aim_core/
```

This directory is a **path bootstrap only**. Do not add engine modules here.
Use `./aim` or `PYTHONPATH=aim-agy_os:aim-agy_os/.aim_core`.

OpenCode-only modules live under the nested core:
`daemon.py`, `aim_crash.py`, `session_bridge.py`, `aim_opencode_update.py`.
