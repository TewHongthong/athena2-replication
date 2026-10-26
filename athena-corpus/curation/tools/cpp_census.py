#!/usr/bin/env python3
"""Census of tree-sitter-cpp parse contexts (Athena Vol. 2, WP2). Read-only; standard library + tsbind only.

Answers, before a C++ extractor is written: in which parent nodes do identifiers occur, how many
function_declarators are really macro invocations (e.g. GDCLASS(...)), and how many files / functions
contain parse errors. Writes nothing except the optional --json file.

  python tools/cpp_census.py --clone ~/.cache/athena2/godot.git    # pinned Godot files (git + network, first run only)
  python tools/cpp_census.py --files tests_cpp/fixtures/godot_like.cpp   # local files, no git, no network
"""
import argparse
import collections
import json
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
CUR = os.path.dirname(HERE)
sys.path.insert(0, CUR)
import tsbind  # noqa: E402

IDENT = {"identifier", "field_identifier", "type_identifier", "namespace_identifier", "statement_identifier",
         "destructor_name", "operator_name"}
UPPER = re.compile(r"[A-Z][A-Z0-9_]*\Z")


def git(*args):
    return subprocess.run(["git", *args], capture_output=True)


def ensure_clone(path, url, pin):
    """Blobless bare clone at `path` that has the pinned commit (blobs are fetched lazily by `git show`)."""
    if not os.path.isdir(path):
        os.makedirs(path, exist_ok=True)
        for cmd in (["init", "-q", "--bare", path],
                    ["-C", path, "remote", "add", "origin", url],
                    ["-C", path, "config", "remote.origin.promisor", "true"],
                    ["-C", path, "config", "remote.origin.partialclonefilter", "blob:none"]):
            r = git(*cmd)
            if r.returncode:
                sys.exit("git %s failed: %s" % (cmd[0], r.stderr.decode()[:300]))
    if git("-C", path, "cat-file", "-e", pin + "^{commit}").returncode:
        print("fetching pinned commit %s ..." % pin[:12], file=sys.stderr)
        r = git("-C", path, "fetch", "-q", "--depth", "1", "--filter=blob:none", "origin", pin)
        if r.returncode:
            sys.exit("git fetch failed: %s" % r.stderr.decode()[:300])


def census(src, ts, c):
    root, has_err = ts.parse("cpp", src)
    c["files"] += 1
    c["files_with_error"] += int(has_err)
    for n in root.walk():
        if n.is_error or n.is_missing:
            c["err_parent"][n.parent.type if n.parent else "-"] += 1
        t = n.type
        if t in IDENT:
            c["ctx"][(t, n.parent.type if n.parent else "-", n.field or "-")] += 1
        elif t == "template_function":
            c["template_function"] += 1
        elif t == "function_declarator":
            d = n.child("declarator")
            if d is not None and d.type == "identifier":
                nm = src[d.start:d.end].decode("utf-8", "replace")
                par = n.parent
                typed = par is not None and par.child("type") is not None
                if UPPER.match(nm) and not typed and par is not None and par.type in ("declaration", "field_declaration"):
                    c["macro_like_declarators"] += 1
                    c["macro_names"][nm] += 1
        elif t == "function_definition":
            c["function_definition"] += 1
            if not any(x.is_error or x.is_missing for x in n.walk()):
                c["function_definition_error_free"] += 1


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--clone", default=os.path.expanduser("~/.cache/athena2/godot.git"),
                    help="bare (or normal) clone used for the pinned Godot files")
    ap.add_argument("--pins", default=os.path.join(CUR, "..", "pins", "corpus_pins.json"))
    ap.add_argument("--files", nargs="*", help="parse these local files instead of the pinned Godot list")
    ap.add_argument("--top", type=int, default=40, help="how many identifier contexts to print")
    ap.add_argument("--json", default=None, help="also write the full census to this file")
    ap.add_argument("--lib", default=None)
    a = ap.parse_args()

    ts = tsbind.TreeSitter(tsbind.find_library(a.lib))
    c = {"files": 0, "files_with_error": 0, "missing_files": 0, "template_function": 0,
         "macro_like_declarators": 0, "function_definition": 0, "function_definition_error_free": 0,
         "ctx": collections.Counter(), "err_parent": collections.Counter(), "macro_names": collections.Counter()}
    if a.files:
        for p in a.files:
            with open(p, "rb") as f:
                census(f.read(), ts, c)
        label = "local files"
    else:
        with open(a.pins, encoding="utf-8") as f:
            pins = json.load(f)
        g = next(r for r in pins["repos"] if r["id"] == "godot")
        pin = g["pinned_commit"]
        lst = os.path.join(os.path.dirname(os.path.abspath(a.pins)), os.path.basename(g["new_files_list"]))
        with open(lst, encoding="utf-8") as f:
            paths = [ln.split("\t")[0] for ln in f.read().splitlines()[1:] if ln.strip()]
        ensure_clone(a.clone, g["repo"], pin)
        for p in paths:
            r = git("-C", a.clone, "show", "%s:%s" % (pin, p))
            if r.returncode:
                c["missing_files"] += 1      # deleted or renamed after it was added
                continue
            census(r.stdout, ts, c)
        label = "godot @ %s (%d listed paths)" % (pin[:12], len(paths))

    print("source: %s" % label)
    print("files parsed: %d   with parse error: %d   missing at pin: %d" % (c["files"], c["files_with_error"], c["missing_files"]))
    print("function_definition: %d   error-free: %d" % (c["function_definition"], c["function_definition_error_free"]))
    print("macro-like function_declarator (UPPER_SNAKE, no return type): %d  %s" % (
        c["macro_like_declarators"], c["macro_names"].most_common(5)))
    print("template_function nodes (templates, casts, or a<b comparisons parsed as templates): %d" % c["template_function"])
    print("error nodes by parent: %s" % c["err_parent"].most_common(8))
    print("\nidentifier contexts (count  node <- parent .field):")
    for (t, p, f), n in c["ctx"].most_common(a.top):
        print("%7d  %-20s <- %-30s .%s" % (n, t, p, f))
    if a.json:
        out = {k: v for k, v in c.items() if k not in ("ctx", "err_parent", "macro_names")}
        out["ctx"] = [[t, p, f, n] for (t, p, f), n in c["ctx"].most_common()]
        out["err_parent"] = c["err_parent"].most_common()
        out["macro_names"] = c["macro_names"].most_common()
        with open(a.json, "w", encoding="utf-8") as f:
            json.dump(out, f, indent=1)
        print("\nwrote %s" % a.json)


if __name__ == "__main__":
    main()
