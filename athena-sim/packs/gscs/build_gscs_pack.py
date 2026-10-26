#!/usr/bin/env python3
"""Build the GSCS pack: ontology graph + benchmark files (snippets, violations, comment units).

  python packs/gscs/build_gscs_pack.py

Inputs : gscs_standard.json (rules + examples), seeds.py (compliant seed snippets)
Outputs: gscs_ontology.json, benchmark/snippets|violations|comment_units/<language>/*.json
Deterministic: two runs produce identical files.  Every violation is verified with the same mechanical checker
used for scoring (vendor/output_validator.check_naming_compliance): the original name passes its rule and the
injected name fails it.
"""
from __future__ import annotations

import json
import keyword
import os
import re
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(ROOT, "vendor"))
sys.path.insert(0, HERE)
from output_validator import check_naming_compliance  # noqa: E402
from seeds import SEEDS  # noqa: E402

LANG_NAMES = {"java": "Java", "python": "Python", "cpp": "C++", "csharp": "C#", "javascript": "JavaScript",
              "typescript": "TypeScript"}
MAX_VIOLATIONS_PER_IDENTIFIER = 2
RESERVED = set(keyword.kwlist) | set("""int float double long short char bool boolean byte string class type def new delete
    default this super static final const void auto register signed unsigned template namespace using""".split())


def dump(path, obj):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        json.dump(obj, f, indent=2, ensure_ascii=False)
        f.write("\n")


# ---------------------------------------------------------------------------------------------- ontology
def build_ontology(std: dict) -> dict:
    s = std["standard"]
    langs = s["scopeLanguages"]
    kinds = sorted({k for r in std["rules"] for k in r["identifierKinds"]})
    nodes = [{"id": l, "type": "Language", "name": LANG_NAMES[l], "defaultStandardId": s["id"]} for l in langs]
    nodes += [{"id": k, "type": "IdentifierKind", "name": k.replace("_", " ").title()} for k in kinds]
    nodes.append(s)
    links = []
    for r in std["rules"]:
        node = {k: v for k, v in r.items()}
        node["identifierKind"] = r["identifierKinds"][0]
        nodes.append(node)
        for l in langs:
            links.append({"source": r["id"], "target": l, "relation": "APPLIES_TO"})
        for k in r["identifierKinds"]:
            links.append({"source": r["id"], "target": k, "relation": "APPLIES_TO"})
        links.append({"source": r["id"], "target": s["id"], "relation": "DEFINED_IN"})
    counter = {}
    for ex in std["examples"]:
        counter[ex["ruleId"]] = counter.get(ex["ruleId"], 0) + 1
        eid = f"EX-{ex['ruleId']}-{counter[ex['ruleId']]}"
        nodes.append({"id": eid, "type": "Example", **ex})
        links.append({"source": ex["ruleId"], "target": eid, "relation": "HAS_EXAMPLE"})
    return {"directed": True, "multigraph": False,
            "graph": {"name": "Athena GSCS user-defined standard", "version": "0.1", "generatedDate": "2026-09-28",
                      "assumptions": std["assumptions"]},
            "nodes": nodes, "links": links}


# ---------------------------------------------------------------------------------------------- injection
def lower_camel(ws):
    ws = [w for w in ws if w]
    return ws[0][:1].lower() + ws[0][1:] + "".join(w[:1].upper() + w[1:] for w in ws[1:])


def candidates(rule_id: str, name: str):
    if rule_id in ("GSCS-VAR-TYPED-PREFIX", "GSCS-BOOL-BLN-PREFIX", "GSCS-FUNC-RETURN-PREFIX"):
        p, rest = re.match(r"^([a-z]+)_(.+)$", name).groups()
        ws = rest.split("_")
        return [("strip_prefix", rest), ("camel_no_prefix", lower_camel(ws)),
                ("glued_prefix", p + "".join(w[:1].upper() + w[1:] for w in ws))]
    if rule_id == "GSCS-CONST-UPPER":
        ws = name.split("_")
        return [("lower_camel", lower_camel([w.lower() for w in ws])),
                ("title_snake", "_".join(w.capitalize() for w in ws))]
    if rule_id == "GSCS-PROC-VERB-OBJECT":
        ws = name.split("_")
        return [("lower_camel", lower_camel(ws)), ("lower_snake", "_".join(w.lower() for w in ws))]
    if rule_id == "GSCS-TYPE-SUFFIX":
        base = name[: -len("_Type")]
        return [("strip_suffix", base), ("glued_suffix", base + "Type")]
    raise KeyError(rule_id)


def word_re(name):
    return re.compile(r"(?<![\w$])" + re.escape(name) + r"(?![\w$])")


def main():
    with open(os.path.join(HERE, "gscs_standard.json"), encoding="utf-8") as f:
        std = json.load(f)
    onto = build_ontology(std)
    dump(os.path.join(HERE, "gscs_ontology.json"), onto)
    rules = {r["id"]: r for r in std["rules"]}
    kind_rule = {}
    for r in std["rules"]:
        if r["type"] == "NamingRule":
            for k in r["identifierKinds"]:
                assert k not in kind_rule, f"two naming rules for kind {k}"
                kind_rule[k] = r["id"]

    bench = os.path.join(HERE, "benchmark")
    if os.path.isdir(bench):
        shutil.rmtree(bench)
    n_snip = n_viol = n_comment = 0
    for seed in SEEDS:
        lang, sid = seed["language"], seed["id"]
        code = seed["template"].replace("{HEADER}", seed["header"])
        bare = seed["template"].replace("{HEADER}\n", "")
        assert seed["header"] in code and "{HEADER}" not in code and bare != code, sid
        idents = []
        for name, kind in seed["identifiers"]:
            rid = kind_rule[kind]
            assert word_re(name).search(code), f"{sid}: {name} not found in code"
            ok, why = check_naming_compliance(name, rules[rid])
            assert ok, f"{sid}: seed name {name} violates {rid}: {why}"
            idents.append({"name": name, "kind": kind, "isCompliant": True})
        dump(os.path.join(bench, "snippets", lang, sid + ".json"), {
            "id": sid, "language": lang, "source": "authored:gscs-seed",
            "sourceDetail": "hand-authored seed written to follow the GSCS document; not real-world code",
            "standardId": std["standard"]["id"], "split": seed["split"], "codeContext": code, "identifiers": idents,
            "provenance": {"authored": "2026-09-28", "license": "project-internal"}})
        n_snip += 1
        for name, kind in seed["identifiers"]:
            rid, made = kind_rule[kind], 0
            for method, inj in candidates(kind_rule[kind], name):
                if made >= MAX_VIOLATIONS_PER_IDENTIFIER:
                    break
                if (inj == name or not re.match(r"^[A-Za-z_]\w*$", inj) or inj in RESERVED
                        or check_naming_compliance(inj, rules[rid])[0] or word_re(inj).search(code)):
                    continue
                code_v, occ = word_re(name).subn(inj, code)
                dump(os.path.join(bench, "violations", lang, f"{sid}__{name}__{method}.json"), {
                    "snippetId": sid, "language": lang, "originalName": name, "injectedName": inj,
                    "identifierKind": kind, "violatedRuleId": rid, "injectionMethod": method, "split": seed["split"],
                    "expectedViolationReasons": check_naming_compliance(inj, rules[rid])[1],
                    "codeContextWithViolation": code_v, "occurrencesRenamed": occ})
                made += 1
                n_viol += 1
            assert made, f"{sid}: no verified violation for {name}"
        fname, fkind = seed["function"]
        dump(os.path.join(bench, "comment_units", lang, f"{sid}__{fname}.json"), {
            "snippetId": sid, "language": lang, "standardId": std["standard"]["id"], "identifierKind": fkind,
            "name": fname, "codeBare": bare, "referenceComment": seed["header"].strip("\n"), "split": seed["split"],
            "ruleIds": ["GSCS-DOC-FUNC-HEADER"]})
        n_comment += 1
    print(f"gscs pack built: {len(onto['nodes'])} nodes / {len(onto['links'])} links; "
          f"{n_snip} seed snippets, {n_viol} rename units, {n_comment} comment units "
          f"(dev snippets: {sum(1 for x in SEEDS if x['split'] == 'dev')}, test: {sum(1 for x in SEEDS if x['split'] == 'test')})")


if __name__ == "__main__":
    main()
