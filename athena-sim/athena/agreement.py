"""Human-LLM agreement of two ontologies at the level of identifier kinds.

Unit = an identifier kind (id) present in both ontologies for the same
language.  For each unit and each attribute, the label of an ontology is the
set of values that the naming rules applying to that kind fix (empty when no
rule fixes the attribute).  Cohen's kappa is computed over all
(unit, attribute) items.  Kinds present in one ontology only are reported
separately and never enter kappa.
"""
from __future__ import annotations

import json
import random
from collections import Counter

ATTRIBUTES = ("casing", "prefix", "suffix", "severity", "length_bound", "forbidden_pattern")
_CASING_ALIASES = {"SCREAMING_SNAKE_CASE": "UPPER_SNAKE_CASE"}
EMPTY = "-"


def load(path):
    with open(path, encoding="utf-8") as fh:
        data = json.load(fh)
    nodes = {n["id"]: n for n in data["nodes"]}
    links = data.get("links", data.get("edges", []))
    kinds = {i for i, n in nodes.items() if n.get("type") == "IdentifierKind"}
    langs = {i for i, n in nodes.items() if n.get("type") == "Language"}
    rules = {i: n for i, n in nodes.items() if n.get("type") == "NamingRule"}
    applies = {i: {"kinds": set(), "langs": set()} for i in rules}
    for lk in links:
        rel = lk.get("relation") or lk.get("type") or lk.get("key")
        if rel != "APPLIES_TO" or lk["source"] not in rules:
            continue
        if lk["target"] in kinds:
            applies[lk["source"]]["kinds"].add(lk["target"])
        elif lk["target"] in langs:
            applies[lk["source"]]["langs"].add(lk["target"])
    return {"rules": rules, "applies": applies}


def _label(values):
    values = sorted(v for v in values if v)
    return "|".join(values) if values else EMPTY


def unit_labels(onto):
    """Map (language, kind) -> {attribute: label}, and the rules behind it."""
    by_unit = {}
    for rid, rule in onto["rules"].items():
        ap = onto["applies"][rid]
        for lang in ap["langs"]:
            for kind in ap["kinds"]:
                by_unit.setdefault((lang, kind), []).append(rule)
    out = {}
    for unit, rules in by_unit.items():
        casing = {_CASING_ALIASES.get(r.get("casing"), r.get("casing")) for r in rules}
        out[unit] = {
            "casing": _label(casing),
            "prefix": _label({r.get("prefix") for r in rules}),
            "suffix": _label({r.get("suffix") for r in rules}),
            "severity": _label({r.get("severity") for r in rules}),
            "length_bound": "yes" if any(r.get("minLength") is not None or r.get("maxLength") is not None for r in rules) else "no",
            "forbidden_pattern": "yes" if any(r.get("forbiddenPatterns") for r in rules) else "no",
            "_rules": sorted(r["id"] for r in rules),
        }
    return out


def cohen_kappa(pairs):
    n = len(pairs)
    if n == 0:
        return None, None
    po = sum(a == b for a, b in pairs) / n
    ca, cb = Counter(a for a, _ in pairs), Counter(b for _, b in pairs)
    pe = sum(ca[c] * cb[c] for c in set(ca) | set(cb)) / (n * n)
    if pe >= 1.0:
        return po, None
    return po, (po - pe) / (1.0 - pe)


def compare(human, llm, boot=10000, seed=20261022):
    h, l = unit_labels(human), unit_labels(llm)
    matched = sorted(set(h) & set(l))
    items = []
    for unit in matched:
        for attr in ATTRIBUTES:
            items.append((unit, attr, h[unit][attr], l[unit][attr]))
    po, kappa = cohen_kappa([(a, b) for _, _, a, b in items])
    informative = [(a, b) for _, _, a, b in items if a not in (EMPTY, "no") or b not in (EMPTY, "no")]
    po_inf, kappa_inf = cohen_kappa(informative)
    per_attr = {}
    for attr in ATTRIBUTES:
        sub = [(a, b) for _, at, a, b in items if at == attr]
        per_attr[attr] = {"n": len(sub), "agreement": (sum(x == y for x, y in sub) / len(sub)) if sub else None}
    ci = None
    if matched:
        rng = random.Random(seed)
        ks = []
        for _ in range(boot):
            draw = [matched[rng.randrange(len(matched))] for _ in matched]
            prs = [(h[u][a], l[u][a]) for u in draw for a in ATTRIBUTES]
            k = cohen_kappa(prs)[1]
            if k is not None:
                ks.append(k)
        ks.sort()
        if ks:
            ci = [ks[int(0.025 * (len(ks) - 1))], ks[int(0.975 * (len(ks) - 1))], len(ks)]
    return {
        "matched_units": [list(u) for u in matched],
        "human_only_units": [list(u) for u in sorted(set(h) - set(l))],
        "llm_only_units": [list(u) for u in sorted(set(l) - set(h))],
        "n_items": len(items),
        "observed_agreement": po,
        "kappa": kappa,
        "kappa_ci95_unit_bootstrap": ci,
        "informative_items": {"n": len(informative), "observed_agreement": po_inf, "kappa": kappa_inf},
        "per_attribute": per_attr,
        "items": [[list(u), a, x, y] for u, a, x, y in items],
        "disagreements": [
            {"unit": list(u), "attribute": a, "human": x, "llm": y,
             "human_rules": h[u]["_rules"], "llm_rules": l[u]["_rules"]}
            for u, a, x, y in items if x != y
        ],
        "rules": {"human": len(human["rules"]), "llm": len(llm["rules"])},
    }


def compare_packs(root, packs, boot=10000, seed=20261022):
    """Compare the human and the LLM-drafted ontology of every pack under `root` (packs/<pack>/*_ontology.json and
    packs/<pack>/llm/llm_ontology.json); the result has one entry per pack and a `pooled` entry."""
    import glob
    import os
    result = {}
    for pack in packs:
        hum = glob.glob(os.path.join(root, pack, "*_ontology.json"))
        if len(hum) != 1:
            raise ValueError(f"{pack}: expected one human ontology, found {hum}")
        llm = os.path.join(root, pack, "llm", "llm_ontology.json")
        if not os.path.exists(llm):
            raise ValueError(f"{pack}: no LLM-drafted ontology at {llm}")
        result[pack] = compare(load(hum[0]), load(llm), boot, seed)
    result["pooled"] = pooled(dict(result))
    return result


def pooled(results):
    """Kappa over the (unit, attribute) items of several packs."""
    pairs = [(x, y) for r in results.values() for _, _, x, y in r["items"]]
    inf = [(x, y) for x, y in pairs if x not in (EMPTY, "no") or y not in (EMPTY, "no")]
    po, k = cohen_kappa(pairs)
    po_i, k_i = cohen_kappa(inf)
    return {"n_items": len(pairs), "observed_agreement": po, "kappa": k,
            "informative_items": {"n": len(inf), "observed_agreement": po_i, "kappa": k_i}}
