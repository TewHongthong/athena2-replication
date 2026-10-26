"""Secondary and exploratory analyses of HYPOTHESES_v2.md (H2 to H6, and the assistant comparison kept for future work): the statistical skeleton.

None of these hypotheses is confirmatory.  Every threshold is an argument; the defaults below are the nominal values
of HYPOTHESES_v2.md, Section 2.4.  The assistant comparison has no default margin.  No p-value or interval computed here enters the Holm family of H1 (confirmatory.py).

* H2: Spearman correlation, across (standard, model) cells, between the zero-shot compliance (`none`) and the
  effect of selection (selection - none); permutation p-value (exact for up to 8 cells, Monte Carlo otherwise).
  The cells share their tasks across models, so they are not independent; the report says so.
* H4: compliance of the LLM-drafted ontology minus the human one (cluster-bootstrap CI, equivalence margin) and the
  attribute-level Cohen's kappa of the two ontologies.
* H5: compliance with kind inferred from the code minus compliance with kind from metadata (non-inferiority).
* H6: catch rate and false alarms of the scope-aware check against the scope-blind check, from labelled cases
  (a conflict case or a rename to a fresh name).  The labels come from the hand-written cases, not from the trials.
* Assistant comparison (outside the scope of the study, kept for future work): coding assistants with an always-on rules file against full document, no rules file against `none`, and
  selection against both (equivalence or superiority; cluster-bootstrap CI).
* Dose-response: compliance of every condition against the size of the prompt (`prompt_chars`), per (standard,
  model) cell, with a Spearman correlation across the conditions (exact permutation p-value), and, within selection,
  the correlation between the context it adds and the gain of each unit.  Descriptive: the conditions differ in more
  than size, so no causal reading and no hypothesis threshold.

Standard library only.  Statistics shared with the confirmatory analysis (sign test, cluster bootstrap) are reused.
"""
from __future__ import annotations

import csv
import itertools
import json
import math
import random
from collections import defaultdict
from statistics import median

from .confirmatory import (ALPHA, BOOT_B, BOOT_SEED, build_index, cluster_bootstrap_ci, cluster_sources,
                           models_of, paired, unit_means)
from .report import load_trials, mean, sign_test_p

PERM_B = 10000
PERM_SEED = 20261020              # fixed so that the Monte Carlo p-values can be reproduced
PERM_EXACT_MAX = 8                # up to 8 cells: all 8! = 40,320 permutations
H4_MARGIN = 0.05                  # nominal: LLM ontology within 5 pp of the human one
H4_KAPPA = 0.6                    # nominal: attribute-level kappa at least 0.6
H5_MARGIN = 0.05                  # nominal: kind inference lowers compliance by at most 5 pp


# ----------------------------------------------------------------------------------------------- basic statistics

def ranks(xs: list) -> list:
    """Average ranks (1-based); values equal after rounding to 12 places share a rank."""
    xs = [round(x, 12) for x in xs]
    order = sorted(range(len(xs)), key=lambda i: xs[i])
    out = [0.0] * len(xs)
    i = 0
    while i < len(order):
        j = i
        while j + 1 < len(order) and xs[order[j + 1]] == xs[order[i]]:
            j += 1
        for k in range(i, j + 1):
            out[order[k]] = (i + j) / 2 + 1
        i = j + 1
    return out


def pearson(a: list, b: list):
    n = len(a)
    if n < 2:
        return None
    ma, mb = sum(a) / n, sum(b) / n
    sa = sum((x - ma) ** 2 for x in a)
    sb = sum((y - mb) ** 2 for y in b)
    if sa == 0 or sb == 0:
        return None
    return sum((x - ma) * (y - mb) for x, y in zip(a, b)) / math.sqrt(sa * sb)


def spearman_permutation(x: list, y: list, b: int = PERM_B, seed: int = PERM_SEED) -> tuple:
    """Return (rho, two-sided permutation p, method).  rho is None (and p None) with fewer than 3 pairs or when one
    variable is constant."""
    n = len(x)
    if n < 3 or n != len(y):
        return None, None, "n<3"
    rx, ry = ranks(x), ranks(y)
    rho = pearson(rx, ry)
    if rho is None:
        return None, None, "constant"
    eps = 1e-12
    if n <= PERM_EXACT_MAX:
        total = hits = 0
        for perm in itertools.permutations(ry):
            total += 1
            r = pearson(rx, list(perm))
            if r is not None and abs(r) >= abs(rho) - eps:
                hits += 1
        return rho, hits / total, "exact"
    rng = random.Random(seed)
    hits = 0
    py = list(ry)
    for _ in range(b):
        rng.shuffle(py)
        r = pearson(rx, py)
        if r is not None and abs(r) >= abs(rho) - eps:
            hits += 1
    return rho, (hits + 1) / (b + 1), "monte-carlo"


def cohen_kappa(a: list, b: list) -> dict:
    """Cohen's kappa of two label sequences of the same length (one label per attribute).  kappa is None when the
    chance agreement is 1 (both raters used one and the same single label)."""
    if len(a) != len(b):
        raise ValueError("the two label lists differ in length")
    n = len(a)
    if n == 0:
        return {"n": 0, "agreement": None, "kappa": None}
    po = sum(x == y for x, y in zip(a, b)) / n
    pe = sum((a.count(c) / n) * (b.count(c) / n) for c in set(a) | set(b))
    kappa = None if pe >= 1 - 1e-12 else (po - pe) / (1 - pe)
    return {"n": n, "agreement": po, "kappa": kappa}


def clopper_pearson_lower(k: int, n: int, alpha: float = ALPHA) -> float:
    """One-sided lower confidence limit (level 1 - alpha) of a binomial proportion with k successes in n trials."""
    if n <= 0:
        raise ValueError("n must be positive")
    if k <= 0:
        return 0.0

    def tail(p):                       # P(X >= k) for X ~ Binomial(n, p); increasing in p
        return sum(math.comb(n, i) * p ** i * (1 - p) ** (n - i) for i in range(k, n + 1))

    lo, hi = 0.0, 1.0
    for _ in range(80):
        mid = (lo + hi) / 2
        if tail(mid) < alpha:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


# ------------------------------------------------------------------------------------------------------------ cells

def _cell(idx: dict, pack, model, cond, split: str = "test") -> dict:
    return idx.get((split, pack, model, cond), {})


def h2(idx: dict, packs, sel: str = "graph", none_cond: str = "none", b: int = PERM_B, seed: int = PERM_SEED) -> dict:
    """Spearman correlation between zero-shot compliance and (selection - none) over the (pack, model) cells that
    have both conditions on the test split.  Anchor packs can be added to `packs`."""
    cells = []
    for pack in packs:
        for model in models_of(idx, pack):
            units, deltas, _u, _d, _t = paired(_cell(idx, pack, model, sel), _cell(idx, pack, model, none_cond))
            if not units:
                continue
            nm = unit_means(_cell(idx, pack, model, none_cond))
            cells.append({"pack": pack, "model": model, "units": len(units),
                          "zero_shot": mean([nm[u] for u in units]), "effect_pp": 100 * mean(deltas)})
    rho, p, method = spearman_permutation([c["zero_shot"] for c in cells], [c["effect_pp"] for c in cells], b, seed)
    return {"cells": cells, "n_cells": len(cells), "rho": rho, "p": p, "method": method,
            "supports": None if rho is None else (rho < 0 and p < ALPHA)}


def contrast(idx_a: dict, idx_b: dict, clusters: dict, packs, cond_a: str, cond_b: str, model_a=None, model_b=None,
             split: str = "test", b: int = BOOT_B, seed: int = BOOT_SEED) -> list:
    """Paired difference a - b per (pack, model) on the units present in both: per-unit means over the repeats, mean
    difference, cluster-bootstrap 95% CI and the counts for the sign test.  With no model labels the cells of the
    same model in both indexes are paired; with labels, the cell (model_a, cond_a) of idx_a against the cell
    (model_b, cond_b) of idx_b (for assistants and models that carry different labels)."""
    if (model_a is None) != (model_b is None):
        raise ValueError("give both model labels or neither")
    rows = []
    for pack in packs:
        if model_a is None:
            pairs = [(m, m) for m in sorted(set(models_of(idx_a, pack, split)) & set(models_of(idx_b, pack, split)))]
        else:
            pairs = [(model_a, model_b)]
        for ma, mb in pairs:
            units, deltas, up, dn, tie = paired(_cell(idx_a, pack, ma, cond_a, split), _cell(idx_b, pack, mb, cond_b, split))
            if not units:
                continue
            lo, hi = cluster_bootstrap_ci(units, deltas, clusters, pack, b, seed)
            rows.append({"pack": pack, "model": ma if ma == mb else f"{ma} vs {mb}", "units": len(units),
                         "clusters": len({clusters.get((pack, u), u) for u in units}),
                         "mean_diff_pp": 100 * mean(deltas), "ci_low_pp": 100 * lo, "ci_high_pp": 100 * hi,
                         "up": up, "down": dn, "tie": tie, "p": sign_test_p(up, dn)})
    return rows


def verdict_equivalence(lo: float, hi: float, margin: float) -> str:
    """CI inside (-margin, +margin): within the margin; CI wholly outside it: outside; otherwise inconclusive."""
    if lo > -margin and hi < margin:
        return "within margin"
    if hi < -margin or lo > margin:
        return "outside margin"
    return "inconclusive"


def verdict_noninferior(lo: float, hi: float, margin: float) -> str:
    """Lower limit above -margin: non-inferior; upper limit below -margin: inferior; otherwise inconclusive."""
    if lo > -margin:
        return "non-inferior"
    if hi < -margin:
        return "inferior"
    return "inconclusive"


def verdict_superior(lo: float, hi: float) -> str:
    if lo > 0:
        return "higher"
    if hi < 0:
        return "lower"
    return "inconclusive"


def _with_verdict(rows: list, fn) -> list:
    for r in rows:
        r["verdict"] = fn(r["ci_low_pp"] / 100, r["ci_high_pp"] / 100)
    return rows


def h4(idx_human: dict, idx_llm: dict, clusters: dict, packs, sel: str = "graph", margin: float = H4_MARGIN,
       kappa_pairs: list | None = None, kappa_min: float = H4_KAPPA, b: int = BOOT_B, seed: int = BOOT_SEED,
       agreement: dict | None = None) -> dict:
    """LLM-drafted ontology minus human ontology (condition `sel` in both), equivalence within `margin`; and the
    agreement of the two ontologies.  `agreement` = result of `agreement.compare_packs` (kappa by identifier kind,
    HYPOTHESES_v2.md Section 3.1): its pooled kappa is the kappa of H4 and is compared with `kappa_min`; the
    informative-items kappa is a secondary figure with no threshold.  Without `agreement`, the kappa of
    `kappa_pairs` = [(human label, llm label), ...] is used when given."""
    rows = contrast(idx_llm, idx_human, clusters, packs, sel, sel, b=b, seed=seed)
    _with_verdict(rows, lambda lo, hi: verdict_equivalence(lo, hi, margin))
    out = {"margin_pp": 100 * margin, "kappa_min": kappa_min, "compliance": rows, "kappa": None}
    out["agreement"] = None
    if agreement is not None:
        pool = agreement["pooled"]
        k = {"n": pool["n_items"], "agreement": pool["observed_agreement"], "kappa": pool["kappa"]}
        k["meets"] = None if k["kappa"] is None else k["kappa"] >= kappa_min
        out["kappa"] = k
        out["agreement"] = {
            "informative": pool["informative_items"],
            "packs": {name: {"matched_units": len(r["matched_units"]), "n_items": r["n_items"],
                             "agreement": r["observed_agreement"], "kappa": r["kappa"],
                             "ci95": r["kappa_ci95_unit_bootstrap"],
                             "human_only": len(r["human_only_units"]), "llm_only": len(r["llm_only_units"])}
                      for name, r in agreement.items() if name != "pooled"}}
    elif kappa_pairs:
        k = cohen_kappa([a for a, _ in kappa_pairs], [c for _, c in kappa_pairs])
        k["meets"] = None if k["kappa"] is None else k["kappa"] >= kappa_min
        out["kappa"] = k
    return out


def h5(idx_meta: dict, idx_inferred: dict, clusters: dict, packs, sel: str = "graph", margin: float = H5_MARGIN,
       b: int = BOOT_B, seed: int = BOOT_SEED) -> dict:
    """Kind inferred from the code minus kind from metadata (condition `sel` in both), non-inferiority at `margin`."""
    rows = contrast(idx_inferred, idx_meta, clusters, packs, sel, sel, b=b, seed=seed)
    _with_verdict(rows, lambda lo, hi: verdict_noninferior(lo, hi, margin))
    return {"margin_pp": 100 * margin, "rows": rows}


def h6(labels: list, alpha: float = ALPHA) -> dict:
    """labels: one dict per proposed rename with boolean `breaks` (ground truth: the rename conflicts with another binding in scope),
    `aware` and `blind` (the scope-aware / scope-blind check flagged the rename).  H6 is supported when the aware
    check flags every rename that breaks, flags fewer harmless renames than the blind check, and the exact sign
    test on the discordant harmless renames gives p < alpha."""
    breaking = [r for r in labels if r["breaks"]]
    harmless = [r for r in labels if not r["breaks"]]
    caught_aware = sum(bool(r["aware"]) for r in breaking)
    caught_blind = sum(bool(r["blind"]) for r in breaking)
    fa_aware = sum(bool(r["aware"]) for r in harmless)
    fa_blind = sum(bool(r["blind"]) for r in harmless)
    aware_only = sum(bool(r["aware"]) and not r["blind"] for r in harmless)
    blind_only = sum(bool(r["blind"]) and not r["aware"] for r in harmless)
    p = sign_test_p(blind_only, aware_only)
    n = len(breaking)
    return {"n": len(labels), "n_breaking": n, "n_harmless": len(harmless),
            "caught_aware": caught_aware, "caught_blind": caught_blind,
            "catch_rate_aware": None if n == 0 else caught_aware / n,
            "catch_rate_aware_lower": None if n == 0 else clopper_pearson_lower(caught_aware, n, alpha),
            "catch_rate_blind": None if n == 0 else caught_blind / n,
            "false_alarms_aware": fa_aware, "false_alarms_blind": fa_blind,
            "aware_only": aware_only, "blind_only": blind_only, "p": p,
            "supports": bool(n) and caught_aware == n and fa_aware < fa_blind and p < alpha}


def h7(idx_assistant: dict, idx_ref: dict, clusters: dict, packs, asst_model: str, ref_model: str,
       rules_cond: str, norules_cond: str, margin: float | None, unknown_packs=(), sel: str = "graph",
       none_cond: str = "none", fulldoc: str = "fulldoc", b: int = BOOT_B, seed: int = BOOT_SEED) -> dict:
    """Assistant (idx_assistant, label asst_model) against the LLM runs (idx_ref, label ref_model).
    rules_vs_fulldoc and norules_vs_none: equivalence within `margin` (required: it is not registered yet);
    selection_vs_rules and selection_vs_norules: superiority, only on `unknown_packs` (the standards the model
    does not know)."""
    if margin is None:
        raise ValueError("the equivalence margin of H7 is not registered; pass it explicitly")
    kw = dict(split="test", b=b, seed=seed)
    eq = lambda lo, hi: verdict_equivalence(lo, hi, margin)
    out = {"margin_pp": 100 * margin, "unknown_packs": list(unknown_packs)}
    out["rules_vs_fulldoc"] = _with_verdict(contrast(idx_assistant, idx_ref, clusters, packs, rules_cond, fulldoc,
                                                     asst_model, ref_model, **kw), eq)
    out["norules_vs_none"] = _with_verdict(contrast(idx_assistant, idx_ref, clusters, packs, norules_cond, none_cond,
                                                    asst_model, ref_model, **kw), eq)
    out["selection_vs_rules"] = _with_verdict(contrast(idx_ref, idx_assistant, clusters, unknown_packs, sel, rules_cond,
                                                       ref_model, asst_model, **kw), verdict_superior)
    out["selection_vs_norules"] = _with_verdict(contrast(idx_ref, idx_assistant, clusters, unknown_packs, sel,
                                                         norules_cond, ref_model, asst_model, **kw), verdict_superior)
    return out


# ------------------------------------------------------------------------------------------------------ input files

# ------------------------------------------------------------------------------------------------ dose-response

def build_dose(recs: list, model_field: str = "backend") -> dict:
    """dose[(split, pack, model, condition)][unit_id] = [prompt_chars per repeat] for the trials that have a graded
    outcome (the same trials as `build_index`).  The dose is the size of the prompt the model received, so it covers
    every condition on one scale: `none` is the code alone, `fulldoc` the largest."""
    dose: dict = defaultdict(lambda: defaultdict(list))
    for r in recs:
        if r.get("task", "rename") != "rename" or (r.get("metrics") or {}).get("core_ok") is None:
            continue
        chars = r.get("prompt_chars")
        if chars is None:
            continue
        dose[(r.get("split"), r.get("pack"), r.get(model_field), r.get("condition"))][r["unit_id"]].append(float(chars))
    return dose


def _conditions(idx: dict, split: str, pack: str, model) -> list:
    return sorted({c for (s, p, m, c) in idx if (s, p, m) == (split, pack, model) and c is not None})


def dose_curve(idx: dict, dose: dict, pack: str, model, none_cond: str = "none", split: str = "test",
               b: int = PERM_B, seed: int = PERM_SEED):
    """One (standard, model) cell: compliance of every condition against its mean prompt size, over the units that
    every condition has.  Returns None with fewer than 3 conditions or no common unit."""
    per = {}
    for c in _conditions(idx, split, pack, model):
        per[c] = (unit_means(_cell(idx, pack, model, c, split)), unit_means(dose.get((split, pack, model, c), {})))
    if len(per) < 3:
        return None
    common = set.intersection(*[set(comp) & set(chars) for comp, chars in per.values()])
    if not common:
        return None
    units = sorted(common)
    rows = [{"condition": c, "chars": mean([per[c][1][u] for u in units]),
             "compliance": mean([per[c][0][u] for u in units])} for c in per]
    rows.sort(key=lambda r: (r["chars"], r["condition"]))
    base = next((r for r in rows if r["condition"] == none_cond), None)
    for r in rows:
        r["added_chars"] = None if base is None else r["chars"] - base["chars"]
        r["effect_pp"] = None if base is None else 100 * (r["compliance"] - base["compliance"])
    rho, p, method = spearman_permutation([r["chars"] for r in rows], [r["compliance"] for r in rows], b, seed)
    best = max(rows, key=lambda r: (r["compliance"], -r["chars"]))        # a tie goes to the smaller context
    largest = rows[-1]
    return {"pack": pack, "model": model, "units": len(units), "n_conditions": len(rows), "rows": rows,
            "rho": rho, "p": p, "method": method, "best": best["condition"], "best_compliance": best["compliance"],
            "largest": largest["condition"], "largest_compliance": largest["compliance"],
            "largest_is_best": largest["compliance"] >= best["compliance"] - 1e-12}


def dose_units(idx: dict, dose: dict, packs, sel: str = "graph", none_cond: str = "none", split: str = "test",
               b: int = PERM_B, seed: int = PERM_SEED) -> list:
    """Within selection: Spearman correlation, over the units of a (standard, model) cell, between the context that
    selection adds to the prompt (characters, against `none`) and the gain of the unit (selection - none)."""
    rows = []
    for pack in packs:
        for model in models_of(idx, pack, split):
            s, n = unit_means(_cell(idx, pack, model, sel, split)), unit_means(_cell(idx, pack, model, none_cond, split))
            ds = unit_means(dose.get((split, pack, model, sel), {}))
            dn = unit_means(dose.get((split, pack, model, none_cond), {}))
            units = sorted(set(s) & set(n) & set(ds) & set(dn))
            if len(units) < 3:
                continue
            added = [ds[u] - dn[u] for u in units]
            gain = [s[u] - n[u] for u in units]
            rho, p, method = spearman_permutation(added, gain, b, seed)
            rows.append({"pack": pack, "model": model, "units": len(units), "median_added_chars": median(added),
                         "rho": rho, "p": p, "method": method})
    return rows


def dose_response(idx: dict, dose: dict, packs, sel: str = "graph", none_cond: str = "none", split: str = "test",
                  b: int = PERM_B, seed: int = PERM_SEED) -> dict:
    cells = []
    for pack in packs:
        for model in models_of(idx, pack, split):
            cell = dose_curve(idx, dose, pack, model, none_cond, split, b, seed)
            if cell is not None:
                cells.append(cell)
    rhos = [c["rho"] for c in cells if c["rho"] is not None]
    summary = {"n_cells": len(cells), "n_rho": len(rhos), "n_positive": sum(1 for r in rhos if r > 0),
               "n_negative": sum(1 for r in rhos if r < 0), "median_rho": median(rhos) if rhos else None,
               "n_largest_best": sum(1 for c in cells if c["largest_is_best"])}
    return {"cells": cells, "summary": summary, "units": dose_units(idx, dose, packs, sel, none_cond, split, b, seed),
            "selection": sel, "none": none_cond}


def read_kappa_csv(path: str) -> list:
    """CSV with a header and the columns `human` and `llm` (one row per attribute); other columns are ignored."""
    with open(path, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    if not rows or "human" not in rows[0] or "llm" not in rows[0]:
        raise ValueError(f"{path}: need a header with the columns human and llm")
    return [(r["human"].strip(), r["llm"].strip()) for r in rows]


def _flag(v) -> bool:
    s = str(v).strip().lower()
    if s in ("1", "true", "yes", "y"):
        return True
    if s in ("0", "false", "no", "n", ""):
        return False
    raise ValueError(f"not a 0/1 flag: {v!r}")


def read_h6_csv(path: str) -> list:
    """CSV with a header and the columns `breaks`, `aware`, `blind` (0/1, true/false) per proposed rename."""
    with open(path, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    need = ("breaks", "aware", "blind")
    if not rows or any(c not in rows[0] for c in need):
        raise ValueError(f"{path}: need a header with the columns breaks, aware, blind")
    return [{c: _flag(r[c]) for c in need} for r in rows]


def load_dose(run_dirs, model_field: str = "backend", cluster_field: str = "file") -> tuple:
    """`load_index` plus the prompt sizes: (idx, clusters, n_trials, cluster_sources, dose)."""
    recs, _errors = load_trials(run_dirs)
    idx, clusters = build_index(recs, model_field, cluster_field)
    return idx, clusters, len(recs), cluster_sources(recs, cluster_field), build_dose(recs, model_field)


def load_index(run_dirs, model_field: str = "backend", cluster_field: str = "file") -> tuple:
    """(idx, clusters, n_trials, cluster_sources) of one group of run folders."""
    recs, _errors = load_trials(run_dirs)
    idx, clusters = build_index(recs, model_field, cluster_field)
    return idx, clusters, len(recs), cluster_sources(recs, cluster_field)


def merge_clusters(*dicts) -> dict:
    out: dict = {}
    for d in dicts:
        out.update(d)
    return out


# ---------------------------------------------------------------------------------------------------------- report

def _table(headers, rows):
    out = ["| " + " | ".join(headers) + " |", "|" + "|".join(["---"] * len(headers)) + "|"]
    out += ["| " + " | ".join(str(c) for c in r) + " |" for r in rows]
    return "\n".join(out)


def _g(x):
    return "-" if x is None else f"{x:.3g}"


def _contrast_table(rows: list) -> str:
    if not rows:
        return "No cell with test data in both conditions."
    return _table(["pack", "model", "units", "clusters", "mean diff (pp)", "95% CI (pp)", "better", "worse", "tied",
                   "verdict"],
                  [[r["pack"], r["model"], r["units"], r["clusters"], f"{r['mean_diff_pp']:+.1f}",
                    f"[{r['ci_low_pp']:+.1f}, {r['ci_high_pp']:+.1f}]", r["up"], r["down"], r["tie"], r["verdict"]]
                   for r in rows])


NOTE = ("Exploratory: thresholds are those of HYPOTHESES_v2.md, no multiplicity correction, and nothing here "
        "enters the Holm family of H1.")


def render_h2(res: dict) -> str:
    out = ["# H2: effect of selection against zero-shot compliance", "", NOTE, "",
           "Cells are (standard, model) pairs on the test split; zero-shot = mean `none` compliance, effect = mean "
           "(selection - none) in pp. The cells of one standard share their tasks across models, so they are not "
           "independent and the permutation p-value is optimistic.", ""]
    out += [_table(["pack", "model", "units", "zero-shot", "effect (pp)"],
                   [[c["pack"], c["model"], c["units"], f"{c['zero_shot']:.3f}", f"{c['effect_pp']:+.1f}"]
                    for c in res["cells"]]), ""]
    if res["rho"] is None:
        out.append(f"No correlation: {res['n_cells']} usable cells ({res['method']}).")
    else:
        out.append(f"Spearman rho = {res['rho']:+.3f} over {res['n_cells']} cells; two-sided permutation p = "
                   f"{_g(res['p'])} ({res['method']}); supports H2 (negative, p < {ALPHA}): "
                   f"{'yes' if res['supports'] else 'no'}.")
    return "\n".join(out) + "\n"


def render_h4(res: dict) -> str:
    out = ["# H4: LLM-drafted ontology against the human ontology", "", NOTE, "",
           f"Difference = LLM ontology - human ontology in `core_ok`; equivalence margin {res['margin_pp']:.0f} pp "
           "(cluster-bootstrap 95% CI).", "", _contrast_table(res["compliance"]), ""]
    k = res["kappa"]
    ag = res.get("agreement")
    what = "Kappa by identifier kind, pooled over the standards" if ag else "Attribute-level kappa"
    unit = "unit-attribute items" if ag else "attributes"
    if k is None:
        out.append("Attribute-level kappa: no label file or ontologies given.")
    elif k["kappa"] is None:
        out.append(f"{what} undefined over {k['n']} {unit} (chance agreement 1 or no common kind); "
                   f"agreement {_g(k['agreement'])}.")
    else:
        out.append(f"{what} = {k['kappa']:.3f} over {k['n']} {unit} (agreement "
                   f"{k['agreement']:.3f}); threshold {res['kappa_min']:.2f}: {'met' if k['meets'] else 'not met'}.")
    if ag:
        out += ["", _table(["pack", "common kinds", "items", "agreement", "kappa", "95% CI over kinds",
                            "human-only kinds", "LLM-only kinds"],
                           [[n, p["matched_units"], p["n_items"],
                             "-" if p["agreement"] is None else f"{p['agreement']:.3f}",
                             "-" if p["kappa"] is None else f"{p['kappa']:.3f}",
                             "-" if not p["ci95"] else f"[{p['ci95'][0]:.3f}, {p['ci95'][1]:.3f}]",
                             p["human_only"], p["llm_only"]] for n, p in ag["packs"].items()]), ""]
        inf = ag["informative"]
        if inf["kappa"] is None:
            out.append(f"Secondary (items in which at least one ontology fixes a value; post hoc, no threshold): "
                       f"undefined over {inf['n']} items.")
        else:
            out.append(f"Secondary (items in which at least one ontology fixes a value; post hoc, no threshold): "
                       f"kappa = {inf['kappa']:.3f} over {inf['n']} items (agreement {inf['observed_agreement']:.3f}).")
    return "\n".join(out) + "\n"


def render_h5(res: dict) -> str:
    return "\n".join(["# H5: kind inferred from the code against kind from metadata", "", NOTE, "",
                      f"Difference = inferred - metadata in `core_ok`; non-inferior if the lower limit of the CI is "
                      f"above -{res['margin_pp']:.0f} pp.", "", _contrast_table(res["rows"]), ""])


def render_h6(res: dict) -> str:
    if res["n"] == 0:
        return "# H6: scope-aware against scope-blind check\n\nNo labelled renames.\n"

    def rate(x):
        return "-" if x is None else f"{x:.3f}"
    out = ["# H6: scope-aware against scope-blind check", "", NOTE, "",
           f"{res['n']} labelled renames: {res['n_breaking']} are conflict cases, {res['n_harmless']} are renames to fresh names.", "",
           _table(["check", "breaking renames caught", "catch rate", "false alarms (harmless renames)"],
                  [["scope-aware", f"{res['caught_aware']}/{res['n_breaking']}", rate(res["catch_rate_aware"]),
                    f"{res['false_alarms_aware']}/{res['n_harmless']}"],
                   ["scope-blind", f"{res['caught_blind']}/{res['n_breaking']}", rate(res["catch_rate_blind"]),
                    f"{res['false_alarms_blind']}/{res['n_harmless']}"]]), ""]
    if res["catch_rate_aware_lower"] is not None:
        out.append(f"One-sided {100 * (1 - ALPHA):.0f}% lower limit of the scope-aware catch rate: "
                   f"{res['catch_rate_aware_lower']:.3f}.")
    out.append(f"Harmless renames flagged by one check only: blind only {res['blind_only']}, aware only "
               f"{res['aware_only']}; exact two-sided sign test p = {_g(res['p'])}.")
    out.append(f"Supports H6 (all breaking renames caught, fewer false alarms, p < {ALPHA}): "
               f"{'yes' if res['supports'] else 'no'}.")
    return "\n".join(out) + "\n"


def render_h7(res: dict) -> str:
    out = ["# H7: coding assistants with and without a rules file", "", NOTE, "",
           f"Equivalence margin {res['margin_pp']:.0f} pp for the first two comparisons; the last two (selection "
           f"above the assistant) cover the packs `{', '.join(res['unknown_packs']) or 'none given'}` only.", ""]
    for key, title in (("rules_vs_fulldoc", "Assistant with rules file - full document"),
                       ("norules_vs_none", "Assistant without rules file - none"),
                       ("selection_vs_rules", "Selection - assistant with rules file"),
                       ("selection_vs_norules", "Selection - assistant without rules file")):
        out += [f"## {title}", "", _contrast_table(res[key]), ""]
    return "\n".join(out)


def render_dose(res: dict) -> str:
    out = ["# Dose-response: compliance against the size of the context", "", NOTE, "",
           "Dose = mean number of characters of the prompt the model received (`prompt_chars`), on the units that "
           "every condition has. The conditions differ in how the context is chosen as well as in its size, so the "
           "curves describe the conditions and do not show a causal effect of size. Each cell has one point per "
           "condition; the permutation p-value is exact up to 8 conditions. The cells of one standard share their "
           "tasks across models, so they are not independent.", ""]
    if not res["cells"]:
        out.append("No cell with at least 3 conditions and test data in all of them.")
        return "\n".join(out) + "\n"
    out += [_table(["pack", "model", "units", "conditions", "rho", "p", "best", "largest context", "largest is best"],
                   [[c["pack"], c["model"], c["units"], c["n_conditions"],
                     "-" if c["rho"] is None else f"{c['rho']:+.3f}", _g(c["p"]),
                     f"{c['best']} ({c['best_compliance']:.3f})", f"{c['largest']} ({c['largest_compliance']:.3f})",
                     "yes" if c["largest_is_best"] else "no"] for c in res["cells"]]), ""]
    s = res["summary"]
    if s["n_rho"]:
        out.append(f"Spearman rho between context size and compliance: positive in {s['n_positive']} and negative in "
                   f"{s['n_negative']} of {s['n_rho']} cells, median {s['median_rho']:+.3f}. The largest context is "
                   f"the best condition in {s['n_largest_best']} of {s['n_cells']} cells.")
    out += ["", "## Curves", "",
            _table(["pack", "model", "condition", "prompt chars", "added chars", "compliance", "effect (pp)"],
                   [[c["pack"], c["model"], r["condition"], f"{r['chars']:.0f}",
                     "-" if r["added_chars"] is None else f"{r['added_chars']:.0f}", f"{r['compliance']:.3f}",
                     "-" if r["effect_pp"] is None else f"{r['effect_pp']:+.1f}"]
                    for c in res["cells"] for r in c["rows"]]), ""]
    out += [f"## Within `{res['selection']}`: added context against gain", ""]
    if res["units"]:
        out += [_table(["pack", "model", "units", "median added chars", "rho", "p", "method"],
                       [[u["pack"], u["model"], u["units"], f"{u['median_added_chars']:.0f}",
                         "-" if u["rho"] is None else f"{u['rho']:+.3f}", _g(u["p"]), u["method"]]
                        for u in res["units"]]), "",
                "Gain = unit mean of selection minus unit mean of `none`. A unit that `none` already gets right "
                "cannot gain, so most gains are zero and the correlation is weak by construction."]
    else:
        out.append(f"No cell has 3 units with both `{res['selection']}` and `{res['none']}`.")
    return "\n".join(out) + "\n"


def dumps(res: dict) -> str:
    return json.dumps(res, indent=2, sort_keys=True)
