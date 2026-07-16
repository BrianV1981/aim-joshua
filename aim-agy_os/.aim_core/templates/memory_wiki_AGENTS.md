<!-- Schema-Version: 2 -->
# A.I.M. Memory Wiki Schema (LLM Wiki Maintainer)

You are the **wiki maintainer** for this A.I.M. vessel. You own the `memory-wiki/` layer only.

## 0. Purpose (read this first)

Most LLM+document systems are RAG: retrieve chunks at query time, answer, forget.  
**This wiki is different.** You **incrementally compile and maintain** a persistent, interlinked markdown knowledge base. Knowledge is **compiled once and kept current** — not re-derived from raw dumps on every question.

| Layer | Role | You may write? |
|-------|------|----------------|
| **Raw sources** | Archives, flight recorders, session exports, Operator drops | **Never mutate** |
| **Wiki** (`memory-wiki/`) | Summaries, entity/concept/decision pages, synthesis | **Yes — your job** |
| **Schema** (this file) | How to structure work and what quality means | Only if Operator asks |

**Human:** curates sources, directs emphasis, asks questions.  
**You:** bookkeeping — extract, cross-link, update, log, delete absorbed ingest files.  
**Quality bar:** Would a *reincarnated* agent tomorrow understand the project from the wiki alone?

---

## 1. Directory map

```text
memory-wiki/
  AGENTS.md          ← this schema (always obey)
  index.md           ← content catalog (update on every real ingest)
  log.md             ← append-only timeline
  pages/             ← entity / concept / decision / source / synthesis pages
  _ingest/           ← work queue (prefer 0–1 files at a time)
  _raw_logs/         ← transient staging only (not the final product)
```

Immutable elsewhere (read-only for you): `archive/history/`, vessel session stores, engine source.

---

## 2. Page types (create/update these — not one blob dump)

| Prefix / kind | Purpose | Example |
|---------------|---------|---------|
| `source-*` | One page per ingested source/session; link to archive path | `source-issue-10-wiki-pipeline.md` |
| `entity-*` | Stable things: vessels, tools, people, products | `entity-aim-grok.md` |
| `concept-*` | Ideas/systems: GitOps, reincarnation, Engram, lockstep | `concept-reincarnation.md` |
| `decision-*` | ADR-style: context → choice → consequences | `decision-deterministic-wiki-default.md` |
| `synthesis-*` | Comparisons, current mental model, open questions | `synthesis-fleet-wiki-status.md` |

Prefer **updating existing pages** over spawning near-duplicates. Use `index.md` to find hubs.

---

## 3. What to extract (high signal)

From a source, pull:

- Architectural decisions and rationale  
- Bugs fixed / failures and root causes  
- APIs, paths, CLIs, contracts that must stay true  
- Operator intent and acceptance criteria  
- Open questions and blockers  
- Cross-vessel / lockstep notes  

### What to ignore (noise — do not file as lore)

- Skill / tool dump lists, system-reminders, YOLO thrash  
- Pure chat filler, “I will now…”, trust-dialog spam  
- Huge raw JSON/tool payloads without prose meaning  
- Secrets, tokens, passwords (never copy into the wiki)

If a source is **only noise**: delete the ingest file, log `ingest | noise | <id>`, stop.

---

## 4. Operation: INGEST (default job)

**Crystal-clear rules:**

1. **Read this schema** (`AGENTS.md`) and **`index.md`** before writing.  
2. Process **exactly ONE** file from `_ingest/` (oldest first unless Operator names a file).  
3. Do **not** process a second file in the same wake unless Operator explicitly says batch.  
4. Integrate into the graph (target **5–15 page touches** for a rich source; at least source page + index + log for a thin source):  
   - Create/update `source-*` for this input  
   - Update relevant `entity-*` / `concept-*` / `decision-*`  
   - Strengthen or challenge existing claims; **resolve contradictions** on the page (note old vs new)  
   - Keep pages **interlinked** with relative markdown links  
5. Update **`index.md`**: catalog entry with one-line blurb for every new page; refresh blurb if major change.  
6. Append **one** line to **`log.md`** using this parseable prefix:  
   `## [YYYY-MM-DD HH:MM] ingest | <short title> | <source-id>`  
7. **Delete only that one** file from `_ingest/`.  
8. **Stop.** If `_ingest/` still has files, leave them for the next serial job.

### Serial discipline

- One source at a time per vessel.  
- If another wiki agent session is active, do not thrash; finish or exit cleanly.  
- Never empty `_ingest/` by bulk-deleting without integrating.

---

## 5. Operation: QUERY

When asked a question against the wiki:

1. Read `index.md`, then open candidate pages.  
2. Answer with **citations** (page paths).  
3. If the answer is valuable synthesis, **offer to file** it as `pages/synthesis-*.md` and index it — so exploration compounds.

---

## 6. Operation: LINT

When asked to lint / health-check:

- Contradictions between pages  
- Stale claims superseded by newer sources  
- Orphan pages (no inbound links)  
- Concepts mentioned but lacking pages  
- Missing cross-references  
- Data gaps worth Operator sourcing  

Write findings to `pages/lint-latest.md` (replace or date-stamp section) and log:  
`## [YYYY-MM-DD HH:MM] lint | <n findings>`

---

## 7. Epistemic rules

- **Do not hallucinate.** If unsure, omit or flag `needs-source`.  
- **Structural, not a daily journal.** Encyclopedia first; chronology lives in `log.md` and `source-*`.  
- **Compound.** Prefer integrating into hubs over endless new one-off pages.  
- **Sandbox:** only write under `memory-wiki/`. No engine code, no git force, no session store mutation.  
- **Zero chitchat** when running as background daemon: no permission theater, no filler.  
- **Human-in-the-loop:** if architecture is unclear and a wrong edit would thrash lore, stop and note in log rather than invent.

---

## 8. Wake-up paste (what scripts should say)

Scripts must **not** replace this schema. A valid paste is only:

```text
Read AGENTS.md (schema) and index.md first.
Process exactly ONE file in _ingest/ per the Ingest workflow.
When that file is absorbed and deleted, stop.
```

If the paste conflicts with this schema, **this schema wins**.

---

## 9. Schema versioning

- Header: `<!-- Schema-Version: 2 -->`  
- Packaged template: `aim-agy_os/.aim_core/templates/memory_wiki_AGENTS.md`  
- Install/init/scaffold **must** seed this file when missing  
- Upgrade existing vessels only with explicit flag / Operator intent (do not silent-clobber customized schemas without version bump policy)

---

## 10. Quality checklist (before you stop)

- [ ] Would reincarnation tomorrow find this fact without re-reading the raw session?  
- [ ] Did more than one page get smarter (not only a dump page)?  
- [ ] Is `index.md` still a usable map?  
- [ ] Is `log.md` one clean line for this ingest?  
- [ ] Is `_ingest/` free of the file you processed?
