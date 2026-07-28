#!/usr/bin/env python3
"""Acceptance check for effort attribution across all three live lanes.

Authored by the orchestrator, not the worker. A worker must make this pass
WITHOUT editing this file.

Context: routing treats a cell as (model x effort). Until this passes, the
eval log records the effort half for codex only -- claude and kimi rows log
null, so the scoreboard cannot distinguish k3-low from k3-max.
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from ringer import effective_reasoning_effort_from_command as eff  # noqa: E402


class CodexFormRegression(unittest.TestCase):
    """The pre-existing behaviour must not change."""

    def test_config_flag_pair(self) -> None:
        self.assertEqual(eff(["-c", "model_reasoning_effort=xhigh"]), "xhigh")

    def test_quoted_value(self) -> None:
        self.assertEqual(eff(["-c", 'model_reasoning_effort="max"']), "max")

    def test_embedded_in_larger_item(self) -> None:
        self.assertEqual(eff(["-c", "foo=1,model_reasoning_effort=low"]), "low")


class ClaudeArgvForm(unittest.TestCase):
    """`--effort <value>` arrives as two adjacent argv items."""

    def test_separate_items(self) -> None:
        self.assertEqual(eff(["--model", "opus", "--effort", "high", "-p", "spec"]), "high")

    def test_equals_form(self) -> None:
        self.assertEqual(eff(["--effort=max", "-p", "spec"]), "max")

    def test_low(self) -> None:
        self.assertEqual(eff(["--effort", "low"]), "low")

    def test_dangling_flag_is_not_a_crash(self) -> None:
        self.assertIsNone(eff(["--effort"]))


class KimiAliasForm(unittest.TestCase):
    """The kimi CLI carries effort in the model alias, not a flag."""

    def test_alias_max(self) -> None:
        self.assertEqual(eff(["-m", "k3-max", "-p", "spec"]), "max")

    def test_alias_low(self) -> None:
        self.assertEqual(eff(["-m", "k3-low", "-p", "spec"]), "low")

    def test_alias_high(self) -> None:
        self.assertEqual(eff(["-m", "k3-high", "-p", "spec"]), "high")

    def test_namespaced_alias(self) -> None:
        self.assertEqual(eff(["-m", "kimi-code/k3-max"]), "max")

    def test_legacy_k3max_alias(self) -> None:
        self.assertEqual(eff(["-m", "kimi-code/k3max"]), "max")


class MustNotGuess(unittest.TestCase):
    """Silence is correct when effort was never stated explicitly."""

    def test_bare_k3_is_config_dependent(self) -> None:
        # Bare k3 takes whatever default_effort the config gives it. Guessing
        # here would write a fabricated value into the eval log.
        self.assertIsNone(eff(["-m", "kimi-code/k3"]))

    def test_bare_k3_unnamespaced(self) -> None:
        self.assertIsNone(eff(["-m", "k3"]))

    def test_empty_command(self) -> None:
        self.assertIsNone(eff([]))

    def test_unrelated_argv(self) -> None:
        self.assertIsNone(eff(["exec", "-C", "/tmp/x", "write a file"]))

    def test_sonnet_without_effort(self) -> None:
        self.assertIsNone(eff(["--model", "sonnet", "-p", "spec"]))

    def test_max_context_is_not_an_effort(self) -> None:
        # "max" appears inside an unrelated token; must not be harvested.
        self.assertIsNone(eff(["-c", "max_context_size=1048576"]))


class ExplicitFlagBeatsAlias(unittest.TestCase):
    def test_flag_wins(self) -> None:
        self.assertEqual(eff(["-m", "k3-low", "--effort", "max"]), "max")


if __name__ == "__main__":
    unittest.main(verbosity=2)
