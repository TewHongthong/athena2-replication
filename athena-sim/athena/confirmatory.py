"""Confirmatory analysis across runs, as registered in HYPOTHESES_v2.md (Sections 2.3 and 4).

Reads the trials of several run folders (any number of packs, models and splits) and computes

* eligibility of each standard for H1 (Section 2.3): mean `core_ok` of condition `none` on the dev units, averaged
  over the models; eligible if below 0.90;
* H1 (Section 4): selection vs `none` on the test units, per eligible standard and model; per-unit means over the
  repeats, exact two-sided sign test; one Holm family made of exactly these tests;
* H3 (Section 4): selection vs `fulldoc` as a non-inferiority estimate (cluster-bootstrap 95% CI of the paired
  difference, margin 2 pp), and selection vs the retrieval baselines with the paired sign test and a separate Holm family.

Standard library only.  The statistics (sign test, Holm) are those of report.py.
"""
from __future__ import annotations

import json
import random
from collections import defaultdict

from .report import holm, load_trials, mean, sign_test_p

ELIGIBILITY_THRESHOLD = 0.90      # Section 2.3: zero-shot compliance below this value
NI_MARGIN = 0.02                  # Section 4, H3: non-inferiority margin (2 pp)
ALPHA = 0.05
BOOT_B = 10000
BOOT_SEED = 20261018              # fixed so that the intervals can be reproduced
DEFAULT_PACKS = ("godot", "dotnet-runtime", "odoo")
RETRIEVAL_BASELINES = ("chunk", "bm25", "dense")      # `chunk` is the TF-IDF condition of the harness


def select_models(recs: list, tokens, model_field: str = "backend") -> tuple:
    """Keep the trials of the models named by `tokens`.  A token matches every model whose identifier contains it
    (case-insensitive).  Returns (trials, matched model identifiers); a token that matches no model raises ValueError."""
    models = sorted({r.get(model_field) for r in recs if r.get(model_field) is not None})
    keep: set = set()
    for t in tokens:
        hit = [m for m in models if t.lower() in str(m).lower()]
        if not hit:
            raise ValueError(f"no model matches {t!r}; models present: {', '.join(map(str, models)) or 'none'}")
        keep.update(hit)
    return [r for r in recs if r.get(model_field) in keep], sorted(keep)


def build_index(recs: list, model_field: str = "backend", cluster_field: str = "file") -> tuple:
    """Return (idx, clusters).  idx[(split, pack, model, condition)][unit_id] = [core_ok as 0/1 per repeat];
    clusters[(pack, unit_id)] = value of `cluster_field` (the source file by default); if a trial lacks it the
    `snippet_id` is used, and then the unit itself (see `cluster_sources`)."""
    idx: dict = defaultdict(lambda: defaultdict(list))
    clusters: dict = {}
    for r in recs:
        if r.get("task", "rename") != "rename":
            continue
        v = (r.get("metrics") or {}).get("core_ok")
        if v is None:
            continue
        model = r.get(model_field)
        key = (r.get("split"), r.get("pack"), model, r.get("condition"))
        idx[key][r["unit_id"]].append(1.0 if v else 0.0)
        clusters[(r.get("pack"), r["unit_id"])] = r.get(cluster_field) or r.get("snippet_id") or r["unit_id"]
    return idx, clusters


def cluster_sources(recs: list, cluster_field: str = "file") -> dict:
    """How many units were clustered by `cluster_field`, by the snippet id (field missing), or alone (both missing)."""
    seen: dict = {}
    for r in recs:
        if r.get("task", "rename") != "rename" or (r.get("metrics") or {}).get("core_ok") is None:
            continue
        seen[(r.get("pack"), r["unit_id"])] = "field" if r.get(cluster_field) else ("snippet_id" if r.get("snippet_id") else "unit")
    out = {"field": 0, "snippet_id": 0, "unit": 0}
    for v in seen.values():
        out[v] += 1
    return out


def unit_means(d: dict) -> dict:
    return {u: sum(v) / len(v) for u, v in d.items() if v}


def paired(a: dict, b: dict) -> tuple:
    """Per-unit means of a and b on the units present in both.  Returns (units, deltas a - b, up, down, tie)."""
    ma, mb = unit_means(a), unit_means(b)
    units = sorted(set(ma) & set(mb))
    deltas = [round(ma[u] - mb[u], 12) for u in units]
    return units, deltas, sum(d > 0 for d in deltas), sum(d < 0 for d in deltas), sum(d == 0 for d in deltas)


def eligibility(idx: dict, packs, none_cond: str = "none", threshold: float = ELIGIBILITY_THRESHOLD) -> list:
    """Section 2.3.  value = mean over the models of (mean over the dev units of the unit means of `none`)."""
    out = []
    for pack in packs:
        per_model = {}
        for (split, p, model, cond), d in idx.items():
            if split == "dev" and p == pack and cond == none_cond:
                m = mean(list(unit_means(d).values()))
                if m is not None:
                    per_model[model] = m
        value = round(mean(list(per_model.values())), 12) if per_model else None     # 0.85/0.95 must give exactly 0.9
        out.append({"pack": pack, "value": value, "n_models": len(per_model), "per_model": per_model,
                    "eligible": None if value is None else value < threshold})
    return out


def h1_status(elig: list, rows: list) -> str:
    """Whether H1 can be tested (Section 2.3).  `not_testable`: dev data exist but no standard is below the threshold;
    `no_dev_data`: no standard has dev data; `no_test_data`: a standard is eligible but has no paired test units;
    `testable` otherwise."""
    if not any(e["value"] is not None for e in elig):
        return "no_dev_data"
    if not any(e["eligible"] for e in elig):
        return "not_testable"
    return "testable" if rows else "no_test_data"


def models_of(idx: dict, pack: str, split: str = "test") -> list:
    return sorted({m for (s, p, m, _c) in idx if s == split and p == pack and m is not None})


def _cell(idx, pack, model, cond, split="test"):
    return idx.get((split, pack, model, cond), {})


def h1(idx: dict, eligible_packs, sel: str = "graph", none_cond: str = "none") -> list:
    """Selection vs none on the test units: one row per (eligible pack, model); Holm over exactly these rows."""
    rows = []
    for pack in eligible_packs:
        for model in models_of(idx, pack):
            units, deltas, up, dn, tie = paired(_cell(idx, pack, model, sel), _cell(idx, pack, model, none_cond))
            if not units:
                continue
            rows.append({"pack": pack, "model": model, "units": len(units), "up": up, "down": dn, "tie": tie,
                         "mean_diff_pp": 100 * mean(deltas), "p": sign_test_p(up, dn)})
    for row, ap in zip(rows, holm([r["p"] for r in rows])):
        row["p_holm"] = ap
        row["supports"] = ap < ALPHA and row["mean_diff_pp"] > 0
    return rows


def cluster_bootstrap_ci(units: list, deltas: list, clusters: dict, pack: str, b: int = BOOT_B,
                         seed: int = BOOT_SEED) -> tuple:
    """Percentile 95% CI of the mean of `deltas`, resampling whole clusters with replacement."""
    groups: dict = defaultdict(list)
    for u, d in zip(units, deltas):
        groups[clusters.get((pack, u), u)].append(d)
    keys = sorted(groups, key=str)
    sums = [sum(groups[k]) for k in keys]
    sizes = [len(groups[k]) for k in keys]
    rng = random.Random(seed)
    k = len(keys)
    means = []
    for _ in range(b):
        s = n = 0
        for _j in range(k):
            i = rng.randrange(k)
            s += sums[i]
            n += sizes[i]
        means.append(s / n)
    means.sort()
    return means[int(0.025 * b)], means[min(b - 1, int(0.975 * b))]


def h3_noninferiority(idx: dict, clusters: dict, packs, sel: str = "graph", ref: str = "fulldoc",
                      margin: float = NI_MARGIN, b: int = BOOT_B, seed: int = BOOT_SEED) -> list:
    """Selection vs fulldoc per (pack, model).  non-inferior: lower limit > -margin; inferior: upper limit < -margin;
    otherwise inconclusive.  No multiplicity correction (Section 4)."""
    rows = []
    for pack in packs:
        for model in models_of(idx, pack):
            units, deltas, _u, _d, _t = paired(_cell(idx, pack, model, sel), _cell(idx, pack, model, ref))
            if not units:
                continue
            lo, hi = cluster_bootstrap_ci(units, deltas, clusters, pack, b, seed)
            verdict = "non-inferior" if lo > -margin else ("inferior" if hi < -margin else "inconclusive")
            rows.append({"pack": pack, "model": model, "units": len(units),
                         "clusters": len({clusters.get((pack, u), u) for u in units}),
                         "mean_diff_pp": 100 * mean(deltas), "ci_low_pp": 100 * lo, "ci_high_pp": 100 * hi,
                         "verdict": verdict})
    return rows


def h3_retrieval(idx: dict, packs, sel: str = "graph", baselines=RETRIEVAL_BASELINES) -> list:
    """Selection vs each retrieval baseline (paired exact sign test); one Holm family over all rows."""
    rows = []
    for pack in packs:
        for model in models_of(idx, pack):
            for cond in baselines:
                units, deltas, up, dn, tie = paired(_cell(idx, pack, model, sel), _cell(idx, pack, model, cond))
                if not units:
                    continue
                rows.append({"pack": pack, "model": model, "baseline": cond, "units": len(units), "up": up,
                             "down": dn, "tie": tie, "mean_diff_pp": 100 * mean(deltas),
                             "p": sign_test_p(up, dn)})
    for row, ap in zip(rows, holm([r["p"] for r in rows])):
        row["p_holm"] = ap
        row["higher"] = ap < ALPHA and row["mean_diff_pp"] > 0
    return rows


def analyse(recs: list, packs=DEFAULT_PACKS, sel: str = "graph", none_cond: str = "none", fulldoc: str = "fulldoc",
            model_field: str = "backend", cluster_field: str = "file", b: int = BOOT_B,
            seed: int = BOOT_SEED, models=None) -> dict:
    matched = None
    if models:
        recs, matched = select_models(recs, models, model_field)
    idx, clusters = build_index(recs, model_field, cluster_field)
    elig = eligibility(idx, packs, none_cond)
    eligible = [e["pack"] for e in elig if e["eligible"]]
    h1_rows = h1(idx, eligible, sel, none_cond)
    return {"settings": {"packs": list(packs), "selection": sel, "none": none_cond, "fulldoc": fulldoc,
                         "threshold": ELIGIBILITY_THRESHOLD, "margin_pp": 100 * NI_MARGIN, "alpha": ALPHA,
                         "bootstrap_b": b, "bootstrap_seed": seed, "model_field": model_field,
                         "cluster_field": cluster_field,
                         "models": matched,
                         "cluster_sources": cluster_sources(recs, cluster_field)},
            "eligibility": elig,
            "h1_status": h1_status(elig, h1_rows),
            "h1": h1_rows,
            "h3_noninferiority": h3_noninferiority(idx, clusters, packs, sel, fulldoc, NI_MARGIN, b, seed),
            "h3_retrieval": h3_retrieval(idx, packs, sel)}


def _table(headers, rows):
    out = ["| " + " | ".join(headers) + " |", "|" + "|".join(["---"] * len(headers)) + "|"]
    out += ["| " + " | ".join(str(c) for c in r) + " |" for r in rows]
    return "\n".join(out)


def _g(x):
    return f"{x:.3g}"


def render(res: dict) -> str:
    s = res["settings"]
    out = ["# Confirmatory analysis (HYPOTHESES_v2 Sections 2.3 and 4)", "",
           f"Selection condition `{s['selection']}`; baselines `{s['none']}` / `{s['fulldoc']}`; packs: "
           f"{', '.join(s['packs'])}. " + (f"Models: {', '.join(s['models'])}. " if s.get("models") else "") + f"Test split for the comparisons, dev split for eligibility. "
           f"Unit = one task, mean of `core_ok` over its repeats.", "",
           "## Eligibility for H1 (zero-shot compliance on dev, mean over models; eligible if below "
           f"{s['threshold']:.2f})", ""]
    rows = []
    for e in res["eligibility"]:
        pm = ", ".join(f"{m}: {v:.3f}" for m, v in sorted(e["per_model"].items()))
        rows.append([e["pack"], "-" if e["value"] is None else f"{e['value']:.3f}", e["n_models"],
                     {True: "yes", False: "no", None: "no dev data"}[e["eligible"]], pm])
    out += [_table(["pack", "zero-shot (dev)", "models", "in H1", "per model"], rows), ""]
    out += ["## H1: selection vs none (own Holm family, two-sided exact sign test)", ""]
    if res["h1"]:
        out += [_table(["pack", "model", "units", "better", "worse", "tied", "mean diff (pp)", "p", "p (Holm)",
                        "supports H1"],
                       [[r["pack"], r["model"], r["units"], r["up"], r["down"], r["tie"],
                         f"{r['mean_diff_pp']:+.1f}", _g(r["p"]), _g(r["p_holm"]), "yes" if r["supports"] else "no"]
                        for r in res["h1"]]), "",
                f"Holm family: {len(res['h1'])} tests; supports H1 = adjusted p < {s['alpha']} and a positive mean difference.", ""]
    else:
        out += [{"not_testable": f"H1 is not testable: no standard has zero-shot compliance below {s['threshold']:.2f} "
                                 "(Section 2.3). No confirmatory test is performed; the selection comparisons below "
                                 "are secondary.",
                 "no_dev_data": "H1 cannot be assessed: no standard has dev data for the eligibility rule.",
                 "no_test_data": "H1: an eligible standard has no paired test units.",
                 }.get(res.get("h1_status"), "No eligible pack with test data."), ""]
    out += [f"## H3: selection vs {s['fulldoc']}, non-inferiority margin {s['margin_pp']:.0f} pp "
            f"(cluster bootstrap 95% CI, {s['bootstrap_b']} resamples, seed {s['bootstrap_seed']})", "",
            f"Clusters are defined by `{s['cluster_field']}`; units clustered by it: {s['cluster_sources']['field']}, "
            f"by snippet id because the field is missing: {s['cluster_sources']['snippet_id']}, "
            f"alone: {s['cluster_sources']['unit']}.", ""]
    out += [_table(["pack", "model", "units", "clusters", "mean diff (pp)", "95% CI (pp)", "verdict"],
                   [[r["pack"], r["model"], r["units"], r["clusters"], f"{r['mean_diff_pp']:+.1f}",
                     f"[{r['ci_low_pp']:+.1f}, {r['ci_high_pp']:+.1f}]", r["verdict"]]
                    for r in res["h3_noninferiority"]]), "",
            "non-inferior: lower limit above the negative margin; inferior: upper limit below it; otherwise inconclusive. "
            "No multiplicity correction.", ""]
    out += ["## H3: selection vs retrieval baselines (paired exact sign test, one Holm family)", ""]
    if res["h3_retrieval"]:
        out += [_table(["pack", "model", "baseline", "units", "better", "worse", "tied", "mean diff (pp)", "p",
                        "p (Holm)", "selection higher"],
                       [[r["pack"], r["model"], r["baseline"], r["units"], r["up"], r["down"], r["tie"],
                         f"{r['mean_diff_pp']:+.1f}", _g(r["p"]), _g(r["p_holm"]), "yes" if r["higher"] else "no"]
                        for r in res["h3_retrieval"]]), "",
                f"Holm family: {len(res['h3_retrieval'])} tests.", ""]
    else:
        out += ["No retrieval baseline with test data.", ""]
    return "\n".join(out)


def run(run_dirs, **kw) -> tuple:
    recs, errors = load_trials(run_dirs)
    res = analyse(recs, **kw)
    res["n_trials"] = len(recs)
    res["n_error_keys"] = len(errors)
    return res, render(res)


def dumps(res: dict) -> str:
    return json.dumps(res, indent=2, sort_keys=True)
