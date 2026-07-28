# Model Routing (all workflows, subagents, and Ringer manifests)

Applies to all orchestration. **This file is the one canonical routing
table.** Supporting evidence lives in `~/fleet/swarm/docs/MODEL-NOTES.md` and
the live scoreboard (`python ringer.py models`); skills and manifests point
here and must not embed their own tables (drift). Worker lanes are flat-rate
within plan caps, so budget by **caps and latency**, not per-token price.

Deployed 2026-07-27 from `overlay/rules/model-routing.md` in
AustinJunyuLi/ringer, replacing the Claude-only variant (backup:
`model-routing.md.bak-claude-only-20260727`) now that Ringer and the
cross-family CLIs are installed here. Two deltas from the overlay source:

- **Boss is role-defined, never model-named** (user decision 2026-07-25).
  The overlay text named Fable as boss throughout; that has been rewritten
  to "the boss (the session model)". Fable remains callable as a red-phone
  advisor lane, user-invoked only — see Review / verification.
- **Qwen is off this fleet** (user decision 2026-07-27). No qwenclaude,
  qwencode or kimiqwen lane exists; the identity blocks and eval rows were
  deleted. Do not re-add.

**2026-07-28 merge (user decisions, after a Fable red-phone consult).** The
07-27 deploy was authored on the Windows laptop against a MODEL-NOTES that
stopped at 07-22, so it silently reverted the 07-25 Opus 5 lane swap and
re-justified k3 on features with a premise the record marks FALSIFIED. The
missing 07-24/07-25 entries have been restored to MODEL-NOTES. Three
decisions resolve it:

- **The table is now ADVISORY PRIORS, not assignments** — see below. This
  dissolves the reverted-lane dispute rather than re-litigating it: the
  evidence is kept, the pin is dropped.
- **Model is adaptive too, not just effort.** Every dispatch chooses both.
- **The k3@max ban is LIFTED in full**, replaced by a watch item.

## Route CELLS, not models

The routing unit is a **cell = (model × effort)**. Effort changes the
worker's personality, not just quality: the same model can be the fleet's
cleanest executor at one effort and unreliable at another. A scoreboard
row for one cell says nothing about its siblings.

**Fully adaptive rule: BOTH HALVES OF THE CELL ARE CHOSEN PER TASK**
(user, 2026-07-28; extends the 07-27 adaptive-effort rule, which itself
replaced the older rule that pinned Codex to fixed cells). Neither the
model nor the effort is predetermined. Every dispatch picks a model for
that specific task and an effort for that specific task — low for the
trivial end, max when the task earns it. No standing "default high," no
"typically max," and no lane that a task shape must go to. Both halves
are still passed EXPLICITLY on every call: adaptive means chosen per
task, not omitted.

What stays binding under full adaptivity — flexibility is not absence of
rules: the **hard exclusions** (safety and trust, not performance
priors), and the **cap pressure** section. Free choice of model must not
mean piling a whole run onto one metered plan.

**A routing variable the log cannot record is not yet part of doctrine.**
Under full adaptivity nothing is inferable from the lane any more, so an
unrecorded variable is an unlearnable one. Effort attribution was fixed
2026-07-28 for exactly this reason (`--effort` and the k3 aliases were
logging null on 176 live rows while doctrine already treated effort as
the unit of analysis). Before adopting a new routing variable, check the
log can capture it.

Where the knob lives, verified 2026-07-27 — **every lane is adaptive**:

| Lane | Per-dispatch effort control | Adaptive? |
|---|---|---|
| codex | `engine_args: ["-c", "model_reasoning_effort=…"]` | yes |
| claude | `engine_args: ["--effort", "…"]` | yes |
| kimi (CLI) | the `model` field — alias `k3-low` / `k3-high` / `k3-max` | yes |

The native kimi CLI has no `--effort` flag, but it does not need one.
Kimi Code's config keys in the `[models."…"]` table **are** the `-m`
aliases, and `default_effort` is a per-alias field, so three aliases
pointing at the same underlying `k3` with different `default_effort`
turn effort into a per-task choice carried by `{model_args}`. Defined in
`~/.kimi-code/config.toml`, live-dispatched 2026-07-27, registered as
distinct scoreboard cells so the three efforts never merge. Do NOT tune
this lane by editing the global `[thinking] effort` — that is shared
state and races under parallel runs; route the alias instead.

## Execution surface — ringer default, routing words override

**Ringer is the default delegation path** (cross-family fleet, executed
checks, scoreboard — keeps the evidence learning and the lanes
break-detected). Trigger: any model-calling command or harness, any
edit→test→edit loop or batch, anything spawning a model. Exempt (stay
inline): reading/searching, git ops, a one-file few-line one-shot edit
(once — a second pass on the same problem is a loop → ringer),
prose/specs/docs from own context, pure conversation.

**Explicit routing words override the default, scoped to that job only**
(no re-offering, no nudges for an overridden job; the next job defaults
back):

- "workflow" / "native swarm" / "native workflow" → the native workflow
  protocol below (session-model boss, sonnet/opus workers).
- "inline" → the boss's own hands, no fan-out at all.
- **Ultracode active = a standing native declaration for the session**:
  all orchestration runs native; ringer runs only on the explicit word
  "ringer".

Ringer engines (see `~/.config/ringer/config.toml`):

- **codex** — GPT-5.6 Sol/Terra/Luna; tier via `model`
  (`gpt-5.6-sol|terra|luna`), effort via
  `engine_args: ["-c", "model_reasoning_effort=high|xhigh|max"]`.
  Luna is the cheapest tier.
- **kimi** — **the only k3 lane.** The native kimi CLI. Effort is
  adaptive via the `model` field: `k3-low` / `k3-high` / `k3-max` (all →
  underlying `k3` at 1M context), plus `kimi-code/k3-256k` for the
  smaller context. `-p` auto-approves with no sandbox — scope specs to
  task dirs.
- **claude** — `sonnet` / `opus` workers, effort via
  `engine_args: ["--effort", "high"|"max"]`; `claude-fable-5` red-phone
  only (gated, see below). Draws on the same Claude subscription as live
  sessions. Workers on this engine inherit the main Claude config, so
  global rules can leak into worker output — treat stray artifacts in
  worker taskdirs as harness noise and write checks that ignore them.
- **mock** — free local worker, no credentials, no network. Smoke the
  harness itself (dispatch → check → log) without spending a plan call.

Not wired here: `grok` (no SuperGrok/X Premium Plus) and `opencode` (no
OpenRouter key, and its sandbox wrapper is macOS-only). Reference blocks
live in `overlay/config/config.toml.example`.

## Native workflow protocol (standing contract — applies the moment the user says "workflow" / "native swarm"; no per-job restating needed)

- **The boss is the session model, and it never touches the code.** Boss
  lane only: break work down, write worker briefs/schemas, route cells,
  adjudicate, spot-check, execute checks. The boss never types
  implementation — not inline, not in a worker, and never via a subagent
  with no model named (fork/omitted-model agents silently inherit the
  boss: an omitted `model` field is a bug in the orchestration, never
  what execution wants).
- **Every agent call names its model explicitly; effort is the boss's
  per-task judgment** (adaptive, never a predetermined tier — but always
  passed explicitly). Sonnet carries execution, mechanical, research,
  bulk; `model: 'opus'` carries the hard cells: architecture/design
  review, must-not-wobble work, final review. Opus briefs start with
  the rules-file preamble (rule below). Same-family review is allowed
  (Opus over Sonnet's diff); find and fix are separate workers. Never
  Haiku.
- **Worker claims are not evidence.** Every workflow ends with the boss
  EXECUTING the verification — run the tests/build/validator via Bash
  in the main loop, or have a verify-stage worker run the exact command
  and return raw output through a schema, which the boss spot-checks.
  "The agent said it passed" never closes a task. Structured-output
  schemas for anything that feeds a decision.
- **Routing words** (honored fleet-wide): "ringer" → ringer; "workflow" /
  "native swarm" / "native workflow" → this protocol, that job only;
  "inline" → the boss's own hands, no fan-out. No word → ringer is the
  default for swarm-shaped work (see Execution surface). Ultracode =
  standing native declaration for the session.

## Priors table (ADVISORY — not assignments)

**This table does not assign work. It records what happened when a shape
was tried** (user decision, 2026-07-28). Pick model and effort per task;
these are the starting points and the known traps, and you may depart
from any of them for a reason. What you may NOT depart from: the hard
exclusions and the cap-pressure section below.

Read the Evidence column as strength-of-prior. Most cells are n=1–2 —
"tried twice, worked" is not "proven," and the column says which.

| Task shape | Prior | Evidence (and how strong) |
|---|---|---|
| Math / quant verification | sol | fastest proven lane for exact math; exact rationals. Hard instances tend to earn max — a prior about difficulty, not a pin |
| Substantial code feature | opus or k3 — **read this row before choosing** | 07-25 paired bakeoff, blind-graded: executed checks TIED 2/2 vs 2/2, so the blind side-by-side read decided it and **opus won both** — shorter (84L vs 92L, 82L vs 105L) and left a runnable self-check where k3 left none. k3's F2 indexed by FILE LINE not row (a blank line shifts every index — a spec deviation that survived its own passing check); k3's F1 `.get(...,0)` turns a malformed row into a silently wrong median. **The "k3 parsimony is a feature virtue" premise is FALSIFIED — k3 wrote MORE code on both tasks.** k3's one real win: timestamp robustness where opus raised TypeError. n=2, unproven |
| Code fix / hotfix / minimal diff | terra | proven fix lane; also keeps the metered Kimi window free |
| Small/medium executor & build | sonnet or k3 | 07-25 bakeoff: quality tie, both 2/2; k3 ~1.6× slower on E2 (81s vs 49s). n=2 |
| Architecture / design review | opus or k3 | 07-25 A1, blind-graded: a **TIE, no measured gain** — both 4/4 planted defects, both 5 legitimate extras, same 1 false positive (and the key itself is contestable: 4/4 independent reviews flagged it). opus named the retry/idempotency defect outright where k3 got there indirectly. Cost of that edge: 167 lines vs 21, 349s vs 234s. n=1. **If one of them authored the artifact, the other reviews it** |
| Taste-gated (UI, copy, user-facing docs) | k3 | best taste; sonnet is faster but less contract-reliable here |
| Exploratory / live-web research | opus or sonnet | Claude-family owned by exclusion (terra is banned here, see below) — opus for hard/open-ended, sonnet for lighter sweeps |
| Bounded research (repo lookup, DB scrape) | sonnet or opus | usually ON the critical path, where slow IS failure; opus when the answer feeds a decision |
| Mechanical / bulk transforms, probes, smokes | luna | matches terra quality at the cheapest tier; low effort usually right. 8/8 on the 07-24 bulk bakeoff |
| Math independent re-derivation (paper/trade) | opus | matched sol's tamper-verified ground truth to full float precision, two independent implementations, first try. Cross-family decorrelation is the point — do not use a second GPT tier |
| Scheduled / background batch jobs | sonnet | off-peak, when live-session contention on the shared plan is lowest |
| Test-hardening | sol | proven lane |
| Diff review — non-blocking, small | terra, sonnet, k3, luna (rotate) | interchangeable on correctness at this size; rotating keeps every lane's scoreboard alive |
| Diff review — gating (blocks a merge/step) | sonnet or k3 | 07-25 G1, blind-graded: **identical** — both 4/4 planted, 5 findings each, no padding, same severity ordering. Latency within noise (k3 87/104s, sonnet 91/56s), both ~9× under timeout — **the gate-latency worry did not survive measurement.** Gate specs MUST be diff-scoped: the 908s k3 review on record was a research-synthesis review, not a diff. n=1 |
| Gate on irreversible / high-stakes (publish, prod deploy, security) | opus, usually max | trigger is "what does it cost if the reviewer is wrong", not diff size. **Non-author second eye required when the gate's author is also the gate** |
| Consult (engineering second opinion) | terra | consult only, never citation deliverables |
| Premium steady (must-not-wobble) | opus | meticulous, zero drama, slow |

**Hard exclusions — these are NOT priors and do not bend.** Everything
above is advisory; everything here is not. These are trust and safety
findings, not performance rankings, which is why adaptivity does not
reach them.

- **Never terra on live-web research** — it fabricated a "verbatim"
  quote by stitching two page regions (hand-verified 2026-07-21). That
  is a trust failure; no effort setting fixes it.
- **Never Haiku for substantive work.**
- **No qwen lane exists on this fleet** (2026-07-27). Do not wire one.
- **One harness per model.** k3 always routes to the `kimi` engine.

**Watch item — k3 at max effort (ban LIFTED 2026-07-28, user decision).**
k3@max may now run any shape, unsupervised. It is a watch item, not a
rule, and here is precisely what to watch, because the two failures came
from different places:

- On the **native kimi CLI** — the harness in use today — k3@max went
  **0 for 2 on build-feature** in the 07-21 audition (7 PASS / 3 FAIL
  overall; the other failure was research-proof). This evidence was NOT
  retired by dropping kimiclaude, so build shapes are where to look first.
- On the **deleted kimiclaude harness**, k3@max silently no-opped: read
  the files, wrote nothing, exited 0 — twice, including a retry with
  failure context injected. That basis died with the harness.

Why lifting is tolerable: the silent walk-away exits 0, but an executed
check plus `expect_files` still FAILS the task, so the harness catches
it. What it costs is wall-clock and a doubled request burn on a
request-metered plan — not a false PASS. Never run k3@max without a
check that reads a declared deliverable back.

**Cap pressure — binding under full adaptivity.** Free choice of model
must not become a pile-on. Kimi (Allegro) is **request**-metered:
300–1200 req per 5h, measured 4–5 requests/task single-attempt and **8
when a check fails** — ~67 tasks at the floor. Retries, not volume, are
what blow this window, so a check that fails for the wrong reason
(format, not substance) is a cap incident. The Claude subscription (Max
x20) is shared with live sessions. The OpenAI plan (Codex Pro x5) is the
roomiest of the three. Spread a multi-task run across plans rather than
sending every task to the same prior.

## Review / verification

- **Same-family review is ALLOWED.** Reviewer choice follows the priors
  table (cheapest capable review cell); cross-family remains an option
  when decorrelated eyes are wanted, not a requirement. Find and fix are
  still separate workers.
- **Non-author second eye.** When the same cell would author an artifact
  and gate it, that is a correlated blind spot, not a review — route the
  gate to a cell that did not write it. Binding for the high-stakes gate
  row; a strong default everywhere else.
- **Rules-file preamble on Opus**: every Opus agent brief (review,
  verification, or user-facing execution) starts with an instruction to
  first read your rules file and follow its procedures as hard
  constraints.
- **Fable red phone** (ringer `claude` engine, model `claude-fable-5`):
  advisor/reviewer only, never a typing worker, and never the boss —
  **user-invoked only**, never part of automated routing. One-task
  manifest whose spec states WHY Fable is warranted, written to survive
  an audit.
- Math that feeds a paper or a trade: Sol derivation + **opus**
  independent re-derivation, checks executed; agreement to 4+ digits or
  it doesn't ship. The re-derivation partner is deliberately
  cross-family (Anthropic vs OpenAI) so errors are decorrelated.

## Rules

- All worker lanes are correctness-ceiling reasoners at probe sizes:
  route by latency, cap pressure, and blind spot — not imagined
  capability gaps. Judge the output, not the tier: failed review →
  escalate one rung (luna → terra → sol-high → sol-xhigh → sol-max /
  opus-max) without asking. Escalation is the one place a fixed effort is
  named, because the rung IS the effort.
- **The scoreboard outranks this table** — which under advisory priors
  is nearly tautological: the rows ARE the scoreboard's summary, held in
  prose. Every row is thin evidence (most n=1–2). When
  `python ringer.py models` disagrees with a row, the scoreboard wins and
  the row gets rewritten. Do not defend a row against its own data.
  **But read the row's Evidence column before deferring**: where checks
  TIED and a blind read broke the tie, the scoreboard cannot see the
  tie-break at all — exit 0 measures "did it work," not "which working
  version do you want to live with." A tie on the board is not
  disagreement with the row.
- **A decision reached by blind comparison is evidence, and it lives in
  MODEL-NOTES** (2026-07-28). It is the strongest instrument available
  once executed checks tie, and it has caught real defects that a passing
  check could not — a solution indexing by file line instead of row
  passed its own check. Such a finding is not a soft opinion to be
  overwritten by the next file sync; record it with its n and its
  caveats, and port it forward.
- **Explore or the scoreboard fossilizes**: in any low-stakes run of 3+
  tasks, give roughly ONE task to an untested cell (strong executed
  check, retry absorbs failure). Promotion ladder: untested → probation
  → proven (3+ tasks, first-try ≥ 0.67). Record demotions in
  `~/fleet/swarm/docs/MODEL-NOTES.md`.
- Every new lane or model change goes through a Ringer probe with an
  executed check before real work; outcomes recorded in
  `~/fleet/swarm/docs/MODEL-NOTES.md`.
- **A recorded FAIL whose root cause was the CHECK, not the worker, must
  be annotated as such in MODEL-NOTES** — otherwise the scoreboard slowly
  learns a lie. Read the raw worker log before blaming a model.
- Evidence strength: probe tasks are small and most personality claims
  are N=1–2. Strong priors, not laws; let the scoreboard overturn them.
