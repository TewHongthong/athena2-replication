"""Build blinded, de-duplicated judging items from the frozen comment runs (see ADDENDUM.md).
Writes items.jsonl (what the judges see) and item_map.jsonl (item -> trials; never shown to a judge)."""
import hashlib, json, os, random, sys
HERE = os.path.dirname(os.path.abspath(__file__)); SIM = os.path.dirname(HERE)
sys.path.insert(0, SIM)
from athena.packs import load_pack

RUNS = [  # (pack, source label, trials path)
    ("gscs", "o3-mini", "runs/test_o3mini_gscs_comment/trials.jsonl"),
    ("gscs", "GPT-6 Luna", "runs/test_luna_gscs_comment/trials.jsonl"),
    ("gscs", "Qwen3.5-9B", "qwen_plan_a/runs/qwen_gscs_comment/trials.jsonl"),
    ("gscs", "Gemini 3.1 Flash-Lite", "gemini31fl/runs/gemini31fl_gscs_comment/trials.jsonl"),
    ("gscs", "DeepSeek V4 Flash", "dsv4f_v2/runs/dsv4f_gscs_comment/trials.jsonl"),
    ("gscs", "Gemma 4 26B", "gemma4/gemma4_gscs_comment/trials.jsonl"),
    ("gscs", "linter autofix", "runs/test_autofix_gscs_comment/trials.jsonl"),
    ("public5", "GPT-6 Luna", "runs/test_luna_p5_comment/trials.jsonl"),
]


def rules_for(pack, unit):
    out = []
    for rid in unit.rule_ids:
        r = pack.ontology.rule(rid)
        req = r.get("requiredElements")
        if req is not None and unit.expected_elements is not None:
            req = [e for e in req if e in unit.expected_elements]
        out.append({k: v for k, v in dict(id=rid, format=r.get("format"), description=r.get("description"),
                    required_elements=req, required_labels=r.get("requiredLabels"),
                    optional_labels=r.get("optionalFilledLabels")).items() if v})
    return out


def main():
    packs = {"gscs": load_pack("gscs"), "public5": load_pack("public5", os.path.join(SIM, "..", "athena-corpus"))}
    units = {(p, u.unit_id): u for p, pk in packs.items() for u in pk.comment_units() if u.split == "test"}
    items, mp = {}, []

    def add(pack, unit, comment):
        iid = hashlib.sha256(f"{pack}|{unit.unit_id}|{comment}".encode()).hexdigest()[:16]
        if iid not in items:
            items[iid] = dict(id=iid, language=unit.language, kind=unit.kind, name=unit.name,
                              rules=rules_for(packs[pack], unit), code=unit.code_bare, comment=comment)
        return iid

    for (pack, uid), u in sorted(units.items()):
        mp.append(dict(item=add(pack, u, u.reference_comment.strip()), source="reference", pack=pack, unit=uid,
                       condition="reference", repeat=0, key=None))
    for pack, src, rel in RUNS:
        best = {}
        for line in open(os.path.join(SIM, rel)):
            t = json.loads(line); k = t["key"]
            if t.get("split") != "test": continue
            if k not in best or (best[k].get("error") and not t.get("error")) or (not t.get("error") and t["ts"] >= best[k]["ts"]):
                best[k] = t
        for k, t in sorted(best.items()):
            u = units[(pack, t["unit_id"])]
            c = (t.get("metrics") or {}).get("comment")
            c = c.strip() if isinstance(c, str) else ""
            mp.append(dict(item=add(pack, u, c) if c else None, source=src, pack=pack, unit=t["unit_id"],
                           condition=t["condition"], repeat=t["repeat"], key=k))
    order = sorted(items); random.Random(20261001).shuffle(order)
    with open(os.path.join(HERE, "items.jsonl"), "w", encoding="utf-8") as f:
        for iid in order: f.write(json.dumps(items[iid], ensure_ascii=False) + "\n")
    with open(os.path.join(HERE, "item_map.jsonl"), "w", encoding="utf-8") as f:
        for r in mp: f.write(json.dumps(r, ensure_ascii=False) + "\n")
    from collections import Counter
    print("items:", len(items), "| map rows:", len(mp), "| no comment:", sum(r["item"] is None for r in mp))
    print(Counter((r["pack"], r["source"]) for r in mp))


if __name__ == "__main__":
    main()
