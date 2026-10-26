"""Tests for the confirmatory analysis (H1 family, eligibility, H3).  Run:  python -m unittest discover -s tests -v
(from the athena-sim folder).  Synthetic trials only: no API key, no network, no corpus.
"""
from __future__ import annotations

import io
import json
import math
import os
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

import analyse_confirmatory  # noqa: E402
from athena import confirmatory as cf  # noqa: E402
from athena.report import holm, sign_test_p  # noqa: E402


def rec(pack, model, cond, split, unit, ok, snippet=None, repeat=0, error=None, file=None):
    r = {"key": f"{pack}|{model}|{cond}|{split}|{unit}|{repeat}", "pack": pack, "task": "rename",
            "unit_id": unit, "snippet_id": snippet or unit, "split": split, "condition": cond, "backend": model,
            "repeat": repeat, "error": error, "metrics": {"core_ok": ok}}
    if file is not None:
        r["file"] = file
    return r


def fill(recs, pack, model, cond, split, oks, prefix="u", snippets=None, files=None):
    for i, ok in enumerate(oks):
        recs.append(rec(pack, model, cond, split, f"{prefix}{i}", ok, snippets[i] if snippets else None,
                        file=files[i] if files else None))


class TestEligibility(unittest.TestCase):
    def test_mean_over_models_and_threshold(self):
        recs = []
        fill(recs, "p1", "m1", "none", "dev", [1] * 17 + [0] * 3)      # 0.85
        fill(recs, "p1", "m2", "none", "dev", [1] * 19 + [0] * 1)      # 0.95  -> mean 0.90, not below 0.90
        fill(recs, "p2", "m1", "none", "dev", [1] * 10 + [0] * 10)     # 0.5
        fill(recs, "p2", "m1", "none", "test", [1] * 20)               # test is not used
        idx, _ = cf.build_index(recs)
        e = {x["pack"]: x for x in cf.eligibility(idx, ["p1", "p2", "p3"])}
        self.assertAlmostEqual(e["p1"]["value"], 0.90)
        self.assertFalse(e["p1"]["eligible"])                          # strictly below 0.90 is required
        self.assertAlmostEqual(e["p2"]["value"], 0.5)
        self.assertTrue(e["p2"]["eligible"])
        self.assertIsNone(e["p3"]["eligible"])
        self.assertEqual(e["p1"]["n_models"], 2)

    def test_only_none_condition_counts(self):
        recs = []
        fill(recs, "p1", "m1", "none", "dev", [0] * 10)
        fill(recs, "p1", "m1", "graph", "dev", [1] * 10)
        idx, _ = cf.build_index(recs)
        self.assertAlmostEqual(cf.eligibility(idx, ["p1"])[0]["value"], 0.0)


class TestH1(unittest.TestCase):
    def setUp(self):
        self.recs = []
        for model in ("m1", "m2"):
            fill(self.recs, "p1", model, "none", "dev", [1] * 10 + [0] * 10)           # eligible
            fill(self.recs, "p2", model, "none", "dev", [1] * 19 + [0])                # 0.95: not eligible
            # test: selection better on 20 of 30 units, tied on 10
            fill(self.recs, "p1", model, "none", "test", [0] * 20 + [1] * 10)
            fill(self.recs, "p1", model, "graph", "test", [1] * 20 + [1] * 10)
            fill(self.recs, "p2", model, "none", "test", [0] * 20 + [1] * 10)
            fill(self.recs, "p2", model, "graph", "test", [1] * 30)
            # other conditions must not enter the H1 family
            fill(self.recs, "p1", model, "fulldoc", "test", [1] * 30)
            fill(self.recs, "p1", model, "bm25", "test", [1] * 30)

    def test_family_is_eligible_packs_times_models(self):
        res = cf.analyse(self.recs, packs=("p1", "p2"))
        self.assertEqual([(r["pack"], r["model"]) for r in res["h1"]], [("p1", "m1"), ("p1", "m2")])
        r = res["h1"][0]
        self.assertEqual((r["units"], r["up"], r["down"], r["tie"]), (30, 20, 0, 10))
        self.assertAlmostEqual(r["p"], 2 * 0.5 ** 20)
        self.assertAlmostEqual(r["p_holm"], min(1.0, 2 * 2 * 0.5 ** 20))      # Holm with m = 2, not with all tables
        self.assertTrue(r["supports"])
        self.assertAlmostEqual(r["mean_diff_pp"], 100 * 20 / 30)

    def test_ineligible_pack_reported_but_not_tested(self):
        res = cf.analyse(self.recs, packs=("p1", "p2"))
        self.assertEqual({e["pack"]: e["eligible"] for e in res["eligibility"]}, {"p1": True, "p2": False})
        self.assertNotIn("p2", {r["pack"] for r in res["h1"]})

    def test_repeats_are_averaged_per_unit(self):
        recs = []
        for rep, v in enumerate([1, 0, 1]):
            recs.append(rec("p1", "m1", "graph", "test", "u0", v, repeat=rep))
        for rep in range(3):
            recs.append(rec("p1", "m1", "none", "test", "u0", 0, repeat=rep))
        idx, _ = cf.build_index(recs)
        units, deltas, up, dn, tie = cf.paired(idx[("test", "p1", "m1", "graph")], idx[("test", "p1", "m1", "none")])
        self.assertEqual(units, ["u0"])
        self.assertAlmostEqual(deltas[0], 2 / 3)
        self.assertEqual((up, dn, tie), (1, 0, 0))

    def test_unpaired_units_are_dropped(self):
        recs = []
        fill(recs, "p1", "m1", "graph", "test", [1] * 5)
        fill(recs, "p1", "m1", "none", "test", [0] * 3)
        idx, _ = cf.build_index(recs)
        units, *_ = cf.paired(idx[("test", "p1", "m1", "graph")], idx[("test", "p1", "m1", "none")])
        self.assertEqual(len(units), 3)

    def test_error_trials_are_ignored_by_the_loader(self):
        d = tempfile.mkdtemp()
        rows = [rec("p1", "m1", "none", "dev", "u0", 0), rec("p1", "m1", "none", "dev", "u1", None, error="boom")]
        with open(os.path.join(d, "trials.jsonl"), "w", encoding="utf-8") as f:
            f.write("\n".join(json.dumps(r) for r in rows))
        res, _md = cf.run([d], packs=("p1",))
        self.assertEqual(res["n_trials"], 1)
        self.assertEqual(res["n_error_keys"], 1)


class TestH3(unittest.TestCase):
    def cell(self, sel_oks, full_oks, snippets=None):
        recs = []
        fill(recs, "p1", "m1", "graph", "test", sel_oks, snippets=snippets)
        fill(recs, "p1", "m1", "fulldoc", "test", full_oks, snippets=snippets)
        return recs

    def run_ni(self, recs):
        idx, clusters = cf.build_index(recs)
        return cf.h3_noninferiority(idx, clusters, ["p1"], b=2000)[0]

    def test_identical_is_noninferior(self):
        r = self.run_ni(self.cell([1, 0] * 35, [1, 0] * 35))
        self.assertEqual(r["verdict"], "non-inferior")
        self.assertAlmostEqual(r["ci_low_pp"], 0.0)
        self.assertAlmostEqual(r["ci_high_pp"], 0.0)

    def test_clearly_worse_is_inferior(self):
        r = self.run_ni(self.cell([0] * 20 + [1] * 80, [1] * 100))
        self.assertEqual(r["verdict"], "inferior")
        self.assertAlmostEqual(r["mean_diff_pp"], -20.0)
        self.assertLess(r["ci_high_pp"], -2.0)

    def test_noisy_small_difference_is_inconclusive(self):
        sel = [1] * 5 + [0] * 5 + [1] * 60
        full = [0] * 5 + [1] * 5 + [1] * 60
        r = self.run_ni(self.cell(sel, full))
        self.assertEqual(r["verdict"], "inconclusive")
        self.assertAlmostEqual(r["mean_diff_pp"], 0.0)
        self.assertLess(r["ci_low_pp"], -2.0)
        self.assertGreater(r["ci_high_pp"], -2.0)

    def test_boundary_uses_lower_limit(self):
        # a small consistent shortfall of 1 pp with a tight interval is non-inferior at a 2 pp margin
        sel = [1] * 99 + [0]
        full = [1] * 100
        idx, clusters = cf.build_index(self.cell(sel, full))
        units, deltas, *_ = cf.paired(idx[("test", "p1", "m1", "graph")], idx[("test", "p1", "m1", "fulldoc")])
        lo, hi = cf.cluster_bootstrap_ci(units, deltas, clusters, "p1", 2000)
        self.assertLessEqual(lo, -0.01 + 1e-9)
        self.assertGreaterEqual(hi, -0.01 - 1e-9)

    def test_clusters_widen_the_interval(self):
        # 60 units; the first 30 differ (-1) and the last 30 do not.  As 60 clusters the interval is narrower than
        # when units come in 6 clusters of 10 (units of one cluster move together).
        sel = [0] * 30 + [1] * 30
        full = [1] * 60
        snippets_one = None
        snippets_six = [f"s{i // 10}" for i in range(60)]
        # make the shortfall cluster-aligned: clusters 0-2 all differ
        r1 = self.run_ni(self.cell(sel, full, snippets_one))
        r6 = self.run_ni(self.cell(sel, full, snippets_six))
        self.assertEqual(r1["clusters"], 60)
        self.assertEqual(r6["clusters"], 6)
        self.assertGreater(r6["ci_high_pp"] - r6["ci_low_pp"], r1["ci_high_pp"] - r1["ci_low_pp"])

    def test_file_is_the_default_cluster_and_beats_the_snippet(self):
        # every task has its own snippet id, but 10 tasks share each file: the file defines the clusters
        sel = [0] * 30 + [1] * 30
        full = [1] * 60
        files = [f"repo:f{i // 10}.cpp" for i in range(60)]
        recs = []
        fill(recs, "p1", "m1", "graph", "test", sel, files=files)
        fill(recs, "p1", "m1", "fulldoc", "test", full, files=files)
        r = self.run_ni(recs)
        self.assertEqual(r["clusters"], 6)
        by_snippet = self.run_ni(self.cell(sel, full))
        self.assertGreater(r["ci_high_pp"] - r["ci_low_pp"], by_snippet["ci_high_pp"] - by_snippet["ci_low_pp"])

    def test_missing_file_falls_back_to_snippet_then_unit_and_is_counted(self):
        recs = []
        recs.append(rec("p1", "m1", "graph", "test", "a", 1, snippet="s1", file="r:f"))
        recs.append(rec("p1", "m1", "graph", "test", "b", 1, snippet="s2"))
        recs.append(rec("p1", "m1", "graph", "test", "c", 1))
        recs[-1]["snippet_id"] = ""
        self.assertEqual(cf.cluster_sources(recs), {"field": 1, "snippet_id": 1, "unit": 1})
        _, clusters = cf.build_index(recs)
        self.assertEqual([clusters[("p1", u)] for u in "abc"], ["r:f", "s2", "c"])

    def test_bootstrap_is_reproducible(self):
        recs = self.cell([1, 0, 1] * 20, [1, 1, 0] * 20)
        self.assertEqual(self.run_ni(recs), self.run_ni(recs))

    def test_retrieval_family_and_direction(self):
        recs = []
        fill(recs, "p1", "m1", "graph", "test", [1] * 30)
        fill(recs, "p1", "m1", "chunk", "test", [0] * 20 + [1] * 10)
        fill(recs, "p1", "m1", "bm25", "test", [1] * 30)
        fill(recs, "p1", "m1", "dense", "test", [1] * 10 + [0] * 20)
        idx, _ = cf.build_index(recs)
        rows = cf.h3_retrieval(idx, ["p1"])
        self.assertEqual([r["baseline"] for r in rows], ["chunk", "bm25", "dense"])
        by = {r["baseline"]: r for r in rows}
        self.assertTrue(by["chunk"]["higher"])
        self.assertFalse(by["bm25"]["higher"])                  # tied everywhere: p = 1
        self.assertEqual(by["bm25"]["p"], 1.0)
        want = holm([r["p"] for r in rows])
        self.assertEqual([r["p_holm"] for r in rows], want)
        self.assertAlmostEqual(by["chunk"]["p"], sign_test_p(20, 0))


class TestSourceFile(unittest.TestCase):
    def test_source_file_comes_from_the_provenance(self):
        from athena.packs import _source_file
        self.assertEqual(_source_file({"provenance": {"repo": "o/r", "path": "src/a.cpp"}}), "o/r:src/a.cpp")
        self.assertEqual(_source_file({"provenance": {"repo": "o/r"}}), "")
        self.assertEqual(_source_file({}), "")


class TestCliAndRender(unittest.TestCase):
    def test_cli_writes_report_and_json(self):
        d = tempfile.mkdtemp()
        recs = []
        for model in ("m1", "m2"):
            fill(recs, "godot", model, "none", "dev", [1] * 10 + [0] * 10)
            fill(recs, "godot", model, "none", "test", [0] * 30)
            fill(recs, "godot", model, "graph", "test", [1] * 30)
            fill(recs, "godot", model, "fulldoc", "test", [1] * 30)
        with open(os.path.join(d, "trials.jsonl"), "w", encoding="utf-8") as f:
            f.write("\n".join(json.dumps(r) for r in recs))
        out_md, out_js = os.path.join(d, "a.md"), os.path.join(d, "a.json")
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            rc = analyse_confirmatory.main([d, "--out", out_md, "--json", out_js, "--bootstrap", "500"])
        self.assertEqual(rc, 0)
        with open(out_md, encoding="utf-8") as f:
            md = f.read()
        self.assertIn("supports H1", md)
        self.assertIn("non-inferior", md)
        self.assertIn("dotnet-runtime", md)                      # absent pack is listed as having no dev data
        self.assertIn("no dev data", md)
        with open(out_js, encoding="utf-8") as f:
            js = json.load(f)
        self.assertEqual(len(js["h1"]), 2)
        self.assertTrue(all(r["supports"] for r in js["h1"]))

    def test_no_eligible_standard_reports_h1_not_testable(self):
        recs = []
        for pack in ("godot", "odoo"):
            for model in ("m1", "m2"):
                fill(recs, pack, model, "none", "dev", [1] * 19 + [0])
                fill(recs, pack, model, "none", "test", [1] * 20)
                fill(recs, pack, model, "graph", "test", [1] * 20)
                fill(recs, pack, model, "fulldoc", "test", [1] * 20)
        res = cf.analyse(recs, packs=("godot", "odoo"), b=200)
        self.assertEqual(res["h1_status"], "not_testable")
        self.assertEqual(res["h1"], [])
        self.assertTrue(res["h3_noninferiority"])
        md = cf.render(res)
        self.assertIn("H1 is not testable", md)
        self.assertNotIn("supports H1 =", md)

    def test_h1_status_other_cases(self):
        recs = []
        fill(recs, "godot", "m1", "none", "dev", [0] * 10)
        res = cf.analyse(recs, packs=("godot",), b=200)
        self.assertEqual(res["h1_status"], "no_test_data")
        self.assertIn("no paired test units", cf.render(res))
        res = cf.analyse([], packs=("godot",), b=200)
        self.assertEqual(res["h1_status"], "no_dev_data")
        fill(recs, "godot", "m1", "none", "test", [0] * 10)
        fill(recs, "godot", "m1", "graph", "test", [1] * 10)
        self.assertEqual(cf.analyse(recs, packs=("godot",), b=200)["h1_status"], "testable")

    def test_models_filter_limits_eligibility_and_rejects_unknown(self):
        recs = []
        fill(recs, "godot", "openai:a/model-x", "none", "dev", [0] * 10)
        fill(recs, "godot", "openai:b/model-y", "none", "dev", [1] * 10)
        fill(recs, "godot", "openai:c/Other", "none", "dev", [1] * 10)
        e = cf.analyse(recs, packs=("godot",), b=200)["eligibility"][0]
        self.assertAlmostEqual(e["value"], 2 / 3)
        res = cf.analyse(recs, packs=("godot",), b=200, models=["MODEL-x", "model-y"])
        self.assertAlmostEqual(res["eligibility"][0]["value"], 0.5)
        self.assertEqual(res["settings"]["models"], ["openai:a/model-x", "openai:b/model-y"])
        self.assertIn("Models: openai:a/model-x", cf.render(res))
        with self.assertRaises(ValueError):
            cf.analyse(recs, packs=("godot",), b=200, models=["nothing"])

    def test_cli_models_option(self):
        d = tempfile.mkdtemp()
        recs = []
        fill(recs, "godot", "m1", "none", "dev", [1] * 10)
        fill(recs, "godot", "m2", "none", "dev", [0] * 10)
        with open(os.path.join(d, "trials.jsonl"), "w", encoding="utf-8") as f:
            f.write("\n".join(json.dumps(r) for r in recs))
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            self.assertEqual(analyse_confirmatory.main([d, "--models", "m2", "--bootstrap", "200"]), 0)
            self.assertEqual(analyse_confirmatory.main([d, "--models", "zzz", "--bootstrap", "200"]), 2)
        self.assertIn("| godot | 0.000 | 1 | yes |", out.getvalue())
        self.assertIn("no model matches", err.getvalue())

    def test_cli_rejects_missing_trials(self):
        err = io.StringIO()
        with redirect_stderr(err):
            rc = analyse_confirmatory.main([tempfile.mkdtemp()])
        self.assertEqual(rc, 2)


if __name__ == "__main__":
    unittest.main()
