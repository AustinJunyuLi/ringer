# Reinstall Ringer (qwen-free) + deploy the scoreboard-overrule routing rule

## Context

Ringer was removed from this machine on 2026-07-27 after a qwen worker stalled,
and the machine was put on a Claude-only routing rule that declares Ringer
unavailable. The trigger was qwen specifically, not Ringer — Codex, Kimi and
Claude lanes were never implicated.

Goal: bring Ringer back with every backend **except** qwen, and deploy the
evidence-driven routing doctrine (scoreboard overrules the table) that was
authored in the fork but never installed here.

Two recon findings shrink the job considerably:

- **The fork is already qwen-free.** `overlay/config/config.toml.example` has 7
  engine blocks — codex, grok, mock, opencode, kimi, claude, kimiclaude — and no
  qwen. The qwen lanes existed only in the archived local
  `~/.config/ringer/config.toml`. Qwen survives in exactly one repo file:
  `registry/model-identity.toml`.
- **The scoreboard-overrule logic already exists**, in
  `overlay/rules/model-routing.md`, never deployed to `~/.claude/rules/`. It
  carries the promotion ladder (untested → probation → proven at 3+ tasks,
  first-try ≥ 0.67), the anti-fossilization rule (~1 task per low-stakes run to
  an untested cell), and "strong priors, not laws; let the scoreboard overturn
  them." Nothing to author — this needs deploying, not writing.

`ringer.py` is byte-identical between the fork and upstream (md5
`85af79dd…`), so no engine code changes are in scope.

**Decisions taken (user, this session):** purge qwen rows from the restored
eval log; Ringer becomes the default delegation path with routing words
overriding per job.

## Steps

### 1. Clone

`git clone https://github.com/AustinJunyuLi/ringer ~/fleet/swarm` — the prior
path on this machine, per the removal archive. The fork is 1 commit behind
upstream (missing `templates/bakeoff-kit`); optionally cherry-pick it after.

### 2. Purge qwen from the checkout

`registry/model-identity.toml` — delete the `[engines.qwen]`,
`[engines.qwencode]` and `[engines.kimiqwen]` blocks and their nested
`.models."…"` tables (7 model entries). Nothing else in the repo mentions qwen.

### 3. Write `~/.config/ringer/config.toml`

Adapt `overlay/config/config.toml.example` to Windows paths. Five live lanes:

| Lane | bin | Notes |
|---|---|---|
| `codex` | `C:\Users\ALi\AppData\Roaming\npm\codex.cmd` | Roaming npm copy, NOT winget-node — the winget sandbox helper path exceeds MAX_PATH |
| `claude` | `C:\Users\ALi\.local\bin\claude.exe` | explicit `--model`, `-p`, `--dangerously-skip-permissions` |
| `kimiclaude` | `C:\Users\ALi\.local\bin\claude-kimi.cmd` | k3 via Claude harness; preferred k3 lane |
| `kimi` | `C:\Users\ALi\.kimi-code\bin\kimi.exe` | native CLI; heavier on the request-metered plan |
| `mock` | `python` + `engines/mock_worker.py` | free, no credentials — used for harness smoke tests |

`grok` and `opencode` stay commented out: no X Premium Plus, no OpenRouter key.

Bin values must be full paths with extension — Ringer spawns via
`create_subprocess_exec` (no shell), so a bare name fails.

### 4. Restore the Kimi wrapper

`~/.local/bin/claude-kimi.cmd` from the archive, with the four gaps the removal
README flags as missing versus the fork's `overlay/bin/claude-kimi`:
`ANTHROPIC_MODEL=k3[1m]`, `CLAUDE_CODE_MAX_CONTEXT_TOKENS=1000000`, the
`ANTHROPIC_DEFAULT_*_MODEL` pins, and `CLAUDE_CODE_SUBAGENT_MODEL`.

Key already present and readable at `~/.kimi-code/claude-code-key`.

### 5. Restore state, minus qwen

Copy `runs.jsonl` from the archive filtering out rows whose `model` matches
qwen — 35 rows in, **22 out**. Then `./ringer.py db rebuild` to regenerate
`ringer.db` from the filtered log rather than restoring the archived DB.

Honest note on what survives: of the 22, roughly 17 are `probe` and `bakeoff`
rows. Real-task evidence is about 5 rows. The scoreboard starts near-empty and
that is the correct starting state.

### 6. Install the Claude Code integration — order matters

1. `./ringer.py install-agent` first. It writes `~/.claude/settings.json`
   (backed up automatically) adding a PreToolUse `Bash` hook and a PostToolUse
   `Edit|Write` hook, both invoking `python3 <repo>/hooks/ringer_nudge.py`, and
   copies the repo's **generic** `.claude/skills/ringer/SKILL.md` into
   `~/.claude/skills/ringer/SKILL.md`.
2. **Then** overwrite that skill with the personalized edition from
   `overlay/skills/ringer/SKILL.md`, per the fork README's deployment table.
   Running these in the other order silently reverts you to the public copy.

`python3` resolves to a real 3.12.10 on this box, so the hook command works
as written.

Flagging the blast radius: these hooks fire on every Bash call and every
edit, in every project, not just Ringer work. That is consistent with the
"Ringer default" decision, but say the word and I'll skip the hooks and install
the skill only.

### 7. Deploy the routing rule — merge, not overwrite

`overlay/rules/model-routing.md` → `~/.claude/rules/model-routing.md`, backing
up the current Claude-only file first. Deploy it **with one edit**:

The fork's file says *"Fable is the brain and never touches the code"* and
names Fable as boss throughout. That contradicts the Fable-boss retirement
recorded on 2026-07-25 and reaffirmed by the 2026-07-27 port: the boss is
**role-defined — the session model — never model-named**, with Fable callable
but user-invoked only. The retirement is the newer decision and it wins. I will
rewrite the boss references to the role-defined form and keep everything else
verbatim: the execution surface, the routing table, the hard exclusions, the
cap-pressure notes, and the scoreboard rules.

Everything else transfers as written. Per the user decision, the
execution-surface section stands as authored — Ringer is the default for
swarm-shaped work; `workflow`/`native swarm` and `inline` override per job;
ultracode remains a standing native declaration.

## Verification (all executed, not asserted)

1. `./ringer.py lint` on each probe manifest — must exit 0.
2. `./ringer.py demo` — the built-in 3-task toy manifest, end to end. This is
   the pass/fail gate on the install itself.
3. **One probe per live lane** — codex, claude, kimiclaude, kimi — using
   `templates/probe/` and the fork's `overlay/probes/kimiclaude-isolated-probe.json`
   with its paths re-pointed. A lane is not installed until a probe with an
   executed check passes on it. Four small dispatches.
4. `./ringer.py models` — confirm 22 rows, zero qwen, and that the new probe
   rows land with the right `model` and `task_type`.
5. Confirm `~/.claude/skills/ringer/SKILL.md` is the personalized edition
   (~18.7 KB), not the generic one (~5.6 KB) — the step-6 ordering trap.
6. `grep -ri qwen ~/fleet/swarm ~/.config/ringer ~/.claude/rules` returns
   nothing.

Per the session-logging rule, I'll save this plan to
`quality_reports/plans/2026-07-27_ringer-reinstall-qwen-free.md` and open a
session log once approved.

## Not in scope

- No changes to `ringer.py` — it is byte-identical to upstream and stays that way.
- No `grok`/`opencode` lanes (no credentials).
- Not pushing anything to the fork on GitHub.
