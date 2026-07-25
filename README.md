# aim-joshua — J.O.S.H.U.A. for LeadDeeds.com

**Custom AI agent for [LeadDeeds.com](https://leaddeeds.com).**  
Each live JOSHUA is a **sandboxed** A.I.M. node for one entitled user: web research + **local** lead data — not a multi-vessel swarm peer.

**This repository is the starting point / cloning point for new JOSHUAs.**  
Copy or provision from here, drop that user’s data into the sandbox, inject their API key, boot.

| | |
|--|--|
| **Full name** | **J.O.S.H.U.A.** — Joint Operational System for Heuristic User Automation |
| **Product** | LeadDeeds customer agent |
| **Runtime** | OpenCode + BYOK (default free model: `google/gemini-3.5-flash-lite`) |
| **Agent rules** | [`AGENTS.md`](./AGENTS.md) |
| **Mission / isolation** | [`VESSEL.md`](./VESSEL.md) |

---

## What JOSHUA can use (in his sandbox)

He does **not** pull LeadDeed packs over the network for core data. Data is **already on disk** in the sandbox:

| Asset | Role |
|-------|------|
| **Daily CSV files** | Fresh daily lead / signal drops for that account |
| **Rolling 30-day lists** | Recent window (“rolling 30”) for volume and triangulation-style work |
| **SQLite database** | Queryable local DB ready to open and inspect (views / tables provisioned per tenant) |
| **Internet** | Public research when tools allow (outside the local files) |
| **Optional tools** | People-find / marketing-lead helpers (add in-sandbox as needed) |

**Boundary:** only **this** user’s entitled files and DB. No other tenants. No host Operator OAuth. No chat with aim-grok / aim-agy / other vessels.

---

## Intended sandbox layout (per new JOSHUA)

When aim-connect (or ops) clones a new node, give him something like:

```text
joshua-<user>/
  AGENTS.md          # contract (from this repo)
  README.md          # optional short tenant note
  data/
    daily/           # daily CSV drops
    rolling-30/      # rolling 30-day list exports
  db/
    leads.sqlite     # (or tenant-named) ready-to-query SQLite
  brain/             # agent memory (runtime)
  tools/             # optional lead/marketing helpers
```

Exact paths can match your provisioner; the rule is **local paths, not fetch-on-demand** for those packs.

---

## How new Joshuas are born

1. **Clone / copy this repo** (or rsync a thin slice: at least `AGENTS.md` + empty `data/` / `db/`).  
2. **Provision** that user’s daily CSVs, rolling-30 lists, and SQLite into the sandbox.  
3. **Inject** BYOK: `GOOGLE_GENERATIVE_AI_API_KEY` (required for OpenCode Google; also set `GEMINI_API_KEY` if other tools need it).  
4. **Boot** via aim-connect bwrap (or local OpenCode) with cwd = **that thin sandbox**, not necessarily the full monorepo tree.  
5. User chats on LeadDeeds.com; JOSHUA answers from **local data + web**, under `AGENTS.md`.

```bash
# DNA / template work
git clone https://github.com/BrianV1981/aim-joshua.git
cd aim-joshua

# Runtime smoke (thin dir recommended)
export GOOGLE_GENERATIVE_AI_API_KEY='…'   # never commit
opencode run --pure -m google/gemini-3.5-flash-lite "hello"
```

Upstream vessel upgrades (optional): remote `upstream` → `aim-opencode` — review before merge; never overwrite product identity blindly.

---

## Repo roles

| Piece | Role |
|-------|------|
| **This repo** | Template + DNA for every new JOSHUA |
| **aim-connect** | Gateway: sandbox spawn, key inject, chat bridge |
| **aim-ld** | LeadDeeds dashboard / product UI |
| **aim-opencode** | Optional upstream for OpenCode vessel engine fixes |

---

## Security

- No API keys or DB secrets in git.  
- No master host OAuth in client sandboxes.  
- Multi-tenant: one sandbox = one account’s radar.
