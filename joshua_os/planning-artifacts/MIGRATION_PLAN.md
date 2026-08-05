# Migration Plan: Antigravity CLI to Antigravity CLI (agy)

## Objective
Convert the clean A.I.M. exoskeleton (`aim-agy`) from utilizing the deprecated Antigravity CLI to the new Go-based agent-first platform: Antigravity CLI (`agy`).

## Phase 1: Terminology and File Structure Overhaul
- **Rename Configuration Files:** Rename `.agyignore` to `.agyignore`.
- **Rename Hidden Directories:** Ensure all project-level `.agy/` directories (used for local state or tool caches) are migrated to `.agy/`.
- **Update Markdown Documentation:** Modify `AGENTS.md`, `BOOTSTRAP.md`, `README.md`, and any files in `memory-wiki/` to reflect the transition (e.g. replacing "Antigravity terminal shell" with "Antigravity terminal shell").

## Phase 2: Core Engine Code Migration
- **Script Refactoring:** Perform bulk string replacements across `aim_core/` and `scripts/`.
  - Replace `agy login` with `agy login`.
  - Replace `agy --dangerously-skip-permissions` with `agy --dangerously-skip-permissions`.
  - Replace internal `subprocess.run(["agy", ...])` calls with `subprocess.run(["agy", ...])`.
- **Configuration Defaults:** Update default tool endpoints and CLI flags mapped in `aim_config.py` to match Antigravity 2.0 specifications.
- **Alias Updates:** Verify that the system-wide `.bashrc` aliases correctly map the exoskeleton router to intercept `agy` processes if required.

## Phase 3: Validation and TDD
- **Background Packer Update:** Ensure the automated background packer (`pack_mission.sh` or equivalent) handles out-of-memory checks for `agy` appropriately.
- **Flight Recorder:** Confirm the conversational signal extractor (`recover_json_logs.py` or equivalent) can accurately parse `.agy/tmp/aim/chats/` JSONL outputs, as the new backend may have structural differences from the old Antigravity CLI.

## Deployment Strategy
All changes will be implemented in isolated Git worktrees according to the GitOps Mandate. We will empirically test the engine router and JSON log extraction before merging to `main`.
