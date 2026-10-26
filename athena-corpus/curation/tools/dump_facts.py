#!/usr/bin/env python3
"""Dump extractor facts as stable, diff-able text (Athena Vol. 2, C++ extractor work).

Purpose: (1) prove that adding C++ did not change what the Vol. 1 extractors emit (dump before / after,
`diff -r` must be empty); (2) inspect C++ facts on a fixture or on the pinned Godot files; (3) report
role / kind histograms and per-file extractor exceptions. Read-only; standard library + the curation modules.

  # Vol. 1 regression dump (all 5 languages from the .md corpus)
  python tools/dump_facts.py --corpus <vol1 athena-corpus> --out /tmp/facts_before
  # C++ fixture or any local files
  python tools/dump_facts.py --lang cpp --files tests_cpp/fixtures/godot_like.cpp --out - --summary
  # pinned Godot files (needs the clone made by cpp_census.py)
  python tools/dump_facts.py --lang cpp --pin godot --out /tmp/facts_godot --summary --strict

Record format (one record per line, offsets are byte offsets):
  F <name> ok=<0|1> skip=<reason> shape=<sha1:12> err=<n> cmt=<n> str=<n> [EXC=<type: msg>]
  D <start> <end> <name> kind=<kind> ns=<ns> exempt=<reason> extra=<json>
  T <start> <end> <role> <node_type> <text>
  U <start_line> <end_line> top=<0|1> <label>
"""
import argparse
import collections
import hashlib
import json
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
CUR = os.path.dirname(HERE)
sys.path.insert(0, CUR)
sys.path.insert(0, HERE)

V1_LANGS = ["python", "java", "javascript", "typescript", "csharp"]
IDENTISH = {"identifier", "field_identifier", "type_identifier", "namespace_identifier", "statement_identifier",
            "property_identifier", "shorthand_property_identifier", "shorthand_property_identifier_pattern",
            "private_property_identifier", "destructor_name", "operator_name"}
EXT = {"cpp": (".cpp", ".cc", ".cxx", ".h", ".hpp", ".hh", ".inc")}


def preprocessor_lines(src: bytes):
    """0-based line numbers that belong to a preprocessor directive (including backslash continuations)."""
    out, cont = set(), False
    for i, ln in enumerate(src.split(b"\n")):
        s = ln.lstrip()
        if cont or s.startswith(b"#"):
            out.add(i)
            cont = ln.rstrip(b"\r").endswith(b"\\")
        else:
            cont = False
    return out


UPPER = re.compile(r"_?[A-Z][A-Z0-9_]*\Z")
PP_WHOLE = {"preproc_def", "preproc_function_def", "preproc_call", "preproc_include", "preproc_params",
            "preproc_arg", "preproc_defined"}
OTHER_REASONS = ("error_span", "macro_like", "preproc", "label", "attribute")


def other_reason(node, src, line_starts, pp_lines, facts):
    """Why an identifier token is role `other` in C++, decided from tree-sitter node names only
    (independent of lang_ts.py). Returns one of OTHER_REASONS or 'unexplained'."""
    if node is None:
        return "unexplained"
    if node.type == "statement_identifier":
        return "label"
    a = node
    while a is not None:
        if a.is_error or a.is_missing:
            return "error_span"
        if a.type in PP_WHOLE:
            return "preproc"
        if "attribute" in a.type or a.type == "alignas_qualifier":
            return "attribute"
        a = a.parent
    if facts.line_of(line_starts, node.start) in pp_lines:      # #if / #ifdef header, incl. continuations
        return "preproc"
    def macro_type(tn):     # UPPER_SNAKE type_identifier with a digit or underscore: GDVIRTUAL0, RES_BASE_EXTENSION
        if tn is None or tn.type != "type_identifier":
            return False
        t = src[tn.start:tn.end].decode("utf-8", "replace")
        return bool(UPPER.match(t)) and any(ch.isdigit() or ch == "_" for ch in t.lstrip("_")[1:])

    def upper_call(fd):     # function_declarator named UPPER_SNAKE
        d = fd.child("declarator")
        return d is not None and d.type in ("identifier", "field_identifier") \
            and bool(UPPER.match(src[d.start:d.end].decode("utf-8", "replace")))

    a = node
    while a is not None:                                        # NAME(args); declaration without a type (H1)
        if a.type == "function_declarator":
            par = a.parent
            if par is not None and par.type in ("declaration", "field_declaration") and upper_call(a) \
                    and (par.child("type") is None or macro_type(par.child("type"))):
                return "macro_like"
        if a.type in ("declaration", "field_declaration") and macro_type(a.child("type")) \
                and a.parent is not None and a.parent.type in ("field_declaration_list", "declaration_list",
                                                              "translation_unit") \
                and any(x.type == "parenthesized_declarator" or (x.type == "function_declarator" and upper_call(x))
                        for x in a.children_of("declarator")):
            return "macro_like"             # MACRO0(x) / MACRO("str") / a run of macros with no `;`
        a = a.parent
    return "unexplained"


def esc(s: str) -> str:
    return s.replace("\\", "\\\\").replace("\n", "\\n").replace("\r", "\\r").replace("\t", "\\t")


def dump_one(name, lang, path, content, ts, lang_ts, lang_python, facts, sink, hist, unexplained):
    exc = ""
    ff = None
    try:
        ff = lang_python.extract(content) if lang == "python" else lang_ts.extract(lang, path, content, ts)
    except Exception as e:  # noqa: BLE001 - the point is to report every extractor failure
        exc = "%s: %s" % (type(e).__name__, str(e)[:120])
    if ff is None:
        sink.append("F %s ok=0 skip=- shape=- err=- cmt=- str=- EXC=%s" % (name, esc(exc)))
        hist["exceptions"] += 1
        return
    shape = hashlib.sha1(repr(ff.shape).encode()).hexdigest()[:12] if ff.shape is not None else "-"
    sink.append("F %s ok=%d skip=%s shape=%s err=%d cmt=%d str=%d" % (
        name, int(ff.parse_ok), esc(ff.skip_reason or "-"), shape,
        len(ff.error_spans), len(ff.comment_spans), len(ff.string_spans)))
    hist["files"] += 1
    hist["files_with_error"] += int(bool(ff.error_spans))
    pp = preprocessor_lines(ff.src) if lang == "cpp" else set()
    by_start = {}
    if lang == "cpp" and any(t.role == facts.OTHER for t in ff.toks):
        root, _ = ts.parse("cpp", content)
        by_start = {n.start: n for n in root.walk() if n.type in IDENTISH and n.type != "destructor_name"}
    for d in sorted(ff.decls, key=lambda d: (d.start, d.end, d.name)):
        sink.append("D %d %d %s kind=%s ns=%s exempt=%s extra=%s" % (
            d.start, d.end, esc(d.name), d.kind, d.ns, d.exempt or "-",
            json.dumps(d.extra, sort_keys=True, default=str)))
        hist["kind:%s%s" % (d.kind, "(exempt)" if d.exempt else "")] += 1
    for t in ff.toks:
        sink.append("T %d %d %s %s %s" % (t.start, t.end, t.role, t.node_type, esc(t.text)))
        hist["role:%s" % t.role] += 1
        if t.node_type in IDENTISH:
            hist["ident_tokens"] += 1
            if t.role == facts.OTHER and lang == "cpp":
                why = other_reason(by_start.get(t.start), ff.src, ff.line_starts, pp, facts)
                hist["other:" + why] += 1
                if why == "unexplained":
                    hist["other_ctx:%s" % t.node_type] += 1
                    if len(unexplained) < 20:
                        unexplained.append("%s:%d %s" % (name, facts.line_of(ff.line_starts, t.start) + 1, esc(t.text)))
    for u in ff.units:
        sink.append("U %d %d top=%d %s" % (u.start_line, u.end_line, int(u.top_level), esc(u.label)))
        hist["units"] += 1


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--corpus", help="Vol. 1 athena-corpus folder (reads corpus/<lang>/*.md)")
    ap.add_argument("--lang", help="language for --files / --pin (default: all V1 languages with --corpus)")
    ap.add_argument("--files", nargs="*", help="local source files")
    ap.add_argument("--pin", choices=["godot"], help="pinned post-cutoff files (clone made by cpp_census.py)")
    ap.add_argument("--clone", default=os.path.expanduser("~/.cache/athena2/godot.git"))
    ap.add_argument("--pins", default=os.path.join(CUR, "..", "pins", "corpus_pins.json"))
    ap.add_argument("--out", required=True, help="output folder (one <lang>.facts per language) or '-' for stdout")
    ap.add_argument("--summary", action="store_true", help="print kind/role histograms and A3 coverage")
    ap.add_argument("--strict", action="store_true", help="exit 1 if any file raised an extractor exception")
    ap.add_argument("--lib", default=None)
    a = ap.parse_args()

    import facts  # noqa: E402
    import lang_python  # noqa: E402
    import lang_ts  # noqa: E402
    import tsbind  # noqa: E402
    ts = tsbind.TreeSitter(tsbind.find_library(a.lib))

    jobs = []   # (lang, [(name, path, bytes)])
    if a.corpus:
        import curate  # noqa: E402  (parse_corpus_md)
        for lang in ([a.lang] if a.lang else V1_LANGS):
            d = os.path.join(a.corpus, "corpus", lang)
            items = []
            for n in sorted(os.listdir(d)):
                if n.endswith(".md"):
                    meta, content = curate.parse_corpus_md(os.path.join(d, n))
                    if content is not None:
                        items.append((n, meta.get("file path", n), content))
            jobs.append((lang, items))
    elif a.files:
        if not a.lang:
            sys.exit("--lang is required with --files")
        items = []
        for p in a.files:
            with open(p, "rb") as f:
                items.append((os.path.basename(p), p, f.read()))
        jobs.append((a.lang, items))
    elif a.pin:
        import cpp_census as cc  # noqa: E402
        with open(a.pins, encoding="utf-8") as f:
            pins = json.load(f)
        g = next(r for r in pins["repos"] if r["id"] == a.pin)
        pin = g["pinned_commit"]
        lst = os.path.join(os.path.dirname(os.path.abspath(a.pins)), os.path.basename(g["new_files_list"]))
        with open(lst, encoding="utf-8") as f:
            paths = [ln.split("\t")[0] for ln in f.read().splitlines()[1:] if ln.strip()]
        cc.ensure_clone(a.clone, g["repo"], pin)
        items = []
        for p in paths:
            r = subprocess.run(["git", "-C", a.clone, "show", "%s:%s" % (pin, p)], capture_output=True)
            if r.returncode == 0:
                items.append((p.replace("/", "__"), p, r.stdout))
        jobs.append(("cpp" if a.pin == "godot" else a.lang, items))
    else:
        sys.exit("give one of --corpus, --files, --pin")

    exceptions = 0
    for lang, items in jobs:
        sink, hist, unexplained = [], collections.Counter(), []
        for name, path, content in items:
            dump_one(name, lang, path, content, ts, lang_ts, lang_python, facts, sink, hist, unexplained)
        exceptions += hist["exceptions"]
        text = "\n".join(sink) + "\n"
        if a.out == "-":
            sys.stdout.write(text)
        else:
            os.makedirs(a.out, exist_ok=True)
            with open(os.path.join(a.out, lang + ".facts"), "w", encoding="utf-8", newline="\n") as f:
                f.write(text)
        if a.summary:
            err = sys.stderr
            print("== %s: files=%d (with parse error %d)  extractor exceptions=%d  units=%d" % (
                lang, hist["files"], hist["files_with_error"], hist["exceptions"], hist["units"]), file=err)
            print("   decl kinds: " + "  ".join("%s=%d" % (k[5:], v) for k, v in sorted(hist.items()) if k.startswith("kind:")), file=err)
            print("   token roles: " + "  ".join("%s=%d" % (k[5:], v) for k, v in sorted(hist.items()) if k.startswith("role:")), file=err)
            n = hist["ident_tokens"] or 1
            if lang == "cpp":
                tot = sum(hist["other:" + r] for r in OTHER_REASONS + ("unexplained",))
                print("   A3 ident tokens=%d  other=%d (%.2f%%): %s  unexplained=%d  => %s" % (
                    hist["ident_tokens"], tot, 100.0 * tot / n,
                    "  ".join("%s=%d (%.2f%%)" % (r, hist["other:" + r], 100.0 * hist["other:" + r] / n) for r in OTHER_REASONS),
                    hist["other:unexplained"], "PASS" if hist["other:unexplained"] == 0 else "FAIL"), file=err)
                if unexplained:
                    print("   unexplained examples (file:line token): %s" % unexplained[:10], file=err)
    if a.strict and exceptions:
        sys.exit("%d file(s) raised extractor exceptions" % exceptions)


if __name__ == "__main__":
    main()
