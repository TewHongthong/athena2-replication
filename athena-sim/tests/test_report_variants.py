"""Runs that differ only in the ontology or the kind source must stay apart in the combined report."""
from __future__ import annotations

import json
import os
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from athena import report  # noqa: E402


def rec(unit, cond, ok, backend="mock:x"):
    return {"key": f"p|rename|{unit}|{cond}|{backend}|0", "pack": "p", "task": "rename", "unit_id": unit,
            "language": "cpp", "condition": cond, "backend": backend, "split": "dev", "error": None,
            "retrieval": {}, "metrics": {"parse_ok": True, "exact_match": ok, "violated_rule_ok": ok,
                                         "core_ok": ok, "collision": False, "prefix_match": None,
                                         "sim_char_before": 0.5, "sim_char_after": 0.6}}


def make_run(root, name, recs, ontology_variant="human", no_oracle=False, config=True):
    d = os.path.join(root, name)
    os.makedirs(d)
    with open(os.path.join(d, "trials.jsonl"), "w", encoding="utf-8") as f:
        f.write("\n".join(json.dumps(r) for r in recs))
    if config:
        with open(os.path.join(d, "config.json"), "w", encoding="utf-8") as f:
            json.dump({"run_id": name, "args": {"ontology_variant": ontology_variant, "no_oracle": no_oracle}}, f)
    return d


class TestRunVariant(unittest.TestCase):
    def test_labels(self):
        with tempfile.TemporaryDirectory() as t:
            self.assertEqual(report.run_variant(make_run(t, "a", [], "human", False)), "")
            self.assertEqual(report.run_variant(make_run(t, "b", [], "llm", False)), "llm")
            self.assertEqual(report.run_variant(make_run(t, "c", [], "human", True)), "infer")
            self.assertEqual(report.run_variant(make_run(t, "d", [], "llm", True)), "llm+infer")
            self.assertEqual(report.run_variant(make_run(t, "e", [], config=False)), "")
            self.assertEqual(report.run_variant(os.path.join(t, "missing")), "")


class TestLoadTrialsLabels(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        t = self.tmp.name
        units = [f"u{i}" for i in range(4)]
        self.dirs = [make_run(t, "meta", [rec(u, c, True) for u in units for c in ("none", "graph")]),
                     make_run(t, "llm", [rec(u, "graph", u != "u0") for u in units], "llm"),
                     make_run(t, "infer", [rec(u, "graph", u not in ("u0", "u1")) for u in units], "human", True)]

    def tearDown(self):
        self.tmp.cleanup()

    def test_default_behaviour_is_unchanged(self):
        recs, _ = report.load_trials(self.dirs)
        self.assertEqual(len(recs), 8)                                  # the graph rows of three runs collapse into one
        self.assertEqual({r["condition"] for r in recs}, {"none", "graph"})

    def test_labelled_runs_stay_apart(self):
        recs, _ = report.load_trials(self.dirs, label_variants=True)
        self.assertEqual(len(recs), 16)
        by = {}
        for r in recs:
            by.setdefault(r["condition"], []).append(r)
        self.assertEqual(sorted(by), ["graph", "graph[infer]", "graph[llm]", "none"])
        self.assertEqual(sum(r["metrics"]["core_ok"] for r in by["graph[llm]"]), 3)
        self.assertEqual(sum(r["metrics"]["core_ok"] for r in by["graph[infer]"]), 2)
        self.assertEqual(sum(r["metrics"]["core_ok"] for r in by["graph"]), 4)
        self.assertTrue(all(r["condition_base"] == "graph" for r in by["graph[llm]"]))
        self.assertEqual(len({r["key"] for r in recs}), 16)

    def test_retried_error_is_still_replaced_within_a_labelled_run(self):
        t = self.tmp.name
        bad = rec("u0", "graph", True)
        bad["error"] = "HTTP 502"
        d = make_run(t, "llm2", [bad, rec("u0", "graph", True)], "llm")
        recs, errors = report.load_trials([d], label_variants=True)
        self.assertEqual((len(recs), len(errors)), (1, 0))

    def test_cond_key_orders_labelled_conditions_after_their_base(self):
        conds = ["graph[llm]", "graph", "none", "graph[infer]", "bm25"]
        self.assertEqual(sorted(conds, key=report._cond_key), ["none", "bm25", "graph", "graph[infer]", "graph[llm]"])

    def test_summary_lists_each_graph_variant(self):
        out = os.path.join(self.tmp.name, "report")
        md = report.write_reports(self.dirs, out)
        for label in ("| graph |", "| graph[llm] |", "| graph[infer] |", "graph[llm] vs none", "graph[infer] vs none"):
            self.assertIn(label, md)
        with open(os.path.join(out, "trials.csv"), encoding="utf-8-sig") as f:
            head = f.readline()
        self.assertIn("condition_base", head)


if __name__ == "__main__":
    unittest.main()
