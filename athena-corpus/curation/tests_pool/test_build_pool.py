#!/usr/bin/env python3
"""Tests of tools/build_pool.py and tools/export_tasks.py on a tiny C++ corpus with the mock ontology of tests_core.

  python3 -m unittest tests_pool/test_build_pool.py      (from the curation folder)

The ontology and the core table are the TESTONLY-* ones of tests_core: they exercise the code and are not a standard.
"""
import collections
import copy
import csv
import json
import os
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
CUR = os.path.dirname(HERE)
sys.path.insert(0, CUR)
sys.path.insert(0, os.path.join(CUR, "tools"))
sys.path.insert(0, os.path.join(CUR, "tests_core"))

import build_pool as bp  # noqa: E402
import core_table  # noqa: E402
import curate as C  # noqa: E402
import export_tasks as ex  # noqa: E402
import rules as R  # noqa: E402
import select_tasks as st  # noqa: E402
import test_core_table as tc  # noqa: E402
from tsbind import TreeSitter, find_library  # noqa: E402

PACK = "testpack"


def corpus_md(content, path):
    return ("# test\n\n- source repo: acme/demo\n- repo url: https://example.invalid/acme/demo\n"
            "- file path: %s\n- commit: 0123456789abcdef0123456789abcdef01234567\n"
            "- license: MIT\n- created_at: 2026-07-01\n\n```cpp\n%s```\n" % (path, content))


class Base(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        t = cls.tmp.name
        cls.onto_path = os.path.join(t, "onto.json")
        with open(cls.onto_path, "w", encoding="utf-8") as f:
            json.dump(tc.mock_ontology_dict(), f)
        cls.core_path = os.path.join(t, "core_rules.json")
        with open(cls.core_path, "w", encoding="utf-8") as f:
            json.dump(tc.mock_core_dict(), f)
        cls.corpus = os.path.join(t, "corpus_root")
        os.makedirs(os.path.join(cls.corpus, "corpus", "cpp"))
        cls.write_md("a__counter.cpp.md", "src/counter.cpp", tc.CPP_SOURCE)
        cls.ts = TreeSitter(find_library(None))

    @classmethod
    def write_md(cls, name, path, content):
        with open(os.path.join(cls.corpus, "corpus", "cpp", name), "w", encoding="utf-8", newline="\n") as f:
            f.write(corpus_md(content, path))

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def onto(self):
        o = R.Ontology(self.onto_path)
        self.assertEqual(core_table.apply(self.core_path, o), [])
        return o

    def build(self, **kw):
        return bp.build(PACK, "cpp", self.corpus, self.onto(), self.ts, **kw)


class PoolTests(Base):
    def test_pool_has_one_verified_violation_per_unit(self):
        recs, stats = self.build()
        self.assertTrue(recs)
        for r in recs:
            v = r["violation"]
            self.assertNotEqual(v["injected"], r["target"]["name"])
            self.assertIn(r["target"]["name"], r["code"])
            self.assertNotIn(v["injected"], r["code"])
            self.assertIn(v["injected"], v["code"])
            self.assertNotIn(r["target"]["name"], v["code"].replace(v["injected"], ""))
            self.assertNotIn("violations", r)               # one violation, not a list
        self.assertEqual(stats["rename_verify"]["scope_binding_conflict"], 0)

    def test_deterministic(self):
        a, _ = self.build()
        b, _ = self.build()
        self.assertEqual(json.dumps(a, sort_keys=True), json.dumps(b, sort_keys=True))

    def test_target_order_depends_on_pack_path_and_unit_only(self):
        r1 = bp.target_rng("p", "a.cpp", 3).random()
        self.assertEqual(r1, bp.target_rng("p", "a.cpp", 3).random())
        self.assertNotEqual(r1, bp.target_rng("q", "a.cpp", 3).random())
        self.assertNotEqual(r1, bp.target_rng("p", "b.cpp", 3).random())
        self.assertNotEqual(r1, bp.target_rng("p", "a.cpp", 4).random())

    def test_targets_are_a_subset_of_vol1_eligible_targets(self):
        onto = self.onto()
        meta, content = C.parse_corpus_md(os.path.join(self.corpus, "corpus", "cpp", "a__counter.cpp.md"))
        ff = C.analyze("cpp", meta["file path"], content, self.ts)
        checked = 0
        for k, u in enumerate(ff.units):
            vstats = {"units": collections.Counter(), "unit_gate_failures_by_rule": collections.Counter(),
                      "target_rejects": collections.Counter(), "rename_verify": collections.Counter()}
            ev = C.evaluate_unit("cpp", ff, u, onto, meta, vstats)
            pstats = bp.new_stats()
            u_start, u_end = C.unit_range(ff, u)
            decls = [d for d in ff.decls if u_start <= d.start < u_end]
            toks = [t for t in ff.toks if u_start <= t.start < u_end]
            mine = {d.name for d, _, _ in bp.eligible_targets("cpp", ff, decls, toks, u_start, u_end, pstats)}
            if ev is not None:
                checked += 1
                vol1 = {t["decl"].name for t in ev["targets"]}
                self.assertTrue(vol1 <= mine, (vol1, mine))
        self.assertGreater(checked, 0)

    def test_scope_conflict_rejects_the_target(self):
        old = bp.SCOPE_CHECK
        try:
            bp.SCOPE_CHECK = lambda lang, code, a, b: {"status": "ok", "binding_conflict": True,
                                                      "declaration_conflict": False}
            recs, stats = self.build()
        finally:
            bp.SCOPE_CHECK = old
        self.assertEqual(recs, [])
        self.assertGreater(stats["rename_verify"]["scope_binding_conflict"], 0)
        self.assertGreater(stats["units"]["no_target_with_violation"], 0)

    def test_declaration_conflict_and_unsupported_reject(self):
        old = bp.SCOPE_CHECK
        try:
            bp.SCOPE_CHECK = lambda lang, code, a, b: {"status": "ok", "binding_conflict": False,
                                                      "declaration_conflict": True}
            recs, stats = self.build()
            self.assertEqual(recs, [])
            self.assertGreater(stats["rename_verify"]["scope_declaration_conflict"], 0)
            bp.SCOPE_CHECK = lambda lang, code, a, b: {"status": "unsupported"}
            recs, stats = self.build()
            self.assertEqual(recs, [])
            self.assertGreater(stats["scope_status"]["unsupported"], 0)
        finally:
            bp.SCOPE_CHECK = old

    def test_next_target_is_tried_when_the_first_fails(self):
        # reject the first renamed identifier asked about, accept the rest: the unit must still enter the pool
        old = bp.SCOPE_CHECK
        seen = []

        def fake(lang, code, a, b):
            seen.append(a)
            bad = (a == seen[0])
            return {"status": "ok", "binding_conflict": bad, "declaration_conflict": False}
        try:
            bp.SCOPE_CHECK = fake
            recs, _ = self.build()
        finally:
            bp.SCOPE_CHECK = old
        self.assertTrue(recs)
        self.assertGreater(len(seen), 1)             # more than one target was asked about

    def test_duplicate_code_is_dropped(self):
        self.write_md("b__counter_copy.cpp.md", "src/other/counter_copy.cpp", tc.CPP_SOURCE)
        try:
            recs, stats = self.build()
            self.assertGreater(stats["units"]["duplicate_code_dropped"], 0)
            codes = [" ".join(r["code"].split()) for r in recs]
            self.assertEqual(len(codes), len(set(codes)))
        finally:
            os.remove(os.path.join(self.corpus, "corpus", "cpp", "b__counter_copy.cpp.md"))

    def test_a_noncompliant_identifier_fails_the_gate(self):
        src = tc.CPP_SOURCE.replace("sum_value", "sumValue")
        self.write_md("c__bad.cpp.md", "src/bad.cpp", src)
        try:
            recs, stats = self.build()
            self.assertGreater(stats["units"]["noncompliant_identifier"], 0)
            for r in recs:
                if r["path"] == "src/bad.cpp":
                    self.assertNotIn("sumValue", r["code"])
        finally:
            os.remove(os.path.join(self.corpus, "corpus", "cpp", "c__bad.cpp.md"))

    def test_outputs_feed_select_tasks(self):
        recs, stats = self.build()
        out = os.path.join(self.tmp.name, "pool_out")
        pool, units, sp = bp.write_outputs(out, PACK, recs, stats)
        extra, loaded = st.load_pool(pool)
        self.assertEqual(len(loaded), len(recs))
        self.assertEqual(extra, bp.POOL_COLUMNS[2:])
        s = json.load(open(sp, encoding="utf-8"))
        self.assertEqual(s["pool"]["units"], len(recs))


def variant(src, k):
    """The tiny source with every identifier made unique, so the units are not duplicates of each other."""
    import re
    for name in ("Counter", "total_count", "last_amount", "add_amount", "amount_value", "new_total", "get_total",
                 "current_total", "adjusted_total", "compute_sum", "first_value", "second_value", "sum_value",
                 "double_value", "result_value"):
        new = name + ("%s" % chr(ord("A") + k) if name == "Counter" else "_v%d" % k)
        src = re.sub(r"\b%s\b" % name, new, src)
    return src


class ExportTests(Base):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.corpus2 = os.path.join(cls.tmp.name, "corpus_many")
        os.makedirs(os.path.join(cls.corpus2, "corpus", "cpp"))
        want = {"dev": 3, "test": 5}
        k = 0
        for side, n in want.items():
            made, j = 0, 0
            while made < n:
                path = "src/%s/f%d.cpp" % (side, j)
                j += 1
                if st.side_of(path) != side:
                    continue
                fn = "m%02d.cpp.md" % k
                with open(os.path.join(cls.corpus2, "corpus", "cpp", fn), "w", encoding="utf-8", newline="\n") as f:
                    f.write(corpus_md(variant(tc.CPP_SOURCE, k), path))
                k += 1
                made += 1

    def run_py(self, *args):
        return subprocess.run([sys.executable] + list(args), capture_output=True, text=True, cwd=CUR)

    def test_pipeline_then_validate(self):
        out = os.path.join(self.tmp.name, "pipe")
        common = ["--pack", PACK]
        r = self.run_py(os.path.join("tools", "build_pool.py"), *common, "--language", "cpp", "--corpus", self.corpus2,
                        "--ontology", self.onto_path, "--core", self.core_path, "--out-dir", out)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        r = self.run_py(os.path.join("tools", "select_tasks.py"), *common, "--pool", os.path.join(out, PACK + "_pool.tsv"),
                        "--out-dir", out, "--size", "10")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        bench = os.path.join(out, "bench")
        r = self.run_py(os.path.join("tools", "export_tasks.py"), *common, "--language", "cpp",
                        "--selection", os.path.join(out, PACK + "_selection.tsv"),
                        "--pool-units", os.path.join(out, PACK + "_pool_units.jsonl"),
                        "--ontology", self.onto_path, "--core", self.core_path, "--out-dir", bench)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        sel = list(csv.DictReader(open(os.path.join(out, PACK + "_selection.tsv"), encoding="utf-8"), delimiter="\t"))
        snips = sorted(os.listdir(os.path.join(bench, "snippets", "cpp")))
        viols = sorted(os.listdir(os.path.join(bench, "violations", "cpp")))
        self.assertEqual(len(snips), len(sel))
        self.assertEqual(len(viols), len(sel))                         # one violation per task
        s0 = json.load(open(os.path.join(bench, "snippets", "cpp", snips[0]), encoding="utf-8"))
        self.assertEqual(len(s0["identifiers"]), 1)
        self.assertEqual(s0["split"], sel[0]["side"])
        self.assertEqual(s0["pack"], PACK)
        v = self.run_py("validate_benchmark.py", "--benchmark", bench, "--corpus", self.corpus2, "--ontology",
                        self.onto_path, "--languages", "cpp", "--core", self.core_path)
        self.assertEqual(v.returncode, 0, v.stdout + v.stderr)
        self.assertIn("VALIDATION PASSED", v.stdout)
        summ = json.load(open(os.path.join(bench, "tasks_summary.json"), encoding="utf-8"))
        self.assertEqual(summ["tasks"], len(sel))
        self.assertEqual(sum(summ["by_kind"]["all"].values()), len(sel))

    def test_export_rejects_a_selection_outside_the_pool(self):
        onto = self.onto()
        with self.assertRaises(ex.ExportError):
            ex.export(PACK, "cpp", [{"side": "dev", "rank": 1, "path": "nope.cpp", "unit_index": 0}], {}, onto,
                      os.path.join(self.tmp.name, "bad"))


if __name__ == "__main__":
    unittest.main()
