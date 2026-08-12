# Architecture

## The OS Framework
J.O.S.H.U.A. is a CLI-agnostic operating system designed to serve as the foundational brain for autonomous AI agents. The framework has entirely decoupled from legacy "CLI vessels" (e.g., aim-grok, aim-opencode). 

## Memory Synthesis
The system utilizes a Just-In-Time (JIT) memory synthesis approach. 
- The legacy `_ingest/` drop zone and background `session_summarizer.py` daemons have been abolished. 
- Instead, Conscious Agents invoke the `aim-memory-wiki` skill synchronously to synthesize recent architectural changes and natively edit this persistent markdown wiki.
- During system boot, the wiki is embedded directly into the `memory_lance` LanceDB RAM pool.

## The Skill Library Architecture
The `aim-skill-library` utilizes a **Base + Override** architecture. All universal tool skills reside in the global `skills/` directory. However, when a specific vessel requires unique mechanics (e.g., `aim-handoff` triggering distinct `agy-blackbox` or `grok-blackbox` commands), the vessel-specific override is stored in `vessels/<cli>/skills/`. The installation script seamlessly detects and links the override, falling back to the global base if none exists.
