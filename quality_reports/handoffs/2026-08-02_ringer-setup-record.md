# Ringer setup record — Austin's Mac, 2026-08-02

**Audience:** the Claude Code instance on Austin's other computer, tasked with
replicating these lanes. This is a RECORD of the working setup, not an install
script — read it whole, then wire the equivalent on your machine and validate
with your own probes.

**Non-negotiables before you start:**

1. **Evidence is per-machine.** Do NOT copy this machine's scoreboard numbers
   or tier conclusions into your `~/.ringer/runs.jsonl`. The routing DOCTRINE
   below transfers; the EVIDENCE does not. Validate every lane with a
   one-task probe manifest (templates/probe in the repo) before batch use.
2. **No secrets in this document.** Austin supplies the API keys / plan
   logins at auth time (see §5). If an auth step needs a key, ask Austin.
3. Paths below are this Mac's. Translate; don't transplant blindly. The
   Seatbelt sandbox wrapper is macOS-ONLY (§4) — on Linux you must solve
   sandboxing differently.

---

## 1. What this install is

- Ringer lives at `~/fleet/swarm`. **UPDATED (later on 2026-08-02): clone
  the FORK** — `https://github.com/AustinJunyuLi/ringer`, branch `main` —
  which now mirrors this machine exactly (through commit `4e62d95`). Keep
  upstream `https://github.com/NateBJones-Projects/ringer` as remote
  `origin` for deliberate rebases; the pre-reset archive is preserved as
  tag `archive/pre-reset-2026-07-28` on the fork.
- Local commits on top of upstream `a1a91b8`, ALL pushed to the fork:
  `f21b8f0` (effort attribution + registry engine blocks), `75412e5`
  (opencode model rows, kimi retirement, deepseek/qwen capability TOMLs),
  `7a7b4bd` (quality_reports records incl. this document), `4e62d95`
  (round-2: doc_check `--symbol-mode relaxed`, terra/luna capability
  TOMLs, MODEL-NOTES doctrine).
- **Appendices A–D below are now redundant with fork history** — retained
  only as an offline audit copy in case the fork is unreachable.
- `[update] auto = false` on purpose: local commits mean ff-only updates
  can never apply. Pull upstream deliberately: `git fetch origin && git
  rebase origin/main`.

## 2. The engine lanes (current, post-2026-08-02)

Four engines wired; one deliberately retired:

| Engine | What | Access | Notes |
|---|---|---|---|
| codex | Codex CLI, GPT-5.6 family | OAuth plan | default engine; effort via `engine_args ["-c","model_reasoning_effort=…"]` |
| claude | Claude Code CLI (sonnet/opus/fable) | OAuth plan | fable = user-invoked only (standing rule); effort via `["--effort",…]` |
| opencode | **THE universal API-model lane** — deepseek / qwen / kimi | per-provider (§5) | model rides the manifest `model` field |
| mock | local fixture worker | none | harness smokes without spending calls |
| ~~kimi~~ | native Kimi Code CLI | — | **HARD RETIRED 2026-08-02. Do not wire.** Parity audition showed opencode-kimi ≥ CLI, and opencode adds sandbox + token counts. Kimi runs ONLY as `kimi-for-coding/k3` via opencode. |

The complete `~/.config/ringer/config.toml` as of today (machine-specific
paths and all — translate paths for your machine):

### 2a. config.toml verbatim

```toml
# Ringer config — hand-maintained, 2026-07-28 factory reset.
#
# The overlay/deploy.py generator that used to write this file was removed
# when the install reverted to upstream. Edit this file directly.
#
# Engine bins are absolute because three of the four live outside a standard
# PATH prefix. Upstream's sample uses shutil.which("codex"); absolute paths
# are the documented option for machine-specific installs.
#
# No NATIVE qwen CLI engine exists on this fleet — do not add one. Qwen
# MODELS ride the opencode lane via the alibaba-token-plan-cn provider
# (wired 2026-08-02).

state_dir = "~/.ringer"
dashboard_port_base = 8787
allow_full_access = false

[update]
# origin = upstream (NateBJones-Projects/ringer); fork = AustinJunyuLi/ringer,
# which since 2026-08-02 MIRRORS local main (all local commits pushed after
# each session) and also carries the pre-reset archive tag. auto stays off
# because main carries local commits on top of upstream, so an ff-only move
# can never apply. Pull upstream deliberately instead:
#   git fetch origin && git rebase origin/main   (then push fork main)
auto = false

# Model steering. profiles/ starts empty by design: rules arrive from observed
# runs and change status only through the validation gate, never by hand-edit.
[steering]
dir = "~/.ringer/steering"
inject_candidates = true

[eval]
backend = "jsonl"
jsonl_path = "~/.ringer/runs.jsonl"

[artifact]
enabled = true
out = "~/.ringer/artifacts/{run_id}.html"
report_out = "~/.ringer/artifacts/{run_id}-report.html"
index_out = "~/.ringer/artifacts/index.html"

# codex — GPT-5.6 Sol/Terra/Luna. Per-task model; effort via engine_args
# ["-c","model_reasoning_effort=high|xhigh|max"].
[engines.codex]
bin = '/opt/homebrew/bin/codex'
args_template = ["exec", "--skip-git-repo-check", "{access_args}", "{model_args}", "{engine_args}", "-C", "{taskdir}", "{spec}"]
sandbox_args = ["--sandbox", "workspace-write"]
full_access_args = ["--dangerously-bypass-approvals-and-sandbox"]
token_regex = "tokens\\s+used\\s*:?\\s*([0-9][0-9,]*)"
model_report_regex = "(?m)^model:[ \\t]*([^ \\t\\r\\n]+)[ \\t]*\\r?$"

# claude — sonnet/opus/fable. Uses {model} + explicit --model ({model_args}
# would emit "-m", which is not a --model short flag). Effort via engine_args
# ["--effort","low|high|max"]. Headless -p needs skip-permissions to write.
# model_default = opus per the 2026-08-02 standing doctrine: Sonnet is
# research-only + break-glass (name it explicitly in manifests); an untyped
# claude task should not silently land on Sonnet.
[engines.claude]
bin = '/Users/austinli/.local/bin/claude'
model_default = "opus"
args_template = ["{access_args}", "--model", "{model}", "{engine_args}", "-p", "{spec}"]
sandbox_args = ["--dangerously-skip-permissions"]
full_access_args = []

# kimi native CLI lane — HARD RETIRED 2026-08-02 (Austin's call) after the
# opencode-model-audition parity verdict: opencode-kimi matched or beat the
# CLI on every shared scenario, and adds Seatbelt + token counts the CLI
# lacked. Kimi now rides the opencode lane as "kimi-for-coding/k3". Do not
# re-add a native kimi engine block; historical scoreboard rows keep their
# attribution via the retained [engines.kimi] registry entries.

# mock — free local worker, no credentials, no network. Smokes the harness
# itself without spending a plan call. model_default is the reserved fixture
# name "mock-model" so smoke runs are excluded from the scoreboard instead of
# logging as an unregistered model.
[engines.mock]
bin = '/opt/homebrew/opt/python@3.12/bin/python3.12'
model_default = "mock-model"
args_template = ['/Users/austinli/fleet/swarm/engines/mock_worker.py', "{spec}"]
sandbox_args = []
full_access_args = []

# opencode — the universal API-model lane (wired 2026-08-02). Sandbox is
# engines/opencode-sandboxed.sh (macOS Seatbelt: network + reads open, writes
# confined to task dir + scratch + opencode state dirs). Binary lives at
# ~/.opencode/bin/opencode, symlinked to /opt/homebrew/bin/opencode so the
# wrapper's `command -v` resolves in non-interactive shells. Providers authed
# in opencode's auth store: deepseek (API key), kimi-for-coding (coding
# plan), alibaba-token-plan-cn (prepaid token plan). The model rides the
# manifest field — the standing mix (2026-08-02): "deepseek/deepseek-v4-flash"
# (DEFAULT where similarly qualified — Austin's cost directive),
# "alibaba-token-plan-cn/qwen3.8-max-preview" (preview slug; strong but
# temporary), "kimi-for-coding/k3" (the ONLY kimi route since the native CLI
# lane retired). Reasoning effort per task via engine_args
# ["--variant", "low|high|max"] (provider-specific; replaces the old
# k3-low/high/max model aliases). NOTE vs upstream sample: opencode 1.18.11
# replaced --dangerously-skip-permissions with --auto.
[engines.opencode]
bin = "/Users/austinli/fleet/swarm/engines/opencode-sandboxed.sh"
model_default = "deepseek/deepseek-v4-flash"
args_template = [
  "{taskdir}",
  "{access_args}",
  "run",
  "-m",
  "{model}",
  "--auto",
  "--format",
  "json",
  "{engine_args}",
  "--dir",
  "{taskdir}",
  "{spec}",
]
sandbox_args = []
full_access_args = ["--no-sandbox"]
token_regex = '"tokens":\{"total":([0-9]+)'

# Not wired: grok (needs SuperGrok/X Premium Plus). Reference block in
# upstream's config.sample.toml.
```

## 3. The model mix and routing doctrine

Standing mix on the opencode lane (Austin's directives, 2026-08-02):

- **`deepseek/deepseek-v4-flash` — the DEFAULT worker model wherever the
  local scoreboard shows it similarly qualified.** Austin, verbatim:
  "deepseek is extremely cheap. we want everything to default to deepseek if
  the lanes are similarly qualified." $0.14/M in (miss), $0.0028/M cache
  hit, $0.28/M out; 1M context; 384K max output; thinking mode default
  (effort high); thinking mode ignores temperature/top_p. Alias floats over
  snapshots (currently DeepSeek-V4-Flash-0731). Peak-hour 2x pricing
  (Beijing 9–12/14–18) announced, not yet in force.
- **`alibaba-token-plan-cn/qwen3.8-max-preview`** — strongest single-round
  showing in the audition (4/4 first-try incl. research), but a PREVIEW
  slug: Alibaba will retire or replace it after preview. Thinking-only.
  Token-Plan (credits) billed, Beijing region. Re-audit at GA.
- **`kimi-for-coding/k3`** — the only kimi route. Same trained artifact as
  the old CLI's k3; effort via `--variant low|high|max` in `engine_args`
  (replaces the old k3-low/high/max model aliases).

On this machine's evidence (2026-08-02 audition, 15 cells + 3 probes):
deepseek took code-fix and data-pipeline first-try (fastest in row), needed
one retry on research and docs; qwen went 4/4 first-try; kimi-oc matched or
beat kimi-CLI everywhere. Treat that as PRIOR, not as your machine's truth —
run your own audition or probes.

### 3a. Heavyweight + succession doctrine (added after round 2, 2026-08-02)

A second bakeoff (run `round2-heavyweight-succession`, 22 cells; full
evidence in `docs/MODEL-NOTES.md` "Round 2" + "STANDING ROUTING DOCTRINE"
sections in the repo) settled the plan-billed lanes. Austin-approved
assignments, replicate as doctrine:

| Route to | task_types |
|---|---|
| GPT-5.6 Sol (codex engine, `-c model_reasoning_effort=high` for heavy work) | code-review / adversarial verification; constrained rewrites & docs-at-scale; site-build |
| Claude Opus (claude engine, `--effort high`) | code-feature; hard code-fix; diagnosis post-mortems |
| GPT-5.6 Luna (codex engine) | docs + short-context light fixes ONLY — long-context retrieval craters (MRCR ~41%) despite the nominal 1M window; 10x cheaper plan credits than Terra |
| Claude Sonnet | research ONLY + break-glass (minimized by directive; hard unplug pending a confirming round) |
| benched | GPT-5.6 Terra |

Operating rules: new heavyweight type → Opus if implementation/latency-
shaped, Sol if verification/citation-shaped, else the plan the last batch
didn't use; assignments sticky until the demotion trigger; never route
research to Sol. Rationale: the ledgers balance because the Claude plan
also carries Sonnet-research and the GPT plan carries Luna-volume.

KNOWN GAP (fix pending, found by BOTH round-2 review cells): ringer's
effort attribution does not parse opencode's `--variant`, so effort on
`kimi-for-coding/k3` rows is currently unrecorded — read those scoreboard
rows accordingly until the fix lands in the fork.

## 4. OpenCode lane — the wiring facts that bit us

- **Version:** opencode 1.18.11 (brew has it; this Mac used the curl
  installer → binary at `~/.opencode/bin/opencode`, which is OFF the
  non-interactive PATH. Fix here: symlink into `/opt/homebrew/bin`. Check
  `command -v opencode` from a NON-login shell before trusting the lane.)
- **Flag change vs upstream sample:** opencode ≥1.18 removed
  `--dangerously-skip-permissions`; use `--auto`. Upstream's
  `config.sample.toml` opencode block is stale on this — the config in §2a
  already has the fix.
- **Sandbox:** `bin` points at the repo's `engines/opencode-sandboxed.sh`
  (macOS Seatbelt: network+reads open, writes confined to taskdir + scratch
  + opencode state dirs). **macOS-only** (`/usr/bin/sandbox-exec`). On
  Linux, the wrapper only works in `--no-sandbox` mode = unconfined writes;
  decide deliberately (bubblewrap/firejail equivalent, or accept full
  access with `allow_full_access` gating).
- **Token counts** parse from the `--format json` event stream via
  `token_regex = '"tokens":\{"total":([0-9]+)'` — verify your first probe
  shows a tokens column; if empty, the JSON shape changed.
- **Model identity in checks:** the worker.log (json events) contains the
  serving model slug; our probe/bakeoff checks grep it as an identity
  assertion. Recommended on any new lane.

## 5. Auth (names only — Austin supplies the actual credentials)

`~/.local/share/opencode/auth.json` on this Mac has four entries:

| Provider key | Type | What it is |
|---|---|---|
| `deepseek` | api | DeepSeek platform API key (Austin holds it) |
| `kimi-for-coding` | api | Moonshot coding-plan credential |
| `alibaba-token-plan-cn` | api | Alibaba Model Studio Token Plan key (Beijing region) |
| `openai` | oauth | OpenAI OAuth (not used by ringer lanes) |

Replication: run `opencode auth login` per provider (or have Austin
securely copy his auth.json himself — this document deliberately excludes
the values). Then `opencode models | grep -E 'deepseek|qwen|kimi'` must list:
`deepseek/deepseek-v4-flash`, `deepseek/deepseek-v4-pro`,
`alibaba-token-plan-cn/qwen3.8-max-preview`, `kimi-for-coding/k3`,
`kimi-for-coding/k3-256k`. (A free gateway route
`opencode/deepseek-v4-flash-free` also exists — unused here; candidate for
zero-cost exploration slots.)

## 6. Registry and capability state

- `registry/model-identity.toml`: Appendix B's diff adds the three opencode
  model rows (DeepSeek V4 Flash, Qwen 3.8 Max Preview, Kimi K3 (OpenCode)),
  retires-but-retains the `[engines.kimi]` block (historical attribution),
  and fixes the `kimi-code/k3-low` unregistered slug. Two identity
  decisions worth preserving: (1) "Kimi K3 (OpenCode)" is deliberately NOT
  noncanonical-merged into the old CLI row — a merge would stamp new
  evidence with the dead harness; (2) `claude:sonnet` is the canonical
  claude route (lint rejects `claude-sonnet-5`; the noncanonical map
  covers it).
- `registry/model-capabilities/`: four grounded capability files ship in
  the fork (deepseek-v4-flash, qwen3.8-max-preview, gpt-5.6-terra,
  gpt-5.6-luna — every claim quote-verified against saved primary sources
  during the two audition rounds). Appendices C and D are audit copies of
  the first two.

## 7. How this machine validated the lanes (repeat the pattern, not the data)

1. `./ringer.py lint` on everything before running.
2. One trivial probe per new lane (templates/probe, mode `generic`):
   deterministic marker + `grep` of the model slug in worker.log. All three
   lanes passed first-try here (~10-13K tokens each).
3. Then a 15-cell bakeoff across research / code-fix / docs / data-pipeline
   with executed checks (details + check-design lessons in
   `docs/MODEL-NOTES.md` sections dated 2026-08-02 — read them, especially
   the doc_check literal-symbol trap before writing docs manifests).
4. `./ringer.py demo` after any config surgery.

---

## Appendix A — local commit `f21b8f0` (HISTORICAL AUDIT COPY — already in fork main; do not apply when cloning the fork)

```patch
From f21b8f00437a6da3360a2b86d39dea2ee84163fa Mon Sep 17 00:00:00 2001
From: Junyu Li <106483677+AustinJunyuLi@users.noreply.github.com>
Date: Tue, 28 Jul 2026 15:59:32 +0800
Subject: [PATCH] Record reasoning effort on all three lanes; register local
 engines
MIME-Version: 1.0
Content-Type: text/plain; charset=UTF-8
Content-Transfer-Encoding: 8bit

Two local changes on top of upstream, both needed because this install
dispatches through three vendor CLIs rather than a shared harness.

- effective_reasoning_effort_from_command now attributes --effort (claude)
  and the k3-low/high/max aliases (kimi) alongside codex's -c flag. A bare
  k3 with no effort named still returns None rather than guessing, so
  unknown effort stays unknown instead of being invented. 19 acceptance
  tests cover the parse.
- registry: claude and kimi identity blocks. Canonical keys are the short
  CLI nicknames; long forms (claude-opus-5, claude-sonnet-5, bare k3,
  kimi-code/k3max) are recorded as noncanonical so one model stops
  splitting across two scoreboard rows.

Verified end to end: a claude task dispatched at --effort low lands as
"Claude Sonnet · low" with reasoning_effort: 'low' in the eval log.

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>
---
 registry/model-identity.toml                |  76 +++++++++++++++
 ringer.py                                   |  15 +++
 tests/test_effort_attribution_acceptance.py | 102 ++++++++++++++++++++
 3 files changed, 193 insertions(+)
 create mode 100644 tests/test_effort_attribution_acceptance.py

diff --git a/registry/model-identity.toml b/registry/model-identity.toml
index 2807de9..b785738 100644
--- a/registry/model-identity.toml
+++ b/registry/model-identity.toml
@@ -98,3 +98,79 @@ lab = "Meta"
 confidence = "verified"
 source = "manifest model field; OpenRouter slug meta-llama/llama-3.3-70b-instruct:free"
 last_verified = 2026-07-10
+
+# ---------------------------------------------------------------------------
+# Local lanes (2026-07-28). Upstream ships codex/grok/opencode; this install
+# also runs the Claude Code and Kimi Code CLIs, so their identities are
+# declared here. Canonical keys are the short CLI nicknames; the long forms
+# are recorded as noncanonical so the scoreboard stops splitting one model
+# across two rows and lint catches the duplicate spelling at authoring time.
+# ---------------------------------------------------------------------------
+
+[engines.claude]
+harness = "Claude Code CLI"
+access = "OAuth plan"
+default_model_key = "sonnet"
+
+[engines.claude.models."sonnet"]
+display = "Claude Sonnet"
+lab = "Anthropic"
+confidence = "unverified"     # the alias floats over snapshots; a release lands in this row invisibly
+source = "claude --help v2.1.216 (local)"
+last_verified = 2026-07-28
+noncanonical_slugs = ["claude:claude-sonnet-5"]
+
+[engines.claude.models."opus"]
+display = "Claude Opus"
+lab = "Anthropic"
+confidence = "unverified"     # alias floats; verified headless 2026-07-21
+source = "claude --help v2.1.216 (local)"
+last_verified = 2026-07-28
+noncanonical_slugs = ["claude:claude-opus-5"]
+
+[engines.claude.models."fable"]
+display = "Claude Fable 5"
+lab = "Anthropic"
+confidence = "unverified"     # red-phone lane, user-invoked only
+source = "claude --help v2.1.216 (local)"
+last_verified = 2026-07-28
+noncanonical_slugs = ["claude:claude-fable-5"]
+
+[engines.kimi]
+harness = "Kimi Code CLI"
+access = "OAuth plan"
+default_model_key = "kimi-code/k3"
+
+# The three k3-* aliases are one trained artifact at three reasoning efforts
+# (see ~/.kimi-code/config.toml: each sets default_effort). They stay separate
+# rows on purpose — upstream's effort attribution reads Codex's -c flag only,
+# so for this lane the model field is the only place effort is observable.
+[engines.kimi.models."kimi-code/k3"]
+display = "Kimi K3"
+lab = "Moonshot AI"
+confidence = "verified"
+source = "https://www.kimi.com/code"
+last_verified = 2026-07-28
+noncanonical_slugs = ["kimi:k3"]
+
+[engines.kimi.models."k3-low"]
+display = "Kimi K3 (low)"
+lab = "Moonshot AI"
+confidence = "verified"
+source = "https://www.kimi.com/code"
+last_verified = 2026-07-28
+
+[engines.kimi.models."k3-high"]
+display = "Kimi K3 (high)"
+lab = "Moonshot AI"
+confidence = "verified"
+source = "https://www.kimi.com/code"
+last_verified = 2026-07-28
+
+[engines.kimi.models."k3-max"]
+display = "Kimi K3 (max)"
+lab = "Moonshot AI"
+confidence = "verified"
+source = "https://www.kimi.com/code"
+last_verified = 2026-07-28
+noncanonical_slugs = ["kimi:kimi-code/k3max"]
diff --git a/ringer.py b/ringer.py
index 062615b..a832d01 100755
--- a/ringer.py
+++ b/ringer.py
@@ -9483,6 +9483,21 @@ def effective_reasoning_effort_from_command(command: list[str]) -> str | None:
         if match:
             effort = match.group(1).strip()
             return effort or None
+
+    for index, item in enumerate(command):
+        if item == "--effort":
+            if index + 1 >= len(command) or command[index + 1].startswith("-"):
+                return None
+            effort = command[index + 1].strip()
+            return effort or None
+        if item.startswith("--effort="):
+            effort = item.removeprefix("--effort=").strip()
+            return effort or None
+
+    model = effective_model_from_command(command)
+    match = re.fullmatch(r"(?:kimi-code/)?(?:k3-(low|high|max)|k3max)", model)
+    if match:
+        return match.group(1) or "max"
     return None
 
 
diff --git a/tests/test_effort_attribution_acceptance.py b/tests/test_effort_attribution_acceptance.py
new file mode 100644
index 0000000..e1cc773
--- /dev/null
+++ b/tests/test_effort_attribution_acceptance.py
@@ -0,0 +1,102 @@
+#!/usr/bin/env python3
+"""Acceptance check for effort attribution across all three live lanes.
+
+Authored by the orchestrator, not the worker. A worker must make this pass
+WITHOUT editing this file.
+
+Context: routing treats a cell as (model x effort). Until this passes, the
+eval log records the effort half for codex only -- claude and kimi rows log
+null, so the scoreboard cannot distinguish k3-low from k3-max.
+"""
+from __future__ import annotations
+
+import sys
+import unittest
+from pathlib import Path
+
+ROOT = Path(__file__).resolve().parents[1]
+sys.path.insert(0, str(ROOT))
+
+from ringer import effective_reasoning_effort_from_command as eff  # noqa: E402
+
+
+class CodexFormRegression(unittest.TestCase):
+    """The pre-existing behaviour must not change."""
+
+    def test_config_flag_pair(self) -> None:
+        self.assertEqual(eff(["-c", "model_reasoning_effort=xhigh"]), "xhigh")
+
+    def test_quoted_value(self) -> None:
+        self.assertEqual(eff(["-c", 'model_reasoning_effort="max"']), "max")
+
+    def test_embedded_in_larger_item(self) -> None:
+        self.assertEqual(eff(["-c", "foo=1,model_reasoning_effort=low"]), "low")
+
+
+class ClaudeArgvForm(unittest.TestCase):
+    """`--effort <value>` arrives as two adjacent argv items."""
+
+    def test_separate_items(self) -> None:
+        self.assertEqual(eff(["--model", "opus", "--effort", "high", "-p", "spec"]), "high")
+
+    def test_equals_form(self) -> None:
+        self.assertEqual(eff(["--effort=max", "-p", "spec"]), "max")
+
+    def test_low(self) -> None:
+        self.assertEqual(eff(["--effort", "low"]), "low")
+
+    def test_dangling_flag_is_not_a_crash(self) -> None:
+        self.assertIsNone(eff(["--effort"]))
+
+
+class KimiAliasForm(unittest.TestCase):
+    """The kimi CLI carries effort in the model alias, not a flag."""
+
+    def test_alias_max(self) -> None:
+        self.assertEqual(eff(["-m", "k3-max", "-p", "spec"]), "max")
+
+    def test_alias_low(self) -> None:
+        self.assertEqual(eff(["-m", "k3-low", "-p", "spec"]), "low")
+
+    def test_alias_high(self) -> None:
+        self.assertEqual(eff(["-m", "k3-high", "-p", "spec"]), "high")
+
+    def test_namespaced_alias(self) -> None:
+        self.assertEqual(eff(["-m", "kimi-code/k3-max"]), "max")
+
+    def test_legacy_k3max_alias(self) -> None:
+        self.assertEqual(eff(["-m", "kimi-code/k3max"]), "max")
+
+
+class MustNotGuess(unittest.TestCase):
+    """Silence is correct when effort was never stated explicitly."""
+
+    def test_bare_k3_is_config_dependent(self) -> None:
+        # Bare k3 takes whatever default_effort the config gives it. Guessing
+        # here would write a fabricated value into the eval log.
+        self.assertIsNone(eff(["-m", "kimi-code/k3"]))
+
+    def test_bare_k3_unnamespaced(self) -> None:
+        self.assertIsNone(eff(["-m", "k3"]))
+
+    def test_empty_command(self) -> None:
+        self.assertIsNone(eff([]))
+
+    def test_unrelated_argv(self) -> None:
+        self.assertIsNone(eff(["exec", "-C", "/tmp/x", "write a file"]))
+
+    def test_sonnet_without_effort(self) -> None:
+        self.assertIsNone(eff(["--model", "sonnet", "-p", "spec"]))
+
+    def test_max_context_is_not_an_effort(self) -> None:
+        # "max" appears inside an unrelated token; must not be harvested.
+        self.assertIsNone(eff(["-c", "max_context_size=1048576"]))
+
+
+class ExplicitFlagBeatsAlias(unittest.TestCase):
+    def test_flag_wins(self) -> None:
+        self.assertEqual(eff(["-m", "k3-low", "--effort", "max"]), "max")
+
+
+if __name__ == "__main__":
+    unittest.main(verbosity=2)
-- 
2.50.1 (Apple Git-155)
```

## Appendix B — the 2026-08-02 registry diff (HISTORICAL AUDIT COPY — committed as `75412e5`, already in fork main)

```diff
diff --git a/registry/model-identity.toml b/registry/model-identity.toml
index b785738..10dd3a8 100644
--- a/registry/model-identity.toml
+++ b/registry/model-identity.toml
@@ -66,11 +66,36 @@ last_verified = 2026-07-10
 
 [engines.opencode]
 harness = "OpenCode"
-access = "OpenRouter API"
+access = "Provider auth (API key / plans)"   # was "OpenRouter API"; no OpenRouter key on this fleet since 2026-07. deepseek = API key, kimi-for-coding = coding plan, alibaba-token-plan-cn = prepaid token plan.
 # model key = the manifest "model" slug; entries below map slugs to display
 # names. Unlisted slugs are marked unregistered and derive a display name;
 # their complete raw value appears only in scoreboard diagnostics until verified.
 
+[engines.opencode.models."deepseek/deepseek-v4-flash"]
+display = "DeepSeek V4 Flash"
+lab = "DeepSeek"
+confidence = "verified"     # alias resolves to snapshot DeepSeek-V4-Flash-0731 as of 2026-08-02 (GA); 1M ctx / 384K out; thinking default
+source = "https://api-docs.deepseek.com/quick_start/pricing"
+last_verified = 2026-08-02
+
+[engines.opencode.models."alibaba-token-plan-cn/qwen3.8-max-preview"]
+display = "Qwen 3.8 Max Preview"
+lab = "Alibaba"
+confidence = "verified"     # PREVIEW snapshot (released 2026-07-19); placement provisional until GA; 1M ctx / 131K out
+source = "models.dev provider alibaba-token-plan-cn; verified via `opencode models` 2026-08-02"
+last_verified = 2026-08-02
+
+[engines.opencode.models."kimi-for-coding/k3"]
+# THE living kimi lane since 2026-08-02 (native CLI engine retired after the
+# parity audition). Kept as its own row — NOT merged into kimi:kimi-code/k3
+# — because a noncanonical merge would stamp new OpenCode evidence with the
+# retired CLI harness. Old rows stay under "Kimi K3", new ones accrue here.
+display = "Kimi K3 (OpenCode)"
+lab = "Moonshot AI"
+confidence = "verified"     # same trained artifact as kimi-code/k3, served via the kimi-for-coding plan endpoint
+source = "verified via `opencode models` 2026-08-02; coding-plan provider"
+last_verified = 2026-08-02
+
 [engines.opencode.models."openrouter/z-ai/glm-5.2"]
 display = "GLM 5.2"
 lab = "Z.ai (Zhipu AI)"
@@ -136,6 +161,11 @@ source = "claude --help v2.1.216 (local)"
 last_verified = 2026-07-28
 noncanonical_slugs = ["claude:claude-fable-5"]
 
+# ENGINE RETIRED 2026-08-02 — the native kimi CLI lane was removed from
+# ringer config after the opencode-model-audition parity verdict (kimi now
+# rides opencode as kimi-for-coding/k3). These entries are RETAINED so the
+# 20+ historical Kimi Code CLI scoreboard rows keep their attribution. Do
+# not delete them and do not re-wire the engine.
 [engines.kimi]
 harness = "Kimi Code CLI"
 access = "OAuth plan"
@@ -159,6 +189,7 @@ lab = "Moonshot AI"
 confidence = "verified"
 source = "https://www.kimi.com/code"
 last_verified = 2026-07-28
+noncanonical_slugs = ["kimi:kimi-code/k3-low"]   # fixes the unregistered kimi-code/k3-low row from 2026-07-30
 
 [engines.kimi.models."k3-high"]
 display = "Kimi K3 (high)"
```

## Appendix C — `registry/model-capabilities/deepseek-v4-flash.toml`

```toml
# Produced from the opencode-model-audition run (2026-08-02): grounded
# capability research by the research--deepseek cell (29 verified quotes),
# cross-validated against the research--qwen cell's independent report and
# the orchestrator's own doc fetches. Saved page excerpts live in the run
# workdir under research--deepseek/sources/.

[model]
key = "deepseek/deepseek-v4-flash"
display = "DeepSeek V4 Flash"
vendor = "DeepSeek"
release_date = "2026-04-24"
snapshot = "DeepSeek-V4-Flash-0731"
snapshot_note = "The API id is a floating alias: 'deepseek-v4-flash' always serves the newest snapshot (currently DeepSeek-V4-Flash-0731). There is no documented way to pin an old snapshot."

[api]
endpoint_families = ["chat-completions", "anthropic-messages"]
auth = "API key (Bearer) against https://api.deepseek.com (OpenAI format) or https://api.deepseek.com/anthropic (Anthropic format). OpenCode uses the deepseek provider with the same key."
streaming = "OpenAI-compatible chat completions; standard streaming."

[caching]
supported = true
mode = "implicit"
how_enabled = "Automatic context caching; cache hits billed at $0.0028/M input."
ttl = "unknown"
read_pricing_per_m = 0.0028
write_pricing_per_m = "unknown"

[reasoning]
params = ["thinking (default on)", "non-thinking mode"]
defaults = "Thinking mode enabled by default, default effort 'high'. Supports switching to non-thinking mode."
quirks = [
  "Thinking mode does not support temperature, top_p, presence_penalty, or frequency_penalty.",
]

[limits]
context_window = 1000000
max_output_tokens = 384000
rate_limits = "Concurrency limit 2500 for deepseek-v4-flash (vs 500 for v4-pro)."

[pricing]
prompt_per_m = 0.14
completion_per_m = 0.28
cache_read_per_m = 0.0028
as_of = "2026-08-02"
notes = "Peak/off-peak policy announced but not yet in force: 2x prices during Beijing 9:00-12:00 and 14:00-18:00, all billing items, implementation date pending."

[[sources]]
claim = "identity: alias -> DeepSeek-V4-Flash-0731 snapshot"
url = "https://api-docs.deepseek.com/"
accessed = "2026-08-02"
quote = "The `deepseek-v4-flash` model has been updated to DeepSeek-V4-Flash-0731. The calling method remains unchanged"

[[sources]]
claim = "limits + pricing: context 1M, max output 384K, $0.0028/$0.14/$0.28, concurrency 2500, peak policy"
url = "https://api-docs.deepseek.com/quick_start/pricing"
accessed = "2026-08-02"
quote = "During peak hours, prices will be 2x the regular prices, applicable to all billing items."

[[sources]]
claim = "reasoning: thinking default with effort high; sampler params unsupported in thinking"
url = "https://api-docs.deepseek.com/guides/thinking_mode"
accessed = "2026-08-02"
quote = "Thinking mode is enabled by default, with the default effort being `high`"

[[sources]]
claim = "api: max_tokens bounded by context length"
url = "https://api-docs.deepseek.com/api/create-chat-completion"
accessed = "2026-08-02"
quote = "The total length of input tokens and generated tokens is limited by the model's context length."

[[sources]]
claim = "cross-check: release date, open weights, 1,000,000 / 384,000 limits"
url = "https://models.dev/models/deepseek/deepseek-v4-flash"
accessed = "2026-08-02"
quote = "Context: 1,000,000"
```

## Appendix D — `registry/model-capabilities/qwen3.8-max-preview.toml`

```toml
# Produced from the opencode-model-audition run (2026-08-02): grounded
# capability research by the research--deepseek cell (18 verified quotes,
# several from Chinese-language Alibaba docs), cross-validated against the
# research--qwen cell's independent report. Saved page excerpts live in the
# run workdir under research--deepseek/sources/.

[model]
key = "alibaba-token-plan-cn/qwen3.8-max-preview"
display = "Qwen 3.8 Max Preview"
vendor = "Alibaba"
release_date = "2026-07-19"
snapshot = "preview"
snapshot_note = "PREVIEW: Alibaba states capabilities will keep iterating during preview, and the model will be TAKEN OFFLINE or replaced by a GA version when preview ends. Treat scoreboard evidence as provisional and expect the slug to disappear."

[api]
endpoint_families = ["chat-completions", "anthropic-messages", "dashscope"]
auth = "Alibaba Cloud Model Studio Token Plan subscription (Credits-based); OpenCode provider alibaba-token-plan-cn. Compatible-mode base URL pattern: https://[{WorkspaceId}].cn-beijing.maas.aliyuncs.com/compatible-mode/v1. Token Plan is restricted to the Beijing (华北2) region."
streaming = "unknown"

[caching]
supported = "unknown"
mode = "unknown"

[reasoning]
params = ["reasoning_content (always returned)"]
defaults = "Thinking-ONLY: the model always reasons before replying and thinking cannot be switched off. Reasoning arrives in reasoning_content, the answer in content."
quirks = [
  "Classed by Alibaba as a reasoning + vision-understanding + text-generation model.",
]

[limits]
context_window = 1000000
max_output_tokens = 131072
rate_limits = "unknown"

[pricing]
prompt_per_m = "n/a"
completion_per_m = "n/a"
as_of = "2026-08-02"
notes = "Not sold per-token: Token Plan subscription only (personal promo tiers Lite ¥39 / Standard ¥139 / Pro ¥499 per month; usage packs ¥100 for 20,000 Credits). During preview, Credits consumption is discounted to 1/10, and night calls (22:00-08:00 Beijing) drop to 0.2x standard on top of that."

[[sources]]
claim = "identity + api: Token Plan availability, thinking-only series, interfaces"
url = "https://help.aliyun.com/zh/model-studio/models"
accessed = "2026-08-02"
quote = "qwen3.8-max-preview 目前仅面向 Token Plan 订阅用户提供"

[[sources]]
claim = "identity: preview status; model retired or replaced after preview"
url = "https://help.aliyun.com/zh/model-studio/token-plan-overview"
accessed = "2026-08-02"
quote = "预览结束后该模型会下线或替换成正式版本"

[[sources]]
claim = "reasoning: thinking-only, reasoning_content field"
url = "https://help.aliyun.com/zh/model-studio/deep-thinking"
accessed = "2026-08-02"
quote = "仅思考模式：模型始终在回复前进行思考，无法关闭。"

[[sources]]
claim = "pricing: personal Token Plan tiers and usage packs"
url = "https://help.aliyun.com/zh/model-studio/token-plan-personal-overview"
accessed = "2026-08-02"
quote = "原价 60 元/月 限时 39 元/月"

[[sources]]
claim = "pricing: 1/10 preview Credits discount and 0.2x night window"
url = "https://help.aliyun.com/zh/model-studio/token-plan-overview"
accessed = "2026-08-02"
quote = "每晚 22:00 - 次日 08:00 期间调用模型，Credits 消耗再享 2 折"

[[sources]]
claim = "limits cross-check: context 1,000,000 / output 131,072, closed weights"
url = "https://models.dev/models/alibaba/qwen3.8-max-preview"
accessed = "2026-08-02"
quote = "Output limit: 131,072"
```
