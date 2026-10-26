#!/usr/bin/env python3
"""Kind inference vs the Vol. 1 Public5 gold kind (read-only; Vol. 1 data is development material for Vol. 2).

  python3 tools/eval_kind_public5.py --v1 <project2>/coding/athena-corpus/benchmark --units <p5_units.txt> --split dev
  --split dev  : every violation whose unit id is NOT in --units  (use while developing)
  --split test : the units in --units (the 100 Vol. 1 test units; look at this once)
"""
import argparse, collections, glob, json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
import kind_infer  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("--v1", required=True)
ap.add_argument("--units", required=True)
ap.add_argument("--split", choices=["dev", "test"], default="dev")
ap.add_argument("--out", default=None)
ap.add_argument("--langs", nargs="*", default=None)
a = ap.parse_args()

test_ids = set(open(a.units).read().split())
rows = []
for f in sorted(glob.glob(os.path.join(a.v1, "violations", "*", "*.json"))):
    uid = os.path.basename(f)[:-5]
    if (uid in test_ids) != (a.split == "test"):
        continue
    v = json.load(open(f))
    if a.langs and v["language"] not in a.langs:
        continue
    r = kind_infer.infer_kind(v["language"], v["codeContextWithViolation"], v["injectedName"])
    rows.append(dict(uid=uid, lang=v["language"], gold=v["identifierKind"], pred=r.kind, status=r.status,
                     alt=r.detail.get("alt_kinds", []), why=r.reason, name=v["injectedName"]))

n = len(rows)
ok = sum(r["pred"] == r["gold"] for r in rows)
ok_alt = sum(r["gold"] in ([r["pred"]] + r["alt"]) for r in rows)
print(f"split={a.split} n={n} exact={ok} ({100*ok/n:.1f}%)  gold-in-{{pred+alt}}={ok_alt} ({100*ok_alt/n:.1f}%)")
print("status:", dict(collections.Counter(r["status"] for r in rows)))
by = collections.defaultdict(lambda: [0, 0])
for r in rows:
    by[r["lang"]][0] += 1
    by[r["lang"]][1] += r["pred"] == r["gold"]
for l, (t, k) in sorted(by.items()):
    print(f"  {l:11s} {k}/{t} ({100*k/t:.1f}%)")
conf = collections.Counter((r["gold"], r["pred"], r["status"]) for r in rows if r["pred"] != r["gold"])
print("mismatches (gold, pred, status): count")
for (g, p, s), c in conf.most_common(25):
    print(f"  {g:17s} -> {str(p):17s} {s:12s} {c}")
if a.out:
    json.dump(rows, open(a.out, "w"), indent=1)
