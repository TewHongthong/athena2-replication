#!/usr/bin/env python3
"""Build a blinded review sheet for checking the program verdict (core_ok).

The sheet shows, for each sampled trial, the language, the kind of
identifier, the name to judge (the name proposed by the model), and the code
with that name applied in place of the injected one. It hides the injected
name, the model, the condition, the standard text given in the prompt, the
reasoning of the model, and the verdict of the program. Every row carries
the question to answer, so that the reviewer judges the proposed name and
not the code as it was before the rename. The key file that links each
item to its trial is written separately and is not opened until every item
has a judgement.

Sampling is stratified by the verdict of the program: n_pass trials with
core_ok = true and n_fail trials with core_ok = false, drawn with a fixed
seed from the trials that have a proposed name.

Example (from athena-sim/):
    python3 make_blind_sheet.py --out-dir ~/athena_analysis/blind
"""
import argparse
import csv
import glob
import json
import os
import random
import re

DOCS = {
    "godot": "godotengine/godot-contributing-docs, development/engine/cpp_usage_guidelines.rst (Naming)",
    "dotnet": "dotnet/runtime, docs/coding-guidelines/coding-style.md",
    "odoo": "odoo/documentation, content/contributing/development/coding_guidelines.rst",
}


def doc_for(standard_id):
    s = (standard_id or "").lower()
    for k, v in DOCS.items():
        if k in s:
            return v
    return ""


def extract_code(prompt):
    """Return the code block of the prompt (between CODE and OUTPUT FORMAT)."""
    i = prompt.find("\nCODE\n")
    j = prompt.find("\n\nOUTPUT FORMAT")
    if i < 0 or j < 0 or j <= i:
        return None
    return prompt[i + len("\nCODE\n"):j].strip("\n")


def apply_name(code, old, new):
    """Show the code as it reads after the rename: whole-word replacement."""
    if not old:
        return code
    pat = r"(?<![A-Za-z0-9_])" + re.escape(old) + r"(?![A-Za-z0-9_])"
    return re.sub(pat, lambda _m: new, code)


def load_excluded(path):
    if not path:
        return set()
    with open(path, newline="", encoding="utf-8-sig") as fh:
        return {r["key"] for r in csv.DictReader(fh)}


def rules_card(src_dir):
    """Quote, word for word, the naming rules of the three pinned documents."""
    def read(*parts):
        with open(os.path.join(src_dir, *parts), encoding="utf-8") as fh:
            return fh.read().split("\n")

    out = ["# Naming rules of the three standards (quoted from the pinned documents)", "",
           "Judge only the name in the column name_to_judge. The code is context for the kind of identifier.",
           "If the quoted text does not decide the case, answer unsure and write a note.", ""]
    g = read("godot", "cpp_usage_guidelines.rst")
    i = next(n for n, l in enumerate(g) if l.strip() == "Naming")
    j = next(n for n in range(i + 1, len(g)) if g[n].strip() == "Spacing")
    out += ["## Godot (C++) - cpp_usage_guidelines.rst, section Naming", ""] + \
        ["    " + l for l in g[i + 2:j] if l.strip()] + [""]
    d = read("dotnet-runtime", "coding-style.md")
    out += ["## .NET runtime (C#) - coding-style.md, rules 3, 12 and 13", ""]
    for num in ("3.", "12.", "13."):
        line = next(l for l in d if l.startswith(num + " "))
        out += ["    " + line, ""]
    o = read("odoo", "coding_guidelines.rst")
    k = next(n for n, l in enumerate(o) if l.strip() == "- Variable name :")
    out += ["## Odoo (Python) - coding_guidelines.rst, Variable name", ""] + ["    " + l for l in o[k:k + 4]] + [""]
    return "\n".join(out)


def load_frame(runs_glob):
    frame, skipped = [], {"no_metrics": 0, "no_name": 0, "no_code": 0, "error": 0}
    for path in sorted(glob.glob(os.path.join(runs_glob, "trials.jsonl"))):
        with open(path, encoding="utf-8") as fh:
            for line in fh:
                if not line.strip():
                    continue
                d = json.loads(line)
                m = d.get("metrics")
                if d.get("error"):
                    skipped["error"] += 1
                    continue
                if not m or "core_ok" not in m:
                    skipped["no_metrics"] += 1
                    continue
                name = (d.get("parsed") or {}).get("suggested_name")
                if not isinstance(name, str) or not name.strip():
                    skipped["no_name"] += 1
                    continue
                code = extract_code(d.get("prompt") or "")
                if code is None:
                    skipped["no_code"] += 1
                    continue
                frame.append({
                    "key": d.get("key") or "%s|%s|%s" % (d.get("run_id"), d.get("unit_id"), d.get("repeat")),
                    "run_id": d.get("run_id"), "pack": d.get("pack"), "model": d.get("model"),
                    "condition": d.get("condition"), "repeat": d.get("repeat"),
                    "language": d.get("language"), "kind": d.get("kind"),
                    "standard_id": d.get("standard_id"),
                    "injected": d.get("injected"), "proposed": name.strip(), "code": code,
                    "core_ok": bool(m["core_ok"]), "core_failed": m.get("core_failed") or [],
                })
    return frame, skipped


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--runs-glob", default="runs/test_*_meta", help="directories that hold trials.jsonl")
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--n-pass", type=int, default=60)
    ap.add_argument("--n-fail", type=int, default=60)
    ap.add_argument("--seed", default="athena2-blind-v2")
    ap.add_argument("--standards-src", default="../standards/src",
                    help="folder with the pinned standard documents; when it exists a rules card is written")
    ap.add_argument("--exclude-key", action="append", default=[],
                    help="key file of an earlier sheet; its trials are not sampled again (repeatable)")
    a = ap.parse_args(argv)

    frame, skipped = load_frame(a.runs_glob)
    excluded = set()
    for path in a.exclude_key:
        excluded |= load_excluded(path)
    n_before = len(frame)
    frame = [r for r in frame if r["key"] not in excluded]
    frame.sort(key=lambda r: r["key"])
    strata = {"pass": [r for r in frame if r["core_ok"]], "fail": [r for r in frame if not r["core_ok"]]}
    want = {"pass": a.n_pass, "fail": a.n_fail}
    rng = random.Random(a.seed)
    chosen = []
    for name in ("pass", "fail"):
        pool = list(strata[name])
        rng.shuffle(pool)
        if len(pool) < want[name]:
            raise SystemExit("stratum %s has %d trials, fewer than %d requested" % (name, len(pool), want[name]))
        chosen += [dict(r, stratum=name) for r in pool[:want[name]]]
    rng.shuffle(chosen)

    os.makedirs(a.out_dir, exist_ok=True)
    sheet_path = os.path.join(a.out_dir, "blind_sheet.csv")
    key_path = os.path.join(a.out_dir, "blind_key.csv")
    report_path = os.path.join(a.out_dir, "blind_report.json")
    with open(sheet_path, "w", newline="", encoding="utf-8-sig") as sf, \
            open(key_path, "w", newline="", encoding="utf-8") as kf:
        sw = csv.writer(sf)
        kw = csv.writer(kf)
        sw.writerow(["item", "language", "kind", "standard_document", "name_to_judge",
                     "question", "code_with_name", "judgement", "note"])
        kw.writerow(["item", "stratum", "key", "run_id", "pack", "model", "condition", "repeat",
                     "core_ok", "core_failed"])
        for n, r in enumerate(chosen, 1):
            item = "B%03d" % n
            q = "Does the name %s comply with the naming rules of the standard for a %s in %s? Judge this name only." % (
                r["proposed"], r["kind"], r["language"])
            sw.writerow([item, r["language"], r["kind"], doc_for(r["standard_id"]),
                         r["proposed"], q, apply_name(r["code"], r["injected"], r["proposed"]), "", ""])
            kw.writerow([item, r["stratum"], r["key"], r["run_id"], r["pack"], r["model"],
                         r["condition"], r["repeat"], int(r["core_ok"]), ";".join(r["core_failed"])])
    report = {"seed": a.seed, "runs_glob": a.runs_glob, "frame_size": len(frame),
              "stratum_sizes": {k: len(v) for k, v in strata.items()},
              "sample_sizes": want, "skipped": skipped,
              "excluded_earlier": n_before - len(frame)}
    with open(report_path, "w", encoding="utf-8") as fh:
        json.dump(report, fh, indent=1)
    if os.path.isdir(a.standards_src):
        with open(os.path.join(a.out_dir, "blind_rules.md"), "w", encoding="utf-8") as fh:
            fh.write(rules_card(a.standards_src))
        print("rules card:", os.path.join(a.out_dir, "blind_rules.md"))
    print("sheet:", sheet_path, "(%d items)" % len(chosen))
    print("key:  ", key_path, "(do not open until every item has a judgement)")
    print("frame %d (after excluding %d earlier trials); pass %d, fail %d; skipped %s" % (
        len(frame), n_before - len(frame), len(strata["pass"]), len(strata["fail"]), skipped))


if __name__ == "__main__":
    main()
