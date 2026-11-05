#!/usr/bin/env python3
"""The Study 2 analysis (athena_s2/analysis.py, analyse_study2.py) on synthetic trials and on the core tables of the
Study 2 packs.

  python3 -m unittest discover -s tests_s2       (from the athena-sim folder)
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
SIM = os.path.dirname(HERE)
sys.path.insert(0, SIM)
sys.path.insert(0, HERE)

from athena_s2 import analysis as A  # noqa: E402
from test_s2_harness import write_bench  # noqa: E402

G_RULE = "GODOT-PARAM-INPUT-PREFIX"
D_RULE = "DOTNET-FIELD-INSTANCE-PREFIX"


def trial(pack, unit, cond, pin, rep=0, ok=True, split="test", ts="2026-01-01T00:00:00+00:00", name=None,
          kind=None, error=None, file=None, inferred=None, finish="stop"):
    godot = pack == "godot-s2"
    kind = kind or ("input_parameter" if godot else "instance_field")
    original = "p_size" if godot else "_size"
    if name is None:
        name = original if ok else "size"
    r = {"key": f"{pack}|rename|{unit}|{cond}|backend-{pin}|{rep}", "ts": ts, "pack": pack, "task": "rename",
         "unit_id": unit, "split": split, "snippet_id": unit.split("__")[0], "language": "cpp" if godot else "csharp",
         "kind": kind, "condition": cond, "backend": f"backend-{pin}", "repeat": rep, "error": error,
         "rule_id": G_RULE if godot else D_RULE, "original": original, "injected": "size",
         "injection": "prefix_strip", "file": file or f"repo:{unit}", "prompt_chars": 1000, "prompt_tokens": 250,
         "completion_tokens": 50, "cost_usd": 0.001, "finish": finish,
         "metrics": None if error else {"parse_ok": True, "suggested": name, "valid_identifier": True,
                                        "exact_match": name == original, "core_ok": ok}}
    if inferred is not None:
        r["kind_inferred"] = inferred
    return r


def write_run(root, name, recs, pin, pack, infer=False, extra_lines=()):
    d = os.path.join(root, name)
    os.makedirs(d, exist_ok=True)
    with open(os.path.join(d, "config.json"), "w", encoding="utf-8") as f:
        json.dump({"args": {"model_pin": pin, "pack": pack, "no_oracle": infer, "ontology_variant": "human"}}, f)
    with open(os.path.join(d, "trials.jsonl"), "w", encoding="utf-8") as f:
        for r in recs:
            f.write(json.dumps(r) + "\n")
        for line in extra_lines:
            f.write(line + "\n")
    return d


class _Tmp(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="athena_s2_analysis_")

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)


class TestRecords(_Tmp):
    def test_first_record_per_key_by_time(self):
        late = trial("godot-s2", "u1", "none", "m", ok=True, ts="2026-01-01T00:00:09+00:00")
        early = trial("godot-s2", "u1", "none", "m", ok=False, ts="2026-01-01T00:00:01+00:00")
        d = write_run(self.tmp, "r", [late, early], "m", "godot-s2", extra_lines=['{"key": "broken'])
        recs, runs, err = A.read_runs([d], "first")
        self.assertEqual(len(recs), 1)
        self.assertFalse(recs[0]["metrics"]["core_ok"])
        self.assertEqual((runs[0]["corrupt"], runs[0]["duplicates_not_used"], runs[0]["lines"]), (1, 1, 3))
        recs, _, _ = A.read_runs([d], "last")
        self.assertTrue(recs[0]["metrics"]["core_ok"])
        self.assertEqual(err, [])

    def test_errors(self):
        only_err = trial("godot-s2", "u1", "none", "m", error="timeout")
        err_then_ok = [trial("godot-s2", "u2", "none", "m", error="timeout", ts="2026-01-01T00:00:01+00:00"),
                       trial("godot-s2", "u2", "none", "m", ts="2026-01-01T00:00:05+00:00")]
        d = write_run(self.tmp, "r", [only_err] + err_then_ok, "m", "godot-s2")
        recs, runs, err = A.read_runs([d])
        self.assertEqual([r["unit_id"] for r in recs], ["u2"])
        self.assertEqual(len(err), 1)
        self.assertEqual(runs[0]["error_records"], 2)

    def test_infer_family_is_labelled(self):
        meta = write_run(self.tmp, "meta", [trial("godot-s2", "u1", "graph", "m", ok=True)], "m", "godot-s2")
        inf = write_run(self.tmp, "infer", [trial("godot-s2", "u1", "graph", "m", ok=False)], "m", "godot-s2", infer=True)
        recs, _, _ = A.read_runs([meta, inf])
        self.assertEqual(sorted(r["condition"] for r in recs), ["graph", "graph[infer]"])
        self.assertEqual({r["pin"] for r in recs}, {"m"})

    def test_llm_ontology_refused(self):
        d = write_run(self.tmp, "r", [trial("godot-s2", "u1", "none", "m")], "m", "godot-s2")
        with open(os.path.join(d, "config.json"), "w", encoding="utf-8") as f:
            json.dump({"args": {"ontology_variant": "llm"}}, f)
        with self.assertRaises(ValueError):
            A.read_runs([d])


def dataset(none_dev_ok, n_test=10, models=("m1", "m2")):
    """Dev: 4 tasks per pack, none passes on the first `none_dev_ok`; test: n_test tasks, 3 rounds, none fails and
    every other condition passes."""
    recs = []
    for pack in A.PACKS:
        for m in models:
            for i in range(4):
                recs.append(trial(pack, f"d{i}", "none", m, ok=i < none_dev_ok, split="dev"))
            for i in range(n_test):
                for rep in range(3):
                    recs.append(trial(pack, f"t{i}", "none", m, rep=rep, ok=False, file=f"f{i // 2}"))
                    for cond in ("fulldoc", "naming", "chunk", "bm25", "dense", "graph"):
                        recs.append(trial(pack, f"t{i}", cond, m, rep=rep, ok=True, file=f"f{i // 2}"))
                    recs.append(dict(trial(pack, f"t{i}", "graph", m, rep=rep, ok=True, file=f"f{i // 2}",
                                           inferred="input_parameter" if pack == "godot-s2" else "instance_field"),
                                     condition="graph[infer]"))
    for r in recs:
        r["pin"] = r["backend"].split("-", 1)[1]
    return recs


class TestHypotheses(unittest.TestCase):
    def test_eligibility_and_h1(self):
        res = A.analyse(dataset(none_dev_ok=2), [], [], b=200)
        self.assertTrue(all(e["eligible"] and abs(e["value"] - 0.5) < 1e-12 for e in res["eligibility"]))
        self.assertEqual(res["h1_status"], "testable")
        self.assertEqual(len(res["h1"]), 4)                          # 2 standards x 2 models
        for r in res["h1"]:
            self.assertEqual((r["up"], r["down"], r["units"]), (10, 0, 10))
            self.assertAlmostEqual(r["p"], 2 / 2 ** 10)
            self.assertTrue(r["supports"])
        self.assertEqual(res["h2"]["summary"], "supported")
        self.assertEqual(res["h4"]["summary"], "supported")
        self.assertEqual(res["h3"]["summary"], "inconclusive")       # selection ties every retrieval condition
        self.assertEqual(len(res["h3"]["retrieval"]), 12)

    def test_not_eligible(self):
        res = A.analyse(dataset(none_dev_ok=4), [], [], b=200)
        self.assertFalse(any(e["eligible"] for e in res["eligibility"]))
        self.assertEqual((res["h1_status"], res["h1"]), ("not_testable", []))
        self.assertIn("Study 2 stops", A.render(res))

    def test_compare_split_dev(self):
        recs = dataset(none_dev_ok=2)
        recs += [dict(r, condition="graph", key=r["key"].replace("|none|", "|graph|"),
                      metrics=dict(r["metrics"], core_ok=True)) for r in recs if r["split"] == "dev"]
        res = A.analyse(recs, [], [], compare_split="dev", b=200)
        self.assertEqual({(r["units"], r["up"], r["tie"]) for r in res["h1"]}, {(4, 2, 2)})
        self.assertIn("not a result of the study", A.render(res))

    def test_drift_and_sensitivity(self):
        recs = dataset(none_dev_ok=2, models=("m1", "m2", "m3"))
        canary = []
        for m in ("m1", "m2", "m3"):
            for pack in A.PACKS:
                for i in range(12):
                    b = trial(pack, f"d{i}", "none", m, split="dev", ok=True, ts="2026-01-01T00:00:00+00:00")
                    a = trial(pack, f"d{i}", "none", m, split="dev", ok=(m != "m2"), ts="2026-01-09T00:00:00+00:00")
                    if m == "m1":                                   # same outcomes, another model identity at the end
                        b["model"], a["model"] = "v1", "v2"
                    for r, side in ((b, "before"), (a, "after")):
                        r["pin"], r["canary_side"] = m, side
                        canary.append(r)
        res = A.analyse(recs, [], [], b=200, canary={"records": canary, "runs": []})
        rows = {r["model"]: r for r in res["drift"]["models"]}
        self.assertEqual(res["drift"]["flagged"], ["m1", "m2"])
        self.assertTrue(rows["m1"]["identity_changed"])
        self.assertEqual((rows["m1"]["down"], rows["m1"]["up"]), (0, 0))
        self.assertEqual((rows["m2"]["units"], rows["m2"]["down"]), (24, 24))
        self.assertLess(rows["m2"]["mcnemar_p"], 0.05)
        self.assertFalse(rows["m3"]["flagged"])
        self.assertEqual(res["sensitivity"]["without"], ["m1", "m2"])
        self.assertEqual({r["model"] for r in res["sensitivity"]["h1"]}, {"m3"})
        self.assertEqual(len(res["h1"]), 6)
        self.assertIn("## Sensitivity", A.render(res))
        self.assertIsNone(A.analyse(recs, [], [], b=200)["sensitivity"])

    def test_canary_folder_names(self):
        with tempfile.TemporaryDirectory() as tmp:
            d = write_run(tmp, "s2_before_m1_godot-s2", [trial("godot-s2", "d1", "none", "m1", split="dev")], "m1", "godot-s2")
            with self.assertRaises(ValueError):
                A.read_canary([d])
            d2 = write_run(tmp, "s2canary_after_m1_godot-s2", [trial("godot-s2", "d1", "none", "m1", split="dev")], "m1",
                           "godot-s2")
            self.assertEqual([r["canary_side"] for r in A.read_canary([d2])["records"]], ["after"])

    def test_summaries(self):
        self.assertEqual(A.summarise(["supported", "supported"]), "supported")
        self.assertEqual(A.summarise(["supported", "inconclusive"]), "inconclusive")
        self.assertEqual(A.summarise(["supported", "clearly against"]), "not supported")
        self.assertEqual(A.summarise([]), "no data")

    def test_h4_against(self):
        recs = [r for r in dataset(none_dev_ok=2) if r["condition"] != "graph[infer]"]
        for r in dataset(none_dev_ok=2):
            if r["condition"] == "graph[infer]":
                r["metrics"]["core_ok"] = False
                recs.append(r)
        res = A.analyse(recs, [], [], b=200)
        self.assertEqual(res["h4"]["summary"], "not supported")
        self.assertTrue(all(r["cell"] == "clearly against" for r in res["h4"]["rows"]))


class TestGrades(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.t = A.Tables()

    def test_prefixes(self):
        self.assertEqual(self.t.family["godot-s2"], ["p_", "r_"])
        self.assertEqual(self.t.family["dotnet-runtime-s2"], ["s_", "t_", "_"])
        self.assertEqual(self.t.required_prefix("godot-s2", "cpp", "output_parameter"), "r_")
        self.assertEqual(self.t.required_prefix("dotnet-runtime-s2", "csharp", "static_field"), "s_")
        fam = self.t.family["dotnet-runtime-s2"]
        self.assertEqual(A.prefix_class("_count", "_", fam), "right")
        self.assertEqual(A.prefix_class("s_count", "_", fam), "sibling")
        self.assertEqual(A.prefix_class("count", "_", fam), "none")
        self.assertEqual(A.prefix_class(None, "_", fam), "no name")
        self.assertEqual(A.prefix_class("_count", "s_", fam), "sibling")

    def test_scores(self):
        g = self.t.rules("godot-s2", "cpp", "input_parameter")
        self.assertTrue(A.score("p_size", "cpp", g))
        self.assertFalse(A.score("size", "cpp", g))
        self.assertFalse(A.score("p_Size", "cpp", g))
        self.assertFalse(A.score("not valid", "cpp", g))
        s1 = self.t.rules_s1("godot-s2", "cpp", "input_parameter")             # Study 1: parameter, snake_case
        self.assertTrue(A.score("size", "cpp", s1))
        self.assertFalse(A.score("pSize", "cpp", s1))
        self.assertIsNone(A.score("_count", "csharp", self.t.rules_s1("dotnet-runtime-s2", "csharp", "instance_field")))

    def test_reference_program(self):
        t = self.t
        self.assertEqual(A.reference_name("size", "cpp", "input_parameter", t, "godot-s2"), "p_size")
        self.assertEqual(A.reference_name("r_size", "cpp", "input_parameter", t, "godot-s2"), "p_size")
        self.assertEqual(A.reference_name("p_aabb", "cpp", "output_parameter", t, "godot-s2"), "r_aabb")
        self.assertEqual(A.reference_name("size", "cpp", "parameter", t, "godot-s2"), "size")
        self.assertEqual(A.reference_name("s_count", "csharp", "instance_field", t, "dotnet-runtime-s2"), "_count")
        self.assertEqual(A.reference_name("_cache", "csharp", "static_field", t, "dotnet-runtime-s2"), "s_cache")
        self.assertEqual(A.reference_name("maxValue", "csharp", "instance_field", t, "dotnet-runtime-s2"), "_maxValue")

    def test_lexer(self):
        cpp = ('void f(int p_a) { // p_comment\n /* p_block */ const char *s = "p_str \\" p_esc";\n'
               " char c = '\\''; int n = 1'000'000; auto r = R\"x(p_raw)x\"; g(p_b); }")
        self.assertEqual(A.prefixed_others(cpp, "cpp", "p_a", "p_"), ["p_b"])
        cs = ('class C { private int _a; string s = @"_v ""_q"" "; string t = """_raw"""; int n = 1_000;\n'
              ' char c = \'_\'; void M() { _ = _b; } }')
        self.assertEqual(A.prefixed_others(cs, "csharp", "_a", "_"), ["_b"])


class TestCli(_Tmp):
    def test_end_to_end_with_snippets(self):
        write_bench(self.tmp)
        unit_g = "cpp_001__p_position__" + G_RULE
        unit_d = "csharp_001___count__" + D_RULE
        runs = []
        for pin in ("m1", "m2"):
            g = [trial("godot-s2", unit_g, c, pin, ok=(c == "graph"), split="dev", name=None if c == "graph" else "position")
                 for c in ("none", "fulldoc", "naming", "chunk", "bm25", "graph")]
            d = [trial("dotnet-runtime-s2", unit_d, c, pin, ok=True, split="dev") for c in ("none", "graph")]
            runs.append(write_run(self.tmp, f"s2dev_{pin}_godot-s2_meta", g, pin, "godot-s2"))
            runs.append(write_run(self.tmp, f"s2dev_{pin}_dotnet-runtime-s2_meta", d, pin, "dotnet-runtime-s2"))
        canary = [write_run(self.tmp, f"s2canary_{side}_m1_godot-s2",
                            [trial("godot-s2", unit_g, "none", "m1", split="dev", ok=False, name="position")], "m1", "godot-s2")
                  for side in ("before", "after")]
        out = os.path.join(self.tmp, "a.md")
        r = subprocess.run([sys.executable, os.path.join(SIM, "analyse_study2.py"), *runs, "--compare-split", "dev",
                            "--bench", self.tmp, "--bootstrap", "100", "--out", out, "--json", out + ".json",
                            "--canary", *canary],
                           capture_output=True, text=True, cwd=SIM)
        self.assertEqual(r.returncode, 0, r.stderr)
        with open(out, encoding="utf-8") as f:
            md = f.read()
        self.assertIn("not a result of the study", md)
        self.assertIn("godot-s2: 0 of 1 tasks", md)
        self.assertNotIn("not computed", md)
        with open(out + ".json", encoding="utf-8") as f:
            res = json.load(f)
        g = [e for e in res["eligibility"] if e["pack"] == "godot-s2"][0]
        self.assertEqual((g["value"], g["eligible"]), (0.0, True))
        d = [e for e in res["eligibility"] if e["pack"] == "dotnet-runtime-s2"][0]
        self.assertEqual((d["value"], d["eligible"]), (1.0, False))
        self.assertEqual([(x["pack"], x["model"]) for x in res["h1"]], [("godot-s2", "m1"), ("godot-s2", "m2")])
        self.assertEqual([(m["model"], m["units"], m["flagged"]) for m in res["drift"]["models"]], [("m1", 1, False)])

    def test_missing_trials(self):
        r = subprocess.run([sys.executable, os.path.join(SIM, "analyse_study2.py"), os.path.join(self.tmp, "nope")],
                           capture_output=True, text=True, cwd=SIM)
        self.assertEqual(r.returncode, 2)


if __name__ == "__main__":
    unittest.main()
