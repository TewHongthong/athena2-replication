"""Scope-aware name-conflict check on GSCS renames (exploratory; see ADDENDUM.md).
Usage: python3 run_scope.py controls | score"""
import csv
import re
import glob
import json
import os
import subprocess
import sys
import tempfile
from collections import Counter, defaultdict

from common import IDENTITY, OffsetMap, apply_rename, compare, word_re
import cpp_scope
import py_scope

HERE = os.path.dirname(os.path.abspath(__file__))
UNITS = {os.path.basename(f)[:-5]: json.load(open(f))
         for f in glob.glob(os.path.join(HERE, "packs/gscs/benchmark/violations/*/*.json"))}
UNITS = {k: v for k, v in UNITS.items() if v["split"] == "test"}
JAVA_KW = set("""abstract assert boolean break byte case catch char class const continue default do double else enum
extends final finally float for goto if implements import instanceof int interface long native new package private
protected public return short static strictfp super switch synchronized this throw throws transient try void volatile
while true false null var record yield""".split())
OUT = os.path.join(HERE, "results")


def lang_of(uid):
    return uid.split("_")[1]


# ---------------------------------------------------------------- Java (batch through one JVM)
def java_batch(codes):
    """codes: list of source strings -> list of raw dumps"""
    tmp = tempfile.mkdtemp()
    paths = []
    for i, c in enumerate(codes):
        d = os.path.join(tmp, str(i)); os.makedirs(d)
        p = os.path.join(d, "Snippet.java"); open(p, "w").write(c); paths.append(p)
    env = dict(os.environ); env.pop("JAVA_TOOL_OPTIONS", None)
    r = subprocess.run(["java", "-cp", os.path.join(HERE, "jbin"), "ScopeDump"], input="\n".join(paths) + "\n",
                       capture_output=True, text=True, env=env, timeout=3600)
    outs = [json.loads(l) for l in r.stdout.splitlines() if l.strip()]
    assert len(outs) == len(codes), r.stderr[-2000:]
    return outs


def java_info(raw, omap):
    res = {"errors": raw["errors"], "occ": {}, "decls": [], "ext_uses": []}
    mk = lambda k: tuple(k) if k[0] != "src" else ("src", k[1], omap(k[2]))  # noqa: E731
    sc = lambda s: tuple((k, omap(p)) for k, p in s)  # noqa: E731
    for d in raw["decls"]:
        o = omap(d["pos"])
        res["occ"][("d", d["kind"], o)] = ("src", d["kind"], o)
        res["decls"].append({"name": d["name"], "kind": d["kind"], "scope": sc(d["scope"])})
    for x in raw["occ"]:
        res["occ"][("r", omap(x["pos"]))] = mk(x["key"])
        if x["simple"] and x["ext"]:
            res["ext_uses"].append({"name": x["name"], "scope": sc(x["scope"])})
    return res


def java_decl_conflicts(info, injected, suggested):
    reasons = []
    if suggested in JAVA_KW:
        reasons.append("reserved word")
    for r in [d for d in info["decls"] if d["name"] == injected]:
        rs = r["scope"]
        for d in [d for d in info["decls"] if d["name"] == suggested]:
            ds = d["scope"]
            if rs[:len(ds)] == ds:
                reasons.append(f"{suggested} declared in enclosing/same scope ({d['kind']})")
            elif ds[:len(rs)] == rs:
                reasons.append(f"{suggested} declared in nested scope ({d['kind']})")
        for u in info["ext_uses"]:
            if u["name"] == suggested and u["scope"][:len(rs)] == rs:
                reasons.append(f"external name {suggested} used in scope")
    return sorted(set(reasons))


# ---------------------------------------------------------------- one batch of renames
def _cpp_after(args):
    u, s = args
    unit = UNITS[u]; b = unit["codeContextWithViolation"]; inj = unit["injectedName"]
    a, _ = apply_rename(b, inj, s)
    return cpp_scope.analyse(a, OffsetMap(b, inj, s))


def check_all(pairs):
    """pairs: list of (uid, suggested). Returns dict (uid, suggested) -> verdict."""
    before = {}
    jb_ids = sorted({u for u, _ in pairs if lang_of(u) == "java"})
    jb_raw = java_batch([UNITS[u]["codeContextWithViolation"] for u in jb_ids]) if jb_ids else []
    for u, raw in zip(jb_ids, jb_raw):
        before[u] = java_info(raw, IDENTITY)
    for u in sorted({u for u, _ in pairs if lang_of(u) != "java"}):
        code = UNITS[u]["codeContextWithViolation"]
        before[u] = (cpp_scope.analyse if lang_of(u) == "cpp" else py_scope.analyse)(code, IDENTITY)
    for u, info in before.items():
        assert not info["errors"], (u, info["errors"])
    out = {}
    jp = [(u, s) for u, s in pairs if lang_of(u) == "java"]
    j_after = java_batch([apply_rename(UNITS[u]["codeContextWithViolation"], UNITS[u]["injectedName"], s)[0]
                          for u, s in jp]) if jp else []
    after_raw = dict(zip(jp, j_after))
    from concurrent.futures import ProcessPoolExecutor
    cp = [(u, s) for u, s in pairs if lang_of(u) == "cpp"]
    with ProcessPoolExecutor(max_workers=os.cpu_count()) as ex:
        cpp_after = dict(zip(cp, ex.map(_cpp_after, cp, chunksize=4)))
    for u, s in pairs:
        unit = UNITS[u]; b = unit["codeContextWithViolation"]; inj = unit["injectedName"]; lang = lang_of(u)
        a, n = apply_rename(b, inj, s)
        om = OffsetMap(b, inj, s)
        if lang == "java":
            ia = java_info(after_raw[(u, s)], om)
            c3 = java_decl_conflicts(before[u], inj, s)
        elif lang == "cpp":
            ia = cpp_after[(u, s)]
            c3 = cpp_scope.declaration_conflicts(before[u], inj, s)
        else:
            ia = py_scope.analyse(a, om)
            c3 = py_scope.declaration_conflicts(before[u], inj, s)
        reasons = []
        if ia["errors"]:
            reasons.append("front-end error after rename: " + "; ".join(ia["errors"])[:200])
        bad, why = compare(before[u]["occ"], ia["occ"]) if not ia["errors"] else (True, [])
        reasons += why
        blind = s not in (inj, unit["originalName"]) and bool(word_re(s).search(b))
        out[(u, s)] = {"check2": bool(reasons), "check2_reasons": reasons, "check3": bool(c3), "check3_reasons": c3,
                       "blind": blind, "occurrences_renamed": n}
    return out


CONTROLS_NEG = [  # (unit prefix, suggested, why)
    ("gscs_cpp_004__str_new_name__strip_prefix", "str_student_name", "parameter shadows field read in method"),
    ("gscs_cpp_004__str_new_name__strip_prefix", "MAX_NAME_SIZE", "parameter redeclared by local"),
    ("gscs_cpp_005__i_index__", "f_maximum", "loop variable merged with local"),
    ("gscs_cpp_002__f_gpax__", "int", "keyword"),
    ("gscs_java_004__d_amount__", "d_balance", "parameter shadows field read in method"),
    ("gscs_java_001__f_gpax__", "f_point_total", "local redeclares parameter"),
    ("gscs_java_002__f_gpax__", "class", "keyword"),
    ("gscs_java_001__f_gpax__", "Math", "local shadows class used in Math.min"),
    ("gscs_python_005__str_price_text__", "f_price", "parameter merged with local"),
    ("gscs_python_001__f_gpax__", "min", "local captures builtin min used in method"),
    ("gscs_python_002__f_gpax__", "print", "parameter captures builtin print"),
    ("gscs_python_004__i_count_total__", "Add_Count", "attribute merged with method"),
    ("gscs_python_002__f_gpax__", "for", "keyword"),
]


def find_unit(prefix):
    hits = sorted(u for u in UNITS if u.startswith(prefix))
    assert hits, prefix
    return hits[0]


def controls():
    pos = [(u, "zzFreshName") for u in sorted(UNITS)]
    neg = [(find_unit(p), s) for p, s, _ in CONTROLS_NEG]
    v = check_all(pos + neg)
    fp2 = [k for k in pos if v[k]["check2"]]
    fp3 = [k for k in pos if v[k]["check3"]]
    lines = [f"Positive control: {len(pos)} units renamed to a fresh name; check 2 flags {len(fp2)}, check 3 flags {len(fp3)}"]
    for k in fp2 + fp3:
        lines.append(f"  FLAG {k}: {v[k]['check2_reasons']} {v[k]['check3_reasons']}")
    lines.append("Negative controls (must be flagged by check 2):")
    for (p, s, why), k in zip(CONTROLS_NEG, neg):
        lines.append(f"  {'OK  ' if v[k]['check2'] else 'MISS'} {k[0]} -> {s} ({why}); check2={v[k]['check2']} "
                     f"{v[k]['check2_reasons'][:2]}; check3={v[k]['check3']} {v[k]['check3_reasons']}")
    return "\n".join(lines)


def versions():
    env = dict(os.environ); env.pop("JAVA_TOOL_OPTIONS", None)
    cl = subprocess.run(["clang++", "--version"], capture_output=True, text=True).stdout.splitlines()[0]
    jv = subprocess.run(["java", "-version"], capture_output=True, text=True, env=env).stderr.splitlines()[0]
    return {"clang": cl, "java": jv, "python": sys.version.split()[0]}


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    if sys.argv[1] == "controls":
        txt = controls()
        print(txt)
        open(os.path.join(OUT, "controls.txt"), "w").write(json.dumps(versions()) + "\n" + txt + "\n")


# ---------------------------------------------------------------- scoring
MODELS = ["o3-mini", "GPT-6 Luna", "Qwen3.5-9B", "Gemini 3.1 Flash-Lite", "DeepSeek V4 Flash", "Gemma 4 26B",
          "linter autofix"]
CONDS = ["none", "fulldoc", "chunk", "graph"]


def strip_comments_strings(code, lang):
    if lang == "python":
        code = re.sub(r'("""|\'\'\')[\s\S]*?\1', " ", code)
        code = re.sub(r'"(\\.|[^"\\\n])*"|\'(\\.|[^\'\\\n])*\'', " ", code)
        return re.sub(r"#[^\n]*", " ", code)
    code = re.sub(r"/\*[\s\S]*?\*/", " ", code)
    code = re.sub(r"//[^\n]*", " ", code)
    return re.sub(r'"(\\.|[^"\\\n])*"', " ", code)


def score():
    rows = list(csv.DictReader(open(os.path.join(HERE, "semantic_check/results/trial_results.csv"))))
    applied = [r for r in rows if r["status"] != "not_applied"]
    pairs = sorted({(r["unit"], r["suggested"]) for r in applied})
    v = check_all(pairs)
    json.dump({f"{u}|{s}": x for (u, s), x in v.items()}, open(os.path.join(OUT, "verdicts.json"), "w"), indent=1)
    L = [f"# Scope-aware name-conflict check (exploratory; see ADDENDUM.md)", "",
         f"Front ends: {json.dumps(versions())}", "",
         f"Trials: {len(rows)}; applied (compiled and run in semantic_check): {len(applied)}; distinct renames analysed: {len(pairs)}", ""]
    # contingency
    L += ["## Each check against the compile-and-run outcome (applied trials)", "",
          "| check | flagged | flagged, behaviour changed | flagged, behaviour unchanged (false alarm) | not flagged, behaviour changed |",
          "|---|---|---|---|---|"]
    for name, key in [("1 scope-blind collision (frozen)", "blind"), ("2 scope-aware conflict (binding)", "check2"),
                      ("3 scope-aware declaration (IDE-style)", "check3")]:
        f = [r for r in applied if v[(r["unit"], r["suggested"])][key]]
        bc = lambda r: r["status"] != "pass"  # noqa: E731
        L.append(f"| {name} | {len(f)} | {sum(bc(r) for r in f)} | {sum(not bc(r) for r in f)} | "
                 f"{sum(bc(r) for r in applied if not v[(r['unit'], r['suggested'])][key])} |")
    L.append("")
    # per model x condition
    L += ["## Per model and condition (all 366 trials; not applied = failure)", "",
          "| Model | Condition | core-rule % | collision-screened (scope-blind) % | scope-screened (check 2) % | core_ok AND pass % | blind flags | check 2 flags |",
          "|---|---|---|---|---|---|---|---|"]
    tab = defaultdict(list)
    for r in rows:
        tab[(r["model"], r["cond"])].append(r)
    summary = {}
    for m in MODELS:
        for c in CONDS:
            rs = tab[(m, c)]
            def vv(r, k):
                return r["status"] != "not_applied" and v[(r["unit"], r["suggested"])][k]
            core = [r["core_ok"] == "True" for r in rs]
            pct = lambda xs: 100.0 * sum(xs) / len(xs)  # noqa: E731
            a = pct(core); b = pct([co and not vv(r, "blind") for co, r in zip(core, rs)])
            s2 = pct([co and not vv(r, "check2") for co, r in zip(core, rs)])
            cp = pct([co and r["status"] == "pass" for co, r in zip(core, rs)])
            nb = sum(vv(r, "blind") for r in rs); n2 = sum(vv(r, "check2") for r in rs)
            summary[f"{m}|{c}"] = dict(n=len(rs), core=a, blind_screened=b, scope_screened=s2, core_and_pass=cp,
                                       blind_flags=nb, check2_flags=n2)
            L.append(f"| {m} | {c} | {a:.1f} | {b:.1f} | {s2:.1f} | {cp:.1f} | {nb} | {n2} |")
    L.append("")
    # flags of check 2
    cnt = Counter((r["unit"], r["suggested"]) for r in applied)
    status = defaultdict(Counter)
    for r in applied:
        status[(r["unit"], r["suggested"])][r["status"]] += 1
    L += ["## Every rename flagged by check 2 (distinct unit and suggestion)", "",
          "| unit | injected -> suggested | trials | outcomes | blind | check 3 | reason |", "|---|---|---|---|---|---|---|"]
    for k in pairs:
        if v[k]["check2"]:
            u, s = k
            L.append(f"| {u} | {UNITS[u]['injectedName']} -> {s} | {cnt[k]} | {dict(status[k])} | {v[k]['blind']} | "
                     f"{v[k]['check3']} | {'; '.join(v[k]['check2_reasons'])[:160]} |")
    L.append("")
    # blind false alarms: why
    L += ["## Scope-blind flags that check 2 does not raise (distinct renames)", "",
          "| unit | injected -> suggested | trials | name outside comments/strings | check 3 | check 3 reason |", "|---|---|---|---|---|---|"]
    cat = Counter()
    for k in pairs:
        if v[k]["blind"] and not v[k]["check2"]:
            u, s = k
            code = strip_comments_strings(UNITS[u]["codeContextWithViolation"], lang_of(u))
            in_code = bool(word_re(s).search(code))
            cat[("code" if in_code else "comments/strings only", v[k]["check3"])] += cnt[k]
            L.append(f"| {u} | {UNITS[u]['injectedName']} -> {s} | {cnt[k]} | {in_code} | {v[k]['check3']} | {'; '.join(v[k]['check3_reasons'])} |")
    L.append("")
    L.append("Trials by category (where the name occurs, check 3 flag): " + json.dumps({f"{a}, check3={b}": n for (a, b), n in cat.items()}))
    L.append("")
    # check 3 only
    only3 = [k for k in pairs if v[k]["check3"] and not v[k]["check2"]]
    L += [f"## Check 3 flags without a check 2 flag: {len(only3)} distinct renames, {sum(cnt[k] for k in only3)} trials", ""]
    for k in only3:
        L.append(f"- {k[0]}: {UNITS[k[0]]['injectedName']} -> {k[1]} ({cnt[k]} trials; {dict(status[k])}): {'; '.join(v[k]['check3_reasons'])}")
    open(os.path.join(OUT, "results.md"), "w").write("\n".join(L) + "\n")
    json.dump(summary, open(os.path.join(OUT, "summary.json"), "w"), indent=1)
    print("\n".join(L[:40]))


if __name__ == "__main__" and sys.argv[1] == "score":
    score()
