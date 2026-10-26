#!/usr/bin/env python3
"""Snippet-only kind inference vs the file-level extractor kind, on a fetched corpus (read-only).

For each candidate unit (6-40 lines, no parse-error span) of each corpus file, every declaration inside the unit
that the extractor labels (kind not None, not exempt) is looked up again from the unit text ALONE.  The file-level
extractor sees the whole file; the inference sees only what the model would be shown.  Agreement here measures
the information lost by cutting the snippet, not the correctness of either label against an ontology.

  python3 tools/eval_kind_snippet_vs_file.py --lang cpp --corpus ../corpus_v2/corpus/cpp [--limit N] [--out f.json]
"""
import argparse, collections, glob, json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
CUR = os.path.dirname(HERE)
sys.path.insert(0, CUR)
import curate  # noqa: E402
import kind_infer  # noqa: E402
import tsbind  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("--lang", required=True)
ap.add_argument("--corpus", required=True)
ap.add_argument("--limit", type=int, default=0)
ap.add_argument("--out", default=None)
a = ap.parse_args()

TS = tsbind.TreeSitter(tsbind.find_library(os.path.join(CUR, "libtsall.so")))
rows, nfiles = [], 0
for path in sorted(glob.glob(os.path.join(a.corpus, "*.md"))):
    meta, content = curate.parse_corpus_md(path)
    if content is None:
        continue
    ff = curate.analyze(a.lang, meta.get("path", "x"), content, TS)
    if not ff.parse_ok:
        continue
    nfiles += 1
    for u in ff.units:
        if not (6 <= u.end_line - u.start_line + 1 <= 40):
            continue
        s, e = curate.unit_range(ff, u)
        if any(es < e and ee > s for es, ee in ff.error_spans):
            continue
        text = curate.unit_text(ff.src, ff.line_starts, u.start_line, u.end_line)
        inside = [d for d in ff.decls if s <= d.start < e and d.kind is not None and not d.exempt]
        count = collections.Counter(d.name for d in inside)
        for d in inside:
            if count[d.name] != 1 or len(d.name) < 3:
                continue
            r = kind_infer.infer_kind(a.lang, text, d.name)
            rows.append(dict(file=os.path.basename(path), unit=u.label, name=d.name, file_kind=d.kind,
                             cpp_kind=d.extra.get("cpp_kind"), pred=r.kind, status=r.status, alt=r.detail.get("alt_kinds", [])))
    if a.limit and nfiles >= a.limit:
        break

n = len(rows)
ok = sum(r["pred"] == r["file_kind"] for r in rows)
print(f"files={nfiles} declarations={n} agree={ok} ({100*ok/n:.1f}%)")
print("status:", dict(collections.Counter(r["status"] for r in rows)))
by = collections.defaultdict(lambda: [0, 0])
for r in rows:
    by[r["file_kind"]][0] += 1
    by[r["file_kind"]][1] += r["pred"] == r["file_kind"]
for k, (t, g) in sorted(by.items(), key=lambda x: -x[1][0]):
    print(f"  {k:12s} {g}/{t} ({100*g/t:.1f}%)")
conf = collections.Counter((r["file_kind"], r["pred"], r["status"]) for r in rows if r["pred"] != r["file_kind"])
for (g, p, s), c in conf.most_common(15):
    print(f"  file={g:11s} snippet={str(p):11s} {s:10s} {c}")
if a.out:
    json.dump(rows, open(a.out, "w"), indent=1)
