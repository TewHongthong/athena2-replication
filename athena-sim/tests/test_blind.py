import csv
import json
import os
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))

import make_blind_sheet as mb  # noqa: E402
import score_blind as sb  # noqa: E402


def trial(i, ok, name="good_name"):
    prompt = "TASK\nx\n\nCODING STANDARD\nSECRET-CONDITION-TEXT\n\nCODE\n```cpp\nint f_%d() {}\n```\n\nOUTPUT FORMAT\ny" % i
    return {"key": "k%03d" % i, "run_id": "r1", "unit_id": "u%d" % i, "repeat": 0, "pack": "godot",
            "model": "MODEL-X", "condition": "graph", "language": "cpp", "kind": "function",
            "standard_id": "GODOT", "injected": "BAD_%d" % i, "error": None, "prompt": prompt,
            "parsed": {"suggested_name": name}, "metrics": {"core_ok": ok, "core_failed": [] if ok else ["R1"]}}


class BlindTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        run = os.path.join(self.tmp, "runs", "test_a_meta")
        os.makedirs(run)
        rows = [trial(i, i % 5 != 0) for i in range(100)]
        rows.append(trial(900, True, name=""))
        bad = trial(901, True)
        bad["metrics"] = None
        rows.append(bad)
        with open(os.path.join(run, "trials.jsonl"), "w") as fh:
            for r in rows:
                fh.write(json.dumps(r) + "\n")
        self.glob = os.path.join(self.tmp, "runs", "test_*_meta")
        self.out = os.path.join(self.tmp, "out")

    def make(self, seed="s"):
        mb.main(["--runs-glob", self.glob, "--out-dir", self.out, "--n-pass", "10", "--n-fail", "8", "--seed", seed])

    def test_sheet_hides_condition_model_and_verdict(self):
        self.make()
        text = open(os.path.join(self.out, "blind_sheet.csv"), encoding="utf-8-sig").read()
        for hidden in ("SECRET-CONDITION-TEXT", "MODEL-X", "graph", "core_ok", "R1", "BAD_"):
            self.assertNotIn(hidden, text)
        rows = list(csv.DictReader(open(os.path.join(self.out, "blind_sheet.csv"), encoding="utf-8-sig")))
        self.assertEqual(len(rows), 18)
        self.assertTrue(all("int f_" in r["code_with_name"] for r in rows))
        self.assertTrue(all(r["name_to_judge"] in r["question"] for r in rows))

    def test_deterministic_and_frame_excludes_unusable(self):
        self.make("a")
        first = open(os.path.join(self.out, "blind_key.csv")).read()
        self.make("a")
        self.assertEqual(first, open(os.path.join(self.out, "blind_key.csv")).read())
        rep = json.load(open(os.path.join(self.out, "blind_report.json")))
        self.assertEqual(rep["frame_size"], 100)
        self.assertEqual(rep["stratum_sizes"], {"pass": 80, "fail": 20})
        self.assertEqual(rep["skipped"]["no_name"], 1)
        self.assertEqual(rep["skipped"]["no_metrics"], 1)

    def test_scoring_perfect_and_disagreement(self):
        self.make()
        sheet = list(csv.DictReader(open(os.path.join(self.out, "blind_sheet.csv"), encoding="utf-8-sig")))
        key = list(csv.DictReader(open(os.path.join(self.out, "blind_key.csv"))))
        rep = json.load(open(os.path.join(self.out, "blind_report.json")))
        kmap = {k["item"]: k for k in key}
        for s in sheet:
            s["judgement"] = "complies" if kmap[s["item"]]["core_ok"] == "1" else "does not comply"
        res = sb.score(sheet, key, rep)
        self.assertAlmostEqual(res["weighted_agreement"], 1.0)
        self.assertAlmostEqual(res["kappa"], 1.0)
        sheet[0]["judgement"] = "unsure"
        sheet[1]["judgement"] = "does not comply" if kmap[sheet[1]["item"]]["core_ok"] == "1" else "complies"
        res = sb.score(sheet, key, rep)
        self.assertEqual(len(res["unsure"]), 1)
        self.assertLess(res["weighted_agreement"], 1.0)
        self.assertIn("Disagreements", sb.render(res))

    def test_too_few_in_stratum(self):
        with self.assertRaises(SystemExit):
            mb.main(["--runs-glob", self.glob, "--out-dir", self.out, "--n-pass", "10", "--n-fail", "50"])




class ApplyNameTest(unittest.TestCase):
    def test_whole_word_only(self):
        code = "int FOO() { return FOO_X + FOO; }"
        self.assertEqual(mb.apply_name(code, "FOO", "foo"), "int foo() { return FOO_X + foo; }")


class RulesCardTest(unittest.TestCase):
    def test_card_quotes_documents(self):
        d = tempfile.mkdtemp()
        for sub in ("godot", "dotnet-runtime", "odoo"):
            os.makedirs(os.path.join(d, sub))
        open(os.path.join(d, "godot", "cpp_usage_guidelines.rst"), "w").write(
            "Intro\n-----\n\nNaming\n------\n\n- All other identifiers use ``snake_case``.\n\nSpacing\n-------\n- x\n")
        open(os.path.join(d, "dotnet-runtime", "coding-style.md"), "w").write(
            "3. We use `_camelCase` for fields.\n12. We use PascalCasing for constants.\n13. We use PascalCasing for all method names.\n14. other\n")
        open(os.path.join(d, "odoo", "coding_guidelines.rst"), "w").write(
            "- Variable name :\n    - use Pascal case for model variable\n    - use underscore lowercase notation for common variable.\n    - suffix\n\nnext\n")
        card = mb.rules_card(d)
        self.assertIn("All other identifiers use ``snake_case``.", card)
        self.assertIn("13. We use PascalCasing for all method names.", card)
        self.assertNotIn("14. other", card)
        self.assertIn("use underscore lowercase notation for common variable.", card)
        self.assertNotIn("Spacing", card)


if __name__ == "__main__":
    unittest.main()
