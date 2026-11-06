#!/usr/bin/env python3
"""analyse_s2_a14 - ADDENDUM_study2.md, S2-A14: sign tests that respect the source-file clusters (sensitivity).

  python analyse_s2_a14.py [--runs runs] [--registered ../analysis/study2.json]
                           [--out ../analysis/s2_a14.md] [--json ../analysis/s2_a14.json]

Covers every sign test whose result the manuscript reports, in the families of the registered analyses:

* Study 2, H1-S2: selection (graph, kind from metadata) against none, 8 tests, Holm over the 8;
* Study 2, H3-S2: selection against chunk (TF-IDF), bm25 and dense, 24 tests, Holm over the 24;
* Study 1: selection against none, 12 tests, without correction (as reported);
* Study 1, H3: selection against chunk (TF-IDF), bm25 and dense, 36 tests, Holm over the 36.

Data. Study 2: the test runs of the command of S2-A11 (s2test_<pin>_*; the hosted runs of Qwen3.5-9B), read with
the rules of the analysis (athena_s2/analysis.py, read_runs: the first record without an error of each key by time
stamp); model = pin. Study 1: the test meta runs (test_*_meta), read with athena.report.load_trials (the last record
of each key), as the analysis of Study 1 reads them; model = backend. Test split only. A task is a unit_id; its score
is the mean of its rounds; its difference is selection minus the other condition; its cluster is its source file
(field `file`), as in the cluster bootstrap. The rounds of a task are never separate units.

Per comparison:

1. task-level exact two-sided sign test, recomputed as registered (a check of the reading; for Study 2 it is compared
   with the registered results in study2.json);
2. file-level exact two-sided sign test on the mean difference of the tasks of each file (files with a mean of zero
   are not counted; each file has equal weight);
3. file-level sign-flip test: statistic = mean difference over tasks; under the null hypothesis the sum of the task
   differences of a file is symmetric about zero, and its sign is flipped file by file; the two-sided p-value is the
   share of the 2^k sign patterns whose absolute sum is at least the observed one, counted exactly (the differences
   are multiples of 1/3, so the sums are counted as integers; no sampling, no seed);
4. the 95% percentile interval of the mean difference over tasks from the cluster bootstrap over source files
   (athena.confirmatory.cluster_bootstrap_ci, 10,000 resamples, seed 20261018).

Holm's method is applied to each test separately within each family. A conclusion is "significant" when the
(adjusted) p-value is below 0.05 and the mean difference over tasks is positive, the rule of the registered tests.
Also reported: tasks and files per comparison, the mean difference weighted by task and by file, the files better,
worse and tied, and per study and pack the files of the test split with the tasks per file. Nothing here changes a
registered result. Standard library only.
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import sys
from collections import Counter, defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from athena import confirmatory as C  # noqa: E402
from athena.report import holm, load_trials, mean, sign_test_p  # noqa: E402
from athena_s2 import analysis as A  # noqa: E402

ALPHA = C.ALPHA
SELECTION = "graph"
NONE = "none"
RETRIEVAL = C.RETRIEVAL_BASELINES                     # chunk (TF-IDF), bm25, dense
S2_PACKS = ("godot-s2", "dotnet-runtime-s2")          # both included in H1-S2 (S2-A7)
S2_PINS = ("luna", "gemini31fl", "gemma4_local_s2", "qwen35_9b_or_s2")
S1_PACKS = C.DEFAULT_PACKS                            # godot, dotnet-runtime, odoo
FAMILIES = (
    ("S2-H1", "Study 2", "none", "Holm over 8 (registered family of H1-S2)"),
    ("S2-H3", "Study 2", "retrieval", "Holm over 24 (as registered)"),
    ("S1-none", "Study 1", "none", "no correction (as reported)"),
    ("S1-H3", "Study 1", "retrieval", "Holm over 36 (as registered)"),
)
TESTS = ("task", "file_sign", "file_flip")


# ------------------------------------------------------------------------------------------------------ statistics

def flip_p(file_sums3: list) -> float:
    """Exact two-sided p of the sign-flip test on integer file sums (three times the sum of the task differences)."""
    nz = [abs(int(s)) for s in file_sums3 if int(s) != 0]
    if not nz:
        return 1.0
    obs = abs(sum(int(s) for s in file_sums3))
    dist = {0: 1}
    for s in nz:
        nxt: dict = defaultdict(int)
        for k, v in dist.items():
            nxt[k + s] += v
            nxt[k - s] += v
        dist = nxt
    hit = sum(v for k, v in dist.items() if abs(k) >= obs)
    return min(1.0, hit / 2 ** len(nz))


def compare(cell_sel: dict, cell_other: dict, clusters: dict, pack: str, b: int, seed: int) -> dict:
    units, deltas, up, dn, tie = C.paired(cell_sel, cell_other)
    by: dict = defaultdict(list)
    for u, d in zip(units, deltas):
        by[clusters.get((pack, u), u)].append(d)
    fmeans = [sum(v) / len(v) for v in by.values()]
    sums3 = [round(3 * sum(v)) for v in by.values()]
    fu, fd = sum(m > 1e-12 for m in fmeans), sum(m < -1e-12 for m in fmeans)
    lo, hi = C.cluster_bootstrap_ci(units, deltas, clusters, pack, b, seed) if units else (None, None)
    return {"tasks": len(units), "files": len(by), "up": up, "down": dn, "tie": tie,
            "files_up": fu, "files_down": fd, "files_tie": len(by) - fu - fd,
            "files_nonzero_sum": sum(1 for s in sums3 if s != 0),
            "mean_diff_pp": 100 * mean(deltas) if deltas else None,
            "file_weighted_diff_pp": 100 * mean(fmeans) if fmeans else None,
            "ci_low_pp": None if lo is None else 100 * lo, "ci_high_pp": None if hi is None else 100 * hi,
            "p_task": sign_test_p(up, dn), "p_file_sign": sign_test_p(fu, fd), "p_file_flip": flip_p(sums3)}


def adjust(rows: list, correct: bool) -> None:
    for t in TESTS:
        ps = [r[f"p_{t}"] for r in rows]
        adj = holm(ps) if correct else ps
        for r, a in zip(rows, adj):
            r[f"padj_{t}"] = a
            r[f"sig_{t}"] = bool(a < ALPHA and (r["mean_diff_pp"] or 0) > 0)
    for r in rows:
        r["same_file_sign"] = r["sig_file_sign"] == r["sig_task"]
        r["same_file_flip"] = r["sig_file_flip"] == r["sig_task"]


def file_distribution(idx: dict, clusters: dict, packs) -> list:
    out = []
    for pack in packs:
        units = set()
        for (split, p, _m, cond), d in idx.items():
            if split == "test" and p == pack and cond == SELECTION:
                units.update(d)
        per = Counter(clusters.get((pack, u), u) for u in units)
        hist = Counter(per.values())
        out.append({"pack": pack, "tasks": len(units), "files": len(per),
                    "tasks_per_file": {str(k): hist[k] for k in sorted(hist)},
                    "largest": max(per.values()) if per else 0})
    return out


# -------------------------------------------------------------------------------------------------------- reading

def expand(runs: str, patterns) -> list:
    out = []
    for p in patterns:
        out.extend(sorted(glob.glob(os.path.join(runs, p))))
    return out


def study2(runs: str) -> tuple:
    dirs = expand(runs, [f"s2test_{p}_*" for p in S2_PINS])
    if len(dirs) != 4 * len(S2_PINS):
        raise SystemExit(f"Study 2: expected {4 * len(S2_PINS)} run folders, found {len(dirs)}")
    recs, _, error_keys = A.read_runs(dirs)
    recs = [r for r in recs if r.get("split") == "test" and r.get("pack") in S2_PACKS
            and r.get("task", "rename") == "rename"]
    idx, clusters = C.build_index(recs, "pin", "file")
    info = {"run_folders": [os.path.basename(d) for d in dirs], "records": len(recs), "error_keys": len(error_keys),
            "cluster_sources": C.cluster_sources(recs, "file")}
    return idx, clusters, info


def study1(runs: str) -> tuple:
    dirs = expand(runs, ["test_*_meta"])
    if len(dirs) != 12:
        raise SystemExit(f"Study 1: expected 12 run folders, found {len(dirs)}")
    recs, error_keys = load_trials(dirs)
    recs = [r for r in recs if r.get("split") == "test" and r.get("pack") in S1_PACKS
            and r.get("task", "rename") == "rename"]
    idx, clusters = C.build_index(recs, "backend", "file")
    info = {"run_folders": [os.path.basename(d) for d in dirs], "records": len(recs), "error_keys": len(error_keys),
            "cluster_sources": C.cluster_sources(recs, "file")}
    return idx, clusters, info


def family_rows(idx, clusters, packs, others, b, seed, model_order=None) -> list:
    rows = []
    for pack in packs:
        models = C.models_of(idx, pack)
        if model_order:
            models = sorted(models, key=lambda m: (model_order.index(m) if m in model_order else 99, str(m)))
        for model in models:
            for other in others:
                sel = idx.get(("test", pack, model, SELECTION), {})
                oth = idx.get(("test", pack, model, other), {})
                if not sel or not oth:
                    continue
                r = {"pack": pack, "model": model, "other": other}
                r.update(compare(sel, oth, clusters, pack, b, seed))
                rows.append(r)
    return rows


def check_registered(rows_h1: list, rows_h3: list, path: str | None) -> dict:
    """Compare the recomputed task-level tests of Study 2 with the registered results (study2.json)."""
    if not path or not os.path.exists(path):
        return {"available": False}
    with open(path, "r", encoding="utf-8") as f:
        reg = json.load(f)
    mism = []
    n = 0
    pairs = [((x["pack"], x["model"], NONE), x) for x in reg.get("h1", [])]
    pairs += [((x["pack"], x["model"], x["baseline"]), x) for x in (reg.get("h3") or {}).get("retrieval", [])]
    mine = {(r["pack"], r["model"], r["other"]): r for r in rows_h1 + rows_h3}
    for key, x in pairs:
        n += 1
        r = mine.get(key)
        if r is None:
            mism.append({"key": list(key), "reason": "missing"})
            continue
        for a, bkey in (("up", "up"), ("down", "down"), ("tie", "tie")):
            if r[a] != x[bkey]:
                mism.append({"key": list(key), "field": a, "registered": x[bkey], "recomputed": r[a]})
        for a, bkey in (("p_task", "p"), ("padj_task", "p_holm")):
            if abs(r[a] - x[bkey]) > 1e-12:
                mism.append({"key": list(key), "field": a, "registered": x[bkey], "recomputed": r[a]})
    return {"available": True, "compared": n, "mismatches": mism}


# --------------------------------------------------------------------------------------------------------- report

def _p(x):
    if x is None:
        return "n/a"
    return "<0.001" if x < 0.001 else f"{x:.3f}"


def _f(x, d=1):
    return "n/a" if x is None else f"{x:+.{d}f}"


def short(m) -> str:
    s = str(m)
    for k, v in (("luna", "Luna"), ("gemini", "Gemini"), ("gemma", "Gemma"), ("qwen", "Qwen")):
        if k in s.lower():
            return v
    return s


def render(res: dict) -> str:
    out = ["# S2-A14: sign tests that respect the source-file clusters (sensitivity analysis)", "",
           "Test split. Task score = mean of its rounds; difference = selection minus the other condition; "
           "cluster = source file. Significant = adjusted p < 0.05 and a positive mean difference over tasks. "
           "Nothing here changes a registered result.", ""]
    out += ["## Source files of the test split", "",
            "| Study | Pack | Tasks | Files | Tasks per file (files) | Largest |", "|---|---|---|---|---|---|"]
    for st in ("study2", "study1"):
        for d in res[st]["files"]:
            tp = ", ".join(f"{k}: {v}" for k, v in d["tasks_per_file"].items())
            out.append(f"| {res[st]['name']} | {d['pack']} | {d['tasks']} | {d['files']} | {tp} | {d['largest']} |")
    out.append("")
    for fam in res["families"]:
        rows = fam["rows"]
        out += [f"## {fam['study']}: selection against {fam['against']}; {fam['correction']}", "",
                "| Pack | Model | Other | Tasks | Files | Tasks +/-/= | Files +/-/= | Diff task-wt (pp) | "
                "Diff file-wt (pp) | 95% CI (cluster bootstrap) | p task | p file sign | p file flip | "
                "Sig task / file sign / file flip |",
                "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
        for r in rows:
            sig = " / ".join("yes" if r[f"sig_{t}"] else "no" for t in TESTS)
            ci = "n/a" if r["ci_low_pp"] is None else f"[{r['ci_low_pp']:+.1f}, {r['ci_high_pp']:+.1f}]"
            out.append(f"| {r['pack']} | {short(r['model'])} | {r['other']} | {r['tasks']} | {r['files']} | "
                       f"{r['up']}/{r['down']}/{r['tie']} | {r['files_up']}/{r['files_down']}/{r['files_tie']} | "
                       f"{_f(r['mean_diff_pp'])} | {_f(r['file_weighted_diff_pp'])} | {ci} | {_p(r['padj_task'])} | "
                       f"{_p(r['padj_file_sign'])} | {_p(r['padj_file_flip'])} | {sig} |")
        s = fam["summary"]
        out += ["", f"- Significant: task {s['sig_task']}, file sign {s['sig_file_sign']}, file flip "
                f"{s['sig_file_flip']} of {s['n']}. Conclusion changed: file sign {s['changed_file_sign']}, file flip "
                f"{s['changed_file_flip']}.", ""]
    chk = res["check_registered"]
    if chk.get("available"):
        out.append(f"Check of the reading (Study 2): {chk['compared']} registered task-level tests compared, "
                   f"{len(chk['mismatches'])} mismatches.")
    for st in ("study2", "study1"):
        i = res[st]["info"]
        out.append(f"{res[st]['name']}: {len(i['run_folders'])} run folders, {i['records']} records, keys with "
                   f"errors only {i['error_keys']}, units clustered by file {i['cluster_sources']}.")
    return "\n".join(out)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--runs", default=os.path.join(HERE, "runs"))
    ap.add_argument("--registered", default=os.path.join(HERE, "..", "analysis", "study2.json"))
    ap.add_argument("--bootstrap", type=int, default=C.BOOT_B)
    ap.add_argument("--seed", type=int, default=C.BOOT_SEED)
    ap.add_argument("--out", default=None, help="write the report (markdown) here")
    ap.add_argument("--json", default=None, help="write the results (JSON) here")
    a = ap.parse_args(argv)

    i2, c2, info2 = study2(a.runs)
    i1, c1, info1 = study1(a.runs)
    fams = []
    spec = {"S2-H1": (i2, c2, S2_PACKS, (NONE,), list(S2_PINS)),
            "S2-H3": (i2, c2, S2_PACKS, RETRIEVAL, list(S2_PINS)),
            "S1-none": (i1, c1, S1_PACKS, (NONE,), None),
            "S1-H3": (i1, c1, S1_PACKS, RETRIEVAL, None)}
    for fid, study, against, corr in FAMILIES:
        idx, cl, packs, others, order = spec[fid]
        rows = family_rows(idx, cl, packs, others, a.bootstrap, a.seed, order)
        adjust(rows, correct=not corr.startswith("no correction"))
        summ = {"n": len(rows)}
        for t in TESTS:
            summ[f"sig_{t}"] = sum(r[f"sig_{t}"] for r in rows)
        summ["changed_file_sign"] = sum(not r["same_file_sign"] for r in rows)
        summ["changed_file_flip"] = sum(not r["same_file_flip"] for r in rows)
        fams.append({"id": fid, "study": study, "against": against, "correction": corr, "rows": rows,
                     "summary": summ})
    by = {f["id"]: f["rows"] for f in fams}
    res = {"settings": {"alpha": ALPHA, "bootstrap_b": a.bootstrap, "bootstrap_seed": a.seed,
                        "cluster_field": "file", "split": "test"},
           "study2": {"name": "Study 2", "info": info2, "files": file_distribution(i2, c2, S2_PACKS)},
           "study1": {"name": "Study 1", "info": info1, "files": file_distribution(i1, c1, S1_PACKS)},
           "families": fams,
           "check_registered": check_registered(by["S2-H1"], by["S2-H3"], a.registered)}
    md = render(res)
    if a.out:
        with open(a.out, "w", encoding="utf-8", newline="\n") as f:
            f.write(md + "\n")
    if a.json:
        with open(a.json, "w", encoding="utf-8", newline="\n") as f:
            json.dump(res, f, indent=2)
            f.write("\n")
    print(md)
    return 0


if __name__ == "__main__":
    sys.exit(main())
