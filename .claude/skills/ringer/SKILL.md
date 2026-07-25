---
name: ringer
description: >-
  Orchestrator playbook and routing rules for Ringer, the verified-swarm
  delegation tool (ringer.py). TRIGGER — load BEFORE acting, not after —
  whenever: you are about to run ANY script or command that calls a model or
  drives a conversational/eval harness (probe, smoke test, simulation,
  grader, persona conversation) outside a live Ringer run; you are about to
  start an edit→test→edit loop or a batch of similar edits across files; you
  are about to do a "quick check" that spawns a model or a CLI agent; you are
  reviewing or diagnosing failed worker or model output; you catch yourself
  thinking a task is "small enough to just do myself" — that thought IS the
  trigger (a single task is a one-task manifest); or you are writing or
  reviewing a manifest, choosing a swarm pattern (review swarm, fix swarm,
  focus group, bakeoff, research-with-proof), picking a worker engine, or
  debugging a failed run. SKIP only for: reading or searching files, git
  operations, a one-file few-line ONE-SHOT edit (once — if you are back for a
  second pass, that is a loop: TRIGGER), authoring prose/specs/docs straight
  from your own context, or pure conversation.
---

# Ringer orchestrator playbook

## Read this first — the four rules that actually get broken

1. **You review; workers type.** Your lane: specs, checks, pattern choice,
   reading results. If you are typing implementation, running probes, or
   babysitting a retry loop yourself, you have left your lane.
2. **A single task is a one-task manifest.** Same verification, zero
   ceremony. "Too small for Ringer" is how drift starts — the smoke test,
   the probe script, the three-edit fix are all one-task manifests.
3. **Beware the tiny-edit death spiral.** The named anti-pattern: each step
   is individually small enough to justify inline, and two hours later the
   exception has become the workflow and nothing was verified or visible.
   The one-shot exception is ONE file, a few lines, ONCE. The second pass on
   the same problem is a loop, and loops are manifests.
4. **Runs are watched, not hidden — and the screen comes up FIRST.** The
   moment this skill loads for real work, before you write a single spec,
   put Ringside on the human's screen: `./ringer.py hud` (idempotent — if
   one is already up it says so and opens the page; runs also auto-start
   it). Ringside is the PAGE at http://127.0.0.1:8700 — NEVER launch the
   Ringside.app application (`open -a Ringside`); it is a parked prototype
   with a stale frontend. And never go dark: if your prep (research,
   check-writing, manifest drafting) will take more than ~30 seconds,
   tell the human in one sentence what you're doing and roughly how long
   before you start — they should be watching the empty arena and reading
   your one-liner, not wondering if anything is happening. Never pass
   `--no-dashboard` except in automated tests or when the user explicitly
   asks.

Ringer runs manifest tasks in parallel across cheap CLI workers (Codex,
OpenCode/GLM, others via config) and verifies every task by **executing a
check command** — exit 0 is the only PASS. Failed tasks are retried once
with the check's actual failure output injected into the retry prompt. You —
the orchestrating model — pay tokens only for specs, orchestration, and
review.

```bash
./ringer.py lint manifest.json            # always lint before running
./ringer.py run manifest.json --identity <who-you-are>
./ringer.py demo                          # 3-worker smoke test
./ringer.py run manifest.json --dry-run   # print the plan, spawn nothing
```

Runs land in `~/.ringer/runs/`. Raw worker logs land in `<workdir>/logs/`.
Full reference: `README.md`. Ready-made manifest skeletons: `templates/`.
Lint catches unverifiable checks, silent checks, worktree deliverable/commit
loss, serial fan-out, write collisions, and underspecified specs; `run`
prints the same findings as non-blocking warnings.

## One job, one artifact

A job the human asked for — however many rounds it takes — is ONE artifact.
Use the SAME `run_name` for every round (`sd-crate-launch`, not
`sd-crate-r1` / `sd-crate-r2`): the library accumulates each round as a
version under one entry, and the human watches one page evolve instead of
hunting across three "live" tabs. Name it after the JOB in the human's
words, not after your batch structure.

And the artifact page is where results are REVIEWED. When a round finishes,
read the deliverables from the artifact store and direct the human to the
page — never `cat` result files into the terminal as the reveal. If a result
matters, it belongs in the artifact; if it isn't there, that's a harvest gap
to fix (declare it in `expect_files`), not a reason to bypass the page.

## Deep dives — load the reference file when you hit its job

- Writing a task spec: `references/spec-writing.md`
- Writing a check command: `references/check-writing.md`
- Choosing a swarm pattern / template kit: `references/patterns.md`
  (browse `templates/README.md` alongside it)
- Picking an engine or model, and the scoreboard commands:
  `references/engine-selection.md`
- A manifest with `"worktrees": true`: `references/worktrees-footguns.md`
- A run just finished: `references/post-run-review.md`

## Baked-in invariants (preserve in any change to ringer.py)

Stdin closed (`< /dev/null`); sandbox mode explicit; verification executes
the artifact; logs carry raw worker output only. These are load-bearing —
engine and invocation changes must keep all four.
