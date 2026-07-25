# SOURCE.md — Vessel & soul pins

| Field | Value |
|-------|--------|
| **Vessel** | `aim-joshua` |
| **Product** | LeadDeed / J.O.S.H.U.A. |
| **Runtime** | OpenCode CLI |
| **Created** | 2026-07-24 |

## Clone base (this repo IS a clone of aim-opencode)

| Field | Value |
|-------|--------|
| **Cloned from** | https://github.com/BrianV1981/aim-opencode |
| **Clone point** | `1e6962d` (main at seed time) |
| **Remote `upstream`** | `BrianV1981/aim-opencode` — pull vessel upgrades from here |
| **Remote `origin`** | `BrianV1981/aim-joshua` — this specialized vessel |

```bash
# Pull selected vessel upgrades
git fetch upstream
git log HEAD..upstream/main --oneline   # review
# merge or cherry-pick deliberately; never blind overwrite AGENTS.md / README.md
```

## Soul (A.I.M. engine)

| Field | Value |
|-------|--------|
| **Soul lineage** | aim-agy via nested `aim-agy_os/` (same as aim-opencode) |
| **Upgrade** | Prefer soul lockstep policies from the fleet; then re-test free Gemini via OpenCode |

## Intentional product overlays (protect when merging upstream)

| Path | Why |
|------|-----|
| `AGENTS.md` | JOSHUA + LeadDeed contract |
| `README.md` | Product vessel story |
| `SOURCE.md` | This pin |
| `VESSEL.md` | aim-connect spawn card |
| `opencode.jsonc` | Default `google/gemini-3.5-flash-lite` |
| `VERSION` / `CHANGELOG.md` | Joshua version line |

## History note

Earlier rsync-only seed (`d96a069`) was replaced by a **true git clone** of aim-opencode, then product identity commits on top.
