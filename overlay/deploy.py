#!/usr/bin/env python3
"""Reproduce this operator's exact Ringer setup on another machine.

Stdlib only, idempotent, and it RESOLVES the machine-specific paths rather than
asking you to hand-edit them — those paths are the whole reason a config file
cannot just be copied between laptops.

    python overlay/deploy.py            # deploy
    python overlay/deploy.py --check    # report only, change nothing

What it writes:
  ~/.config/ringer/config.toml          4 lanes with resolved binary paths
  ~/.kimi-code/config.toml              adds k3-low / k3-high / k3-max aliases
  ~/.claude/rules/model-routing.md      the routing table
  ~/.claude/skills/ringer/SKILL.md      the orchestrator playbook
  ~/.ringer/runs.jsonl                  seeded from overlay/state/runs.seed.jsonl
                                        (harness rows only — see DEPLOY.md)

Every existing file is backed up to <name>.bak-<UTC timestamp> first.
Afterwards run, from the repo root:

    python ringer.py install-agent                        # hooks
    python ringer.py db rebuild                           # scoreboard
    python ringer.py run overlay/probes/lane-probe.json    # PROVE it
"""
from __future__ import annotations

import argparse
import os
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
HOME = Path.home()
WINDOWS = os.name == "nt"

# ── lane binaries ────────────────────────────────────────────────────────────
# On WINDOWS the bin MUST be a native .exe: CreateProcess routes .cmd/.bat
# through cmd.exe, which DROPS any argument containing a newline, so a
# multi-line {spec} arrives as nothing — silently. Hence the explicit hunt for
# codex's vendored codex.exe rather than the codex.cmd that sits on PATH.
# On macOS/Linux there is no such trap: PATH entries are shebang scripts or
# symlinks and argv survives intact, so which() is authoritative.
if WINDOWS:
    CANDIDATES = {
        "codex": ([HOME / "AppData/Roaming/npm/node_modules/@openai/codex/node_modules"
                          "/@openai/codex-win32-x64/vendor/x86_64-pc-windows-msvc/bin/codex.exe"], "codex"),
        "claude": ([HOME / ".local/bin/claude.exe"], "claude"),
        "kimi": ([HOME / ".kimi-code/bin/kimi.exe"], "kimi"),
        "python": ([Path(sys.executable)], "python3"),
    }
else:
    CANDIDATES = {
        "codex": ([], "codex"),
        "claude": ([HOME / ".local/bin/claude"], "claude"),
        "kimi": ([HOME / ".kimi-code/bin/kimi"], "kimi"),
        "python": ([Path(sys.executable)], "python3"),
    }

K3_ALIASES = """
# Per-effort k3 aliases. Kimi Code's models-table keys ARE the -m aliases and
# default_effort is per-alias, so these three point at one underlying "k3" with
# different effort — this is how the native CLI gets per-dispatch adaptive
# effort despite having no --effort flag. Do NOT tune via the global
# [thinking] effort instead: that is shared state and races under parallel runs.
[models."k3-low"]
provider = "managed:kimi-code"
model = "k3"
max_context_size = 1048576
capabilities = [ "thinking", "always_thinking", "image_in", "video_in", "tool_use" ]
display_name = "K3 (low effort)"
support_efforts = [ "low", "high", "max" ]
default_effort = "low"

[models."k3-high"]
provider = "managed:kimi-code"
model = "k3"
max_context_size = 1048576
capabilities = [ "thinking", "always_thinking", "image_in", "video_in", "tool_use" ]
display_name = "K3 (high effort)"
support_efforts = [ "low", "high", "max" ]
default_effort = "high"

[models."k3-max"]
provider = "managed:kimi-code"
model = "k3"
max_context_size = 1048576
capabilities = [ "thinking", "always_thinking", "image_in", "video_in", "tool_use" ]
display_name = "K3 (max effort)"
support_efforts = [ "low", "high", "max" ]
default_effort = "max"
"""


def resolve(lane: str) -> Path | None:
    paths, path_name = CANDIDATES[lane]
    for p in paths:
        if p.exists():
            return p
    found = shutil.which(path_name)
    return Path(found) if found else None


def backup(path: Path) -> Path | None:
    if not path.exists():
        return None
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    dest = path.with_name(f"{path.name}.bak-{stamp}")
    shutil.copy2(path, dest)
    return dest


def write(path: Path, text: str, check: bool) -> None:
    if check:
        print(f"  would write {path}")
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    b = backup(path)
    path.write_text(text, encoding="utf-8")
    print(f"  wrote {path}" + (f"  (backup: {b.name})" if b else ""))


def q(p: Path) -> str:
    """TOML literal string — backslashes stay literal, so Windows paths are safe."""
    return "'" + str(p) + "'"


WINDOWS_NOTES = """#
# WINDOWS NOTES (this machine):
#   - NEVER point an engine at a .cmd shim. CreateProcess routes .cmd through
#     cmd.exe, which DROPS any argument containing a newline: a multi-line
#     spec arrives as NOTHING, no error, and the worker answers a truncated
#     prompt. Probed: "line one:\\nPAYLOAD\\nline three" -> .cmd: []  .exe: intact.
#   - Checks run via create_subprocess_shell = cmd.exe, so POSIX check syntax
#     fails ("'{' is not recognized"). Wrap every check as:  bash -c '...'
"""

POSIX_NOTES = """#
# macOS / Linux NOTES (this machine):
#   - PATH entries are shebang scripts or symlinks and argv survives intact,
#     so the Windows .cmd newline trap does not apply here.
#   - Checks run via /bin/sh, so POSIX check syntax works natively. The shared
#     probe manifest still wraps its checks in `bash -c` so ONE manifest runs
#     on both machines; that is harmless here, not required.
#   - The opencode lane's sandbox wrapper IS macOS Seatbelt, so that lane can
#     be enabled here if you add an OpenRouter key — see
#     overlay/config/config.toml.example.
"""


def build_ringer_config(bins: dict[str, Path]) -> str:
    notes = WINDOWS_NOTES if WINDOWS else POSIX_NOTES
    return f"""# Ringer config — generated by overlay/deploy.py. Re-run it rather than
# hand-editing, so both laptops stay identical.
{notes}#
# No qwen lane exists on this fleet. Do not add one.

state_dir = "~/.ringer"
dashboard_port_base = 8787
allow_full_access = false

[eval]
backend = "jsonl"
jsonl_path = "~/.ringer/runs.jsonl"

[artifact]
enabled = true
out = "~/.ringer/artifacts/{{run_id}}.html"
report_out = "~/.ringer/artifacts/{{run_id}}-report.html"
index_out = "~/.ringer/artifacts/index.html"

# codex — GPT-5.6 Sol/Terra/Luna. Per-task model; effort via engine_args
# ["-c","model_reasoning_effort=high|xhigh|max"].
[engines.codex]
bin = {q(bins['codex'])}
args_template = ["exec", "--skip-git-repo-check", "{{access_args}}", "{{model_args}}", "{{engine_args}}", "-C", "{{taskdir}}", "{{spec}}"]
sandbox_args = ["--sandbox", "workspace-write"]
full_access_args = ["--dangerously-bypass-approvals-and-sandbox"]
token_regex = "tokens\\\\s+used\\\\s*:?\\\\s*([0-9][0-9,]*)"
model_report_regex = "(?m)^model:[ \\\\t]*([^ \\\\t\\\\r\\\\n]+)[ \\\\t]*\\\\r?$"

# claude — sonnet/opus/fable. Uses {{model}} + explicit --model ({{model_args}}
# would emit "-m", which is not a --model short flag). Effort via engine_args
# ["--effort","low|high|max"]. Headless -p needs skip-permissions to write.
[engines.claude]
bin = {q(bins['claude'])}
model_default = "sonnet"
args_template = ["{{access_args}}", "--model", "{{model}}", "{{engine_args}}", "-p", "{{spec}}"]
sandbox_args = ["--dangerously-skip-permissions"]
full_access_args = []

# kimi — the only k3 lane. Effort rides the model field: k3-low / k3-high /
# k3-max (all -> underlying k3, 1M context). -p auto-approves and there is no
# sandbox flag, so writes are unconfined — scope specs to task dirs.
[engines.kimi]
bin = {q(bins['kimi'])}
model_default = "kimi-code/k3"
args_template = ["{{access_args}}", "{{model_args}}", "{{engine_args}}", "-p", "{{spec}}"]
sandbox_args = []
full_access_args = []

# mock — free local worker, no credentials, no network. Smokes the harness
# itself without spending a plan call.
[engines.mock]
bin = {q(bins['python'])}
model_default = "mock"
args_template = [{q(REPO / 'engines' / 'mock_worker.py')}, "{{spec}}"]
sandbox_args = []
full_access_args = []

# Not wired: grok (needs SuperGrok/X Premium Plus), opencode (needs an
# OpenRouter key; its sandbox wrapper is macOS Seatbelt).
# Reference blocks: overlay/config/config.toml.example
"""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="report only, change nothing")
    args = ap.parse_args()
    check = args.check

    print(f"repo: {REPO}\nhome: {HOME}\n")

    print("resolving lane binaries:")
    bins: dict[str, Path] = {}
    missing: list[str] = []
    for lane in CANDIDATES:
        p = resolve(lane)
        print(f"  {lane:<8} {'OK  ' + str(p) if p else 'MISSING'}")
        if p:
            bins[lane] = p
        else:
            missing.append(lane)
    if missing:
        print(f"\nERROR: cannot resolve {', '.join(missing)}.")
        print("Install the CLI and authenticate it, then re-run:")
        print("  codex  -> npm i -g @openai/codex && codex login")
        print("  claude -> install Claude Code, then `claude login`")
        print("  kimi   -> install Kimi Code CLI, then `kimi login`")
        return 1

    print("\nringer config:")
    write(HOME / ".config/ringer/config.toml", build_ringer_config(bins), check)

    print("\nkimi per-effort aliases:")
    kimi_cfg = HOME / ".kimi-code/config.toml"
    if not kimi_cfg.exists():
        print(f"  SKIP — {kimi_cfg} not found (run `kimi login` first)")
    else:
        text = kimi_cfg.read_text(encoding="utf-8")
        if '[models."k3-low"]' in text:
            print("  already present")
        else:
            marker = "[[hooks]]"
            new = (text.replace(marker, K3_ALIASES.lstrip("\n") + "\n" + marker, 1)
                   if marker in text else text.rstrip() + "\n" + K3_ALIASES)
            write(kimi_cfg, new, check)
            print("  validate with: kimi doctor")

    print("\nclaude overlay:")
    for src, dst in [
        (REPO / "overlay/rules/model-routing.md", HOME / ".claude/rules/model-routing.md"),
        (REPO / "overlay/skills/ringer/SKILL.md", HOME / ".claude/skills/ringer/SKILL.md"),
    ]:
        write(dst, src.read_text(encoding="utf-8"), check)

    print("\neval log seed:")
    seed = REPO / "overlay/state/runs.seed.jsonl"
    live = HOME / ".ringer/runs.jsonl"
    if not seed.exists():
        print(f"  SKIP — no seed at {seed}")
    elif live.exists() and live.stat().st_size > 0:
        print(f"  SKIP — {live} already has data; delete it first to reseed")
    else:
        write(live, seed.read_text(encoding="utf-8"), check)

    print("\nnext (from the repo root):")
    print("  python ringer.py install-agent")
    print("  python ringer.py db rebuild")
    print("  python ringer.py run overlay/probes/lane-probe.json")
    print("\nThe probe run is the acceptance test: 5/5 PASS, exit 0, or the")
    print("deployment is not done. A lane is not installed until an executed")
    print("check has passed on it.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
