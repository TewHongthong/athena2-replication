#!/usr/bin/env python3
"""Expectations for kind_infer, typed by hand from the language rules (never copied from the module's output).

  python3 -m unittest tests_kind/test_kind_infer.py      (from the curation folder)
"""
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))

import kind_infer as K  # noqa: E402

# (language, code, name, expected kind, expected status)
CASES = [
    # --- Python
    ("python", "def f(count):\n    return count + 1\n", "count", "parameter", "ok"),
    ("python", "def f(a):\n    total = a * 2\n    return total\n", "total", "variable", "ok"),
    ("python", "LIMIT = 10\n\ndef f():\n    return LIMIT\n", "LIMIT", "constant", "ok"),
    ("python", "limit = 10\n\ndef f():\n    return limit\n", "limit", "constant", "ok"),   # casing carries nothing
    ("python", "def f():\n    n = 0\n    for i in range(3):\n        n += i\n    return n\n", "n", "variable", "ok"),
    ("python", "class A:\n    def __init__(self):\n        self.size = 0\n", "size", "field", "ok"),
    ("python", "def helper(x):\n    return x\n", "helper", "function", "ok"),
    ("python", "    def run(self):\n        return 1\n", "run", "method", "ok"),            # indented excerpt
    ("python", "class Box:\n    pass\n", "Box", "class", "ok"),
    # --- Java
    ("java", "class A { static final int MAX = 3; }", "MAX", "constant", "ok"),
    ("java", "class A { private int count; }", "count", "field", "ok"),
    ("java", "class A { void run(int times) { } }", "times", "parameter", "ok"),
    ("java", "class A { int total() { int sum = 0; return sum; } }", "sum", "variable", "ok"),
    ("java", "class A { void run() { } }", "run", "method", "ok"),
    ("java", "    int total(int a) {\n        return a;\n    }\n", "total", "method", "ok"),   # bare method
    ("java", "enum Color { RED, GREEN }", "RED", "enum_member", "ok"),
    ("java", "interface Shape { }", "Shape", "interface", "ok"),
    # --- C#
    ("csharp", "class A { const int Max = 3; }", "Max", "constant", "ok"),
    ("csharp", "class A { public int Count { get; set; } }", "Count", "property", "ok"),
    ("csharp", "class A { void Run() { bool ready = true; } }", "ready", "boolean_variable", "ok"),
    ("csharp", "class A { void Run(int times) { } }", "times", "parameter", "ok"),
    ("csharp", "enum Color { Red, Green }", "Red", "enum_member", "ok"),
    ("csharp", "public void Run(int times) { }", "Run", "method", "ok"),                   # bare method
    ("csharp", "interface IShape { }", "IShape", "interface", "ok"),
    # --- TypeScript / JavaScript
    ("typescript", "const LIMIT = 10;\nfunction f() { return LIMIT; }\n", "LIMIT", "constant", "ok"),
    ("typescript", "const limit = 10;\nfunction f() { return limit; }\n", "limit", "constant", "ok"),
    ("typescript", "const items = [1, 2];\n", "items", "variable", "ok"),                   # composite: policy knob
    ("typescript", "function f() {\n  const k = 3;\n  return k;\n}\n", "k", "variable", "ok"),
    ("typescript", "interface Shape { area: number }", "Shape", "interface", "ok"),
    ("typescript", "function View({ onTap }: P) { return <b onClick={(ev) => onTap(ev)} />; }", "ev", "parameter", "ok"),
    ("javascript", "function f(value) { return value; }", "value", "parameter", "ok"),
    ("javascript", "function f(value) { return value; }", "f", "function", "ok"),
    # --- C++
    ("cpp", "int Foo::get_size() const { return size_; }", "get_size", "method", "ok"),
    ("cpp", "void set(int count) { }", "count", "parameter", "ok"),
    ("cpp", "void f() { int total = 0; }", "total", "variable", "ok"),
    ("cpp", "class W { static const int MAX = 3; };", "MAX", "constant", "ok"),
    ("cpp", "class W { int count; };", "count", "field", "ok"),
    ("cpp", "enum Mode { MODE_A, MODE_B };", "MODE_A", "enum_member", "ok"),
    ("cpp", "class Widget { };", "Widget", "class", "ok"),
    ("cpp", "void f() { }", "f", "function", "ok"),
]


class KindCases(unittest.TestCase):
    def test_table(self):
        for lang, code, name, kind, status in CASES:
            with self.subTest(lang=lang, name=name, code=code[:40]):
                r = K.infer_kind(lang, code, name)
                self.assertEqual((r.kind, r.status), (kind, status), r.detail.get("tried"))

    def test_name_casing_is_ignored(self):
        """The same declaration under three spellings of the injected name gives the same kind."""
        tmpl = {
            "python": "def f(a):\n    {n} = a * 2\n    return {n}\n",
            "java": "class A { void m(int {n}) { } }",
            "csharp": "class A { void M(int {n}) { } }",
            "cpp": "void f(int {n}) { }",
            "javascript": "function f({n}) { return {n}; }",
        }
        for lang, t in tmpl.items():
            kinds = {K.infer_kind(lang, t.replace("{n}", n), n).kind for n in ("totalcount", "TOTAL_COUNT", "TotalCount")}
            self.assertEqual(len(kinds), 1, (lang, kinds))

    def test_class_level_literal_keeps_both_kinds(self):
        r = K.infer_kind("python", "class A:\n    steps = 3\n", "steps")
        self.assertEqual((r.kind, r.status), ("field", "ok"))
        self.assertIn("constant", r.kinds)

    def test_cpp_free_function_may_be_an_inline_method(self):
        r = K.infer_kind("cpp", "void reset() {\n  n = 0;\n}\n", "reset")
        self.assertEqual((r.kind, r.status), ("function", "ok"))
        self.assertIn("method", r.kinds)

    def test_not_found_and_parse_failed(self):
        r = K.infer_kind("python", "x = 1\n", "missing")
        self.assertEqual((r.kind, r.status), (None, "not_found"))
        r = K.infer_kind("python", "def f(:\n", "f")
        self.assertEqual((r.kind, r.status), (None, "parse_failed"))

    def test_kind_map_retargets(self):
        r = K.infer_kind("java", "class A { void m(int p) { } }", "p", kind_map={"parameter": "arg"})
        self.assertEqual(r.kind, "arg")

    def test_unsupported_language(self):
        with self.assertRaises(ValueError):
            K.infer_kind("ruby", "x = 1", "x")


if __name__ == "__main__":
    unittest.main()
