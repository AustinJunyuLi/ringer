# Ringer

Verified-swarm orchestrator. `ringer.py` is a single-file, stdlib-only Python
3.11+ CLI; `templates/` holds swarm-pattern manifest skeletons. This repo is
both a working tool and a public template others fork.

## Gotchas

- **Load the ringer skill FIRST, not after.** Any task that calls a model,
  drives a probe/smoke/eval, or runs a multi-step edit loop goes through it
  before you act — including the ones that feel too small to bother.
- **`.claude/` and `overlay/` are deliberately different editions, not copies.**
  `.claude/skills/ringer/SKILL.md` is the generic public-template edition that
  ships with the repo; `overlay/skills/ringer/SKILL.md` is the maintainer's
  personalized edition, deployed to `~/.claude/` per the README's deployment
  table. Never blind-sync one onto the other, and never backport
  operator-specific language (real engine names, ports, routing tables) into
  the `.claude/` copy.
- **No routing table lives in this repo's skill.** The canonical
  model-routing table is the operator's own (`~/.claude/rules/model-routing.md`,
  shipped as `overlay/rules/model-routing.md`). Anything here that needs
  routing points at it — copies drift.
- **Tests that spawn the CLI must set `RINGER_NO_SELF_UPDATE=1`.** Skip it
  and the suite can trigger a live self-update (`CONTRIBUTING.md`).
- **`tests/test_contributors.py` fails the ENTIRE suite over a missing
  README line.** Any merged contributor absent from the README's
  Contributors section takes down the whole run, not just that test — a
  failure mode that looks nothing like its cause (`CONTRIBUTING.md`).
- **Editing `ringer.py`? Preserve its baked-in invariants.** Listed in
  `.claude/skills/ringer/SKILL.md` under "Baked-in invariants" — that skill
  only auto-loads for orchestration work, not code edits, so it won't
  remind you here.

Orchestrator playbook: `.claude/skills/ringer/SKILL.md` (auto-loads via its
trigger description; deep dives under `.claude/skills/ringer/references/`).
