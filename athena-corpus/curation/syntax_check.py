#!/usr/bin/env python3
"""Standalone syntax check of every snippet and violation context (needs the parsers).

Python: ast.parse on the snippet text. Java/C#/TypeScript/JavaScript: tree-sitter parse of the snippet,
wrapped in `class __W { ... }` when the snippet is a class member (unit label starts with 'method'/'constructor').
Reports snippets whose original OR violated context fails to parse.
Usage: python syntax_check.py --benchmark <dir> [--lib <tree-sitter lib>]
"""
import argparse, ast, glob, json, os, sys, collections
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from tsbind import TreeSitter, find_library

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--benchmark", required=True); ap.add_argument("--lib", default=None)
    a = ap.parse_args()
    ts = TreeSitter(find_library(a.lib))
    bad = collections.defaultdict(list); n = collections.Counter()

    def ok(lang, text, wrap, path_hint=""):
        if lang == "python":
            try:
                ast.parse(text); return True
            except SyntaxError:
                return False
        g = {"typescript": "tsx" if "tsx" in path_hint else "typescript"}.get(lang, lang)
        src = text
        if wrap:
            src = "class __W {\n" + text + "\n}\n"
        _, err = ts.parse(g, src.encode("utf-8"))
        return not err

    for lang in ["python", "java", "javascript", "typescript", "csharp"]:
        for p in sorted(glob.glob(os.path.join(a.benchmark, "snippets", lang, "*.json"))):
            s = json.load(open(p, encoding="utf-8"))
            unit = s["provenance"]["unit"]; wrap = unit.startswith(("method ", "constructor "))
            hint = s["provenance"]["path"]
            n[lang] += 1
            if not ok(lang, s["codeContext"], wrap, hint):
                bad[lang].append(s["id"] + " (original)")
            for vp in glob.glob(os.path.join(a.benchmark, "violations", lang, s["id"] + "__*.json")):
                v = json.load(open(vp, encoding="utf-8")); n[lang + "_viol"] += 1
                if not ok(lang, v["codeContextWithViolation"], wrap, hint):
                    bad[lang].append(os.path.basename(vp))
    print({k: v for k, v in n.items()})
    for lang, lst in bad.items():
        print(lang, len(lst), lst[:12])
    print("SYNTAX OK" if not bad else "SYNTAX PROBLEMS")
    sys.exit(1 if bad else 0)
main()
