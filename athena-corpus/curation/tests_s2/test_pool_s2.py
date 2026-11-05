#!/usr/bin/env python3
"""Study 2 pool, method assignment and validation (tools/build_pool_s2.py, export_tasks_s2.py,
validate_benchmark_s2.py) on hand-written snippets and synthetic selections.

  python3 -m unittest discover -s tests_s2       (from the curation folder)
"""
import collections
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
CUR = os.path.dirname(HERE)
sys.path.insert(0, CUR)
sys.path.insert(0, os.path.join(CUR, "tools"))

import build_pool_s2 as B  # noqa: E402
import core_table  # noqa: E402
import export_tasks_s2 as X  # noqa: E402
import facets_s2 as F  # noqa: E402
import rules as R  # noqa: E402
import tsbind  # noqa: E402

PACKS = os.path.normpath(os.path.join(CUR, "..", "..", "athena-sim", "packs"))

CS_OK = b"""internal sealed class Counter
{
    private int _count;
    private static int s_total;

    public void Add(int n)
    {
        _count += n;
        s_total += n;
    }
}
"""

CS_STRIP_CLASH = b"""internal sealed class Holder
{
    private readonly int _count;

    public Holder(int count)
    {
        _count = count;
    }

    public int Get() => _count;
}
"""

CS_GATE_FAIL = b"""internal sealed class Bad
{
    private int count;
    private int _other;

    public void Add(int n)
    {
        count += n;
        _other += n;
    }
}
"""


class _Core(unittest.TestCase):
    """Installs the core table of a Study 2 pack and restores the Study 1 table afterwards."""
    PACK, ONTO = "dotnet-runtime-s2", "dotnet_ontology.json"

    @classmethod
    def setUpClass(cls):
        cls._saved = (dict(R.CORE), dict(R.EXCLUDED), list(R.TARGET_KINDS), R._SPECIALS)
        cls.onto = R.Ontology(os.path.join(PACKS, cls.PACK, cls.ONTO))
        problems = core_table.apply(os.path.join(PACKS, cls.PACK, "core_rules.json"), cls.onto)
        assert not problems, problems
        cls.ts = tsbind.TreeSitter(tsbind.find_library(None))

    @classmethod
    def tearDownClass(cls):
        core, excl, tk, spec = cls._saved
        R.CORE.clear()
        R.CORE.update(core)
        R.EXCLUDED.clear()
        R.EXCLUDED.update(excl)
        R.TARGET_KINDS[:] = tk
        R._SPECIALS = spec

    def unit_record(self, src, rule="both"):
        ff = F.extract_s2("csharp", "x.cs", src, self.ts)
        stats = B.new_stats()
        rec = B.evaluate_unit(self.PACK, "csharp", ff, ff.units_s2[0], 0, "x.cs", self.onto, stats, pool_rule=rule)
        return rec, stats


class TestDotnetUnits(_Core):
    def test_both_methods(self):
        rec, stats = self.unit_record(CS_OK)
        self.assertIsNotNone(rec)
        self.assertEqual(set(rec["methods"]), {"prefix_strip", "prefix_swap"})
        for m, x in rec["methods"].items():
            v, t = x["violation"], x["target"]
            self.assertEqual(v["method"], m)
            self.assertIn(t["name"], ("_count", "s_total"))
            rule = {"_count": "DOTNET-FIELD-INSTANCE-PREFIX", "s_total": "DOTNET-FIELD-STATIC-PREFIX"}[t["name"]]
            self.assertEqual(v["rule"], rule)
            self.assertIn(v["injected"], v["code"])
            self.assertNotIn(t["name"], v["code"].replace(v["injected"], ""))
        self.assertEqual(rec["methods"]["prefix_strip"]["violation"]["injected"],
                         rec["methods"]["prefix_strip"]["target"]["name"].split("_", 1)[1])

    def test_strip_clash(self):
        rec, stats = self.unit_record(CS_STRIP_CLASH)
        self.assertIsNone(rec)
        self.assertEqual(stats["units"]["one_method_only"], 1)
        rec, stats = self.unit_record(CS_STRIP_CLASH, "either")
        self.assertEqual(set(rec["methods"]), {"prefix_swap"})
        self.assertEqual(stats["units"]["one_method_only_kept"], 1)
        self.assertIn(rec["methods"]["prefix_swap"]["violation"]["injected"], ("s_count", "t_count"))

    def test_gate(self):
        rec, stats = self.unit_record(CS_GATE_FAIL, "either")
        self.assertIsNone(rec)
        self.assertEqual(stats["unit_gate_failures_by_rule"], {"DOTNET-FIELD-INSTANCE-PREFIX": 1})

    def test_deterministic(self):
        self.assertEqual(self.unit_record(CS_OK)[0], self.unit_record(CS_OK)[0])


class TestCandidates(unittest.TestCase):
    def test_godot(self):
        d = collections.namedtuple("D", "name")("p_value")
        rule = {"prefix": "p_"}
        self.assertEqual(B.candidates("cpp", "godot-s2", "a.cpp", 0, d, rule, "prefix_strip"), ["value"])
        self.assertEqual(B.candidates("cpp", "godot-s2", "a.cpp", 0, d, rule, "prefix_swap"), ["r_value"])

    def test_dotnet_siblings(self):
        d = collections.namedtuple("D", "name")("_count")
        got = B.candidates("csharp", "dotnet-runtime-s2", "a.cs", 3, d, {"prefix": "_"}, "prefix_swap")
        self.assertEqual(sorted(got), ["s_count", "t_count"])
        self.assertEqual(got, B.candidates("csharp", "dotnet-runtime-s2", "a.cs", 3, d, {"prefix": "_"}, "prefix_swap"))
        d2 = collections.namedtuple("D", "name")("s_cache")
        self.assertEqual(sorted(B.candidates("csharp", "p", "a.cs", 0, d2, {"prefix": "s_"}, "prefix_swap")),
                         ["_cache", "t_cache"])


class TestAssignMethods(unittest.TestCase):
    @staticmethod
    def make(side_avail):
        selection, units = [], {}
        for side, avails in side_avail.items():
            for rank, av in enumerate(avails, 1):
                p = "%s/f%d.cs" % (side, rank)
                selection.append({"side": side, "rank": rank, "path": p, "unit_index": 0})
                units[(p, 0)] = {"methods": {m: {} for m in av}}
        return selection, units

    def test_balanced(self):
        both = ("prefix_strip", "prefix_swap")
        sel, units = self.make({"dev": [both] * 5, "test": [both] * 5})
        out, rep = X.assign_methods(sel, units, "p")
        self.assertEqual(rep["dev"]["assigned"], {"prefix_strip": 3, "prefix_swap": 2})
        self.assertEqual(rep["test"]["assigned"], {"prefix_strip": 2, "prefix_swap": 3})
        self.assertTrue(rep["dev"]["balanced"] and rep["test"]["balanced"])
        self.assertEqual(out, X.assign_methods(sel, units, "p")[0])

    def test_forced(self):
        both, swap = ("prefix_strip", "prefix_swap"), ("prefix_swap",)
        sel, units = self.make({"dev": [swap, swap, both, both], "test": [swap, swap, swap, both]})
        out, rep = X.assign_methods(sel, units, "p")
        self.assertEqual(rep["dev"]["assigned"], {"prefix_strip": 2, "prefix_swap": 2})
        self.assertTrue(rep["dev"]["balanced"])
        self.assertEqual(rep["test"]["assigned"], {"prefix_strip": 1, "prefix_swap": 3})
        self.assertFalse(rep["test"]["balanced"])
        for r in sel:
            self.assertIn(out[(r["path"], 0)], units[(r["path"], 0)]["methods"])


class TestValidatorCandidates(unittest.TestCase):
    def test_swap_added_after_study1(self):
        import validate_benchmark_s2 as V
        try:
            got = list(R.iter_candidates("_count", {"prefix": "_"}))
            self.assertEqual(got, [("prefix_strip", "count"), ("prefix_swap", "s_count"), ("prefix_swap", "t_count")])
            self.assertEqual(list(R.iter_candidates("p_a", {"prefix": "p_"}))[-1], ("prefix_swap", "r_a"))
            self.assertEqual(list(R.iter_candidates("fooBar", {"casing": "snake_case"})),
                             list(V._study1_candidates("fooBar", {"casing": "snake_case"})))
        finally:
            R.iter_candidates = V._study1_candidates


if __name__ == "__main__":
    unittest.main()
