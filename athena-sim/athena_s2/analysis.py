"""The analysis of Study 2 (HYPOTHESES_v2_study2.md, Sections 2.2 to 2.4 and 4) across run folders.

Reads the trials of the development and test runs of Study 2 and computes

* eligibility (Section 2.3): mean core_ok_s2 of condition none on the dev units, over the models; a standard is
  included in H1-S2 if the value is below 0.90;
* H1-S2: selection (graph, kind from metadata) against none on the test units, per included standard and model;
  the task is the unit (mean over its rounds), exact two-sided sign test, one Holm family made of exactly these tests;
* H2-S2: selection - naming, cluster-bootstrap 95% CI, margin 2 pp, and the mean prompt length of both;
* H3-S2: selection - fulldoc, cluster-bootstrap 95% CI, margin 2 pp, and selection against chunk (TF-IDF), bm25 and
  dense with the exact sign test and one Holm family over those comparisons;
* H4-S2: selection with the kind and its facets inferred from the code (graph[infer]) - selection with them from
  metadata, cluster-bootstrap 95% CI, margin 5 pp;
* per (standard, model) cell and condition: core_ok_s2, the Study 1 core_ok (casing), the share of names with the
  required prefix, exact_match, tokens, cost and the trials that ended at the output limit; per standard: the tasks
  whose snippet holds another identifier that carries the prefix the task requires, the agreement of the inferred
  kind and facets with metadata, and a reference program that applies the rule from the kind (as addendum A10).

The verdicts of H2-S2 to H4-S2 are given per cell (supported, clearly against, inconclusive) and summarised as in
HYPOTHESES_v2.md Section 2.4: supported if every cell is supported, not supported if any cell is clearly against,
inconclusive otherwise. Intervals resample source files (the field `file` of a trial) with the resamples and the seed
of Study 1. The statistics are those of Study 1 (athena.confirmatory, athena.secondary, athena.report), unchanged.

Records. The key of a trial does not say which family a run belongs to, so the family is read from the config.json
of its run folder (no_oracle: infer) and the trials of an infer run get the condition graph[infer]. When a key has
more than one record without an error (two copies of a run wrote the same key), the first by its time stamp `ts` is
used (keep="last" uses the last, as a check), and the others are counted as duplicates. A key whose records all carry
an error is counted and left out. Lines that are not valid JSON are counted. Do not pass canary runs: they share
their keys with the development round.

Grades. core_ok of a Study 2 trial is core_ok_s2 (the core of the Study 2 pack for the kind of the task); an answer
that cannot be parsed fails. The other grades are recomputed from the proposed name with the check of the trials
(athena.evaluate, vendor/output_validator.py): the Study 1 core_ok uses the core of the Study 1 pack for the Study 1
kind of the task (KIND_S1) and is not defined where that core has no rule for the kind; the prefix is the prefix of
the core rule of the task's kind, and a name without it is counted as carrying a sibling prefix (another prefix of
the same core table) or no prefix. A check re-scores core_ok_s2 of every trial with a valid name and counts the trials
whose stored grade differs.

Snippets. The identifiers of the snippet shown to the model are read after comments and string and character
literals are removed; an identifier counts if it differs from the injected name, starts with the required prefix and
is longer than it. The snippets come from the benchmark (bench_dir, or $ATHENA_S2_BENCH/<pack>); without it this
report is left out and the other results are unchanged.

Reference program. For each task it takes the injected name and the kind, removes a leading prefix of the pack's core
table (the longest that matches), joins the words in the casing of a core rule of the kind if it has one (the word
split and join of repair_baseline.py, addendum A10) and adds the prefix of the kind's core rule. It is scored with the
check of the trials (core_ok_s2 for the kind from metadata, exact_match against the original name). It is run once
with the kind from metadata and once with the kind inferred from the code (from the infer trials). It does not read
the original name, uses no model and has no decision rule.

Drift check (HYPOTHESES_v2.md Section 2.1, applied by Section 2.1 of the amendment). The canary run folders are given
apart from the other runs, each named with canary_before or canary_after (s2canary_before_<pin>_<pack>), and each is
read on its own, because the two canary runs and the development round share their keys. The canary set is every
dev unit of the two packs. Per model: the units present in both canary runs, core_ok_s2 before and after, the exact
two-sided McNemar test on the paired outcomes, and the share of units whose proposed name is identical in both runs;
and the model, provider and system_fingerprint of the first and of the last trial of the model by time stamp, over its
canary trials and its trials on the comparison split. A model is flagged if these differ or if the McNemar p is below
0.05. A flag changes no data: H1-S2, H2-S2 and H3-S2 are recomputed without the flagged models and reported next to
the primary result as a sensitivity analysis.

Standard library only.
"""
from __future__ import annotations

import json
import os
import re
import sys
from collections import Counter, defaultdict

from athena import confirmatory as C
from athena import secondary as S
from athena.evaluate import _IDENT, name_for_check
from athena.report import mcnemar_p, mean, wilson

from output_validator import check_naming_compliance  # noqa: E402  (athena.evaluate puts vendor on the path)

SIM = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if SIM not in sys.path:
    sys.path.insert(0, SIM)
import repair_baseline as RB  # noqa: E402  (addendum A10: word split and join)

from .packs import S2_PACKS  # noqa: E402

PACKS = tuple(S2_PACKS)                                   # godot-s2, dotnet-runtime-s2
PANEL = ("luna", "gemini31fl", "qwen35_9b_s2", "gemma4_local_s2")
SELECTION = "graph"
INFER = "graph[infer]"
NAMING = "naming"
FULLDOC = "fulldoc"
NONE = "none"
RETRIEVAL = C.RETRIEVAL_BASELINES                         # chunk (TF-IDF), bm25, dense
COND_ORDER = (NONE, FULLDOC, NAMING, "chunk", "bm25", "dense", SELECTION, INFER)
MARGIN_H2 = 0.02
MARGIN_H3 = 0.02
MARGIN_H4 = 0.05
LIMIT_FINISH = "length"                                   # `finish` of a trial that stopped at the output limit (A11)
KIND_S1 = {"input_parameter": "parameter", "output_parameter": "parameter", "instance_field": "field",
           "static_field": "field", "threadstatic_field": "field", "public_field": "field"}
VERDICT = {"non-inferior": "supported", "inferior": "clearly against", "inconclusive": "inconclusive"}
IDENTITY = ("model", "provider", "system_fingerprint")      # recorded per trial (HYPOTHESES_v2 Section 2.1)


# --------------------------------------------------------------------------------------------------------- records

def run_args(run_dir: str) -> dict:
    try:
        with open(os.path.join(run_dir, "config.json"), "r", encoding="utf-8") as f:
            return (json.load(f) or {}).get("args") or {}
    except (OSError, ValueError, AttributeError):
        return {}


def read_runs(run_dirs, keep: str = "first") -> tuple:
    """Return (records, runs, error_keys).  One record per key (see the module text); `runs` has the counts of each
    run folder."""
    if keep not in ("first", "last"):
        raise ValueError("keep must be first or last")
    groups: dict = defaultdict(list)
    runs = []
    order = 0
    for d in run_dirs:
        args = run_args(d)
        if args.get("ontology_variant", "human") not in (None, "human"):
            raise ValueError(f"{d}: Study 2 has only the human ontology")
        family = "infer" if args.get("no_oracle") else "meta"
        info = {"run": os.path.basename(os.path.normpath(d)), "family": family, "pin": args.get("model_pin"),
                "pack": args.get("pack"), "lines": 0, "corrupt": 0, "records": 0, "error_records": 0}
        with open(os.path.join(d, "trials.jsonl"), "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                info["lines"] += 1
                try:
                    r = json.loads(line)
                except json.JSONDecodeError:
                    info["corrupt"] += 1
                    continue
                if not isinstance(r, dict) or not r.get("key"):
                    info["corrupt"] += 1
                    continue
                r["run_dir"] = info["run"]
                r["family"] = family
                r["pin"] = info["pin"] or r.get("backend")
                key = r["key"]
                if family == "infer":
                    r["condition_base"] = r.get("condition")
                    r["condition"] = f"{r.get('condition')}[infer]"
                    key = f"{key}|infer"
                info["records"] += 1
                info["error_records"] += bool(r.get("error"))
                order += 1
                groups[key].append((str(r.get("ts") or ""), order, r))
        runs.append(info)
    recs, error_keys = [], []
    dup: Counter = Counter()
    for key, items in groups.items():
        ok = sorted((x for x in items if not x[2].get("error")), key=lambda x: (x[0], x[1]))
        if not ok:
            error_keys.append(key)
            continue
        chosen = ok[0] if keep == "first" else ok[-1]
        recs.append(chosen[2])
        for x in ok:
            if x is not chosen:
                dup[x[2]["run_dir"]] += 1
    for info in runs:
        info["duplicates_not_used"] = dup.get(info["run"], 0)
    return recs, runs, sorted(error_keys)


def metrics(r: dict) -> dict:
    return r.get("metrics") or {}


def proposed(r: dict):
    m = metrics(r)
    s = m.get("suggested")
    return s if (s and m.get("valid_identifier") and _IDENT.match(s)) else None


def cond_rank(c) -> int:
    return COND_ORDER.index(c) if c in COND_ORDER else 99


def pin_order(pins) -> list:
    return sorted(pins, key=lambda p: (PANEL.index(p) if p in PANEL else 99, str(p)))


def pack_rank(p) -> int:
    return PACKS.index(p) if p in PACKS else 9


# ----------------------------------------------------------------------------------------------------- core tables

def core_table(pack_dir: str, onto_file: str) -> dict:
    with open(os.path.join(pack_dir, onto_file), "r", encoding="utf-8") as f:
        nodes = {n["id"]: n for n in json.load(f)["nodes"]}
    with open(os.path.join(pack_dir, "core_rules.json"), "r", encoding="utf-8") as f:
        core = json.load(f).get("core", {})
    return {(lang, kind): [nodes[r] for r in ids] for lang, kinds in core.items() for kind, ids in kinds.items()}


class Tables:
    """Core tables of the Study 2 packs and of the Study 1 packs of the same standards."""

    def __init__(self, packs_dir: str | None = None):
        packs_dir = packs_dir or os.path.join(SIM, "packs")
        self.s2, self.s1, self.family = {}, {}, {}
        for pack, (std, onto) in S2_PACKS.items():
            self.s2[pack] = core_table(os.path.join(packs_dir, pack), onto)
            self.s1[pack] = core_table(os.path.join(packs_dir, std), onto)
            self.family[pack] = sorted({r["prefix"] for rules in self.s2[pack].values() for r in rules
                                        if r.get("prefix") and "/" not in r["prefix"]}, key=lambda p: (-len(p), p))

    def rules(self, pack, language, kind) -> list:
        return self.s2[pack].get((language, kind), [])

    def rules_s1(self, pack, language, kind) -> list:
        return self.s1[pack].get((language, KIND_S1.get(kind, kind)), [])

    def required_prefix(self, pack, language, kind):
        return next((r["prefix"] for r in self.rules(pack, language, kind)
                     if r.get("prefix") and "/" not in r["prefix"]), None)


def score(name, language: str, rules: list):
    """The check of the trials: None if there is no rule; False for no valid name; else every rule passes."""
    if not rules:
        return None
    if not name or not _IDENT.match(name):
        return False
    chk = name_for_check(language, name)
    return all(check_naming_compliance(chk, r)[0] for r in rules)


def prefix_class(name, required, family) -> str:
    """right, sibling (another prefix of the core table), none (no such prefix) or no name."""
    if not name:
        return "no name"
    if required and name.startswith(required):
        return "right"
    if any(name.startswith(p) for p in family if p != required):
        return "sibling"
    return "none"


def reference_name(injected: str, language: str, kind, tables: Tables, pack: str) -> str:
    stem = injected
    for p in tables.family[pack]:
        if stem.startswith(p) and len(stem) > len(p):
            stem = stem[len(p):]
            break
    rules = tables.rules(pack, language, kind) if kind else []
    casing = next((r.get("casing") for r in rules if r.get("casing")), None)
    if casing:
        stem = RB.join(RB.words(stem), casing)
    prefix = next((r["prefix"] for r in rules if r.get("prefix") and "/" not in r["prefix"]), None)
    return (prefix or "") + stem


# -------------------------------------------------------------------------------------------------------- snippets

_ID = re.compile(r"(?<![A-Za-z0-9_$])[A-Za-z_][A-Za-z0-9_]*")


def strip_comments_and_literals(code: str, language: str) -> str:
    """The code with comments and string and character literals replaced by a space (C++ and C#)."""
    out, i, n = [], 0, len(code)
    while i < n:
        c = code[i]
        nxt = code[i + 1] if i + 1 < n else ""
        if c == "/" and nxt == "/":
            j = code.find("\n", i)
            i = n if j < 0 else j
            out.append(" ")
            continue
        if c == "/" and nxt == "*":
            j = code.find("*/", i + 2)
            i = n if j < 0 else j + 2
            out.append(" ")
            continue
        if language == "csharp" and code.startswith('"""', i):                       # raw string literal
            j = code.find('"""', i + 3)
            i = n if j < 0 else j + 3
            while i < n and code[i] == '"':
                i += 1
            out.append(" ")
            continue
        if c == '"' and language == "cpp" and i > 0 and code[i - 1] == "R":           # raw string R"d(...)d"
            k = code.find("(", i + 1)
            if k >= 0:
                delim = code[i + 1:k]
                end = code.find(")" + delim + '"', k + 1)
                i = n if end < 0 else end + len(delim) + 2
                out.append(" ")
                continue
        if c == '"':
            verbatim = language == "csharp" and "@" in code[max(0, i - 2):i]
            j = i + 1
            while j < n:
                if code[j] == '"':
                    if verbatim and j + 1 < n and code[j + 1] == '"':
                        j += 2
                        continue
                    break
                if code[j] == "\\" and not verbatim:
                    j += 2
                    continue
                if code[j] == "\n" and not verbatim:
                    break
                j += 1
            i = j + 1
            out.append(" ")
            continue
        if c == "'" and not (i > 0 and code[i - 1].isalnum()):                        # not a digit separator
            j = i + 1
            while j < n and code[j] not in "'\n":
                j += 2 if code[j] == "\\" else 1
            i = j + 1
            out.append(" ")
            continue
        out.append(c)
        i += 1
    return "".join(out)


def identifiers(code: str, language: str) -> set:
    return set(_ID.findall(strip_comments_and_literals(code, language)))


def prefixed_others(code: str, language: str, injected: str, required) -> list:
    if not required:
        return []
    return sorted(i for i in identifiers(code, language)
                  if i != injected and i.startswith(required) and len(i) > len(required))


def load_snippets(packs, bench_dir: str | None = None) -> tuple:
    """unit_id -> code shown to the model, per pack; and a note per pack that could not be read."""
    from .packs import load_pack
    out, notes = {}, {}
    for pack in packs:
        d = os.path.join(bench_dir, pack) if bench_dir else None
        try:
            p = load_pack(pack, d)
            out[pack] = {u.unit_id: u.code_violation for u in p.rename_units()}
        except (FileNotFoundError, KeyError, ValueError) as e:
            notes[pack] = str(e).splitlines()[0]
    return out, notes


# -------------------------------------------------------------------------------------------------------- analysis

def task_mean(pairs):
    """Mean over tasks of the mean over the rounds of each task; None if a value is None or there is no value."""
    by = defaultdict(list)
    for u, v in pairs:
        if v is None:
            return None
        by[u].append(float(v))
    return sum(sum(v) / len(v) for v in by.values()) / len(by) if by else None


def cell_verdicts(rows: list, key: str = "verdict") -> list:
    return [VERDICT.get(r[key], r[key]) for r in rows]


def summarise(verdicts: list) -> str:
    if not verdicts:
        return "no data"
    if all(v == "supported" for v in verdicts):
        return "supported"
    if any(v == "clearly against" for v in verdicts):
        return "not supported"
    return "inconclusive"


def mean_of(recs, field):
    return mean([r.get(field) for r in recs if r.get(field) is not None])


def h2(idx, clusters, packs, recs_cmp, b, seed, margin=MARGIN_H2) -> dict:
    rows = S.contrast(idx, idx, clusters, packs, SELECTION, NAMING, b=b, seed=seed)
    by = defaultdict(list)
    for r in recs_cmp:
        by[(r["pack"], r["pin"], r["condition"])].append(r)
    for row in rows:
        row["verdict"] = S.verdict_noninferior(row["ci_low_pp"] / 100, row["ci_high_pp"] / 100, margin)
        for cond, tag in ((SELECTION, "selection"), (NAMING, "naming")):
            rs = by.get((row["pack"], row["model"], cond), [])
            row[f"{tag}_prompt_chars"] = mean_of(rs, "prompt_chars")
            row[f"{tag}_prompt_tokens"] = mean_of(rs, "prompt_tokens")
    v = cell_verdicts(rows)
    for row, x in zip(rows, v):
        row["cell"] = x
    return {"margin_pp": 100 * margin, "rows": rows, "summary": summarise(v)}


def h3(idx, clusters, packs, b, seed, margin=MARGIN_H3) -> dict:
    ni = C.h3_noninferiority(idx, clusters, packs, SELECTION, FULLDOC, margin, b, seed)
    rt = C.h3_retrieval(idx, packs, SELECTION, RETRIEVAL)
    cells = []
    for row in ni:
        ret = [x for x in rt if (x["pack"], x["model"]) == (row["pack"], row["model"])]
        higher_all = len(ret) == len(RETRIEVAL) and all(x["higher"] for x in ret)
        if row["verdict"] == "inferior":
            cell = "clearly against"
        elif row["verdict"] == "non-inferior" and higher_all:
            cell = "supported"
        else:
            cell = "inconclusive"
        cells.append({"pack": row["pack"], "model": row["model"], "fulldoc": row["verdict"],
                      "higher_than_all_retrieval": higher_all, "n_retrieval": len(ret), "cell": cell})
    return {"margin_pp": 100 * margin, "fulldoc": ni, "retrieval": rt, "cells": cells,
            "summary": summarise([c["cell"] for c in cells])}


def h4(idx, clusters, packs, b, seed, margin=MARGIN_H4) -> dict:
    rows = S.contrast(idx, idx, clusters, packs, INFER, SELECTION, b=b, seed=seed)
    for row in rows:
        row["verdict"] = S.verdict_noninferior(row["ci_low_pp"] / 100, row["ci_high_pp"] / 100, margin)
    v = cell_verdicts(rows)
    for row, x in zip(rows, v):
        row["cell"] = x
    return {"margin_pp": 100 * margin, "rows": rows, "summary": summarise(v)}


def cell_table(recs_cmp, tables: Tables) -> list:
    """One row per (pack, model, condition) of the comparison split."""
    by = defaultdict(list)
    for r in recs_cmp:
        by[(r["pack"], r["pin"], r["condition"])].append(r)
    rows = []
    for (pack, pin, cond), rs in by.items():
        core, s1, right, sib, nopre, exact = [], [], [], [], [], []
        for r in rs:
            u, lang, kind, name = r["unit_id"], r["language"], r["kind"], proposed(r)
            core.append((u, bool(metrics(r).get("core_ok"))))
            s1.append((u, score(name, lang, tables.rules_s1(pack, lang, kind))))
            pc = prefix_class(name, tables.required_prefix(pack, lang, kind), tables.family[pack])
            right.append((u, pc == "right"))
            sib.append((u, pc == "sibling"))
            nopre.append((u, pc in ("none", "no name")))
            exact.append((u, bool(metrics(r).get("exact_match"))))
        costs = [r.get("cost_usd") for r in rs if r.get("cost_usd") is not None]
        rows.append({"pack": pack, "model": pin, "condition": cond, "tasks": len({r["unit_id"] for r in rs}),
                     "trials": len(rs), "core_ok_s2": task_mean(core), "core_ok_s1": task_mean(s1),
                     "prefix_right": task_mean(right), "prefix_sibling": task_mean(sib),
                     "prefix_none": task_mean(nopre), "exact_match": task_mean(exact),
                     "prompt_tokens": mean_of(rs, "prompt_tokens"), "completion_tokens": mean_of(rs, "completion_tokens"),
                     "cost_usd": sum(costs) if costs else None,
                     "at_limit": sum(r.get("finish") == LIMIT_FINISH for r in rs)})
    pins = pin_order({r["model"] for r in rows})
    return sorted(rows, key=lambda r: (pack_rank(r["pack"]), pins.index(r["model"]), cond_rank(r["condition"]),
                                       r["condition"]))


def tasks_of(recs_cmp, pack) -> dict:
    """unit_id -> one record of the task (the fields of the task are the same in every record)."""
    out = {}
    for r in recs_cmp:
        if r["pack"] == pack and r["unit_id"] not in out:
            out[r["unit_id"]] = r
    return out


def snippet_report(recs_cmp, idx, tables, packs, snippets, notes) -> list:
    out = []
    for pack in packs:
        tasks = tasks_of(recs_cmp, pack)
        if pack in notes or pack not in snippets:
            out.append({"pack": pack, "note": notes.get(pack, "benchmark not read"), "tasks": len(tasks)})
            continue
        with_ids, missing, examples = {}, [], []
        for uid, r in sorted(tasks.items()):
            code = snippets[pack].get(uid)
            if code is None:
                missing.append(uid)
                continue
            others = prefixed_others(code, r["language"], r["injected"],
                                     tables.required_prefix(pack, r["language"], r["kind"]))
            if others:
                with_ids[uid] = others
                if len(examples) < 5:
                    examples.append({"unit": uid, "identifiers": others[:5]})
        kinds = Counter(tasks[u]["kind"] for u in with_ids)
        per_model = []
        for model in pin_order(C.models_of(idx, pack)):
            um = C.unit_means(C._cell(idx, pack, model, NONE))
            a = [v for u, v in um.items() if u in with_ids]
            b_ = [v for u, v in um.items() if u not in with_ids]
            per_model.append({"model": model, "with": mean(a), "n_with": len(a), "without": mean(b_),
                              "n_without": len(b_)})
        out.append({"pack": pack, "tasks": len(tasks), "with_prefixed_identifier": len(with_ids),
                    "by_kind": dict(kinds), "missing_snippets": missing, "examples": examples,
                    "none_by_group": per_model})
    return out


def inference_report(recs_cmp, packs) -> list:
    out = []
    for pack in packs:
        seen = defaultdict(set)
        meta = {}
        for r in recs_cmp:
            if r["pack"] == pack and r["condition"] == INFER:
                seen[r["unit_id"]].add(r.get("kind_inferred"))
                meta[r["unit_id"]] = r["kind"]
        pairs = Counter()
        inconsistent = 0
        for u, ks in seen.items():
            if len(ks) > 1:
                inconsistent += 1
            pairs[(meta[u], str(sorted(ks, key=str)[0]))] += 1
        agree = sum(n for (m, k), n in pairs.items() if m == k)
        out.append({"pack": pack, "tasks": len(seen), "agree": agree, "inconsistent_across_trials": inconsistent,
                    "pairs": [{"metadata": m, "inferred": k, "tasks": n} for (m, k), n in sorted(pairs.items())]})
    return out


def inferred_kinds(recs_cmp) -> dict:
    out = {}
    for r in recs_cmp:
        if r["condition"] == INFER and (r["pack"], r["unit_id"]) not in out:
            out[(r["pack"], r["unit_id"])] = r.get("kind_inferred")
    return out


def reference_report(recs_cmp, idx, tables, packs) -> list:
    inf = inferred_kinds(recs_cmp)
    out = []
    for pack in packs:
        tasks = tasks_of(recs_cmp, pack)
        vals = {}
        for cond in (NONE, SELECTION):
            per = []
            for model in C.models_of(idx, pack):
                d = C.unit_means(C._cell(idx, pack, model, cond))
                if d:
                    per.append(sum(d.values()) / len(d))
            vals[cond] = mean(per)
        row = {"pack": pack, "none": vals[NONE], "selection": vals[SELECTION], "variants": []}
        for source in ("metadata", "inferred"):
            n = ok = em = 0
            by_method = defaultdict(lambda: [0, 0, 0])
            fails = []
            for uid, r in sorted(tasks.items()):
                if source == "inferred" and (pack, uid) not in inf:
                    continue
                kind = r["kind"] if source == "metadata" else inf[(pack, uid)]
                name = reference_name(r["injected"], r["language"], kind, tables, pack)
                s = bool(score(name, r["language"], tables.rules(pack, r["language"], r["kind"])))
                e = name == r["original"]
                n += 1
                ok += s
                em += e
                bm = by_method[str(r.get("injection"))]
                bm[0] += 1
                bm[1] += s
                bm[2] += e
                if not (s and e) and len(fails) < 10:
                    fails.append({"unit": uid, "kind": r["kind"], "kind_used": kind, "injected": r["injected"],
                                  "proposed": name, "original": r["original"], "core_ok_s2": s})
            if n == 0:
                continue
            lo, hi = wilson(ok, n)
            elo, ehi = wilson(em, n)
            row["variants"].append({"kind_source": source, "tasks": n, "core_ok_s2": ok / n, "core_lo": lo,
                                    "core_hi": hi, "exact_match": em / n, "exact_lo": elo, "exact_hi": ehi,
                                    "by_method": {k: {"tasks": v[0], "core_ok_s2": v[1], "exact": v[2]}
                                                  for k, v in sorted(by_method.items())},
                                    "not_restored": fails})
        out.append(row)
    return out


def scorer_check(recs, tables) -> dict:
    checked = mismatch = 0
    for r in recs:
        name = proposed(r)
        if name is None or metrics(r).get("core_ok") is None:
            continue
        checked += 1
        stored = bool(metrics(r)["core_ok"])
        if bool(score(name, r["language"], tables.rules(r["pack"], r["language"], r["kind"]))) != stored:
            mismatch += 1
    return {"checked": checked, "mismatch": mismatch}


def read_canary(canary_dirs, keep: str = "first") -> dict:
    """The records of the canary runs, each run folder read on its own, with the side (before, after) in the field
    `canary_side`; and the counts of each folder."""
    recs, runs = [], []
    for d in canary_dirs or ():
        base = os.path.basename(os.path.normpath(d))
        side = "before" if "canary_before" in base else ("after" if "canary_after" in base else None)
        if side is None:
            raise ValueError(f"{d}: the name of a canary run folder holds canary_before or canary_after")
        rs, info, _err = read_runs([d], keep)
        for r in rs:
            r["canary_side"] = side
        recs.extend(rs)
        runs.extend(info)
    return {"records": recs, "runs": runs}


def drift(canary: dict | None, recs_cmp, packs, model_field: str = "pin") -> dict:
    """HYPOTHESES_v2.md Section 2.1 on the canary runs of Study 2 (see the module text)."""
    if not canary or not canary.get("records"):
        return {"available": False, "models": [], "flagged": []}
    sides = defaultdict(lambda: {"before": {}, "after": {}})
    trials = defaultdict(list)
    for r in canary["records"]:
        if r.get("pack") in packs and r.get("condition") == NONE:
            sides[r.get(model_field)][r["canary_side"]][(r["pack"], r["unit_id"])] = r
            trials[r.get(model_field)].append(r)
    for r in recs_cmp:
        if r.get(model_field) in sides:
            trials[r.get(model_field)].append(r)
    rows = []
    for model in pin_order(sides):
        bef, aft = sides[model]["before"], sides[model]["after"]
        keys = sorted(set(bef) & set(aft), key=str)
        ob = [bool(metrics(bef[k]).get("core_ok")) for k in keys]
        oa = [bool(metrics(aft[k]).get("core_ok")) for k in keys]
        down = sum(x and not y for x, y in zip(ob, oa))
        up = sum(y and not x for x, y in zip(ob, oa))
        p = mcnemar_p(down, up) if keys else None
        ordered = sorted(trials[model], key=lambda r: str(r.get("ts") or ""))
        ident = [tuple(str(r.get(f)) for f in IDENTITY) for r in ordered]
        changed = bool(ident) and ident[0] != ident[-1]
        rows.append({"model": model, "units": len(keys), "units_by_pack": dict(Counter(k[0] for k in keys)),
                     "before_only": len(set(bef) - set(aft)), "after_only": len(set(aft) - set(bef)),
                     "before": mean([float(x) for x in ob]), "after": mean([float(x) for x in oa]),
                     "down": down, "up": up, "mcnemar_p": p,
                     "same_name": (sum(proposed(bef[k]) == proposed(aft[k]) for k in keys) / len(keys)) if keys else None,
                     "first_identity": list(ident[0]) if ident else None,
                     "last_identity": list(ident[-1]) if ident else None,
                     "distinct_identities": [list(x) for x in sorted(set(ident))], "identity_changed": changed,
                     "flagged": bool(changed or (p is not None and p < C.ALPHA))})
    return {"available": True, "models": rows, "flagged": [r["model"] for r in rows if r["flagged"]],
            "runs": canary.get("runs", [])}


def compare(recs_cmp, included, packs, b, seed, model_field="pin", cluster_field="file") -> dict:
    idx, clusters = C.build_index(recs_cmp, model_field, cluster_field)
    return {"idx": idx, "clusters": clusters, "h1": C.h1(idx, included, SELECTION, NONE),
            "h2": h2(idx, clusters, packs, recs_cmp, b, seed), "h3": h3(idx, clusters, packs, b, seed),
            "h4": h4(idx, clusters, packs, b, seed)}


def analyse(recs, runs, error_keys, packs=PACKS, compare_split: str = "test", model_field: str = "pin",
            cluster_field: str = "file", b: int = C.BOOT_B, seed: int = C.BOOT_SEED, models=None,
            snippets=None, snippet_notes=None, tables: Tables | None = None, keep: str = "first",
            canary: dict | None = None) -> dict:
    tables = tables or Tables()
    matched = None
    if models:
        recs, matched = C.select_models(recs, models, model_field)
        if canary and canary.get("records"):
            canary = dict(canary, records=C.select_models(canary["records"], models, model_field)[0])
    recs = [r for r in recs if r.get("task", "rename") == "rename" and r.get("pack") in packs]
    idx_all, _ = C.build_index(recs, model_field, cluster_field)
    elig = C.eligibility(idx_all, packs, NONE)
    included = [e["pack"] for e in elig if e["eligible"]]
    recs_cmp = [dict(r, split="test") for r in recs if r.get("split") == compare_split]
    main = compare(recs_cmp, included, packs, b, seed, model_field, cluster_field)
    idx = main["idx"]
    dr = drift(canary, recs_cmp, packs, model_field)
    sens = None
    if dr["flagged"]:
        kept = [r for r in recs_cmp if r.get(model_field) not in set(dr["flagged"])]
        s = compare(kept, included, packs, b, seed, model_field, cluster_field)
        sens = {"without": dr["flagged"], "h1": s["h1"], "h2": s["h2"], "h3": s["h3"]}
    return {"settings": {"packs": list(packs), "compare_split": compare_split, "model_field": model_field,
                         "cluster_field": cluster_field, "bootstrap_b": b, "bootstrap_seed": seed,
                         "threshold": C.ELIGIBILITY_THRESHOLD, "alpha": C.ALPHA, "keep": keep, "models": matched,
                         "cluster_sources": C.cluster_sources(recs_cmp, cluster_field)},
            "runs": runs, "n_records": len(recs), "n_error_keys": len(error_keys), "error_keys": error_keys[:50],
            "scorer_check": scorer_check(recs, tables), "drift": dr,
            "eligibility": elig, "h1_status": C.h1_status(elig, main["h1"]), "h1": main["h1"],
            "h2": main["h2"], "h3": main["h3"], "h4": main["h4"], "sensitivity": sens,
            "cells": cell_table(recs_cmp, tables),
            "snippets": snippet_report(recs_cmp, idx, tables, packs, snippets or {}, snippet_notes or {}),
            "inference": inference_report(recs_cmp, packs),
            "reference": reference_report(recs_cmp, idx, tables, packs)}


# ---------------------------------------------------------------------------------------------------------- report

def _t(headers, rows):
    out = ["| " + " | ".join(headers) + " |", "|" + "|".join(["---"] * len(headers)) + "|"]
    out += ["| " + " | ".join(str(c) for c in r) + " |" for r in rows]
    return "\n".join(out)


def _p(x, d=1):
    return "n/a" if x is None else f"{100 * x:.{d}f}"


def _n(x, d=0):
    return "-" if x is None else f"{x:,.{d}f}"


def _g(x):
    return f"{x:.3g}"


def _ci(r):
    return f"[{r['ci_low_pp']:+.1f}, {r['ci_high_pp']:+.1f}]"


def render(res: dict) -> str:
    s = res["settings"]
    split = s["compare_split"]
    out = ["# Study 2 analysis (HYPOTHESES_v2_study2)", ""]
    if split != "test":
        out += [f"**Comparisons on the {split} split: a check of the procedure, not a result of the study.**", ""]
    out += [f"Packs: {', '.join(s['packs'])}. Comparisons on the {split} split, eligibility on dev. Unit = one task, "
            f"mean of core_ok_s2 over its rounds. Intervals: cluster bootstrap over `{s['cluster_field']}`, "
            f"{s['bootstrap_b']} resamples, seed {s['bootstrap_seed']}. Duplicate records of a key: the {s['keep']} "
            "by time stamp is used." + (f" Models: {', '.join(s['models'])}." if s.get("models") else ""), ""]

    out += ["## Records", ""]
    out += [_t(["run", "family", "model", "lines", "not JSON", "records", "with an error", "duplicates not used"],
               [[r["run"], r["family"], r["pin"], r["lines"], r["corrupt"], r["records"], r["error_records"],
                 r["duplicates_not_used"]] for r in res["runs"]]), ""]
    sc = res["scorer_check"]
    cs = s["cluster_sources"]
    out += [f"Records used: {res['n_records']}; keys with errors only (left out): {res['n_error_keys']}. "
            f"Scorer check: {sc['checked']} trials with a valid name re-scored, {sc['mismatch']} differ from the stored "
            f"core_ok_s2. Units clustered by the field: {cs['field']}, by snippet id: {cs['snippet_id']}, "
            f"alone: {cs['unit']}.", ""]

    dr = res["drift"]
    out += ["## Drift check (HYPOTHESES_v2 Section 2.1: canary before and after, condition none)", ""]
    if not dr["available"]:
        out += ["No canary run folders were given.", ""]
    else:
        out += [_t(["model", "units", "before (%)", "after (%)", "change (pp)", "pass->fail", "fail->pass",
                    "McNemar p", "same name (%)", "model/provider/fingerprint", "flagged"],
                   [[r["model"], r["units"], _p(r["before"]), _p(r["after"]),
                     "-" if r["before"] is None else f"{100 * (r['after'] - r['before']):+.1f}", r["down"], r["up"],
                     "-" if r["mcnemar_p"] is None else _g(r["mcnemar_p"]), _p(r["same_name"]),
                     "changed" if r["identity_changed"] else "same", "yes" if r["flagged"] else "no"]
                    for r in dr["models"]]), ""]
        for r in dr["models"]:
            extra = []
            if r["before_only"] or r["after_only"]:
                extra.append(f"units in one canary run only: before {r['before_only']}, after {r['after_only']}")
            extra.append(f"first trial {' / '.join(r['first_identity'] or [])}; last trial "
                         f"{' / '.join(r['last_identity'] or [])}; distinct values {len(r['distinct_identities'])}")
            out += [f"- {r['model']}: " + "; ".join(extra) + "."]
        out += ["", "Flagged: changed model, provider or system_fingerprint between the first and the last trial of the "
                "model, or McNemar p < 0.05. A flag changes no data; see the sensitivity analysis.", ""]

    out += ["## Eligibility for H1-S2 (Section 2.3: mean core_ok_s2 of none on dev, over the models; included if "
            f"below {s['threshold']:.2f})", ""]
    rows = []
    for e in res["eligibility"]:
        pm = ", ".join(f"{m}: {_p(e['per_model'][m])}" for m in pin_order(e["per_model"]))
        rows.append([e["pack"], _p(e["value"]), e["n_models"],
                     {True: "yes", False: "no", None: "no dev data"}[e["eligible"]], pm])
    out += [_t(["standard", "none on dev (%)", "models", "included", "per model (%)"], rows), ""]

    out += ["## H1-S2 (confirmatory): selection vs none, exact two-sided sign test, Holm over these tests", ""]
    if res["h1"]:
        out += [_t(["standard", "model", "tasks", "better", "worse", "tied", "mean diff (pp)", "p", "p (Holm)",
                    "supports"],
                   [[r["pack"], r["model"], r["units"], r["up"], r["down"], r["tie"], f"{r['mean_diff_pp']:+.1f}",
                     _g(r["p"]), _g(r["p_holm"]), "yes" if r["supports"] else "no"] for r in res["h1"]]), "",
                f"Holm family: {len(res['h1'])} tests; supports = adjusted p < {s['alpha']} and a positive mean "
                f"difference. Tests that support H1-S2: {sum(r['supports'] for r in res['h1'])} of {len(res['h1'])}.", ""]
    else:
        out += [{"not_testable": "No standard is included (Section 2.3): Study 2 stops before the test trials.",
                 "no_dev_data": "No dev data for the eligibility rule.",
                 "no_test_data": "An included standard has no paired tasks on this split."}.get(res["h1_status"], "-"), ""]

    h = res["h2"]
    out += [f"## H2-S2: selection - naming (margin {h['margin_pp']:.0f} pp)", ""]
    out += [_t(["standard", "model", "tasks", "files", "mean diff (pp)", "95% CI (pp)", "cell",
                "prompt chars sel / naming", "prompt tokens sel / naming"],
               [[r["pack"], r["model"], r["units"], r["clusters"], f"{r['mean_diff_pp']:+.1f}", _ci(r), r["cell"],
                 f"{_n(r['selection_prompt_chars'])} / {_n(r['naming_prompt_chars'])}",
                 f"{_n(r['selection_prompt_tokens'])} / {_n(r['naming_prompt_tokens'])}"] for r in h["rows"]]), "",
            f"Summary: **{h['summary']}**.", ""]

    h = res["h3"]
    out += [f"## H3-S2: selection - fulldoc (margin {h['margin_pp']:.0f} pp) and selection vs the retrieval "
            "conditions", ""]
    out += [_t(["standard", "model", "tasks", "files", "mean diff (pp)", "95% CI (pp)", "vs fulldoc"],
               [[r["pack"], r["model"], r["units"], r["clusters"], f"{r['mean_diff_pp']:+.1f}", _ci(r), r["verdict"]]
                for r in h["fulldoc"]]), ""]
    out += [_t(["standard", "model", "condition", "tasks", "better", "worse", "tied", "mean diff (pp)", "p",
                "p (Holm)", "higher"],
               [[r["pack"], r["model"], r["baseline"], r["units"], r["up"], r["down"], r["tie"],
                 f"{r['mean_diff_pp']:+.1f}", _g(r["p"]), _g(r["p_holm"]), "yes" if r["higher"] else "no"]
                for r in h["retrieval"]]), "",
            f"Holm family: {len(h['retrieval'])} tests (chunk is TF-IDF).", ""]
    out += [_t(["standard", "model", "vs fulldoc", "higher than chunk, bm25 and dense", "cell"],
               [[c["pack"], c["model"], c["fulldoc"], "yes" if c["higher_than_all_retrieval"] else "no", c["cell"]]
                for c in h["cells"]]), "", f"Summary: **{h['summary']}**.", ""]

    h = res["h4"]
    out += [f"## H4-S2 (exploratory): kind and facets inferred - from metadata, selection (margin "
            f"{h['margin_pp']:.0f} pp)", ""]
    out += [_t(["standard", "model", "tasks", "files", "mean diff (pp)", "95% CI (pp)", "cell"],
               [[r["pack"], r["model"], r["units"], r["clusters"], f"{r['mean_diff_pp']:+.1f}", _ci(r), r["cell"]]
                for r in h["rows"]]), "", f"Summary: **{h['summary']}**.", ""]

    sens = res.get("sensitivity")
    if sens:
        out += [f"## Sensitivity: H1-S2, H2-S2 and H3-S2 without the flagged models ({', '.join(sens['without'])})", ""]
        out += [_t(["standard", "model", "tasks", "mean diff (pp)", "p", "p (Holm)", "supports"],
                   [[r["pack"], r["model"], r["units"], f"{r['mean_diff_pp']:+.1f}", _g(r["p"]), _g(r["p_holm"]),
                     "yes" if r["supports"] else "no"] for r in sens["h1"]]), "",
                f"H1-S2 Holm family without the flagged models: {len(sens['h1'])} tests. "
                f"H2-S2: **{sens['h2']['summary']}**. H3-S2: **{sens['h3']['summary']}**.", ""]

    out += ["## Results by condition (exploratory)", "",
            "core_ok_s2, Study 1 core_ok (casing; n/a where the Study 1 core has no rule for the kind), the required "
            "prefix (right, a sibling prefix, no prefix or no valid name) and exact_match in % (mean over tasks of the "
            "mean over rounds); tokens are means per trial; cost is the sum in USD; at limit = trials that ended at the "
            "output limit.", ""]
    out += [_t(["standard", "model", "condition", "tasks", "trials", "core_ok_s2", "S1 core_ok", "prefix right",
                "sibling", "no prefix", "exact", "prompt tok", "completion tok", "cost", "at limit"],
               [[r["pack"], r["model"], r["condition"], r["tasks"], r["trials"], _p(r["core_ok_s2"]),
                 _p(r["core_ok_s1"]), _p(r["prefix_right"]), _p(r["prefix_sibling"]), _p(r["prefix_none"]),
                 _p(r["exact_match"]), _n(r["prompt_tokens"]), _n(r["completion_tokens"]),
                 "-" if r["cost_usd"] is None else f"{r['cost_usd']:.4f}", r["at_limit"]] for r in res["cells"]]), ""]

    out += ["## Tasks whose snippet holds another identifier with the required prefix", ""]
    for x in res["snippets"]:
        if "note" in x:
            out += [f"- {x['pack']}: not computed ({x['note']}).", ""]
            continue
        out += [f"- {x['pack']}: {x['with_prefixed_identifier']} of {x['tasks']} tasks"
                + (f" (by kind: {', '.join(f'{k} {v}' for k, v in sorted(x['by_kind'].items()))})" if x["by_kind"] else "")
                + (f"; snippets not found: {len(x['missing_snippets'])}" if x["missing_snippets"] else "") + "."]
        if x["examples"]:
            out += ["  Examples: " + "; ".join(f"{e['unit']}: {', '.join(e['identifiers'])}" for e in x["examples"]) + "."]
        out += ["", _t(["model", "none core_ok_s2 with (%)", "tasks", "without (%)", "tasks"],
                       [[m["model"], _p(m["with"]), m["n_with"], _p(m["without"]), m["n_without"]]
                        for m in x["none_by_group"]]), ""]

    out += ["## Agreement of the inferred kind and facets with metadata", ""]
    for x in res["inference"]:
        if not x["tasks"]:
            out += [f"- {x['pack']}: no infer trials."]
            continue
        out += [f"- {x['pack']}: {x['agree']} of {x['tasks']} tasks agree"
                + (f"; tasks whose inferred kind differs between trials: {x['inconsistent_across_trials']}"
                   if x["inconsistent_across_trials"] else "")
                + ". " + "; ".join(f"{p['metadata']} -> {p['inferred']}: {p['tasks']}" for p in x["pairs"]) + "."]
    out += [""]

    out += ["## Reference program (as addendum A10; no model)", "",
            "core_ok_s2 is scored for the kind from metadata; none and selection are the mean over the models of "
            "core_ok_s2 on the same split.", ""]
    rows = []
    for x in res["reference"]:
        for v in x["variants"]:
            meth = ", ".join(f"{k} {m['core_ok_s2']}/{m['tasks']}" for k, m in v["by_method"].items())
            rows.append([x["pack"], v["kind_source"], v["tasks"],
                         f"{_p(v['core_ok_s2'])} [{_p(v['core_lo'])}, {_p(v['core_hi'])}]",
                         f"{_p(v['exact_match'])} [{_p(v['exact_lo'])}, {_p(v['exact_hi'])}]", meth,
                         _p(x["none"]), _p(x["selection"])])
    out += [_t(["standard", "kind from", "tasks", "core_ok_s2 % [95% Wilson]", "exact % [95% Wilson]",
                "core_ok_s2 by method", "none %", "selection %"], rows), ""]
    for x in res["reference"]:
        for v in x["variants"]:
            for f in v["not_restored"]:
                out += [f"- {x['pack']} ({v['kind_source']}) {f['unit']}: `{f['injected']}` -> `{f['proposed']}` "
                        f"(kind used {f['kind_used']}); original `{f['original']}`; core_ok_s2 {f['core_ok_s2']}"]
    out += [""]
    return "\n".join(out)


def run(run_dirs, bench_dir=None, keep="first", canary_dirs=None, **kw) -> tuple:
    recs, runs, error_keys = read_runs(run_dirs, keep)
    packs = kw.get("packs", PACKS)
    snippets, notes = load_snippets(packs, bench_dir)
    res = analyse(recs, runs, error_keys, snippets=snippets, snippet_notes=notes, keep=keep,
                  canary=read_canary(canary_dirs, keep), **kw)
    return res, render(res)


def dumps(res: dict) -> str:
    return json.dumps(res, indent=2, sort_keys=True, default=str)
