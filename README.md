# aim-joshua

Specialized **LeadDeed** A.I.M. vessel for **J.O.S.H.U.A.** (Joint Operational System for Heuristic User Automation).

True **git clone** of [aim-opencode](https://github.com/BrianV1981/aim-opencode), specialized for LeadDeed BYOK agents (OpenCode + API keys — default free model `google/gemini-3.5-flash-lite`).

| | |
|--|--|
| **Agent contract** | [`AGENTS.md`](./AGENTS.md) — read this; that is the real operating manual |
| **Spawn card** | [`VESSEL.md`](./VESSEL.md) — for aim-connect wiring |
| **Upstream pin** | [`SOURCE.md`](./SOURCE.md) |
| **Local** | `/home/kingb/aim-joshua` |
| **origin** | `BrianV1981/aim-joshua` |
| **upstream** | `BrianV1981/aim-opencode` |

```bash
cd /home/kingb/aim-joshua
export GEMINI_API_KEY='…'   # never commit
opencode run --pure -m google/gemini-3.5-flash-lite "hello"

# optional vessel upgrades (review first)
git fetch upstream && git log HEAD..upstream/main --oneline
```

Gateway: **aim-connect**. Product monorepo: **aim-ld**. Full A.I.M. CLI: `./aim` after `bash aim-agy_os/setup.sh`.
