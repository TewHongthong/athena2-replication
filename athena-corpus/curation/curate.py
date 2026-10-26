#!/usr/bin/env python3
"""Athena Task C - curate the raw corpus into benchmark snippets + injected violations.

Input : athena-corpus/corpus/<language>/*.md   (792 files, exact source bytes inside a code fence)
Output: <out>/snippets/<language>/<id>.json
        <out>/violations/<language>/<snippet_id>__<identifier>__<rule_id>.json
        <out>/snippets_index.tsv, <out>/violations_index.tsv, <out>/curation_stats.json
Formats follow benchmark_schema.md (Task C). Nothing here calls an LLM; every step is deterministic.

Pipeline per file:  parse (ast / tree-sitter)  ->  candidate units (function / method / small class)
  ->  gate: every checked identifier of the unit must satisfy the ontology's core NamingRules
            (output_validator.check_naming_compliance)  ->  pick up to 6 target identifiers
  ->  inject one violation per (identifier, core rule) with the project's own candidate order
      (violation_injector), rename all occurrences token-by-token, and re-parse the whole file to
      prove the rename changed nothing but identifier text  ->  greedy selection (kind diversity,
      repo balance)  ->  write JSON.

Usage:
  python curate.py --corpus <athena-corpus> --out <athena-corpus>/benchmark --per-language 100
"""
from __future__ import annotations

import argparse
import collections
import hashlib
import json
import os
import re
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import lang_python  # noqa: E402
import lang_ts  # noqa: E402
import rules as R  # noqa: E402
from facts import (DECL, KEY, MEMBER, REF, SHORTHAND, TYPE, dedent_lines, line_starts_of)  # noqa: E402
from output_validator import check_naming_compliance  # noqa: E402

LANGS = ["python", "java", "javascript", "typescript", "csharp"]
ID_PREFIX = {"python": "py", "java": "java", "csharp": "csharp", "typescript": "ts", "javascript": "js", "cpp": "cpp"}
ALL_LANGS = LANGS + ["cpp"]   # LANGS stays the Vol. 1 default; cpp is Vol. 2 and needs --core
MIN_LINES, MAX_LINES = 6, 40
MAX_TARGETS = 6
MIN_TARGET_LEN = 3
KIND_ORDER = ["class", "interface", "enum", "function", "method", "property", "field", "constant", "enum_member",
              "boolean_variable", "variable", "parameter"]
PIPELINE_VERSION = "athena-curation-1.0"


# --------------------------------------------------------------------------- corpus reading

def parse_corpus_md(path):
    data = open(path, "rb").read()
    pos, opener = 0, None
    for line in data.split(b"\n"):
        if line.startswith(b"```"):
            opener = line
            break
        pos += len(line) + 1
    meta = {}
    for s in data[:pos].decode("utf-8", errors="replace").split("\n"):
        s = s.rstrip("\r")
        if s.startswith("- ") and ": " in s:
            k, v = s[2:].split(": ", 1)
            meta[k.strip()] = v.strip()
    content = None
    if opener is not None:
        closer = b"`" * (len(opener) - len(opener.lstrip(b"`"))) + b"\n"
        if data.endswith(closer):
            content = data[pos + len(opener) + 1: len(data) - len(closer)]
    return meta, content


def blob12(content: bytes) -> str:
    return hashlib.sha1(b"blob %d\0" % len(content) + content).hexdigest()[:12]


def load_index(corpus_root):
    idx = {}
    p = os.path.join(corpus_root, "corpus_index.tsv")
    if os.path.exists(p):
        with open(p, encoding="utf-8") as f:
            header = f.readline().rstrip("\n").split("\t")
            for line in f:
                row = dict(zip(header, line.rstrip("\n").split("\t")))
                idx[(row["language"], row["md_file"])] = row
    return idx


# --------------------------------------------------------------------------- analysis helpers

def analyze(lang, path, content, ts):
    if lang == "python":
        return lang_python.extract(content)
    return lang_ts.extract(lang, path, content, ts)


def unit_range(ff, u):
    ls = ff.line_starts
    start = ls[u.start_line]
    end = ls[u.end_line + 1] - 1 if u.end_line + 1 < len(ls) else len(ff.src)
    return start, end


def unit_text(src: bytes, line_starts, start_line, end_line) -> str:
    start = line_starts[start_line]
    end = line_starts[end_line + 1] - 1 if end_line + 1 < len(line_starts) else len(src)
    text = src[start:end].decode("utf-8", errors="replace").replace("\r\n", "\n").replace("\r", "\n")
    lines = dedent_lines(text.split("\n"))
    while lines and not lines[-1].strip():
        lines.pop()
    return "\n".join(lines)


def _word_re(name):
    return re.compile(r"(?<![A-Za-z0-9_$])" + re.escape(name) + r"(?![A-Za-z0-9_$])")


def plan_rename(lang, ff, decls, toks, target):
    """Token spans to rewrite when `target` is renamed, or (None, reason)."""
    old = target.name
    same = [t for t in toks if t.text == old]
    if any(t.role == SHORTHAND for t in same):
        return None, "shorthand_property"
    if lang in ("typescript", "javascript") and target.ns == "member" and any(t.role == KEY for t in same):
        return None, "object_key_conflict"
    if len({d.ns for d in decls if d.name == old}) > 1:
        return None, "name_in_multiple_namespaces"
    dmap = {d.start: d for d in decls}
    spans = []
    for t in same:
        if t.role == DECL:
            d = dmap.get(t.start)
            if d is not None and d.ns == target.ns:
                spans.append(t)
        elif target.ns == "local" and t.role == REF:
            spans.append(t)
        elif target.ns == "member" and t.role in (MEMBER, REF):
            spans.append(t)
        elif target.ns == "type" and t.role in (TYPE, REF):
            spans.append(t)
    if not any(t.start == target.start for t in spans):
        return None, "declaration_token_not_found"
    if lang == "cpp":
        # C5: tree-sitter-cpp misparses some expressions (`a < b` as a template, `sizeof(T)`, macro arguments), so a
        # same-named token whose role we did not claim may still denote the target -> refuse instead of half-renaming
        claimed = {t.start for t in spans}
        for t in same:
            if t.start not in claimed and t.role != DECL:
                return None, "unclaimed_token:%s" % t.role
    return spans, None


def code_like(name: str) -> bool:
    """Multi-word identifier (snake_case / camelCase / PascalCase multiword / UPPER_SNAKE): when it appears
    in a comment it is a reference to the identifier, not an ordinary English word."""
    core = name.strip("_")
    return "_" in core or bool(re.search(r"[a-z0-9][A-Z]", core))


def text_coupling(ff, u_start, u_end, name):
    """Returns (reject_reason | None, comment_spans_to_rewrite).

    * Python f-string expressions cannot be renamed token-wise -> reject the target if the name is used there.
    * A code-like name inside a (non-f) string literal is probably a key / reflection reference -> reject.
    * A code-like name inside comments / docstrings is rewritten together with the code (like an IDE rename),
      so the original name does not leak through the comment.
    * Single-word names are ordinary English words in prose; comments and strings are left untouched.
    """
    for a, b, names in ff.fstring_refs:
        if a < u_end and b > u_start and name in names:
            return "name_in_fstring_expression", []
    if not code_like(name):
        return None, []
    rx = _word_re(name)
    for a, b in ff.string_spans:
        if a < u_end and b > u_start and rx.search(ff.src[max(a, u_start):min(b, u_end)].decode("utf-8", errors="replace")):
            return "code_like_name_in_string", []
    edits = []
    for a, b in ff.comment_spans:
        lo, hi = max(a, u_start), min(b, u_end)
        if lo >= hi:
            continue
        seg = ff.src[lo:hi].decode("utf-8", errors="replace")
        for m in rx.finditer(seg):
            pre = len(seg[:m.start()].encode("utf-8"))
            edits.append((lo + pre, lo + pre + len(name.encode("utf-8"))))
    return None, edits


def apply_edits(src: bytes, edits, new: str) -> bytes:
    nb = new.encode("utf-8")
    out, last = [], 0
    for a, b in sorted(edits):
        out.append(src[last:a])
        out.append(nb)
        last = b
    out.append(src[last:])
    return b"".join(out)


# --------------------------------------------------------------------------- unit evaluation

def evaluate_unit(lang, ff, u, onto, meta, stats):
    st = stats["units"]
    nlines = u.end_line - u.start_line + 1
    if nlines < MIN_LINES:
        st["too_short"] += 1
        return None
    if nlines > MAX_LINES:
        st["too_long"] += 1
        return None
    u_start, u_end = unit_range(ff, u)
    if any(a < u_end and b > u_start for a, b in ff.error_spans):
        st["parse_error_in_unit"] += 1
        return None
    decls = [d for d in ff.decls if u_start <= d.start < u_end]
    toks = [t for t in ff.toks if u_start <= t.start < u_end]
    # ---- gate: all checked identifiers must be compliant
    for d in decls:
        if d.exempt or (lang, d.kind) not in R.CORE:
            continue
        f = R.gate(lang, d, onto)
        if f:
            st["noncompliant_identifier"] += 1
            stats["unit_gate_failures_by_rule"][f[0][0]] += 1
            return None
    # ---- eligible targets
    eligible, seen = [], set()
    for d in sorted(decls, key=lambda x: x.start):
        if d.exempt or (lang, d.kind) not in R.CORE or d.name in seen:
            continue
        if R.name_for_check(lang, d) != d.name or len(d.name) < MIN_TARGET_LEN:
            continue
        seen.add(d.name)
        spans, why = plan_rename(lang, ff, decls, toks, d)
        if spans is None:
            stats["target_rejects"][why] += 1
            continue
        why, comment_edits = text_coupling(ff, u_start, u_end, d.name)
        if why:
            stats["target_rejects"][why] += 1
            continue
        eligible.append((d, spans, comment_edits))
    if len(eligible) < 2:
        st["fewer_than_2_eligible_targets"] += 1
        return None
    # diversity-first order: one of each kind first, then the rest by position
    first, rest, kinds_seen = [], [], set()
    for item in sorted(eligible, key=lambda x: (KIND_ORDER.index(x[0].kind) if x[0].kind in KIND_ORDER else 99, x[0].start)):
        if item[0].kind not in kinds_seen:
            kinds_seen.add(item[0].kind)
            first.append(item)
        else:
            rest.append(item)
    ordered = first + sorted(rest, key=lambda x: x[0].start)
    unit_names = {t.text for t in toks}
    base_text = unit_text(ff.src, ff.line_starts, u.start_line, u.end_line)
    targets = []
    for d, spans, comment_edits in ordered:
        if len(targets) >= MAX_TARGETS:
            break
        viols = []
        for rid in R.target_rule_ids(lang, d):
            rule = onto.rule(rid)
            ok0, _ = check_naming_compliance(R.name_for_check(lang, d), rule)
            if not ok0:
                continue
            for method, cand in R.iter_candidates(d.name, rule):
                if (cand == d.name or not R.is_valid_new_name(lang, cand) or cand in unit_names
                        or _word_re(cand).search(base_text)):
                    continue
                ok, reasons = check_naming_compliance(cand, rule)
                if ok:
                    continue
                new_src = apply_edits(ff.src, [(t.start, t.end) for t in spans] + comment_edits, cand)
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
                new_ls = line_starts_of(new_src)
                viols.append({
                    "rule": rid, "method": method, "injected": cand, "reasons": reasons,
                    "code": unit_text(new_src, new_ls, u.start_line, u.end_line),
                    "occurrences": len(spans),
                    "comment_occurrences": len(comment_edits),
                })
                stats["rename_verify"]["ok"] += 1
                break
        if viols:
            targets.append({"decl": d, "viols": viols})
        else:
            stats["target_rejects"]["no_verified_violation"] += 1
    if len(targets) < 2:
        st["fewer_than_2_targets_with_violation"] += 1
        return None
    return {"lang": lang, "unit": u, "code": base_text, "targets": targets, "meta": meta}


# --------------------------------------------------------------------------- selection

def select(cands, quota, stats, lang):
    """Greedy: prefer candidates that add rare identifier kinds; cap per repo; <=2 non-overlapping per file.
    If the quota is not met, the caps are relaxed in tiers (recorded in stats)."""
    if not cands:
        return []
    repos = sorted({c["repo"] for c in cands})
    base_cap = max(3, int(-(-1.6 * quota // len(repos))))
    tiers = [(base_cap, 2), (base_cap * 2, 2), (10 ** 6, 3)]
    chosen, kind_count, repo_count = [], collections.Counter(), collections.Counter()
    per_file = collections.defaultdict(list)
    seen_code = set()
    remaining = sorted(cands, key=lambda c: (c["repo"], c["path"], c["unit"].start_line))
    tier_used = 0
    for ti, (cap, file_cap) in enumerate(tiers):
        if len(chosen) >= quota:
            break
        tier_used = ti
        while remaining and len(chosen) < quota:
            best, best_score = None, -1e9
            for c in remaining:
                if repo_count[c["repo"]] >= cap:
                    continue
                fl = per_file[c["file"]]
                if len(fl) >= file_cap or any(not (c["unit"].end_line < a or c["unit"].start_line > b) for a, b in fl):
                    continue
                kinds = {t["decl"].kind for t in c["targets"]}
                score = sum(1.0 / (1 + kind_count[k]) for k in kinds) + 0.25 * min(len(c["targets"]), MAX_TARGETS) / MAX_TARGETS
                score -= 0.5 * repo_count[c["repo"]] / min(cap, 1000)
                score -= 0.4 * len(fl)
                if score > best_score:
                    best, best_score = c, score
            if best is None:
                break
            remaining.remove(best)
            key = re.sub(r"\s+", " ", best["code"])
            if key in seen_code:
                stats["units"]["duplicate_code_dropped"] += 1
                continue
            seen_code.add(key)
            chosen.append(best)
            repo_count[best["repo"]] += 1
            per_file[best["file"]].append((best["unit"].start_line, best["unit"].end_line))
            for t in best["targets"]:
                kind_count[t["decl"].kind] += 1
    stats.setdefault("selection_tier", {})[lang] = {"tier": tier_used, "base_repo_cap": base_cap,
                                                     "repos_with_candidates": len(repos)}
    return chosen


# --------------------------------------------------------------------------- output

def _safe(name):
    return re.sub(r"[^A-Za-z0-9_]", "_", name)


def write_outputs(chosen_by_lang, onto, out_dir, corpus_meta, langs=None):
    snippets_rows, viol_rows = [], []
    for lang in (langs or LANGS):
        chosen = sorted(chosen_by_lang.get(lang, []), key=lambda c: (c["repo"], c["path"], c["unit"].start_line))
        sdir = os.path.join(out_dir, "snippets", lang)
        vdir = os.path.join(out_dir, "violations", lang)
        os.makedirs(sdir, exist_ok=True)
        os.makedirs(vdir, exist_ok=True)
        for i, c in enumerate(chosen, 1):
            sid = f"{ID_PREFIX[lang]}_{i:03d}"
            m = c["meta"]
            snippet = {
                "id": sid,
                "language": lang,
                "source": f"github:{m['source repo']}@{m['commit']}",
                "sourceDetail": (f"{m['file path']} lines {c['unit'].start_line + 1}-{c['unit'].end_line + 1} "
                                 f"({c['unit'].label}); license {m['license']}; repo created {m['created_at']}; "
                                 f"curated by {PIPELINE_VERSION}"),
                "standardId": onto.default_standard[lang],
                "codeContext": c["code"],
                "identifiers": [{"name": t["decl"].name, "kind": t["decl"].kind, "isCompliant": True}
                                for t in c["targets"]],
                "provenance": {
                    "repo": m["source repo"], "repoUrl": m.get("repo url"), "license": m["license"],
                    "repoCreatedAt": m["created_at"], "commit": m["commit"], "path": m["file path"],
                    "startLine": c["unit"].start_line + 1, "endLine": c["unit"].end_line + 1,
                    "unit": c["unit"].label, "corpusFile": f"corpus/{lang}/{c['file']}",
                },
            }
            with open(os.path.join(sdir, sid + ".json"), "w", encoding="utf-8", newline="\n") as f:
                json.dump(snippet, f, indent=2, ensure_ascii=False)
                f.write("\n")
            snippets_rows.append([sid, lang, snippet["standardId"], m["source repo"], m["file path"],
                                  c["unit"].start_line + 1, c["unit"].end_line + 1, c["unit"].label,
                                  len(c["targets"]), ",".join(sorted({t['decl'].kind for t in c['targets']})),
                                  sum(len(t["viols"]) for t in c["targets"])])
            for t in c["targets"]:
                d = t["decl"]
                for v in t["viols"]:
                    vio = {
                        "snippetId": sid,
                        "language": lang,
                        "originalName": d.name,
                        "injectedName": v["injected"],
                        "identifierKind": d.kind,
                        "violatedRuleId": v["rule"],
                        "injectionMethod": v["method"],
                        "expectedViolationReasons": v["reasons"],
                        "codeContextWithViolation": v["code"],
                        "occurrencesRenamed": v["occurrences"],
                        "commentOccurrencesRenamed": v["comment_occurrences"],
                    }
                    if v["rule"] in R.RULE_CAVEATS:
                        vio["ruleCaveat"] = R.RULE_CAVEATS[v["rule"]]
                    fn = f"{sid}__{_safe(d.name)}__{v['rule']}.json"
                    with open(os.path.join(vdir, fn), "w", encoding="utf-8", newline="\n") as f:
                        json.dump(vio, f, indent=2, ensure_ascii=False)
                        f.write("\n")
                    viol_rows.append([sid, lang, d.name, d.kind, v["rule"], v["method"], v["injected"], fn])
    with open(os.path.join(out_dir, "snippets_index.tsv"), "w", encoding="utf-8", newline="\n") as f:
        f.write("\t".join(["snippet_id", "language", "standard_id", "repo", "path", "start_line", "end_line", "unit",
                           "n_targets", "target_kinds", "n_violations"]) + "\n")
        for r in snippets_rows:
            f.write("\t".join(str(x) for x in r) + "\n")
    with open(os.path.join(out_dir, "violations_index.tsv"), "w", encoding="utf-8", newline="\n") as f:
        f.write("\t".join(["snippet_id", "language", "original_name", "kind", "rule_id", "method", "injected_name",
                           "file"]) + "\n")
        for r in viol_rows:
            f.write("\t".join(str(x) for x in r) + "\n")
    return len(snippets_rows), len(viol_rows)


# --------------------------------------------------------------------------- main

def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--corpus", required=True, help="athena-corpus folder (contains corpus/ and corpus_index.tsv)")
    ap.add_argument("--out", required=True, help="output folder for snippets/ and violations/")
    ap.add_argument("--ontology", default=R.DEFAULT_ONTOLOGY)
    ap.add_argument("--lib", default=None, help="tree-sitter shared library (see tsbind.find_library)")
    ap.add_argument("--per-language", type=int, default=100)
    ap.add_argument("--languages", default=",".join(LANGS), help="comma list from " + ",".join(ALL_LANGS))
    ap.add_argument("--core", default=None, help="per-pack core_rules.json (core_table.py); replaces the Vol. 1 "
                    "CORE table. Required for cpp")
    ap.add_argument("--stats", default=None, help="write full statistics JSON here (default <out>/curation_stats.json)")
    args = ap.parse_args()

    from tsbind import TreeSitter, find_library
    t0 = time.time()
    onto = R.Ontology(args.ontology)
    langs = args.languages.split(",")
    bad = [l for l in langs if l not in ALL_LANGS]
    if bad:
        sys.exit(f"unknown language(s) {bad}; choose from {ALL_LANGS}")
    if "cpp" in langs and not args.core:
        sys.exit("cpp has no built-in CORE table: pass --core <core_rules.json>")
    if args.core:
        import core_table
        problems = core_table.apply(args.core, onto)
        missing = [l for l in langs if not any(k[0] == l for k in R.CORE)]
        problems += [f"language {l} has no entry in {args.core}" for l in missing]
    else:
        problems = onto.validate_core()
    if problems:
        sys.exit("CORE rule table inconsistent with ontology:\n  " + "\n  ".join(problems))
    ts = TreeSitter(find_library(args.lib))
    index = load_index(args.corpus)

    stats = {"pipeline": PIPELINE_VERSION, "ontology_sha256": onto.sha256, "ontology_nodes": onto.n_nodes,
             "ontology_links": onto.n_links, "per_language_quota": args.per_language,
             "files": collections.Counter(), "skipped_files": collections.defaultdict(list),
             "index_mismatch": [], "units": collections.Counter(), "unit_gate_failures_by_rule": collections.Counter(),
             "target_rejects": collections.Counter(), "rename_verify": collections.Counter(),
             "decl_compliance": collections.defaultdict(lambda: collections.Counter()),
             "decl_counts": collections.defaultdict(lambda: collections.Counter()),
             "exempt_counts": collections.defaultdict(lambda: collections.Counter()),
             "candidates": {}, "selected": {}, "parity": collections.Counter()}

    chosen_by_lang = {}
    for lang in langs:
        ldir = os.path.join(args.corpus, "corpus", lang)
        cands = []
        nfiles = 0
        for name in sorted(os.listdir(ldir)):
            if not name.endswith(".md"):
                continue
            nfiles += 1
            meta, content = parse_corpus_md(os.path.join(ldir, name))
            row = index.get((lang, name))
            if content is None:
                stats["skipped_files"][lang].append((name, "no code block"))
                continue
            if row and row.get("git_blob_sha1_12") and blob12(content) != row["git_blob_sha1_12"]:
                stats["index_mismatch"].append(f"{lang}/{name}")
            ff = analyze(lang, meta["file path"], content, ts)
            if not ff.parse_ok:
                stats["skipped_files"][lang].append((name, ff.skip_reason))
                continue
            stats["files"][lang] += 1
            # file-level compliance census (all non-exempt checked declarations)
            for d in ff.decls:
                stats["decl_counts"][lang][d.kind] += 1
                if d.exempt:
                    stats["exempt_counts"][lang][d.exempt] += 1
                    continue
                if (lang, d.kind) not in R.CORE:
                    continue
                for rid in R.rules_for_check(lang, d):
                    ok, _ = check_naming_compliance(R.name_for_check(lang, d), onto.rule(rid))
                    stats["decl_compliance"][lang][f"{rid}|checked"] += 1
                    if not ok:
                        stats["decl_compliance"][lang][f"{rid}|failed"] += 1
            for u in ff.units:
                stats["units"]["total"] += 1
                ev = evaluate_unit(lang, ff, u, onto, meta, stats)
                if ev is None:
                    continue
                ev["repo"] = meta["source repo"]
                ev["path"] = meta["file path"]
                ev["file"] = name
                cands.append(ev)
        stats["candidates"][lang] = {"files": nfiles, "clean_candidate_units": len(cands),
                                     "repos_with_candidates": len({c["repo"] for c in cands}),
                                     "files_with_candidates": len({c["file"] for c in cands})}
        chosen = select(cands, args.per_language, stats, lang)
        chosen_by_lang[lang] = chosen
        kc, rc = collections.Counter(), collections.Counter()
        for c in chosen:
            rc[c["repo"]] += 1
            for t in c["targets"]:
                kc[t["decl"].kind] += 1
        stats["selected"][lang] = {"snippets": len(chosen), "identifiers_by_kind": dict(kc),
                                   "snippets_by_repo": dict(rc),
                                   "violations": sum(len(t["viols"]) for c in chosen for t in c["targets"])}
        print(f"[{lang}] files={nfiles} clean_units={len(cands)} selected={len(chosen)} "
              f"({time.time() - t0:.0f}s)", flush=True)

    os.makedirs(args.out, exist_ok=True)
    out_langs = langs if args.core else LANGS + [l for l in langs if l not in LANGS]
    ns, nv = write_outputs(chosen_by_lang, onto, args.out, None, out_langs)
    print(f"wrote {ns} snippets, {nv} violation files to {args.out}")

    def plain(o):
        if isinstance(o, collections.defaultdict) or isinstance(o, dict):
            return {k: plain(v) for k, v in o.items()}
        if isinstance(o, collections.Counter):
            return dict(o)
        return o
    sp = args.stats or os.path.join(args.out, "curation_stats.json")
    with open(sp, "w", encoding="utf-8") as f:
        json.dump(plain(stats), f, indent=1, ensure_ascii=False, default=str)
    if stats["index_mismatch"]:
        print("WARNING: blob mismatch vs corpus_index.tsv:", stats["index_mismatch"][:5])


if __name__ == "__main__":
    main()
