#!/usr/bin/env python3
"""Evaluate the C++ scope resolver (scope_ts.analyse_cpp, scope_check.check_rename) on the pinned Godot corpus.

For every unit that curate.py would consider (6-40 lines, no ERROR overlap) and every rename target the extractor
plans (same selection as check_rename_roundtrip.py):

  differential  the identifier occurrences the resolver binds to the target's name (a declaration in the unit or
                an unqualified outside name) are compared with the spans curate.plan_rename plans to rename.
                plan_rename works by name, so it may also rename same-named members selected through `.`, `->`
                or `::`; those extra spans are expected to be bound as member selections ("attr") by the resolver
                and are counted separately. Any other disagreement is reported with examples.
  fresh name    renaming the target to an unused synthetic name must give status "ok" and no binding conflict.
  unsupported   units whose snippet has parse errors.

Read-only.

  python tools/eval_scope_check.py [--max-files N] [--examples K]
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
    ap.add_argument("--corpus", default=os.path.join(CUR, "..", "corpus_v2", "corpus", "cpp"))
    ap.add_argument("--max-files", type=int, default=0, help="0 = all files")
    ap.add_argument("--examples", type=int, default=3)
    a = ap.parse_args()

    import curate
    import lang_ts
    import scope_ts
    import tsbind
    from scope_check import check_rename
    from scope_common import IDENTITY

    ts = tsbind.TreeSitter(tsbind.find_library())
    files = sorted(glob.glob(os.path.join(a.corpus, "*.md")))
    if a.max_files:
        files = files[:a.max_files]
    cnt = collections.Counter()
    examples = collections.defaultdict(list)
    t0 = time.time()
    for fp in files:
        _meta, content = curate.parse_corpus_md(fp)
        if content is None:
            continue
        ff = lang_ts.extract("cpp", fp, content, ts)
        for u in ff.units:
            nl = u.end_line - u.start_line + 1
            if nl < curate.MIN_LINES or nl > curate.MAX_LINES:
                continue
            u_start, u_end = curate.unit_range(ff, u)
            if any(x < u_end and y > u_start for x, y in ff.error_spans):
                continue
            raw = ff.src[u_start:u_end]
            code = raw.decode("utf-8", errors="replace")
            ascii_only = len(raw) == len(code)

            def cpos(b):
                return b if ascii_only else len(raw[:b].decode("utf-8", errors="replace"))

            cnt["units"] += 1
            info = scope_ts.analyse_cpp(code, IDENTITY)
            if info["errors"]:
                cnt["unit_with_parse_errors"] += 1
                continue
            decls = [d for d in ff.decls if u_start <= d.start < u_end]
            toks = [t for t in ff.toks if u_start <= t.start < u_end]
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
                    continue
                cnt["targets"] += 1
                planned = {cpos(t.start - u_start) for t in spans}
                bound = {(o[-1] if o[0] == "r" else o[2]) for o, k in info["occ"].items()
                         if info["names"][o] == d.name and k[0] in ("src", "ext")}
                if planned == bound:
                    cnt["agree"] += 1
                else:
                    only_planned, only_bound = planned - bound, bound - planned
                    kinds = {k[0] for o, k in info["occ"].items()
                             if (o[-1] if o[0] == "r" else o[2]) in only_planned}
                    if not only_bound and kinds == {"attr"}:
                        cnt["planned_extra_member_spans"] += 1
                    else:
                        cnt["other_disagreement"] += 1
                        if len(examples["other"]) < a.examples:
                            examples["other"].append((os.path.basename(fp), u.label, d.name,
                                                      sorted(only_planned)[:4], sorted(only_bound)[:4]))
                res = check_rename("cpp", code, d.name, "zzFreshName")
                cnt["fresh_status_" + res["status"]] += 1
                if res["binding_conflict"]:
                    cnt["fresh_binding_conflict"] += 1
                    if len(examples["fresh"]) < a.examples:
                        examples["fresh"].append((os.path.basename(fp), u.label, d.name, res["binding_reasons"][:1]))
    print("files %d, %.0fs" % (len(files), time.time() - t0))
    for k in sorted(cnt):
        print("  %-30s %d" % (k, cnt[k]))
    for k, v in examples.items():
        print("examples:", k)
        for e in v:
            print("  ", e)
    ok = cnt["other_disagreement"] == 0 and cnt["fresh_binding_conflict"] == 0 \
        and cnt["fresh_status_ok"] == cnt["targets"]
    print("PASS" if ok else "FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
