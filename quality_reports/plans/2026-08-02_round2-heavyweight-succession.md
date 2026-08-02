# Round 2 bakeoff — Sonnet succession + Opus↔Sol interchangeability

**Status:** APPROVED (design discussed with Austin; 3 shaping choices answered)
**Date:** 2026-08-02
**Run name:** `round2-heavyweight-succession` (one artifact, all manifests)

## Goals (Austin's words, distilled)

1. Minimize Sonnet: bake it off against GPT-5.6 Terra and Luna on its old
   lanes; suspicion is Luna/Terra do the work better and cheaper (plan-wise).
2. Add Opus as a heavyweight interchangeable with GPT-5.6 Sol so the GPT and
   Claude subscriptions spread evenly; intuition: good at different shapes,
   neither totally superior. Find the must-route map.
3. Evidence over intuition throughout.

**Decisions taken:** 2b uses real ringer work + one fixture. Sonnet is
minimized NOW where matched, hard-unplugged only after a confirming round 3
(kimi precedent). Load-split rule between Opus/Sol deferred until results.

## Matrix — 3 probes + 19 cells, all plan-billed (deepseek ref = pennies)

**Round 0 (probes):** terra, luna (codex engine — identity hard-verified via
model_report_regex), opus (claude engine — identity by invocation pinning,
like sonnet historically). Probe template, generic mode.

**2a — Sonnet succession (fresh fixtures, zero round-1 contamination):**

| Scenario | task_type | Cells |
|---|---|---|
| capability research: gpt-5.6-terra + gpt-5.6-luna files (feeds registry AND this very decision) | research | sonnet · terra · deepseek(ref) |
| code-fix: fresh 2-defect fixture (rate-limiter tier ≈ round 1) | code-fix | sonnet · terra · luna · deepseek(ref) |
| docs: templates/probe/checks/probe_check.py, WITH the round-1 lesson applied (--symbol-allowlist for signature phrasings) | docs | sonnet · terra · luna · deepseek(ref) |

Luna is excluded from research on verified evidence (MRCR cliff 41%,
long-context collapse) — short-context cells only. DeepSeek reference cells
anchor fixture difficulty across rounds.

**2b — Opus vs Sol, matched high effort (`--effort high` / `model_reasoning_effort=high`):**

| Shape | task_type | What |
|---|---|---|
| code-feature (worktrees manifest) | code-feature | REAL: implement relaxed symbol-matching mode in doc-swarm's doc_check.py + tests (the round-1 check-trap fix we actually want); patch-export pattern; I review both patches, best lands |
| adversarial review | code-review | REAL: review the unreviewed local commits f21b8f0 + 75412e5 (ringer.py effort attribution + registry changes); structured findings, every cited location must exist (anti-hallucination grep) |
| diagnosis post-mortem | probe (postmortem) | REAL: root-cause the round-1 research--kimi-cli double-failure from its preserved worker.log; quotes verified against the log |
| hard code-fix | code-fix | FIXTURE: 3-defect topological-sort module (cycle detection + isolated nodes + deterministic tie-break), hash-guarded master tests |

## Mechanics

- Three manifests, same run_name: probes → main (2a + 2b non-feature) →
  feature (worktrees: true, repo ~/fleet/swarm, patch export outside).
- Checks: same craft as round 1 (print WHY, verify substance, hash-guard
  fixtures, identity grep where the engine reports the model). doc_check
  gets --symbol-allowlist this time.
- Timeouts: feature 2400s, review/research 1800s, hard-fix 1500s, others
  1200s, probes 600s. max_parallel 6.
- Registry: all five models already registered (codex: sol/terra/luna;
  claude: sonnet/opus) — no registry work needed pre-run.
- Post-run deliverables: (a) Sonnet routing verdict per lane; (b) Opus/Sol
  must-route map + the interchangeable middle (Austin decides the split
  rule on seeing it); (c) capability TOMLs for terra/luna if research
  survives review; (d) MODEL-NOTES + scoreboard rows with efforts recorded
  (f21b8f0 attribution now live).

## Success criteria

- A Sonnet lane is "matched" when a challenger's first-try equals or beats
  Sonnet's on the same fresh scenario. Matched ⇒ route away now; unplug
  doctrine waits for round 3.
- Opus/Sol: a shape belongs to a model if it wins first-try or wins on
  verified quality at equal first-try (my review of artifacts breaks ties,
  documented in MODEL-NOTES). Everything else = interchangeable middle.
