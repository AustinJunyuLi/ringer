# 2026-07-28 — Force local Ringer config to conform to AustinJunyuLi/ringer

## Goal

User: "force the local config to conform with the remote one, full install."
Their 2026-07-27 work (retire kimiclaude, make every lane adaptive) was on
GitHub but had never reached this machine.

## Why it was invisible at first

`~/fleet/swarm` was wired to **upstream** `NateBJones-Projects/ringer` only.
The user's own repo `AustinJunyuLi/ringer` was not a remote, so every fetch
came back clean. It is an *independent* repo, not a GitHub fork — no shared
history with upstream. Found it via `gh repo list`.

The three commits: `736ef1d` (retire kimiclaude, adaptive lanes),
`d9a9ee5` (session log), `559e1f2` (remove kimiclaude entirely + deploy path).

## Blocker: git transfer stalls

`git ls-remote` returns instantly, but `fetch` and even a fresh
`clone --depth 1` hang in `git-upload-pack` negotiation and time out (240s+).
Repo is only 6.4 MB, so it is not size. Cause is the zero shared history
between the two repos — negotiation loops.

**Workaround that worked:** `gh api repos/.../tarball/main` — one request,
instant, no negotiation. Use this whenever git transport misbehaves but `gh`
works.

## Key constraint found by reading deploy.py before running it

`overlay/deploy.py` bakes its own `REPO` path into the generated config (the
`mock` engine's `bin` points at `<repo>/engines/mock_worker.py`). Running it
from a scratchpad would have written a temp path that later gets wiped. So
the tree had to be placed at its permanent home *first*.

## What was done

1. Backed up local state to scratchpad `ringer-backup/`: uncommitted diff,
   the `local-overlay` commit as a patch, old `config.toml`, old
   `model-routing.md`.
2. `~/fleet/swarm` → `~/fleet/swarm.upstream-old` (preserved, not deleted).
3. Tarball tree extracted to `~/fleet/swarm` (commit `559e1f2`).
4. `overlay/test_deploy.py` → both platform branches generate valid TOML.
5. `overlay/deploy.py --check` → all 4 lanes resolve; then real deploy.
   Every overwritten file got a `.bak-20260727T180516Z` sibling.
6. `ringer.py install-agent`; `ringer.py db rebuild` → 408 attempts, 0 skipped.
   Existing `runs.jsonl` was **not** reseeded (deploy skips a non-empty log).
7. `ringer.py run overlay/probes/lane-probe.json` → **5/5 PASS, first attempt**
   (mock, codex-luna, claude-sonnet, kimi k3-low, kimi k3-max).

## The mechanism that replaced kimiclaude

The native Kimi CLI has no `--effort` flag, which was the original reason
kimiclaude existed. deploy.py adds `k3-low` / `k3-high` / `k3-max` blocks to
`~/.kimi-code/config.toml` — Kimi Code's `[models."…"]` keys *are* the `-m`
aliases and `default_effort` is per-alias, so three aliases over one
underlying `k3` make effort a per-task choice carried by `{model_args}`.
Both ends verified live in the probe.

Do NOT tune this lane via the global `[thinking] effort` — shared state,
races under parallel runs.

## Open items

- `~/fleet/swarm` has no `.git` yet; a full clone was still running at
  `~/fleet/swarm.forkclone`. Attach its `.git` to make a proper checkout
  (working tree already equals `main` tip, so it lands clean).
- `~/fleet/swarm.upstream-old` holds an unpushed `local-overlay` commit
  (+196 lines to MODEL-NOTES / model-identity) plus uncommitted MODEL-NOTES
  edits. The fork's MODEL-NOTES is now live, so those are **orphaned** —
  decide what, if anything, needs porting.
- Upstream `NateBJones-Projects` is no longer a remote of the live repo.
  Re-add it if upstream commits are still wanted (last pull brought
  `2c2b599`, the bakeoff-kit templates).
