"""Count Godot parameter trials whose proposed name lacks the p_ or r_ prefix.

Usage:
    python count_godot_prefix.py runs/test_godot_*_meta

Reads trials.jsonl of each directory given. Only trials of kind parameter that
have a proposed name and did not end in an error are counted. A prefix miss is
a proposed name that does not start with p_ or r_. Whether the prefix is the
right one of the two is not checked. The output is descriptive.
"""
import argparse
import collections
import glob
import json
import math
import os

PREFIXES = ("p_", "r_")


def wilson(k, n, z=1.96):
    if n == 0:
        return (float("nan"), float("nan"))
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (c - h, c + h)


def load(patterns):
    rows, skipped = [], collections.Counter()
    for pat in patterns:
        for d in sorted(glob.glob(pat)):
            path = os.path.join(d, "trials.jsonl")
            if not os.path.isfile(path):
                continue
            with open(path, encoding="utf-8") as fh:
                for line in fh:
                    if not line.strip():
                        continue
                    t = json.loads(line)
                    if t.get("kind") != "parameter":
                        skipped["other_kind"] += 1
                        continue
                    if t.get("error"):
                        skipped["error"] += 1
                        continue
                    name = (t.get("parsed") or {}).get("suggested_name")
                    m = t.get("metrics")
                    if not isinstance(name, str) or not name.strip() or not m or "core_ok" not in m:
                        skipped["no_name"] += 1
                        continue
                    name = name.strip()
                    rows.append({
                        "model": t.get("model"), "condition": t.get("condition"),
                        "task": t.get("unit_id"),
                        "original": t.get("original") or "",
                        "core_ok": bool(m["core_ok"]),
                        "miss": not name.startswith(PREFIXES),
                    })
    return rows, skipped


def fmt(k, n):
    if n == 0:
        return "0/0"
    lo, hi = wilson(k, n)
    return "%d/%d = %.1f%% (Wilson 95%% %.1f to %.1f)" % (k, n, 100.0 * k / n, 100 * lo, 100 * hi)


def report(rows, skipped):
    out = []
    out.append("Counted parameter trials: %d" % len(rows))
    out.append("Not counted: " + ", ".join("%s %d" % kv for kv in sorted(skipped.items())))
    ok = [r for r in rows if r["core_ok"]]
    out.append("")
    out.append("Prefix miss among core_ok = 1: " + fmt(sum(r["miss"] for r in ok), len(ok)))
    out.append("Prefix miss among all counted: " + fmt(sum(r["miss"] for r in rows), len(rows)))
    for label in ("condition", "model"):
        out.append("")
        out.append("By %s (core_ok = 1 trials):" % label)
        groups = collections.defaultdict(list)
        for r in ok:
            groups[r[label]].append(r)
        for g in sorted(groups, key=str):
            out.append("  %-28s %s" % (g, fmt(sum(r["miss"] for r in groups[g]), len(groups[g]))))
    tasks = {}
    for r in rows:
        tasks[r["task"]] = r["original"]
    pref = sum(1 for o in tasks.values() if o.startswith(PREFIXES))
    out.append("")
    out.append("Original names that start with p_ or r_: %d of %d tasks" % (pref, len(tasks)))
    return "\n".join(out)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("runs", nargs="+", help="run directories (globs) that hold trials.jsonl")
    ap.add_argument("--json", help="also write the counts to this file")
    a = ap.parse_args(argv)
    rows, skipped = load(a.runs)
    print(report(rows, skipped))
    if a.json:
        with open(a.json, "w", encoding="utf-8") as fh:
            json.dump({"counted": len(rows), "skipped": dict(skipped),
                       "miss_core_ok": sum(r["miss"] for r in rows if r["core_ok"]),
                       "core_ok": sum(r["core_ok"] for r in rows),
                       "miss_all": sum(r["miss"] for r in rows)}, fh, indent=2)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
