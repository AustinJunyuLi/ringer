# Model Routing (all workflows, subagents, and Ringer manifests)

Applies to ALL orchestration on this machine. Rewritten 2026-07-22, merging
the maintainer's binding 2026-07-21 routing decisions, the 48-task
model-capability-study, and the 85-task K3-boss lane-audition (3 rounds,
executed checks; writeup in `~/fleet/swarm/docs/MODEL-NOTES.md`).
Revised 2026-07-24: **qwen DELETED from the fleet** (Token Plan cut
qwen3.8-max usage; user-directed full burn, NO fallbacks — engines, shims,
~/.qwen, kimi-code provider all removed). Vacated lanes refilled on
executed evidence: bulk-lane-bakeoff (luna/terra/sonnet, 8/8),
math-partner-rundown (sol-authored, opus PASS / k3-max double-FAIL), and
the k3-harness-efficiency A/B — all in MODEL-NOTES.

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
omitted. Codex lanes stay fixed cells.

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

- **codex** — GPT-5.6 Sol/Terra/Luna; tier via `model`
  (`gpt-5.6-sol|terra|luna`), effort via
  `engine_args: ["-c", "model_reasoning_effort=high|xhigh|max"]`. OAuth plan.
  Luna is the cheapest tier — bulk-lane primary since 2026-07-24.
- **kimi** — k3 workers **when K3-bossed** (2026-07-22 pm): the kimi CLI
  itself (`kimi-code/k3` default, `kimi-code/k3max` for max effort — aliases
  are the effort carrier here; no `--effort` flag exists). `-p`
  auto-approves, no sandbox — scope specs to task dirs. Note 2026-07-24:
  the kimi CLI burns 2.5–3× more of the plan's REQUEST-metered window
  (6–10 req/task vs kimiclaude's 2–4) — prefer kimiclaude wherever the
  boss allows.
- **kimiclaude** — the k3 lane **when Fable-bossed** (2026-07-22): k3 through the Claude Code
  harness via `~/.local/bin/claude-kimi` (api.kimi.com/coding, membership
  plan, key 0600 in `~/.kimi-code/claude-code-key`). Went 5/5 first-try on
  the capacity screen; A/B 2026-07-24 vs the kimi CLI (same tasks, effort
  high, executed checks): 2.2–3.3× faster, 2.3–2.9× less raw token
  traffic, 2–4 requests/task vs 6–10 on a request-metered plan
  (300–1200 req/5h, ≤30 concurrent). Endpoint honors `--effort
  low|high|max` → k3 effort is ADAPTIVE, Fable's per-task call via
  engine_args. Wrapper rewired 2026-07-24 per kimi.com/code/docs: ALL
  alias env vars + subagent model pinned to k3, `ANTHROPIC_MODEL=k3[1m]`
  + `CLAUDE_CODE_MAX_CONTEXT_TOKENS=1000000` so the endpoint's native 1M
  context (verified via /v1/models metadata) is actually budgeted;
  rewire probe PASS. **k3 ONLY** — the endpoint's
  `kimi-for-coding[-highspeed]` slugs are K2.7 in disguise (banned).
  Heavy-task behavior still unmeasured; 1M budget configured but
  behaviorally unverified until a long task exercises it.
- **claude** — `sonnet` / `opus` workers, effort via
  `engine_args: ["--effort", "high"|"max"]`; `claude-fable-5` red-phone only
  (gated, see below). Draws on the same Claude subscription as live sessions.
  KNOWN CONTAMINATION (2026-07-24): this engine runs against the main
  ~/.claude config, so the user's global rules leak into workers — sonnet
  and opus workers both dropped `quality_reports/session_logs/` into
  bakeoff taskdirs, violating explicit one-deliverable contracts. Not
  fixable by CLAUDE_CONFIG_DIR isolation without breaking OAuth; treat
  stray quality_reports/ in worker output as harness noise, and write
  checks that ignore it.

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

## Routing table (binding until revised; updated 2026-07-22 pm — feature/fix/architecture/research rebalance)

| Task shape | Primary cell | Backup | Basis |
|---|---|---|---|
| Math / quant verification (all of it) | **sol-max** | terra-xhigh | user 2026-07-21; 2–4× faster, exact rationals |
| Substantial code feature | **k3** (effort adaptive, cap at high unsupervised — max ban binds; PROBATION: sol-high standing backup until 3+ features first-try ≥ 0.67) | sol-high | user 2026-07-22 pm; k3 parsimony is a feature virtue; kimiclaude feature-scale behavior UNMEASURED — hence staged |
| Code fix / hotfix / minimal diff | **terra-xhigh** | k3, sonnet | user 2026-07-22 pm; terra was the proven audition backup on this lane; frees Kimi cap for features |
| Small/medium executor & build | **sonnet** (effort adaptive) | k3, terra-xhigh | user 2026-07-22: x20 Claude sub was underutilized; volume moves off Kimi's cap |
| Architecture / design review | **k3** (effort adaptive) | opus second opinion (usually earns max) | user 2026-07-22 pm: swap of am assignment; both were audition clean sheets |
| Taste-gated (UI, copy, user-facing docs) | **k3** (effort adaptive) | sonnet (executed word/structure caps only) | user 2026-07-22: stays k3; sonnet 5–10× faster but 2 contract misses |
| Exploratory / live-web research | **opus or sonnet** — Fable judges model AND effort per task (opus for hard/open-ended, sonnet for lighter sweeps) | k3 | user 2026-07-22 pm: research lanes are Claude-family owned |
| Bounded research (repo lookup, DB scrape) | **sonnet or opus** — Fable judges model AND effort per task (sonnet default; opus when the answer feeds a decision) | k3 | user 2026-07-22 pm: bounded lookups are usually ON the critical path, and slow is failure there |
| Mechanical / bulk transforms, probes, smokes | **luna-xhigh** (PROBATION: sonnet standing backup until 3+ real bulk tasks first-try ≥ 0.67) | sonnet (adaptive, low typical), terra-xhigh | 2026-07-24 bulk-lane-bakeoff (8/8 first-try): luna-xhigh ≈ terra-xhigh on quality+tokens at a cheaper tier; luna-max adds nothing over xhigh; sonnet-low is 2–4× faster but loads the shared x20 and left contract-violating quality_reports/ debris in both taskdirs (see claude-engine contamination note) |
| Math independent re-derivation (paper/trade math) | **opus** (effort adaptive — this lane usually earns max) | terra-xhigh (same-family-as-Sol caveat) | 2026-07-24 math-partner-rundown: opus matched sol-max's tamper-verified ground truth to full float precision on both problems, self-validated via two independent implementations, first-try in 429s; k3-max double-FAILED the same task (silent no-op — see exclusions) |
| Scheduled / background batch jobs | **sonnet** (adaptive; generous timeouts) | k3, luna-xhigh | 2026-07-24: off-peak batch runs when x20 live-session contention is lowest |
| Test-hardening | **sol-high** | sonnet | user 2026-07-22 pm; backup moved to sonnet 2026-07-24 (qwen deleted) |
| Diff review — non-blocking, small | **terra-xhigh or sonnet** (rotate; cheapest capable, same-family allowed) | k3, luna-xhigh | all interchangeable on correctness at audition sizes; terra in rotation keeps the GPT lane scoreboard live |
| Diff review — gating (blocks a merge/step) | **sonnet** (effort adaptive) | k3, terra-xhigh | user 2026-07-22: a gate's latency is part of its quality |
| Gate on irreversible / high-stakes (publish, prod deploy, security-touching) | **opus** (effort adaptive, usually earns max) | — | user 2026-07-22: wrong-and-merged costs more than slow-and-right; escalation trigger is "what does it cost if the reviewer is wrong", not diff size |
| Consult (engineering second opinion) | **terra-high** | — | user 2026-07-21; consult only, never citation deliverables |
| Premium steady lane (must-not-wobble) | **opus** (effort adaptive — this lane usually earns max) | — | meticulous, zero drama, slow |

**Qwen: DELETED (user 2026-07-24).** The Token Plan cut qwen3.8-max
usage, killing the cap-arbitrage rationale for every qwen lane. Full
burn, no fallbacks: engines qwen/qwencode/qwenclaude/kimiqwen removed
from ringer config, shims and ~/.qwen deleted, kimi-code qwen-token-plan
provider removed. DeepSeek explore candidate died with the channel. The
omp binary has no fleet role. Historical qwen rows remain in runs.jsonl
and MODEL-NOTES only. Do not rebuild without a fresh user directive.

**Hard exclusions (as load-bearing as the assignments):**

- **Never terra on live-web research** — fabricated a "verbatim" quote by
  stitching two page regions (verified by hand, 2026-07-21).
- **k3 at max effort never runs UNSUPERVISED deliverable tasks — any
  shape** (BROADENED 2026-07-24; was builds-only). New evidence: in the
  math-partner rundown k3@max read the two problem files, wrote nothing,
  said nothing, and exited 0 — twice, including the retry with failure
  context injected (transcripts: 5 then 4 assistant msgs, 2 tool uses
  each, no deliverables, 1182s burned). The silent-walk-away personality
  is not build-specific. k3@max = thinker/second-opinion with the boss in
  the loop, ONLY. All unsupervised k3 dispatches cap at `--effort high`.
- **Harness follows the boss (user, 2026-07-22 pm).** K3-bossed jobs
  route k3 workers to `[engines.kimi]` (kimi CLI); Fable-bossed jobs to
  `[engines.kimiclaude]`. Effort note: via the kimi CLI, k3 effort comes
  from the model alias (`kimi-code/k3` high vs `kimi-code/k3max` max) —
  the adaptive `--effort` rule applies to the Claude-harness lanes only.
  The kimiclaude endpoint's `kimi-for-coding[-highspeed]` slugs are K2.7
  in disguise — banned.
- **Never Haiku for substantive work. K2.7 slugs banned fleet-wide.**
- **GLM-5.2: UNPLUGGED** (2026-07-21). No tie-breaker role; Fable
  adjudicates disagreements or escalates one rung.

**Standing cautions (post-deletion, 2026-07-24):** three caps carry
everything. **OpenAI** carries math (sol-max), fixes (terra-xhigh),
test-hardening (sol-high), consult (terra-high), a diff-review rotation
share, AND bulk/mechanical (luna-xhigh — new highest-volume lane, but on
the cheapest GPT tier): watch this cap first now. **Kimi** carries
features + architecture + taste — low-volume/high-value; features stay
ON PROBATION (sol-high standing backup) because kimiclaude has never
carried a multi-minute build; the 2026-07-24 wrapper rewire (1M context
budget) is untested at feature scale. **Claude x20** carries executor,
both research lanes, gating reviews, premium steady, the math
re-derivation second leg (opus), and scheduled batch — relieved of bulk,
still shared with live sessions. Luna's bulk probation mirrors the k3
features pattern: first real-bulk failure or 3+ passes resolves it
either way.

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
- Math that feeds a paper or a trade: Sol derivation + **opus** independent
  re-derivation, checks executed; agreement to 4+ digits or it doesn't ship.
  (Partner changed from qwen 2026-07-24: rundown evidence — opus matched
  sol's tamper-verified ground truth to full float precision, both
  problems, with two independent implementations per answer. Cross-family
  OpenAI↔Anthropic decorrelation preserved. k3 is NOT the partner: k3@max
  double-no-opped the rundown, and the lane usually earns max.)

## Rules

- All worker lanes are correctness-ceiling reasoners at audition sizes:
  route by latency, cap pressure, and blind spot — not imagined capability
  gaps. Judge the output, not the tier: failed review → escalate one rung
  (luna/terra → sol-high → sol-xhigh → sol-max / opus-max) without asking.
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
