# Dynamic Bwrap Forge Skill (`aim-bwrap-forge`)

With the demotion of mandatory sandboxing from the core OS install, the ability to spawn strict isolation has been delegated to an autonomous agent skill.

## Overview
The `aim-bwrap-forge` skill allows J.O.S.H.U.A. to dynamically spin up a `bwrap`-isolated sandbox and dispatch a co-agent into it on demand. 

## Purpose
- Safely executing untrusted code or experimental generation.
- Isolating specific high-risk tasks to prevent contamination of the global OS.
- Maintaining strict data isolation in multi-tenant workloads.

## Execution Flow
1. Agent creates a secure directory for the new tenant/sandbox.
2. Initializes the `bwrap` environment pointing to the standard J.O.S.H.U.A. install scripts but confined to the sandbox folder.
3. Spawns a co-agent into the sandbox using `tmux` attached to the `bwrap` shell.
4. Communicates with the isolated agent via standard `aim-communicate` sockets.
5. Upon completion, the sandboxed agent commits its final memory state to its local `.git` ledger. The Prime Agent retrieves the outputs and deletes the sandbox.
