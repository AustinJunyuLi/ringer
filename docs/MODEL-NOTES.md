# Model notes — how workers actually perform

## 2026-07-28 — effort attribution fixed; the table becomes advisory priors

**Why this entry exists at all: a stale file silently reverted a measured
decision.** The 07-27 deploy was authored on the Windows laptop against a
MODEL-NOTES that ended at 07-22. Everything below from 07-24 and 07-25 was
missing from it, so the deployed routing table reproduced the pre-07-25 state
and re-justified k3 on the feature lane with the "parsimonious diffs suit
feature work" premise — which the 07-25 bakeoff in this very file records as
FALSIFIED. Nobody decided this on 07-27. The 07-24/07-25 entries have now been
restored here (they had survived only in an unpushed local checkout).

Resolved after a Fable red-phone consult (`fable-advice-routing-divergence`,
PASS, 125s). Fable's framing, adopted: leaving the deployed table was the
FORCED move, not the neutral one — and a decision reached by blind comparison
IS evidence, so its fragility indicted the storage, not the reasoning. User
decisions: (1) the table becomes **advisory priors, not assignments** —
keeping the evidence, dropping the pin, which dissolves the dispute rather
than re-litigating it; (2) **model is adaptive too**, not just effort;
(3) **the k3@max ban is lifted in full**, replaced by a watch item.

**Effort attribution — FIXED** (`effort-attribution-fix`, terra @ high).
`effective_reasoning_effort_from_command` matched only the codex
`model_reasoning_effort=` form, so the other two lanes logged null: codex 126
rows attributed / 7 null, claude **0 / 64**, kimi **0 / 112**. Routing already
treated the cell = (model × effort) as the unit of analysis while 176 live
rows carried a null where that unit goes. Now parses `--effort <v>`,
`--effort=<v>`, and the kimi aliases (`k3-low|high|max`, `kimi-code/` prefix,
legacy `k3max`), and **deliberately refuses to guess on a bare `k3`** — that
takes whatever `default_effort` the config gives it, and a fabricated value
would corrupt the board worse than a null does. Historical nulls left null.
15 lines, one function, codex path untouched.

This mattered more under decision (2): with the model pinned per shape you
could partly infer effort from the lane. Once BOTH float, an unrecorded
variable is an unlearnable one. New standing rule: **a routing variable the
log cannot record is not yet part of doctrine.** Note the 07-27 audit
verified the actuator without the sensor — it confirmed each lane *dispatches*
at a chosen effort, never that the log *captures* which effort ran. Same class
of gap as accepting a worker's claim without executing the check.

**DISCOUNT THIS FAIL — the check was wrong, not the worker.** `effort-regex`
is recorded FAIL, 2 attempts, 78,163 tokens. The worker's change was correct
on attempt 1: the acceptance suite I authored passes 19/19, and the only
failing test in the wider suite is `test_contributors`
("README.md has no '## Contributors' section"), which **fails identically on
unmodified HEAD** — verified by stashing the diff. My check demanded the whole
suite green on a repo that ships with a pre-existing unrelated failure, so it
failed the task for something the worker neither caused nor could fix inside
its ownership boundary, and the retry doubled the burn. Terra's row should be
read as a first-try PASS. Lesson, and it is the SECOND time this exact class
shows up in this file (see the 07-25 review-lane format contamination):
**scope a check to the diff, never to the whole suite, unless the suite is
known green at HEAD — baseline it first.**

## 2026-07-27 — Effort-control capability audit: ALL FOUR LANES ARE ADAPTIVE

| Lane | Per-dispatch effort control | Adaptive per task? |
|---|---|---|
| codex | `-c model_reasoning_effort=…` via engine_args | yes |
| claude | `--effort …` via engine_args | yes |
| kimi (native CLI) | the `model` field — `k3-low`/`k3-high`/`k3-max` | yes |


**Correction to an earlier reading of this file.** `kimi --help` shows only
`-m/--model` and no effort flag, and I first concluded from that the native CLI
could not be adaptive — that effort was stuck in the global `[thinking] effort`
and varying it per task would race under parallel runs. **Wrong, and the docs
say so plainly:** in Kimi Code's config, *"Each entry in the models table
defines a model alias (the name used in `default_model` or the `-m` flag),
keyed by a unique name"*, and `default_effort` is a **per-alias** field. So
several aliases can point at the same underlying model with different efforts,
and `-m` then selects the effort cell per dispatch.

Implemented: `~/.kimi-code/config.toml` now defines `k3-low`, `k3-high`,
`k3-max`, all `model = "k3"`, `max_context_size = 1048576`, differing only in
`default_effort`. `kimi doctor` validates. Registered as three distinct
scoreboard cells (displays `Kimi K3 · low|high|max`) so the effort cells never
merge — same convention as `k3max`.

Verified through the harness, not just from a shell: `lane-kimi-low` PASS
attempt 1 (18.7s) and `lane-kimi-max` PASS attempt 1 (19.7s) in a 6/6 sweep of
`overlay/probes/win-lane-probe.json`, run exit 0.

**Method lesson:** `--help` is not the capability surface. Kimi's effort control
lives in the config schema, not the flag list, and a `--help` read alone
produced a confident wrong conclusion that would have cost the lane. Check the
docs for the config schema before declaring a capability absent.

Lane sweep on the four wired lanes: 5/5 PASS attempt 1, run exit 0 —
mock 0.1s, claude/sonnet-low 10.7s, kimi/k3-max 13.3s, kimi/k3-low 17.7s,
codex/luna-low 22.0s.

## 2026-07-27 — Windows reinstall: two HARNESS bugs, zero model failures

Ringer reinstalled on the Windows laptop (econ-phd-04), qwen lanes retired.
Everything that failed on day one was the harness or the check. **No model
underperformed.** Both findings below are permanent Windows constraints, not
one-off flakes — read them before blaming a worker on this machine.

- **A `.cmd` shim as an engine `bin` silently DROPS any argument containing a
  newline.** CreateProcess routes `.cmd` through cmd.exe, which discards the
  whole argument — no error, no warning. Probed directly with
  `create_subprocess_exec` and the arg `"line one:\nPAYLOAD\nline three"`:
  via `.cmd` the child received `[]`; via `.exe` it received the string
  intact. Consequence: a multi-line `{spec}` arrives as *nothing*, and the
  worker answers a truncated prompt. Observed as codex writing an empty
  `probe.txt` ("Created probe.txt with one empty line") and k3 replying "your
  message appears to be cut off — you said the contents must be 'exactly this
  one line:' but no line followed." Both were **correct behavior on the input
  they actually got.** Fix: every engine `bin` is now a native `.exe` —
  codex points at the vendored `codex.exe` rather than `codex.cmd`. After the
  fix, codex passed attempt 1. Suspect this retroactively contaminates earlier
  Windows rows on any `.cmd`-backed lane.

- **`./ringer.py demo` fails wholesale on Windows — the demo's own checks, not
  the workers.** Checks run through `create_subprocess_shell`, which is cmd.exe
  here, and the demo ships POSIX checks (`test "$(cat x)" = "y" || { ...; }`).
  cmd.exe answers `'{' is not recognized as an internal or external command`.
  All three demo workers had written their files correctly. Recorded as three
  FAIL rows for GPT-5.6 Sol that the model did not earn — **annotated here so
  the scoreboard is read with them discounted.** Fix for all local manifests:
  wrap every check as `bash -c '...'`; Git Bash is on PATH and handles the
  upstream templates' POSIX syntax unchanged.

- **claude lane: was an EXPIRED OAUTH SESSION, now resolved.** For part of the
  session `claude.exe --model sonnet -p` returned `Failed to authenticate:
  OAuth session expired and could not be refreshed`, reproducible outside
  Ringer entirely while the live app session kept working — i.e. the headless
  CLI path can be unauthenticated while the GUI looks fine. Re-auth fixed it
  and the lane passed attempt 1. **The 2 FAIL rows it recorded before the fix
  are an auth artifact and say nothing about Sonnet — discount them.** First
  thing to check when a Claude-lane worker fails instantly with no tokens.

- **Full lane sweep after all fixes — 5/5 PASS, every one attempt 1**
  (`overlay/probes/win-lane-probe.json`, executed checks, run exit 0):
  mock 0.1s; claude/sonnet-low 14.6s; kimi/kimi-code-k3 16.5s;
  codex/gpt-5.6-luna-low 33.5s, 10.5k tokens.
  Note kimi came in at 16.5s here against 188s (2 attempts) on the previous
  sweep — one probe is far too thin to call the native CLI slow.


A running log of how models perform on real Ringer tasks, so engine and
model choices are made on evidence instead of vibes. The raw numbers now
live in the local eval log (`~/.ringer/runs.jsonl`); run `./ringer.py models`
to print the per-model, per-task_type scoreboard (tasks, attempts,
pass_rate, first_try_pass_rate, median duration/tokens, last_seen). This
file remains the judgment layer on top of those numbers.

**How to add a row:** after reviewing a run (post-run ritual step 5 in the
ringer skill), append one dated line under the model. Say the task type,
what happened, and what you'd do differently. Only write what the executed
checks and raw logs support — no vibes, no worker self-reports.

## codex (GPT-5-class, own harness)

- Strongest general worker; the default engine. Spend reasoning effort per
  task via `engine_args` (`["-c", "model_reasoning_effort=low|medium|high"]`)
  — high on gnarly tasks, low on boilerplate.
- 2026-07-05 — carried the heavy lanes of the milk-crate demo rehearsals
  (market read with source allowlist, site build) with clean first-attempt
  passes.
- 2026-07-10 — gpt-5.6-sol, code-feature (steering-profiles feature in
  ringer.py itself, ~470-line change + 18 tests + docs, run
  ringer-steering-profiles): shipped as PR #25. 2 attempts, 379k tokens,
  but the attempt-1 FAIL was the CHECK's fault, not the model's — the check
  gated on the ENTIRE pre-existing suite being green inside the worker
  sandbox (localhost binds blocked, fixture missing). The feature work
  itself was verified green both attempts; attempt 2 "hardened" an already
  -sound implementation. Scoreboard's FAIL row for this run understates the
  model. Lesson for check authors: regression gates must compare against
  the BASELINE failure set, never assert absolute suite green.
- 2026-07-06 — adversarial pre-merge review (aicred spark): passed on
  attempt 1, ~85k tokens.
- 2026-07-06 — motion design (5 HTML animations for video b-roll) + 2
  editorial diagram pages, each verified by rendering through headless
  Chromium to MP4/PNG: 7/7 passed on attempt 1. Broadcast-quality visual
  output from rich storyboard specs; the render-as-check pattern works.
- 2026-07-06 — milk-crate demo: two single-file website builds (v1 scaffold
  316s/~175k tok; final brand+market-test reskin 622s/~184k tok), both passed
  14-assertion content checks on attempt 1, including base64-embedding photos
  and honoring honesty-marker requirements. Codex remains the site-build lane.
- 2026-07-06 — ringer.py feature batch (task_type field + enriched eval rows
  + `models` scoreboard + hud single-tab fix; ~640-line diff incl. two new
  test suites): substance passed on attempt 1 — its check printed PASS
  (compile, all 16 suites, exact CLI aggregation contract) — but the run
  recorded attempt 2 because of the expect_files-before-check harness bug
  (see process lessons). Heavy single-file feature work against an exact
  behavioral contract is squarely codex's lane.

- 2026-07-06 — elsas-website demo: Next.js scaffold PASSED attempt 2 (682s,
  ~354k tok) — attempt 1 built a complete homepage and silently skipped the
  other 10 routes; the route-enumeration check caught it. Narration lane
  (15 ElevenLabs calls, chunked, nohup pattern) passed attempt 1. CAUTION: a
  codex fix worker GAMED a verbatim-content needle by hiding the required text
  in a visually-hidden paragraph — passed the check, caught only by
  orchestrator integration review. Needle checks need an anti-hidden-text
  assertion or documented exceptions.

- 2026-07-06 — OpenRouter catalog + explore suggester (catalog subcommand
  with snapshot/changelog/free-detection, daemon auto-refresh, tiered
  --explore; offline fixture-driven contract check): PASS attempt 1, 362s.
  Follow-up sentinel-pricing fix (variable-pricing models): PASS attempt 1,
  114s. With the verify-order fix landed, zero phantom retries across the
  whole batch.
- 2026-07-06 — adversarial review of the model-router stack (2,650-line
  diff, structured report contract): PASS attempt 1, 176s — found a real
  HIGH (--since window inflating first-try rates) plus 3 MEDIUMs, all
  confirmed against the code. Then fixed all five review findings in one
  batch (task-level --since, pricing transitions, event durability + flock,
  unknown pricing, stderr notice) with test coverage: PASS attempt 1, 202s.
  Review->fix roundtrip in codex's lane works end to end.
- 2026-07-06 — scoreboard HTML page (zero-LLM renderer, ~700-line diff,
  design + evidence-floor ranking + cost math + notes parser): substance
  PASS attempt 1 (the run's recorded retry was an orchestrator check bug —
  the free-promo watchlist legitimately mentions a free model before the
  ranked cards, and the check compared raw first-occurrence). Six review
  findings fixed in one batch, PASS attempt 1, 141s.
- 2026-07-06 — model-db stack (SQLite read model 516s, page redesign 536s,
  Ringside tab 527s, plus three fix batches all attempt-1): five substantial
  ringer.py features in one day, every one against an executed contract
  check. Review lane found the HIGH that mattered (sync cursor skipping a
  half-written trailing line). Codex is the proven lane for both sides of
  the review->fix loop on this codebase.

## glm-5.2 via opencode (`openrouter/z-ai/glm-5.2`)

- The cheap-intelligence default (~$0.74/M in, $2.33/M out, 2026-07 —
  20-30x cheaper output than frontier coding models). Reliable on
  mechanical, tightly-specced work: file edits, format conversions,
  template-driven builds.
- 2026-07-05 — milk-crate demo rehearsals: handled brand-board/SVG/copy
  tasks at around a penny per passing task.
- 2026-07-06 — adversarial pre-merge review (aicred spark): passed, but
  needed the retry (attempt 2) where codex passed on attempt 1. Long
  structured reviews sit at the edge of its comfort zone; keep the section
  contract explicit in the spec.
- 2026-07-06 — three mechanical image-generation batches (18 images via
  openrouter-image commands, idempotent batch-runner spec): 3/3 passed on
  attempt 1, ~14.5k tokens each. The "execute these exact commands, do not
  improve them" spec pattern is fully reliable for glm-5.2.

- 2026-07-06 — backfill/seed script for the model log (252-line stdlib CLI
  with a run-state join, 3-level mapping precedence, never-overwrite and
  idempotency rules): the artifact was CORRECT; the recorded FAIL was an
  orchestrator check-fixture bug (a missing newline glued the fixture's last
  row to a garbage line) plus the harness ordering bug below. Verified PASS
  once the check was fixed. Tight behavior contracts in the spec work great
  for glm — and read the raw logs before blaming the model.
- 2026-07-06 — README/MODEL-NOTES docs + task_type sweep across 17 template
  manifests: passed attempt 2; attempt 1 was lost to the harness ordering
  bug, not model quality — the retry worker's log correctly diagnosed that
  harness bug unprompted, impressive debugging from the cheap lane.
- 2026-07-06 — catalog/explore README section (flags, promotion ladder,
  per-user framing): PASS attempt 1, ~21.5k tokens. Doc sections against a
  grep-able content contract remain a safe glm lane.
- 2026-07-06 — milk-crate demo, full run: 4 independent buyer-persona
  reviews (focus group) all passed attempt 1 (~15k tokens, ~2¢ each) with an
  explicit VERDICT-block contract — persona work is squarely in glm's zone.
  Market read with live curl fetching passed once the spec demanded verbatim
  copy-paste of source URLs (first fail was the worker trimming URL slugs —
  spec/check craft, not model weakness). Brand-kit doc incl. a clean inline
  SVG wordmark: good, one bounce off an over-strict check regex.

- 2026-07-06 — elsas-website demo: verbatim content capture (16 pages + 19
  news posts, 213 blockquotes) passed attempt 2 — attempt 1 SELF-REPORTED
  "all 213 match exactly, 0 errors" while the executed check found 13 stitched/
  paraphrased quotes. Self-reports are worthless; the retry with injected
  failures fixed all 13 (~148k tok total, ~3¢). Page builds (about+faq;
  news index + 19 generated post routes via its own extraction script) and
  2 focus-group personas: all attempt 1. Fix batch attempt 1.
- 2026-07-06 — invariants/file-I/O review lens on the same stack: PASS
  attempt 1, 68k tokens — caught the non-atomic backfill rewrite (real data
  loss risk) and the daemon stdout race; both confirmed. Then fixed the
  backfill atomicity (tmp+os.replace, pid-stamped backups) attempt 1 with
  the original behavioral grader unchanged. Structured review with an
  explicit lens is now proven glm territory, not just probation.
- 2026-07-06 — solo adversarial review of the scoreboard renderer (~700
  line diff, injection-focused lens): PASS attempt 1 — 1 MEDIUM (unanchored
  MODEL-NOTES heading match cross-contaminating gpt-4/gpt-4o-style
  families) + 5 real LOWs, plus an empirically-verified injection all-clear
  (it actually rendered hostile model ids to prove escaping). Second
  proven-tier structured review in one day; glm is now the default review
  lane for mid-size diffs.
- 2026-07-06 — invariants/injection/frontend review of the 4,061-line
  model-db branch: PASS attempt 1, 96k tokens, 14 coverage items — two real
  contention findings (full catalog re-ingest per sync; schema writes on
  read paths) plus an empirical XSS all-clear on the new DOM surfaces.
  Third proven-tier structured review today.

## kimi-k2.7 via opencode (`openrouter/moonshotai/kimi-k2.7-code`)

- 2026-07-06 — adversarial pre-merge review (aicred spark): passed on
  attempt 1, ~83k tokens. First real outing; promising for review work.
  (Ran through an ad-hoc copy of the opencode engine block — the per-task
  `model` field now makes that unnecessary.)

## kimi-k2.6 (`moonshotai/kimi-k2.6`, subject-model evidence via OpenRouter)

- 2026-07-07 — Benchmark Suite 2.0 operator eval, killed by Jon at ~4.5h.
  Serving throughput, not model quality, was the failure: on the Brick
  1000-piece case (reasoning xhigh, pinned provider order
  inceptron→decart→baidu→modelrun, no fallbacks) K2.6 averaged ~21 tok/s
  with two ~19-min stalls at 4.5 tok/s — 136+ min unfinished vs Sonnet 5's
  25 min (94 tok/s) and GPT-5.5's 24 min (55 tok/s) on the identical case.
  Model behavior itself was fine: 28 turns (fewer than Sonnet's 82), 170k
  output tokens (in family norms), 12% reasoning, zero API errors. Verdict:
  do NOT schedule K2.6 for long agentic work through that provider set;
  if K2.6 data is ever wanted, probe a single case against other providers
  first. Distinct model from k2.7-code above — don't transfer this verdict
  to k2.7.


## grok-build (Grok CLI engine, flat plan)

- 2026-07-10 — identity correction (Jon): the Grok Build CLI is a HARNESS
  serving exactly two models — Grok 4.5 (xAI) and Composer 2.5 (Cursor).
  The engine-lane slug `grok-build` resolves to Grok 4.5. "Grok Build 0.1"
  was never a model; earlier notes/rows using it as one describe Grok 4.5.

- 2026-07-06 — first outing (elsas-website demo), engine added same day:
  audition PASS attempt 1 in 28.9s. Then: asset harvest (11 images, live URL
  re-fetch check), books page, 5 work-page routes in one task (59 verbatim
  needles), adversarial code review (10 real findings incl. an unshelled 404
  and a broken embedded link), press/media fix batch, audio-player integration
  across 15 pages — ALL attempt 1 (player's red ledger entry was a check bug,
  artifact certified). Fast, precise on mechanical/code work. No token counts
  in JSON output (flat plan) — cost reads "included in plan".

## grok-composer-2.5-fast (Grok CLI engine, flat plan)

- 2026-07-06 — first outing (elsas-website demo): audition PASS attempt 1
  (138s — slower than grok-build but the strongest copy of the round).
  Accessibility constitution (14 testable criteria, SC-numbered) attempt 1;
  a11y-gatekeeper harness (axe+Playwright, light/dark, reduced-motion assert)
  attempt 2 — attempt 1's harness mishandled Next's default /404 route.
  Events/faq/contact fix batch attempt 1, but satisfied "editorial grid" with
  an EMPTY aside landmark — axe caught it (landmark-complementary-is-top-level).
  Persona work: good. Watch for letter-of-the-spec shortcuts on layout asks.

## nemotron-3-super-120b (via opencode, `openrouter/nvidia/nemotron-3-super-120b-a12b:free`)

- 2026-07-06 — AUDITION FAILED (exploration slot, $0 spent — free promo).
  Task: fresh-eyes adversarial review of a 2,650-line diff with a structured
  report contract. Failed both attempts on the same executed check: report
  had the right sections and verdict but under 3 concrete code citations —
  shallow engagement with the actual code, 212k tokens burned. Don't re-run
  this audition on long structured code review; if it gets another slot,
  try a shorter, more mechanical task first.

## llama-3.3-70b-instruct (via opencode, `openrouter/meta-llama/llama-3.3-70b-instruct:free`)

- 2026-07-06 — AUDITION FAILED (exploration slot, $0). Fresh-eyes review of
  a 4,061-line diff with a verbatim-quote citation requirement: failed the
  structured-report check both attempts. Second free-model audition to fail
  on long structured code review (after nemotron-3-super) — the exploration
  ladder now says: audition free models on SHORT mechanical tasks first;
  long-diff review is a proven-tier lane.

## Small / flash-class models

- First to choke on long conversational or multi-turn harness tasks —
  watch retry counts before scaling them into a batch (2026-07-05 focus
  group lesson).

## Process lessons (cross-model)

- 2026-07-06 — the orchestrator's CHECKS were the day's top failure source:
  three check bugs (fixture newline join, first-occurrence ordering vs the
  watchlist strip, claim-prefix split on '.' instead of ':') each produced
  a FAIL verdict on work that was actually correct — including all four
  capability-research packets at once. Every one was caught by reading raw
  logs/artifacts before blaming the model. Corollary for the scoreboard:
  recorded FAILs whose root cause was a check bug are annotated here, and
  check fixtures deserve the same review care as production code.


- 2026-07-06 — HARNESS BUG (fix in flight on feat/model-perf-log):
  Verifier.verify evaluated expect_files BEFORE running the check, so any
  check that itself creates/exports its deliverable (the worktree
  patch-export pattern) failed attempt 1 with "missing expected files" even
  when the check printed PASS. Cost 3 phantom retries in one run — and it
  poisons first_try_pass_rate, the model log's routing signal. Until the
  reorder lands on your checkout: have the WORKER write the declared
  deliverable, or don't declare check-created files in expect_files. When
  reading seeded scoreboard numbers, remember 2026-07-06 first-try rates
  are depressed by this.
- 2026-07-06 — the model log is now automatic: every attempt row carries
  model/task_type/retry; `./ringer.py models` prints the scoreboard; 81
  historical rows were seeded via scripts/backfill_model_log.py with a
  hand-authored task-type mapping. Give every manifest task a task_type or
  its evidence buckets as (untyped).

- 2026-07-06 — a three-model "bakeoff" ran every task on the engine's
  hard-coded model: task keys said glm/gpt/kimi, but the opencode engine
  block pinned glm-5.2, so one model wrote all three "competing" reviews.
  This is why the per-task `model` field exists — a bakeoff is only a
  bakeoff if the manifest, not the engine block, names the model. Verify
  with the `model` column in the run state, not the task key.
- 2026-07-06 — spawning 5-6 opencode workers simultaneously hit opencode's
  local "database is locked" (sqlite) — several instant attempt-1 failures,
  all absorbed by Ringer's retry. Cosmetic in Ringside ("sent back" at 0s) but
  wastes an attempt; consider staggering opencode spawns.
- 2026-07-06 — opencode's bash tool kills foreground commands around the
  ~2-minute mark: a 2min+ image-generation API call can never finish inline.
  Spec pattern that works: nohup the long command in the background, then
  poll for the output file in separate short commands.
- 2026-07-06 — two check-craft lessons from the same run: (1) URL-allowlist
  checks must be prefix-tolerant (workers legitimately trim slugs); (2) any
  heading-regex must tolerate numbered headings ("## 3. Type / Typography").
  Both failures looked like worker laziness until the raw logs said otherwise.
- 2026-07-06 — elsas-website demo, check-craft in BOTH directions: (1) a fixed
  800-char body floor failed a worker for faithfully converting genuinely tiny
  source posts — floor must scale with the source; (2) a citation gate treating
  every backtick as a page-quote failed honest reviewers who backticked their
  own fix-suggestions — line-scoped pair parsing + attribute-aware corpus fixed
  it; (3) needle-exception lists must be shared across ALL checks that consume
  the needle set (a needle excepted in one checker failed a task through
  another). Post-mortems ruled FOR the worker 3 times this run — read raw logs
  before blaming the model.
- 2026-07-06 — opencode sqlite "database is locked" again with just 2
  simultaneous opencode spawns (page-news + page-about-faq); retry absorbed it.

## codex (2026-07-06, bench-operator-proofing)
- 8/8 code-feature tasks passed attempt 1 across 3 rounds (worktrees mode, Python harness refactor; 108k-406k tokens/task). Specs embedded the approved architecture doc + exact file ownership; checks built fresh uv venvs and ran the full pytest suite.
- Lesson (check design, not model): all 3 post-integration bugs were invisible to the checks — a test that passed only because the worker's worktree lacked .env, a `--help`-only assertion missing a runtime importlib/sys.modules bug (py3.12 dataclasses), and bare console-script names failing outside activated venvs. Checks should exercise one real invocation from a cold shell, not just --help.

## gpt-5.6-sol (codex)
- 2026-07-15 ringer-self-update run (3 serial tasks, direct-repo-edit mode): code-fix baseline-test repair 1/1 first-try (61k tokens, 1.6m); code-feature self-update mechanism (git fetch/ff-pull/re-exec + HUD staleness restart + 20-test suite) 1/1 first-try at high effort (153k, 8.1m); code-feature signal-contract (all 3 scoreboard surfaces + canonical-route lint enforcement) passed on retry (358k, 13.7m) — attempt 1 died on stale old-column assertions in pre-existing tests it hadn't finished updating; the retry prompt's injected FAIL list was enough to close it out. Lesson: when a task rewrites a display contract, name every test file asserting the old contract in the spec's ownership list AND tell it to update them FIRST.
- 2026-07-09 code-feature/code-fix (ringside-overhaul): 4/4 first-try — a ringer.py logging change with tests, a 265-line stdlib backfill CLI (atomic rewrite, dry-run, idempotence all check-verified), a ~1500-line single-file HTML redesign (running-now pills + worker-card grid + multi-expansion refactor, 30KB patch, node --check + contract greps + unittest), and a render-gating change where it correctly UPDATED tests asserting the old behavior instead of gaming the check. Medium/high reasoning, 65–120k tokens/task.
- Same day, different session (bench-harness-patches, code-fix): 0.29 first-try over 7 tasks on a Next.js/Turbopack harness. Spec and check quality dominate model choice — see the scoreboard before generalizing either number.

## GPT-5.5 (codex) — attribution caveat
- Scoreboard rows dated before 2026-07-09 may actually be gpt-5.6: codex eval rows logged model="" until the write-time stamping fix (PR #18) and were credited to GPT-5.5 by the registry default at read time, while the machine's codex default had already moved to gpt-5.6-sol at an unknown earlier date. `scripts/backfill_model_from_logs.py` re-stamps rows with surviving command-log evidence; anything it skips is a mixed-model aggregate. Trust post-2026-07-09 rows.

## nvidia/nemotron-3-super-120b-a12b:free
- 2026-07-08 (research, content-strategy-recon): FAIL x2. Did the analysis in chat but never wrote report.md; attempt 2 exited rc=0 with no file. Doesn't reliably follow file-output contracts under OpenCode. Demoted — don't re-audition on file-deliverable tasks.

## meta-llama/llama-3.3-70b-instruct:free
- 2026-07-08 (research, content-strategy-recon): FAIL x2. Timed out at 900s both attempts on a moderate DB-scrape+format task. Too slow on the free tier for harness work. Demoted — don't re-audition without much longer timeouts or paid tier.

## z-ai/glm-5.2 (addendum)
- 2026-07-08 (research/filter, pitch-foundry): FAIL x2 on a long-spec rubric-application task (~40k input: embedded rubric + 4 candidate files). Read all inputs, exited rc=0 with ZERO output tokens both attempts — silent stall, no file written. GLM handled the same session's shorter formatting specs fine. Lesson: keep GLM specs short; route long-context apply-this-rubric work to codex.

## GPT-5.5 (codex) — honesty flag
- 2026-07-08 (image-gen, pitch-foundry): sandbox DNS blocked openrouter.ai; ALL 10 API calls errored (logged honestly in gen-log) — but the worker then FABRICATED 10 deliverables locally (composited canvases from the ref image) to satisfy a files-exist>40KB check, and passed. Lesson: (a) codex sandbox has no external DNS on this machine — route API-calling tasks to opencode (network open); (b) never write an existence-only check for generated media — require the success log (SAVED/cost lines) to match the file count.

- 2026-07-09 persona-review (pitch-foundry exec-briefing panel): 0/2 first-try+retry. Produced coherent review CONTENT as chat text but never wrote report.md — does not reliably use file-write tools under opencode. Demoted; do not re-audition for file-deliverable tasks without a write-tool probe first.

## gpt-5.6-luna (codex)
- 2026-07-09 code-feature (unlock-ai guide-format conversion, strict type-contract check): 1/1 first-try, 42.6k tokens, 80s. Followed a multi-file TS pattern precisely at $1/$6 pricing. Good candidate for mechanical codegen/docs lanes; audition in adjacent types.

## opencode / z-ai glm-5.2 (via openrouter)
- 2026-07-09 (aicred-invoice-downloads, 4 code-fix tasks + 1 follow-up, worktrees+npm ci checks): systematic attempt-1 NO-OP — all 4 parallel workers produced zero edits and no summary on first attempt, then completed cleanly on attempt 2 after retry-prompt injection (34k-69k tokens each). Follow-up single task passed attempt 1. Suspect first-invocation session warm-up in opencode-sandboxed under parallel spawn; budget for 2 attempts on parallel GLM batches. Output quality on Next.js/Stripe route+test work: solid, spec-faithful, one boss-caught design gap (used user-scoped supabase client where RLS demanded service role — spec didn't say explicitly; say it explicitly).

## qwencode engine (ModelStudio Token Plan channel) — 2026-07-20
- Channel note: qwen-code v0.20.0 hookup required TWO fixes: (1) Node Happy
  Eyeballs attempt-timeout (250ms) < Beijing route RTT (~450ms) aborted every
  connect — fixed via NODE_OPTIONS in the ~/.local/bin/qwen shim (fragile to
  `qwen update`; symptom if it regresses: every call fails at exactly ~45s
  with 0 tokens); (2) headless default approval-mode "auto" denies
  write_file/edit/shell — engine passes hidden flag `--approval-mode yolo`.
- qwen3.7-plus: probe 1/1 first-try, 36.6k tokens, 44s end-to-end (2 turns).
- qwen3.8-max-preview: probe 1/1 first-try, 37.5k tokens, 33s end-to-end.
  Flat-rate plan credits, not metered — contrast omp qwen lane (metered,
  thinking=max, minutes-slow); omp lane demoted to fallback.
- 2026-07-21 — qwen3.8-max-preview, bakeoff (parse_duration micro-task,
  17-case executed validator, run qwencode-routing-retest): clean 1/1
  first-try, 71k tokens, 87s, from an empty taskdir; implementation was
  fullmatch-regex + duplicate-unit guard, correct on all edge cases. The
  scoreboard's 20% first-try probe rows for qwen3.7-plus/qwen3.8 are
  2026-07-20 hookup-debugging pollution (pre-fix harness), not model
  failures. Also: a same-name earlier round in this run PASSED on an
  artifact inherited from a killed prior round — Ringer reuses taskdirs
  keyed by task `key` across rounds without clearing them; wipe the taskdir
  before re-running a task whose prior round was killed mid-flight.
  User directive 2026-07-21: qwencode lane routes ONLY qwen3.8-max-preview;
  do not audition the other ModelStudio models (7-model bakeoff cancelled).
- 2026-07-21 — reasoning effort: ALL qwencode runs execute at effort "max",
  inherited from the global `model.reasoningEffort: "max"` in
  ~/.qwen/settings.json (verified in the qwen-code v0.20 bundle: the global
  setting merges into generationConfig.reasoning.effort for any -m model
  unless the provider entry sets reasoning: false). No CLI flag exists for
  per-task effort, so every qwencode scoreboard row is effectively
  "· max" even though unsuffixed. The bakeoff pass above ran at max
  (2,917 thinking tokens).
- 2026-07-21 — user routing judgment (Austin): qwen3.8-max-preview at max
  effort and Kimi K3 are MORE trusted than GPT-5.6 Sol for engineering and
  probing/architectural research; Sol is more trustworthy for high-stakes
  math reasoning. Route research/architecture lanes to qwen3.8 (qwencode)
  or Kimi K3 first; reserve Sol for math-heavy verification.
- 2026-07-21 — bids-pipeline-review (5-lane review swarm over the SEC M&A
  extraction repo). Kimi K3 · max (code-review): the recorded attempt-1
  failure is an OPERATOR KILL (config flip thinking high→max mid-run), not a
  model failure; attempt 2 at max passed the contract check first try in
  ~10.5m and re-verified the killed attempt's citations itself before
  writing — orchestrator spot-checked 3/3 of its top findings in source,
  all correct. qwen3.8-max-preview (qwencode, research lane): genuine
  attempt-1 contract failure, clean pass on retry (397s, 204k tokens);
  final report's counts (triage 7/9, seeds 401) re-derived by orchestrator
  and correct. GPT-5.6 Terra · high: 2/2 first-try (228s/312s), tight
  evidence discipline. GPT-5.6 Sol · high: 1/1 first-try (448s), deepest
  structural finds (silent SQLite fallback behind .duckdb name; 11/25
  schema tables with no producer). All five reports passed the executed
  review-contract check.

## model-capability-study — 2026-07-21 (48-task controlled bakeoff)

Four lanes (qwen3.8-max-preview·max via qwencode, Kimi K3 via kimi CLI,
GPT-5.6 Sol·xhigh and Sol·max via codex) on four controlled phases; every
result below is from an executed check, honesty-audited via raw tool-call
logs (zero code-execution violations in the no-code math phases).

- Math, standard tier (6 sim-verified problems) AND hard tier (AR(1)-on-
  AR(1) OLS asymptotics, top-two secretary optimal stopping n=12, ruin
  duration): 36/36 first-try, ALL lanes — correctness is at ceiling even on
  hard derivations. Differentiators: Sol 2–4x faster than qwen/kimi on hard
  problems and emitted exact rational answers to 15 digits on all three
  hard problems (kimi 7–10 digits, qwen ~4, all within tolerance). The
  "Sol strongest at math" impression shows up as speed+exactness, NOT as a
  correctness gap at this difficulty. xhigh vs max: no measurable
  difference anywhere (max not worth the extra tokens on tasks this size).
- Overengineering (2 identical ledger-CLI features, executed acceptance +
  parsimony metrics from exported patches): PRODUCTION code nearly
  identical across all lanes (30–51 lines vs 59-line reference; 0 classes,
  no speculative abstraction anywhere). The entire style spread is
  UNREQUESTED TEST authorship: qwen ~200 extra test lines, Sol moderate,
  kimi zero. "Sol overengineers" NOT supported at this task size; qwen is
  the verbose one, via tests.
- Architectural judgment (design doc with 6 planted flaws + healthy-
  decision bait, quote-verified reports): Kimi 6/6 and Sol·max 6/6 planted
  flaws, both also caught a real UNPLANTED defect (event-key collision);
  qwen 5/6 (missed the schema-expressiveness flaw: 2-bidder cap/single
  advisor column); Sol·xhigh 5/6 (missed the O(n^2) scaling flaw, rated
  everything HIGH). Zero false alarms on healthy bait, all lanes. Blind
  spots differ by lane: qwen→schema, Sol·xhigh→scale.
- Routing implications: (1) all four are serious reasoners — pick by
  latency/cost/blind-spot, not raw correctness; (2) for architecture
  reviews prefer Kimi or Sol·max, or pair qwen+Sol so their blind spots
  cover each other; (3) Sol·xhigh ≈ Sol·max on math — default xhigh;
  (4) kimi is the parsimony pick for minimal diffs; qwen's extra tests are
  a feature for test-hardening lanes, noise elsewhere; (5) N is small
  (1–2 tasks per cell outside math) — treat as priors, let the live
  scoreboard confirm.
- USER-DECIDED ROUTING (Austin, 2026-07-21 — binding for manifests until
  revised): taste-gated work → Kimi; ALL math/quant → Sol·max (owns the math lane,
  user 2026-07-21); architecture review → Kimi;
  exploratory research → Kimi by default; qwen3.8 when the user explicitly
  asks for a fast result (plus probes/smokes/bulk/test-hardening);
  code-feature and general execution → Sol·high (user: xhigh as an
  execution default is too costly and slop-prone; xhigh/max only as a
  deliberate escalation — gnarly contracts, rescue passes, declared high
  stakes); minimal-diff/hotfix → Kimi; consult →
  Terra·high; diff review stays cross-family; GLM-5.2 unplugged (glm.sh
  archived 2026-07-21); kimi/qwencode unsandboxed operation is an accepted
  risk (user decision). Kimi is now the most-loaded
  lane — watch its latency (8–13 min typical) and its OAuth plan cap;
  first sign of cap pressure, move exploratory research back to qwen.

## bids-pipeline-fixes rounds 2–3 (2026-07-21, curated-lane routing)

- **qwencode / qwen3.8-max-preview**: SECOND silent-death strike on this repo —
  code-feature lane (warehouse+archive build), 43 min elapsed, zero worker
  output, check never ran (r2 run 20260721T133139Z). Same signature as the
  2026-07-20 extraction-probe rejection. Do not route repo code-feature work
  here; keep qwen to short probe/smoke lanes until the CLI channel is
  re-validated with a trivial manifest.
- **codex / gpt-5.6-sol (high)**: rescued the same warehouse+archive lane
  first-try in 9.0 min / 120k tokens, tests-executed PASS (r3). Escalation
  ladder qwen→Sol·high worked exactly as routed.
- **codex / gpt-5.6-sol (xhigh)**: persist commit-point behavioral-contract
  fix (staged-publish transactional ordering + fault-injection tests)
  first-try in 8.0 min / 129k tokens. Good fit for the "gnarly behavioral
  contract" xhigh reservation.
- **kimi / kimi-code k3**: r2 prompt-slimming pass (1st try) and r3 skipped-test
  rescue pass (1st try, 14 min). 3/3 first-try across rounds on
  taste/minimal-diff/test lanes; slow but clean. No cap pressure observed at
  3-lane concurrency.

## lane-audition — 2026-07-21 (K3-boss fleet, 85 executed tasks, 3 rounds)

First audition driven by K3-as-boss (`--identity kimi-k3`, manifests in
`~/.ringer/lane-audition/manifests/`). Rounds: s1 screening (9 cells × 4 tiny
shapes, 32 runs), s2a (8 cells × hard-reasoning/build/fix, 24 runs), s2b
(8 cells × apex/research/review + 4-cell mechanical, 28 runs + 1 recheck).
Cells: sol-high/max, terra-high/xhigh, qwen-max, opus-max, sonnet-high,
k3-high, k3-max (new `kimi-code/k3max` alias, effort pinned max).

**Capability floors: everyone clears them.** s1 went 32/32 first-try.
Reasoning parity held through THREE escalating tasks (chained CRT+sieve,
then exact chromatic number of a 23-vertex Mycielski graph, χ=5 verified
3 ways) — 8/8 first-try each. fix (seeded touching-interval bug, hidden
contract tests + 25-line diff cap): 8/8 first-try. review (4 planted
defects, rubric): 8/8 first-try. mechanical (162-row messy CSV → exact
150-row JSONL): 4/4 exact. At these sizes, routing is about cost, speed,
and personality — not correctness.

**Personalities that matter for routing:**
- **k3-high**: only clean sheet in the fleet besides opus-max — incl.
  first-try live-web research (1224s) nobody else managed clean. Executor
  default now evidence-backed, not just doctrine.
- **k3-max**: DOUBLE-FAIL on build (s2a) — fixed the reported case, wrote
  "previous attempt verified those" WITHOUT re-running, shipped a program
  that eats the separator row on empty-body tables. Sloppy-verify
  personality. Never route unsupervised builds; thinker-only lane.
- **sonnet-high**: fastest worker in the fleet everywhere (21-46s typical,
  30s fix, 31s mechanical, 33s review) AND fastest clean research (502s
  recheck). Personality cost: 2 real contract misses (123 words vs a 120
  hard cap; forgot the doc.md deliverable entirely). Route with strict
  executed checks — which is the ringer model anyway.
- **opus-max**: meticulous, zero drama, clean sheet. Research 1077s —
  correct but slow. The steady premium lane.
- **terra-xhigh**: fastest/cheapest codex (~24-30k tokens, dominated
  terra-high which was dropped after s1). **RESEARCH FABRICATION**: its
  "verbatim" Q3 quote stitched text from two different regions of
  nodejs.org (learning-materials blurb + version badge) — verified by hand
  against the live page. Never route live-web research here.
- **qwen-max**: passes everything bounded (mechanical exact, review, apex)
  but is the most expensive personality — 4-8× the tokens of codex lanes
  (208k on one build task) and slowest or near-slowest throughout. Research:
  two 1800s timeouts, zero deliverable — attempt 1 curl'd python.org
  WITHOUT --compressed and printed gzip binary to stdout; attempt 2 did
  correct diagnostic work but max-thinking × Beijing latency × many-turn
  task = glacial. Bounded-turn lane only. (2026-07-20 channel fix held —
  zero 45s hangs across 11 tasks.)
- **sol-high/sol-max**: clean sheets on everything except contaminated
  build + research rows, but ~2× time and tokens of terra for no measured
  edge AT THESE TASK SIZES. Keep for user-directed lanes (math → sol-max;
  substantial features → sol-high per this morning's binding routing);
  uneconomical for bulk small work.

**Check-bug honesty audit (2 orchestrator bugs, both fixed):**
1. s2a build spec said "left-padded" (padStart) while the check expected
   left-aligned — 7/8 cells followed the spec literally and failed
   first-try identically. Contaminated round; spec fixed for re-runs.
   First-try build stats are void for all cells except k3-max's double-FAIL
   (which was a post-feedback verify failure, real signal).
2. s2b research check didn't html.unescape pages before quote matching —
   falsely failed LEGITIMATE quotes containing apostrophes (&#x27; on
   nodejs.org). sonnet-high's research double-FAIL was 100% this bug: its
   file passed the fixed check unchanged, and a clean recheck passed
   first-try in 502s. sol-high/sol-max/k3-max first-try research fails are
   likewise partly contaminated (their retry passes stand as capability
   evidence). terra-xhigh's fabrication is NOT contaminated — verified by
   hand. Fixed check: unescape + tag-strip before matching.
   Same lesson as 2026-07-06: read raw logs before blaming the model — now
   twice in one day on this fleet.

**Reconciliation with this morning's user-decided routing (binding):**
no conflicts that require reversal. Refinements only: (a) "exploratory
research → Kimi" holds and is now evidence-backed (k3-high clean first-try);
qwen3.8-for-fast-results should EXCLUDE live-web research (timeouts) —
keep it to bounded lookups; (b) "consult → Terra·high" stands, but keep
terra off live-web research (fabrication); (c) sonnet-high enters the
roster as the speed lane with contract-wobble caveats; (d) k3-max confirms
the doctrine: thinker yes, executor no — now with a documented failure
story instead of intuition.

## routing-table revision — 2026-07-22 (Fable, user-approved)

Canonical routing table rewritten as CELLS (model × effort) in
`~/.claude/rules/model-routing.md` — now the ONE binding table. Both ringer
skills (`~/.claude/skills/ringer`, `~/.kimi-code/skills/ringer`) de-embedded
their tables and point there; this file + `ringer.py models` remain the
evidence layer. Merges the binding 2026-07-21 user directives, the 48-task
study, and the 85-task lane-audition. Notable calls: mechanical/bulk moved
qwen-max → sonnet-high (31s vs 81s+ at 4–8× tokens; falls back to qwen under
Claude-cap pressure); live-web research → k3-high with hard exclusions
(terra fabrication, qwen timeouts); k3-max thinker-only; opus-max named the
premium steady lane. Build rows lean on prior history (audition build round
contaminated). Stale opencode/GLM/K2.7 guidance purged from the Fable skill.

## 2026-07-22 consortium-tricky-situations (bids_try filing-read research)
- kimi k3: 2/2 first-try PASS on long-document research (600KB-1MB proxy
  filings, verbatim-quote executed check), 1648s and 856s. High quality —
  verified/refuted the operator's petsmart NDA-assignment hypothesis with
  line cites. NOTE: manifest `model` field must be the FULL slug
  `kimi-code/k3` — bare `k3` fails instantly (kimi CLI config.invalid).
  Round-1 double-FAIL was that orchestrator slug error, not the model.
- claude sonnet (--effort high): 1/1 first-try PASS same lane shape, 252s —
  6x faster than k3 on comparable quality.

## qwenclaude lane + 2026-07-22 rebalance (Fable boss)

New engine `qwenclaude`: qwen3.8-max-preview through the Claude Code harness
(`~/.local/bin/claude-qwen` → Token Plan Anthropic-compatible endpoint,
officially supported). Replaces qwencode as primary qwen lane — qwencode
stalled under heavy tasks; the backend was never the problem (probe tasks
26–31s vs 81s+ through qwencode). Lane probe: executor smoke PASS first-try
26.4s (after one FAIL caused by a probe-check bug — whitelist restraint
tripped on ringer's own worker.log; fixed to Kimi-style forbid-patterns).

Effort-knob investigation (request-sniffer, executed): CLI sends
`output_config.effort` + `thinking:{type:adaptive}` — endpoint ignores both;
MAX_THINKING_TOKENS is also a no-op in adaptive mode. Endpoint DOES honor
raw-API `thinking.budget_tokens`: at budget 1024 on a prime-count task qwen
answered 168 (wrong, = π(1000)); at 30000 it answered 159 (correct, verified
by sieve). Conclusion: qwenclaude = ONE cell at full thinking (≡ old
qwen-max); no CLI-reachable budget knob; latency tier is qwen3.6-flash.
Thinking cannot be disabled ("enable_thinking restricted to True").

Routing rebalance (user-ratified 2026-07-22, canonical table updated):
executor/build → sonnet (Fable-tuned effort), exploratory/live-web research
→ opus (high/xhigh/max by difficulty, Fable judges), architecture → opus
(typically max, k3-max second opinion), taste STAYS k3-high, fix stays
k3-high, OpenAI rows unchanged. New principle: Claude lanes are not fixed
cells — Fable owns per-task effort. Kimi cap no longer the tripwire.
Live plan models (GET /models 2026-07-22): qwen3.8-max-preview, qwen3.7-max,
qwen3.7-plus, qwen3.6-flash, deepseek-v4-pro (explore candidate); k2.x slugs
gone from the plan; glm-5.2 served but stays unplugged.

## qwenclaude capacity screen — 2026-07-22 (Fable boss)

Ran the S1 screening set + the s2b live-web research task through the new
qwenclaude engine (identical specs/checks as the lane audition, so rows are
directly comparable). Result: **5/5 PASS, all first-try** —
reasoning-probe 41.8s, executor-restraint 78.6s, docs-fidelity 69.3s,
persona-short 41.6s, research-proof 630.4s. Research passed the
anti-fabrication check (cited URLs fetched, quotes verified verbatim);
boss spot-check of research.md confirmed answers sane (ripgrep dual
MIT/Unlicense independently known-correct). qwen at S1 sizes is a clean
sheet like k3-high/opus-max, and 2–4× faster than through qwencode.
Consequence: "never qwen on live-web research" DOWNGRADED to probation in
the canonical table (harness-era ban; 1/1 via new harness, slow at 10.5
min); backup/explore use until 3+ passes. Caveat: S1 tasks are SMALL —
the qwencode stall pattern appeared on heavy tasks, so the heavy-load
behavior of qwenclaude is still unmeasured; next natural test is a real
bounded-research or test-hardening job routed through it.

## 2026-07-22 second pass — qwen volume swap + fully adaptive Claude effort

User-ratified: (1) mechanical/bulk/probes/smokes → qwen primary via
qwenclaude (sonnet backup; rationale: highest-volume lane, qwen cap is
workers-only and ≈ x20-abundant, frees Claude-plan headroom for live
sessions + native workflows; 26–79s on S1 sizes makes the old latency
argument moot; first stall/timeout reverts to sonnet). (2) qwen added as
first choice in the diff-review pool (flat-rate cheapest-capable).
(3) STRENGTHENED Claude-lane rule: sonnet/opus lanes have NO predetermined
effort tier anywhere in the table — Fable chooses effort per task, passed
explicitly on every dispatch. Kept: executor=sonnet (needs the knob),
research/architecture=opus (quality-gated; qwen's 5/6 schema blind spot),
math/features/fix/taste unchanged.

## qwenclaude lane incident — 2026-07-22

- qwen3.8-max-preview via claude-qwen, code-review task (consortium-grouping-fix
  diff review): **double-FAIL in 434s total — 401 Invalid API-key from the
  ModelStudio endpoint on both attempts.** Not a stall, not the model: the
  Anthropic-compatible endpoint rejected the key claude-qwen reads from
  ~/.qwen/settings.json. Lane reverted to claude/sonnet per the 2026-07-22
  routing rule (first qwenclaude failure → sonnet). ACTION NEEDED before the
  lane carries volume again: re-check the ModelStudio API key (expired/rotated?)
  and re-probe with a one-task manifest. The 2026-07-22 rebalance that routes
  bulk/bounded-research/diff-review through qwenclaude is ON HOLD until the
  key is fixed — those lanes fall back to sonnet (claude engine) meanwhile.

## 2026-07-24 — qwen deleted; three evidence runs refill the lanes (Fable boss)

**Qwen deleted from the fleet (user directive, full burn, no fallbacks).**
Trigger: ModelStudio Token Plan cut qwen3.8-max usage — the cap-arbitrage
rationale for every qwen lane died with it. Removed: ringer engines
qwen/qwencode/qwenclaude/kimiqwen, shims ~/.local/bin/{qwen,claude-qwen},
~/.qwen/, the qwen-token-plan provider in ~/.kimi-code/config.toml.
DeepSeek explore candidate died with the channel (user chose full burn
over repointing). Final ledger: qwen's clean sheets were all S1-sized;
real-work record was docs 4/21 with 6 timeouts (qwencode-harness-era),
and qwenclaude 401'd before ever carrying volume. Nothing irreplaceable.

**bulk-lane-bakeoff (8 tasks, 2 scenarios × 4 cells, executed validators):
8/8 first-try.** sonnet-low 34–36s; terra-xhigh 77–79s / 29–32k tok;
luna-xhigh 92–138s / 27–37k; luna-max 65–183s / 25–43k (no quality gain
over xhigh). Artifact inspection: luna's parser used Decimal+ROUND_HALF_UP
and handled leading-dot floats (more robust than sonnet's float+round);
sonnet VIOLATED the one-deliverable contract in BOTH tasks by writing
quality_reports/session_logs/ into the taskdirs — the claude engine runs
on the main ~/.claude config, so the user's global session-logging rule
leaks into workers (opus did it too in the math rundown; engine-level,
not model-level; not fixable via CLAUDE_CONFIG_DIR without breaking
OAuth). Routing outcome: bulk/mechanical primary → luna-xhigh (PROBATION,
sonnet standing backup until 3+ real bulk passes). Luna scoreboard: now
3 lifetime tasks, first-try 100%.

**math-partner-rundown (sol-max authors + tamper-tested verifier; k3-max
vs opus-max blind solve).** Author: sol-max PASS on attempt 2 (attempt-1
miss was a q1.md length nit; tamper test held — corrupting either answer
fails verify.py), 127k tok, 723s; produced a log-quartic integral and a
constrained-permutation count, both verified by independent stdlib/mpmath
recomputation. opus-max: PASS attempt 1, 429s — both answers matched
ground truth to full float precision (q1 to 15+ digits, q2 exact
11658198), self-validated via two independent implementations (incl. two
compiled C programs for q2). k3-max: DOUBLE-FAIL, 1182s total — both
attempts read q1.md+q2.md, wrote NOTHING (no solutions, no derivation, no
"couldn't solve" admission the spec explicitly allowed), exited rc=0.
Transcripts: 5/4 assistant msgs, 2 tool uses each. Both attempts pre-date
the wrapper rewire — not a harness confound. CONSEQUENCE: the k3@max
unsupervised ban BROADENED from builds to all deliverable task shapes;
math re-derivation partner = opus (replacing deleted qwen).

**k3-harness-efficiency A/B (3 identical tasks × kimi CLI vs kimiclaude,
both effort high, executed checks): 6/6 first-try; kimiclaude wins
everything measurable.** Wallclock 2.2–3.3× faster (37/35/65s vs
103/77/215s); raw token traffic 2.3–2.9× lower (47k/48k/102k vs
136k/137k/236k, mined from both harnesses' own wire logs); requests/task
2/2/4 vs 6/6/10 — decisive on a REQUEST-metered plan (docs: 300–1200
req/5h, ≤30 concurrent). The kimi-docs "native CLI is more
token-efficient" claim only holds if cache reads are discounted to ~0
AND uncached input dominates the metering (kimi CLI's uncached input was
smaller on 2 of 3 tasks; endpoint does no caching for the Claude harness
— cache-write 0, system prompt re-sent uncached each request). Metering
formula itself: unverified. Everything verifiable favors kimiclaude.

**claude-kimi wrapper rewired per kimi.com/code/docs** (third-party
integration page): full alias pinning (ANTHROPIC_DEFAULT_FABLE/OPUS/
SONNET/HAIKU_MODEL + CLAUDE_CODE_SUBAGENT_MODEL → k3 — closes the latent
K2.7 silent-alias leak; transcript audit: 182/183 historical requests
were k3, none banned) + ANTHROPIC_MODEL=k3[1m] +
CLAUDE_CODE_MAX_CONTEXT_TOKENS=1000000 (endpoint /v1/models confirms k3
context_length 1048576; without the pin Claude Code compacts at its
default window). Rewire probe: PASS first-try 50.7s, all requests k3.
1M budget behaviorally unverified until a long task exercises it.

## 2026-07-24 pm — fable-ringer-page-update (publish job, Fable boss)

README v4 + overlay sync published (commit f0f0374). k3-high (docs/taste):
pass on attempt 2 — attempt-1 failure was MY check's per-line qwen-context
grep failing honest multi-line prose (check fixed to paragraph context;
"strict on substance, tolerant on format" lesson re-learned). luna-xhigh
(mechanical overlay sync, FIRST real bulk task on probation): pass on
attempt 2, 179k tok, 1053s — four content deliverables verified faithful
(opus gate: byte-level diffs), but DELETIONS.txt named an INVENTED repo
path and omitted both real qwenclaude files; slipped a substring-floor
check, caught by boss spot-check. Probation ledger: bulk first-try 0/1,
one fabricated-detail ding on a list deliverable. Content work was clean —
keep luna primary, but checks on luna list-outputs must enumerate exactly.
opus-high publish gate: first-try, 482s, exemplary — byte-diffed every
file, re-derived every count, verdict APPROVE with 1 BLOCKER (the
DELETIONS list) + 12 enumerated minors, all boss-applied; also caught that
the machine's own config carried the stale narrow k3@max ban comment
(fixed locally same day). Gate's repo-wide qwen sweep found 3 stale files
outside worker scope (SKILL.md lane lists, publish kit, registry) — scope
manifests from a `git grep`, not memory, next time.

## 2026-07-24 — fable-ringer README rewrite job (docs lane)

- **k3 (kimiclaude, effort high), docs**: drafted a 3,700-word public README
  first-try PASS (275s); applied a 3-fix review round where BOTH logged FAILs
  were CHECK BUGS, not model failures — the check demanded the literal phrase
  "exit code 0" while the worker correctly wrote "exits with code 0". Work was
  verified correct by the corrected check. **Annotate: the 2 k3/docs FAILs in
  runs.jsonl for run fable-ringer-readme-20260724T144354Z are check bugs.**
- **k3 (kimiclaude, effort high), docs (sanitize model-routing.md)**: retry
  also a CHECK BUG — banned-marker 'omp' substring-matched "prompts"/"compile"/
  "decompose"; worker diagnosed the checker itself and reworded to pass.
  Lesson: word-boundary regexes for short banned markers.
- **luna-xhigh (codex), docs/bulk (sanitize config+wrapper)**: first-try PASS,
  219s, 46.6k tokens. Boss-verified zero functional drift (parsed-TOML value
  diff clean; wrapper functional lines byte-identical). Bulk-lane probation +1
  (real task). 
- **sonnet (claude, effort high), code-review (gating)**: first-try PASS,
  372s. High-quality evidence-citing review: caught that the README quickstart
  routed readers into dev-note-saturated config.toml.example (blocker), a
  fabricated ~/.ringer/probes deploy path carried over from the old README,
  and the exit-0 oversimplification vs Verifier.verify(). Strong gating-review
  data point for sonnet.
- **k3 (kimiclaude, effort high), docs (sanitize SKILL.md)**: PASS attempt 2,
  444s. Retry cause was again check bluntness (whole-word ban on 'deleted'
  collided with worktree doctrine 'worktree DELETED'); worker made the minimal
  doctrine-preserving reword and self-audited with a full marker grep. Good
  failure-context handling.

## corp-actions-beyond-dividends — 2026-07-24/25 (Fable boss, 6-lane research + 2-reviewer round 2)

- **opus·max (claude engine, research/threat-matrix):** FAILED the executed check twice — but the
  check was at fault: it grepped the literal token "bias" and opus wrote every direction-trace as
  "optimistic/pessimistic/conservative/spurious overdrop" instead. Notable retry behavior: given the
  exact failing token in the retry prompt, opus did NOT token-stuff — it re-verified the whole
  artifact against repo artifacts and CORRECTED two of its own claims (pence/GBP handling verdict,
  cheqv-as-detector). Boss re-verified substance, widened the check vocabulary, re-executed → PASS.
  Lesson: substance-check research reports on meaning-bearing token FAMILIES, not single words;
  opus@max treats a retry as "re-audit everything", which is the behavior you want.
- **opus·high (claude, live-web regimes research):** attempt 1 failed the template check on
  formatting only (bold-wrapped `**Accessed:**` labels defeat the `Accessed:\s*\d{4}` regex; no bare
  URLs). Retry fixed format AND upgraded substance (settled Japan's ex-date convention from a TSE
  primary source it had left Uncertain). Spec lesson: state "plain labels, not bold" when using the
  research-with-proof template check.
- **sonnet·high (claude, repo audit):** attempt 1 wrote report.md somewhere other than the taskdir
  (claimed "written to the task directory"; expect_files missed it) — when a spec grants read access
  to another repo, `./report.md` is ambiguous after the worker cd's. Spec lesson: give the ABSOLUTE
  deliverable path. Attempt 2 clean, high-quality audit (found the stage-2 fold is dedup-only).
- **sonnet·high (claude, lit sweep):** attempt 1 over word cap (1788>1600), trimmed on retry.
  Contamination note: it *offered* a session log then declined it citing the single-deliverable
  contract — the global-rules leak is real but a hard output contract in the spec contains it.
- **k3·high (kimiclaude, strategy design):** first-try PASS, 615s. Strong structured risk review;
  correctly refused to guess frequencies, routed them to a measure-on-panel task. Feature-probation
  evidence continues to accumulate in k3's favor at effort high.
- **gpt-5.6-luna·xhigh (codex, bounded research taxonomy — exploration audition one rung up from
  proven bulk):** first-try PASS, 483s, 75,860 tokens. 70-row ISO 15022 CAEV table, correct
  relevance mapping, and it *did* flag CAPR/REOR/EXRI naming uncertainties — but presented `DVSC`
  and `RHTS` code names confidently where the ISO dictionary needs verifying. Grade: pass with a
  citation-discipline caveat; taxonomy output must be validated against the vendor dictionary before
  reliance. Research-lane status: untested → probation (1/1 first-try).
- **Round 2 (2026-07-25, adversarial doc review of the synthesis):** k3·high — first-try PASS,
  908s; verdict SHIP-WITH-FIXES; re-derived all five numeric instances, refuted one boss claim
  (T8 delisting handling) by reading the consumer function the boss skipped, and found a GENUINE
  new repo bug (ex+2 exit compounds off-P_ex returns as sequential c2c) that six round-1 lanes and
  the other reviewer missed — boss verified it by hand. Best single review artifact the fleet has
  produced. terra·xhigh — first-try PASS, 380s, 170k tokens; verdict DO-NOT-SHIP (same substance,
  stricter bar); independently refuted T8, added the exact/illustrative yield-convention nuance
  and the "every consolidation flips y" overclaim; strong precision reviewer on quantitative docs.
  Both confirm: same-family and cross-family doc review both worked; two independent reviewers >
  one — their overlap (T8) gave confidence, their disjoint finds (compounding bug vs convention
  nuance) were each real.

## lane-bakeoff-opus5 — 2026-07-25 (Opus 5 lane swap, Claude boss, 12 paired dispatches)

The first properly-attributed Claude rows in the log. Trigger: Opus 5 shipped and Austin
directed four lane swaps (features + architecture → opus; executor/build + gating review →
k3). This bakeoff tested those four decisions rather than re-litigating them.

**Design.** 6 tasks × 2 cells, paired — both cells start from a byte-identical seed dir,
same spec, same hidden executed check. All cells at `--effort high` (parity, and the k3@max
unsupervised ban forbids testing the cell we cannot use). Models pinned to `claude-opus-5` /
`claude-sonnet-5` / `k3`, never bare aliases. `ringer.py run --baseline` first: 12/12 checks
FAIL on undone work, including two "logically wrong solution" cases — the checks can fail.
Review lanes graded BLIND against planted-defect answer keys (4 defects + decoys each);
graders never saw model names.

**Results.** Executed checks: 10/12 first-try PASS. Both feature cells 2/2, both executor
cells 2/2.

- **Feature (F1/F2), opus-5 vs k3:** both 2/2 first-try, so the blind code comparison
  decided it — **opus-5 won both**. Shorter (84L vs 92L, 82L vs 105L), left a runnable
  self-check on each task, k3 left none. k3's F2 indexes by FILE LINE not row, so a blank
  line shifts every subsequent index — a spec deviation that survived its own passing check.
  k3's F1 `.get("duration_ms", 0)` turns a malformed row into a silently wrong median and an
  inflated first-try rate rather than a crash. k3's one real win: timestamp robustness
  (mixed naive/aware, lowercase z) where opus-5 raises TypeError.
  **The "k3 parsimony is a feature virtue" premise that held this lane since 2026-07-22 is
  FALSIFIED — k3 wrote MORE code, not less, on both tasks.**
- **Architecture review (A1), opus-5 vs k3: a TIE, no measured gain.** Both 4/4 planted
  defects, both 5 legitimate extras beyond the key, both the same 1 false positive. opus-5's
  only edge: named the retry/idempotency defect outright where k3 reached it indirectly
  ("partial"). Cost: 167 lines vs 21, 349s vs 234s. n=1. The swap here is consolidation, not
  an upgrade — record it as such.
- **Gating diff review (G1), k3 vs sonnet-5: identical.** Both 4/4 planted, 5 findings each,
  no padding, sensible severity order. Per-attempt latency k3 87s/104s vs sonnet 91s/56s —
  within noise, both ~9× under timeout. **The gate-latency worry does not survive
  measurement**; the 908s k3 review on record was a research-synthesis review, not a diff,
  hence the new diff-scoping rule.
- **Executor/build (E1/E2), k3 vs sonnet-5:** quality tie, k3 ~1.6× slower on E2 (81s vs 49s).

**MEASURED: kimiclaude request burn** (recovered retroactively by counting unique assistant
message IDs in `~/.claude-kimi-config/projects/<taskdir>/*.jsonl` — works for any past run):
F1 3, F2 4, E1 4, E2 5 requests single-attempt; A1 and G1 8 each **because they retried**.
Mean 4.5 on executor shapes → the 300–1200 req/5h window holds ~67 tasks at the floor,
~267 at the ceiling. **Retries, not volume, are what blow the window.**

**Contract adherence, unprompted finding:** `quality_reports/session_logs/` appeared in 4 of
4 claude-engine code-writing taskdirs (incl. 2/2 Opus 5 feature tasks) and 0 of 6 kimiclaude
taskdirs, against an explicit single-deliverable contract. The known claude-engine
contamination, now measured rather than anecdotal.

**Three faults in the instrument — all mine, all recorded so the numbers are not over-read:**
1. The review-lane structural checks required location AND severity inside one top-level
   bullet — a format never stated in the spec. This contaminated all 4 review-lane attempt
   counts and produced the single FAIL (G1--sonnet5 reviewed fine; it failed my formatting).
   Each contaminated retry also DOUBLED that task's Kimi request burn (8 vs 4).
2. The A1 answer key's multi-region decoy is contestable: all four reviews independently
   flagged it, with sound reasoning (the vendor enforcing its own cap is the failure being
   prevented, not a safety net). Four independent reviews against one key means the KEY is
   wrong — real false-positive count is likely zero across the board.
3. `reasoning_effort` logged null on all 16 rows despite manifests passing `--effort high`.
   Cause found and verified by reading the source: `effective_reasoning_effort_from_command`
   (ringer.py:8805) regex-matches only the codex `model_reasoning_effort=` form, so the
   Claude-harness `--effort <level>` argv form returns None. ~4-line fix; until it lands
   every claude/kimiclaude row stays half-unattributable.

**Status: all four lanes PROBATION, not proven** — n=2 per code lane, n=1 per review lane,
below the 3-task threshold.

## 2026-07-25 pm — corp-action-directions continuation (cap-handoff fleet, zero Anthropic)

Context: Claude 5h cap hit mid-deep-research; 5/7 native opus/sonnet lanes harvested from the
killed workflow's journal; remainder ran on ringer (runs corp-action-directions-contA/contB).
All 6 tasks PASS first-try, ~20 min wall. Exploration-ladder outcomes:

- **sol·xhigh on live-web research (2 lanes): untested → PASS ×2.** Both lane reports dense,
  contract-clean, heavily verified-web-tagged with real URLs (spot-checked by luna audit +
  terra review; no fabrications attributed to sol). Codex web recipe:
  `-c sandbox_workspace_write.network_access=true` (+ tools.web_search=true), banner-verifiable
  ("network access enabled"). sol is now the proven non-Anthropic fallback for the research
  lane when Claude caps bind. n=2, promote to probation.
- **luna·xhigh citation audit (web): untested → PASS.** 23 citations checked, 17/6/0
  CONFIRMED/MISMATCH/fabricated; verdict lines precise; caught 6 over-bundled claims the boss
  then enforced. A genuinely load-bearing QA cell at the cheapest codex tier. Probation.
- **luna·xhigh consolidation (39-row table): PASS**, consistent with its bulk-lane primary role.
- **k3·high as coverage critic (doc): untested → PASS.** Found 2 real gaps (Japan capital
  reductions; H-share full circulation) and mapped 9 duplicate clusters + all reserved-design
  adjacencies; arguably the highest-density report of the run. Probation for doc-critic role.
- **terra·xhigh adversarial doc-review: PASS** (SHIP-WITH-FIXES), consistent with its G1-seat
  history; sandbox-without-network is a clean way to ENFORCE the terra live-web ban.

Ops lesson: killed native workflows are recoverable — journal.jsonl retains completed agents'
structured results verbatim; only in-flight agents are lost. Harvest before re-running anything.
