"""The freeze must bind the written hypotheses of Vol. 2 (HYPOTHESES_v2.md)."""
from __future__ import annotations

import json
import os
import sys
import tempfile
import unittest
from types import SimpleNamespace

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from athena import freeze  # noqa: E402


class FakePack:
    def fingerprint(self):
        return {"pack": "fake"}


def fake_args():
    a = {k: None for k in freeze.SETTING_KEYS}
    a.update(pack="fake", task="rename", conditions="none,graph", backend="mock:oracle", seed=42, repeats=1)
    return SimpleNamespace(**a)


class TestHypothesesV2Binding(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.h2 = os.path.join(self.tmp.name, "HYPOTHESES_v2.md")
        self.saved = freeze.HYPOTHESES_V2
        freeze.HYPOTHESES_V2 = self.h2
        with open(self.h2, "w", encoding="utf-8") as f:
            f.write("H1: ...\n")
        self.path = os.path.join(self.tmp.name, "frozen.json")

    def tearDown(self):
        freeze.HYPOTHESES_V2 = self.saved
        self.tmp.cleanup()

    def test_default_path_is_the_repository_root(self):
        self.assertEqual(os.path.basename(self.saved), "HYPOTHESES_v2.md")
        self.assertEqual(os.path.dirname(self.saved), os.path.dirname(ROOT))

    def test_hash_is_recorded_and_verified(self):
        fp = freeze.write_frozen(self.path, fake_args(), FakePack())
        self.assertEqual(len(fp["hypotheses_v2_sha256"]), 64)
        self.assertEqual(freeze.verify(self.path, fake_args(), FakePack()), [])

    def test_change_of_the_registration_is_a_difference(self):
        freeze.write_frozen(self.path, fake_args(), FakePack())
        with open(self.h2, "a", encoding="utf-8") as f:
            f.write("H2: ...\n")
        diffs = freeze.verify(self.path, fake_args(), FakePack())
        self.assertTrue(any(d.startswith("hypotheses_v2_sha256") for d in diffs), diffs)

    def test_line_ending_change_is_not_a_difference(self):
        freeze.write_frozen(self.path, fake_args(), FakePack())
        with open(self.h2, "wb") as f:
            f.write(b"H1: ...\r\n")
        self.assertEqual(freeze.verify(self.path, fake_args(), FakePack()), [])

    def test_removed_registration_is_a_difference(self):
        freeze.write_frozen(self.path, fake_args(), FakePack())
        os.remove(self.h2)
        diffs = freeze.verify(self.path, fake_args(), FakePack())
        self.assertTrue(any(d.startswith("hypotheses_v2_sha256") for d in diffs), diffs)

    def test_freeze_made_without_the_file_still_verifies(self):
        os.remove(self.h2)
        fp = freeze.write_frozen(self.path, fake_args(), FakePack())
        self.assertNotIn("hypotheses_v2_sha256", fp)
        with open(self.h2, "w", encoding="utf-8") as f:
            f.write("later\n")
        self.assertEqual(freeze.verify(self.path, fake_args(), FakePack()), [])


if __name__ == "__main__":
    unittest.main()
