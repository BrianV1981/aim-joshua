# Architecture

## The OS Framework
J.O.S.H.U.A. is a CLI-agnostic operating system designed to serve as the foundational brain for autonomous AI agents. The framework has entirely decoupled from legacy "CLI vessels" (e.g., aim-grok, aim-opencode). 

## Memory Synthesis
The system utilizes a Just-In-Time (JIT) memory synthesis approach. 
- The legacy `_ingest/` drop zone and background `session_summarizer.py` daemons have been abolished. 
- Instead, Conscious Agents invoke the `aim-memory-wiki` skill synchronously to synthesize recent architectural changes and natively edit this persistent markdown wiki.
- During system boot, the wiki is embedded directly into the `memory_lance` LanceDB RAM pool.
