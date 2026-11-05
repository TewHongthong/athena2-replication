#!/usr/bin/env python3
"""Study 2 kinds inferred from snippets (kind_infer_s2.py). Expectations typed in by hand from packs/*-s2/KINDS.md.

  python3 -m unittest discover -s tests_s2       (from the curation folder)
"""
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))

import kind_infer_s2 as K  # noqa: E402

CPP_QUALIFIED = """void Node::set_value(const Variant &VALUE, Node *TARGET, int COUNT, const char **NAMES, Foo &&MOVED) {
    value = VALUE;
    TARGET->count = COUNT;
    (void)NAMES;
    (void)MOVED;
}
"""

CPP_INLINE = """void set_value(const Variant &VALUE, Node *TARGET) {
    value = VALUE;
    target = TARGET;
}
"""

CS_CLASS = """internal sealed class Holder
{
    private int VALUE;
    private static int STATIC_ONE;
    [ThreadStatic] private static int PER_THREAD;
    public int PUBLIC_ONE;
    protected int PROTECTED_ONE;
    private const int CONSTANT_ONE = 1;

    public void Add(int n) { VALUE += n; STATIC_ONE += n; PER_THREAD += n; PUBLIC_ONE += PROTECTED_ONE + CONSTANT_ONE; }
}
"""


class TestGodot(unittest.TestCase):
    def test_qualified_method(self):
        got = {n: K.infer_kind_s2("cpp", CPP_QUALIFIED, n).kind for n in ("VALUE", "TARGET", "COUNT", "NAMES", "MOVED")}
        self.assertEqual(got, {"VALUE": "input_parameter", "TARGET": "output_parameter", "COUNT": "input_parameter",
                               "NAMES": "output_parameter", "MOVED": "output_parameter"})

    def test_inline_method_is_read_as_free_function(self):
        for n in ("VALUE", "TARGET"):
            r = K.infer_kind_s2("cpp", CPP_INLINE, n)
            self.assertEqual((r.kind, r.status), ("parameter", "ok"))
            self.assertEqual(r.detail["kind_s1"], "parameter")

    def test_name_casing_and_prefix_carry_no_information(self):
        a = K.infer_kind_s2("cpp", CPP_QUALIFIED.replace("TARGET", "p_target"), "p_target").kind
        b = K.infer_kind_s2("cpp", CPP_QUALIFIED.replace("TARGET", "r_target"), "r_target").kind
        self.assertEqual((a, b), ("output_parameter", "output_parameter"))

    def test_other_kinds_keep_study1(self):
        r = K.infer_kind_s2("cpp", CPP_QUALIFIED, "value")
        self.assertIsNone(r.kind)          # `value` is not declared in the snippet

    def test_not_found(self):
        self.assertEqual(K.infer_kind_s2("cpp", CPP_QUALIFIED, "absent").status, "not_found")


class TestDotnet(unittest.TestCase):
    def test_fields(self):
        got = {n: K.infer_kind_s2("csharp", CS_CLASS, n).kind for n in
               ("VALUE", "STATIC_ONE", "PER_THREAD", "PUBLIC_ONE", "PROTECTED_ONE", "CONSTANT_ONE")}
        self.assertEqual(got, {"VALUE": "instance_field", "STATIC_ONE": "static_field",
                               "PER_THREAD": "threadstatic_field", "PUBLIC_ONE": "public_field",
                               "PROTECTED_ONE": "field", "CONSTANT_ONE": "constant"})

    def test_method_keeps_study1_kind(self):
        self.assertEqual(K.infer_kind_s2("csharp", CS_CLASS, "Add").kind, "method")


if __name__ == "__main__":
    unittest.main()
