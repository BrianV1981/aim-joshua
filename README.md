# J.O.S.H.U.A. (LeadDeeds Custom Node)

This vessel houses the sovereign operating environment for **J.O.S.H.U.A.**, tailored for [LeadDeeds.com](https://leaddeeds.com).

> **Starter source:** product language from  
> `aim-connect/agent_workspaces/agent-mikeywillvas2018_gmail_com/README.md`  
> **Vessel:** `aim-joshua` — specialized clone of `aim-opencode` (not a long-lived GitHub fork).

| Field | Value |
|-------|--------|
| **Acronym** | **J.O.S.H.U.A.** — Joint Operational System for Heuristic User Automation |
| **Product** | LeadDeed / LeadDeeds platform |
| **Runtime** | [OpenCode CLI](https://github.com/opencode-ai/opencode) (multi-provider, API-key / BYOK) |
| **Default free model** | `google/gemini-3.5-flash-lite` |
| **Repo** | https://github.com/BrianV1981/aim-joshua (private) |
| **Local path** | `/home/kingb/aim-joshua` |

---

## Architecture & Concept

J.O.S.H.U.A. is an advanced AI operating system that provides a unified, persistent interface for users of the LeadDeeds platform. It bridges frontend user interactions (dashboard chat) and backend autonomous operations (sandboxed agent node).

- **Sovereignty** — Each client node runs in a sandboxed, isolated directory (e.g. `agent-mikeywillvas2018_gmail_com` under aim-connect) strictly insulated from the main host server and from other tenants.
- **Sub-Agent Fleet Management** — J.O.S.H.U.A. can spawn and orchestrate sub-agents (“Fleet Agents”) in their own ephemeral `fleet_workspaces/` sandboxes.
- **A.I.M. layer** — Long-term memory, GitOps helpers, wiki, and reincarnation come from the A.I.M. stack nested in this vessel (`aim-agy_os/`), same DNA as other A.I.M. vessels.
- **OpenCode host (BYOK)** — Public/client inference uses **OpenCode** with the user’s API keys (free Gemini proven). This replaces Antigravity/`agy` OAuth for customer nodes so free AI Studio keys and multi-provider models work cleanly.
- **Optional Operator path** — Admin / subscription “god-mode” may still use Antigravity on the host; client sandboxes must **never** receive master OAuth tokens.

```text
leaddeeds.com dashboard (aim-ld)
        │  WebSocket + BYOK key
        ▼
aim-connect (gateway / bwrap / fleet)
        │  runtime → opencode (planned)
        ▼
aim-joshua vessel  OR  per-client agent_workspaces/…
        │
        ├─ AGENTS.md   (JOSHUA contract)
        ├─ brain/      (session memory — on connect workspaces)
        └─ fleet_workspaces/  (isolated sub-agents)
```

---

## Example tenant setup (starter node)

Gold-standard starter workspace used while designing the product:

| Field | Value |
|-------|--------|
| **Owner** | Mike (`mikeywillvas2018@gmail.com`) |
| **Workspace** | `aim-connect/agent_workspaces/agent-mikeywillvas2018_gmail_com` |
| **Memory** | Long-term conversations and logs in that workspace’s `brain/` directory |
| **Contract** | That workspace’s `AGENTS.md` (promoted into this vessel as the template) |

Other LeadDeed accounts get the same pattern with their own email-derived workspace and Operator line.

---

## This vessel vs other repos

| Repo | Role |
|------|------|
| **aim-joshua** (this) | Product vessel template + OpenCode host DNA |
| **aim-opencode** | Upstream vessel clone source (`git remote upstream`) |
| **aim-connect** | WebSocket, bwrap, per-client workspaces, fleet |
| **aim-ld** | Dashboard, contracts, modules, `AgentTerminal` |
| **aim-agy** | Flagship A.I.M. soul lineage (engine pin) |

### Git remotes

```bash
origin    → BrianV1981/aim-joshua      # this product vessel
upstream  → BrianV1981/aim-opencode    # pull vessel upgrades carefully
```

```bash
git fetch upstream
git log HEAD..upstream/main --oneline   # review before merge/cherry-pick
# Never blind-merge over AGENTS.md / this README without intent
```

---

## Quick start (local vessel)

Requirements: Linux/WSL, Node 20+, OpenCode CLI.

```bash
cd /home/kingb/aim-joshua
export GEMINI_API_KEY='…'   # AI Studio key — never commit
opencode run --pure -m google/gemini-3.5-flash-lite "hello"
```

Read **`AGENTS.md`** before autonomous work — that file is the full JOSHUA operating contract.

Optional full A.I.M. stack: `bash aim-agy_os/setup.sh` when you want Engram/wiki CLI (`./aim`).

---

## Default models (honest)

| Intent | OpenCode model id |
|--------|-------------------|
| Free / default | `google/gemini-3.5-flash-lite` |
| Free balanced | `google/gemini-3.5-flash` |
| Free newer flash | `google/gemini-3.6-flash` |
| Paid Pro (API) | `google/gemini-3.1-pro-preview` (not free-tier) |
| Other APIs | DeepSeek, Anthropic, etc. via OpenCode providers |

---

## Security / BYOK

1. Never commit API keys, DB passwords, or signing secrets.  
2. Client sandboxes must not mount Operator master OAuth tokens.  
3. Prefer env injection for keys; avoid long-lived secrets in `ps` argv.  
4. Multi-tenant: one account’s workspace ≠ global data.

---

## Status

- [x] True git clone of `aim-opencode` → `aim-joshua`  
- [x] Product `README` language from mikey starter node  
- [x] Product `AGENTS.md` from mikey workspace (OpenCode paths)  
- [ ] aim-connect spawn `runtime=opencode` → this vessel / client workspaces  
- [ ] aim-ld BYOK modal model list = OpenCode free IDs  

---

## License

MIT (A.I.M. lineage) — see `LICENSE`.
