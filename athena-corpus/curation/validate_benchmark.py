#!/usr/bin/env python3
"""Independent validator for the curated benchmark (standard library + the project's output_validator).

It does NOT use the parsers: it re-checks every promise the curation makes by other means.

  snippets   schema; standardId; kinds known to the ontology; every listed identifier occurs in the code
             and satisfies ALL core rules of its (language, kind); provenance consistent; codeContext is an
             exact (dedented) excerpt of the pinned source bytes in corpus/<lang>/<file>.md
  violations schema; parent snippet + identifier exist; rule is retrievable for (language, kind) AND core;
             original name passes / injected name fails the rule with the recorded reasons;
             the two code contexts differ ONLY by original->injected identifier text
             (count == occurrencesRenamed + commentOccurrencesRenamed); injectionMethod reproduces
  indexes    TSV rows match the files on disk

Usage: python validate_benchmark.py --benchmark <dir> --corpus <athena-corpus dir> [--graph-crosscheck]
Exit status 1 if any error.
"""
from __future__ import annotations

import argparse
import collections
import glob
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import rules as R  # noqa: E402
from facts import dedent_lines  # noqa: E402
from output_validator import check_naming_compliance  # noqa: E402

LANGS = ["python", "java", "javascript", "typescript", "csharp"]
SNIPPET_KEYS = {"id", "language", "source", "sourceDetail", "standardId", "codeContext", "identifiers"}
VIOLATION_KEYS = {"snippetId", "language", "originalName", "injectedName", "identifierKind", "violatedRuleId",
                  "injectionMethod", "expectedViolationReasons", "codeContextWithViolation"}
TOKEN = re.compile(r"[A-Za-z_$][A-Za-z0-9_$]*|\s+|.", re.S)
ID_PREFIX = {"python": "py", "java": "java", "csharp": "csharp", "typescript": "ts", "javascript": "js", "cpp": "cpp"}


def word_in(name, text):
    return re.search(r"(?<![A-Za-z0-9_$])" + re.escape(name) + r"(?![A-Za-z0-9_$])", text) is not None


def read_corpus_content(corpus_root, lang, corpus_file):
    p = os.path.join(corpus_root, corpus_file)
    data = open(p, "rb").read()
    pos, opener = 0, None
    for line in data.split(b"\n"):
        if line.startswith(b"```"):
            opener = line
            break
        pos += len(line) + 1
    closer = b"`" * (len(opener) - len(opener.lstrip(b"`"))) + b"\n"
    assert data.endswith(closer)
    return data[pos + len(opener) + 1: len(data) - len(closer)]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--benchmark", required=True)
    ap.add_argument("--corpus", default=None)
    ap.add_argument("--ontology", default=R.DEFAULT_ONTOLOGY)
    ap.add_argument("--graph-crosscheck", action="store_true")
    ap.add_argument("--languages", default=",".join(LANGS))
    ap.add_argument("--core", default=None, help="core_rules.json of a Vol. 2 pack (replaces the Vol. 1 CORE table)")
    args = ap.parse_args()
    LANGS[:] = args.languages.split(",")

    onto = R.Ontology(args.ontology)
    errors = []

    def err(msg):
        errors.append(msg)

    if args.core:
        import core_table
        core_problems = core_table.apply(args.core, onto)
    else:
        core_problems = onto.validate_core()
    for p in core_problems:
        err("CORE table: " + p)

    if args.graph_crosscheck:
        sys.path.insert(0, os.path.join(HERE, "pipeline"))
        import graph_loader
        bad = onto.crosscheck_with_graph_loader(graph_loader)
        for b in bad[:10]:
            err(f"applicable() differs from graph_loader.get_applicable_rules: {b}")
        print(f"graph_loader cross-check over {len(onto.languages) * len(onto.kinds)} (language, kind) pairs: "
              f"{'OK' if not bad else str(len(bad)) + ' MISMATCHES'}")

    snippets = {}
    counts = collections.Counter()
    for lang in LANGS:
        for p in sorted(glob.glob(os.path.join(args.benchmark, "snippets", lang, "*.json"))):
            s = json.load(open(p, encoding="utf-8"))
            sid = s.get("id", "?")
            missing = SNIPPET_KEYS - set(s)
            if missing:
                err(f"{sid}: missing keys {sorted(missing)}")
                continue
            if os.path.basename(p) != sid + ".json":
                err(f"{sid}: file name mismatch {os.path.basename(p)}")
            if s["language"] != lang:
                err(f"{sid}: language {s['language']} in folder {lang}")
            if not re.fullmatch(ID_PREFIX[lang] + r"_\d{3}", sid):
                err(f"{sid}: unexpected id format")
            if sid in snippets:
                err(f"{sid}: duplicate id")
            snippets[sid] = s
            counts[("snippets", lang)] += 1
            if s["standardId"] != onto.default_standard[lang]:
                err(f"{sid}: standardId {s['standardId']} != ontology default {onto.default_standard[lang]}")
            code = s["codeContext"]
            if code != code.strip("\n") or "\r" in code:
                err(f"{sid}: codeContext has leading/trailing newlines or CR")
            if not s["identifiers"]:
                err(f"{sid}: no identifiers")
            seen = set()
            for ident in s["identifiers"]:
                name, kind = ident["name"], ident["kind"]
                if ident.get("isCompliant") is not True:
                    err(f"{sid}: {name} isCompliant != true")
                if name in seen:
                    err(f"{sid}: identifier {name} listed twice")
                seen.add(name)
                if kind not in onto.kinds:
                    err(f"{sid}: unknown kind {kind}")
                    continue
                if (lang, kind) not in R.CORE:
                    err(f"{sid}: ({lang},{kind}) has no core rules")
                    continue
                if not word_in(name, code):
                    err(f"{sid}: identifier {name} not found in codeContext")
                for rid in R.CORE[(lang, kind)]:
                    ok, reasons = check_naming_compliance(name, onto.rule(rid))
                    if not ok:
                        err(f"{sid}: {name} violates core rule {rid}: {reasons}")
                counts[("identifiers", lang, kind)] += 1
            prov = s.get("provenance", {})
            if prov:
                if s["source"] != f"github:{prov['repo']}@{prov['commit']}":
                    err(f"{sid}: source != provenance")
                if not (1 <= prov["startLine"] <= prov["endLine"]):
                    err(f"{sid}: bad line range")
                if args.corpus:
                    try:
                        content = read_corpus_content(args.corpus, lang, prov["corpusFile"])
                        lines = content.decode("utf-8", errors="replace").replace("\r\n", "\n").replace("\r", "\n").split("\n")
                        seg = dedent_lines(lines[prov["startLine"] - 1: prov["endLine"]])
                        while seg and not seg[-1].strip():
                            seg.pop()
                        if "\n".join(seg) != code:
                            err(f"{sid}: codeContext is not an exact excerpt of {prov['corpusFile']} lines "
                                f"{prov['startLine']}-{prov['endLine']}")
                    except Exception as e:  # noqa: BLE001
                        err(f"{sid}: cannot verify excerpt: {e}")

    nviol = 0
    for lang in LANGS:
        for p in sorted(glob.glob(os.path.join(args.benchmark, "violations", lang, "*.json"))):
            v = json.load(open(p, encoding="utf-8"))
            nviol += 1
            fn = os.path.basename(p)
            missing = VIOLATION_KEYS - set(v)
            if missing:
                err(f"{fn}: missing keys {sorted(missing)}")
                continue
            sid = v["snippetId"]
            s = snippets.get(sid)
            if s is None:
                err(f"{fn}: parent snippet {sid} not found")
                continue
            if v["language"] != lang or s["language"] != lang:
                err(f"{fn}: language mismatch")
            expect_fn = f"{sid}__{re.sub(r'[^A-Za-z0-9_]', '_', v['originalName'])}__{v['violatedRuleId']}.json"
            if fn != expect_fn:
                err(f"{fn}: expected file name {expect_fn}")
            ident = next((i for i in s["identifiers"] if i["name"] == v["originalName"]), None)
            if ident is None or ident["kind"] != v["identifierKind"]:
                err(f"{fn}: originalName/kind not among the snippet's identifiers")
                continue
            kind, rid = v["identifierKind"], v["violatedRuleId"]
            if rid not in onto.applicable(lang, kind):
                err(f"{fn}: {rid} is not retrievable for ({lang},{kind})")
            if rid not in R.CORE.get((lang, kind), []):
                err(f"{fn}: {rid} is not a core rule for ({lang},{kind})")
            rule = onto.rule(rid)
            ok0, _ = check_naming_compliance(v["originalName"], rule)
            if not ok0:
                err(f"{fn}: original name does not satisfy {rid}")
            ok1, reasons = check_naming_compliance(v["injectedName"], rule)
            if ok1:
                err(f"{fn}: injected name {v['injectedName']} does NOT violate {rid}")
            elif reasons != v["expectedViolationReasons"]:
                err(f"{fn}: expectedViolationReasons differ from recomputed")
            # method reproduces
            method = None
            for m, cand in R.iter_candidates(v["originalName"], rule):
                if cand == v["injectedName"]:
                    method = m
                    break
            if method != v["injectionMethod"]:
                err(f"{fn}: injectionMethod {v['injectionMethod']} not reproduced (got {method})")
            # diff exactly the identifier text
            a = TOKEN.findall(s["codeContext"])
            b = TOKEN.findall(v["codeContextWithViolation"])
            if len(a) != len(b):
                err(f"{fn}: token count differs {len(a)} vs {len(b)}")
            else:
                diff = [(x, y) for x, y in zip(a, b) if x != y]
                bad = [(x, y) for x, y in diff if not (x == v["originalName"] and y == v["injectedName"])]
                if bad:
                    err(f"{fn}: unexpected difference {bad[0]}")
                total = v.get("occurrencesRenamed", 0) + v.get("commentOccurrencesRenamed", 0)
                if not diff:
                    err(f"{fn}: contexts are identical")
                elif len(diff) != total:
                    err(f"{fn}: {len(diff)} changed tokens != occurrences recorded ({total})")
            if word_in(v["injectedName"], s["codeContext"]):
                err(f"{fn}: injected name already occurs in the original snippet")
            counts[("violations", lang)] += 1
            counts[("viol_rule", rid)] += 1
            counts[("viol_method", v["injectionMethod"])] += 1

    # indexes
    for name, expect in (("snippets_index.tsv", len(snippets)), ("violations_index.tsv", nviol)):
        p = os.path.join(args.benchmark, name)
        if os.path.exists(p):
            rows = sum(1 for _ in open(p, encoding="utf-8")) - 1
            if rows != expect:
                err(f"{name}: {rows} rows but {expect} files")
        else:
            err(f"{name} missing")

    print(f"snippets: {sum(v for k, v in counts.items() if k[0] == 'snippets')}  "
          f"violations: {nviol}  identifiers: {sum(v for k, v in counts.items() if k[0] == 'identifiers')}")
    for lang in LANGS:
        print(f"  {lang:11s} snippets={counts[('snippets', lang)]:3d} violations={counts[('violations', lang)]:4d}")
    print("violations by method:", {k[1]: v for k, v in counts.items() if k[0] == "viol_method"})
    if errors:
        print(f"\n{len(errors)} ERRORS")
        for e in errors[:25]:
            print("  -", e)
        sys.exit(1)
    print("\nVALIDATION PASSED: 0 errors")


if __name__ == "__main__":
    main()
