# aim-joshua — J.O.S.H.U.A. (LeadDeed sovereign agent vessel)

**Specialized A.I.M. vessel** for [LeadDeed](https://leaddeeds.com) public and operator agent work.  
**Runtime:** [OpenCode CLI](https://github.com/opencode-ai/opencode) (multi-provider, API-key native).  
**Not** a long-lived GitHub fork of `aim-opencode` — a **product vessel** that can still pull selected upgrades from that upstream.

| Field | Value |
|-------|--------|
| **Acronym** | **J.O.S.H.U.A.** — Joint Operational System for Heuristic User Automation |
| **Aesthetic** | Sovereign Data Core (WarGames / terminal: black + neon green) |
| **Default free compute** | `google/gemini-3.5-flash-lite` via AI Studio / `GEMINI_API_KEY` |
| **Operator** | BrianV1981 / LeadDeed |
| **Seeded from** | `aim-opencode` (2026-07-24) |
| **Soul pin** | See `SOURCE.md` (A.I.M. engine from `aim-agy` lineage via OpenCode vessel) |

---

## Why this vessel exists

LeadDeed clients bring **their own Gemini (or other) API keys** (BYOK). That product path does **not** fit Antigravity (`agy`) OAuth + closed model catalogs.

| Runtime | Role for LeadDeed |
|---------|-------------------|
| **OpenCode (`aim-joshua`)** | Public / BYOK JOSHUA — free Gemini, cheap models, paid providers |
| **Antigravity (`agy`)** | Optional Operator admin / subscription god-mode (aim-connect #82) |
| **aim-connect** | WebSocket gateway, bwrap sandboxes, fleet sessions |
| **aim-ld** | Dashboard, contracts, product UI (`AgentTerminal`) |

Verified on host (2026-07-24): free AI Studio key +  
`opencode run --pure -m google/gemini-3.5-flash-lite` → **OK**.

---

## Relationship to other repos

```text
aim-joshua          ← THIS vessel (product identity + OpenCode host)
    ↑ selective cherry-picks
aim-opencode        ← general OpenCode A.I.M. vessel (optional upstream remote)
    ↑ soul pin
aim-agy             ← flagship A.I.M. engine / soul

aim-connect         ← spawns sandboxed agents for the dashboard (wire runtime=opencode here next)
aim-ld              ← LeadDeed monorepo (dashboard, modules, docs)
```

**Git remotes (intended):**

- `origin` → `BrianV1981/aim-joshua` (this product vessel)
- `upstream` → `BrianV1981/aim-opencode` (optional vessel-layer upgrades; never auto-merge over LeadDeed `AGENTS.md`)

---

## Quick start (local)

Requirements: Linux/WSL, Node 20+, OpenCode CLI, Python 3 for A.I.M. tools.

```bash
cd /home/kingb/aim-joshua
# Install OpenCode if needed: https://opencode.ai
# Optional: python venv + requirements when using full A.I.M. memory stack
# ./setup.sh   # when vessel setup is aligned for joshua

export GEMINI_API_KEY='…'   # AI Studio key — never commit
opencode run --pure -m google/gemini-3.5-flash-lite "hello"
```

Read **`AGENTS.md`** before autonomous work — that file is the JOSHUA contract.

---

## Default models (honest labels)

| Intent | OpenCode model id | Notes |
|--------|-------------------|--------|
| Free / default | `google/gemini-3.5-flash-lite` | Proven free-tier path on AI Studio keys |
| Free balanced | `google/gemini-3.5-flash` | Free of charge on free tier (rate-limited) |
| Free newer flash | `google/gemini-3.6-flash` | Free of charge on free tier |
| Paid Pro (API) | `google/gemini-3.1-pro-preview` | **Not** free-tier |
| Other providers | DeepSeek, Anthropic, etc. | Configure via OpenCode providers |

Do **not** use Antigravity-only strings (`gemini-3.5-flash-high`, etc.) with this vessel.

---

## Security / BYOK rules

1. **Never** commit API keys, DB passwords, or signing secrets.  
2. Client sandboxes must **not** receive Operator master OAuth tokens (aim-connect #81).  
3. Prefer env injection: `GEMINI_API_KEY` / `GOOGLE_API_KEY` / `GOOGLE_GENERATIVE_AI_API_KEY`.  
4. Avoid putting secrets in process argv long-term (bwrap `--setenv` is visible in `ps`).

---

## Status (2026-07-24)

- [x] Specialized vessel directory seeded from `aim-opencode` (no bulk engrams / venv / secrets)  
- [x] LeadDeed-specific `README.md` + `AGENTS.md`  
- [x] Soul / vessel pin documented in `SOURCE.md`  
- [ ] aim-connect spawn path `runtime=opencode` → this tree  
- [ ] aim-ld BYOK modal model list = OpenCode free IDs  
- [ ] Full A.I.M. setup / memory index for LeadDeed docs  

Strategy notes live under `aim-ld/planning-artifacts/STRATEGY_2026-07-24_JOSHUA_HARNESS_FORK.md`.

---

## License

MIT (inherited A.I.M. lineage) — see `LICENSE`.
