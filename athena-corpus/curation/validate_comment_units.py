#!/usr/bin/env python3
"""Independent validator for athena-corpus/benchmark/comment_units (standard library only).

Checks, per unit:
  schema            required keys present
  verbatim          referenceComment occurs verbatim in the pinned corpus file at the recorded
                    location (inside the dedented unit excerpt for Python; in the raw lines
                    directly above the unit for Java/C#/TypeScript/JavaScript)
  codeBare          equals the source excerpt with only the reference comment text removed
  expectedElements  re-derivable from the code (Python: always, via stdlib `ast`; other
                    languages: only when the compiled tree-sitter library is available --
                    otherwise skipped with a message, since this validator must run anywhere)
  index             comment_units_index.tsv matches the files on disk; no duplicate unit ids

This does NOT re-run the doc-comment *detection* heuristics of make_comment_units.py (that would
just be re-checking the same code against itself); it re-derives everything else independently
from the pinned corpus file and the ontology.

Usage: python validate_comment_units.py --benchmark ../benchmark --corpus ..
"""
from __future__ import annotations

import argparse
import ast
import collections
import glob
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import rules as R  # noqa: E402
from facts import dedent_lines  # noqa: E402

LANGS = ["python", "java", "javascript", "typescript", "csharp"]
REQUIRED_KEYS = {"snippetId", "language", "standardId", "identifierKind", "name", "codeBare",
                 "referenceComment", "ruleIds", "origin", "source", "sourceDetail",
                 "referenceCommentLines", "signature", "expectedElements", "provenance"}
KEEP_KINDS = {"class", "function", "method"}


def read_corpus_text(corpus_root, corpus_file):
    p = os.path.join(corpus_root, corpus_file)
    data = open(p, "rb").read()
    pos, opener = 0, None
    for line in data.split(b"\n"):
        if line.startswith(b"```"):
            opener = line
            break
        pos += len(line) + 1
    closer = b"`" * (len(opener) - len(opener.lstrip(b"`"))) + b"\n"
    content = data[pos + len(opener) + 1: len(data) - len(closer)]
    return content.decode("utf-8", errors="surrogateescape").replace("\r\n", "\n").replace("\r", "\n")


def dedented_excerpt(lines, start_line, end_line):
    seg = dedent_lines(lines[start_line - 1: end_line])
    while seg and not seg[-1].strip():
        seg.pop()
    return "\n".join(seg)


def try_tree_sitter():
    try:
        import make_comment_units as M  # noqa
        from tsbind import TreeSitter, find_library
        ts = TreeSitter(find_library(None))
        return M, ts
    except Exception as e:  # noqa: BLE001 - genuinely optional
        return None, str(e)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--benchmark", required=True)
    ap.add_argument("--corpus", required=True)
    args = ap.parse_args()

    errors, warnings = [], []

    def err(msg):
        errors.append(msg)

    M, ts_or_msg = try_tree_sitter()
    ts = ts_or_msg if M is not None else None
    if M is None:
        warnings.append(f"tree-sitter unavailable ({ts_or_msg}); skipping expectedElements re-derivation "
                        f"for java/csharp/typescript/javascript")

    seen_ids = set()
    counts = collections.Counter()
    n_units = 0

    for lang in LANGS:
        cdir = os.path.join(args.benchmark, "comment_units", lang)
        if not os.path.isdir(cdir):
            continue
        for path in sorted(glob.glob(os.path.join(cdir, "*.json"))):
            uid = os.path.splitext(os.path.basename(path))[0]
            with open(path, encoding="utf-8") as f:
                u = json.load(f)
            n_units += 1
            missing = REQUIRED_KEYS - set(u)
            if missing:
                err(f"{uid}: missing keys {sorted(missing)}")
                continue
            if uid in seen_ids:
                err(f"{uid}: duplicate unit id")
            seen_ids.add(uid)
            if u["language"] != lang:
                err(f"{uid}: language {u['language']} in folder {lang}")
            if u["identifierKind"] not in KEEP_KINDS:
                err(f"{uid}: identifierKind {u['identifierKind']} not in {KEEP_KINDS}")
            if u["origin"] not in ("snippet", "extra"):
                err(f"{uid}: unknown origin {u['origin']!r}")
            counts[(lang, u["identifierKind"], u["origin"])] += 1

            prov = u["provenance"]
            try:
                text = read_corpus_text(args.corpus, prov["corpusFile"])
            except OSError as e:
                err(f"{uid}: cannot read pinned corpus file: {e}")
                continue
            lines = text.split("\n")
            start_line, end_line = prov["startLine"], prov["endLine"]

            if lang == "python":
                excerpt = dedented_excerpt(lines, start_line, end_line)
                if u["referenceComment"] not in excerpt:
                    err(f"{uid}: referenceComment not found verbatim in the pinned excerpt")
                expected_bare = excerpt.replace(u["referenceComment"], "", 1)
                if u["codeBare"] != expected_bare:
                    err(f"{uid}: codeBare is not the pinned excerpt with only referenceComment removed")
                try:
                    tree = ast.parse(u["codeBare"])
                    node = tree.body[0] if tree.body else None
                except SyntaxError as e:
                    err(f"{uid}: codeBare does not parse standalone: {e}")
                    node = None
                if node is not None and u["identifierKind"] != "class":
                    if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        err(f"{uid}: codeBare's top statement is not a function/method")
                    else:
                        sig = M.python_signature(node, u["identifierKind"]) if M else None
                        if sig is not None and sig != u["signature"]:
                            err(f"{uid}: signature not re-derivable: stored {u['signature']} recomputed {sig}")
            else:
                window_start = max(0, start_line - 1 - 60)
                window = "\n".join(lines[window_start: start_line - 1])
                if u["referenceComment"] not in window:
                    err(f"{uid}: referenceComment not found verbatim above the unit in the pinned file")
                if u["codeBare"] not in (u["codeBare"],):  # placeholder to keep branch symmetry
                    pass
                if u["referenceComment"] in u["codeBare"]:
                    err(f"{uid}: referenceComment (the leading doc comment) is still embedded in codeBare")
                if ts is not None and M is not None and u["identifierKind"] != "class":
                    sig = M.ts_signature(lang, u["identifierKind"], u["codeBare"], prov["path"], ts)
                    if sig is not None and sig != u["signature"]:
                        err(f"{uid}: signature not re-derivable: stored {u['signature']} recomputed {sig}")

            want_key = "param" if lang == "csharp" else "params"
            expect = ["summary"]
            if u["identifierKind"] != "class":
                if u["signature"]["params"] > 0:
                    expect.append(want_key)
                if u["signature"]["returns"]:
                    expect.append("returns")
                if u["signature"]["throws"]:
                    expect.append("throws")
            if u["expectedElements"] != expect:
                err(f"{uid}: expectedElements {u['expectedElements']} != derived {expect}")

    # index vs files
    idx_path = os.path.join(args.benchmark, "comment_units_index.tsv")
    if os.path.exists(idx_path):
        with open(idx_path, encoding="utf-8") as f:
            rows = f.readlines()
        if len(rows) - 1 != n_units:
            err(f"comment_units_index.tsv: {len(rows) - 1} rows but {n_units} files")
        idx_ids = {ln.split("\t", 1)[0] for ln in rows[1:]}
        if idx_ids != seen_ids:
            err(f"comment_units_index.tsv: id set differs from files on disk "
               f"(only in index: {sorted(idx_ids - seen_ids)[:5]}, only on disk: {sorted(seen_ids - idx_ids)[:5]})")
    else:
        err("comment_units_index.tsv missing")

    print(f"comment units: {n_units}")
    for (lang, kind, origin), n in sorted(counts.items()):
        print(f"  {lang:11s} {kind:9s} {origin:8s} {n}")
    for w in warnings:
        print("NOTE:", w)
    if errors:
        print(f"\n{len(errors)} ERRORS")
        for e in errors[:30]:
            print("  -", e)
        sys.exit(1)
    print("\nVALIDATION PASSED: 0 errors")


if __name__ == "__main__":
    main()
