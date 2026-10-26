#!/usr/bin/env python3
"""Build comment-generation benchmark units (Athena Task C, RQ2) for the public5 benchmark.

Deterministic, no LLM anywhere. Reuses the same parsers curate.py uses (facts.py / lang_python.py /
lang_ts.py / tsbind.py) to find unit boundaries and declarations; comment detection, codeBare
construction, signature inference and expectedElements are new logic specific to this script.

Source unit: the main declared entity (function/method/class only) of each curated benchmark
snippet (snippets/<lang>/*.json). Reference comment is read from the PINNED corpus source file
(not the already-dedented snippet text), since for non-Python languages the doc comment sits
above the snippet's own line range. For languages with fewer than 30 qualifying snippet-derived
units, extra units are mined directly from the 792-file corpus (see top_up()).

Writes:
  athena-corpus/benchmark/comment_units/<language>/<unit_id>.json
  athena-corpus/benchmark/comment_units_index.tsv
  athena-corpus/benchmark/comment_units_stats.json   (counts, for the curation report / debugging)

Usage:
  python make_comment_units.py --corpus .. --out ../benchmark
"""
from __future__ import annotations

import argparse
import ast
import collections
import hashlib
import json
import math
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import lang_python  # noqa: E402
import lang_ts  # noqa: E402
import rules as R  # noqa: E402
import curate as CUR  # noqa: E402
from facts import line_starts_of  # noqa: E402

LANGS = ["python", "java", "javascript", "typescript", "csharp"]
MIN_LINES, MAX_LINES = 6, 40           # same bounds curate.py uses for a unit
TOPUP_MIN, TOPUP_MAX = 30, 40
MAX_PER_FILE = 2
MAX_REPO_SHARE = 0.25
PIPELINE_VERSION = "athena-comment-units-1.0"

_SURROGATE = re.compile("[\ud800-\udfff]")
_JAVA_ANNOT = re.compile(r"^\s*@[A-Za-z_][\w.]*(\s*\([^)]*\))?\s*$")
_CS_ATTR = re.compile(r"^\s*\[[^\]]*\]\s*$")
_TSJS_DECORATOR = re.compile(r"^\s*@[A-Za-z_][\w.$]*(\s*\([^)]*\))?\s*$")
_ANNOT_RE = {"java": _JAVA_ANNOT, "csharp": _CS_ATTR, "typescript": _TSJS_DECORATOR, "javascript": _TSJS_DECORATOR}

_TARGET_DECL_KINDS = {"class", "interface", "enum", "function", "method"}
_KEEP_KINDS = {"class", "function", "method"}

_CLASS_TYPES = {
    "java": {"class_declaration", "record_declaration"},
    "csharp": {"class_declaration", "struct_declaration", "record_declaration", "record_struct_declaration"},
    "typescript": {"class_declaration", "abstract_class_declaration", "class"},
    "tsx": {"class_declaration", "abstract_class_declaration", "class"},
    "javascript": {"class_declaration", "class"},
}
_FUNC_TYPES = {"function_declaration", "generator_function_declaration"}
_METHOD_TYPES = {"method_declaration", "method_definition"}

_JAVA_STOP = {"lambda_expression", "class_declaration", "interface_declaration", "enum_declaration",
             "record_declaration"}
_CS_STOP = {"lambda_expression", "anonymous_method_expression", "local_function_statement",
           "class_declaration", "struct_declaration", "record_declaration", "interface_declaration"}
_TSJS_STOP = {"arrow_function", "function_expression", "function", "generator_function",
             "method_definition", "class_declaration", "abstract_class_declaration", "class"}


def has_surrogate(s: str) -> bool:
    return bool(_SURROGATE.search(s or ""))


# --------------------------------------------------------------------------- corpus index

def load_corpus_index(corpus_root):
    """Returns (by_md[(lang, md_file)] -> row, by_repo_path[(lang, repo, path)] -> md_file)."""
    by_md, by_repo_path = {}, {}
    p = os.path.join(corpus_root, "corpus_index.tsv")
    with open(p, encoding="utf-8") as f:
        header = f.readline().rstrip("\n").split("\t")
        for line in f:
            row = dict(zip(header, line.rstrip("\n").split("\t")))
            by_md[(row["language"], row["md_file"])] = row
            by_repo_path[(row["language"], row["repo"], row["source_path"])] = row["md_file"]
    return by_md, by_repo_path


# --------------------------------------------------------------------------- comment detection

def extract_plain(text: str, lang: str) -> str:
    if lang == "csharp":
        return "\n".join(re.sub(r"^\s*///\s?", "", ln) for ln in text.split("\n"))
    body = text.strip()
    if body.startswith("/**"):
        body = body[3:]
    elif body.startswith("/*"):
        body = body[2:]
    if body.endswith("*/"):
        body = body[:-2]
    return re.sub(r"(?m)^[ \t]*\*[ \t]?", "", body)


def _content_reject(text: str, plain: str):
    low = text.lower()
    if "copyright" in low or "license" in low or "spdx-license" in low:
        return "license_header"
    words = plain.split()
    if len(words) < 3 or len(plain.strip()) < 20:
        return "comment_too_short"
    if has_surrogate(text):
        return "non_utf8_comment"
    return None


def leading_comment(lines: list, start_idx: int, lang: str):
    """Scan upward from `start_idx` (0-based, first line of the unit) in the pinned file's raw
    lines for a doc comment (java/ts/js: /** ... */; csharp: contiguous ///), skipping blank
    lines and annotations/attributes/decorators. Returns (text_or_None, reject_reason_or_None)."""
    annot_re = _ANNOT_RE[lang]
    i = start_idx - 1
    while i >= 0 and (not lines[i].strip() or annot_re.match(lines[i])):
        i -= 1
    if i < 0:
        return None, "no_comment_found"
    if lang == "csharp":
        if not lines[i].lstrip().startswith("///"):
            return None, "no_comment_found"
        j = i
        while j >= 0 and lines[j].lstrip().startswith("///"):
            j -= 1
        text = "\n".join(lines[j + 1: i + 1])
    else:
        ls_i = lines[i].lstrip()
        if ls_i.startswith("//"):
            return None, "ordinary_comment"
        if not lines[i].rstrip().endswith("*/"):
            return None, "no_comment_found"
        j, is_doc = i, None
        while j >= 0:
            ls = lines[j].lstrip()
            if ls.startswith("/**"):
                is_doc = True
                break
            if ls.startswith("/*"):
                is_doc = False
                break
            j -= 1
        if is_doc is None:
            return None, "no_comment_found"
        if not is_doc:
            return None, "ordinary_comment"
        text = "\n".join(lines[j: i + 1])
    reason = _content_reject(text, extract_plain(text, lang))
    if reason:
        return None, reason
    return text, None


def python_docstring(code_text: str):
    """code_text: a standalone function/class def (the unit's own codeContext)."""
    try:
        tree = ast.parse(code_text)
    except SyntaxError:
        return None, "parse_error"
    if not tree.body or not isinstance(tree.body[0], (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
        return None, "parse_error"
    node = tree.body[0]
    if not node.body or not (isinstance(node.body[0], ast.Expr) and isinstance(node.body[0].value, ast.Constant)
                              and isinstance(node.body[0].value.value, str)):
        return None, "no_comment_found"
    doc_node = node.body[0]
    text = ast.get_source_segment(code_text, doc_node)
    if text is None:
        return None, "parse_error"
    reason = _content_reject(text, doc_node.value.value)
    if reason:
        return None, reason
    if len(node.body) == 1:
        return None, "empty_body_after_removal"
    return text, None


# --------------------------------------------------------------------------- signature inference

def _shallow(node, stop_types, target_types):
    def rec(n, top):
        if not top and n.type in stop_types:
            return False
        if n.type in target_types and (n.type != "return_statement" or n.named_children()):
            return True
        return any(rec(c, False) for c in n.children)
    return rec(node, True)


def python_signature(node, kind):
    args = node.args
    allp = list(args.posonlyargs) + list(args.args) + list(args.kwonlyargs)
    if args.vararg:
        allp.append(args.vararg)
    if args.kwarg:
        allp.append(args.kwarg)
    if kind == "method" and allp and allp[0].arg in ("self", "cls", "mcs", "metacls"):
        allp = allp[1:]

    class ShallowReturn(ast.NodeVisitor):
        found = False

        def visit_FunctionDef(self, n):
            pass

        def visit_AsyncFunctionDef(self, n):
            pass

        def visit_Lambda(self, n):
            pass

        def visit_Return(self, n):
            if n.value is not None:
                self.found = True

    class ShallowRaise(ShallowReturn):
        def visit_Return(self, n):
            pass

        def visit_Raise(self, n):
            self.found = True

    rv, tv = ShallowReturn(), ShallowRaise()
    for stmt in node.body:
        rv.visit(stmt)
        tv.visit(stmt)
    return {"params": len(allp), "returns": bool(rv.found), "throws": bool(tv.found)}


def ts_grammar(lang, path_hint):
    if lang == "typescript":
        return "tsx" if (path_hint or "").lower().endswith(".tsx") else "typescript"
    return lang


def find_unit_node(root, grammar, lang, kind):
    if kind == "method":
        types = _METHOD_TYPES
    elif kind == "class":
        types = _CLASS_TYPES[grammar]
    else:
        types = _FUNC_TYPES
    for n in root.walk():
        if n.type in types:
            return n
    return None


def count_params(params_node, grammar, src):
    if params_node is None:
        return 0
    n = 0
    for c in params_node.named_children():
        if grammar in ("typescript", "tsx") and c.type in ("required_parameter", "optional_parameter"):
            pat = c.child("pattern")
            if pat is not None and pat.type == "identifier" and pat.text(src) == "this":
                continue
        n += 1
    return n


def ts_signature(language, kind, code_bare, path_hint, ts):
    wrapped = "class __W {\n" + code_bare + "\n}\n" if kind == "method" else code_bare
    grammar = ts_grammar(language, path_hint)
    src = wrapped.encode("utf-8")
    root, _ = ts.parse(grammar, src)
    node = find_unit_node(root, grammar, language, kind)
    if node is None:
        return None
    params = count_params(node.child("parameters"), grammar, src)
    body = node.child("body")
    if language == "java":
        tn = node.child("type")
        returns = tn is not None and tn.text(src).strip() != "void"
        throws = body is not None and _shallow(body, _JAVA_STOP, {"throw_statement"})
    elif language == "csharp":
        tn = node.child("returns")
        rt = tn.text(src).strip() if tn is not None else ""
        returns = rt not in ("", "void", "Task")
        throws = body is not None and _shallow(body, _CS_STOP, {"throw_statement"})
    else:
        returns = body is not None and _shallow(body, _TSJS_STOP, {"return_statement"})
        throws = body is not None and _shallow(body, _TSJS_STOP, {"throw_statement"})
    return {"params": params, "returns": bool(returns), "throws": bool(throws)}


# --------------------------------------------------------------------------- ontology

def comment_rule_ids(onto, lang, kind):
    ids = [rid for rid in onto.applicable(lang, kind, naming_only=False)
          if onto.nodes[rid]["type"] == "CommentRule"]
    rank = {"MUST": 0, "SHOULD": 1, "MAY": 2}
    return sorted(ids, key=lambda rid: (rank.get(onto.nodes[rid].get("severity"), 3), rid))


# --------------------------------------------------------------------------- record builder

def build_record(*, origin, language, standard_id, kind, name, code_text, path_hint, lines_above,
                 u_start_idx, source, source_detail, snippet_id, provenance, stats, onto, ts):
    if kind not in _KEEP_KINDS:
        stats["rejections"]["kind_excluded"] += 1
        return None
    if has_surrogate(code_text):
        stats["rejections"]["non_utf8_code"] += 1
        return None

    if language == "python":
        ref_comment, reason = python_docstring(code_text)
    else:
        ref_comment, reason = leading_comment(lines_above, u_start_idx, language)
    if reason:
        stats["rejections"][reason] += 1
        return None

    stripped_from_code = language != "python" and ref_comment in code_text
    code_bare = code_text.replace(ref_comment, "", 1) if stripped_from_code or language == "python" else code_text
    if stripped_from_code:
        stats["leading_comment_was_inside_snippet"] += 1

    if kind == "class":
        sig = {"params": 0, "returns": False, "throws": False}
    elif language == "python":
        try:
            t2 = ast.parse(code_bare)
        except SyntaxError:
            stats["rejections"]["reparse_failed"] += 1
            return None
        if not t2.body or not isinstance(t2.body[0], (ast.FunctionDef, ast.AsyncFunctionDef)) or not t2.body[0].body:
            stats["rejections"]["empty_body_after_removal"] += 1
            return None
        sig = python_signature(t2.body[0], kind)
    else:
        sig = ts_signature(language, kind, code_bare, path_hint, ts)
        if sig is None:
            stats["rejections"]["reparse_failed"] += 1
            return None

    if kind == "class":
        expected = ["summary"]
    else:
        params_key = "param" if language == "csharp" else "params"
        expected = ["summary"]
        if sig["params"] > 0:
            expected.append(params_key)
        if sig["returns"]:
            expected.append("returns")
        if sig["throws"]:
            expected.append("throws")

    return {
        "snippetId": snippet_id,
        "language": language,
        "standardId": standard_id,
        "identifierKind": kind,
        "name": name,
        "codeBare": code_bare,
        "referenceComment": ref_comment,
        "ruleIds": comment_rule_ids(onto, language, kind),
        "origin": origin,
        "source": source,
        "sourceDetail": source_detail,
        "referenceCommentLines": ref_comment.count("\n") + 1,
        "signature": sig,
        "expectedElements": expected,
        "provenance": provenance,
    }


# --------------------------------------------------------------------------- pinned-file helpers

class FileCache:
    def __init__(self, corpus_root, by_md, ts):
        self.corpus_root = corpus_root
        self.by_md = by_md
        self.ts = ts
        self._cache = {}

    def get(self, lang, md_file):
        key = (lang, md_file)
        if key not in self._cache:
            path = os.path.join(self.corpus_root, "corpus", lang, md_file)
            meta, content = CUR.parse_corpus_md(path)
            text = content.decode("utf-8", errors="surrogateescape").replace("\r\n", "\n").replace("\r", "\n")
            ff = lang_python.extract(content) if lang == "python" else lang_ts.extract(lang, meta["file path"], content, self.ts)
            ls = line_starts_of(content)
            self._cache[key] = (meta, content, text, ff, ls)
        return self._cache[key]


def resolve_kind_name(ff, ls, content, start_line0, end_line0):
    """Find the unit's own declaration (smallest-offset decl of a type/callable kind inside the
    unit's byte range) so ambiguous `unit` label words (e.g. java/typescript folding enum/record/
    abstract/generator into 'class'/'function') are resolved to the real identifierKind."""
    u_start = ls[start_line0]
    u_end = ls[end_line0 + 1] - 1 if end_line0 + 1 < len(ls) else len(content)
    cands = [d for d in ff.decls if u_start <= d.start < u_end and d.kind in _TARGET_DECL_KINDS]
    if not cands:
        return None, None
    d0 = min(cands, key=lambda d: d.start)
    return d0.kind, d0.name


# --------------------------------------------------------------------------- pass 1: snippet-derived units

def snippet_units(corpus_root, bench_dir, by_md, by_repo_path, ts, onto, stats):
    cache = FileCache(corpus_root, by_md, ts)
    records = collections.defaultdict(list)   # lang -> [record]
    consumed = set()   # (lang, md_file, start_line0, end_line0) already used, so top-up skips them

    for lang in LANGS:
        sdir = os.path.join(bench_dir, "snippets", lang)
        if not os.path.isdir(sdir):
            continue
        for name in sorted(os.listdir(sdir)):
            if not name.endswith(".json"):
                continue
            with open(os.path.join(sdir, name), encoding="utf-8") as f:
                s = json.load(f)
            stats["units"]["snippet_candidates"] += 1
            prov = s["provenance"]
            label = prov["unit"]
            label_word = label.split(" ", 1)[0]
            start0, end0 = prov["startLine"] - 1, prov["endLine"] - 1

            if lang == "python":
                if label_word not in _KEEP_KINDS:
                    stats["rejections"]["kind_excluded"] += 1
                    continue
                kind = label_word
                name_ = label.rsplit(".", 1)[-1] if label_word == "method" else label.split(" ", 1)[1]
                rec = build_record(origin="snippet", language=lang, standard_id=s["standardId"], kind=kind,
                                   name=name_, code_text=s["codeContext"], path_hint=prov["path"], lines_above=None,
                                   u_start_idx=None, source=s["source"], source_detail=s["sourceDetail"],
                                   snippet_id=s["id"], provenance=dict(prov), stats=stats, onto=onto, ts=ts)
            else:
                if label_word in ("interface", "constructor", "const", "enum"):
                    stats["rejections"]["kind_excluded"] += 1
                    continue
                md_file = by_repo_path.get((lang, prov["repo"], prov["path"]))
                if md_file is None:
                    stats["rejections"]["corpus_index_lookup_failed"] += 1
                    continue
                meta, content, text, ff, ls = cache.get(lang, md_file)
                kind, name_ = resolve_kind_name(ff, ls, content, start0, end0)
                if kind not in _KEEP_KINDS:
                    stats["rejections"]["kind_excluded"] += 1
                    continue
                lines_all = text.split("\n")
                rec = build_record(origin="snippet", language=lang, standard_id=s["standardId"], kind=kind,
                                   name=name_, code_text=s["codeContext"], path_hint=prov["path"],
                                   lines_above=lines_all, u_start_idx=start0, source=s["source"],
                                   source_detail=s["sourceDetail"], snippet_id=s["id"], provenance=dict(prov),
                                   stats=stats, onto=onto, ts=ts)
                consumed.add((lang, md_file, start0, end0))
            if rec is not None:
                records[lang].append(rec)
    return records, consumed


# --------------------------------------------------------------------------- pass 2: top-up from the 792-file corpus

def top_up(lang, need_from, corpus_root, by_md, ts, onto, stats, consumed):
    ldir = os.path.join(corpus_root, "corpus", lang)
    cache = FileCache(corpus_root, by_md, ts)
    cands = []
    for md_file in sorted(os.listdir(ldir)):
        if not md_file.endswith(".md"):
            continue
        row = by_md.get((lang, md_file))
        if row is None:
            continue
        meta, content, text, ff, ls = cache.get(lang, md_file)
        lines_all = text.split("\n")
        for u in ff.units:
            nlines = u.end_line - u.start_line + 1
            if nlines < MIN_LINES or nlines > MAX_LINES:
                continue
            if (lang, md_file, u.start_line, u.end_line) in consumed:
                continue
            kind, name_ = resolve_kind_name(ff, ls, content, u.start_line, u.end_line)
            if kind not in _KEEP_KINDS:
                continue
            key = hashlib.sha256(f"{row['repo']}|{row['source_path']}|{u.start_line + 1}".encode()).hexdigest()
            cands.append({"sort_key": key, "md_file": md_file, "repo": row["repo"], "path": row["source_path"],
                         "start_line": u.start_line, "end_line": u.end_line, "kind": kind, "name": name_,
                         "label": u.label, "meta": meta, "content": content, "lines": lines_all})
    cands.sort(key=lambda c: c["sort_key"])

    file_count, repo_count, accepted = collections.Counter(), collections.Counter(), []
    for c in cands:
        if len(accepted) >= TOPUP_MAX or need_from + len(accepted) >= TOPUP_MIN:
            break
        if file_count[c["md_file"]] >= MAX_PER_FILE:
            continue
        cap = max(1, math.ceil(MAX_REPO_SHARE * (len(accepted) + 1)))
        if repo_count[c["repo"]] >= cap:
            continue
        m = c["meta"]
        code_text = CUR.unit_text(c["content"], line_starts_of(c["content"]), c["start_line"], c["end_line"])
        source = f"github:{m['source repo']}@{m['commit']}"
        source_detail = (f"{m['file path']} lines {c['start_line'] + 1}-{c['end_line'] + 1} ({c['label']}); "
                         f"license {m['license']}; repo created {m['created_at']}; curated by {PIPELINE_VERSION}")
        stats["units"]["extra_candidates"] += 1
        provenance = {"repo": c["repo"], "path": c["path"], "startLine": c["start_line"] + 1,
                     "endLine": c["end_line"] + 1, "corpusFile": f"corpus/{lang}/{c['md_file']}"}
        rec = build_record(origin="extra", language=lang, standard_id=onto.default_standard[lang], kind=c["kind"],
                           name=c["name"], code_text=code_text, path_hint=c["path"], lines_above=c["lines"],
                           u_start_idx=c["start_line"], source=source, source_detail=source_detail,
                           snippet_id=None, provenance=provenance, stats=stats, onto=onto, ts=ts)
        if rec is None:
            continue
        file_count[c["md_file"]] += 1
        repo_count[c["repo"]] += 1
        accepted.append(rec)
    for i, rec in enumerate(accepted, 1):
        rec["snippetId"] = f"cx_{lang}_{i:03d}"
    return accepted


# --------------------------------------------------------------------------- output

def write_outputs(records_by_lang, out_dir, stats):
    rows = []
    for lang in LANGS:
        recs = sorted(records_by_lang.get(lang, []), key=lambda r: r["snippetId"])
        cdir = os.path.join(out_dir, "comment_units", lang)
        os.makedirs(cdir, exist_ok=True)
        for existing in sorted(os.listdir(cdir)) if os.path.isdir(cdir) else []:
            os.remove(os.path.join(cdir, existing))
        for rec in recs:
            uid = rec["snippetId"]
            with open(os.path.join(cdir, uid + ".json"), "w", encoding="utf-8", newline="\n") as f:
                json.dump(rec, f, indent=2, ensure_ascii=False)
                f.write("\n")
            rows.append([uid, lang, rec["standardId"], rec["identifierKind"], rec["name"], rec["origin"],
                        rec["referenceCommentLines"], rec["signature"]["params"], rec["signature"]["returns"],
                        rec["signature"]["throws"]])
    with open(os.path.join(out_dir, "comment_units_index.tsv"), "w", encoding="utf-8", newline="\n") as f:
        f.write("\t".join(["unit_id", "language", "standard_id", "identifier_kind", "name", "origin",
                          "reference_comment_lines", "sig_params", "sig_returns", "sig_throws"]) + "\n")
        for r in rows:
            f.write("\t".join(str(x) for x in r) + "\n")
    return len(rows)


def plain(o):
    if isinstance(o, (dict, collections.defaultdict)):
        return {k: plain(v) for k, v in o.items()}
    if isinstance(o, collections.Counter):
        return dict(sorted(o.items()))
    return o


# --------------------------------------------------------------------------- main

def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--corpus", required=True, help="athena-corpus folder (contains corpus/ and corpus_index.tsv)")
    ap.add_argument("--out", required=True, help="benchmark folder (contains snippets/, violations/)")
    ap.add_argument("--ontology", default=R.DEFAULT_ONTOLOGY)
    ap.add_argument("--lib", default=None)
    ap.add_argument("--stats", default=None)
    args = ap.parse_args()

    from tsbind import TreeSitter, find_library
    onto = R.Ontology(args.ontology)
    ts = TreeSitter(find_library(args.lib))
    by_md, by_repo_path = load_corpus_index(args.corpus)

    stats = {"pipeline": PIPELINE_VERSION, "units": collections.Counter(), "rejections": collections.Counter(),
             "leading_comment_was_inside_snippet": 0, "by_lang_kind_origin": collections.Counter()}

    records, consumed = snippet_units(args.corpus, args.out, by_md, by_repo_path, ts, onto, stats)
    for lang in LANGS:
        if len(records.get(lang, [])) < TOPUP_MIN:
            extra = top_up(lang, len(records.get(lang, [])), args.corpus, by_md, ts, onto, stats, consumed)
            records.setdefault(lang, []).extend(extra)

    for lang in LANGS:
        for rec in records.get(lang, []):
            stats["by_lang_kind_origin"][f"{lang}|{rec['identifierKind']}|{rec['origin']}"] += 1

    n = write_outputs(records, args.out, stats)
    print(f"wrote {n} comment units to {os.path.join(args.out, 'comment_units')}")
    for lang in LANGS:
        by_kind = collections.Counter(r["identifierKind"] for r in records.get(lang, []))
        by_origin = collections.Counter(r["origin"] for r in records.get(lang, []))
        print(f"  {lang:11s} n={len(records.get(lang, [])):3d} kinds={dict(by_kind)} origin={dict(by_origin)}")
    print("rejections:", dict(sorted(stats["rejections"].items())))

    sp = args.stats or os.path.join(args.out, "comment_units_stats.json")
    with open(sp, "w", encoding="utf-8", newline="\n") as f:
        json.dump(plain(stats), f, indent=1, ensure_ascii=False, default=str)
        f.write("\n")


if __name__ == "__main__":
    main()
