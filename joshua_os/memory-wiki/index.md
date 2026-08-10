# Project Wiki Index
This is the persistent LLM wiki for the A.I.M. project. Active agents use the `aim-memory-wiki` skill to systematically update this index and associated pages to maintain a cohesive, long-term memory of architectural decisions, context, and project lore.

## Core Concepts
- [Active Memory Protocol](pages/active-memory-protocol.md): The shift from offline background cron vacuuming to JIT, active-agent synthesis.
- [Native OS Shift & GitOps Worktrees](pages/native-os-shift.md): Transitioning from mandatory sandboxing to native installation utilizing `git worktree` for isolated, parallel execution.

## Architecture
- [Dynamic Bwrap Forge Skill](pages/bwrap-forge-skill.md): Offloading strict sandbox creation to an autonomous, on-demand skill (`aim-bwrap-forge`).

## Operations

