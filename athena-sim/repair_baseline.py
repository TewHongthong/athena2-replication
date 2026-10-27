#!/usr/bin/env python3
"""repair_baseline - the program that applies the casing rule (addendum A10; exploratory, no model call).

  python repair_baseline.py --meta runs/test_*_meta [--packs-dir packs] [--out a10.md] [--json a10.json] [--selftest]

For each test task (unit) found in the trials of --meta, the program takes the injected name, the language, the kind and
the core rules of the human ontology (packs/<pack>/core_rules.json and the ontology), splits the injected name into words,
joins them in the casing that the rules require (with the prefix and the suffix of a rule, if it has any), and scores the
result with the same check as the trials (check_naming_compliance over the core rules, after the same normalisation of
Python's leading underscores). The original name is used only to score exact match. The scorer is first checked against
the stored `core_ok` of every trial that has a proposed name. Standard library only.
"""
from __future__ import annotations

import argparse
import glob
import json
import math
import os
import re
import sys
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from athena import confirmatory as C  # noqa: E402
from athena.evaluate import name_for_check  # noqa: E402
from athena.report import load_trials  # noqa: E402
from output_validator import check_naming_compliance  # noqa: E402  (athena.evaluate puts vendor on the path)

PACKS = ("godot", "dotnet-runtime", "odoo")
ONTOLOGY_FILES = {"godot": "godot_ontology.json", "dotnet-runtime": "dotnet_ontology.json", "odoo": "odoo_ontology.json"}
WORD = re.compile(r"[A-Z]+(?=[A-Z][a-z])|[A-Z]?[a-z]+[0-9]*|[A-Z]+[0-9]*|[0-9]+[a-z]*")


def words(name: str) -> list:
    out = []
    for chunk in name.split("_"):
        out.extend(WORD.findall(chunk))
    return out


def join(ws: list, casing: str) -> str:
    low = [w.lower() for w in ws]
    if casing == "snake_case":
        return "_".join(low)
    if casing in ("UPPER_SNAKE_CASE", "CONSTANT_CASE"):
        return "_".join(w.upper() for w in ws)
    if casing == "kebab-case":
        return "-".join(low)
    if casing == "lowercase":
        return "".join(low)
    if casing == "PascalCase":
        return "".join(w[:1].upper() + w[1:].lower() for w in ws)
    if casing in ("camelCase", "lowerCamelCase"):
        return "".join((w.lower() if i == 0 else w[:1].upper() + w[1:].lower()) for i, w in enumerate(low))
    return "".join(ws)


def repair(injected: str, language: str, rules: list) -> str:
    lead = ""
    if language == "python":
        m = re.match(r"^(_+)", injected)
        lead = m.group(1) if m and not (injected.startswith("__") and injected.endswith("__")) else ""
    ws = words(injected.lstrip("_"))
    casing = next((r.get("casing") for r in rules if r.get("casing")), None)
    name = join(ws, casing) if casing else "".join(ws)
    prefix = next((r.get("prefix") for r in rules if r.get("prefix") and "/" not in r["prefix"]), None)
    suffix = next((r.get("suffix") for r in rules if r.get("suffix")), None)
    if prefix and not name.startswith(prefix):
        name = prefix + name
    if suffix and not name.endswith(suffix):
        name = name + suffix
    return lead + name


def load_rules(packs_dir: str, pack: str):
    ont = json.load(open(os.path.join(packs_dir, pack, ONTOLOGY_FILES[pack]), encoding="utf-8"))
    nodes = {n["id"]: n for n in ont["nodes"]}
    core = json.load(open(os.path.join(packs_dir, pack, "core_rules.json"), encoding="utf-8")).get("core", {})
    table = {(lang, kind): [nodes[r] for r in ids] for lang, kinds in core.items() for kind, ids in kinds.items()}
    return table


def score(name: str, language: str, rules: list) -> bool | None:
    if not rules:
        return None
    chk = name_for_check(language, name)
    return all(check_naming_compliance(chk, r)[0] for r in rules)


def wilson(k, n, z=1.96):
    if n == 0:
        return (float("nan"), float("nan"))
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (c - h, c + h)


def pct(x):
    return "n/a" if x is None or x != x else f"{100 * x:.1f}"


def selftest():
    cases = [("createRawOwnedCustomAttribute", "snake_case", "create_raw_owned_custom_attribute"),
             ("create_raw_owned", "PascalCase", "CreateRawOwned"),
             ("HTTPServerName", "snake_case", "http_server_name"),
             ("MaxValue", "UPPER_SNAKE_CASE", "MAX_VALUE"),
             ("Vector3Length", "snake_case", "vector3_length"),
             ("get_2d_size", "camelCase", "get2dSize"),
             ("SomeModule", "lowercase", "somemodule")]
    bad = [(a, c, join(words(a), c), want) for a, c, want in cases if join(words(a), c) != want]
    if bad:
        sys.exit(f"selftest failed: {bad}")
    assert repair("_PrivateName", "python", [{"casing": "snake_case"}]) == "_private_name"
    print("selftest ok")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--meta", nargs="+")
    ap.add_argument("--packs-dir", default=os.path.join(HERE, "packs"))
    ap.add_argument("--selection", default="graph")
    ap.add_argument("--none", default="none", dest="none_cond")
    ap.add_argument("--out", default=None)
    ap.add_argument("--json", default=None)
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        selftest()
        if not a.meta:
            return
    if not a.meta:
        sys.exit("--meta is required")
    dirs = []
    for p in a.meta:
        dirs.extend(sorted(glob.glob(p)) or [p])
    recs, _ = load_trials(dirs)
    tables = {p: load_rules(a.packs_dir, p) for p in PACKS}

    # 1 check of the scorer against the stored core_ok
    checked = mismatch = 0
    for r in recs:
        if r.get("task", "rename") != "rename" or r.get("split") != "test":
            continue
        m = r.get("metrics") or {}
        sug = m.get("suggested")
        if not sug or m.get("core_ok") is None or not m.get("valid_identifier", True):
            continue
        rules = tables[r["pack"]].get((r["language"], r["kind"]), [])
        checked += 1
        if bool(score(sug, r["language"], rules)) != bool(m["core_ok"]):
            mismatch += 1

    # 2 units of the test part
    units = {}
    for r in recs:
        if r.get("task", "rename") == "rename" and r.get("split") == "test":
            units[(r["pack"], r["unit_id"])] = r
    idx, _ = C.build_index(recs)
    rows, fails, bykind = [], [], defaultdict(lambda: [0, 0])
    for pack in PACKS:
        us = {k: v for k, v in units.items() if k[0] == pack}
        n = ok = em = 0
        for (_, uid), r in sorted(us.items()):
            rules = tables[pack].get((r["language"], r["kind"]), [])
            prop = repair(r["injected"], r["language"], rules)
            s = score(prop, r["language"], rules)
            if s is None:
                continue
            n += 1
            ok += bool(s)
            em += prop == r["original"]
            bykind[(pack, r["language"], r["kind"])][0] += 1
            bykind[(pack, r["language"], r["kind"])][1] += bool(s)
            if not s or prop != r["original"]:
                fails.append((pack, uid, r["kind"], r["injected"], prop, r["original"], bool(s)))
        def pooled(cond):
            vals = []
            for model in C.models_of(idx, pack, "test"):
                d = C.unit_means(C._cell(idx, pack, model, cond, "test"))
                if d:
                    vals.append(sum(d.values()) / len(d))
            return sum(vals) / len(vals) if vals else None
        lo, hi = wilson(ok, n)
        elo, ehi = wilson(em, n)
        rows.append({"pack": pack, "tasks": n, "core_ok": ok / n if n else None, "core_lo": lo, "core_hi": hi,
                     "exact": em / n if n else None, "exact_lo": elo, "exact_hi": ehi,
                     "none": pooled(a.none_cond), "selection": pooled(a.selection)})

    L = ["# Addendum A10 - a program that applies the casing rule (exploratory)", "",
         f"Scorer check: {checked} test trials with a proposed name were re-scored with the function used here; "
         f"{mismatch} differ from the stored core_ok.", "",
         "| pack | tasks | repair core_ok % [95% Wilson] | repair exact match % [95% Wilson] | none core_ok % (mean of models) | selection core_ok % (mean of models) |",
         "|---|---|---|---|---|---|"]
    for r in rows:
        L.append(f"| {r['pack']} | {r['tasks']} | {pct(r['core_ok'])} [{pct(r['core_lo'])}, {pct(r['core_hi'])}] | "
                 f"{pct(r['exact'])} [{pct(r['exact_lo'])}, {pct(r['exact_hi'])}] | {pct(r['none'])} | {pct(r['selection'])} |")
    L += ["", "By kind (tasks, core_ok):", ""]
    L += [f"- {p} / {lang} / {kind}: {v[1]} of {v[0]}" for (p, lang, kind), v in sorted(bykind.items())]
    L += ["", f"Tasks where the proposed name is not compliant or differs from the original name: {len(fails)}", ""]
    L += [f"- {p} {uid} ({kind}): injected `{inj}` -> `{prop}`; original `{orig}`; core_ok {ok}" for p, uid, kind, inj, prop, orig, ok in fails[:40]]
    text = "\n".join(L)
    print(text)
    if a.out:
        open(a.out, "w", encoding="utf-8").write(text + "\n")
    if a.json:
        json.dump({"rows": rows, "checked": checked, "mismatch": mismatch, "fails": fails}, open(a.json, "w"), indent=1)


if __name__ == "__main__":
    main()
