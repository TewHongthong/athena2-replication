"""Tests for the secondary analyses (H2, H4, H5, H6, H7, dose-response).  Run:  python -m unittest discover -s tests -v
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

import analyse_secondary  # noqa: E402
from athena import confirmatory as cf  # noqa: E402
from athena import secondary as sec  # noqa: E402

B = 300       # bootstrap resamples: enough for the synthetic cases and fast


def rec(pack, model, cond, split, unit, ok, repeat=0, file=None):
    return {"key": f"{pack}|{model}|{cond}|{split}|{unit}|{repeat}", "pack": pack, "task": "rename",
            "unit_id": unit, "snippet_id": unit, "split": split, "condition": cond, "backend": model,
            "repeat": repeat, "error": None, "metrics": {"core_ok": ok}, "file": file or f"{pack}/{unit}.py"}


def fill(recs, pack, model, cond, split, oks):
    for i, ok in enumerate(oks):
        recs.append(rec(pack, model, cond, split, f"u{i}", ok))


def index(recs):
    return cf.build_index(recs)


def first(n, k):
    return [1] * k + [0] * (n - k)


class TestStatistics(unittest.TestCase):
    def test_ranks_average_ties(self):
        self.assertEqual(sec.ranks([10, 20, 20, 30]), [1.0, 2.5, 2.5, 4.0])
        self.assertEqual(sec.ranks([0.1 + 0.2, 0.3]), [1.5, 1.5])      # equal after rounding

    def test_spearman_exact_perfect_negative(self):
        rho, p, method = sec.spearman_permutation([1, 2, 3, 4, 5], [9, 7, 5, 3, 1])
        self.assertAlmostEqual(rho, -1.0)
        self.assertAlmostEqual(p, 2 / 120)
        self.assertEqual(method, "exact")

    def test_spearman_monte_carlo_reproducible(self):
        x = list(range(10))
        y = [-v for v in x]
        a = sec.spearman_permutation(x, y, b=500, seed=1)
        b = sec.spearman_permutation(x, y, b=500, seed=1)
        self.assertEqual(a, b)
        self.assertEqual(a[2], "monte-carlo")
        self.assertLess(a[1], 0.01)

    def test_spearman_degenerate(self):
        self.assertEqual(sec.spearman_permutation([1, 2], [2, 1])[0], None)
        self.assertEqual(sec.spearman_permutation([1, 1, 1], [1, 2, 3])[2], "constant")

    def test_kappa(self):
        k = sec.cohen_kappa(["y", "y", "n", "n"], ["y", "n", "n", "n"])
        self.assertAlmostEqual(k["agreement"], 0.75)
        self.assertAlmostEqual(k["kappa"], 0.5)
        self.assertIsNone(sec.cohen_kappa(["a", "a"], ["a", "a"])["kappa"])
        self.assertAlmostEqual(sec.cohen_kappa(["a", "b", "a", "b"], ["a", "b", "a", "b"])["kappa"], 1.0)
        self.assertLess(sec.cohen_kappa(["a", "b", "a", "b"], ["b", "a", "b", "a"])["kappa"], 0)
        with self.assertRaises(ValueError):
            sec.cohen_kappa(["a"], ["a", "b"])

    def test_clopper_pearson_lower(self):
        self.assertAlmostEqual(sec.clopper_pearson_lower(20, 20), 0.05 ** (1 / 20), places=6)
        self.assertEqual(sec.clopper_pearson_lower(0, 10), 0.0)
        self.assertAlmostEqual(sec.clopper_pearson_lower(5, 10), 0.2224, places=3)

    def test_verdicts(self):
        self.assertEqual(sec.verdict_equivalence(-0.02, 0.03, 0.05), "within margin")
        self.assertEqual(sec.verdict_equivalence(0.06, 0.10, 0.05), "outside margin")
        self.assertEqual(sec.verdict_equivalence(-0.10, -0.06, 0.05), "outside margin")
        self.assertEqual(sec.verdict_equivalence(-0.08, 0.02, 0.05), "inconclusive")
        self.assertEqual(sec.verdict_noninferior(-0.04, 0.0, 0.05), "non-inferior")
        self.assertEqual(sec.verdict_noninferior(-0.20, -0.07, 0.05), "inferior")
        self.assertEqual(sec.verdict_noninferior(-0.10, 0.0, 0.05), "inconclusive")
        self.assertEqual(sec.verdict_superior(0.01, 0.1), "higher")
        self.assertEqual(sec.verdict_superior(-0.1, -0.01), "lower")
        self.assertEqual(sec.verdict_superior(-0.1, 0.1), "inconclusive")


class TestH2(unittest.TestCase):
    def make(self, effects):
        recs = []
        zero = [4, 8, 10, 12, 14, 16]
        for i, (k, e) in enumerate(zip(zero, effects)):
            pack, model = f"p{i // 2}", f"m{i % 2}"
            fill(recs, pack, model, "none", "test", first(20, k))
            fill(recs, pack, model, "graph", "test", first(20, k + e))
        return recs

    def test_negative_correlation_supported(self):
        res = sec.h2(index(self.make([8, 6, 5, 3, 2, 0]))[0], ["p0", "p1", "p2"])
        self.assertEqual(res["n_cells"], 6)
        self.assertAlmostEqual(res["rho"], -1.0)
        self.assertAlmostEqual(res["p"], 2 / 720)
        self.assertTrue(res["supports"])
        self.assertAlmostEqual(res["cells"][0]["zero_shot"], 0.2)
        self.assertAlmostEqual(res["cells"][0]["effect_pp"], 40.0)

    def test_positive_correlation_not_supported(self):
        res = sec.h2(index(self.make([0, 2, 3, 5, 6, 4]))[0], ["p0", "p1", "p2"])
        self.assertGreater(res["rho"], 0)
        self.assertFalse(res["supports"])

    def test_dev_split_and_other_packs_ignored(self):
        recs = self.make([8, 6, 5, 3, 2, 0])
        fill(recs, "p0", "m0", "none", "dev", [0] * 20)
        fill(recs, "other", "m0", "none", "test", [1] * 20)
        fill(recs, "other", "m0", "graph", "test", [1] * 20)
        res = sec.h2(index(recs)[0], ["p0", "p1", "p2"])
        self.assertEqual(res["n_cells"], 6)

    def test_too_few_cells(self):
        recs = []
        fill(recs, "p0", "m0", "none", "test", first(10, 5))
        fill(recs, "p0", "m0", "graph", "test", first(10, 8))
        res = sec.h2(index(recs)[0], ["p0"])
        self.assertIsNone(res["rho"])
        self.assertIsNone(res["supports"])
        self.assertIn("n=", sec.render_h2(res) + "n=")      # renders without a correlation


class TestContrast(unittest.TestCase):
    def test_labels_pair_cells_across_backends(self):
        a, b = [], []
        fill(a, "p", "assistant", "rules", "test", first(10, 9))
        fill(b, "p", "llm", "fulldoc", "test", first(10, 6))
        (ia, ca), (ib, cb) = index(a), index(b)
        rows = sec.contrast(ia, ib, sec.merge_clusters(ca, cb), ["p"], "rules", "fulldoc", "assistant", "llm", b=B)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["model"], "assistant vs llm")
        self.assertAlmostEqual(rows[0]["mean_diff_pp"], 30.0)
        self.assertEqual((rows[0]["up"], rows[0]["down"], rows[0]["tie"]), (3, 0, 7))

    def test_one_label_is_an_error(self):
        with self.assertRaises(ValueError):
            sec.contrast({}, {}, {}, ["p"], "x", "y", model_a="m")

    def test_no_common_units_gives_no_rows(self):
        a, b = [], []
        a.append(rec("p", "m", "graph", "test", "x1", 1))
        b.append(rec("p", "m", "graph", "test", "y1", 0))
        self.assertEqual(sec.contrast(index(a)[0], index(b)[0], {}, ["p"], "graph", "graph", b=B), [])


class TestH4H5(unittest.TestCase):
    def pair(self, n, human_ok, llm_ok):
        h, l = [], []
        fill(h, "p", "m", "graph", "test", first(n, human_ok))
        fill(l, "p", "m", "graph", "test", first(n, llm_ok))
        (ih, ch), (il, cl) = index(h), index(l)
        return ih, il, sec.merge_clusters(ch, cl)

    def test_h4_equal_ontologies_within_margin(self):
        ih, il, cl = self.pair(40, 30, 30)
        res = sec.h4(ih, il, cl, ["p"], b=B)
        self.assertEqual(res["compliance"][0]["verdict"], "within margin")
        self.assertAlmostEqual(res["compliance"][0]["mean_diff_pp"], 0.0)
        self.assertIsNone(res["kappa"])

    def test_h4_large_gap_outside_margin_with_sign(self):
        ih, il, cl = self.pair(40, 40, 20)             # LLM ontology 50 pp lower
        res = sec.h4(ih, il, cl, ["p"], b=B)
        row = res["compliance"][0]
        self.assertEqual(row["verdict"], "outside margin")
        self.assertAlmostEqual(row["mean_diff_pp"], -50.0)
        self.assertEqual((row["up"], row["down"]), (0, 20))

    def test_h4_kappa_threshold(self):
        ih, il, cl = self.pair(10, 5, 5)
        good = sec.h4(ih, il, cl, ["p"], kappa_pairs=[("a", "a"), ("b", "b"), ("a", "a"), ("b", "b")], b=B)
        self.assertTrue(good["kappa"]["meets"])
        bad = sec.h4(ih, il, cl, ["p"], kappa_pairs=[("a", "b"), ("b", "a"), ("a", "a"), ("b", "b")], b=B)
        self.assertFalse(bad["kappa"]["meets"])

    def test_h4_kappa_by_kind_from_agreement(self):
        ih, il, cl = self.pair(10, 5, 5)
        pool = {"n_items": 6, "observed_agreement": 5 / 6, "kappa": 0.7,
                "informative_items": {"n": 4, "observed_agreement": 0.5, "kappa": 0.4}}
        one = {"matched_units": [["l", "k"]], "human_only_units": [], "llm_only_units": [["l", "t"]], "n_items": 6,
               "observed_agreement": 5 / 6, "kappa": 0.7, "kappa_ci95_unit_bootstrap": [0.5, 0.9, 100]}
        res = sec.h4(ih, il, cl, ["p"], agreement={"p": one, "pooled": pool}, b=B)
        self.assertEqual(res["kappa"]["n"], 6)
        self.assertTrue(res["kappa"]["meets"])                       # pooled kappa 0.7 >= 0.6
        self.assertEqual(res["agreement"]["packs"]["p"]["llm_only"], 1)
        self.assertEqual(res["agreement"]["informative"]["kappa"], 0.4)
        md = sec.render_h4(res)
        self.assertIn("Kappa by identifier kind, pooled over the standards = 0.700", md)
        self.assertIn("met", md)
        self.assertIn("Secondary (items in which at least one ontology fixes a value; post hoc, no threshold): kappa = 0.400", md)
        below = dict(pool, kappa=0.5)
        self.assertFalse(sec.h4(ih, il, cl, ["p"], agreement={"p": one, "pooled": below}, b=B)["kappa"]["meets"])
        none = dict(pool, n_items=0, observed_agreement=None, kappa=None,
                    informative_items={"n": 0, "observed_agreement": None, "kappa": None})
        res0 = sec.h4(ih, il, cl, ["p"], agreement={"p": one, "pooled": none}, b=B)
        self.assertIsNone(res0["kappa"]["meets"])
        self.assertIn("undefined", sec.render_h4(res0))

    def test_h5_noninferior_and_inferior(self):
        ih, il, cl = self.pair(50, 40, 40)
        self.assertEqual(sec.h5(ih, il, cl, ["p"], b=B)["rows"][0]["verdict"], "non-inferior")
        ih, il, cl = self.pair(50, 50, 40)             # inferred kinds 20 pp lower
        row = sec.h5(ih, il, cl, ["p"], b=B)["rows"][0]
        self.assertEqual(row["verdict"], "inferior")
        self.assertAlmostEqual(row["mean_diff_pp"], -20.0)

    def test_margin_is_a_parameter(self):
        ih, il, cl = self.pair(50, 50, 40)             # inferred kinds 20 pp lower
        self.assertEqual(sec.h5(ih, il, cl, ["p"], margin=0.05, b=B)["rows"][0]["verdict"], "inferior")
        self.assertEqual(sec.h5(ih, il, cl, ["p"], margin=0.50, b=B)["rows"][0]["verdict"], "non-inferior")


class TestH6(unittest.TestCase):
    @staticmethod
    def labels(breaking, harmless_aware_only, harmless_blind_only, harmless_both, harmless_none, caught_aware=None):
        out = []
        for i in range(breaking):
            ca = True if caught_aware is None else i < caught_aware
            out.append({"breaks": True, "aware": ca, "blind": True})
        out += [{"breaks": False, "aware": True, "blind": False}] * harmless_aware_only
        out += [{"breaks": False, "aware": False, "blind": True}] * harmless_blind_only
        out += [{"breaks": False, "aware": True, "blind": True}] * harmless_both
        out += [{"breaks": False, "aware": False, "blind": False}] * harmless_none
        return out

    def test_supported(self):
        res = sec.h6(self.labels(10, 0, 18, 2, 10))
        self.assertEqual((res["n_breaking"], res["n_harmless"]), (10, 30))
        self.assertEqual(res["catch_rate_aware"], 1.0)
        self.assertEqual((res["false_alarms_aware"], res["false_alarms_blind"]), (2, 20))
        self.assertEqual((res["aware_only"], res["blind_only"]), (0, 18))
        self.assertAlmostEqual(res["p"], 2 / 2 ** 18)
        self.assertTrue(res["supports"])
        self.assertAlmostEqual(res["catch_rate_aware_lower"], 0.05 ** (1 / 10), places=6)

    def test_missed_breaking_rename_fails(self):
        res = sec.h6(self.labels(10, 0, 18, 2, 10, caught_aware=9))
        self.assertEqual(res["caught_aware"], 9)
        self.assertFalse(res["supports"])

    def test_no_fewer_false_alarms_fails(self):
        self.assertFalse(sec.h6(self.labels(5, 3, 3, 4, 10))["supports"])

    def test_no_breaking_renames(self):
        res = sec.h6(self.labels(0, 0, 5, 0, 5))
        self.assertIsNone(res["catch_rate_aware"])
        self.assertFalse(res["supports"])
        self.assertIn("No labelled", sec.render_h6(sec.h6([])))

    def test_csv_reader(self):
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "r.csv")
            with open(path, "w", encoding="utf-8") as f:
                f.write("breaks,aware,blind,note\n1,1,1,x\n0,false,TRUE,y\n0,0,0,\n")
            got = sec.read_h6_csv(path)
            self.assertEqual(got[1], {"breaks": False, "aware": False, "blind": True})
            bad = os.path.join(d, "b.csv")
            with open(bad, "w", encoding="utf-8") as f:
                f.write("breaks,aware\n1,1\n")
            with self.assertRaises(ValueError):
                sec.read_h6_csv(bad)
            odd = os.path.join(d, "o.csv")
            with open(odd, "w", encoding="utf-8") as f:
                f.write("breaks,aware,blind\n1,maybe,1\n")
            with self.assertRaises(ValueError):
                sec.read_h6_csv(odd)


class TestH7(unittest.TestCase):
    def setUp(self):
        a, r = [], []
        for pack in ("known", "unknown"):
            fill(a, pack, "assistant", "rules", "test", first(40, 30))
            fill(a, pack, "assistant", "norules", "test", first(40, 10))
            fill(r, pack, "llm", "fulldoc", "test", first(40, 30))
            fill(r, pack, "llm", "none", "test", first(40, 10))
            fill(r, pack, "llm", "graph", "test", first(40, 38))
        (self.ia, ca), (self.ir, cr) = index(a), index(r)
        self.cl = sec.merge_clusters(ca, cr)

    def run7(self, **kw):
        args = dict(asst_model="assistant", ref_model="llm", rules_cond="rules", norules_cond="norules",
                    margin=0.05, unknown_packs=["unknown"], b=B)
        args.update(kw)
        return sec.h7(self.ia, self.ir, self.cl, ["known", "unknown"], **args)

    def test_registered_pattern(self):
        res = self.run7()
        self.assertEqual({r["verdict"] for r in res["rules_vs_fulldoc"]}, {"within margin"})
        self.assertEqual({r["verdict"] for r in res["norules_vs_none"]}, {"within margin"})
        self.assertEqual([r["pack"] for r in res["selection_vs_rules"]], ["unknown"])
        self.assertEqual(res["selection_vs_rules"][0]["verdict"], "higher")
        self.assertEqual(res["selection_vs_norules"][0]["verdict"], "higher")
        self.assertIn("unknown", sec.render_h7(res))

    def test_margin_has_no_default(self):
        with self.assertRaises(ValueError):
            self.run7(margin=None)


def fill_dose(recs, pack, model, cond, split, k, chars, n=20, skip=()):
    """n units with k passes; the prompt of unit i has chars + i characters; `skip` units are left out."""
    for i in range(n):
        if i in skip:
            continue
        r = rec(pack, model, cond, split, f"u{i}", 1 if i < k else 0)
        r["prompt_chars"] = chars + i
        recs.append(r)


LADDER = [("none", 100), ("graph", 300), ("chunk", 500), ("bm25", 600), ("fulldoc", 5000)]


def ladder(ks, **kw):
    recs = []
    for (cond, chars), k in zip(LADDER, ks):
        fill_dose(recs, "p0", "m0", cond, "test", k, chars, **kw)
    return recs


class TestDose(unittest.TestCase):
    def curve(self, recs, **kw):
        idx, _ = index(recs)
        return sec.dose_curve(idx, sec.build_dose(recs), "p0", "m0", b=2000, **kw)

    def test_build_dose_keeps_the_graded_trials_with_a_prompt_size(self):
        recs = ladder([10, 10, 10, 10, 10], n=2)
        recs[0]["metrics"]["core_ok"] = None
        del recs[1]["prompt_chars"]
        d = sec.build_dose(recs)
        self.assertEqual(sum(len(v) for g in d.values() for v in g.values()), 8)

    def test_curve_is_ordered_by_size_and_has_the_effect_against_none(self):
        c = self.curve(ladder([10, 16, 14, 13, 12]))
        self.assertEqual([r["condition"] for r in c["rows"]], ["none", "graph", "chunk", "bm25", "fulldoc"])
        self.assertAlmostEqual(c["rows"][1]["effect_pp"], 30.0)
        self.assertAlmostEqual(c["rows"][1]["added_chars"], 200.0)
        self.assertAlmostEqual(c["rows"][0]["chars"], 100 + 9.5)       # mean of 100 + i over 20 units
        self.assertEqual(c["best"], "graph")
        self.assertEqual(c["largest"], "fulldoc")
        self.assertFalse(c["largest_is_best"])
        self.assertAlmostEqual(c["rho"], 0.0)
        self.assertEqual(c["method"], "exact")

    def test_more_context_always_better_gives_rho_one(self):
        c = self.curve(ladder([4, 8, 12, 16, 20]))
        self.assertAlmostEqual(c["rho"], 1.0)
        self.assertAlmostEqual(c["p"], 2 / 120)
        self.assertTrue(c["largest_is_best"])

    def test_tie_for_best_goes_to_the_smaller_context(self):
        c = self.curve(ladder([10, 16, 12, 12, 16]))
        self.assertEqual(c["best"], "graph")
        self.assertTrue(c["largest_is_best"])        # the largest context ties with the best

    def test_only_the_units_every_condition_has_are_used(self):
        recs = []
        for (cond, chars), k in zip(LADDER, [4, 8, 12, 16, 20]):
            fill_dose(recs, "p0", "m0", cond, "test", k, chars, skip=(0, 1) if cond == "fulldoc" else ())
        self.assertEqual(self.curve(recs)["units"], 18)

    def test_too_few_conditions_or_a_constant_size(self):
        recs = []
        fill_dose(recs, "p0", "m0", "none", "test", 5, 100)
        fill_dose(recs, "p0", "m0", "graph", "test", 9, 300)
        self.assertIsNone(self.curve(recs))
        recs = []
        for cond, k in (("none", 4), ("graph", 8), ("chunk", 12)):
            fill_dose(recs, "p0", "m0", cond, "test", k, 100)
        self.assertIsNone(self.curve(recs)["rho"])

    def test_the_split_is_respected(self):
        recs = ladder([4, 8, 12, 16, 20])
        for r in recs:
            r["split"] = "dev"
        idx, _ = index(recs)
        self.assertEqual(sec.dose_response(idx, sec.build_dose(recs), ["p0"])["cells"], [])

    def test_units_within_selection(self):
        recs = []
        for i in range(20):
            for cond, ok, chars in (("none", 0, 100), ("graph", 1 if i >= 10 else 0, 200 + 10 * i)):
                r = rec("p0", "m0", cond, "test", f"u{i}", ok)
                r["prompt_chars"] = chars
                recs.append(r)
        idx, _ = index(recs)
        rows = sec.dose_units(idx, sec.build_dose(recs), ["p0"], b=500)
        self.assertEqual(len(rows), 1)
        self.assertGreater(rows[0]["rho"], 0.8)
        self.assertLess(rows[0]["p"], 0.01)
        self.assertEqual(rows[0]["method"], "monte-carlo")
        self.assertEqual(rows[0]["units"], 20)
        self.assertAlmostEqual(rows[0]["median_added_chars"], 195.0)

    def test_response_summary_and_reproducible(self):
        recs = ladder([4, 8, 12, 16, 20])
        idx, _ = index(recs)
        dose = sec.build_dose(recs)
        a = sec.dose_response(idx, dose, ["p0"], b=300)
        b = sec.dose_response(idx, dose, ["p0"], b=300)
        self.assertEqual(sec.dumps(a), sec.dumps(b))
        self.assertEqual(a["summary"]["n_cells"], 1)
        self.assertEqual(a["summary"]["n_positive"], 1)
        self.assertEqual(a["summary"]["n_largest_best"], 1)

    def test_render(self):
        recs = ladder([10, 16, 14, 13, 12])
        idx, _ = index(recs)
        md = sec.render_dose(sec.dose_response(idx, sec.build_dose(recs), ["p0"], b=300))
        self.assertIn("Dose-response", md)
        self.assertIn("graph (0.800)", md)
        self.assertIn("do not show a causal effect", md)
        empty = sec.render_dose(sec.dose_response({}, {}, ["p0"]))
        self.assertIn("No cell with at least 3 conditions", empty)


class TestCli(unittest.TestCase):
    def write_run(self, d, name, recs):
        path = os.path.join(d, name)
        os.makedirs(path)
        with open(os.path.join(path, "trials.jsonl"), "w", encoding="utf-8") as f:
            for r in recs:
                f.write(json.dumps(r) + "\n")
        return path

    def call(self, argv):
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            code = analyse_secondary.main(argv)
        return code, out.getvalue(), err.getvalue()

    def test_h2_h4_h5_h6_and_h7_guard(self):
        with tempfile.TemporaryDirectory() as d:
            recs = []
            for i, (k, e) in enumerate(zip([4, 8, 10, 12, 14, 16], [8, 6, 5, 3, 2, 0])):
                fill(recs, f"p{i // 2}", f"m{i % 2}", "none", "test", first(20, k))
                fill(recs, f"p{i // 2}", f"m{i % 2}", "graph", "test", first(20, k + e))
            run = self.write_run(d, "run", recs)
            out_md, out_json = os.path.join(d, "o.md"), os.path.join(d, "o.json")
            code, out, _ = self.call(["h2", run, "--packs", "p0,p1,p2", "--out", out_md, "--json", out_json])
            self.assertEqual(code, 0)
            self.assertIn("Spearman rho = -1.000", out)
            self.assertTrue(os.path.exists(out_md))
            with open(out_json, encoding="utf-8") as fh:
                self.assertEqual(json.load(fh)["n_cells"], 6)

            h, l = [], []
            fill(h, "p0", "m0", "graph", "test", first(40, 30))
            fill(l, "p0", "m0", "graph", "test", first(40, 30))
            rh, rl = self.write_run(d, "human", h), self.write_run(d, "llm", l)
            kap = os.path.join(d, "k.csv")
            with open(kap, "w", encoding="utf-8") as f:
                f.write("attribute,human,llm\na1,x,x\na2,y,y\na3,x,x\na4,y,y\n")
            code, out, _ = self.call(["h4", "--human", rh, "--llm", rl, "--packs", "p0", "--kappa", kap,
                                      "--bootstrap", str(B)])
            self.assertEqual(code, 0)
            self.assertIn("within margin", out)
            self.assertIn("kappa = 1.000", out)
            onto = {"nodes": [{"id": "cpp", "type": "Language"}, {"id": "method", "type": "IdentifierKind"},
                              {"id": "R", "type": "NamingRule", "casing": "snake_case", "prefix": None, "suffix": None,
                               "minLength": None, "maxLength": None, "forbiddenPatterns": [], "severity": "MUST"}],
                    "links": [{"source": "R", "target": "cpp", "relation": "APPLIES_TO"},
                              {"source": "R", "target": "method", "relation": "APPLIES_TO"}]}
            os.makedirs(os.path.join(d, "ont", "p0", "llm"))
            for rel in ("p0/p0_ontology.json", "p0/llm/llm_ontology.json"):
                with open(os.path.join(d, "ont", rel), "w", encoding="utf-8") as f:
                    json.dump(onto, f)
            code, out, _ = self.call(["h4", "--human", rh, "--llm", rl, "--packs", "p0", "--agreement-root",
                                      os.path.join(d, "ont"), "--bootstrap", str(B)])
            self.assertEqual(code, 0)
            self.assertIn("Kappa by identifier kind", out)
            self.assertIn("agreement 1.000", out)
            code, _, err = self.call(["h4", "--human", rh, "--llm", rl, "--packs", "p0", "--kappa", kap,
                                      "--agreement-root", os.path.join(d, "ont")])
            self.assertEqual(code, 2)
            code, _, err = self.call(["h4", "--human", rh, "--llm", rl, "--packs", "nope", "--agreement-root",
                                      os.path.join(d, "ont")])
            self.assertEqual(code, 2)
            code, out, _ = self.call(["h5", "--metadata", rh, "--inferred", rl, "--packs", "p0", "--bootstrap", str(B)])
            self.assertEqual(code, 0)
            self.assertIn("non-inferior", out)

            lab = os.path.join(d, "lab.csv")
            with open(lab, "w", encoding="utf-8") as f:
                f.write("breaks,aware,blind\n1,1,1\n0,0,1\n0,0,1\n0,0,1\n0,0,1\n0,0,1\n0,0,1\n0,0,0\n")
            code, out, _ = self.call(["h6", "--labels", lab])
            self.assertEqual(code, 0)
            self.assertIn("Supports H6", out)

            code, _, err = self.call(["h7", "--assistant", rh, "--ref", rl, "--assistant-label", "a", "--ref-label", "b",
                                      "--rules-cond", "r", "--norules-cond", "n"])
            self.assertEqual(code, 2)
            self.assertIn("margin", err)

    def test_dose(self):
        with tempfile.TemporaryDirectory() as d:
            run = self.write_run(d, "run", ladder([4, 8, 12, 16, 20]))
            out_json = os.path.join(d, "o.json")
            code, out, _ = self.call(["dose", run, "--packs", "p0", "--permutations", "200", "--json", out_json])
            self.assertEqual(code, 0)
            self.assertIn("# Dose-response", out)
            self.assertIn("+1.000", out)
            with open(out_json, encoding="utf-8") as fh:
                res = json.load(fh)
            self.assertEqual(res["summary"]["n_cells"], 1)
            self.assertEqual(res["n_trials"], [100])

    def test_missing_trials(self):
        with tempfile.TemporaryDirectory() as d:
            code, _, err = self.call(["h2", os.path.join(d, "nothing")])
            self.assertEqual(code, 2)
            self.assertIn("no trials.jsonl", err)


if __name__ == "__main__":
    unittest.main()
