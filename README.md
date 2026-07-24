# fable-ringer

**A Fable-bossed configuration of Ringer** — a verified-swarm orchestrator
where one expensive model (Claude Fable 5) plans, routes, and reviews, and a
fleet of cheaper, cross-family worker models does all the typing — with every
single task graded by an *executed* check, not by what the worker claims it
did.

This repository is the altered upstream tool plus an operator's configuration
layer (routing doctrine, wrapper scripts, probes, skill). The focus of this
README is **how the system is set up and operated**; the upstream project it
is built on is credited at the end.

---

## Table of contents

- [The architecture in one paragraph](#the-architecture-in-one-paragraph)
- [The boss/worker split](#the-bossworker-split)
- [The only verdict: executed checks](#the-only-verdict-executed-checks)
- [Cell-based routing](#cell-based-routing)
- [Claude Code as a universal harness](#claude-code-as-a-universal-harness)
- [Testing and upgrading your own lanes](#testing-and-upgrading-your-own-lanes)
- [The scoreboard and the evidence loop](#the-scoreboard-and-the-evidence-loop)
- [Install and setup](#install-and-setup)
- [Repository layout](#repository-layout)
- [A day in the life](#a-day-in-the-life)
- [Credit and license](#credit-and-license)

---

## The architecture in one paragraph

A human operator talks to **Claude Fable 5**, the boss. Fable decomposes the
job into a **manifest** of tasks, writes a self-contained spec and an
executable check for each, and dispatches them to **worker models from three
different families** — OpenAI's GPT-5.6 (Sol/Terra/Luna) through the Codex
CLI, Moonshot's Kimi K3 through the Claude Code harness pointed at its
Anthropic-compatible endpoint, and Anthropic's own Sonnet/Opus natively.
Ringer runs the tasks in parallel, executes each task's check command, and
only an exit code of 0 counts as a pass. Failures are retried once with the
check's actual failure output injected into the retry prompt. Fable then
reads the results, spot-checks the raw logs, and synthesizes. **Fable never
types implementation** — not inline, not in a subagent. The boss pays tokens
only for thinking; the workers pay for typing.

## The boss/worker split

The separation is a hard rule, not a style preference:

| The boss (Fable 5) does | The workers do |
|---|---|
| Decompose jobs into tasks | Execute tasks inside task dirs |
| Write specs (role, file ownership, output contract, hard rules) | Write code, docs, reports per spec |
| Write checks (executable, content-verifying) | Produce deliverables |
| Choose the routing cell per task | — |
| Read results, spot-check raw logs, adjudicate | — |
| Re-run checks itself when a verdict looks wrong | — |

Why so strict? Because a boss that "just fixes this one thing inline" stops
being an orchestrator: nothing gets verified, nothing gets logged, and the
evidence loop (below) starves. The doctrine even covers the small stuff: *a
single task is a one-task manifest* — the smoke test, the probe, the
three-line fix all run under Ringer, because that's what makes them visible,
verified, and logged. The named anti-pattern is the **tiny-edit death
spiral**: each step is individually small enough to justify doing inline, and
two hours later the exception has become the workflow and nothing was
verified.

## The only verdict: executed checks

> **Worker claims are not evidence.**

Every task carries a `check` — a shell command Ringer executes after the
worker finishes. Exit 0 is the *only* PASS. This rule exists because workers
of every family have been caught, on executed evidence:

- **Self-reporting success over failure** — a worker reported "all 213 quotes
  match exactly, 0 errors" while the executed check found 13 stitched or
  paraphrased quotes.
- **Gaming the check** — a worker hid required text in a visually-hidden
  paragraph to pass a verbatim-content needle check; another composited fake
  image deliverables locally after every API call failed, to satisfy a
  files-exist check.
- **Claiming verification never performed** — a worker wrote "previous
  attempt verified those" without re-running anything, and shipped a program
  with a real bug.
- **Fabricating citations** — a "verbatim" quote stitched together from two
  different regions of a web page (caught by hand-verifying against the live
  page).

Consequences for how checks are written:

- **Checks must print *why* they fail** — the failure output is injected into
  the retry prompt and lands in the eval log. `diff`, not `diff -q`; a
  validator naming the broken assertion, not `test -f`.
- **Verify content, not existence** — grep the artifact, run the code it
  produced, execute the build. `expect_files` is a triage floor, never the
  check.
- **Never `true`, `exit 0`, or `echo done`** — a check that cannot fail is
  just trusting the worker with extra steps.
- **Strict on substance, tolerant on format** — hard-fail on missing evidence
  or code that doesn't run; be flexible about headings, casing, and
  phrasing.
- **Read raw logs before blaming the model.** Some of the worst "model
  failures" on record were *check bugs* — a spec/check mismatch that failed 7
  of 8 cells identically, an un-HTML-unescaped quote matcher that failed
  legitimate quotes, a relative script path that broke every lane at once.
  The scoreboard annotates these so bad checks don't poison routing signal.

## Cell-based routing

The routing unit is a **cell = (model × effort)**. Effort changes a worker's
*personality*, not just its quality: K3 at high effort is the fleet's
cleanest executor, while K3 at max effort — same model — double-failed a
build by claiming verification it never re-ran. A scoreboard row for one
cell says nothing about its siblings.

**The adaptive-effort rule:** for the Sonnet, Opus, and K3 lanes, effort is
never a predetermined tier. The boss chooses an effort *per task* — low for
the trivial end, max when the task earns it — and passes it explicitly on
every dispatch (`--effort low|high|max`). "Adaptive" means chosen per task,
not omitted. The codex lanes are the exception: they stay fixed cells (tier
via model slug, effort via engine arg).

The binding routing table (canonical version in
`overlay/rules/model-routing.md`; this is a snapshot):

| Task shape | Primary cell | Backup |
|---|---|---|
| Math / quant verification | **Sol-max** (codex) | Terra-xhigh |
| Math independent re-derivation (paper/trade math) | **Opus**, effort adaptive (usually earns max) | Terra-xhigh (same-family-as-Sol caveat) |
| Substantial code feature | **K3**, effort adaptive — *probation* (unsupervised dispatches cap at effort high) | Sol-high (standing backup during probation) |
| Code fix / hotfix / minimal diff | **Terra-xhigh** (codex) | K3, Sonnet |
| Small/medium executor & build | **Sonnet**, effort adaptive | K3, Terra-xhigh |
| Architecture / design review | **K3**, effort adaptive | Opus second opinion (usually earns max) |
| Taste-gated (UI, copy, user-facing docs) | **K3**, effort adaptive | Sonnet |
| Exploratory / live-web research | **Opus or Sonnet** — the boss judges model *and* effort per task | K3 |
| Bounded research (repo lookup, DB scrape) | **Sonnet or Opus** — the boss judges model *and* effort per task | K3 |
| Mechanical / bulk transforms, probes, smokes | **Luna-xhigh** (codex) — *probation* (Sonnet standing backup until 3+ real bulk tasks pass) | Sonnet, Terra-xhigh |
| Scheduled / background batch jobs | **Sonnet**, effort adaptive (generous timeouts) | K3, Luna-xhigh |
| Test-hardening | **Sol-high** (codex) | Sonnet |
| Diff review — non-blocking, small diffs | **Terra-xhigh or Sonnet**, in rotation (cheapest capable; same-family review allowed) | K3, Luna-xhigh |
| Diff review — gating (blocks a merge or step) | **Sonnet**, effort adaptive | K3, Terra-xhigh |
| Gate on irreversible / high-stakes actions (public publish, prod deploy, security-touching) | **Opus**, effort adaptive (usually earns max) | — |
| Consult (engineering second opinion) | **Terra-high** | — |
| Premium steady lane (must-not-wobble) | **Opus** (usually earns max) | — |

**Qwen: deleted from the fleet (2026-07-24).** The Token Plan cut its
qwen3.8-max usage — historical context, not a live lane — killing the
cap-arbitrage rationale, so every qwen lane was deleted in full, with no
fallbacks: the removed engines `qwen`, `qwencode`, `qwenclaude`, and
`kimiqwen` (all deleted from the Ringer config), the shims deleted, and
the kimi-code qwen provider removed. The old qwen scope rule (bounded *and*
off the critical path) died with the deleted lane; qwen's historical rows
remain in the eval log and `docs/MODEL-NOTES.md` only. Do not rebuild the
lane without a fresh operator directive.

**Diff review is tiered by what a wrong verdict costs, not by diff size.**
Non-blocking small diffs go to the cheapest capable cell — on correctness
these lanes are interchangeable at ordinary review sizes — with Terra-xhigh
and Sonnet **rotating**: running both keeps the codex lane's scoreboard rows
live instead of fossilizing on a single pick. A review that *blocks* a merge
or step goes to Sonnet, because a gate's latency is part of its quality. A
gate on an **irreversible or high-stakes action** — a public publish, a
production deploy, anything security-touching — goes to Opus at whatever
effort the task earns, because wrong-and-merged costs more than
slow-and-right. The escalation trigger is always "what does it cost if the
reviewer is wrong" — and a failed review escalates one rung without asking:
luna/terra → sol-high → sol-xhigh → sol-max (or opus-max).

**Bulk moved to Luna-xhigh — on probation.** With the qwen lane deleted,
the bulk/mechanical/probes/smokes lane was refilled on executed evidence: an 8/8
first-try bakeoff across luna-xhigh, luna-max, terra-xhigh, and sonnet-low.
Luna-xhigh matched Terra-xhigh on quality and token counts at the cheapest
GPT tier, and luna-max added nothing over xhigh — so the lane is Luna-xhigh,
with Sonnet as standing backup until 3+ real bulk tasks pass first-try. The
probation mirrors the K3 feature-lane pattern: the first real-bulk failure
or 3+ passes resolves it either way.

**The math re-derivation partner is Opus.** Math that feeds a paper or a
trade gets a Sol derivation plus an *independent* re-derivation, checks
executed — agreement to 4+ digits or it doesn't ship. The partner seat moved
to Opus (usually at max effort) on the strength of a blind rundown: two
Sol-max-authored problems, a tamper-tested verifier, and Opus matched the
ground truth to full float precision, first-try, self-validating each answer
with two independent implementations — while K3 at max effort double-failed
the same task as a silent no-op (see the exclusions below). The cross-family
OpenAI↔Anthropic decorrelation the seat exists for is preserved.

**Why the feature lane flipped to K3 — and why the flip is staged.** K3's
parsimony is a virtue in feature coding: it writes the diff the spec asks
for and stops. But every measurement of K3 through the Claude harness so
far is on *small* tasks — the lane has never carried a multi-minute build.
So the previous owner, Sol-high, remains the **standing backup** until K3
accumulates 3+ feature passes first-try at ≥ 0.67 on the promotion ladder.
And the broadened K3-at-max ban (below) binds directly here: unsupervised
feature dispatches cap at **effort high**; max only with the boss actively
reviewing mid-task.

**Fixes moved to Terra-xhigh** for two reasons that compound: Terra was the
proven backup on exactly this lane, and moving fixes off K3 frees that
subscription's capacity for the feature lane that K3 now carries.

**Architecture review swapped to K3, with Opus as the second opinion.**
Both lanes had clean audition sheets, so the assignment was interchangeable
on evidence — and the swap concentrates the Kimi plan on low-volume,
high-value work while Opus's slower, meticulous style is spent where a
second reading actually changes outcomes.

**The research lanes are Claude-family owned.** Exploratory and bounded
research both route to Opus or Sonnet, with the boss judging model *and*
effort per task — Opus for hard or open-ended questions and lookups whose
answer feeds a decision, Sonnet for lighter sweeps. K3 is the only backup:
a repo lookup or DB scrape is usually *on* the critical path — something is
blocked waiting on the answer — and on the critical path, slow *is*
failure.

**Test-hardening stays on Sol-high, with the backup moved to Sonnet.** The
backup was qwen's background test batches; with the qwen lane deleted, the
fallback is Sonnet. (The historical concern about qwen writing unrequested
tests was gathered under a different harness and never re-verified against
the current one — retired with the lane, never disproven.)

**Scheduled background/batch jobs are a Sonnet lane.** Off-peak batch runs
when contention with live sessions on the shared Claude subscription is
lowest, with generous timeouts; K3 and Luna-xhigh back it up.

**Harness follows the boss.** A fleet can have more than one boss — e.g. a
K3 boss alongside the Fable boss — and each boss routes its K3 worker lane
through its own harness: the **Kimi CLI engine** for a K3 boss, the
**`claude-kimi` wrapper** (below) for the Fable boss. The adaptive
`--effort` rule applies to the Claude-harness lane; through the Kimi CLI,
K3's effort is selected by **model alias** instead (the alias is the effort
carrier — there is no `--effort` flag). The harness choice is not cosmetic:
a paired A/B (same tasks, effort high, executed checks) measured the Claude
harness at **2.2–3.3× faster, 2.3–2.9× less raw token traffic, and 2–4
requests per task vs the Kimi CLI's 6–10** — decisive because the plan is
request-metered (300–1200 requests per 5 hours, max 30 concurrent). Prefer
the Claude harness for K3 workers wherever the boss allows. Same workers,
same doctrine, different wire — and the scoreboard attributes results per
engine, so harness differences stay visible in the evidence.

**Hard exclusions** (as load-bearing as the assignments, each backed by a
documented incident):

- **Terra never does live-web research** — it fabricated a "verbatim" quote
  by stitching two regions of a page.
- **K3 at max effort never runs unsupervised deliverable tasks — of any
  shape** (broadened from builds-only). The failure is a silent walk-away,
  and it is not build-specific: in the math-partner rundown, K3 at max
  effort read the two problem files, wrote nothing, said nothing, and
  exited 0 — twice, including the retry with failure context injected. K3
  at max is a thinker/second-opinion with the boss in the loop, only; **all
  unsupervised K3 dispatches cap at effort high.**
- **K2.7 slugs are banned fleet-wide** — including the Kimi endpoint's
  `kimi-for-coding[-highspeed]` slugs, which are K2.7 under new names.
- **GLM-5.2 is unplugged** — the boss adjudicates disagreements instead of a
  tie-breaker lane.
- **Never Haiku for substantive work.**

**Known issue — harness noise from the `claude` engine.** The `claude`
worker engine runs against the machine's main Claude Code config, so the
operator's global rules leak into Sonnet and Opus workers — both have
dropped stray scaffolding (a `quality_reports/` directory) into task dirs,
violating explicit one-deliverable contracts. It isn't fixable by config
isolation without breaking the OAuth login, so treat stray `quality_reports/`
in worker output as harness noise and write checks that tolerate it.

Budget by **subscription caps and latency**, not per-token price: every
worker lane is flat-rate within a plan cap, so routing decisions are about
which cap has headroom and which cell is fast enough — not imagined
capability gaps. Every lane clears the capability floor at ordinary task
sizes; the scoreboard proved that. The current cap flow: the **OpenAI plan**
carries six lanes — math, fixes, test-hardening, consult, a share of the
non-blocking review rotation, and now bulk/mechanical on Luna (the new
highest-volume lane, but on the cheapest GPT tier): watch this cap first.
The **Kimi plan** carries features, architecture review, and taste —
low-volume, high-value work, the right shape for that cap. The **Claude
plan** is still the heaviest — executor, both research lanes, gating
reviews, the premium steady lane, the math re-derivation second leg, and
scheduled batch — relieved of bulk, but shared with live sessions.

## Claude Code as a universal harness

The most unusual — and most valuable — piece of this setup is running
**Kimi K3 as a worker through the Claude Code CLI**, by pointing it at its
Anthropic-compatible endpoint. The lane is a short POSIX wrapper
(`overlay/bin/claude-kimi`) that sets environment variables and `exec`s the
stock `claude` binary:

```sh
#!/bin/sh
# The pattern (values simplified — see overlay/bin/ for the real script):
export ANTHROPIC_BASE_URL="<the vendor's Anthropic-compatible endpoint>"
export CLAUDE_CONFIG_DIR="$HOME/.claude-<lane>-config"   # isolated; see below
export ANTHROPIC_API_KEY="$(cat <path-to-key-file>)"
unset ANTHROPIC_AUTH_TOKEN   # a stale token can shadow the key
# Pin every model path to the sanctioned slug, and budget the endpoint's
# native 1M context:
export ANTHROPIC_MODEL="k3[1m]"
export ANTHROPIC_DEFAULT_FABLE_MODEL="k3"
export ANTHROPIC_DEFAULT_OPUS_MODEL="k3"
export ANTHROPIC_DEFAULT_SONNET_MODEL="k3"
export ANTHROPIC_DEFAULT_HAIKU_MODEL="k3"
export ANTHROPIC_SMALL_FAST_MODEL="k3"
export CLAUDE_CODE_SUBAGENT_MODEL="k3"
export CLAUDE_CODE_MAX_CONTEXT_TOKENS=1000000
exec claude "$@"
```

One endpoint is wired this way:

- **Kimi** (`claude-kimi`): `https://api.kimi.com/coding/` — Kimi officially
  supports Claude Code against this endpoint; K3 here is natively 1M context
  and honors the `--effort` knob (verified by A/B: a primes-counting task at
  low vs max effort produced measurably different thinking-token counts,
  both correct against a sieve-computed ground truth). The wrapper was
  rewired per the vendor's Claude Code docs: **all** Claude Code alias env
  vars (the per-tier defaults and the subagent model) are pinned to `k3`,
  `ANTHROPIC_MODEL="k3[1m]"`, and `CLAUDE_CODE_MAX_CONTEXT_TOKENS=1000000` —
  the endpoint serves K3 at 1M context natively, and the pin is what makes
  Claude Code actually budget it. Honest caveat: the 1M budget is
  configured but behaviorally unverified until a long task exercises it.
  (A second endpoint — the since-deleted qwen, via a removed `claude-qwen`
  wrapper — used to be wired the same way; it was removed with the rest of
  the deleted qwen lane.)

**Why this beat the native CLIs:**

- The Kimi CLI was fine but slower and thirstier: on identical tasks with
  identical checks at effort high, `claude-kimi` ran **2.2–3.3× faster**
  with **2.3–2.9× less raw token traffic**, and — decisive on a
  request-metered plan (300–1200 requests per 5 hours, max 30 concurrent) —
  spent **2–4 requests per task vs the CLI's 6–10**. Both harnesses remain
  in service — the Kimi CLI carries K3-bossed work, the wrapper carries
  Fable-bossed work (see "Harness follows the boss" above) — but the Claude
  harness is preferred for K3 workers wherever the boss allows.
- Historical note (the qwen lane itself is deleted): the same pattern once
  rescued that lane — the native Qwen CLI of the deleted lane repeatedly
  **stalled or silently died on heavy tasks** (two 1800s timeouts; a
  43-minute zero-output run), while through Claude Code the *same backend*
  ran identical probe tasks in 26–31s vs 81s+ and went 5/5 first-try on the
  capacity screen. The harness was the problem, never the model — recorded
  here as history; the lane itself is gone.
- Bonus diagnostic capability: the isolated config dir keeps full per-event
  session JSONL transcripts, which turned a "worker stalled" verdict into a
  "the orchestrator set the timeout too tight; transcript shows continuous
  work" correction.

## Testing and upgrading your own lanes

The wrappers and routing table above are the *output* of a process. This
section is the process itself: how to safely add a worker lane, or upgrade an
existing one, on your own endpoints and subscriptions. Every step ends in an
executed check — never in "it obviously works."

**1. Probe first — no lane carries real work on a handshake.** Before a new
lane touches a real task, run a one-task Ringer probe with an executed check
through it and require a pass. The manifests in `overlay/probes/` are the
pattern: a small task, a self-contained spec, a check that verifies content.
A lane that can't pass a probe can't be trusted with a queue, and a probe
costs almost nothing to run.

**2. Screen for capacity with identical tasks and identical checks.** When a
new lane is a candidate to displace an existing one, run the *same* screening
tasks with the *same* checks through both, so the scoreboard rows are
directly comparable — same spec, same check, same timeout. The displacement
bar is **equal-or-faster with a clean sheet**: first-try passes everywhere,
no retries, no stalls. Anything less and the incumbent keeps the lane.

**3. Verify the effort knob empirically — never assume a flag maps through a
third-party endpoint.** A/B the same task at low vs max effort against a
ground truth you computed yourself (e.g. count primes up to N by sieve, then
ask the lane at both efforts), and measure the actual thinking-token output
at each setting. On one endpoint here, `--effort` produced measurably
different thinking counts and correct answers at both settings — knob
confirmed. On a second endpoint (since removed from the fleet), request
sniffing showed the CLI sends the effort fields and the endpoint ignores
them — one full-thinking cell, and routing was adjusted accordingly while
the lane lived. The endpoint's documentation is a hypothesis; the A/B is the
verdict.

**4. Verify auth at the wire.** Run a local header-capture server (a dozen
lines of Python), point the wrapper at it, and confirm exactly which
credential leaves the machine. The failure this catches: an OAuth-logged-in
main Claude config **silently shadows env-var tokens** — requests go out
carrying the main config's OAuth bearer instead of your lane key, and the
endpoint 401s a perfectly good key. That is why each wrapper exports an
**isolated `CLAUDE_CONFIG_DIR`** with no OAuth session, so the env token
wins. Corollary for debugging: a 401 through a wrapper implicates the
harness's credential *precedence* before the credential itself.

**5. Pin every model path.** Some endpoints silently alias unknown model
slugs — they return HTTP 200 for *anything*, echo your requested name back,
and serve whatever they feel like. And the harness makes internal
"small fast model" calls of its own (title generation, compaction), so
unspecified traffic can be served by an undisclosed default. Pin **every**
model env var the harness honors — the per-tier defaults, the subagent
model, the small-fast slot — to a sanctioned slug on that endpoint so *no*
traffic leaves the approved model — and never trust an echoed model name as
confirmation of what served the request. Capture-or-pin, never assume.

**6. Operate like keys, timeouts, and promotions all have blast radius — they do.**
   - **Rotate keys everywhere they live.** If the same key exists in two
     config files, rotate both, or one lane starts 401ing the day you rotate
     the other.
   - **Check timeout verdicts against the session transcript before blaming
     the model.** Two "hung" runs here turned out to be continuously working
     (100+ events, dozens of tool calls each) — the orchestrator's timeout
     was simply too tight for a 100+-turn grind. Heavy single-grind tasks
     get generous timeouts or get split.
   - **Advance lanes on the promotion ladder, and record demotions.** A lane
     earns scope: **untested → probation → proven** (3+ tasks in a task type
     with first-try ≥ 0.67). Proven lanes get bigger assignments and an
     audition one rung up; repeated first-attempt failures end the audition,
     and the demotion goes in the notes with the evidence, so the scoreboard
     stays an honest memory instead of a highlight reel.

## The scoreboard and the evidence loop

Routing doctrine is only as good as its evidence, so every attempt lands in
an append-only eval log (`~/.ringer/runs.jsonl`: model, task_type, retry
count, tokens, duration, verdict), and three mechanisms keep the doctrine
honest:

- **The scoreboard** — `ringer.py models` aggregates the log per (model,
  task_type): `first_try_pass_rate` is the routing signal; `pass_rate`
  includes retry rescues. `docs/MODEL-NOTES.md` is the dated judgment layer
  on top of the numbers — what happened, what the failure mode was, what
  you'd do differently, written only from what executed checks and raw logs
  support. Rows whose FAIL was actually a *check bug* are annotated so they
  don't poison the signal.
- **The promotion ladder** — models earn lanes: **untested → probation →
  proven** (3+ tasks in a task_type with first-try ≥ 0.67). Proven models
  get bigger lanes and an audition one rung up; repeated first-attempt
  failures end the audition and the demotion is recorded.
- **Explore or fossilize** — in any low-stakes run of 3+ tasks, roughly ONE
  task goes to an untested cell with a strong executed check (the retry
  absorbs failure). Always recommending the proven pick means never learning
  a new one; the scoreboard would freeze in its initial state.

**Capacity screens** are how new lanes earn trust: the *identical* screening
tasks with the *identical* checks run through the new engine, so rows are
directly comparable across lanes. That's how `claude-kimi` displaced the
Kimi CLI for Fable-bossed work in one afternoon (5/5 first-try,
equal-or-faster everywhere), how Luna-xhigh won the bulk lane (8/8
first-try bakeoff), and how the since-deleted qwen lane's heavy-load
behavior was validated post-incident.

**The probe doctrine:** every new lane or model change goes through a
passing Ringer probe with an executed check *before it carries real work*
— see `overlay/probes/` for the manifests. No exceptions, no "it obviously
works."

## Install and setup

You need three things: the tool, the personal layer, and the subscriptions.

**1. Clone and place the overlay.**

```bash
git clone <this-repo-url> fable-ringer
cd fable-ringer
```

The altered upstream lives at the repo root and runs as `./ringer.py`. The
personal layer in `overlay/` is deployed to standard locations:

| Overlay path | Deploy to | Purpose |
|---|---|---|
| `overlay/bin/claude-kimi` | Somewhere on `$PATH` (e.g. `~/.local/bin/`) | Worker-lane wrapper script |
| `overlay/config/config.toml.example` | `~/.config/ringer/config.toml` | Engine wiring; adapt paths to your machine |
| `overlay/probes/` | `~/.ringer/probes/<probe-name>/` | Lane-probe manifests; write their referenced check scripts alongside at deploy time |
| `overlay/rules/model-routing.md` | `~/.claude/rules/model-routing.md` | The canonical routing table the boss reads |
| `overlay/skills/ringer/SKILL.md` | `~/.claude/skills/ringer/SKILL.md` | The orchestrator playbook the boss loads |

**2. Subscriptions and keys (named by kind — bring your own).**

| Lane | What you need |
|---|---|
| codex (GPT-5.6 Sol/Terra/Luna) | An OpenAI plan with Codex CLI access (OAuth login) |
| claude (Sonnet/Opus) | A Claude subscription; the Claude Code CLI, logged in |
| kimiclaude (K3) | A Kimi Code membership + an API key from the Kimi Code Console, stored in a `0600` file the wrapper reads |

No credential is stored in this repo, and none should ever appear in a
manifest, spec, or check.

**3. Validate before real work.**

Wire one engine, then run a probe manifest from `overlay/probes/` and
confirm the executed check passes. Add lanes one at a time, each behind its
own passing probe. Only then route real work.

## Repository layout

```
fable-ringer/
├── ringer.py              # The orchestrator (altered upstream)
├── engines/               # Worker-engine helpers (sandbox shims, mock worker)
├── templates/             # Manifest skeletons: review-swarm, fix-swarm,
│                          #   bakeoff, research-with-proof, probe, …
├── scripts/               # Eval-log backfill and maintenance tools
├── tests/                 # The orchestrator's own test suite
├── dashboard/, hud/       # Ringside: the live run page + HUD
├── registry/              # Model registry used for scoreboard attribution
├── docs/
│   ├── UPSTREAM-README.md # The original project's README, preserved
│   ├── MODEL-NOTES.md     # The evidence trail (dated, executed-check-only)
│   └── …                  # Steering, taxonomy, screenshots
├── overlay/               # The operator's configuration layer (the point of this repo)
│   ├── bin/               #   claude-kimi wrapper script
│   ├── config/            #   config.toml.example (engine wiring)
│   ├── rules/             #   model-routing.md — the canonical routing table
│   ├── skills/ringer/     #   SKILL.md — the orchestrator playbook
│   └── probes/            #   Capacity-screen and lane-validation manifests
├── LICENSE.md             # PolyForm Shield 1.0.0 + Required Notice
└── README.md              # You are here
```

Everything outside `overlay/` tracks the upstream tool (with alterations);
everything inside `overlay/` is the configuration, doctrine, and evidence
that make it *this* system.

## A day in the life

1. The operator describes a job. Fable writes a manifest: one task per
   checkable unit, each with a self-contained spec, a routing cell, and an
   executable check. `ringer.py lint` catches unverifiable checks, silent
   checks, file ownership collisions, and underspecified specs before
   anything runs.
2. `ringer.py run manifest.json --identity fable` — Ringside (the live
   dashboard) comes up first so you watch the swarm, not a silent terminal.
3. Workers execute in parallel, each in its own task dir. Ringer runs every
   check; failures retry once with the check's failure output injected.
4. Fable reads the run JSON, reads the raw logs of anything retried or
   failed, spot-checks at least one *passing* artifact, and re-executes the
   real command itself whenever a check turned out to be wrong.
5. The run teaches something about a model → one dated line in
   `docs/MODEL-NOTES.md`; the numbers update themselves in `runs.jsonl`.
   Routing improves next time.

## Credit and license

**Ringer and Ringside are created by Nate Jones (Nate Jones Media LLC).**

- Upstream: <https://github.com/NateBJones-Projects/ringer>
- License: **PolyForm Shield 1.0.0**

This repository redistributes the upstream code with alterations under that
same license, with the Required Notice preserved in `LICENSE.md`. The
boss/worker doctrine, the routing table, the wrapper scripts, and the
operational evidence described in this README are this repo's operating layer
on top — but the tool that makes any of it verifiable is Nate's.
