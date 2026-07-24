# Model Routing (all workflows, subagents, and Ringer manifests)

Applies to all orchestration. **This file is the one canonical routing
table.** Supporting evidence lives in `docs/MODEL-NOTES.md` and the live
scoreboard (`python3 ringer.py models`); skills and manifests point here
and must not embed their own tables (drift). Worker lanes are flat-rate
within plan caps, so budget by **caps and latency**, not per-token price.

## Route CELLS, not models

The routing unit is a **cell = (model × effort)**. Effort changes the
worker's personality, not just quality: the same model can be the fleet's
cleanest executor at one effort and unreliable at another. A scoreboard
row for one cell says nothing about its siblings.

**Adaptive-effort rule: reasoning effort on the sonnet/opus and k3 lanes
is ADAPTIVE — never a predetermined tier.** For these lanes the table
names only the model; every dispatch gets an effort chosen for that
specific task (low for the trivial end, max when the task earns it). No
standing "default high" or "typically max." Effort is still passed
EXPLICITLY on every call; adaptive means chosen per task, not omitted.
Codex lanes stay fixed cells.

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
  protocol below (Fable boss, sonnet/opus workers).
- "inline" → the boss's own hands, no fan-out at all.
- **Ultracode active = a standing native declaration for the session**:
  all orchestration runs native; ringer runs only on the explicit word
  "ringer".

Ringer engines (see the ringer config):

- **codex** — GPT-5.6 Sol/Terra/Luna; tier via `model`
  (`gpt-5.6-sol|terra|luna`), effort via
  `engine_args: ["-c", "model_reasoning_effort=high|xhigh|max"]`.
  Luna is the cheapest tier.
- **kimi** — k3 workers **when K3-bossed**: the kimi CLI itself. Effort
  comes from the model alias (standard vs max); there is no `--effort`
  flag. `-p` auto-approves with no sandbox — scope specs to task dirs.
  The CLI burns noticeably more of the request-metered plan window per
  task than the Claude-harness lane — prefer kimiclaude wherever the
  boss allows.
- **kimiclaude** — the k3 lane **when Fable-bossed**: k3 through the
  Claude Code harness via a wrapper that points the harness at the Kimi
  coding endpoint, with the model and a 1M-token context budget pinned
  for workers and subagents. Faster and lighter on the request-metered
  plan than the kimi CLI. The endpoint honors `--effort low|high|max`
  → k3 effort is adaptive, chosen per task via engine_args. Heavy-task
  behavior at the 1M budget is configured but not yet exercised by a
  long task.
- **claude** — `sonnet` / `opus` workers, effort via
  `engine_args: ["--effort", "high"|"max"]`; `claude-fable-5` red-phone
  only (gated, see below). Draws on the same Claude subscription as live
  sessions. Workers on this engine inherit the main Claude config, so
  global rules can leak into worker output — treat stray artifacts in
  worker taskdirs as harness noise and write checks that ignore them.

## Native workflow protocol (standing contract — applies the moment the user says "workflow" / "native swarm"; no per-job restating needed)

- **Fable is the brain and never touches the code.** Boss lane only:
  break work down, write worker briefs/schemas, route cells, adjudicate,
  spot-check, execute checks. Fable never types implementation — not
  inline, not in a worker, and never via a Fable-model subagent (fork/
  omitted-model agents inherit Fable: an omitted `model` field is a bug
  in the orchestration, never what execution wants).
- **Every agent call names its model explicitly; effort is Fable's
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
- **Routing words** (honored fleet-wide, both bosses): "ringer" →
  ringer; "workflow" / "native swarm" / "native workflow" → this
  protocol, that job only; "inline" → the boss's own hands, no fan-out.
  No word → ringer is the default for swarm-shaped work (see Execution
  surface). Ultracode = standing native declaration for the session.

## Routing table

| Task shape | Primary cell | Backup | Basis |
|---|---|---|---|
| Math / quant verification (all of it) | **sol-max** | terra-xhigh | fastest proven lane for exact math; exact rationals |
| Substantial code feature | **k3** (effort adaptive; cap at high unsupervised — max ban binds, see exclusions) | sol-high | parsimonious diffs suit feature work |
| Code fix / hotfix / minimal diff | **terra-xhigh** | k3, sonnet | proven fix lane; keeps the Kimi cap free for features |
| Small/medium executor & build | **sonnet** (effort adaptive) | k3, terra-xhigh | high-volume lane on the shared Claude plan |
| Architecture / design review | **k3** (effort adaptive) | opus second opinion (usually earns max) | strong clean-sheet design judgment |
| Taste-gated (UI, copy, user-facing docs) | **k3** (effort adaptive) | sonnet (executed word/structure caps only) | best taste; sonnet is faster but less contract-reliable here |
| Exploratory / live-web research | **opus or sonnet** — Fable judges model AND effort per task (opus for hard/open-ended, sonnet for lighter sweeps) | k3 | research lanes are Claude-family owned |
| Bounded research (repo lookup, DB scrape) | **sonnet or opus** — Fable judges model AND effort per task (sonnet default; opus when the answer feeds a decision) | k3 | bounded lookups are usually on the critical path, and slow is failure there |
| Mechanical / bulk transforms, probes, smokes | **luna-xhigh** | sonnet (adaptive, low typical), terra-xhigh | matches terra-xhigh quality on the cheapest tier |
| Math independent re-derivation (paper/trade math) | **opus** (effort adaptive — this lane usually earns max) | terra-xhigh (same-family-as-Sol caveat) | matches Sol's results to full precision; cross-family decorrelation |
| Scheduled / background batch jobs | **sonnet** (adaptive; generous timeouts) | k3, luna-xhigh | off-peak runs when live-session contention is lowest |
| Test-hardening | **sol-high** | sonnet | proven lane |
| Diff review — non-blocking, small | **terra-xhigh or sonnet** (rotate; cheapest capable, same-family allowed) | k3, luna-xhigh | interchangeable on correctness at this size; rotation keeps the GPT lane measured |
| Diff review — gating (blocks a merge/step) | **sonnet** (effort adaptive) | k3, terra-xhigh | a gate's latency is part of its quality |
| Gate on irreversible / high-stakes (publish, prod deploy, security-touching) | **opus** (effort adaptive, usually earns max) | — | wrong-and-merged costs more than slow-and-right; the escalation trigger is "what does it cost if the reviewer is wrong", not diff size |
| Consult (engineering second opinion) | **terra-high** | — | consult only, never citation deliverables |
| Premium steady lane (must-not-wobble) | **opus** (effort adaptive — this lane usually earns max) | — | meticulous, zero drama, slow |

**Hard exclusions (as load-bearing as the assignments):**

- **Never terra on live-web research** — fabricated a "verbatim" quote
  in testing.
- **k3 at max effort never runs UNSUPERVISED deliverable tasks — any
  shape.** At max it can silently no-op: read the task, write nothing,
  exit 0 — even on retry with failure context injected. k3@max is a
  supervised thinker/second-opinion cell with the boss in the loop,
  ONLY. All unsupervised k3 dispatches cap at `--effort high`.
- **Harness follows the boss.** K3-bossed jobs route k3 workers to the
  kimi CLI engine; Fable-bossed jobs to the Claude-harness (kimiclaude)
  engine. Via the kimi CLI, k3 effort comes from the model alias
  (standard vs max) — the adaptive `--effort` rule applies to the
  Claude-harness lanes only.
- **Never Haiku for substantive work.**

**Cap pressure:** the OpenAI plan carries math, fixes, test-hardening,
consult, bulk/mechanical, and a diff-review share — watch it first. The
Kimi plan carries features, architecture, and taste — low-volume,
high-value. The Claude subscription carries executor, both research
lanes, gating reviews, premium steady, the math re-derivation second
leg, and scheduled batch — and is shared with live sessions.

## Review / verification

- **Same-family review is ALLOWED.** Reviewer choice follows the routing
  table (cheapest capable review cell); cross-family remains an option
  when decorrelated eyes are wanted, not a requirement. Find and fix are
  still separate workers.
- **Rules-file preamble on Opus**: every Opus agent brief (review,
  verification, or user-facing execution) starts with an instruction to
  first read your rules file and follow its procedures as hard
  constraints.
- **Fable red phone** (ringer `claude`/`claude-fable-5`): advisor/
  reviewer only, never a typing worker; one-task manifest whose spec
  states WHY Fable is warranted, written to survive an audit.
- Math that feeds a paper or a trade: Sol derivation + **opus**
  independent re-derivation, checks executed; agreement to 4+ digits or
  it doesn't ship. The re-derivation partner is deliberately
  cross-family (Anthropic vs OpenAI) so errors are decorrelated.

## Rules

- All worker lanes are correctness-ceiling reasoners at probe sizes:
  route by latency, cap pressure, and blind spot — not imagined
  capability gaps. Judge the output, not the tier: failed review →
  escalate one rung (luna/terra → sol-high → sol-xhigh → sol-max /
  opus-max) without asking.
- **Explore or the scoreboard fossilizes**: in any low-stakes run of 3+
  tasks, give roughly ONE task to an untested cell (strong executed
  check, retry absorbs failure). Promotion ladder: untested → probation
  → proven (3+ tasks, first-try ≥ 0.67). Record demotions in
  `docs/MODEL-NOTES.md`.
- Every new lane or model change goes through a Ringer probe with an
  executed check before real work; outcomes recorded in
  `docs/MODEL-NOTES.md`.
- Evidence strength: probe tasks are small and most personality claims
  are N=1–2. Strong priors, not laws; let the scoreboard overturn them.
