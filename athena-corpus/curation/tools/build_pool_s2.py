#!/usr/bin/env python3
"""Build the pool of Study 2 tasks of one pack (HYPOTHESES_v2_study2, Benchmark).

The criteria are those of tools/build_pool.py (Study 1, D18) with the Study 2 kinds, units and injection methods:

  kinds       facets_s2.extract_s2: the kind from metadata of every declaration (Godot parameters, dotnet-runtime
              fields); the gate and the targets use it
  units       facets_s2: Godot functions and methods of 6 to 40 lines (the Study 1 units), dotnet-runtime class and
              struct declarations of 6 to 60 lines, nested ones included; no overlap with a parse error
  qualifies   the unit holds a declaration of a Study 2 kind (input_parameter, output_parameter; instance_field,
              static_field, threadstatic_field)
  gate        every declaration that the Study 2 core checks passes all its core rules
  targets     the declarations of a Study 2 kind that can be renamed (the checks of Study 1: name length, rename plan,
              text coupling), and whose name is declared only once in the unit (a class unit can hold a nested type
              that declares the same name). They are put in a fixed random order seeded per unit with
              "athena2-s2-v1:<pack>:target:<path>:<unit_index>"
  methods     prefix_strip removes the required prefix (the candidate of Study 1 for a prefix rule); prefix_swap
              replaces it with the prefix of a sibling kind (Godot p_ <-> r_; dotnet-runtime _, s_, t_, the two
              siblings in a fixed random order seeded with "athena2-s2-v1:<pack>:sibling:<path>:<unit_index>:<name>").
              The rule is the prefix rule of the target's kind. Changes of casing are not used.
  violation   for each method, the first target in the order above that gets a verified candidate. A candidate is
              verified as in Study 1: a valid identifier that is not already in the unit, fails the rule under the
              checker, leaves the parse-tree shape of the whole file unchanged after every occurrence is renamed, and
              gets no binding or declaration conflict from the scope-aware check
  pool        a unit enters the pool when at least one method has a verified violation (--pool-rule either, the
              default); tools/export_tasks_s2.py assigns the methods after the task draw and gives a unit with one
              verified method that method. --pool-rule both admits only units with both methods (a diagnostic)
  duplicates  a unit whose code (white space collapsed) equals that of an earlier unit of the pool is dropped

Nothing here calls an LLM, and two runs give identical files.

Outputs in --out-dir: <pack>_pool.tsv (for tools/select_tasks_s2.py), <pack>_pool_units.jsonl (read by
tools/export_tasks_s2.py), <pack>_pool_stats.json (counts by reason, kind, method and side).

  python3 tools/build_pool_s2.py --pack godot-s2 --language cpp --corpus ../corpus_v2 \\
      --ontology ../../athena-sim/packs/godot-s2/godot_ontology.json \\
      --core ../../athena-sim/packs/godot-s2/core_rules.json --out-dir pool_s2/
"""
from __future__ import annotations

import argparse
import collections
import csv
import json
import os
import random
import re
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
CUR = os.path.dirname(HERE)
sys.path.insert(0, CUR)
sys.path.insert(0, HERE)

import build_pool as BP  # noqa: E402
import curate as C  # noqa: E402
import facets_s2 as F  # noqa: E402
import rules as R  # noqa: E402
import select_tasks  # noqa: E402
from output_validator import check_naming_compliance  # noqa: E402

SEED = "athena2-s2-v1"
METHODS = ("prefix_strip", "prefix_swap")
SIBLINGS = {"cpp": {"p_": ("r_",), "r_": ("p_",)},
            "csharp": {"_": ("s_", "t_"), "s_": ("_", "t_"), "t_": ("_", "s_")}}
POOL_COLUMNS = ["path", "unit_index", "repo", "start_line", "end_line", "unit", "top_level",
                "strip_kind", "strip_original", "strip_injected", "swap_kind", "swap_original", "swap_injected"]


def target_rng(pack, path, unit_index):
    return random.Random("%s:%s:target:%s:%d" % (SEED, pack, path, unit_index))


def sibling_order(lang, pack, path, unit_index, name, prefix):
    sibs = list(SIBLINGS[lang].get(prefix, ()))
    random.Random("%s:%s:sibling:%s:%d:%s" % (SEED, pack, path, unit_index, name)).shuffle(sibs)
    return sibs


def prefix_rule_id(lang, d, onto):
    """The core rule of the target's kind that requires a prefix (exactly one for a Study 2 kind)."""
    ids = [rid for rid in R.target_rule_ids(lang, d) if onto.rule(rid).get("prefix")]
    if len(ids) != 1:
        raise ValueError("kind %s of %s needs exactly one core prefix rule, found %s" % (d.kind, lang, ids))
    return ids[0]


def eligible_targets(lang, ff, decls, toks, u_start, u_end, stats):
    """build_pool.eligible_targets restricted to the Study 2 kinds, with the extra check on duplicate names."""
    eligible, seen = [], set()
    names = collections.Counter(d.name for d in decls)
    for d in sorted(decls, key=lambda x: x.start):
        if d.exempt or d.kind not in F.S2_KINDS[lang] or (lang, d.kind) not in R.CORE or d.name in seen:
            continue
        if R.name_for_check(lang, d) != d.name or len(d.name) < C.MIN_TARGET_LEN:
            continue
        seen.add(d.name)
        if names[d.name] > 1:
            stats["target_rejects"]["name_declared_more_than_once"] += 1
            continue
        spans, why = C.plan_rename(lang, ff, decls, toks, d)
        if spans is None:
            stats["target_rejects"][why] += 1
            continue
        why, comment_edits = C.text_coupling(ff, u_start, u_end, d.name)
        if why:
            stats["target_rejects"][why] += 1
            continue
        eligible.append((d, spans, comment_edits))
    return eligible


def verify(lang, ff, u, original, spans, comment_edits, rid, rule, method, cand, unit_names, base_text, stats):
    """The violation record when renaming `original` to `cand` passes the checks of Study 1
    (build_pool.evaluate_unit), else None."""
    if not R.is_valid_new_name(lang, cand) or cand in unit_names or C._word_re(cand).search(base_text):
        stats["candidate_rejects"][method + ":invalid_or_present"] += 1
        return None
    ok, reasons = check_naming_compliance(cand, rule)
    if ok:
        stats["candidate_rejects"][method + ":passes_rule"] += 1
        return None
    new_src = C.apply_edits(ff.src, [(t.start, t.end) for t in spans] + comment_edits, cand)
    try:
        fp = ff.reverify(new_src)
    except Exception:
        stats["rename_verify"]["reparse_exception"] += 1
        return None
    same = (fp[0] == ff.shape) and (not fp[1] or bool(ff.error_spans))
    if not same:
        stats["rename_verify"]["shape_changed"] += 1
        return None
    if not BP.scope_accepts(lang, base_text, original, cand, stats):
        return None
    new_ls = C.line_starts_of(new_src)
    stats["rename_verify"]["ok"] += 1
    return {"rule": rid, "method": method, "injected": cand, "reasons": reasons,
            "code": C.unit_text(new_src, new_ls, u.start_line, u.end_line),
            "occurrences": len(spans), "comment_occurrences": len(comment_edits)}


def candidates(lang, pack, path, unit_index, d, rule, method):
    prefix = rule["prefix"]
    if method == "prefix_strip":
        return [c for m, c in R.iter_candidates(d.name, rule) if m == "prefix_strip"]
    if not d.name.startswith(prefix) or len(d.name) == len(prefix):
        return []
    return [s + d.name[len(prefix):] for s in sibling_order(lang, pack, path, unit_index, d.name, prefix)]


def evaluate_unit(pack, lang, ff, u, unit_index, path, onto, stats, max_lines=None, pool_rule="either"):
    """The pool record of the unit (without provenance), or None."""
    st = stats["units"]
    lo, hi = F.UNIT_LINES[lang]
    hi = max_lines or hi
    n = u.end_line - u.start_line + 1
    if n < lo:
        st["too_short"] += 1
        return None
    if n > hi:
        st["too_long"] += 1
        return None
    u_start, u_end = C.unit_range(ff, u)
    if any(a < u_end and b > u_start for a, b in ff.error_spans):
        st["parse_error_in_unit"] += 1
        return None
    decls = [d for d in ff.decls if u_start <= d.start < u_end]
    if not any(not d.exempt and d.kind in F.S2_KINDS[lang] for d in decls):
        st["no_s2_kind"] += 1
        return None
    st["qualifying"] += 1
    toks = [t for t in ff.toks if u_start <= t.start < u_end]
    for d in decls:                       # gate
        if d.exempt or (lang, d.kind) not in R.CORE:
            continue
        f = R.gate(lang, d, onto)
        if f:
            st["noncompliant_identifier"] += 1
            stats["unit_gate_failures_by_rule"][f[0][0]] += 1
            return None
    st["after_gate"] += 1
    eligible = eligible_targets(lang, ff, decls, toks, u_start, u_end, stats)
    if not eligible:
        st["no_eligible_target"] += 1
        return None
    target_rng(pack, path, unit_index).shuffle(eligible)
    unit_names = {t.text for t in toks}
    base_text = C.unit_text(ff.src, ff.line_starts, u.start_line, u.end_line)
    found = {}
    for method in METHODS:
        for d, spans, comment_edits in eligible:
            rid = prefix_rule_id(lang, d, onto)
            rule = onto.rule(rid)
            if not check_naming_compliance(R.name_for_check(lang, d), rule)[0]:
                continue
            viol = None
            for cand in candidates(lang, pack, path, unit_index, d, rule, method):
                if cand == d.name:
                    continue
                viol = verify(lang, ff, u, d.name, spans, comment_edits, rid, rule, method, cand, unit_names,
                              base_text, stats)
                if viol:
                    break
            if viol:
                found[method] = {"target": {"name": d.name, "kind": d.kind, "kind_infer": d.extra.get("kind_infer"),
                                            "facets": d.extra.get("s2", {})},
                                 "violation": viol}
                break
    for m in METHODS:
        if m not in found:
            stats["methods_missing"][m] += 1
    if not found:
        st["no_violation"] += 1
        return None
    if len(found) < len(METHODS):
        if pool_rule == "both":
            st["one_method_only"] += 1
            return None
        st["one_method_only_kept"] += 1
    return {"start_line": u.start_line + 1, "end_line": u.end_line + 1, "unit": u.label, "top_level": u.top_level,
            "code": base_text, "methods": found}


def new_stats():
    s = BP.new_stats()
    s["candidate_rejects"] = collections.Counter()
    s["methods_missing"] = collections.Counter()
    return s


def build(pack, lang, corpus, onto, ts, limit_files=None, progress=None, max_lines=None, pool_rule="either"):
    """Return (records, stats). Records are in the order (file name, unit index)."""
    stats = new_stats()
    index = C.load_index(corpus)
    ldir = os.path.join(corpus, "corpus", lang)
    records, seen_code = [], set()
    names = sorted(n for n in os.listdir(ldir) if n.endswith(".md"))
    if limit_files:
        names = names[:limit_files]
    t0 = time.time()
    for i, name in enumerate(names, 1):
        meta, content = C.parse_corpus_md(os.path.join(ldir, name))
        row = index.get((lang, name))
        if content is None:
            stats["skipped_files"].append([name, "no code block"])
            continue
        if row and row.get("git_blob_sha1_12") and C.blob12(content) != row["git_blob_sha1_12"]:
            stats["index_mismatch"].append(name)
        ff = F.extract_s2(lang, meta["file path"], content, ts)
        if not ff.parse_ok:
            stats["skipped_files"].append([name, ff.skip_reason])
            continue
        stats["files"]["parsed"] += 1
        for unit_index, u in enumerate(ff.units_s2):
            stats["units"]["total"] += 1
            rec = evaluate_unit(pack, lang, ff, u, unit_index, meta["file path"], onto, stats, max_lines, pool_rule)
            if rec is None:
                continue
            key = re.sub(r"\s+", " ", rec["code"])
            if key in seen_code:
                stats["units"]["duplicate_code_dropped"] += 1
                continue
            seen_code.add(key)
            rec.update({"path": meta["file path"], "unit_index": unit_index, "file": name,
                        "repo": meta["source repo"], "repo_url": meta.get("repo url"), "commit": meta["commit"],
                        "license": meta["license"], "created_at": meta["created_at"]})
            records.append(rec)
        if progress and (i % 25 == 0 or i == len(names)):
            progress("[%s] %d/%d files, %d units, pool %d (%.0fs)" % (
                pack, i, len(names), stats["units"]["total"], len(records), time.time() - t0))
    return records, stats


def summarise(records, stats, max_lines=None, pool_rule="either"):
    out = {k: (dict(v) if isinstance(v, collections.Counter) else v) for k, v in stats.items()}
    sides = collections.Counter(select_tasks.side_of(r["path"]) for r in records)
    files = collections.defaultdict(set)
    for r in records:
        files[select_tasks.side_of(r["path"])].add(r["path"])
    out["max_lines"] = max_lines
    out["pool_rule"] = pool_rule
    out["pool"] = {
        "units": len(records), "files": len({r["path"] for r in records}),
        "by_side": dict(sides), "files_by_side": {s: len(v) for s, v in files.items()},
        "top_level": sum(1 for r in records if r["top_level"]),
        "by_method_kind": {m: dict(collections.Counter(r["methods"][m]["target"]["kind"] for r in records
                                                       if m in r["methods"])) for m in METHODS},
        "methods_available": dict(collections.Counter("+".join(sorted(r["methods"])) for r in records)),
        "same_target_both_methods": sum(1 for r in records if len(r["methods"]) == 2 and
                                        r["methods"][METHODS[0]]["target"]["name"]
                                        == r["methods"][METHODS[1]]["target"]["name"]),
    }
    return out


def write_outputs(out_dir, pack, records, stats, max_lines=None, pool_rule="either"):
    os.makedirs(out_dir, exist_ok=True)
    pool = os.path.join(out_dir, "%s_pool.tsv" % pack)
    with open(pool, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh, delimiter="\t", lineterminator="\n")
        w.writerow(POOL_COLUMNS)
        for r in records:
            cols = []
            for m in METHODS:
                x = r["methods"].get(m)
                cols += [x["target"]["kind"], x["target"]["name"], x["violation"]["injected"]] if x else ["", "", ""]
            w.writerow([r["path"], r["unit_index"], r["repo"], r["start_line"], r["end_line"], r["unit"],
                        int(r["top_level"])] + cols)
    units = os.path.join(out_dir, "%s_pool_units.jsonl" % pack)
    with open(units, "w", encoding="utf-8", newline="\n") as fh:
        for r in records:
            fh.write(json.dumps(r, ensure_ascii=False, sort_keys=True) + "\n")
    sp = os.path.join(out_dir, "%s_pool_stats.json" % pack)
    with open(sp, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(summarise(records, stats, max_lines, pool_rule), fh, indent=1, ensure_ascii=False, sort_keys=True)
        fh.write("\n")
    return pool, units, sp


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--pack", required=True, help="pack id, part of the seeds (godot-s2, dotnet-runtime-s2)")
    ap.add_argument("--language", required=True, choices=["cpp", "csharp"])
    ap.add_argument("--corpus", required=True, help="folder with corpus/<language>/*.md and corpus_index.tsv")
    ap.add_argument("--ontology", required=True, help="ontology JSON of the pack")
    ap.add_argument("--core", required=True, help="core_rules.json of the pack")
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--lib", default=None, help="tree-sitter shared library (see tsbind.find_library)")
    ap.add_argument("--limit-files", type=int, default=None, help="only the first N files (for a quick check)")
    ap.add_argument("--max-lines", type=int, default=None,
                    help="longest unit in lines; the default is the registered limit (40 Godot, 60 dotnet-runtime)")
    ap.add_argument("--pool-rule", choices=["both", "either"], default="either",
                    help="methods a unit needs to enter the pool (see above)")
    a = ap.parse_args(argv)

    import core_table
    from tsbind import TreeSitter, find_library
    onto = R.Ontology(a.ontology)
    problems = core_table.apply(a.core, onto)
    if not any(k[0] == a.language for k in R.CORE):
        problems.append("language %s has no entry in %s" % (a.language, a.core))
    for k in F.S2_KINDS[a.language]:
        if (a.language, k) not in R.CORE:
            problems.append("kind %s has no core rules in %s" % (k, a.core))
    if problems:
        print("CORE rule table inconsistent with ontology:\n  " + "\n  ".join(problems), file=sys.stderr)
        return 2
    ts = TreeSitter(find_library(a.lib))
    records, stats = build(a.pack, a.language, a.corpus, onto, ts, a.limit_files,
                           lambda s: print(s, flush=True), a.max_lines, a.pool_rule)
    pool, units, sp = write_outputs(a.out_dir, a.pack, records, stats, a.max_lines, a.pool_rule)
    print("pool %d units from %d files; wrote %s, %s, %s" % (len(records), len({r["path"] for r in records}),
                                                              pool, units, sp))
    if stats["index_mismatch"]:
        print("WARNING: blob mismatch vs corpus_index.tsv:", stats["index_mismatch"][:5])
    return 0


if __name__ == "__main__":
    sys.exit(main())
