"""Phase 1 / task 1.2: graph retrieval vs a flat structured lookup (see ADDENDUM.md).

Run from athena-sim/:  python lookup_check/lookup_compare.py
No LLM calls. Writes lookup_check/rule_table_<pack>.json, lookup_<pack>.json, results.json, results.md.
"""
from __future__ import annotations

import ast
import collections
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)

from athena.ontology import render_rule            # text template only (formatting, not retrieval)
from athena.packs import load_pack, select_split   # units and the live graph retriever, for comparison
from athena.retrieval import Retriever
from athena.runner import unit_inputs

SEV = {"MUST": 3, "SHOULD": 2, "MAY": 1}
SPEC = ["prefix", "suffix", "minLength", "maxLength", "forbiddenPatterns", "requiredElements", "requiredLabels"]
TASK_TYPES = {"rename": ("NamingRule",), "comment": ("CommentRule", "StructureRule")}
N_EXAMPLES = 2


# ---------------------------------------------------------------- 1. flatten ontology -> table
def flatten(onto_path: str) -> dict:
    d = json.load(open(onto_path, encoding="utf-8"))
    nodes = {n["id"]: n for n in d["nodes"]}
    rows = {}
    for nid, n in nodes.items():
        if n["type"] in ("NamingRule", "CommentRule", "StructureRule"):
            rows[nid] = {"id": nid, **n, "_standard": None, "_languages": [], "_kinds": [], "_examples": []}
    for e in d["links"]:
        s, t, rel = e["source"], e["target"], e["relation"]
        if s not in rows:
            continue
        if rel == "APPLIES_TO":
            rows[s]["_languages" if nodes[t]["type"] == "Language" else "_kinds"].append(t)
        elif rel == "DEFINED_IN":
            rows[s]["_standard"] = t
        elif rel == "HAS_EXAMPLE":
            rows[s]["_examples"].append({"id": t, **nodes[t]})
    names = {nid: n.get("name", nid) for nid, n in nodes.items() if n["type"] == "Standard"}
    return {"standards": names, "rules": rows}


def build_index(table: dict) -> dict:
    """key 'standard|language|kind|task' -> rule ids, ordered severity > specificity > id."""
    idx = collections.defaultdict(list)
    for r in table["rules"].values():
        for task, types in TASK_TYPES.items():
            if r["type"] not in types:
                continue
            for lang in r["_languages"]:
                for kind in r["_kinds"]:
                    idx[f"{r['_standard']}|{lang}|{kind}|{task}"].append(r["id"])
    key = lambda rid: (-SEV.get(table["rules"][rid].get("severity"), 0),
                       -sum(1 for f in SPEC if table["rules"][rid].get(f)), rid)
    return {k: sorted(v, key=key) for k, v in sorted(idx.items())}


# ---------------------------------------------------------------- 2. lookup -> CODING STANDARD block
def pick_examples(row: dict) -> list:
    good = [e for e in row["_examples"] if e.get("isCompliant")]
    bad = [e for e in row["_examples"] if not e.get("isCompliant")]
    out = []
    for i in range(max(len(good), len(bad))):
        out += ([good[i]] if i < len(good) else []) + ([bad[i]] if i < len(bad) else [])
    return out[:N_EXAMPLES]


def lookup_block(table, index, *, standard, language, kind, task):
    sname = table["standards"].get(standard, standard)
    ids = index.get(f"{standard}|{language}|{kind}|{task}", [])
    if not ids:
        return (f"{sname}: the ontology holds no specific rule for a {kind} in {language}; "
                f"apply the general conventions of the standard."), [], []
    rows = [{k: v for k, v in table["rules"][i].items() if not k.startswith("_")} for i in ids]
    exs = [pick_examples(table["rules"][i]) for i in ids]
    body = "\n\n".join(render_rule(r, e) for r, e in zip(rows, exs))
    return (f"{sname} - rules retrieved for a {kind} in {language} (most important first):\n{body}",
            ids, [[x["id"] for x in e] for e in exs])


def logged_block(prompt: str) -> str:
    return prompt.split("CODING STANDARD\n", 1)[1].split("\n\nCODE\n```", 1)[0]


def load_logged(run_dir: str) -> dict:
    """unit_id -> list of (repeat, block, retrieved_ids) for graph trials."""
    out = collections.defaultdict(list)
    with open(os.path.join(run_dir, "trials.jsonl"), encoding="utf-8") as f:
        for line in f:
            t = json.loads(line)
            if t["condition"] != "graph":
                continue
            ret = t.get("retrieval")
            if isinstance(ret, str):
                ret = ast.literal_eval(ret)
            out[t["unit_id"]].append((t["repeat"], logged_block(t["prompt"]), (ret or {}).get("retrieved_ids")))
    return out


# ---------------------------------------------------------------- 3. compare
SETS = [  # (pack, task, run dirs with logged prompts)
    ("gscs", "rename", ["runs/test_luna_gscs_rename", "runs/test_o3mini_gscs_rename"]),
    ("gscs", "comment", ["runs/test_luna_gscs_comment", "runs/test_o3mini_gscs_comment"]),
    ("public5", "rename", ["runs/test_luna_p5_rename"]),
    ("public5", "comment", ["runs/test_luna_p5_comment"]),
]


def main():
    os.chdir(ROOT)
    results, tables = [], {}
    for pack_id, task, run_dirs in SETS:
        pack = load_pack(pack_id)
        if pack_id not in tables:
            table = flatten(pack.ontology.path)
            index = build_index(table)
            tables[pack_id] = (table, index)
            json.dump({"standards": table["standards"], "rules": list(table["rules"].values())},
                      open(os.path.join(HERE, f"rule_table_{pack_id}.json"), "w", encoding="utf-8"),
                      ensure_ascii=False, indent=1)
            json.dump(index, open(os.path.join(HERE, f"lookup_{pack_id}.json"), "w", encoding="utf-8"),
                      ensure_ascii=False, indent=1)
        table, index = tables[pack_id]
        units = select_split(pack.rename_units() if task == "rename" else pack.comment_units(), "test")
        live = Retriever(pack, chunk_k=3, top_k=None, n_examples=N_EXAMPLES)
        logged = {d: load_logged(d) for d in run_dirs}
        c = collections.Counter()
        keys, mismatches = set(), []
        for u in units:
            name, code = unit_inputs(task, u)
            text, ids, ex_ids = lookup_block(table, index, standard=u.standard_id, language=u.language,
                                             kind=u.kind, task=task)
            keys.add((u.standard_id, u.language, u.kind))
            g = live.context("graph", task=task, standard_id=u.standard_id, language=u.language,
                             kind=u.kind, name=name, code=code)
            g_ids = g.meta.get("retrieved_ids", [])
            g_ex = [[e["id"] for e in pack.ontology.examples(r, N_EXAMPLES)] for r in g_ids]
            c["units"] += 1
            c["same_set_live"] += set(ids) == set(g_ids)
            c["same_order_live"] += ids == g_ids
            c["same_examples_live"] += ex_ids == g_ex
            c["same_text_live"] += text == g.text
            c["empty"] += not ids
            c["n_rules"] += len(ids)
            for d in run_dirs:
                trials = logged[d].get(u.unit_id, [])
                if not trials:      # unit not sampled in that run (Public5 rename ran 100 of the test units)
                    continue
                c[f"logged_units::{d}"] += 1
                c[f"logged_trials::{d}"] += len(trials)
                ok = all(b == text for _, b, _ in trials)
                ok_ids = all(r == ids for _, _, r in trials)
                c[f"same_text_logged::{d}"] += ok
                c[f"same_ids_logged::{d}"] += ok_ids
                if not ok:
                    mismatches.append({"unit": u.unit_id, "run": d})
        results.append({"pack": pack_id, "task": task, "counts": dict(c), "distinct_keys": len(keys),
                        "mismatches": mismatches[:20]})
    # edge relations: present in the files vs read by the retriever
    rel = {}
    for pack_id in tables:
        d = json.load(open(load_pack(pack_id).ontology.path, encoding="utf-8"))
        rel[pack_id] = dict(collections.Counter(e["relation"] for e in d["links"]))
    out = {"sets": results, "relations_in_file": rel,
           "relations_read_by_retriever": ["APPLIES_TO (rule->language, rule->kind; one hop)",
                                           "DEFINED_IN (filter by standard)", "HAS_EXAMPLE (examples)"]}
    json.dump(out, open(os.path.join(HERE, "results.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)

    L = ["# Graph retrieval vs structured lookup — results", "",
         "| set | units | distinct keys | mean rules/unit | same set | same order | same examples | identical text (live) | identical text (logged prompts) |",
         "|---|---|---|---|---|---|---|---|---|"]
    for r in results:
        c, n = r["counts"], r["counts"]["units"]
        pct = lambda k: f"{100 * c[k] / n:.1f}%"
        logged = "; ".join(
            f"{k.split('::')[1].split('/')[-1]}: {v}/{c['logged_units::' + k.split('::')[1]]} units "
            f"({c['logged_trials::' + k.split('::')[1]]} graph trials)"
            for k, v in c.items() if k.startswith("same_text_logged::"))
        L.append(f"| {r['pack']} {r['task']} | {n} | {r['distinct_keys']} | {c['n_rules'] / n:.2f} | {pct('same_set_live')} | "
                 f"{pct('same_order_live')} | {pct('same_examples_live')} | {pct('same_text_live')} | {logged} |")
    L += ["", "Edge relations in the ontology files: " + json.dumps(rel),
          "", "Relations read by the retriever: " + "; ".join(out["relations_read_by_retriever"])]
    open(os.path.join(HERE, "results.md"), "w", encoding="utf-8").write("\n".join(L) + "\n")
    print("\n".join(L))
    for r in results:
        if r["mismatches"]:
            print("MISMATCH", r["pack"], r["task"], r["mismatches"][:5])


if __name__ == "__main__":
    main()
