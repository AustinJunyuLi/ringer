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
- **kimiclaude is deleted** (user decision 2026-07-27). k3 through the
  Claude Code harness existed solely to give k3 per-task effort. Once the
  native kimi CLI was shown to do that through per-effort model aliases,
  the lane was pure duplication on a scarcer plan. Wrapper, isolated
  config dir, probes, identity blocks and eval rows all removed. Four
  lanes remain: codex, claude, kimi, mock. Do not rebuild it.

## Route CELLS, not models

The routing unit is a **cell = (model × effort)**. Effort changes the
worker's personality, not just quality: the same model can be the fleet's
cleanest executor at one effort and unreliable at another. A scoreboard
row for one cell says nothing about its siblings.

**Adaptive-effort rule: reasoning effort is ADAPTIVE ON EVERY LANE THAT
CAN CARRY IT — never a predetermined tier** (user, 2026-07-27; this
replaces the older rule that pinned Codex to fixed cells). The table
below names only the MODEL; every dispatch gets an effort chosen for that
specific task — low for the trivial end, max when the task earns it. No
standing "default high," no "typically max." Effort is still passed
EXPLICITLY on every call: adaptive means chosen per task, not omitted.

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
  task dirs. The `kimiclaude` lane (k3 routed through the Claude Code
  harness) was **deleted 2026-07-27** once this lane proved adaptive: it
  existed only to supply per-task effort, and duplicated a model this
  lane already serves more cheaply against the plan. Do not rebuild it.
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

## Routing table

**Every cell below is MODEL-only; the boss picks effort per task.** Where a
row says "usually earns max" that is a prior about difficulty, not a pin —
a trivial instance of that shape still gets low.

| Task shape | Primary model | Backup | Basis |
|---|---|---|---|
| Math / quant verification (all of it) | **sol** | terra | fastest proven lane for exact math; exact rationals. Hard instances earn max — but effort is still chosen, not assumed |
| Substantial code feature | **k3** (cap at high unsupervised — max ban binds, see exclusions) | sol | parsimonious diffs suit feature work |
| Code fix / hotfix / minimal diff | **terra** | k3, sonnet | proven fix lane; keeps the Kimi cap free for features |
| Small/medium executor & build | **sonnet** | k3, terra | high-volume lane on the shared Claude plan |
| Architecture / design review | **k3** | opus second opinion | strong clean-sheet design judgment |
| Taste-gated (UI, copy, user-facing docs) | **k3** | sonnet (executed word/structure caps only) | best taste; sonnet is faster but less contract-reliable here |
| Exploratory / live-web research | **opus or sonnet** — boss judges model AND effort (opus for hard/open-ended, sonnet for lighter sweeps) | k3 | research lanes are Claude-family owned |
| Bounded research (repo lookup, DB scrape) | **sonnet or opus** — boss judges model AND effort (sonnet default; opus when the answer feeds a decision) | k3 | bounded lookups are usually on the critical path, and slow is failure there |
| Mechanical / bulk transforms, probes, smokes | **luna** (low effort is usually right here) | sonnet, terra | matches terra quality on the cheapest tier |
| Math independent re-derivation (paper/trade math) | **opus** (usually earns max) | terra (same-family-as-Sol caveat) | matches Sol's results to full precision; cross-family decorrelation |
| Scheduled / background batch jobs | **sonnet** (generous timeouts) | k3, luna | off-peak runs when live-session contention is lowest |
| Test-hardening | **sol** | sonnet | proven lane |
| Diff review — non-blocking, small | **terra or sonnet** (rotate; cheapest capable, same-family allowed) | k3, luna | interchangeable on correctness at this size; rotation keeps the GPT lane measured |
| Diff review — gating (blocks a merge/step) | **sonnet** | k3, terra | a gate's latency is part of its quality |
| Gate on irreversible / high-stakes (publish, prod deploy, security-touching) | **opus** (usually earns max) | — | wrong-and-merged costs more than slow-and-right; the escalation trigger is "what does it cost if the reviewer is wrong", not diff size |
| Consult (engineering second opinion) | **terra** | — | consult only, never citation deliverables |
| Premium steady lane (must-not-wobble) | **opus** (usually earns max) | — | meticulous, zero drama, slow |

**Hard exclusions (as load-bearing as the assignments):**

- **Never terra on live-web research** — fabricated a "verbatim" quote
  in testing.
- **k3 at max effort never runs UNSUPERVISED deliverable tasks — any
  shape.** At max it can silently no-op: read the task, write nothing,
  exit 0 — even on retry with failure context injected. k3@max is a
  supervised thinker/second-opinion cell with the boss in the loop,
  ONLY. All unsupervised k3 dispatches cap at `--effort high`.
- **One harness per model.** k3 always routes to the `kimi` engine,
  whichever model is bossing. The old "harness follows the boss" rule
  existed to pick between two k3 lanes; with `kimiclaude` deleted there
  is nothing to pick.
- **Never Haiku for substantive work.**
- **No qwen lane exists on this fleet** (2026-07-27). Do not wire one.

**Cap pressure:** the OpenAI plan (Codex Pro x5) carries math, fixes,
test-hardening, consult, bulk/mechanical, and a diff-review share — watch
it first. The Kimi plan (Allegro) carries features, architecture, and
taste — low-volume, high-value. The Claude subscription (Max x20) carries
executor, both research lanes, gating reviews, premium steady, the math
re-derivation second leg, and scheduled batch — and is shared with live
sessions.

## Review / verification

- **Same-family review is ALLOWED.** Reviewer choice follows the routing
  table (cheapest capable review cell); cross-family remains an option
  when decorrelated eyes are wanted, not a requirement. Find and fix are
  still separate workers.
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
- **The scoreboard outranks this table.** Every row above is a prior
  written from thin evidence (most cells N=1–2). When
  `python ringer.py models` disagrees with a row for a given task_type,
  the scoreboard wins and the row gets rewritten — that is the whole
  point of logging attempts. Do not defend a row against its own data.
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
