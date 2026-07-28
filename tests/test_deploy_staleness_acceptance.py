#!/usr/bin/env python3
"""Acceptance check for the deploy staleness guard.

Authored by the orchestrator, not the worker. Make it pass WITHOUT editing
this file.

Why this guard exists: on 2026-07-27 a deploy authored on a machine whose
MODEL-NOTES ended at 07-22 overwrote a machine holding 07-25 work, silently
reverting a measured routing decision. Detection was luck. The guard turns a
silent reversal into a loud conflict.
"""
from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
_spec = importlib.util.spec_from_file_location("deploy_mod", ROOT / "overlay" / "deploy.py")
deploy = importlib.util.module_from_spec(_spec)
sys.modules["deploy_mod"] = deploy
_spec.loader.exec_module(deploy)


class NewestDatestamp(unittest.TestCase):
    """`newest_datestamp(text) -> str | None` finds the latest ## YYYY-MM-DD."""

    def test_finds_latest_not_first(self) -> None:
        text = "## 2026-07-22 — old\nbody\n## 2026-07-25 — newer\nbody\n"
        self.assertEqual(deploy.newest_datestamp(text), "2026-07-25")

    def test_order_independent(self) -> None:
        text = "## 2026-07-27 — newest\n## 2026-07-01 — oldest\n"
        self.assertEqual(deploy.newest_datestamp(text), "2026-07-27")

    def test_none_when_absent(self) -> None:
        self.assertIsNone(deploy.newest_datestamp("no date headings here\n"))

    def test_ignores_non_heading_dates(self) -> None:
        # A date in prose is not an entry stamp.
        self.assertIsNone(deploy.newest_datestamp("we shipped on 2026-07-25 fine\n"))


class StalenessConflict(unittest.TestCase):
    """`staleness_conflict(src, dst) -> str | None`; a string means ABORT."""

    OLD = "## 2026-07-22 — entry\n"
    NEW = "## 2026-07-25 — entry\n"

    def test_destination_newer_is_a_conflict(self) -> None:
        result = deploy.staleness_conflict(self.OLD, self.NEW)
        self.assertIsNotNone(result, "destination newer than source must conflict")
        self.assertIn("2026-07-25", result)
        self.assertIn("2026-07-22", result)

    def test_source_newer_is_fine(self) -> None:
        self.assertIsNone(deploy.staleness_conflict(self.NEW, self.OLD))

    def test_equal_is_fine(self) -> None:
        self.assertIsNone(deploy.staleness_conflict(self.NEW, self.NEW))

    def test_missing_destination_is_fine(self) -> None:
        # First install on a fresh machine: nothing to clobber.
        self.assertIsNone(deploy.staleness_conflict(self.NEW, ""))

    def test_undated_destination_is_fine(self) -> None:
        self.assertIsNone(deploy.staleness_conflict(self.NEW, "no stamps\n"))


if __name__ == "__main__":
    unittest.main(verbosity=2)
