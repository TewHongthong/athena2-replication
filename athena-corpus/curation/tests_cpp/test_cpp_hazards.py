#!/usr/bin/env python3
"""H1-H8 of CPP_EXTRACTOR_PLAN.md section 2, plus unit labels, reverify and the C5 guard.
Every snippet is written for this test (no Godot code).

  python3 -m unittest tests_cpp/test_cpp_hazards.py      (from the curation folder)
"""
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))

import curate  # noqa: E402
import facts  # noqa: E402
import lang_ts  # noqa: E402
import tsbind  # noqa: E402

TS = tsbind.TreeSitter(tsbind.find_library())


def ex(code: str):
    return lang_ts.extract("cpp", "t.cpp", code.encode(), TS)


def decl_names(ff):
    return [d.name for d in ff.decls]


def roles(ff, text):
    """roles of every token spelled `text`, in source order"""
    return [t.role for t in ff.toks if t.text == text]


class H1Macro(unittest.TestCase):
    def test_macro_call_in_class_body(self):
        ff = ex("class W : public B {\n  MYCLASS(W, B);\npublic:\n  void f();\n};\n")
        self.assertEqual(decl_names(ff), ["W", "f"])
        self.assertEqual(roles(ff, "MYCLASS"), [facts.OTHER])
        self.assertEqual(roles(ff, "B"), [facts.TYPE, facts.OTHER])      # base clause vs macro argument
        self.assertEqual(roles(ff, "W"), [facts.DECL, facts.OTHER])

    def test_macro_without_semicolon_before_access_specifier(self):
        # one macro, then `public:`
        ff = ex("class A {\n  MYVIRT1RC(Variant, _get_parameter, const StringName &)\n\npublic:\n  void f();\n};\n")
        self.assertEqual(decl_names(ff), ["A", "f"])
        for w in ("MYVIRT1RC", "Variant", "_get_parameter", "StringName"):
            self.assertEqual(roles(ff, w), [facts.OTHER], w)

    def test_chain_of_macros_without_semicolons(self):
        # several macros in a row: tree-sitter merges them into one field_declaration + ERROR
        ff = ex("class A {\n  MYVIRT0_REQUIRED(_stop)\n  MYVIRT0RC_REQUIRED(bool, _is_playing)\n"
                "  MYVIRT0(_tag_used)\n  MYVIRT1RC(Variant, _get_parameter, const StringName &)\n\n"
                "public:\n  virtual void start(double p_pos = 0.0);\n};\n")
        self.assertEqual(decl_names(ff), ["A", "start", "p_pos"])
        for w in ("MYVIRT0_REQUIRED", "_stop", "MYVIRT0RC_REQUIRED", "_is_playing", "MYVIRT0", "_tag_used",
                  "MYVIRT1RC", "_get_parameter"):
            self.assertTrue(all(r == facts.OTHER for r in roles(ff, w)), w)

    def test_single_zero_arg_macro_is_not_a_field(self):
        ff = ex("class A {\n  MYVIRT0(_tag_used)\n  int g;\n};\n")
        self.assertEqual(decl_names(ff), ["A", "g"])
        self.assertEqual(roles(ff, "_tag_used"), [facts.OTHER])

    def test_ctor_of_upper_named_class_is_not_a_macro(self):
        ff = ex("class RID {\n  RID();\n  void f();\n};\n")
        self.assertEqual(decl_names(ff), ["RID", "f"])
        self.assertEqual(roles(ff, "RID"), [facts.DECL, facts.TYPE])


class H2ForceInline(unittest.TestCase):
    def test_unit_overlaps_error_so_the_gate_drops_it(self):
        code = "class A {\n  _FORCE_INLINE_ int get_size() const {\n    return 1;\n  }\n};\n"
        ff = ex(code)
        self.assertTrue(ff.error_spans)
        self.assertEqual(len(ff.units), 1)
        u_start, u_end = curate.unit_range(ff, ff.units[0])
        self.assertTrue(any(a < u_end and b > u_start for a, b in ff.error_spans))


class H3LessThan(unittest.TestCase):
    def test_comparison_is_never_a_decl(self):
        ff = ex("void f(int a, int b) {\n  bool c = a < b;\n  if (c) { g(a < b, b > (a)); }\n}\n")
        self.assertEqual(decl_names(ff), ["f", "a", "b", "c"])

    def test_c5_guard_rejects_when_a_same_named_token_is_not_claimed(self):
        # `b` below is parsed as a type_identifier in a template argument, so the local `b` cannot be renamed safely
        ff = ex("void f(int a) {\n  int b = 1;\n  g<b>(a);\n  h(b);\n}\n")
        b = next(d for d in ff.decls if d.name == "b")
        toks = [t for t in ff.toks]
        spans, why = curate.plan_rename("cpp", ff, ff.decls, toks, b)
        self.assertIsNone(spans)
        self.assertTrue(why.startswith("unclaimed_token:"), why)

    def test_c5_guard_is_cpp_only(self):
        ff = ex("void f(int a) {\n  int b = 1;\n  h(b);\n}\n")
        b = next(d for d in ff.decls if d.name == "b")
        spans, why = curate.plan_rename("cpp", ff, ff.decls, ff.toks, b)
        self.assertIsNone(why)
        self.assertEqual(len(spans), 2)


class H4LocalCtorCall(unittest.TestCase):
    def test_declaration_with_ctor_args_is_a_local_variable(self):
        ff = ex("void f(int p_a) {\n  String name(p_a);\n  use(name);\n}\n")
        self.assertEqual(decl_names(ff), ["f", "p_a", "name"])
        d = next(d for d in ff.decls if d.name == "name")
        self.assertEqual((d.kind, d.ns, d.extra["cpp_kind"]), ("variable", "local", "local"))
        self.assertEqual(roles(ff, "p_a"), [facts.DECL, facts.REF])      # not `type`

    def test_same_shape_at_namespace_scope_is_a_prototype(self):
        ff = ex("String name(p_a);\n")
        d = next(d for d in ff.decls if d.name == "name")
        self.assertEqual(d.extra["cpp_kind"], "free_function")


class H5CtorDtorOperator(unittest.TestCase):
    CODE = ("class Foo {\n  Foo() = default;\n  ~Foo();\n  bool operator==(const Foo &o) const;\n"
            "  Foo(int n);\n};\nFoo::Foo(int n) : a(0) {\n}\nFoo::~Foo() {\n}\n"
            "bool Foo::operator==(const Foo &o) const {\n  return true;\n}\n")

    def test_no_decl_for_ctor_dtor_operator(self):
        ff = ex(self.CODE)
        self.assertEqual(decl_names(ff), ["Foo", "o", "n", "n", "o"])
        self.assertTrue(all(d.extra["cpp_kind"] != "method" for d in ff.decls))

    def test_class_name_tokens_are_type_and_a_is_member(self):
        ff = ex(self.CODE)
        self.assertEqual(roles(ff, "Foo")[0], facts.DECL)
        self.assertTrue(all(r == facts.TYPE for r in roles(ff, "Foo")[1:]))
        self.assertEqual(roles(ff, "a"), [facts.MEMBER])
        self.assertFalse(any(t.text == "operator==" for t in ff.toks))

    def test_unit_labels(self):
        labels = [u.label for u in ex(self.CODE).units]
        # `Foo() = default;` is a function_definition in tree-sitter-cpp, so it gets a unit too (too short to be used)
        self.assertEqual(labels, ["method Foo.Foo", "method Foo::Foo", "method Foo::~Foo",
                                  "method Foo::operator=="])


class H6FunctionPointer(unittest.TestCase):
    def test_field_and_local(self):
        ff = ex("struct S {\n  int (*cb)(int);\n};\nvoid f() {\n  int (*lc)(int) = nullptr;\n}\n")
        by = {d.name: d for d in ff.decls}
        self.assertEqual((by["cb"].kind, by["cb"].ns, by["cb"].extra["fnptr"]), ("field", "member", True))
        self.assertEqual((by["lc"].kind, by["lc"].ns, by["lc"].extra["fnptr"]), ("variable", "local", True))
        self.assertNotIn("method", [d.extra["cpp_kind"] for d in ff.decls])


class H7Sizeof(unittest.TestCase):
    def test_type_in_sizeof_is_a_ref_and_the_guard_protects_it(self):
        ff = ex("struct Node {};\nvoid f() {\n  auto n = sizeof(Node);\n}\n")
        self.assertEqual(roles(ff, "Node"), [facts.DECL, facts.REF])
        d = next(d for d in ff.decls if d.name == "Node")
        spans, why = curate.plan_rename("cpp", ff, ff.decls, ff.toks, d)
        # both tokens are inside the claimed set for ns=type (TYPE, REF), so the rename is complete
        self.assertEqual(len(spans), 2)


class H8Preprocessor(unittest.TestCase):
    def test_identifiers_in_directives_are_other(self):
        ff = ex("#define LIMIT(x) ((x) > DEBUG_MAX ? 1 : 0)\n#if DEBUG\nint kept;\n#endif\n#ifdef FEATURE_X\n"
                "int also;\n#endif\n")
        self.assertEqual(roles(ff, "LIMIT"), [facts.DECL])      # the macro's own name is a declaration (4.1)
        for w in ("x", "DEBUG", "FEATURE_X"):
            self.assertTrue(roles(ff, w) and all(r == facts.OTHER for r in roles(ff, w)), w)
        self.assertEqual(roles(ff, "DEBUG_MAX"), [])     # a #define body is opaque text: no identifier token
        # code inside the conditional blocks is ordinary code
        self.assertEqual(len([t for t in ff.toks if t.text in ("kept", "also")]), 2)
        macro = [d for d in ff.decls if d.extra["cpp_kind"] == "macro"]
        self.assertEqual([(d.name, d.kind, d.exempt) for d in macro], [("LIMIT", None, "macro")])


class UnitsAndReverify(unittest.TestCase):
    def test_labels_and_top_level(self):
        ff = ex("int free_fn() {\n  return 1;\n}\nnamespace N {\nvoid g() {\n}\n}\n"
                "struct S {\n  int m() { return 2; }\n};\nint S::out() {\n  return 3;\n}\n"
                "auto l = [] { return 4; };\n")
        got = [(u.label, u.top_level) for u in ff.units]
        self.assertEqual(got, [("function free_fn", True), ("function g", True), ("method S.m", False),
                               ("method S::out", True)])

    def test_reverify_same_shape_after_rename_and_detects_break(self):
        code = "int f(int value) {\n  int total = value;\n  return total;\n}\n"
        ff = ex(code)
        d = next(d for d in ff.decls if d.name == "total")
        spans, why = curate.plan_rename("cpp", ff, ff.decls, ff.toks, d)
        self.assertIsNone(why)
        new = curate.apply_edits(ff.src, [(t.start, t.end) for t in spans], "sum_of_values")
        shape, err = ff.reverify(new)
        self.assertEqual(shape, ff.shape)
        self.assertFalse(err)
        shape2, _ = ff.reverify(b"int f(int value) {\n  int 1total = value;\n  return 1total;\n}\n")
        self.assertNotEqual(shape2, ff.shape)


if __name__ == "__main__":
    unittest.main()
