import json
import os
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))

import count_godot_prefix as cp  # noqa: E402


def trial(i, name, ok=True, kind="parameter", error=None, original="p_value"):
    return {"model": "M", "condition": "none", "task": "t%d" % i, "unit_id": "u%d" % i, "kind": kind,
            "original": original, "error": error, "parsed": {"suggested_name": name},
            "metrics": {"core_ok": ok}}


class CountTest(unittest.TestCase):
    def test_counts(self):
        d = os.path.join(tempfile.mkdtemp(), "test_godot_x_meta")
        os.makedirs(d)
        rows = [trial(1, "p_a"), trial(2, "r_b"), trial(3, "plain"), trial(4, "Bad", ok=False),
                trial(5, "x", kind="method"), trial(6, "y", error="boom"), trial(7, "")]
        with open(os.path.join(d, "trials.jsonl"), "w") as fh:
            for r in rows:
                fh.write(json.dumps(r) + "\n")
        got, skipped = cp.load([d])
        self.assertEqual(len(got), 4)
        self.assertEqual(skipped["other_kind"], 1)
        self.assertEqual(skipped["error"], 1)
        self.assertEqual(skipped["no_name"], 1)
        self.assertEqual(sum(r["miss"] for r in got if r["core_ok"]), 1)
        self.assertEqual(sum(r["miss"] for r in got), 2)
        self.assertIn("1/3", cp.report(got, skipped))


if __name__ == "__main__":
    unittest.main()
