#!/usr/bin/env python3
"""A1: the C++ extractor's decls on tests_cpp/fixtures/godot_like.cpp must equal the table in
CPP_EXTRACTOR_PLAN.md section 6. The table below is typed in by hand; it is never read from extractor output.

  python3 -m unittest tests_cpp/test_cpp_extractor.py      (from the curation folder)
"""
import collections
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))

import facts  # noqa: E402
import lang_ts  # noqa: E402
import tsbind  # noqa: E402

FIXTURE = os.path.join(HERE, "fixtures", "godot_like.cpp")

# (line, name, cpp_kind, kind, ns, exempt) -- 34 rows, section 6 table A1
A1 = [
    (1, "MY_MAX", "macro", None, "type", "macro"),
    (3, "Demo", "namespace", None, "type", None),
    (5, "Mode", "enum", "enum", "type", None),
    (6, "MODE_IDLE", "enum_member", "enum_member", "member", None),
    (7, "MODE_RUN", "enum_member", "enum_member", "member", None),
    (10, "T", "template_param", None, "type", None),
    (11, "Holder", "class", "class", "type", None),
    (12, "value", "field", "field", "member", None),
    (15, "get", "method", "method", "member", None),
    (18, "Widget", "class", "class", "type", None),
    (21, "MAX_ITEMS", "static_const_field", "constant", "member", None),
    (22, "item_count", "field", "field", "member", None),
    (23, "items", "field", "field", "member", None),
    (24, "_dirty", "field", "field", "member", None),
    (27, "State", "enum", "enum", "type", None),
    (27, "STATE_OFF", "enum_member", "enum_member", "member", None),
    (27, "STATE_ON", "enum_member", "enum_member", "member", None),
    (32, "set_count", "method", "method", "member", None),
    (32, "p_count", "param", "parameter", "local", None),
    (33, "get_count", "method", "method", "member", None),
    (34, "p_other", "param", "parameter", "local", None),
    (35, "create", "method", "method", "member", None),
    (35, "p_name", "param", "parameter", "local", None),
    (35, "r_error", "param", "parameter", "local", None),
    (47, "set_count", "method", "method", "member", None),
    (47, "p_count", "param", "parameter", "local", None),
    (49, "old_count", "local", "variable", "local", None),
    (51, "notify", "local", "variable", "local", None),
    (51, "p_value", "param", "parameter", "local", "lambda_param"),
    (54, "name", "local", "variable", "local", None),
    (62, "create", "method", "method", "member", None),
    (62, "p_name", "param", "parameter", "local", None),
    (62, "r_error", "param", "parameter", "local", None),
    (63, "result", "local", "variable", "local", None),
]

# names that must have NO decl (section 6): GDCLASS (19), ctor/dtor (29, 30, 38, 43), operator== (34),
# a/b in the macro (1), `names` (used, never declared)
ABSENT_AT = [(19, "GDCLASS"), (29, "Widget"), (30, "Widget"), (38, "Widget"), (43, "Widget"),
             (34, "operator=="), (1, "a"), (1, "b")]
ABSENT_NAMES = ["names", "GDCLASS", "a", "b"]


def extract_fixture():
    ts = tsbind.TreeSitter(tsbind.find_library())
    with open(FIXTURE, "rb") as f:
        src = f.read()
    return lang_ts.extract("cpp", FIXTURE, src, ts)


class A1Test(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ff = extract_fixture()
        cls.got = [(facts.line_of(cls.ff.line_starts, d.start) + 1, d) for d in cls.ff.decls]

    def test_no_parse_error(self):
        self.assertEqual(self.ff.error_spans, [])

    def test_table_has_34_rows(self):
        self.assertEqual(len(A1), 34)

    def test_decls_equal_table(self):
        got = collections.Counter((ln, d.name, d.extra.get("cpp_kind"), d.kind, d.ns, d.exempt)
                                  for ln, d in self.got)
        self.assertEqual(got, collections.Counter(A1))

    def test_absent_decls(self):
        have = {(ln, d.name) for ln, d in self.got}
        for item in ABSENT_AT:
            self.assertNotIn(item, have)
        names = {d.name for _, d in self.got}
        for n in ABSENT_NAMES:
            self.assertNotIn(n, names)

    def test_decl_tokens_have_decl_role(self):
        toks = {t.start: t for t in self.ff.toks}
        for _, d in self.got:
            self.assertEqual(toks[d.start].role, facts.DECL, d.name)

    def test_selected_facets(self):
        by = {(ln, d.name): d.extra for ln, d in self.got}
        self.assertTrue(by[(11, "Holder")]["template"])
        self.assertFalse(by[(18, "Widget")]["template"])
        self.assertEqual(by[(18, "Widget")]["bases"], "public Base")
        self.assertFalse(by[(5, "Mode")]["scoped"])
        self.assertEqual(by[(6, "MODE_IDLE")]["enum"], "Mode")
        self.assertTrue(by[(23, "items")]["ptr"])
        self.assertEqual(by[(22, "item_count")]["access"], "private")
        self.assertEqual(by[(21, "MAX_ITEMS")]["static"], True)
        self.assertEqual(by[(27, "State")] .get("scoped"), False)
        self.assertEqual(by[(32, "set_count")]["access"], "public")
        self.assertTrue(by[(32, "set_count")]["proto"])
        self.assertTrue(by[(33, "get_count")]["const_method"])
        self.assertTrue(by[(35, "create")]["static"])
        self.assertTrue(by[(15, "get")]["in_class_def"])
        self.assertFalse(by[(32, "set_count")]["in_class_def"])
        self.assertEqual(by[(23, "items")]["ref_kind"], "none")
        self.assertTrue(by[(47, "set_count")]["out_of_class"])
        self.assertEqual(by[(47, "set_count")]["scope"], "Widget")
        self.assertEqual(by[(34, "p_other")]["ref_kind"], "lref")
        self.assertTrue(by[(34, "p_other")]["const_ref"])
        self.assertEqual(by[(35, "r_error")]["ref_kind"], "lref")
        self.assertFalse(by[(35, "r_error")]["const_ref"])
        self.assertEqual(by[(54, "name")]["ref_kind"], "lref")


if __name__ == "__main__":
    unittest.main()
