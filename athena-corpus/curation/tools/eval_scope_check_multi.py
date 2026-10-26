#!/usr/bin/env python3
"""Unit census and scope-check evaluation for C# and Python on a fetched corpus (read-only).

For every unit that curate.py would consider (6-40 lines, no ERROR overlap) and every rename target the extractor
plans (same selection as eval_scope_check.py for C++):

  census          files read, files the front end rejects, units kept, units dropped for a parse-error overlap
                  (the unit count is comparable with `units_eligible` in pins/<id>_units.tsv)
  fresh name      renaming the target to an unused synthetic name must give status "ok" and no binding conflict;
                  `unsupported` (the snippet does not parse on its own) is counted per unit kind
  occurrences     the number of whole-word occurrences the rename touches is compared with the number of token spans
                  curate.plan_rename plans; a difference means that the name also occurs in comments or string
                  literals (or as a member of another object), not that a binding is wrong

The Python front end uses `ast` and `symtable` of the running interpreter, so the Python version must be at least
the one the corpus targets (Odoo uses PEP 695 syntax and nested f-string quotes: Python 3.12 or later).

  python3 tools/eval_scope_check_multi.py --lang csharp|python [--corpus DIR] [--max-files N] [--skip N]
"""
import argparse
import collections
import glob
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
CUR = os.path.dirname(HERE)
sys.path.insert(0, CUR)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--lang", required=True, choices=["csharp", "python"])
    ap.add_argument("--corpus", default=None, help="default: ../corpus_v2/corpus/<lang>")
    ap.add_argument("--max-files", type=int, default=0, help="0 = all files")
    ap.add_argument("--skip", type=int, default=0)
    ap.add_argument("--examples", type=int, default=3)
    a = ap.parse_args()

    import curate
    import tsbind
    from scope_check import check_rename

    corpus = a.corpus or os.path.join(CUR, "..", "corpus_v2", "corpus", a.lang)
    ts = tsbind.TreeSitter(tsbind.find_library(os.path.join(CUR, "libtsall.so")))
    files = sorted(glob.glob(os.path.join(corpus, "*.md")))[a.skip:]
    if a.max_files:
        files = files[:a.max_files]
    cnt = collections.Counter()
    by_kind = collections.Counter()
    examples = collections.defaultdict(list)
    t0 = time.time()
    for fp in files:
        meta, content = curate.parse_corpus_md(fp)
        if content is None:
            continue
        ff = curate.analyze(a.lang, meta.get("path", "x"), content, ts)
        cnt["files"] += 1
        if not ff.parse_ok:
            cnt["files_rejected_by_front_end"] += 1
            continue
        for u in ff.units:
            if not curate.MIN_LINES <= u.end_line - u.start_line + 1 <= curate.MAX_LINES:
                continue
            s, e = curate.unit_range(ff, u)
            if any(x < e and y > s for x, y in ff.error_spans):
                cnt["units_dropped_parse_error"] += 1
                continue
            cnt["units"] += 1
            ukind = u.label.split()[0]
            text = curate.unit_text(ff.src, ff.line_starts, u.start_line, u.end_line)
            decls = [d for d in ff.decls if s <= d.start < e]
            toks = [t for t in ff.toks if s <= t.start < e]
            seen, n_targets = set(), 0
            for d in sorted(decls, key=lambda x: x.start):
                if d.kind is None or d.exempt or d.name in seen or len(d.name) < curate.MIN_TARGET_LEN:
                    continue
                seen.add(d.name)
                if n_targets >= curate.MAX_TARGETS:
                    break
                n_targets += 1
                spans, _why = curate.plan_rename(ff.language, ff, decls, toks, d)
                if spans is None:
                    cnt["targets_not_plannable"] += 1
                    continue
                cnt["targets"] += 1
                res = check_rename(a.lang, text, d.name, "zzFreshName")
                cnt["fresh_status_" + res["status"]] += 1
                by_kind[(ukind, "conflict" if res["binding_conflict"] else res["status"])] += 1
                if res["status"] == "unsupported" and len(examples["unsupported"]) < a.examples:
                    examples["unsupported"].append((os.path.basename(fp), u.label, res["unsupported_reason"][:60]))
                if res["binding_conflict"]:
                    cnt["fresh_binding_conflict"] += 1
                    if len(examples["conflict"]) < a.examples:
                        examples["conflict"].append((os.path.basename(fp), u.label, d.name, res["binding_reasons"][:1]))
                if res["status"] == "ok":
                    if res["occurrences_renamed"] == len(spans):
                        cnt["occurrence_count_match"] += 1
                    else:
                        cnt["occurrence_count_differs"] += 1
                        if len(examples["differs"]) < a.examples:
                            examples["differs"].append((os.path.basename(fp), u.label, d.name,
                                                        res["occurrences_renamed"], len(spans)))
    print("python %s, lang %s, files %d, %.0fs" % (sys.version.split()[0], a.lang, len(files), time.time() - t0))
    for k in sorted(cnt):
        print("  %-32s %d" % (k, cnt[k]))
    print("by unit kind and outcome:")
    for k in sorted(by_kind):
        print("  %-12s %-12s %d" % (k[0], k[1], by_kind[k]))
    for k, v in examples.items():
        print("examples:", k)
        for e in v:
            print("  ", e)


if __name__ == "__main__":
    main()
