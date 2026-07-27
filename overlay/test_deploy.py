#!/usr/bin/env python3
"""Check that overlay/deploy.py generates a valid config on BOTH platforms.

The Mac branch cannot be exercised by running deploy.py on Windows, so this
drives build_ringer_config directly with each platform's shape. Run it before
trusting a deploy on a machine you are not sitting at:

    python overlay/test_deploy.py
"""
from __future__ import annotations

import importlib.util
import pathlib
import sys
import tomllib

HERE = pathlib.Path(__file__).resolve().parent

CASES = {
    "windows": (True, pathlib.PureWindowsPath(r"C:\Users\op\fleet\swarm"), {
        "codex": pathlib.PureWindowsPath(r"C:\npm\@openai\codex\bin\codex.exe"),
        "claude": pathlib.PureWindowsPath(r"C:\Users\op\.local\bin\claude.exe"),
        "kimi": pathlib.PureWindowsPath(r"C:\Users\op\.kimi-code\bin\kimi.exe"),
        "python": pathlib.PureWindowsPath(r"C:\Python312\python.exe"),
    }),
    "macos": (False, pathlib.PurePosixPath("/Users/op/fleet/swarm"), {
        "codex": pathlib.PurePosixPath("/opt/homebrew/bin/codex"),
        "claude": pathlib.PurePosixPath("/Users/op/.local/bin/claude"),
        "kimi": pathlib.PurePosixPath("/Users/op/.kimi-code/bin/kimi"),
        "python": pathlib.PurePosixPath("/opt/homebrew/bin/python3"),
    }),
}


def load():
    spec = importlib.util.spec_from_file_location("_deploy", HERE / "deploy.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def main() -> int:
    dep = load()
    for name, (is_win, repo, bins) in CASES.items():
        dep.WINDOWS, dep.REPO = is_win, repo
        out = dep.build_ringer_config(bins)

        # must be valid TOML — a broken quote here bricks a remote machine
        cfg = tomllib.loads(out)

        assert sorted(cfg["engines"]) == ["claude", "codex", "kimi", "mock"], \
            f"{name}: wrong lanes {sorted(cfg['engines'])}"
        for lane in cfg["engines"]:
            want = bins["python" if lane == "mock" else lane]
            got = cfg["engines"][lane]["bin"]
            assert got == str(want), f"{name}/{lane}: bin {got!r} != {want!r}"

        # platform guidance must not cross over
        assert ("cmd.exe" in out) == is_win, f"{name}: cmd.exe guidance wrong"
        marker = "WINDOWS NOTES" if is_win else "macOS / Linux NOTES"
        assert marker in out, f"{name}: missing {marker!r}"

        # no qwen lane may ever be generated
        assert "qwen" not in out.lower().replace("no qwen lane exists", ""), \
            f"{name}: qwen leaked into generated config"

        print(f"  {name:<8} OK — valid TOML, 4 lanes, correct paths and notes")

    print("both platform branches generate a valid config")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
