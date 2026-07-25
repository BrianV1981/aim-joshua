# J.O.S.H.U.A. — vessel card

**What he is:** a **sandboxed A.I.M. agent** for a single LeadDeed user (or demo tenant).  
**What he is not:** a board-room peer of aim-grok / aim-agy / aim-ld. He does **not** message other vessels, join fleet orchestration, or “report to the swarm.”

---

## Mission (product)

| Focus | In scope |
|-------|----------|
| **Internet** | Research, public web, lead signals the user asks for |
| **Sandbox data** | CSVs, SQLite/local DBs, files **inside this node only** |
| **Lead / marketing help** | Find, filter, draft outreach, explain territories — using **allowed** data + tools |
| **BYOK compute** | User’s API key (default free: `google/gemini-3.5-flash-lite` via OpenCode) |

| Out of scope | |
|--------------|--|
| Inter-vessel tmux / aim-communicate to other A.I.M. agents | |
| Host Operator OAuth / master billing | |
| Other tenants’ databases or workspaces | |
| Full `/home/kingb/aim-joshua` monorepo as runtime cwd | |

---

## Isolation model

```text
leaddeeds.com (chat UI)
        │  BYOK key + prompt
        ▼
aim-connect (gateway + bwrap)
        │
        ▼
thin sandbox workspace
  AGENTS.md          ← JOSHUA contract
  data/  or *.csv    ← that user’s entitled datasets
  brain/             ← his memory only
  (optional tools/)  ← lead-find / marketing helpers
```

- One sandbox = one account’s world.  
- **Internet + local sandbox DBs** = primary tools.  
- Custom tools (people-find, marketing leads) are **optional add-ons in the sandbox**, not links to other vessels.

---

## Runtime (engineering, short)

| | |
|--|--|
| **DNA repo** | `/home/kingb/aim-joshua` (clone of aim-opencode — template only) |
| **CLI** | OpenCode |
| **Default model** | `google/gemini-3.5-flash-lite` |
| **Required env** | `GOOGLE_GENERATIVE_AI_API_KEY=<client key>` |
| **Client cwd** | Thin workspace (AGENTS + data), not the full git tree |
| **Gateway** | aim-connect injects key + spawns sandbox |

```text
command:  opencode run --pure -m google/gemini-3.5-flash-lite …
env:      GOOGLE_GENERATIVE_AI_API_KEY=…   # required
sandbox:  bwrap; NO master OAuth token
```

---

## Smoke note (2026-07-25)

Thin dir + free Gemini + OpenCode (and bwrap) **PASS**.  
Full monorepo as cwd **hangs** — do not ship that as client spawn.
