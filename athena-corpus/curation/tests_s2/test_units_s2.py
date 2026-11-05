#!/usr/bin/env python3
"""Study 2 units (facets_s2.units_s2 and qualifying_units) on hand-written snippets. The expected tables are typed
in by hand from the registered amendment (HYPOTHESES_v2_study2, Benchmark); they are never read from the code.

  python3 -m unittest discover -s tests_s2       (from the curation folder)
"""
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))

import facets_s2  # noqa: E402
import lang_ts  # noqa: E402
import tsbind  # noqa: E402

BIG_FIELDS = "".join(f"        private int _f{i};\n" for i in range(60))
CS = ("""namespace N
{
    public class Outer
    {
        private int _count;
        public int Value;
        private static int s_cache;

        private struct Inner
        {
            internal int _a;
            internal int _b;
            public int C;
        }

        public void M() { }
    }

    struct Tiny { int _x; }

    record R(int A)
    {
        private int _r;
        private int _s;
        private int _t;
        private int _u;
    }

    interface I
    {
        void A();
        void B();
        void C();
        void D();
    }

    class OnlyPublic
    {
        public int A;
        public const int K = 1;
        private const int k2 = 2;
        public void M() { }
    }

    class Big
    {
""" + BIG_FIELDS + """    }

    class Broken
    {
        private int _y = ;
        private int _z;
        private int _w;
        private int _v;
    }
}
""").encode()

# label -> (top_level, reason); records and interfaces are not units
CS_EXPECTED = {
    "class Outer": (True, None),
    "struct Inner": (False, None),
    "struct Tiny": (True, "too_short"),
    "class OnlyPublic": (True, "no_s2_kind"),
    "class Big": (True, "too_long"),
    "class Broken": (True, "parse_error_in_unit"),
}

CPP = b"""class A {
public:
    void set(int p_v) {
        int a = p_v;
        a += 1;
        a += 2;
        value = a;
    }
    int value;
};
void free_fn(int p_x) {
    int a = p_x;
    a += 1;
    a += 2;
    (void)a;
}
void A::get(int &r_out) const {
    r_out = value;
}
"""

CPP_EXPECTED = {"method A.set": None, "function free_fn": "no_s2_kind", "method A::get": "too_short"}


class _Base(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ts = tsbind.TreeSitter(tsbind.find_library(None))


class TestDotnetUnits(_Base):
    def setUp(self):
        self.ff = facets_s2.extract_s2("csharp", "x.cs", CS, self.ts)

    def test_units_and_reasons(self):
        got = {u.label: (u.top_level, r) for _, u, r in facets_s2.qualifying_units("csharp", self.ff)}
        self.assertEqual(got, CS_EXPECTED)

    def test_line_ranges(self):
        lines = CS.decode().split("\n")
        for u in self.ff.units_s2:
            kw, name = u.label.split()
            self.assertIn(f"{kw} {name}", lines[u.start_line])
            self.assertTrue(lines[u.end_line].rstrip().endswith("}"))

    def test_sizes(self):
        n = {u.label: u.end_line - u.start_line + 1 for u in self.ff.units_s2}
        self.assertEqual((n["class Outer"], n["struct Inner"], n["struct Tiny"], n["class Big"]), (15, 6, 1, 63))

    def test_inner_inside_outer(self):
        u = {u.label: u for u in self.ff.units_s2}
        self.assertTrue(u["class Outer"].start_line < u["struct Inner"].start_line
                        and u["struct Inner"].end_line < u["class Outer"].end_line)

    def test_study1_units_unchanged(self):
        s1 = lang_ts.extract("csharp", "x.cs", CS, self.ts)
        self.assertEqual([(u.start_line, u.end_line, u.label) for u in s1.units],
                         [(u.start_line, u.end_line, u.label) for u in self.ff.units])


class TestGodotUnits(_Base):
    def setUp(self):
        self.ff = facets_s2.extract_s2("cpp", "x.cpp", CPP, self.ts)

    def test_units_are_study1_units(self):
        self.assertEqual(self.ff.units_s2, self.ff.units)

    def test_reasons(self):
        got = {u.label: r for _, u, r in facets_s2.qualifying_units("cpp", self.ff)}
        self.assertEqual(got, CPP_EXPECTED)


if __name__ == "__main__":
    unittest.main()
