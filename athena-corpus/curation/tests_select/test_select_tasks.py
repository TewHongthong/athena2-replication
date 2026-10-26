#!/usr/bin/env python3
"""Tests of tools/select_tasks.py on synthetic pools (run as a file from athena-corpus/curation)."""
import collections
import hashlib
import json
import os
import random
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "tools"))

import select_tasks as st  # noqa: E402


def make_paths(side, count, prefix="src/f"):
    """Return `count` distinct file paths whose hash falls on the given side."""
    out = []
    i = 0
    while len(out) < count:
        p = "%s%d.cpp" % (prefix, i)
        if st.side_of(p) == side:
            out.append(p)
        i += 1
    return out


def make_units(files_by_side):
    """files_by_side: {side: list of unit counts per file}. Returns a unit list with unique paths per side."""
    units = []
    for side, counts in files_by_side.items():
        for path, n in zip(make_paths(side, len(counts), prefix="%s/f" % side), counts):
            for k in range(n):
                units.append({"path": path, "unit_index": k, "extra": []})
    return units


class SplitTests(unittest.TestCase):
    def test_hash_rule_matches_definition(self):
        for p in ("core/a.cpp", "addons/x/models/y.py", "src/libraries/z.cs"):
            v = int(hashlib.sha256(p.encode("utf-8")).hexdigest(), 16) % 100
            self.assertEqual(st.side_of(p), "dev" if v < 30 else "test")

    def test_dev_share_is_about_thirty_percent(self):
        sides = [st.side_of("dir/file%d.py" % i) for i in range(3000)]
        share = sides.count("dev") / len(sides)
        self.assertTrue(0.27 < share < 0.33, share)

    def test_units_of_a_file_share_a_side(self):
        units = make_units({"dev": [4, 4, 4], "test": [4, 4, 4]})
        by_side = st.split_pool(units)
        dev_files = {u["path"] for u in by_side["dev"]}
        test_files = {u["path"] for u in by_side["test"]}
        self.assertFalse(dev_files & test_files)
        self.assertEqual(len(by_side["dev"]) + len(by_side["test"]), len(units))

    def test_targets(self):
        self.assertEqual(st.targets(100), {"dev": 30, "test": 70})
        self.assertEqual(st.targets(96), {"dev": 28, "test": 68})
        self.assertEqual(st.targets(95), {"dev": 28, "test": 67})
        self.assertEqual(st.targets(1), {"dev": 0, "test": 1})
        for s in range(1, 101):
            t = st.targets(s)
            self.assertEqual(t["dev"] + t["test"], s)
            self.assertEqual(t["dev"], (3 * s) // 10)


class SelectionTests(unittest.TestCase):
    def test_default_size_and_cap(self):
        units = make_units({"dev": [3] * 20, "test": [3] * 40})
        selected, report = st.select(units, "p")
        self.assertEqual(report["s_used"], 100)
        self.assertFalse(report["reduced"])
        self.assertEqual(len(selected["dev"]), 30)
        self.assertEqual(len(selected["test"]), 70)
        for side in st.SIDES:
            self.assertEqual(report["sides"][side]["cap_used"], 3)
            counts = collections.Counter(u["path"] for u in selected[side])
            self.assertLessEqual(max(counts.values()), 3)
            self.assertEqual(len({(u["path"], u["unit_index"]) for u in selected[side]}), len(selected[side]))

    def test_selected_units_stay_on_their_side(self):
        units = make_units({"dev": [5] * 20, "test": [5] * 40})
        selected, _ = st.select(units, "p")
        for side in st.SIDES:
            for u in selected[side]:
                self.assertEqual(st.side_of(u["path"]), side)

    def test_deterministic_and_input_order_independent(self):
        units = make_units({"dev": [4] * 20, "test": [4] * 40})
        a, _ = st.select(units, "p")
        shuffled_units = list(units)
        random.Random(7).shuffle(shuffled_units)
        b, _ = st.select(shuffled_units, "p")
        for side in st.SIDES:
            self.assertEqual([(u["path"], u["unit_index"]) for u in a[side]],
                             [(u["path"], u["unit_index"]) for u in b[side]])

    def test_pack_name_changes_the_draw(self):
        units = make_units({"dev": [4] * 30, "test": [4] * 60})
        a, _ = st.select(units, "godot")
        b, _ = st.select(units, "odoo")
        self.assertNotEqual([(u["path"], u["unit_index"]) for u in a["test"]],
                            [(u["path"], u["unit_index"]) for u in b["test"]])

    def test_cap_relaxes_for_the_short_side_only(self):
        # dev: 10 files of 3 units -> capacity 30 at cap 3; test: 15 files of 3 units -> capacity 45 at cap 3 (short of 70),
        # 15 files of 5 units -> capacity 60 at cap 4, 75 at cap 5
        units = make_units({"dev": [3] * 10, "test": [5] * 15})
        selected, report = st.select(units, "p")
        self.assertEqual(report["sides"]["dev"]["cap_used"], 3)
        self.assertEqual(report["sides"]["test"]["cap_used"], 5)
        self.assertTrue(report["sides"]["test"]["cap_relaxed"])
        self.assertFalse(report["sides"]["dev"]["cap_relaxed"])
        self.assertEqual(report["s_used"], 100)
        self.assertEqual(len(selected["test"]), 70)
        self.assertLessEqual(max(collections.Counter(u["path"] for u in selected["test"]).values()), 5)

    def test_cap_four_is_enough_when_it_is(self):
        units = make_units({"dev": [3] * 10, "test": [4] * 18})  # test: cap 3 -> 54, cap 4 -> 72
        _, report = st.select(units, "p")
        self.assertEqual(report["sides"]["test"]["cap_used"], 4)

    def test_pack_size_reduced_when_a_side_is_short_at_cap_five(self):
        # dev capacity at cap 5 = 28 (one task short of 30); test is ample
        units = make_units({"dev": [5] * 5 + [3], "test": [3] * 40})
        self.assertEqual(st.capacity([u for u in units if st.side_of(u["path"]) == "dev"], 5), 28)
        selected, report = st.select(units, "p")
        self.assertEqual(report["s_used"], 96)
        self.assertTrue(report["reduced"])
        self.assertEqual(len(selected["dev"]), 28)
        self.assertEqual(len(selected["test"]), 68)
        self.assertEqual(report["sides"]["dev"]["cap_used"], 5)

    def test_reduction_uses_the_cap_that_reaches_the_new_target(self):
        # dev capacity: cap 3 -> 21, cap 4 -> 28, cap 5 -> 28; the target 30 is out of reach, S' = 96 gives dev 28,
        # which cap 4 already reaches, so cap 4 is used and not 5
        units = make_units({"dev": [4] * 7, "test": [3] * 40})
        selected, report = st.select(units, "p")
        d = report["sides"]["dev"]
        self.assertEqual(d["capacity_by_cap"], {"3": 21, "4": 28, "5": 28})
        self.assertEqual(report["s_used"], 96)
        self.assertEqual(d["cap_used"], 4)
        self.assertEqual(len(selected["dev"]), 28)
        self.assertEqual(len(selected["test"]), 68)

    def test_reduced_target_follows_the_capacity_at_cap_five(self):
        # dev capacity: cap 3 -> 15, cap 4 -> 20, cap 5 -> 25; floor(0.3 * 86) = 25, floor(0.3 * 87) = 26
        units = make_units({"dev": [5] * 5, "test": [3] * 40})
        selected, report = st.select(units, "p")
        d = report["sides"]["dev"]
        self.assertEqual(d["capacity_by_cap"], {"3": 15, "4": 20, "5": 25})
        self.assertEqual(report["s_used"], 86)
        self.assertEqual(d["target"], 25)
        self.assertEqual(d["cap_used"], 5)
        self.assertEqual(len(selected["test"]), 61)

    def test_largest_feasible_size_is_chosen(self):
        units = make_units({"dev": [5] * 5 + [1, 1, 1], "test": [3] * 40})  # dev capacity at 5 = 28
        _, report = st.select(units, "p")
        for s in range(report["s_used"] + 1, 101):
            self.assertGreater(st.targets(s)["dev"], 28)
        self.assertLessEqual(st.targets(report["s_used"])["dev"], 28)

    def test_test_side_can_limit_the_size(self):
        units = make_units({"dev": [3] * 20, "test": [5] * 10})  # test capacity 50 at cap 5
        selected, report = st.select(units, "p")
        self.assertEqual(report["s_used"], 71)  # test = 71 - 21 = 50
        self.assertEqual(len(selected["test"]), 50)
        self.assertEqual(len(selected["dev"]), 21)

    def test_size_option(self):
        units = make_units({"dev": [3] * 20, "test": [3] * 40})
        selected, report = st.select(units, "p", s_target=50)
        self.assertEqual((len(selected["dev"]), len(selected["test"])), (15, 35))
        self.assertFalse(report["reduced"])

    def test_empty_pool_is_an_error(self):
        with self.assertRaises(st.SelectionError):
            st.select([], "p")


class FileTests(unittest.TestCase):
    def write_pool(self, tmp, units, extra=None):
        path = os.path.join(tmp, "pool.tsv")
        with open(path, "w", encoding="utf-8", newline="") as fh:
            fh.write("path\tunit_index" + ("\t" + "\t".join(extra) if extra else "") + "\n")
            for u in units:
                row = [u["path"], str(u["unit_index"])]
                if extra:
                    row += ["%s#%d" % (u["path"], u["unit_index"])] * len(extra)
                fh.write("\t".join(row) + "\n")
        return path

    def test_cli_roundtrip_with_extra_column(self):
        units = make_units({"dev": [3] * 20, "test": [3] * 40})
        with tempfile.TemporaryDirectory() as tmp:
            pool = self.write_pool(tmp, units, extra=["unit_id"])
            out = os.path.join(tmp, "out")
            rc = st.main(["--pack", "demo", "--pool", pool, "--out-dir", out])
            self.assertEqual(rc, 0)
            with open(os.path.join(out, "demo_selection.tsv"), encoding="utf-8") as fh:
                rows = [l.rstrip("\n").split("\t") for l in fh]
            self.assertEqual(rows[0], ["pack", "side", "rank", "path", "unit_index", "unit_id"])
            self.assertEqual(len(rows) - 1, 100)
            for r in rows[1:]:
                self.assertEqual(r[5], "%s#%s" % (r[3], r[4]))
            self.assertEqual([r[1] for r in rows[1:]].count("dev"), 30)
            with open(os.path.join(out, "demo_selection_report.json"), encoding="utf-8") as fh:
                rep = json.load(fh)
            self.assertEqual(rep["s_used"], 100)
            self.assertEqual(rep["seed"], "athena2-b1-v1")

    def test_cli_rejects_bad_pools(self):
        with tempfile.TemporaryDirectory() as tmp:
            bad = os.path.join(tmp, "bad.tsv")
            with open(bad, "w", encoding="utf-8") as fh:
                fh.write("path\tother\nx.py\t1\n")
            self.assertEqual(st.main(["--pack", "p", "--pool", bad, "--out-dir", tmp]), 2)
            dup = os.path.join(tmp, "dup.tsv")
            with open(dup, "w", encoding="utf-8") as fh:
                fh.write("path\tunit_index\nx.py\t1\nx.py\t1\n")
            self.assertEqual(st.main(["--pack", "p", "--pool", dup, "--out-dir", tmp]), 2)
            nonint = os.path.join(tmp, "nonint.tsv")
            with open(nonint, "w", encoding="utf-8") as fh:
                fh.write("path\tunit_index\nx.py\tone\n")
            self.assertEqual(st.main(["--pack", "p", "--pool", nonint, "--out-dir", tmp]), 2)


if __name__ == "__main__":
    unittest.main()
