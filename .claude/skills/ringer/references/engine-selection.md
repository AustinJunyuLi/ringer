## Engine selection

**The engine choice belongs to the human — but the recommendation comes
from THEIR evidence.** Before the FIRST run of a job: read what's wired up
(`[engines.<name>]` blocks in `~/.config/ringer/config.toml`), run
`./ringer.py models --task-type <this job's type>` for the local scoreboard,
and glance at `./ringer.py catalog --changes` for anything newly free or
newly cheap. Then ask the user which model should do the typing — top 2–3
options with the NUMBERS in the pitch and a recommendation, e.g.: *"GLM is
6/6 first-try on persona work here at ~2¢/task — recommended. Codex is also
100% but ~8x the tokens. And kimi went free on OpenRouter yesterday — want
it auditioning one of the small tasks?"* Honor their pick via the per-task
`engine`/`model` fields; don't re-ask every round of the same job unless
the mix isn't working. This is per-user by design: the scoreboard learns
THIS user's workload — never import another machine's conclusions or
recommend from a different user's numbers.

**Explore or the scoreboard fossilizes.** Always recommending the proven
pick means never learning a new one. In any run of 3+ tasks that has a
low-stakes lane (docs sweeps, mechanical edits, persona reviews — strong
executed check, retry to absorb failure), assign roughly ONE task to an
exploration candidate from `./ringer.py models --explore --task-type <type>`
(untested + cheap or free, text-capable, decent context). Free promos from
`catalog --changes` jump the queue — a temporarily-free model is a zero-cost
experiment. Never explore on time-critical work, never with more than a
small slice of a batch, and name the experiment when presenting the engine
ask so the human can veto it. Promotion ladder (computed by --explore):
untested → probation (some evidence) → proven for a task_type (3+ tasks,
first-try ≥ 0.67). Proven models earn bigger lanes in that type and an
audition one rung up in adjacent types; repeated first-attempt failures end
the audition — record the demotion in MODEL-NOTES so the next orchestrator
doesn't re-run the experiment.

**OpenCode is the harness; the model is a manifest field.** Unless a model
ships its own first-class harness (Codex does), it runs through the
`opencode` engine with the task's `"model"` field set to the OpenRouter
slug — e.g. `"engine": "opencode", "model": "openrouter/moonshotai/kimi-k2.7-code"`.
This holds even when someone — including the user, in the heat of a run —
says to "call kimi directly" or reach for the model's own CLI: the harness
is what provides the sandbox, raw logs, token counts, and executed
verification, so routing around it silently drops all four. Never clone an
engine block or splice `-m` through `engine_args` to change models; that's
what the `model` field is for, and a bakeoff is only real when the MANIFEST
names each competitor (2026-07-06 lesson: an engine block with a hard-coded
model ran one model under three competitors' names).

Engines are config blocks (`[engines.<name>]` in config.toml), selectable
per task via the manifest `engine` field. Defaults are deliberate:

- **codex** (default): strongest general worker. Use per-task `engine_args`
  to set reasoning effort — spend it on hard tasks, not boilerplate.
- **opencode**: the universal lane — any OpenRouter model via the `model`
  field (engine `model_default` is GLM-5.2, the cheap-intelligence pick).
  Validate a model new to you with a trivial one-task manifest before
  trusting it with a batch.
- Small/flash-class models are the first to choke on long conversational or
  multi-turn harness tasks — watch their retry counts before scaling them.
- Match `timeout_s` to the task: conversational harness tasks and
  build-and-test checks need far more than file edits.
- **Check the evidence before assigning models to tasks.** Run
  `./ringer.py models` (optionally `--task-type <type>`) — the local
  scoreboard aggregating every executed-check outcome per (model,
  task_type): first_try_pass_rate is the routing signal; pass_rate includes
  retry rescues. Then read `docs/MODEL-NOTES.md` (in the ringer repo) for
  the judgment the numbers can't carry. Routing is grounded in performance,
  not vibes (Jon directive 2026-07-06).
- **"Show me the scoreboard" is one command.** When the human asks to see
  the model scoreboard, rankings, model costs, or "which models work best,"
  run `./ringer.py models --open` — it renders the full scoreboard (tiers,
  first-try rates, est. $/task, usage, MODEL-NOTES excerpts, free-promo
  watchlist) as a zero-LLM HTML page in the artifact library and opens it
  in their browser. Costs no tokens; never hand-summarize the numbers when
  the page can show them.
- **Give every task a `task_type`** (canonical vocabulary in the README —
  code-feature, code-fix, code-review, research, persona-review, site-build,
  image-gen, docs, probe, bakeoff, ...). Untyped tasks bucket as (untyped)
  and teach the scoreboard nothing; lint nudges you when it's missing.
