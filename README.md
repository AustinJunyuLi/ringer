# fable-ringer

**Austin's Fable-bossed configuration of Ringer** — a verified-swarm
orchestrator where one expensive model (Claude Fable 5) plans, routes, and
reviews, and a fleet of cheaper, cross-family worker models does all the
typing — with every single task graded by an *executed* check, not by what
the worker claims it did.

This repository is the altered upstream tool plus Austin's personal operating
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
- [Operational lessons (learned the hard way)](#operational-lessons-learned-the-hard-way)
- [The scoreboard and the evidence loop](#the-scoreboard-and-the-evidence-loop)
- [Install and setup](#install-and-setup)
- [Repository layout](#repository-layout)
- [A day in the life](#a-day-in-the-life)
- [Credit and license](#credit-and-license)

---

## The architecture in one paragraph

A human (Austin) talks to **Claude Fable 5**, the sole boss. Fable decomposes
the job into a **manifest** of tasks, writes a self-contained spec and an
executable check for each, and dispatches them to **worker models from four
different families** — OpenAI's GPT-5.6 (Sol/Terra) through the Codex CLI,
Moonshot's Kimi K3 and Alibaba's Qwen through the Claude Code harness pointed
at their Anthropic-compatible endpoints, and Anthropic's own Sonnet/Opus
natively. Ringer runs the tasks in parallel, executes each task's check
command, and only an exit code of 0 counts as a pass. Failures are retried
once with the check's actual failure output injected into the retry prompt.
Fable then reads the results, spot-checks the raw logs, and synthesizes.
**Fable never types implementation** — not inline, not in a subagent. The
boss pays tokens only for thinking; the workers pay for typing.

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
not omitted. Qwen is the exception: its endpoint ignores the effort knobs
entirely (verified by request sniffing — the CLI sends them, the endpoint
frees them), so **qwen is exactly one cell, always full thinking**.

The binding routing table (canonical version in
`overlay/rules/model-routing.md`; this is a snapshot):

| Task shape | Primary cell | Backup |
|---|---|---|
| Math / quant verification | **Sol-max** (codex) | Terra-xhigh |
| Substantial code feature | **Sol-high** (codex) | Sol-xhigh (deliberate escalation only) |
| Code fix / hotfix / minimal diff | **K3**, effort adaptive (kimiclaude) | Terra-xhigh, Sonnet |
| Small/medium executor & build | **Sonnet**, effort adaptive | K3, Terra-xhigh |
| Architecture / design review | **Opus**, effort adaptive | K3 second opinion (usually earns max) |
| Taste-gated (UI, copy, user-facing docs) | **K3**, effort adaptive | Sonnet |
| Exploratory / live-web research | **Opus**, effort adaptive | K3 |
| Bounded research (repo lookup, DB scrape) | **Qwen** (qwenclaude) | K3 |
| Mechanical / bulk transforms, probes, smokes | **Qwen** (qwenclaude) | Sonnet, Terra-xhigh |
| Test-hardening | **Qwen** | Sol-high |
| Diff review | Cheapest capable cell: qwen / sonnet / k3 / terra-xhigh | — |
| Consult (engineering second opinion) | **Terra-high** | — |
| Premium steady lane (must-not-wobble) | **Opus** (usually earns max) | — |

**Hard exclusions** (as load-bearing as the assignments, each backed by a
documented incident):

- **Terra never does live-web research** — it fabricated a "verbatim" quote
  by stitching two regions of a page.
- **K3 at max effort never types unsupervised builds** — the sloppy-verify
  failure was model personality, not harness; it survived a harness swap.
- **K2.7 slugs are banned fleet-wide** — including the Kimi endpoint's
  `kimi-for-coding[-highspeed]` slugs, which are K2.7 under new names.
- **GLM-5.2 is unplugged** — the boss adjudicates disagreements instead of a
  tie-breaker lane.
- **Qwen on live-web research: probation only** — the original ban was earned
  by harness stalls, not the model; it's a backup/explore slot until it
  accumulates passes.

Budget by **subscription caps and latency**, not per-token price: every
worker lane is flat-rate within a plan cap, so routing decisions are about
which cap has headroom and which cell is fast enough — not imagined
capability gaps. Every lane clears the capability floor at ordinary task
sizes; the scoreboard proved that.

## Claude Code as a universal harness

The most unusual — and most valuable — piece of this setup is running
**Kimi K3 and Qwen as workers through the Claude Code CLI**, by pointing it
at their Anthropic-compatible endpoints. Each lane is a ~10-line POSIX
wrapper (`overlay/bin/claude-kimi`, `overlay/bin/claude-qwen`) that sets
environment variables and `exec`s the stock `claude` binary:

```sh
#!/bin/sh
# The pattern (values simplified — see overlay/bin/ for the real scripts):
export ANTHROPIC_BASE_URL="<the vendor's Anthropic-compatible endpoint>"
export CLAUDE_CONFIG_DIR="$HOME/.claude-<lane>-config"   # isolated; see below
export ANTHROPIC_AUTH_TOKEN="$(cat <path-to-key-file>)"  # or API_KEY, per endpoint
export ANTHROPIC_SMALL_FAST_MODEL="<a sanctioned slug on that endpoint>"
exec claude "$@"
```

Two endpoints are wired this way:

- **Kimi** (`claude-kimi`): `https://api.kimi.com/coding/` — Kimi officially
  supports Claude Code against this endpoint; K3 here is natively 1M context
  and honors the `--effort` knob (verified by A/B: a primes-counting task at
  low vs max effort produced measurably different thinking-token counts,
  both correct against a sieve-computed ground truth).
- **Qwen** (`claude-qwen`): the Alibaba ModelStudio Token Plan's
  Anthropic-compatible endpoint, which lists Claude Code as an officially
  supported harness. The effort knob is a no-op here (verified by request
  sniffing) — one full-thinking cell.

**Why this beat the native CLIs:**

- The native Qwen CLI (`qwencode`) repeatedly **stalled or silently died on
  heavy tasks** (two 1800s timeouts; a 43-minute zero-output run). Through
  Claude Code, the *same backend* ran identical probe tasks in 26–31s vs
  81s+, went 5/5 first-try on the capacity screen, and later passed a
  15.6-minute heavyweight code-review audition first-try. The harness was
  the problem, never the model.
- The Kimi CLI was fine but slower: on identical tasks with identical
  checks, `claude-kimi` matched or beat it on all five, with the
  live-research task **4.8× faster** (256s vs 1224s).
- Bonus diagnostic capability: the isolated config dir keeps full per-event
  session JSONL transcripts, which turned a "worker stalled" verdict into a
  "the orchestrator set the timeout too tight; transcript shows continuous
  work" correction.

## Operational lessons (learned the hard way)

These are the incidents behind the wrappers' exact shape. Each is documented
with executed evidence in `docs/MODEL-NOTES.md`.

1. **An OAuth keychain login silently shadows env-var auth tokens.**
   `claude-qwen` started returning `401 Invalid API-key` on every call. The
   key was fine. A local header capture showed the requests reaching the qwen
   endpoint carrying `Authorization: Bearer sk-ant-oat01-…` — the *main*
   Claude config's OAuth token, which outranks `ANTHROPIC_AUTH_TOKEN`. Fix:
   each wrapper exports an **isolated `CLAUDE_CONFIG_DIR`** with no OAuth
   session, so the env token wins. Corollary: a 401 through a wrapper harness
   implicates the harness's credential precedence *before* the credential
   itself.

2. **Endpoints silently alias unknown model slugs.** The Kimi endpoint
   returns HTTP 200 for *any* model slug — including Claude ones — and
   serves *something*. Claude Code makes internal "small fast model" calls
   (title generation, compaction), so unspecified traffic was being served by
   an undisclosed default — likely a banned K2.7 slug. Fix: pin
   **`ANTHROPIC_SMALL_FAST_MODEL`** to a sanctioned slug (`k3` on Kimi,
   `qwen3.6-flash` on qwen) so *no* traffic leaves the approved model.

3. **Never trust an endpoint's echoed model name.** An Anthropic-compatible
   endpoint that echoes back the model you requested is *not* confirming what
   served the request. Verify at the byte level: capture the wire headers
   (confirmed `x-api-key: sk-kimi-…` on the Kimi lane, `Bearer sk-sp-…` on
   the qwen lane, zero `sk-ant-` leakage on either), or pin the slug.
   Capture-or-pin, never assume.

4. **Key rotation has a blast radius.** The same qwen key lives in two
   config files; rotate in both or one lane 401s.

5. **"Stall" verdicts require a transcript check first.** Two "hung" qwen
   runs were continuously working (127–131 events, ~75 tool calls each) —
   the orchestrator's timeout was just too tight for a 100+-turn task.
   Heavy single-grind tasks now get 3600s+ or get split.

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
Kimi CLI in one afternoon (5/5 first-try, equal-or-faster everywhere), and
how the qwen lane's heavy-load behavior was validated post-incident.

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
| `overlay/bin/claude-kimi`, `claude-qwen` | Somewhere on `$PATH` (e.g. `~/.local/bin/`) | Worker-lane wrapper scripts |
| `overlay/config/config.toml.example` | `~/.config/ringer/config.toml` | Engine wiring; adapt paths to your machine |
| `overlay/rules/model-routing.md` | `~/.claude/rules/model-routing.md` | The canonical routing table the boss reads |
| `overlay/skills/ringer/SKILL.md` | `~/.claude/skills/ringer/SKILL.md` | The orchestrator playbook the boss loads |

**2. Subscriptions and keys (named by kind — bring your own).**

| Lane | What you need |
|---|---|
| codex (GPT-5.6 Sol/Terra) | An OpenAI plan with Codex CLI access (OAuth login) |
| claude (Sonnet/Opus) | A Claude subscription; the Claude Code CLI, logged in |
| kimiclaude (K3) | A Kimi Code membership + an API key from the Kimi Code Console, stored in a `0600` file the wrapper reads |
| qwenclaude (Qwen) | An Alibaba ModelStudio Token Plan key for its Anthropic-compatible endpoint, stored in a config file the wrapper reads |

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
├── overlay/               # Austin's personal layer (the point of this repo)
│   ├── bin/               #   claude-kimi, claude-qwen wrapper scripts
│   ├── config/            #   config.toml.example (engine wiring)
│   ├── rules/             #   model-routing.md — the canonical routing table
│   ├── skills/ringer/     #   SKILL.md — the orchestrator playbook
│   └── probes/            #   Capacity-screen and lane-validation manifests
├── LICENSE.md             # PolyForm Shield 1.0.0 + Required Notice
└── README.md              # You are here
```

Everything outside `overlay/` tracks the upstream tool (with Austin's
alterations); everything inside `overlay/` is the configuration, doctrine,
and evidence that make it *this* system.

## A day in the life

1. Austin describes a job. Fable writes a manifest: one task per checkable
   unit, each with a self-contained spec, a routing cell, and an executable
   check. `ringer.py lint` catches unverifiable checks, silent checks, file
   ownership collisions, and underspecified specs before anything runs.
2. `ringer.py run manifest.json --identity fable` — Ringside (the live
   dashboard) comes up first so the human watches the swarm, not a silent
   terminal.
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
operational evidence described in this README are Austin's layer on top —
but the tool that makes any of it verifiable is Nate's.
