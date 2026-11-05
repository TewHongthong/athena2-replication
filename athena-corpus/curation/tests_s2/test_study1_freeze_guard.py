#!/usr/bin/env python3
"""The Study 2 code must leave the Study 1 setup unchanged: every frozen file of Study 1 still matches the harness
code (athena/*.py, athena_sim.py, vendor/output_validator.py) and, for runs that recorded it, the curation code.
The frozen files of Study 2 (frozen_*-s2_*.json) record the Study 2 code and are checked in athena-sim/tests_s2.

  python3 -m unittest discover -s tests_s2       (from the curation folder)
"""
import glob
import json
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
SIM = os.path.normpath(os.path.join(HERE, "..", "..", "..", "athena-sim"))
sys.path.insert(0, SIM)

from athena import freeze, pipeline  # noqa: E402


class TestStudy1FrozenFiles(unittest.TestCase):
    def test_frozen_files_still_match(self):
        files = sorted(f for f in glob.glob(os.path.join(SIM, "frozen_*.json")) if "-s2_" not in os.path.basename(f))
        self.assertGreater(len(files), 0)
        code = freeze.code_hashes()
        cur = pipeline.curation_fingerprint()
        bad = []
        for f in files:
            with open(f, encoding="utf-8") as fh:
                fr = json.load(fh)
            if fr["code_sha256"] != code:
                bad.append(f"{os.path.basename(f)}: harness code")
            if "curation_sha256" in fr and fr["curation_sha256"] != cur:
                bad.append(f"{os.path.basename(f)}: curation code")
        self.assertEqual(bad, [])


if __name__ == "__main__":
    unittest.main()
