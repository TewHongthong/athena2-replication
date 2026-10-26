#!/usr/bin/env python3
"""Smoke test for the tree-sitter library that tsbind.py loads (standard library only).

Parses one small hand-written snippet per language (java, csharp, typescript, tsx, javascript,
cpp) and exits 1 if the library or a language is missing or any snippet parses with an error.
It does not test the extractors (lang_ts.py / lang_python.py).

Usage: python tools/smoke_test_treesitter.py [--lib PATH]
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import tsbind  # noqa: E402

SNIPPETS = {
    "java": b"package a;\npublic class Foo { private int fooBar; public int getFooBar(int x) { return fooBar + x; } }\n",
    "csharp": b"namespace A { public class Foo { private int _fooBar; public int GetFooBar(int x) { return _fooBar + x; } } }\n",
    "typescript": b"export class Foo { private fooBar: number = 1; get(x: number): number { return this.fooBar + x; } }\n",
    "tsx": b"export const C = (p: {a: number}) => <div className=\"x\">{p.a}</div>;\n",
    "javascript": b"function foo(a, b) { const c = a + b; return c; }\nclass K { m() { return 1; } }\n",
    "cpp": (b"#define MAX_ITEMS 16\n"
            b"namespace demo {\n"
            b"enum class Mode { FAST, SLOW };\n"
            b"constexpr int DEFAULT_SIZE = 8;\n"
            b"template <typename T>\n"
            b"class Buffer : public Base {\n"
            b"public:\n"
            b"    static constexpr int GROW_STEP = 2;\n"
            b"    bool try_get(int p_index, T &r_value) const {\n"
            b"        if (p_index < 0 || p_index >= count) { return false; }\n"
            b"        r_value = items[p_index];\n"
            b"        return true;\n"
            b"    }\n"
            b"private:\n"
            b"    int count = 0;\n"
            b"};\n"
            b"static void free_function(int *p_ptr, int &r_out) {\n"
            b"    auto fn = [&](int v) { return v * 2; };\n"
            b"    r_out += fn(*p_ptr);\n"
            b"}\n"
            b"}\n"),
}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--lib", default=None)
    a = ap.parse_args()
    if a.lib and not os.path.exists(a.lib):
        print("FAIL  --lib %s does not exist" % a.lib)   # find_library would silently fall back to another copy
        return 1
    try:
        lib = tsbind.find_library(a.lib)
        ts = tsbind.TreeSitter(lib)
    except (FileNotFoundError, OSError, AttributeError) as e:
        print("FAIL  cannot load library: %s" % e)
        return 1
    print("library: %s" % os.path.abspath(lib))
    bad = 0
    for lang, src in SNIPPETS.items():
        root, has_err = ts.parse(lang, src)
        n_named = sum(1 for n in root.walk() if n.named)
        print("%-11s %s  named_nodes=%d" % (lang, "FAIL" if has_err else "ok  ", n_named))
        bad += bool(has_err)
    print("%d of %d languages parsed cleanly" % (len(SNIPPETS) - bad, len(SNIPPETS)))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
