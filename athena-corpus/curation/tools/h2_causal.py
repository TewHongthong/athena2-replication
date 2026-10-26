#!/usr/bin/env python3
"""H2 causal test (Athena Vol. 2, WP2). Read-only; standard library + tsbind only.

Question: do the macros _FORCE_INLINE_ / _ALWAYS_INLINE_ cause the tree-sitter-cpp ERROR nodes inside
function_definition? Each pinned Godot .cpp/.h file is parsed twice: as-is, and with those two macros replaced
by `inline` padded with spaces to the same byte length (every byte offset is unchanged). Functions are paired
across the two parses by the start byte of their body (the node start can differ when a leading macro is
mis-parsed). Nothing is written; file contents come from git objects at the pin, not from a working tree.

  python tools/h2_causal.py [--clone ~/.cache/athena2/godot.git] [--pin 5ec712e220b7]

"has error" for a node = the node or any descendant is_error / is_missing (what ts_node_has_error reports;
tsbind.Node does not carry has_error itself). Range = 6..40 lines, end - start + 1 of the function_definition node
of that parse. Header candidate (criteria definition, function level) = function_definition in a .h file that is in
range; it survives if it has no error (before / after counted separately). The file-level variant (.h files with
>= 1 candidate / >= 1 surviving) is printed on its own line for comparison only.
"""
import argparse
import bisect
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
CUR = os.path.dirname(HERE)
sys.path.insert(0, CUR)
import tsbind  # noqa: E402

LO, HI = 6, 40
MACRO = re.compile(rb"(?<![A-Za-z0-9_])(_FORCE_INLINE_|_ALWAYS_INLINE_)(?![A-Za-z0-9_])")

# criteria from the cloud run of 15 Oct 2026 (tree-sitter v0.27.1 + tree-sitter-cpp c0092228)
CRITERIA = [
    ("files", 167), ("fd_total", 1995), ("before_err", 60), ("before_range", 798),
    ("before_range_ok", 771), ("before_range_fail", 27), ("hdr_fn_cand", 45), ("hdr_fn_ok_before", 23),
    ("after_err", 14), ("after_range_fail", 10), ("hdr_fn_ok_after", 39), ("newly_err", 0),
]


def git(*args):
    return subprocess.run(["git", *args], capture_output=True)


def substitute(src):
    return MACRO.sub(lambda m: b"inline" + b" " * (len(m.group(1)) - 6), src)


def has_error(n):
    return any(x.is_error or x.is_missing for x in n.walk())


def functions(ts, src):
    """-> list of dicts for every function_definition: key (body start byte or None), err, line, size."""
    root, _ = ts.parse("cpp", src)
    nl = [i for i, b in enumerate(src) if b == 10]
    ln = lambda off: bisect.bisect_left(nl, off) + 1   # 1-based line of a byte offset
    out = []
    for n in root.walk():
        if n.type != "function_definition":
            continue
        body = n.child("body")
        out.append({"key": body.start if body is not None else None, "err": has_error(n),
                    "line": ln(n.start), "size": ln(max(n.end - 1, n.start)) - ln(n.start) + 1})
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--clone", default=os.path.expanduser("~/.cache/athena2/godot.git"))
    ap.add_argument("--pin", default="5ec712e220b7")
    ap.add_argument("--list", default=os.path.join(CUR, "..", "pins", "godot_new_files.tsv"))
    ap.add_argument("--lib", default=None)
    a = ap.parse_args()

    r = git("-C", a.clone, "rev-parse", "--verify", "-q", a.pin + "^{commit}")
    if r.returncode:
        sys.exit("pin %s not found in %s (this script never fetches)" % (a.pin, a.clone))
    pin = r.stdout.decode().strip()
    with open(a.list, encoding="utf-8") as f:
        rows = [ln.split("\t") for ln in f.read().splitlines()[1:] if ln.strip()]
    paths = [p[0] for p in rows if p[0].endswith((".cpp", ".h"))]

    ts = tsbind.TreeSitter(tsbind.find_library(a.lib))
    m = dict.fromkeys([k for k, _ in CRITERIA], 0)
    missing, nokey, unpaired = [], 0, 0
    still, newly = [], []
    hdr = {}          # path -> [before_cand, before_ok, after_cand, after_ok]  (file level, comparison only)
    fn = dict.fromkeys(("hdr_fn_cand", "hdr_fn_ok_before", "hdr_fn_ok_after"), 0)
    range_changed = 0
    n_changed_files = 0

    for p in paths:
        g = git("-C", a.clone, "show", "%s:%s" % (pin, p))
        if g.returncode:
            missing.append(p)
            continue
        src = g.stdout
        new = substitute(src)
        assert len(new) == len(src)
        n_changed_files += new != src
        m["files"] += 1
        before, after = functions(ts, src), functions(ts, new)
        nokey += sum(f["key"] is None for f in before)
        A = {f["key"]: f for f in after if f["key"] is not None}
        B = {f["key"]: f for f in before if f["key"] is not None}
        unpaired += len(B.keys() ^ A.keys())
        m["fd_total"] += len(before)
        h = hdr.setdefault(p, [0, 0, 0, 0])
        for f in before:
            m["before_err"] += f["err"]
            if LO <= f["size"] <= HI:
                m["before_range"] += 1
                m["before_range_fail"] += f["err"]
                m["before_range_ok"] += not f["err"]
                h[0] = 1
                h[1] |= not f["err"]
                if p.endswith(".h"):
                    fn["hdr_fn_cand"] += 1
                    fn["hdr_fn_ok_before"] += not f["err"]
        for f in after:
            m["after_err"] += f["err"]
            if LO <= f["size"] <= HI:
                m["after_range_fail"] += f["err"]
                h[2] = 1
                h[3] |= not f["err"]
                if p.endswith(".h"):
                    fn["hdr_fn_ok_after"] += not f["err"]
            if f["err"]:
                still.append((p, f["line"], f["size"]))
        for k, f in A.items():
            b = B.get(k)
            if b is None:
                continue
            if f["err"] and not b["err"]:
                m["newly_err"] += 1
                newly.append((p, f["line"], f["size"]))
            range_changed += (LO <= b["size"] <= HI) != (LO <= f["size"] <= HI)

    heads = [v for pth, v in hdr.items() if pth.endswith(".h")]
    m.update(fn)

    print("pin %s   clone %s" % (pin[:12], a.clone))
    print("listed .cpp/.h: %d   missing at pin: %d   files with a substituted macro: %d" % (
        len(paths), len(missing), n_changed_files))
    print("function_definition without body (cannot pair): %d   present in only one parse: %d   "
          "range membership changed by the substitution: %d" % (nokey, unpaired, range_changed))
    print("header, file level (comparison only; cand / ok before / ok after): %d / %d / %d" % (
        sum(v[0] for v in heads), sum(v[1] for v in heads), sum(v[3] for v in heads)))
    print("header, function level (criteria; cand / ok before / ok after): %d / %d / %d" % (
        fn["hdr_fn_cand"], fn["hdr_fn_ok_before"], fn["hdr_fn_ok_after"]))
    print("\nstill ERROR after substitution (file:line:lines), %d:" % len(still))
    for p, l, s in still:
        print("  %s:%d:%d" % (p, l, s))
    if newly:
        print("\nnewly ERROR after substitution, %d:" % len(newly))
        for p, l, s in newly:
            print("  %s:%d:%d" % (p, l, s))
    print("\n%-18s %8s %8s  %s" % ("metric", "measured", "criteria", ""))
    ok = True
    for k, want in CRITERIA:
        good = m[k] == want
        ok &= good
        print("%-18s %8d %8d  %s" % (k, m[k], want, "match" if good else "MISMATCH"))
    print("\nALL MATCH" if ok else "\nMISMATCH present - report only, nothing adjusted")


if __name__ == "__main__":
    main()
