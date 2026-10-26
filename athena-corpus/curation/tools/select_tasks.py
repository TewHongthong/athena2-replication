#!/usr/bin/env python3
"""Select the B1 tasks of one pack: dev/test split by path hash, then seeded sampling with a per-file cap.

Input is the pool of one pack: the units that passed the criteria (size, parse, identifier-consistency gate, injection
possible). A tab-separated file with a header and at least two columns:

  path          path of the file (as in the `path` column of pins/<id>_units.tsv)
  unit_index    integer, the order of the unit within its file

Any other columns are copied to the output unchanged. One row is one unit, and one unit is one task.

Procedure (fixed in HYPOTHESES_v2, D12 and D13):

  split      SHA-256 of the UTF-8 path, read as an integer, mod 100: value < 30 is dev, the rest is test. All units of
             a file fall on the same side.
  order      per side, sort the pool by (path, unit_index) and shuffle with random.Random("athena2-b1-v1:<pack>:<side>").
  draw       take units in shuffled order, skipping a unit whose file has already been taken `cap` times, until the
             target is reached. No unit is borrowed across sides.
  target     S = 100 tasks per pack: 30 on dev and 70 on test.
  cap        3 per file. If a side cannot reach its target at 3, the same shuffled order is used again at 4 and then 5.
  reduction  if a side is still short at 5, S' is the largest integer below 100 for which both sides can reach their
             targets at some cap in {3, 4, 5}, with dev = floor(0.3 * S') and test = S' - dev. Each side then uses the
             smallest cap that reaches its own target.

Outputs in --out-dir: <pack>_selection.tsv (the selected units, in draw order) and <pack>_selection_report.json (the cap
used per side, S', the pool and capacity per side, the number of files and the largest number of tasks per file).

  python3 tools/select_tasks.py --pack godot --pool godot_pool.tsv --out-dir selection/
"""
import argparse
import collections
import csv
import hashlib
import json
import os
import random
import sys

SEED = "athena2-b1-v1"
S_TARGET = 100
DEV_PERCENT = 30
CAPS = (3, 4, 5)
SIDES = ("dev", "test")


class SelectionError(Exception):
    pass


def side_of(path):
    """Return "dev" or "test" for a file path (SHA-256 of the UTF-8 path, mod 100, no salt)."""
    value = int(hashlib.sha256(path.encode("utf-8")).hexdigest(), 16) % 100
    return "dev" if value < DEV_PERCENT else "test"


def targets(s):
    """Return the task count per side for a pack size s: dev = floor(0.3 * s), test = s - dev."""
    dev = s * DEV_PERCENT // 100
    return {"dev": dev, "test": s - dev}


def load_pool(path):
    """Read a pool file and return (extra column names, units). A unit is a dict with path, unit_index and extra."""
    with open(path, newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh, delimiter="\t")
        fields = reader.fieldnames or []
        for col in ("path", "unit_index"):
            if col not in fields:
                raise SelectionError("pool file has no column %r" % col)
        extra_cols = [c for c in fields if c not in ("path", "unit_index")]
        units = []
        seen = set()
        for line_no, row in enumerate(reader, start=2):
            p = row["path"]
            if not p:
                raise SelectionError("line %d: empty path" % line_no)
            try:
                idx = int(row["unit_index"])
            except (TypeError, ValueError):
                raise SelectionError("line %d: unit_index is not an integer" % line_no)
            if (p, idx) in seen:
                raise SelectionError("line %d: duplicate unit (%s, %d)" % (line_no, p, idx))
            seen.add((p, idx))
            units.append({"path": p, "unit_index": idx, "extra": [row[c] for c in extra_cols]})
    return extra_cols, units


def split_pool(units):
    """Group units by side and sort each side by (path, unit_index)."""
    by_side = {side: [] for side in SIDES}
    for u in units:
        by_side[side_of(u["path"])].append(u)
    for side in SIDES:
        by_side[side].sort(key=lambda u: (u["path"], u["unit_index"]))
    return by_side


def shuffled(units, pack, side):
    """The fixed draw order of one pack and side."""
    out = list(units)
    random.Random("%s:%s:%s" % (SEED, pack, side)).shuffle(out)
    return out


def capacity(units, cap):
    """The most tasks a side can give at a per-file cap: the sum over files of min(units in the file, cap)."""
    per_file = collections.Counter(u["path"] for u in units)
    return sum(min(n, cap) for n in per_file.values())


def smallest_cap(cap_table, target):
    """The smallest cap in CAPS whose capacity reaches the target, or None."""
    for cap in CAPS:
        if cap_table[cap] >= target:
            return cap
    return None


def draw(order, target, cap):
    """Take units in the given order, skipping units of a file already taken `cap` times, until the target is reached."""
    taken = collections.Counter()
    chosen = []
    for u in order:
        if len(chosen) >= target:
            break
        if taken[u["path"]] >= cap:
            continue
        taken[u["path"]] += 1
        chosen.append(u)
    return chosen


def plan(by_side, s_target=S_TARGET):
    """Find the pack size S' and the cap per side. Returns (s_used, targets, cap per side, capacity table per side)."""
    cap_tables = {side: {cap: capacity(by_side[side], cap) for cap in CAPS} for side in SIDES}
    for s in range(s_target, 0, -1):
        t = targets(s)
        caps = {side: smallest_cap(cap_tables[side], t[side]) for side in SIDES}
        if all(c is not None for c in caps.values()):
            return s, t, caps, cap_tables
    raise SelectionError("the pool cannot give even one task at a cap of %d" % CAPS[-1])


def select(units, pack, s_target=S_TARGET):
    """Select the tasks of one pack. Returns (selected per side in draw order, report dict)."""
    by_side = split_pool(units)
    s_used, t, caps, cap_tables = plan(by_side, s_target)
    selected = {}
    report = {
        "pack": pack,
        "seed": SEED,
        "s_target": s_target,
        "s_used": s_used,
        "reduced": s_used < s_target,
        "sides": {},
    }
    for side in SIDES:
        order = shuffled(by_side[side], pack, side)
        chosen = draw(order, t[side], caps[side])
        if len(chosen) != t[side]:
            raise SelectionError("internal error: %s side drew %d of %d" % (side, len(chosen), t[side]))
        selected[side] = chosen
        per_file = collections.Counter(u["path"] for u in chosen)
        report["sides"][side] = {
            "target": t[side],
            "cap_used": caps[side],
            "cap_relaxed": caps[side] > CAPS[0],
            "pool_units": len(by_side[side]),
            "pool_files": len({u["path"] for u in by_side[side]}),
            "capacity_by_cap": {str(c): cap_tables[side][c] for c in CAPS},
            "selected": len(chosen),
            "selected_files": len(per_file),
            "max_per_file": max(per_file.values()) if per_file else 0,
        }
    return selected, report


def write_outputs(out_dir, pack, extra_cols, selected, report):
    os.makedirs(out_dir, exist_ok=True)
    sel_path = os.path.join(out_dir, "%s_selection.tsv" % pack)
    with open(sel_path, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh, delimiter="\t", lineterminator="\n")
        w.writerow(["pack", "side", "rank", "path", "unit_index"] + extra_cols)
        for side in SIDES:
            for rank, u in enumerate(selected[side], start=1):
                w.writerow([pack, side, rank, u["path"], u["unit_index"]] + u["extra"])
    rep_path = os.path.join(out_dir, "%s_selection_report.json" % pack)
    with open(rep_path, "w", encoding="utf-8") as fh:
        json.dump(report, fh, indent=2, sort_keys=True)
        fh.write("\n")
    return sel_path, rep_path


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--pack", required=True, help="pack id, part of the shuffle seed (for example godot)")
    ap.add_argument("--pool", required=True, help="pool TSV (columns path, unit_index, ...)")
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--size", type=int, default=S_TARGET, help="tasks per pack (default %d)" % S_TARGET)
    a = ap.parse_args(argv)
    try:
        extra_cols, units = load_pool(a.pool)
        selected, report = select(units, a.pack, a.size)
    except SelectionError as e:
        print("error: %s" % e, file=sys.stderr)
        return 2
    sel_path, rep_path = write_outputs(a.out_dir, a.pack, extra_cols, selected, report)
    for side in SIDES:
        r = report["sides"][side]
        print("%s %-4s selected %3d of target %3d  cap %d  files %3d  max per file %d  pool %4d units / %3d files"
              % (a.pack, side, r["selected"], r["target"], r["cap_used"], r["selected_files"], r["max_per_file"],
                 r["pool_units"], r["pool_files"]))
    if report["reduced"]:
        print("%s: pack size reduced from %d to %d" % (a.pack, report["s_target"], report["s_used"]))
    print("wrote %s and %s" % (sel_path, rep_path))
    return 0


if __name__ == "__main__":
    sys.exit(main())
