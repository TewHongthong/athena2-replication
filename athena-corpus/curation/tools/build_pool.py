#!/usr/bin/env python3
"""Build the pool of B1 tasks of one pack: one injected violation per unit (HYPOTHESES_v2, D18).

A unit enters the pool when it passes the criteria below and at least one identifier of it can be turned into a
verified violation of a core rule of the human ontology of the pack's standard.

  size        6 to 40 lines (as in Vol. 1)
  parse       the unit does not overlap a parse error of the file
  gate        every identifier that the ontology checks (a kind with core rules, not exempt) already passes all the
              core rules of its kind, so the injected name is the only violation in the snippet
  targets     the identifiers of the unit that can be renamed (the checks of Vol. 1: name length, whole-word
              occurrences, text coupling, rename plan); at least one is needed (Vol. 1 needs two)
  target      the eligible targets are put in a fixed random order, seeded per unit with
              "athena2-b1-v1:<pack>:target:<path>:<unit_index>", so the draw does not depend on which units are selected;
              the first target that gets a verified violation is the target of the task
  violation   the candidate names are tried in the order of Vol. 1 (casing swap, forbidden pattern, abbreviation,
              prefix strip, suffix strip), and the core rules of the kind are tried in the order of core_rules.json.
              A candidate is accepted when it is a valid identifier, is not already in the unit, fails the rule under
              the checker, leaves the parse-tree shape of the whole file unchanged after renaming every occurrence and
              parsing again, and the scope-aware check (scope_check.check_rename) reports no binding conflict and no
              declaration conflict. A snippet that the scope-aware check cannot analyse (status other than ok) is
              rejected and counted.
  duplicates  a unit whose code (white space collapsed) equals that of an earlier unit of the pool is dropped

Nothing here calls an LLM, and two runs give identical files.

Outputs in --out-dir:
  <pack>_pool.tsv         one row per pool unit, for tools/select_tasks.py (columns path, unit_index, and the rest)
  <pack>_pool_units.jsonl the full record of each pool unit (code, violation, provenance), read by export_tasks.py
  <pack>_pool_stats.json  counts of units and targets rejected by reason, the pool by kind, rule and method

  python3 tools/build_pool.py --pack godot --language cpp --corpus athena-corpus/corpus_v2 \\
      --ontology athena-sim/packs/godot/godot_ontology.json --core athena-sim/packs/godot/core_rules.json \\
      --out-dir pool/
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

import curate as C  # noqa: E402
import rules as R  # noqa: E402
import scope_check  # noqa: E402
import select_tasks  # noqa: E402
from output_validator import check_naming_compliance  # noqa: E402

SEED = select_tasks.SEED
POOL_COLUMNS = ["path", "unit_index", "repo", "start_line", "end_line", "unit", "kind", "rule", "method",
                "original", "injected"]

# Replaced by the tests; the scope-aware check of Section III-F in normal use.
SCOPE_CHECK = scope_check.check_rename


def target_rng(pack, path, unit_index):
    return random.Random("%s:%s:target:%s:%d" % (SEED, pack, path, unit_index))


def scope_accepts(lang, code, original, injected, stats):
    """True when the scope-aware check can analyse the snippet and finds no conflict for the rename."""
    res = SCOPE_CHECK(lang, code, original, injected)
    stats["scope_status"][res.get("status", "?")] += 1
    if res.get("status") != "ok":
        return False
    if res.get("binding_conflict"):
        stats["rename_verify"]["scope_binding_conflict"] += 1
        return False
    if res.get("declaration_conflict"):
        stats["rename_verify"]["scope_declaration_conflict"] += 1
        return False
    return True


def eligible_targets(lang, ff, decls, toks, u_start, u_end, stats):
    """Renameable identifiers of the unit (same checks as curate.evaluate_unit), in the order of the declarations."""
    eligible, seen = [], set()
    for d in sorted(decls, key=lambda x: x.start):
        if d.exempt or (lang, d.kind) not in R.CORE or d.name in seen:
            continue
        if R.name_for_check(lang, d) != d.name or len(d.name) < C.MIN_TARGET_LEN:
            continue
        seen.add(d.name)
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


def evaluate_unit(pack, lang, ff, u, unit_index, path, onto, stats):
    """The pool record of the unit (without provenance), or None."""
    st = stats["units"]
    nlines = u.end_line - u.start_line + 1
    if nlines < C.MIN_LINES:
        st["too_short"] += 1
        return None
    if nlines > C.MAX_LINES:
        st["too_long"] += 1
        return None
    u_start, u_end = C.unit_range(ff, u)
    if any(a < u_end and b > u_start for a, b in ff.error_spans):
        st["parse_error_in_unit"] += 1
        return None
    decls = [d for d in ff.decls if u_start <= d.start < u_end]
    toks = [t for t in ff.toks if u_start <= t.start < u_end]
    for d in decls:                       # gate
        if d.exempt or (lang, d.kind) not in R.CORE:
            continue
        f = R.gate(lang, d, onto)
        if f:
            st["noncompliant_identifier"] += 1
            stats["unit_gate_failures_by_rule"][f[0][0]] += 1
            return None
    eligible = eligible_targets(lang, ff, decls, toks, u_start, u_end, stats)
    if not eligible:
        st["no_eligible_target"] += 1
        return None
    target_rng(pack, path, unit_index).shuffle(eligible)
    unit_names = {t.text for t in toks}
    base_text = C.unit_text(ff.src, ff.line_starts, u.start_line, u.end_line)
    for d, spans, comment_edits in eligible:
        viol = None
        for rid in R.target_rule_ids(lang, d):
            rule = onto.rule(rid)
            ok0, _ = check_naming_compliance(R.name_for_check(lang, d), rule)
            if not ok0:
                continue
            for method, cand in R.iter_candidates(d.name, rule):
                if (cand == d.name or not R.is_valid_new_name(lang, cand) or cand in unit_names
                        or C._word_re(cand).search(base_text)):
                    continue
                ok, reasons = check_naming_compliance(cand, rule)
                if ok:
                    continue
                new_src = C.apply_edits(ff.src, [(t.start, t.end) for t in spans] + comment_edits, cand)
                try:
                    fp = ff.reverify(new_src)
                except Exception:
                    stats["rename_verify"]["reparse_exception"] += 1
                    continue
                if lang == "python":
                    same = fp == ff.shape
                else:
                    same = (fp[0] == ff.shape) and (not fp[1] or bool(ff.error_spans))
                if not same:
                    stats["rename_verify"]["shape_changed"] += 1
                    continue
                if not scope_accepts(lang, base_text, d.name, cand, stats):
                    continue
                new_ls = C.line_starts_of(new_src)
                viol = {"rule": rid, "method": method, "injected": cand, "reasons": reasons,
                        "code": C.unit_text(new_src, new_ls, u.start_line, u.end_line),
                        "occurrences": len(spans), "comment_occurrences": len(comment_edits)}
                stats["rename_verify"]["ok"] += 1
                break
            if viol:
                break
        if viol:
            return {"start_line": u.start_line + 1, "end_line": u.end_line + 1, "unit": u.label, "code": base_text,
                    "target": {"name": d.name, "kind": d.kind}, "violation": viol}
        stats["target_rejects"]["no_verified_violation"] += 1
    st["no_target_with_violation"] += 1
    return None


def new_stats():
    return {"files": collections.Counter(), "skipped_files": [], "index_mismatch": [],
            "units": collections.Counter(), "unit_gate_failures_by_rule": collections.Counter(),
            "target_rejects": collections.Counter(), "rename_verify": collections.Counter(),
            "scope_status": collections.Counter()}


def build(pack, lang, corpus, onto, ts, limit_files=None, progress=None):
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
        ff = C.analyze(lang, meta["file path"], content, ts)
        if not ff.parse_ok:
            stats["skipped_files"].append([name, ff.skip_reason])
            continue
        stats["files"]["parsed"] += 1
        for unit_index, u in enumerate(ff.units):
            stats["units"]["total"] += 1
            rec = evaluate_unit(pack, lang, ff, u, unit_index, meta["file path"], onto, stats)
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


def summarise(records, stats):
    by_kind = collections.Counter(r["target"]["kind"] for r in records)
    by_rule = collections.Counter(r["violation"]["rule"] for r in records)
    by_method = collections.Counter(r["violation"]["method"] for r in records)
    sides = collections.Counter(select_tasks.side_of(r["path"]) for r in records)
    out = {k: (dict(v) if isinstance(v, collections.Counter) else v) for k, v in stats.items()}
    out["pool"] = {"units": len(records), "files": len({r["path"] for r in records}), "by_kind": dict(by_kind),
                   "by_rule": dict(by_rule), "by_injection_method": dict(by_method), "by_side": dict(sides)}
    return out


def write_outputs(out_dir, pack, records, stats):
    os.makedirs(out_dir, exist_ok=True)
    pool = os.path.join(out_dir, "%s_pool.tsv" % pack)
    with open(pool, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh, delimiter="\t", lineterminator="\n")
        w.writerow(POOL_COLUMNS)
        for r in records:
            v = r["violation"]
            w.writerow([r["path"], r["unit_index"], r["repo"], r["start_line"], r["end_line"], r["unit"],
                        r["target"]["kind"], v["rule"], v["method"], r["target"]["name"], v["injected"]])
    units = os.path.join(out_dir, "%s_pool_units.jsonl" % pack)
    with open(units, "w", encoding="utf-8", newline="\n") as fh:
        for r in records:
            fh.write(json.dumps(r, ensure_ascii=False, sort_keys=True) + "\n")
    sp = os.path.join(out_dir, "%s_pool_stats.json" % pack)
    with open(sp, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(summarise(records, stats), fh, indent=1, ensure_ascii=False, sort_keys=True)
        fh.write("\n")
    return pool, units, sp


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--pack", required=True, help="pack id, part of the target seed (godot, dotnet-runtime, odoo)")
    ap.add_argument("--language", required=True, choices=C.ALL_LANGS)
    ap.add_argument("--corpus", required=True, help="folder with corpus/<language>/*.md and corpus_index.tsv")
    ap.add_argument("--ontology", required=True, help="ontology JSON of the pack")
    ap.add_argument("--core", required=True, help="core_rules.json of the pack")
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--lib", default=None, help="tree-sitter shared library (see tsbind.find_library)")
    ap.add_argument("--limit-files", type=int, default=None, help="only the first N files (for a quick check)")
    a = ap.parse_args(argv)

    import core_table
    from tsbind import TreeSitter, find_library
    onto = R.Ontology(a.ontology)
    problems = core_table.apply(a.core, onto)
    if not any(k[0] == a.language for k in R.CORE):
        problems.append("language %s has no entry in %s" % (a.language, a.core))
    if problems:
        print("CORE rule table inconsistent with ontology:\n  " + "\n  ".join(problems), file=sys.stderr)
        return 2
    ts = TreeSitter(find_library(a.lib))
    records, stats = build(a.pack, a.language, a.corpus, onto, ts, a.limit_files,
                           lambda s: print(s, flush=True))
    pool, units, sp = write_outputs(a.out_dir, a.pack, records, stats)
    print("pool %d units from %d files; wrote %s, %s, %s" % (len(records), len({r["path"] for r in records}),
                                                              pool, units, sp))
    if stats["index_mismatch"]:
        print("WARNING: blob mismatch vs corpus_index.tsv:", stats["index_mismatch"][:5])
    return 0


if __name__ == "__main__":
    sys.exit(main())
