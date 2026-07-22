# Model Routing (all workflows, subagents, and Ringer manifests)

Applies to ALL orchestration on this machine. Rewritten 2026-07-22, merging
Austin's binding 2026-07-21 routing decisions, the 48-task
model-capability-study, and the 85-task K3-boss lane-audition (3 rounds,
executed checks; writeup in `~/fleet/swarm/docs/MODEL-NOTES.md`).

**This file is the ONE canonical routing table.** Evidence lives in
MODEL-NOTES and the live scoreboard (`python3 ringer.py models`); skills and
manifests point HERE and must not embed their own tables (drift). Per-token
cost thinking is dead — worker lanes are flat-rate within plan caps, so
budget by **caps and latency**, not price.

## Route CELLS, not models

The routing unit is a **cell = (model × effort)**. Effort changes the
worker's personality, not just quality: k3-high is the fleet's cleanest
executor while k3-max — same model — double-failed a build by claiming
verification it never re-ran. Sol at xhigh ≈ max on math but slop-prone as
an execution default. A scoreboard row for one cell says nothing about its
siblings.

**Adaptive-effort rule (user 2026-07-22): reasoning on sonnet/opus AND k3
lanes is ADAPTIVE — never a predetermined tier.** For these lanes the table
names ONLY the model; every dispatch gets an effort Fable chooses for that
specific task (low for the trivial end, max when the task earns it). k3
qualifies because it now runs through the Claude Code harness (kimiclaude)
whose endpoint honors `--effort low|high|max` — Fable controls it like a
native Claude model. No standing "default high" or "typically max" — any
effort in a basis column is history, not a directive. Effort is still
passed EXPLICITLY on every call; adaptive means chosen per task, not
omitted. Codex lanes stay fixed cells; qwen has no knob (one cell).

## Execution surface — ringer default, user words override (2026-07-22, full strength)

**Ringer is the DEFAULT delegation path** (cross-family fleet, executed
checks, scoreboard — keeps the evidence learning and the lanes
break-detected). Full-strength trigger: any model-calling command or
harness, any edit→test→edit loop or batch, anything spawning a model.
Exempt (stay inline): reading/searching, git ops, a one-file few-line
ONE-SHOT edit (once — a second pass on the same problem is a loop →
ringer), prose/specs/docs from own context, pure conversation.

**The user's routing words OVERRIDE the default, scoped to THAT JOB only**
(no re-offering, no nudges for an overridden job; next job defaults back):

- "workflow" / "native swarm" / "native workflow" → the native workflow
  protocol below (Fable boss, sonnet/opus workers).
- "inline" → the boss's own hands, no fan-out at all.
- **Ultracode active = a STANDING native declaration for the session**:
  all orchestration runs native; ringer runs only on the explicit word
  "ringer".

`omp-role.sh` is RETIRED. Ringer engines in
`~/.config/ringer/config.toml`:

- **codex** — GPT-5.6 Sol/Terra; tier via `model`, effort via
  `engine_args: ["-c", "model_reasoning_effort=high|xhigh|max"]`. OAuth plan.
- **kimiclaude** — THE k3 lane (2026-07-22): k3 through the Claude Code
  harness via `~/.local/bin/claude-kimi` (api.kimi.com/coding, membership
  plan, key 0600 in `~/.kimi-code/claude-code-key`). Replaces the
  kimi-code CLI for ALL worker traffic (kimiclaude went 5/5 first-try on
  the capacity screen, equal-or-faster on every task, research 4.8×
  faster); the CLI remains installed as the Kimi boss's harness ONLY. Endpoint honors `--effort low|high|max` → k3
  effort is ADAPTIVE, Fable's per-task call via engine_args. k3 is
  natively 1M context here. **k3 ONLY** — the endpoint's
  `kimi-for-coding[-highspeed]` slugs are K2.7 in disguise (banned).
  Heavy-task behavior unmeasured; screen evidence is S1-sized.
- **claude** — `sonnet` / `opus` workers, effort via
  `engine_args: ["--effort", "high"|"max"]`; `claude-fable-5` red-phone only
  (gated, see below). Draws on the same Claude subscription as live sessions.
- **qwenclaude** — PRIMARY qwen lane (2026-07-22): qwen3.8-max-preview
  through the Claude Code harness via `~/.local/bin/claude-qwen` (Token
  Plan's Anthropic-compatible endpoint; officially supported). Flat-rate,
  fast (26–31s tasks — the old 81s+/stall pain was the qwencode harness,
  not the backend). Effort knob findings (sniffed 2026-07-22): the CLI
  sends `output_config.effort` + `thinking:adaptive`, both of which the
  endpoint ignores/frees — **qwen always runs at full thinking; `--effort`
  and MAX_THINKING_TOKENS are no-ops here**. One cell ≡ old qwen-max.
  The endpoint DOES honor raw-API `budget_tokens` (starved budget →
  confidently wrong answers), but no CLI path reaches it — latency tier
  = qwen3.6-flash, not a budget knob. Live plan models: qwen3.8-max-preview,
  qwen3.7-max/plus, qwen3.6-flash, deepseek-v4-pro (explore candidate);
  glm-5.2 served but UNPLUGGED; k2.x slugs no longer served.
- **qwencode** — fallback shim only (stalls under heavy tasks). qwen3.8-max
  preview ONLY (user directive), thinking pinned max in `~/.qwen/settings.json`.
- **qwen (omp)** — emergency fallback ONLY if both qwen shims break.
  Metered. Never routine.

## Native workflow protocol (standing contract — applies the moment the user says "workflow" / "native swarm"; no per-job restating needed)

- **Fable is the brain and never touches the code.** Boss lane only:
  decompose, write worker prompts/schemas, route cells, adjudicate,
  spot-check, execute checks. Fable never types implementation — not
  inline, not in a worker, and never via a Fable-model subagent (fork/
  omitted-model agents inherit Fable: an omitted `model` field is a BUG in
  the orchestration, never what execution wants).
- **Every agent call names its model explicitly; effort is Fable's
  per-task judgment** (user 2026-07-22: adaptive, never a predetermined
  tier — but always passed explicitly). Sonnet carries execution,
  mechanical, research, bulk; `model: 'opus'` carries the hard cells:
  architecture/design review, must-not-wobble work, final review. Opus
  prompts start with the fable-operating-manual preamble (rule below).
  Same-family review is allowed (Opus over Sonnet's diff); find and fix
  are separate workers. Never Haiku.
- **Worker claims are not evidence.** Every workflow ends with the boss
  EXECUTING the verification — run the tests/compile/validator via Bash in
  the main loop, or have a verify-stage worker run the exact command and
  return raw output through a schema, which the boss spot-checks. "The
  agent said it passed" never closes a task. Structured-output schemas for
  anything that feeds a decision.
- **Routing words** (honored fleet-wide, both bosses): "ringer" → ringer;
  "workflow" / "native swarm" / "native workflow" → this protocol, that job
  only; "inline" → the boss's own hands, no fan-out. No word → ringer is
  the default for swarm-shaped work (see Execution surface). Ultracode =
  standing native declaration for the session.

## Routing table (binding until revised; updated 2026-07-22)

| Task shape | Primary cell | Backup | Basis |
|---|---|---|---|
| Math / quant verification (all of it) | **sol-max** | terra-xhigh | user 2026-07-21; 2–4× faster, exact rationals |
| Substantial code feature | **sol-high** | sol-xhigh (deliberate escalation only) | user 2026-07-21; sol uneconomical on small tasks |
| Code fix / hotfix / minimal diff | **k3** (effort adaptive, via kimiclaude) | terra-xhigh, sonnet | audition 8/8 first-try; parsimony champion |
| Small/medium executor & build | **sonnet** (effort adaptive) | k3, terra-xhigh | user 2026-07-22: x20 Claude sub was underutilized; volume moves off Kimi's cap |
| Architecture / design review | **opus** (effort adaptive) | k3 second opinion (usually earns max) | user 2026-07-22; opus-max was the other audition clean sheet |
| Taste-gated (UI, copy, user-facing docs) | **k3** (effort adaptive) | sonnet (executed word/structure caps only) | user 2026-07-22: stays k3; sonnet 5–10× faster but 2 contract misses |
| Exploratory / live-web research | **opus** (effort adaptive, scaled to task difficulty) | k3 | user 2026-07-22 |
| Bounded research (repo lookup, DB scrape) | **qwen** (via qwenclaude) | k3 | preserves "declared-fast → qwen", narrowed to bounded few-turn work |
| Mechanical / bulk transforms, probes, smokes | **qwen** (via qwenclaude) | sonnet, terra-xhigh | user 2026-07-22: highest-volume lane on the workers-only qwen cap frees Claude-plan headroom; 26–79s on S1 sizes; checks cover the wobble. First qwenclaude stall/timeout → lane reverts to sonnet |
| Test-hardening | **qwen** | sol-high | unrequested-test habit is the feature here (qwencode-era evidence; re-verify on qwenclaude) |
| Diff review | cheapest capable cell: qwen (flat-rate, via qwenclaude) / sonnet / k3 / terra-xhigh (48s); same-family allowed (user 2026-07-22) | — | all interchangeable on correctness at audition sizes |
| Consult (engineering second opinion) | **terra-high** | — | user 2026-07-21; consult only, never citation deliverables |
| Premium steady lane (must-not-wobble) | **opus** (effort adaptive — this lane usually earns max) | — | meticulous, zero drama, slow |

**Hard exclusions (as load-bearing as the assignments):**

- **Never terra on live-web research** — fabricated a "verbatim" quote by
  stitching two page regions (verified by hand, 2026-07-21).
- **qwen live-web research: ban DOWNGRADED to probation (2026-07-22)** —
  the "never" was earned by qwencode-harness stalls (two 1800s timeouts),
  not the model: via qwenclaude the same verbatim-quote research task
  PASSED first-try (10.5 min — slow; opus/k3-high stay primary). Backup
  and explore-slot use only until 3+ passes.
- **k3 at max effort never types unsupervised builds** — sloppy-verify
  double-FAIL was model personality, not harness; the ban survives the
  kimiclaude swap. Thinker/reviewer only at max.
- **kimi-code CLI is retired from WORKER duty (2026-07-22)** — the
  `kimi` ringer engine is deleted and never comes back; ALL k3 worker
  traffic runs through kimiclaude. The CLI itself stays installed solely
  as the Kimi BOSS's interactive harness. The kimiclaude endpoint's
  `kimi-for-coding[-highspeed]` slugs are K2.7 in disguise — banned.
- **Never Haiku for substantive work. K2.7 slugs banned fleet-wide.**
- **GLM-5.2: UNPLUGGED** (2026-07-21). No tie-breaker role; Fable
  adjudicates disagreements or escalates one rung.

**Standing cautions:** qwen burns 4–8× codex tokens per task — fine on
flat rate. Sonnet/Opus ringer workers spend Claude-plan cap shared with
live sessions and native workflows — the 2026-07-22 rebalance loads the
x20 plan (executor, research, architecture from Kimi) but pushes the
highest-volume lanes (bulk, bounded research, diff-review first choice)
to the workers-only qwen cap, which is nearly as abundant as the x20 and
competes with nothing. Kimi is now light (fixes, taste, second opinions)
— its cap is no longer the tripwire. qwenclaude heavy-load behavior is
unmeasured (qwencode's stalls were heavy-task); first stall reverts the
lane to sonnet.
Test-hardening's qwen "unrequested-test habit" evidence came from the
qwencode harness; re-verify the habit survives the qwenclaude harness
before leaning on it.

## Review / verification

- **Same-family review is ALLOWED** (user 2026-07-22). The old
  "writer's family never reviews its own diff" rule was council-era model
  doctrine that rode into the 2026-07-21 bundle unexamined — retired.
  Reviewer choice follows the routing table (cheapest capable review cell);
  cross-family remains an OPTION when the user wants decorrelated eyes, not
  a requirement. Find and fix are still separate workers.
- **Fable operating manual on Opus**: every Opus agent prompt (review,
  verification, or user-facing execution) starts with: "First Read
  ~/.claude/fable-operating-manual.md and follow its procedures as hard
  constraints."
- **Fable red phone** (ringer `claude`/`claude-fable-5`): advisor/reviewer
  only, never a typing worker; one-task manifest whose spec states WHY Fable
  is warranted, written to survive an audit.
- Math that feeds a paper or a trade: Sol derivation + qwen independent
  re-derivation, checks executed; agreement to 4+ digits or it doesn't ship.

## Rules

- All worker lanes are correctness-ceiling reasoners at audition sizes:
  route by latency, cap pressure, and blind spot — not imagined capability
  gaps. Judge the output, not the tier: failed review → escalate one rung
  (qwen/terra → sol-high → sol-xhigh → sol-max / opus-max) without asking.
- **Explore or the scoreboard fossilizes**: in any low-stakes run of 3+
  tasks, give roughly ONE task to an untested cell (strong executed check,
  retry absorbs failure). Promotion: untested → probation → proven
  (3+ tasks, first-try ≥ 0.67). Record demotions in MODEL-NOTES.
- Every new lane or model change goes through a Ringer probe with an
  executed check before real work; outcomes recorded in MODEL-NOTES.
- Evidence strength: audition tasks were SMALL and most personality claims
  are N=1–2 — the build rows lean on prior history (audition build round
  contaminated by a spec bug). Strong priors, not laws; let the scoreboard
  overturn them.
