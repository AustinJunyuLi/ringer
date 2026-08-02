# DeepSeek V4 Flash + Qwen 3.8 Max Preview → Ringer: wire the opencode lane, run the audition bakeoff

**Status:** COMPLETED (2026-08-02)
**Date:** 2026-08-02
**Job / run_name:** `opencode-model-audition` (one artifact, all rounds)

## Context

Austin wants DeepSeek V4 Flash GA incorporated into Ringer, with a bakeoff
discovering where it belongs. Mid-planning it emerged the ground truth had
moved: **opencode 1.18.11 is already installed** (`~/.opencode/bin/opencode`,
off the non-interactive PATH) with three providers authed by Austin:

| Slug | Model | Billing |
|---|---|---|
| `deepseek/deepseek-v4-flash` | DeepSeek V4 Flash (snapshot Flash-0731) | API key — $0.14/M in, $0.28/M out, 1M ctx |
| `alibaba-token-plan-cn/qwen3.8-max-preview` | Qwen 3.8 Max Preview | prepaid CN token plan |
| `kimi-for-coding/k3` | Kimi K3 | coding plan (same underlying model as native kimi CLI) |

Ringer's side is NOT wired: no `[engines.opencode]` block. Directives from
Austin: **kimi has an established track record — only compare kimi CLI vs
opencode-kimi** (harness parity); **deepseek and qwen get the proper
bakeoff**. Scope judgment delegated to me: cheap models → test across the
cheap-volume lanes.

## Bakeoff matrix — 3 probes + 15 cells

Round 0 — one trivial probe per NEW lane (skill rule): deepseek-oc, qwen-oc,
kimi-oc. Checks validate a deterministic marker AND grep the worker log for
the expected model slug (identity validation), confirming auth, Seatbelt,
token_regex parsing, and attribution before any batch.

Round 1 — shared scenarios, identical spec wording per row, real task_types
(NOT "bakeoff") so scoreboard rows land in routing buckets:

| Scenario | task_type | Cells |
|---|---|---|
| capability research (produce registry capability files for deepseek-v4-flash AND qwen3.8-max-preview from official docs, quoted citations, domain allowlist) | research | deepseek · qwen · kimi-cli · kimi-oc |
| small bug fix (planted buggy module + failing pytest) | code-fix | deepseek · qwen · claude-sonnet-5 |
| module docs for `engines/mock_worker.py` | docs | deepseek · qwen · kimi-cli · kimi-oc |
| CSV→JSON transform against a schema | data-pipeline | deepseek · qwen · kimi-cli · kimi-oc |

- Kimi pairs ride 3 scenarios — enough for the parity verdict — and double
  as the incumbent reference (research: proven 71% FT / 17 tasks;
  data-pipeline: proven 67%). Sonnet (60% FT) is the code-fix reference.
- Per-task `engine`+`model` fields name every competitor (never engine-block
  hardcoding — 2026-07-06 lesson). Exact IDs only: `claude-sonnet-5` (not
  bare "sonnet"), `kimi-code/k3` (native), full opencode slugs above.
  Registry records the deepseek alias→snapshot resolution (Flash-0731).
- Cost: kimi/sonnet/qwen ride plans; deepseek ≈ $0.50–1. max_parallel 6.
  Timeouts: research 1800s, others 1200s, probes 600s.
- `opencode/deepseek-v4-flash-free` (free gateway route) exists but is NOT
  in the bakeoff — different route than the lane being evaluated. Noted for
  a possible future zero-cost exploration slot.

## Checks (authored by me, reused from template kits where they fit)

- **code-fix:** pytest green + planted test file byte-identical to a pristine
  copy held outside the task dir.
- **docs:** anti-hallucination grep — every flag/function/env the doc names
  must exist in the source (doc-swarm pattern).
- **research:** required capability fields present; every quoted citation
  greps against worker-saved source excerpts; URLs restricted to official
  domains (research-with-proof / competitive-teardown pattern).
- **data-pipeline:** python validator executes against the output JSON
  (data-pipeline pattern).
- All checks print WHY they fail (retry prompts depend on it).

## Files to modify

1. `/opt/homebrew/bin/opencode` — symlink to `~/.opencode/bin/opencode`.
   Smallest fix for the wrapper's `command -v opencode` (binary is off the
   non-interactive PATH; wrapper stays upstream-clean).
2. `~/.config/ringer/config.toml` — enable `[engines.opencode]` from
   upstream's sample: `bin = "/Users/austinli/fleet/swarm/engines/opencode-sandboxed.sh"`
   (Seatbelt: writes confined to task dir), sample args_template/token_regex
   verbatim, `model_default = "deepseek/deepseek-v4-flash"`. Also update the
   stale comments: opencode IS now wired (not "needs an OpenRouter key");
   the "No qwen lane" note gets clarified — it bans a native qwen CLI
   *engine*, while qwen *models* ride the opencode lane (Austin wired them).
3. `~/fleet/swarm/registry/model-identity.toml` — add `[engines.opencode]`
   (harness "OpenCode CLI") + three model entries: DeepSeek V4 Flash
   (DeepSeek, API key, source api-docs.deepseek.com, snapshot note), Qwen
   3.8 Max Preview (Alibaba, token plan), Kimi K3 via opencode (Moonshot,
   coding plan, noncanonical_slugs cross-link to native `kimi-code/k3` so
   the harness split doesn't invent a second model).
4. `~/fleet/swarm/docs/MODEL-NOTES.md` — post-run dated lines: deepseek +
   qwen sections, kimi harness-parity verdict.

No auth writes anywhere — Austin already wired all three providers. The API
key pasted in chat is already in opencode's auth store; nothing else touches
it. New working files (manifests, fixtures, checks) under
`~/.ringer/work/opencode-model-audition/`; plan copy + session log →
`~/fleet/swarm/quality_reports/{plans,session_logs}/`.

## Execution order

0. Ringside up first (`./ringer.py hud`); copy plan to quality_reports/plans/;
   start session log.
1. Symlink; `opencode models` sanity via symlink; quick qwen3.8-max-preview
   doc check (context/pricing for the registry entry); confirm the kimi-oc
   effort default matches the native lane's default (`--variant` mapping
   recorded in config comments).
2. Config + registry edits; `./ringer.py lint` the probe manifest.
3. Round 0: 3 probes. Fix wiring until green.
4. Author fixtures + checks; lint the bakeoff manifest.
5. Round 1: 15 cells, same run_name.
6. Post-run ritual: run JSON → raw logs for every retry/fail → spot-check one
   PASSING artifact → `./ringer.py models --task-type <each>` → MODEL-NOTES →
   results reviewed on the artifact page (never terminal cat). Deliverables:
   (a) lane recommendation per task_type for deepseek + qwen (promotion
   ladder computes tiers); (b) kimi parity verdict — if kimi-oc matches
   kimi-cli, propose retiring the native kimi engine block as a separate
   approval; nothing deleted in this job.
7. Session log close; capability files from the research cells land in
   `registry/model-capabilities/` if they survive review.

## Risks / notes

- Flash-class models historically choke on long multi-turn harness work —
  research cells are the canary; watch retry counts.
- Qwen 3.8 Max is a *preview* snapshot: scoreboard rows will be tagged by
  the full slug, and the registry entry marks preview status — placement is
  provisional until GA.
- DeepSeek peak-hour 2x pricing (Beijing 9–12/14–18) is pending
  implementation; current London afternoon = Beijing off-peak anyway.
- models.dev already lists all needed slugs (verified above) — no custom
  opencode.json entries required.
