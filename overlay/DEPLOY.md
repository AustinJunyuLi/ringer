# Deploying this setup to another machine

Reproduces the operator's exact Ringer state — four lanes, adaptive effort on
every one, the routing table, the orchestrator skill, and the eval history the
scoreboard reads. Works on Windows and macOS/Linux.

## Prerequisites

Python 3.11+, git, and each CLI installed **and authenticated**. The deploy
script resolves their paths for you; it cannot log you in.

| Lane | Install | Authenticate |
|---|---|---|
| codex | `npm i -g @openai/codex` | `codex login` (needs a plan with Codex CLI access) |
| claude | Claude Code | `claude login` |
| kimi | Kimi Code CLI | `kimi login` (needs a Kimi Code membership) |
| mock | — | none; local, free, no network |

`grok` and `opencode` are not wired. On macOS the `opencode` lane *can* work —
its sandbox wrapper is Seatbelt — if you add an OpenRouter key; see
`overlay/config/config.toml.example`.

## Deploy

```bash
git clone https://github.com/AustinJunyuLi/ringer ~/fleet/swarm
cd ~/fleet/swarm
python overlay/test_deploy.py     # sanity-check the generator first
python overlay/deploy.py --check  # dry run: shows resolved paths, writes nothing
python overlay/deploy.py          # do it
```

Then, still from the repo root:

```bash
python ringer.py install-agent    # Claude Code skill + nudge hooks
python ringer.py db rebuild       # build the scoreboard from the seeded log
```

`deploy.py` writes `~/.config/ringer/config.toml`, adds the `k3-low` /
`k3-high` / `k3-max` aliases to `~/.kimi-code/config.toml`, installs
`~/.claude/rules/model-routing.md` and `~/.claude/skills/ringer/SKILL.md`, and
seeds `~/.ringer/runs.jsonl`. Every file it replaces is backed up first with a
UTC timestamp. It is idempotent — re-run it after pulling.

## Acceptance test — not optional

```bash
python ringer.py run overlay/probes/lane-probe.json
```

**5/5 PASS, exit 0, or the deployment is not done.** A lane is not installed
until an executed check has passed on it; a config that merely parses proves
nothing. If a lane fails, read `~/.ringer/runs/<run_id>.json` — the worker log
and the check's own output are both in there — before concluding anything about
the model.

Then confirm the scoreboard reads:

```bash
python ringer.py models
```

## Platform differences the script handles

**Windows.** Engine `bin` must be a native `.exe`. CreateProcess routes `.cmd`
through cmd.exe, which **drops any argument containing a newline** — a
multi-line spec arrives as nothing, silently, and the worker answers a
truncated prompt that looks like a model failure. `deploy.py` therefore hunts
for codex's vendored `codex.exe` instead of the `codex.cmd` on PATH. Checks
also run through cmd.exe, so they must be wrapped as `bash -c '...'`.

**macOS / Linux.** Neither trap applies: PATH entries are shebang scripts or
symlinks and argv survives, and checks run through `/bin/sh` where POSIX syntax
works natively. `which()` is authoritative for every lane. The shared probe
manifest still wraps its checks in `bash -c` so a single manifest runs on both
machines — harmless here, required there.

## What is NOT copied

Credentials. Each machine authenticates its own CLIs; no key, token, or OAuth
session is in this repo, and none should ever be added.

## Keeping two machines in sync

The generated config is derived, not hand-tuned — edit `overlay/deploy.py` and
re-run rather than editing `~/.config/ringer/config.toml` in place, or the two
machines drift. Same for the routing table and skill: edit the copies under
`overlay/`, commit, pull on the other machine, re-run `deploy.py`.

Eval rows accumulate per machine. `overlay/state/runs.seed.jsonl` is a seed,
not a sync — if you want the scoreboards merged, concatenate the two logs and
`db rebuild`; rows are independent JSON objects and order does not matter.

**The seed is deliberately partial.** It carries only `probe` and `bakeoff`
rows — harness evidence, safe to publish. Rows from real work are withheld,
because an eval row embeds the worker's full spec, and a research spec can
carry unpublished findings, dataset sizes, and project paths. This repo is
public; `runs.jsonl` is in `.gitignore` for exactly this reason and should stay
there. To move your real eval history between machines, copy
`~/.ringer/runs.jsonl` directly over a private channel and `db rebuild` — never
through this repo.
