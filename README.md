# fable-ringer

**Ringer is a toolkit for getting big jobs done by a team of AI assistants — with proof, not promises.** You describe a job to one very capable AI (the "boss"). The boss plans the work, hands the typing to a crew of cheaper AI "workers," and every piece of finished work is graded by actually running a test against it — never by taking the worker's word for it. This repository is the tool itself plus the configuration layer that makes the crew run smoothly.

If you have ever asked an AI to do something large and gotten back something confident, polished, and subtly wrong, this repo is the fix.

---

## Table of contents

- [The problem it solves](#the-problem-it-solves)
- [How it works](#how-it-works)
- [Trust is earned by execution](#trust-is-earned-by-execution)
- [Why models from several companies](#why-models-from-several-companies)
- [Loops and graphs: making long jobs reliable](#loops-and-graphs-making-long-jobs-reliable)
- [Choosing which model does what](#choosing-which-model-does-what)
- [Getting started](#getting-started)
  - [Advanced: adding more worker lanes](#advanced-adding-more-worker-lanes)
- [Day to day: one job through the system](#day-to-day-one-job-through-the-system)
- [Repository layout](#repository-layout)
- [Credit and license](#credit-and-license)

---

## The problem it solves

Think of this system as a **general contractor** on a construction job. A good general contractor does not swing a hammer — they hire specialist trades, tell each one exactly what to build, and then *inspect* the work before signing off. Ringer applies that same structure to AI work. Three pressures make the structure necessary.

**Long jobs degrade.** Today's AI assistants are brilliant at short, self-contained tasks. But stretch a job out — a whole website, a long report, a refactor across dozens of files — and small errors compound step by step. By the end, the output looks fluent and is quietly broken in ways that are hard to spot. Worse, the AI's own summary of what it did is not evidence. It will tell you everything went fine whether it did or not, because it is generating a plausible report, not filing test results.

**The smartest models are scarce.** The most capable AI models come with usage limits, and they are the same models you want available for your own live conversations. If your best model does both the *thinking* (planning, judging, reviewing) and the *typing* (grinding out page after page of content or code), you spend your scarcest resource on the cheap part of the job. A general contractor who personally installs every cabinet is wasting the one person who can read the blueprints.

**Unverified output does not scale.** Without independent checks, the only way to trust AI work is to re-check it yourself, line by line. Do that honestly and you have erased the time you saved. Verification has to be built into the pipeline — automatic, executed by a machine, and impossible to sweet-talk — or the whole arrangement collapses back into manual review.

Ringer's answer to all three: split thinking from typing, and grade every deliverable by running a test against it.

---

## How it works

You talk to one highly capable model — the **boss**. The boss never writes the deliverable. Not a paragraph of the report, not a line of the code. Instead it:

1. **Decomposes** your job into small tasks, each small enough that a worker can complete it well in one sitting.
2. Writes each task a **spec** — a self-contained brief that tells the worker its role, exactly which files it owns, what it must produce, and what it must not touch.
3. Writes each task a **check** — an executable test, a plain shell command that examines what the worker actually produced and exits with code 0 (pass) or anything else (fail).
4. Bundles the tasks into a **manifest** — a single JSON file listing every task with its spec and check — and dispatches them, in parallel, to **worker** AIs from several different companies.
5. Reads the results, spot-checks at least one passing artifact with its own eyes, and reports back to you.

After each worker finishes, Ringer **executes the check**. A task passes only if the check exits with code 0 **and** every deliverable the task declared is actually present and non-empty — exit code 0 alone is not a PASS. A failed task is retried exactly once, with the check's real failure output pasted into the retry prompt so the worker can see what it got wrong. Every attempt — pass, fail, retry — is logged to a local **scoreboard** on your machine, so decisions about which model to trust are grounded in measured results.

| The boss (your premium model) | The workers (cheaper models, several companies) |
|---|---|
| Breaks the job into tasks | Execute one task each, in parallel |
| Writes each spec (the brief) | Produce the deliverables — code, docs, research |
| Writes each check (the test) | — |
| Chooses which model gets which task | — |
| Reads results, spot-checks artifacts, reports to you | — |

The separation is a hard rule, not a style choice. A boss that "just fixes this one thing itself" stops being an orchestrator: that fix never gets verified, never gets logged, and the scoreboard starves. Even a three-line change runs as a one-task manifest, because that is what makes it visible, verified, and counted.

---

## Trust is earned by execution

The heart of the whole system is one sentence: **worker claims are not evidence.** Ringer does not ask the worker whether the job is done. It runs the check.

This rule is not theoretical. It was adopted because AI workers — as a class, no vendor exempt — have been caught, on executed evidence:

- Reporting **"all 213 quotes match exactly, 0 errors"** while the executed check found 13 quotes that were stitched together or paraphrased.
- Hiding required text in an **invisible part of a web page** so a content check would find it, without the text ever being visible to a reader.
- Claiming **"the previous attempt already verified this"** without re-running anything — and shipping a program with a real bug.

Note what these have in common: none of them were caught by reading the worker's report. The reports were confident. The checks are what caught them.

Out of these incidents come the craft rules for writing checks, in plain terms:

- **Checks must say *why* they fail, not just *that* they failed.** The failure text is injected into the worker's retry prompt and saved to the log. A check that prints "mismatch on line 41: expected X, got Y" gives the retry something to fix. A check that silently exits 1 wastes the retry.
- **Verify content, not existence.** A check that only asks "does the file exist?" invites exactly the corner-cutting described above. Open the artifact, grep it for the required substance, run the program it produced, execute the build.
- **A check that cannot fail is not a check.** A test that always passes is just trusting the worker with extra steps.
- **Be strict about substance, tolerant about formatting.** Fail hard on missing evidence or code that does not run. Be flexible about headings, capitalization, and phrasing — a check that fails on cosmetics trains workers to polish surfaces instead of fixing substance.

---

## Why models from several companies

The natural question: *why not just use Claude for everything?* Three reasons — and we will be careful to claim only what our own executed checks have shown, at our task sizes, not universal leaderboard truths.

**Economics.** Most AI subscriptions are flat-rate up to a usage cap. One provider means one cap — a hard ceiling on how much work can run at once — and every background task competes with your own live sessions for that same cap. Several providers means several independent caps: real parallel throughput, with the premium model's capacity reserved for the thinking only it can do. The general contractor does not put the master carpenter on drywall duty; the master carpenter reads blueprints while three drywall crews work in parallel.

**Decorrelation.** Models built by the same company share training lineage, and shared lineage means shared blind spots. Ask two same-family models to check each other and they can nod along to the same mistake. So for results that must not be wrong — math that feeds a paper or a financial decision, say — this system requires an *independent re-derivation* by a model from a *different* company, with both answers verified by executed code. They agree, or the work does not ship.

**Comparative advantage.** Different model families genuinely are better at different things. What follows is what we have observed on our own executed checks; our samples are modest, so treat these as working hypotheses that the scoreboard keeps testing, not permanent facts:

- **OpenAI's GPT family** (run through the Codex command-line tool) has been our strongest lane for exact mathematical and quantitative derivation, and for fast, surgical, minimal-diff code fixes. The cheaper GPT tier handles high-volume mechanical work well. Observed weakness: in live-web research, one GPT worker fabricated a "verbatim" quote by stitching text from two different parts of a page — so that family is banned from our live-web research lane.
- **Anthropic's Claude family** (Sonnet and Opus) has been our strongest lane for long tool-using sessions, web research, and reviews where a wrong verdict is expensive. Opus is the meticulous "must-not-wobble" lane and our independent math re-derivation partner — it matched a verified ground truth to full floating-point precision. The trade-offs: it is slower, and it shares capacity with the humans' own live Claude sessions.
- **Moonshot's Kimi K3** is notable for parsimony — it does exactly what the spec asks and stops, with no scope creep — and for taste in user-facing writing. The trade-off: at its highest reasoning-effort setting it has silently walked away from tasks (did nothing, reported nothing), so unsupervised runs cap its effort below that setting.

**The punchline:** because every task ends in an executed check, you do not have to trust any single model. Verification — not brand loyalty — is what makes cheaper and faster models safe to use. When the building inspector pressure-tests every pipe, you can hire the affordable plumbing crew without losing sleep.

---

## Loops and graphs: making long jobs reliable

Short tasks are easy. The system's real value is making *long* jobs reliable, and that comes from two ideas, named plainly.

### Loop engineering

A **loop** is any cycle of work, feedback, and correction. A loop is only as good as its feedback signal — a smoke detector that never beeps is worse than none, because it breeds false confidence. Ringer is loops all the way down:

- **The built-in loop** is the smallest: spec → worker does the task → executed check → on failure, retry once with the check's real failure output injected. This is why checks must print *why* they fail: the failure text *is* the feedback signal. A silent check breaks the loop.
- **The boss's loops** sit above that: a review round feeds a fix round feeds a re-review round. After a fix swarm runs, the boss can dispatch the *same* reviewer panel again to see whether the complaints actually went away — not whether the fixers said they fixed things.
- **The slowest loop is the scoreboard.** Every attempt by every worker is logged locally. Over weeks, the log accumulates into evidence about which model to trust with which kind of task. Routing improves because the system remembers.

### Graph engineering

A **graph** here just means: a big job decomposed into many small tasks, with explicit connections between them. Two moves make graphs work:

- **Fan-out in parallel.** Within one manifest, tasks run in parallel — a swarm. Each task owns its own files, declared up front, so two workers can never collide by writing to the same place. This is how a review of ten different surfaces, or fixes to ten different files, happens in the time of one.
- **Chaining between rounds.** Sequencing happens *between* manifests, not inside them. The boss runs one swarm, reads the verified results, then writes the next manifest. A read-only review swarm feeds a fix swarm. A research round feeds a build round feeds an assembly round. A data pipeline runs fetch, then transform, then validate — each stage gated by executed validators before the next begins. The `templates/` directory is a catalog of these proven multi-round patterns (review-swarm, fix-swarm, research-with-proof, data-pipeline, and more), ready to adapt.

One accuracy note worth stating plainly: **Ringer has no built-in dependency scheduler.** Tasks within a single manifest do not wait on each other — they all start together. The "graph" lives in how the boss chains manifests into rounds, and every edge between rounds is gated by executed checks. If task B needs task A's output, they belong in different rounds.

---

## Choosing which model does what

Routing — deciding which worker gets which task — is a principle, not a fixed table you must copy. The principle:

1. **Measure everything.** Every attempt lands in a local log on your machine. Running `./ringer.py models` renders a per-model scoreboard, broken down by kind of task. The routing signal is the **first-try pass rate** — how often a model passes the executed check on attempt one, with no retry rescue.
2. **Models earn scope on a promotion ladder.** A model starts **untested**. After it accumulates some evidence on a kind of task, it has *some evidence*. After several tasks of one kind at a strong first-try pass rate, it is **proven** for that kind of task and can carry real load. New assignments prove themselves on a cheap **probe** task — a tiny manifest whose whole job is to confirm the lane works — before they carry real work.
3. **Keep exploring.** A small slice of low-stakes work deliberately goes to untested models. Always picking the current champion means never discovering a better one — explore a little, or the scoreboard fossilizes. The retry and the executed check absorb the risk of the experiment.

Illustrative outcomes from this operator's scoreboard: exact math routes to a GPT lane; user-facing writing routes to Kimi K3; reviews that gate a decision route to Claude. Your table will differ — your tasks, your subscriptions, and your log are different, and the numbers are not portable between operators. This operator's current routing table lives at `overlay/rules/model-routing.md`; read it as a worked example, not a law.

---

## Getting started

Most of the team has only a Claude subscription, so the **Claude-only path is the primary path**. You can add more worker lanes later — see the advanced section below — but nothing here requires them.

### Prerequisites

- A **Claude subscription**, with the **Claude Code** command-line tool installed and logged in
- **Python 3** (3.11 or newer)
- **git**

### 1. Clone the repo

```bash
git clone <this-repo-url> fable-ringer
cd fable-ringer
```

The tool runs as `./ringer.py` from the repo root. No build step, no package install — it is Python standard library only.

### 2. Wire the configuration

Create `~/.config/ringer/config.toml` with a single engine block — this minimal Claude-only wiring is all you need to start:

```bash
mkdir -p ~/.config/ringer
```

```toml
[engines.claude]
bin = "/path/to/your/claude"   # find yours with: which claude
model_default = "sonnet"
args_template = ["{access_args}", "--model", "{model}", "{engine_args}", "-p", "{spec}"]
sandbox_args = ["--dangerously-skip-permissions"]
full_access_args = []
```

When you later add more worker lanes, the full multi-lane example lives at `overlay/config/config.toml.example` — consult it then, not now.

### 3. Deploy the boss-side pieces

The `overlay/` directory is the operator's configuration layer — the pieces that teach your Claude session to act as the boss. Deploy them like this:

| Overlay path | Deploy to | Purpose |
|---|---|---|
| `overlay/config/config.toml.example` | Reference only — do not copy wholesale | Full multi-lane engine wiring, for when you add lanes beyond step 2 |
| `overlay/rules/model-routing.md` | `~/.claude/rules/model-routing.md` | The routing table the boss reads when choosing workers |
| `overlay/skills/ringer/SKILL.md` | `~/.claude/skills/ringer/SKILL.md` | The orchestrator playbook the boss loads |

(There is also `./ringer.py install-agent`, which installs the skill and optional reminder hooks for you; the manual table above shows exactly where everything lives if you prefer to place it yourself.)

### 4. Validate before real work

Do not route real work until you have watched a check pass:

1. Write or adapt a one-task **probe manifest** — the `templates/probe/` kit is the generic starting point, and `overlay/probes/` holds this operator's real examples, whose internal paths you must adapt to your machine. Then lint and run it like any other manifest: `./ringer.py lint <manifest>`, then `./ringer.py run <manifest>`, and confirm the executed check passes. A probe is a tiny, nearly free task whose only job is to prove the whole pipeline — dispatch, worker, executed check, logging — works on your machine.
2. Run the **smoke test**: `./ringer.py demo`. It dispatches three real workers in parallel, verifies each one's output by executing it, and prints a verdict table — and it opens Ringside, the live dashboard, in your browser. Three PASSes means your setup is done.

Then describe a real job to your boss session and let it write the manifest.

### Advanced: adding more worker lanes

Everything above runs on Claude alone. Add the lanes below **when you outgrow one provider's usage cap** — when parallel work queues up behind your own live sessions, or when you want the decorrelation and comparative-advantage benefits described earlier. They are upgrades, not prerequisites.

**The OpenAI lane (GPT family).** You need an OpenAI plan that includes Codex CLI access. Install the Codex CLI and sign in with its OAuth login (`codex login`), then enable the codex engine block in `~/.config/ringer/config.toml`. Validate with a probe before routing real work.

**The Kimi lane (K3).** You need a Kimi Code membership and an API key from the Kimi Code Console. Store the key in a file with `0600` permissions (readable only by you — e.g. `chmod 600 <keyfile>`), sign in with `kimi login`, and enable the `kimi` engine block in your config. Effort is selected per task through per-effort model aliases in `~/.kimi-code/config.toml` (`k3-low` / `k3-high` / `k3-max`), since the CLI has no `--effort` flag.

The wrapper deserves a sentence of explanation, because it is a genuinely useful trick: it points the Claude Code harness — the same tool you already know — at Kimi's Anthropic-compatible endpoint, using its own isolated configuration directory. That means **one familiar harness for every worker**, regardless of whose model is behind it; **an isolated config** so the worker's session never tangles with your own; and **full transcripts** of every worker session saved to disk, which turns "the worker stalled" mysteries into readable evidence. One crew uniform, many crews.

One rule holds across every lane and every setup: **no credential is stored in this repository, and none should ever appear in a manifest, a spec, or a check.** Keys live in your home directory with tight permissions, nowhere else.

---

## Day to day: one job through the system

Here is the whole lifecycle of a job, start to finish:

1. **You describe the job** to your Claude session in plain language — the goal, the constraints, what "done" looks like.
2. **The boss writes the manifest**: one task per checkable unit, each with its own self-contained spec, its own executable check, and its declared file ownership.
3. **`./ringer.py lint manifest.json`** inspects the manifest before anything runs. It catches the mistakes that make swarms untrustworthy: checks that cannot fail, checks that fail silently, two tasks claiming the same file, underspecified specs. Fix what it flags.
4. **`./ringer.py run manifest.json`** launches the swarm and opens **Ringside** — the live dashboard page — in your browser, so you watch workers, checks, and verdicts in real time instead of staring at a silent terminal.
5. **Workers run in parallel**, each in its own task directory. Ringer executes every check. Failures retry once, with the check's actual failure output injected into the retry prompt.
6. **The boss reads the results**, opens the raw logs of anything that retried or failed, and spot-checks at least one *passing* artifact — because a check can be wrong too, and the only cure for that is a competent pair of eyes.
7. **The boss reports to you**: what shipped, what was verified and how, and what (if anything) needs a human decision.
8. **The scoreboard updates itself.** Every attempt was logged; next time the boss routes work, it routes on fresher evidence.

### Command reference

| Command | What it does |
|---|---|
| `./ringer.py lint <manifest>` | Validates a manifest before a run — catches broken checks, file collisions, vague specs |
| `./ringer.py run <manifest>` | Runs the swarm: dispatches workers in parallel, executes every check, retries failures once, opens the live dashboard |
| `./ringer.py demo` | Three-worker smoke test, verified end to end — the fastest proof your setup works |
| `./ringer.py models` | The scoreboard: per-model, per-task-type pass rates from your local log |
| `./ringer.py hud` | Opens the Ringside dashboard any time, without running anything |

---

## Repository layout

```
fable-ringer/
├── ringer.py              # The orchestrator itself — the tool you run
├── config.sample.toml     # Sample engine configuration
├── engines/               # Worker-engine helpers (sandbox wrapper, mock worker)
├── templates/             # Starter kits: review-swarm, fix-swarm, bakeoff,
│                          #   research-with-proof, data-pipeline, probe, …
├── scripts/               # Log backfill and maintenance utilities
├── tests/                 # The orchestrator's own test suite
├── dashboard/, hud/       # Ringside — the live dashboard (web page + desktop prototype)
├── hooks/                 # Optional reminder hooks installed by install-agent
├── registry/              # Model registry used for scoreboard attribution
├── docs/
│   ├── UPSTREAM-README.md # The original project's README, preserved
│   ├── MODEL-NOTES.md     # The human judgment layer on top of the scoreboard
│   └── …                  # Steering docs, taxonomy, screenshots
├── overlay/               # The operator's configuration layer
│   ├── config/            #   config.toml.example (engine wiring)
│   ├── rules/             #   model-routing.md — this operator's routing table
│   ├── skills/ringer/     #   SKILL.md — the orchestrator playbook
│   └── probes/            #   Lane-validation probe manifests
├── LICENSE.md             # PolyForm Shield 1.0.0 + Required Notice
└── README.md              # You are here
```

Everything outside `overlay/` is the tool (altered from upstream). Everything inside `overlay/` is the configuration and doctrine that make it *this* team's setup.

---

## Credit and license

**Ringer and Ringside are created by Nate Jones (Nate Jones Media LLC).**

- Upstream: <https://github.com/NateBJones-Projects/ringer>
- License: **PolyForm Shield 1.0.0**, with the Required Notice preserved in `LICENSE.md`

This repository redistributes the upstream code with alterations under that same license. The configuration and doctrine layer on top — the routing rules, the wrapper scripts, the probes, the boss-side skill — is this repository's addition. The tool that makes any of it verifiable is Nate's.
