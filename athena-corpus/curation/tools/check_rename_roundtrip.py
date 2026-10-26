#!/usr/bin/env python3
"""A4 (and A2) for the C++ extractor, without the ontology (CPP_EXTRACTOR_PLAN.md section 6).

For every unit that curate.py would consider (6-40 lines, no ERROR overlap) in the pinned Godot files, take each
decl the extractor emitted (kind not None, not exempt, name length >= MIN_TARGET_LEN, one per name, at most
MAX_TARGETS per unit), run curate.plan_rename, rewrite the planned spans to a synthetic name, and re-parse with
ff.reverify. Pass criteria:
  A4: no shape change after rename, and every reject carries a named reason (never empty)
  A2: no extractor exception; every function_definition without an ERROR node got a UnitCand
Read-only; the synthetic name is never an ontology name.

  python tools/check_rename_roundtrip.py [--max-files N] [--clone DIR] [--examples K]
"""
import argparse
import collections
import json
import os
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
CUR = os.path.dirname(HERE)
sys.path.insert(0, CUR)
sys.path.insert(0, HERE)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--clone", default=os.path.expanduser("~/.cache/athena2/godot.git"))
    ap.add_argument("--pins", default=os.path.join(CUR, "..", "pins", "corpus_pins.json"))
    ap.add_argument("--max-files", type=int, default=0, help="0 = all pinned files")
    ap.add_argument("--examples", type=int, default=3, help="examples to print per reject reason")
    a = ap.parse_args()

    import curate  # noqa: E402
    import facts  # noqa: E402
    import lang_ts  # noqa: E402
    import tsbind  # noqa: E402
    import cpp_census as cc  # noqa: E402
    ts = tsbind.TreeSitter(tsbind.find_library())

    with open(a.pins, encoding="utf-8") as f:
        g = next(r for r in json.load(f)["repos"] if r["id"] == "godot")
    pin = g["pinned_commit"]
    lst = os.path.join(os.path.dirname(os.path.abspath(a.pins)), os.path.basename(g["new_files_list"]))
    with open(lst, encoding="utf-8") as f:
        paths = [ln.split("\t")[0] for ln in f.read().splitlines()[1:] if ln.strip()]
    cc.ensure_clone(a.clone, g["repo"], pin)
    if a.max_files:
        paths = paths[:a.max_files]

    c = collections.Counter()
    rejects = collections.Counter()
    examples = collections.defaultdict(list)
    missing_units, exceptions, changed, empty_reason = [], [], [], []
    t0 = time.time()
    for p in paths:
        r = subprocess.run(["git", "-C", a.clone, "show", "%s:%s" % (pin, p)], capture_output=True)
        if r.returncode != 0:
            continue
        src = r.stdout
        c["files"] += 1
        try:
            ff = lang_ts.extract("cpp", p, src, ts)
        except Exception as e:  # noqa: BLE001
            exceptions.append((p, "%s: %s" % (type(e).__name__, e)))
            continue
        # ---- A2: every error-free function_definition has a unit
        root, _ = ts.parse("cpp", src)
        want = set()
        for n in root.walk():
            if n.type == "function_definition":
                c["function_definition"] += 1
                if any(x.is_error or x.is_missing for x in n.walk()):
                    c["function_definition_with_error"] += 1
                    continue
                s = facts.line_of(ff.line_starts, n.start)
                e = facts.line_of(ff.line_starts, max(n.end - 1, n.start))
                want.add((s, e))
        have = {(u.start_line, u.end_line) for u in ff.units}
        c["fd_error_free"] += len(want)
        for w in sorted(want - have):
            missing_units.append((p, w))
        # ---- A4: rename round-trip
        used_names = {t.text for t in ff.toks}
        for u in ff.units:
            nl = u.end_line - u.start_line + 1
            if nl < curate.MIN_LINES or nl > curate.MAX_LINES:
                continue
            u_start, u_end = curate.unit_range(ff, u)
            if any(x < u_end and y > u_start for x, y in ff.error_spans):
                continue
            c["units_considered"] += 1
            decls = [d for d in ff.decls if u_start <= d.start < u_end]
            toks = [t for t in ff.toks if u_start <= t.start < u_end]
            seen, n_t = set(), 0
            for d in sorted(decls, key=lambda x: x.start):
                if d.kind is None or d.exempt or d.name in seen or len(d.name) < curate.MIN_TARGET_LEN:
                    continue
                seen.add(d.name)
                if n_t >= curate.MAX_TARGETS:
                    break
                n_t += 1
                c["targets"] += 1
                spans, why = curate.plan_rename(ff.language, ff, decls, toks, d)
                if spans is None:
                    if not why:
                        empty_reason.append((p, d.name))
                        why = "<EMPTY>"
                    rejects[why] += 1
                    if len(examples[why]) < a.examples:
                        examples[why].append("%s:%d %s %s" % (
                            p, facts.line_of(ff.line_starts, d.start) + 1, d.name, d.extra.get("cpp_kind")))
                    continue
                c["planned"] += 1
                new = "rt%d_x" % c["planned"]
                while new in used_names:
                    new += "_"
                new_src = curate.apply_edits(ff.src, [(t.start, t.end) for t in spans], new)
                fp = ff.reverify(new_src)
                same = (fp[0] == ff.shape) and (not fp[1] or bool(ff.error_spans))
                if same:
                    c["roundtrip_ok"] += 1
                else:
                    c["shape_changed"] += 1
                    changed.append("%s:%d %s %s" % (p, facts.line_of(ff.line_starts, d.start) + 1, d.name,
                                                    d.extra.get("cpp_kind")))
    print("files=%d  function_definition=%d (with ERROR %d, error-free %d)  [%.0fs]" % (
        c["files"], c["function_definition"], c["function_definition_with_error"], c["fd_error_free"],
        time.time() - t0))
    print("A2: extractor exceptions=%d  error-free function_definition without UnitCand=%d  => %s" % (
        len(exceptions), len(missing_units), "PASS" if not exceptions and not missing_units else "FAIL"))
    for x in (exceptions + missing_units)[:10]:
        print("   ", x)
    print("A4: units considered=%d  targets=%d  planned=%d  round-trip ok=%d  shape changed=%d  empty-reason rejects=%d"
          "  => %s" % (c["units_considered"], c["targets"], c["planned"], c["roundtrip_ok"], c["shape_changed"],
                       len(empty_reason), "PASS" if not changed and not empty_reason else "FAIL"))
    print("   rejects by reason:")
    for why, n in rejects.most_common():
        print("     %-34s %d" % (why, n))
        for ex in examples[why]:
            print("        e.g. %s" % ex)
    for x in changed[:10]:
        print("   SHAPE CHANGED:", x)
    for x in empty_reason[:10]:
        print("   EMPTY REASON:", x)
    sys.exit(0 if not exceptions and not missing_units and not changed and not empty_reason else 1)


if __name__ == "__main__":
    main()
