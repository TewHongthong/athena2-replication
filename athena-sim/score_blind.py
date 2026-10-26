#!/usr/bin/env python3
"""Compare the judgements of the blinded review with the verdict of the program.

Reads the filled sheet, the key and the report written by make_blind_sheet.py.
Judgements: complies / does not comply / unsure (c, n and u are accepted).
'unsure' items are reported and left out of the agreement figures.
Agreement and kappa are weighted by stratum size (the fail stratum is
over-sampled), so they estimate the figures for all trials in the frame.

Example:
    python3 score_blind.py --sheet blind_sheet.csv --key blind_key.csv --report blind_report.json
"""
import argparse
import csv
import json
import math

MAP = {"complies": "pass", "comply": "pass", "c": "pass", "yes": "pass",
       "does not comply": "fail", "not comply": "fail", "n": "fail", "no": "fail",
       "unsure": "unsure", "u": "unsure"}


def wilson(k, n, z=1.96):
    if n == 0:
        return (float("nan"), float("nan"))
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (c - h, c + h)


def norm(v):
    return MAP.get((v or "").strip().lower())


def read_csv(path):
    with open(path, newline="", encoding="utf-8-sig") as fh:
        return list(csv.DictReader(fh))


def score(sheet, key, report):
    keyed = {r["item"]: r for r in key}
    sizes = report["stratum_sizes"]
    rows, unsure, missing = [], [], []
    for s in sheet:
        k = keyed.get(s["item"])
        if k is None:
            raise SystemExit("item %s is not in the key" % s["item"])
        j = norm(s.get("judgement"))
        if j is None:
            missing.append(s["item"])
            continue
        if j == "unsure":
            unsure.append(s["item"])
            continue
        rows.append({"item": s["item"], "stratum": k["stratum"], "program": "pass" if k["core_ok"] == "1" else "fail",
                     "human": j, "core_failed": k["core_failed"], "pack": k["pack"], "kind": s.get("kind"),
                     "injected": "", "proposed": s.get("name_to_judge"), "note": s.get("note", "")})
    n_h = {h: sum(1 for r in rows if r["stratum"] == h) for h in sizes}
    w = {h: (sizes[h] / n_h[h]) if n_h[h] else 0.0 for h in sizes}
    tot = sum(w[r["stratum"]] for r in rows)
    cell = {(a, b): 0.0 for a in ("pass", "fail") for b in ("pass", "fail")}
    for r in rows:
        cell[(r["program"], r["human"])] += w[r["stratum"]] / tot if tot else 0.0
    po = cell[("pass", "pass")] + cell[("fail", "fail")]
    pe = sum((cell[(a, "pass")] + cell[(a, "fail")]) * (cell[("pass", b)] + cell[("fail", b)])
             for a, b in (("pass", "pass"), ("fail", "fail")))
    kappa = (po - pe) / (1 - pe) if pe < 1 else float("nan")
    per = {}
    for h in sizes:
        v = [r for r in rows if r["stratum"] == h]
        per[h] = (sum(1 for r in v if r["program"] == r["human"]), len(v))
    k_all = sum(a for a, _ in per.values())
    n_all = sum(n for _, n in per.values())
    return {"rows": rows, "unsure": unsure, "missing": missing, "weighted_agreement": po,
            "kappa": kappa, "per_stratum": per, "counts": {"judged": len(rows)},
            "overall": (k_all, n_all), "stratum_sizes": sizes}


def render(res):
    out = ["# Blind check of the program verdict", ""]
    out.append("Judged items: %d; unsure: %d; without a judgement: %d" %
               (res["counts"]["judged"], len(res["unsure"]), len(res["missing"])))
    for h, (a, n) in res["per_stratum"].items():
        lo, hi = wilson(a, n)
        out.append("- stratum %s (program verdict %s; %d trials in the frame): human agrees on %d of %d (%.1f%%, Wilson 95%% %.1f-%.1f%%)" % (
            h, h, res["stratum_sizes"][h], a, n, 100.0 * a / n if n else float("nan"), 100 * lo, 100 * hi))
    ka, na = res["overall"]
    lo, hi = wilson(ka, na)
    out.append("- all judged items (not weighted): %d of %d (%.1f%%, Wilson 95%% %.1f-%.1f%%)" % (
        ka, na, 100.0 * ka / na if na else float("nan"), 100 * lo, 100 * hi))
    out.append("- weighted agreement: %.3f; weighted kappa: %.3f (the frame is almost all program-pass, so the weighted figures"
               " follow the pass stratum and kappa is close to 0 even when most items agree; use the stratum rates)" % (
                   res["weighted_agreement"], res["kappa"]))
    out += ["", "## Disagreements", "", "| item | pack | kind | injected | proposed | program | human | core_failed | note |", "|---|---|---|---|---|---|---|---|---|"]
    for r in res["rows"]:
        if r["program"] != r["human"]:
            out.append("| %s | %s | %s | %s | %s | %s | %s | %s | %s |" % (
                r["item"], r["pack"], r["kind"], r["injected"], r["proposed"], r["program"], r["human"],
                r["core_failed"], r["note"].replace("|", "/")))
    if res["unsure"]:
        out += ["", "Unsure items: " + ", ".join(res["unsure"])]
    return "\n".join(out) + "\n"


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--sheet", required=True)
    ap.add_argument("--key", required=True)
    ap.add_argument("--report", required=True)
    ap.add_argument("--out", help="write the markdown report here")
    a = ap.parse_args(argv)
    with open(a.report, encoding="utf-8") as fh:
        report = json.load(fh)
    res = score(read_csv(a.sheet), read_csv(a.key), report)
    if not res["rows"]:
        raise SystemExit("no item has a judgement yet (%d without, %d unsure): fill the judgement column first"
                         % (len(res["missing"]), len(res["unsure"])))
    text = render(res)
    if a.out:
        with open(a.out, "w", encoding="utf-8") as fh:
            fh.write(text)
    print(text)


if __name__ == "__main__":
    main()
