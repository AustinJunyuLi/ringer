# 2026-07-27 — Ringer reinstall on Windows (econ-phd-04)

## End state

Four lanes, all native `.exe`, all adaptive on effort:

| Lane | Binary | Effort control |
|---|---|---|
| codex | vendored `codex.exe` (not `codex.cmd`) | `-c model_reasoning_effort=…` |
| claude | `claude.exe` | `--effort …` |
| kimi | `kimi.exe` | model alias `k3-low` / `k3-high` / `k3-max` |
| mock | `python.exe` + `engines/mock_worker.py` | n/a |

Verified 5/5 PASS attempt 1, run exit 0. Qwen is off the fleet entirely.
Ringer is the default delegation path; routing words override per job.

Reproduce on another machine with `python overlay/deploy.py` — see
`overlay/DEPLOY.md`.

## Findings worth keeping

**A `.cmd` shim silently DROPS any argument containing a newline.**
CreateProcess routes `.cmd` through cmd.exe, which discards the whole
argument — no error. Probed directly with `create_subprocess_exec` and the arg
`"line one:\nPAYLOAD\nline three"`: via `.cmd` the child received `[]`; via
`.exe` it received the string intact. So a multi-line `{spec}` arrives as
*nothing* and the worker answers a truncated prompt — which reads exactly like
a model failure. Every engine `bin` is a native `.exe` for this reason.

**Checks must be `bash -c`-wrapped.** Ringer runs checks through
`create_subprocess_shell`, i.e. cmd.exe here, so POSIX check syntax dies with
`'{' is not recognized`. This is why `ringer.py demo` fails wholesale on
Windows even though its workers write their files correctly.

**`--help` is not the capability surface.** `kimi --help` exposes only
`-m/--model` and no effort flag, and I concluded from that the lane could not
do per-task effort. Wrong: the Kimi Code config docs state that entries in the
models table *are* the `-m` aliases and `default_effort` is a per-alias field,
so several aliases can point at one model with different efforts. Check the
config schema before declaring a capability absent.

**Headless Claude auth can expire while the GUI looks fine.**
`claude.exe -p` returned `Failed to authenticate: OAuth session expired`
reproducibly while the live session worked normally. An instant zero-token
failure on the claude lane means re-auth, not model trouble.

**Compare failure sets, not totals.** The suite reports 31 failed / 188 passed
on Windows. A pristine-HEAD worktree reports the identical set, so that is the
baseline, not a regression — matching this repo's non-blocking-Windows CI.

## Decisions

- Qwen purged: identity blocks, eval rows, and the leftover
  `[providers.qwen-token-plan]` in `~/.kimi-code/config.toml` (which held a
  plaintext key). Backups kept outside the repo.
- Boss is role-defined (the session model), never model-named. Fable remains a
  user-invoked red-phone advisor only.
- Effort adaptive on every lane; the routing table names models only.
- The scoreboard outranks the routing table — promoted to an explicit rule.
- `templates/bakeoff-kit` imported from upstream; the tree matches upstream on
  every shared file and `ringer.py` is byte-identical.
