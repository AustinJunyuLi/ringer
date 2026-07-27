# 2026-07-27 — Ringer reinstall (qwen-free) + routing rule deployment

## Goal

Reinstall Ringer on the Windows laptop with every backend except qwen, and
deploy the evidence-driven routing doctrine (scoreboard overrules the table)
that existed in the fork's `overlay/` but had never been installed here.

Context: Ringer was removed from this machine earlier the same day after a qwen
worker stalled. The trigger was qwen specifically — codex, kimi and claude were
never implicated — so the removal took out more than the problem warranted.

## Decisions

- **Qwen rows purged from the eval log** (user choice). 35 archived rows in,
  11 qwen rows dropped, 24 restored. The plan estimated 13/22; the real split
  is 11/24 — the earlier count keyed on `model` alone, the filter also caught
  `worker_engine`/`expected_model`/`reported_model`.
- **Ringer is the default delegation path**, routing words override per job
  (user choice). Deployed as authored in the overlay.
- **Boss stays role-defined.** The overlay routing file names Fable as boss
  throughout; that contradicts the 2026-07-25 Fable-boss retirement. Retirement
  is the newer decision and won — all boss references rewritten to "the boss
  (the session model)". Fable kept as a user-invoked red-phone advisor lane.
- **Qwen identity blocks deleted** from `registry/model-identity.toml`. They had
  been retained solely to label historical runs.jsonl rows; those rows are gone,
  so the reason went with them.
- **MODEL-NOTES qwen history KEPT** (85 mentions). It is the judgment layer
  explaining *why* qwen was dropped — deleting it invites a future session to
  re-add the lane. Purging the scoreboard input is not the same as erasing the
  reasoning.
- **Orphan `references/` removed** from the installed skill. `install-agent`
  ships the generic split edition; the personalized overlay SKILL.md is
  self-contained and links to none of them, and the fork's CLAUDE.md explicitly
  forbids mixing the two editions.

## Two harness bugs found — both Windows-permanent, neither a model failure

1. **`.cmd` shims silently drop newline-containing arguments.** Verified by
   direct probe: via `.cmd` the child got `[]`, via `.exe` the string arrived
   intact. Multi-line specs vanished entirely; codex wrote an empty file and k3
   said the prompt looked cut off — both correct on the input they got. Every
   engine `bin` is now a native `.exe`; `claude-kimi.cmd` was rewritten as
   `claude_kimi.py` run by `python.exe`. Fixed → codex and kimiclaude passed
   attempt 1.
2. **Checks must be `bash -c`-wrapped.** `create_subprocess_shell` is cmd.exe
   here, so the upstream POSIX checks die with `'{' is not recognized`. This is
   why `ringer.py demo` fails wholesale on Windows despite its workers doing
   the work correctly.

Both are documented at the top of `docs/MODEL-NOTES.md` and in the header of
`~/.config/ringer/config.toml`.

## Resolved blocker — headless OAuth

`claude.exe --model sonnet -p` was returning *"Failed to authenticate: OAuth
session expired and could not be refreshed"*, reproducible outside Ringer while
the live app session kept working. Re-auth cleared it and the lane passed
attempt 1. Lesson worth keeping: the headless CLI path can be unauthenticated
while the GUI looks healthy, so an instant zero-token failure on a Claude lane
means re-auth first. The 2 FAIL rows recorded before the fix are an auth
artifact, not evidence about Sonnet.

## State at end of session

- **5 of 5 lanes pass by executed check, all attempt 1, run exit 0**: mock
  0.1s, claude/sonnet-low 14.6s, kimi/k3 16.5s, kimiclaude/k3-low 20.4s,
  codex/luna-low 33.5s.
- Scoreboard tiers on `probe` after three sweeps (rows accumulate, so several
  lanes already cleared the 3-task bar): **proven** — Kimi K3 via kimi CLI
  (5 tasks, 80% first-try), Kimi K3 via Claude harness (4, 75%), GPT-5.6
  Luna·low (3, 67%). **Probation** — Claude Sonnet (5 tasks but 60% first-try,
  under the 0.67 bar *only* because of the two pre-re-auth FAILs, which are an
  auth artifact; discount them and the lane is clean), mock (1 task).
- 50 eval rows, 0 qwen.
- Scoreboard attributing correctly after adding `[engines.kimiclaude]` and
  `[engines.mock]` to the identity registry (was printing `k3 [unregistered]`).
- Repo is dirty and uncommitted: modified `docs/MODEL-NOTES.md`,
  `registry/model-identity.toml`; new `overlay/probes/win-lane-probe.json`,
  `quality_reports/`. Nothing pushed.

## Phase 2 — adaptive tuning + upstream sync

- **kimiclaude NOT deleted; the capability check overturned the premise.**
  `kimi --help` has no effort flag at all — effort on the native CLI lives in
  `~/.kimi-code/config.toml` (`[thinking] effort`, per-model `default_effort`),
  which is process-global and would race if mutated per task. So kimiclaude is
  the *only* per-task adaptive path to k3, and deleting it would have traded
  the adaptive lane for a fixed one plus lost the pinned 1M context. Latency
  didn't support consolidation either: the same kimi lane measured 188s and
  16.5s across two sweeps — variance, not a trend.
- **Adaptive everywhere it's possible.** Routing rule rewritten: the old
  "Codex lanes stay fixed cells" clause is gone, and every table row now names
  a MODEL only, with effort chosen per task. Added a capability table showing
  where the knob lives per lane (codex `-c model_reasoning_effort`, claude and
  kimiclaude `--effort`, kimi CLI none). Only surviving pinned-effort mention
  is the escalation ladder, where the rung *is* the effort.
- **Scoreboard-outranks-the-table promoted to an explicit rule**, not just an
  aside in the evidence-strength bullet.
- **Repo brought current with upstream.** The two repos share NO git ancestor
  (the fork is an independent repo, not a GitHub fork), so `git log
  HEAD..upstream/main` misleadingly lists ~100 commits. The real file-level
  delta on shared paths was exactly one thing: `templates/bakeoff-kit`,
  imported via `git checkout upstream/main -- templates/bakeoff-kit`. Working
  tree now matches upstream on every shared file; `ringer.py` still identical;
  17 template dirs; new kit lints clean.

## Phase 3 — kimi CLI IS adaptive (correction), qwen gone machine-wide

- **I was wrong about the kimi CLI, and the user was right.** Phase 2 concluded
  from `kimi --help` (only `-m/--model`, no effort flag) that the native lane
  could not do per-task effort. The official config docs say otherwise: *"Each
  entry in the models table defines a model alias (the name used in
  `default_model` or the `-m` flag), keyed by a unique name"* — and
  `default_effort` is a **per-alias** field. Multiple aliases can therefore
  point at one underlying model with different efforts.
- **Implemented:** `~/.kimi-code/config.toml` now defines `k3-low`, `k3-high`,
  `k3-max` — all `model = "k3"`, 1M context, differing only in
  `default_effort`. `kimi doctor` validates. Registered as three distinct
  identity cells so the scoreboard never merges them.
- **Verified through the harness:** 6/6 PASS attempt 1, run exit 0 —
  `lane-kimi-low` 18.7s, `lane-kimi-max` 19.7s, alongside mock/codex/claude/
  kimiclaude. All four lanes are now adaptive; the routing rule's capability
  table and the config header were corrected accordingly.
- **Method lesson worth keeping:** `--help` is not the capability surface. The
  flag list omitted a capability that the config schema exposes, and reading
  only `--help` produced a confident wrong conclusion that would have cost a
  lane. Check the config docs before declaring a capability absent.
- **kimiclaude still retained** — effort is no longer the differentiator, so
  the case now rests on plan metering and the pinned 1M context.
- **qwen removed from `~/.kimi-code/config.toml`**: the
  `[providers.qwen-token-plan]` block (which held a plaintext API key) and the
  `qwen-token-plan/qwen3.8-max-preview` alias. Backup at
  `config.toml.bak-preqwenremoval-20260727`. Machine-wide qwen count in live
  configs is now zero; the only remaining mentions are deliberate
  do-not-re-add notes.

## Next

- The `.cmd` finding likely contaminates earlier Windows scoreboard rows on
  codex/kimiclaude — treat pre-2026-07-27 first-try rates on those lanes as
  depressed by a harness bug, not model quality.
- Nothing committed or pushed.
