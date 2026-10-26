"""Exploratory semantic-preservation check for GSCS renames (see ADDENDUM.md).
Modes: prepare | run --budget SEC | report.  Results go to results/."""
import argparse, functools, glob, hashlib, json, math, os, re, subprocess, sys, tempfile, time
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor

HERE = os.path.dirname(os.path.abspath(__file__))
SIM = os.path.dirname(HERE)
sys.path.insert(0, SIM)
from athena.evaluate import apply_rename  # same whole-word rename as the Similarity Index

RES = os.path.join(HERE, "results")
WORK = os.path.join(os.path.expanduser("~"), "semantic_work")
SNIP = os.path.join(SIM, "packs", "gscs", "benchmark", "snippets")
RUNS = {
    "o3-mini": "runs/test_o3mini_gscs_rename/trials.jsonl",
    "GPT-6 Luna": "runs/test_luna_gscs_rename/trials.jsonl",
    "Qwen3.5-9B": "qwen_plan_a/runs/qwen_gscs_rename/trials.jsonl",
    "Gemini 3.1 Flash-Lite": "gemini31fl/runs/gemini31fl_gscs_rename/trials.jsonl",
    "DeepSeek V4 Flash": "dsv4f_v2/runs/dsv4f_gscs_rename/trials.jsonl",
    "Gemma 4 26B": "gemma4/gemma4_gscs_rename/trials.jsonl",
    "linter autofix": "runs/test_autofix_gscs_rename/trials.jsonl",
}
CONDS = ["none", "fulldoc", "chunk", "graph"]
CPP_PRELUDE = "#include <iostream>\n#include <iomanip>\n#include <string>\n#define private public\n"
EXT = {"cpp": "cpp", "java": "java", "python": "py"}


def seed_code(sid):
    lang = sid.split("_")[1]
    return lang, json.load(open(os.path.join(SNIP, lang, sid + ".json")))["codeContext"]


@functools.lru_cache(maxsize=None)
def program_orig(sid):
    lang, code = seed_code(sid)
    drv = open(os.path.join(HERE, "drivers", f"{sid}.{EXT[lang]}")).read()
    if lang == "cpp":
        return lang, CPP_PRELUDE + code + "\n\n" + drv
    if lang == "java":
        return lang, drv + "\n" + code + "\n"
    return lang, code + "\n\n" + drv


def execute(lang, src):
    """Build and run one program. Returns (status, stdout, detail)."""
    h = hashlib.sha256((lang + src).encode()).hexdigest()[:16]
    d = os.path.join(WORK, h); os.makedirs(d, exist_ok=True)
    env = dict(os.environ); env.pop("JAVA_TOOL_OPTIONS", None)
    try:
        if lang == "cpp":
            p = os.path.join(d, "prog.cpp"); open(p, "w").write(src)
            c = subprocess.run(["g++", "-std=c++17", "-w", "-o", os.path.join(d, "prog"), p],
                               capture_output=True, text=True, timeout=60)
            if c.returncode: return "compile_error", "", c.stderr[-400:]
            r = subprocess.run([os.path.join(d, "prog")], capture_output=True, text=True, timeout=10)
        elif lang == "java":
            p = os.path.join(d, "Prog.java"); open(p, "w").write(src)
            r = subprocess.run(["java", p], capture_output=True, text=True, timeout=60, env=env)
            if r.returncode and "compilation failed" in r.stderr:
                return "compile_error", "", r.stderr[-400:]
        else:
            p = os.path.join(d, "prog.py"); open(p, "w").write(src)
            c = subprocess.run([sys.executable, "-m", "py_compile", p], capture_output=True, text=True, timeout=30)
            if c.returncode: return "compile_error", "", c.stderr[-400:]
            r = subprocess.run([sys.executable, p], capture_output=True, text=True, timeout=10)
    except subprocess.TimeoutExpired:
        return "timeout", "", ""
    if r.returncode: return "runtime_error", r.stdout, r.stderr[-400:]
    return "ran", r.stdout, ""


def load_trials():
    sig = json.dumps({m: os.path.getmtime(os.path.join(SIM, r)) for m, r in RUNS.items()})
    tc = os.path.join(WORK, "trials_min.json")
    if os.path.exists(tc):
        d = json.load(open(tc))
        if d["sig"] == sig: return d["trials"]
    out = []
    for model, rel in RUNS.items():
        best = {}
        for line in open(os.path.join(SIM, rel)):
            t = json.loads(line)
            k = t["key"]
            if k not in best or (best[k].get("error") and not t.get("error")) or (not t.get("error") and t["ts"] >= best[k]["ts"]):
                best[k] = t
        for t in best.values():
            m = t.get("metrics") or {}
            out.append(dict(model=model, unit=t["unit_id"], sid=t["snippet_id"], lang=t["language"], cond=t["condition"],
                            rep=t["repeat"], original=t["original"], injected=t["injected"], suggested=m.get("suggested"),
                            valid=bool(m.get("valid_identifier")), core_ok=bool(m.get("core_ok")), error=t.get("error")))
    os.makedirs(WORK, exist_ok=True); json.dump(dict(sig=sig, trials=out), open(tc, "w"))
    return out


EXEC = os.path.join(RES, "exec_cache.jsonl")


def load_exec():
    c = {}
    if os.path.exists(EXEC):
        for line in open(EXEC):
            r = json.loads(line); c[r["h"]] = r
    return c


def phash(lang, src):
    return hashlib.sha256((lang + src).encode()).hexdigest()


def execute_all(progs, budget):
    """progs: {h: (lang, src)}. Runs the uncached ones (2 workers) until the time budget is spent."""
    os.makedirs(RES, exist_ok=True)
    cache = load_exec(); pending = [(h, v) for h, v in progs.items() if h not in cache]
    t0 = time.time(); done = 0
    def work(item):
        h, (lang, src) = item
        st, out, det = execute(lang, src)
        return dict(h=h, lang=lang, status=st, stdout=out, detail=det[-300:])
    with ThreadPoolExecutor(2) as ex, open(EXEC, "a") as f:
        i = 0
        while i < len(pending) and time.time() - t0 < budget:
            batch = pending[i:i + 4]; i += 4
            for r in ex.map(work, batch):
                f.write(json.dumps(r) + "\n"); f.flush(); done += 1
    left = len(pending) - done
    print(f"programs {len(progs)}, ran now {done}, remaining {left}, {time.time()-t0:.0f}s")
    return left == 0


def seed_ids():
    return sorted(os.path.splitext(os.path.basename(f))[0] for f in glob.glob(os.path.join(HERE, "drivers", "*")))


def prepare(budget):
    trials = load_trials()
    pairs = sorted({(t["sid"], t["original"], t["injected"]) for t in trials})
    progs, gold_h, viol_h = {}, {}, {}
    for sid in seed_ids():
        lang, src = program_orig(sid); h = phash(lang, src); progs[h] = (lang, src); gold_h[sid] = h
    for sid, o, i in pairs:
        lang, src = program_orig(sid); v = apply_rename(src, o, i)[0]; h = phash(lang, v); progs[h] = (lang, v); viol_h[(sid, o, i)] = h
    if not execute_all(progs, budget):
        print("prepare not finished - run again"); return
    cache = load_exec()
    golden = {sid: dict(status=cache[h]["status"], stdout=cache[h]["stdout"], detail=cache[h]["detail"]) for sid, h in gold_h.items()}
    sanity = []
    for (sid, o, i), h in viol_h.items():
        r = cache[h]; ok = r["status"] == "ran" and golden[sid]["status"] == "ran" and r["stdout"] == golden[sid]["stdout"]
        sanity.append(dict(sid=sid, original=o, injected=i, ok=ok, status=r["status"], detail=r["detail"]))
    json.dump(golden, open(os.path.join(RES, "golden.json"), "w"), indent=1)
    json.dump(sanity, open(os.path.join(RES, "sanity.json"), "w"), indent=1)
    for sid, g in golden.items(): print(sid, g["status"], repr(g["stdout"][:100]))
    print("units:", len(sanity), "sanity ok:", sum(s["ok"] for s in sanity), "fail:", [(s["sid"], s["original"], s["injected"], s["status"]) for s in sanity if not s["ok"]])


def jobs():
    trials = load_trials(); todo = {}
    for t in trials:
        if t["valid"] and t["suggested"] != t["injected"]:
            lang, src = program_orig(t["sid"])
            viol = apply_rename(src, t["original"], t["injected"])[0]
            after = apply_rename(viol, t["injected"], t["suggested"])[0]
            t["h"] = phash(t["lang"], after); todo[t["h"]] = (t["lang"], after)
    return trials, todo


def run(budget):
    _, todo = jobs()
    print("finished" if execute_all(todo, budget) else "not finished - run again")


def wilson(k, n, z=1.96):
    if n == 0: return (float("nan"),) * 2
    p = k / n; d = 1 + z * z / n; c = (p + z * z / (2 * n)) / d; w = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return c - w, c + w


def sign_p(b, w):
    n = b + w
    if n == 0: return 1.0
    k = min(b, w)
    return min(1.0, 2 * sum(math.comb(n, i) for i in range(k + 1)) / 2 ** n)


def report():
    cache = load_exec(); trials, todo = jobs()
    golden = json.load(open(os.path.join(RES, "golden.json")))
    sanity_bad = {(s["sid"], s["original"]) for s in json.load(open(os.path.join(RES, "sanity.json"))) if not s["ok"]}
    rows = []
    for t in trials:
        if (t["sid"], t["original"]) in sanity_bad: continue
        if "h" in t:
            if t["h"] not in cache: raise SystemExit("not finished: run more")
            r = cache[t["h"]]; st = r["status"]
            if st == "ran": st = "pass" if r["stdout"] == golden[t["sid"]]["stdout"] else "wrong_output"
        else:
            st = "not_applied"
        t["status"] = st; t["preserved"] = st in ("pass", "not_applied"); t["cap"] = t["core_ok"] and st == "pass"
        rows.append(t)
    import csv
    with open(os.path.join(RES, "trial_results.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["model", "unit", "sid", "lang", "cond", "rep", "original", "injected", "suggested", "core_ok", "status", "cap"], extrasaction="ignore")
        w.writeheader(); w.writerows(rows)
    agg = defaultdict(lambda: defaultdict(int)); fails = defaultdict(lambda: defaultdict(int))
    for t in rows:
        a = agg[(t["model"], t["cond"])]; a["n"] += 1; a["core"] += t["core_ok"]; a["cap"] += t["cap"]
        if t["status"] != "not_applied":
            a["applied"] += 1; a["build"] += t["status"] not in ("compile_error",); a["pass"] += t["status"] == "pass"
            if t["status"] != "pass": fails[(t["model"], t["cond"])][t["status"]] += 1
    L = ["# Semantic preservation of GSCS renames (exploratory; see ADDENDUM.md)", "",
         f"Units excluded by sanity check: {len(sanity_bad)}. Trials scored: {len(rows)}.", "",
         "| Model | Condition | n | applied | build ok % | behavior ok % (applied) | core_ok % | core_ok AND pass % [95% CI] | failures |",
         "|---|---|---|---|---|---|---|---|---|"]
    summ = {}
    for model in RUNS:
        for c in CONDS:
            a = agg[(model, c)]
            if not a["n"]: continue
            lo, hi = wilson(a["cap"], a["n"])
            pb = 100 * a["build"] / a["applied"] if a["applied"] else float("nan")
            pp = 100 * a["pass"] / a["applied"] if a["applied"] else float("nan")
            fs = ", ".join(f"{k} {v}" for k, v in sorted(fails[(model, c)].items())) or "-"
            L.append(f"| {model} | {c} | {a['n']} | {a['applied']} | {pb:.1f} | {pp:.1f} | {100*a['core']/a['n']:.1f} | {100*a['cap']/a['n']:.1f} [{100*lo:.0f}-{100*hi:.0f}] | {fs} |")
            summ[f"{model}|{c}"] = dict(a, failures=dict(fails[(model, c)]))
    # paired tests on per-unit means of core_ok AND pass
    per = defaultdict(list)
    for t in rows: per[(t["model"], t["cond"], t["unit"])].append(t["cap"])
    tests = []
    for model in RUNS:
        if model == "linter autofix": continue
        units = sorted({u for (m, c, u) in per if m == model})
        for other in ("none", "fulldoc"):
            b = w = 0; diffs = []
            for u in units:
                g = sum(per[(model, "graph", u)]) / len(per[(model, "graph", u)]); o = sum(per[(model, other, u)]) / len(per[(model, other, u)])
                diffs.append(g - o); b += g > o; w += g < o
            tests.append([model, other, 100 * sum(diffs) / len(diffs), b, w, sign_p(b, w)])
    order = sorted(range(len(tests)), key=lambda i: tests[i][5]); m = len(tests); prev = 0
    for rank, i in enumerate(order):
        adj = min(1.0, max(prev, (m - rank) * tests[i][5])); tests[i].append(adj); prev = adj
    L += ["", "Paired exact sign tests on per-unit means of core_ok AND pass (Holm across all 12):", "",
          "| Model | graph vs | mean diff (pp) | units better | units worse | p | Holm p |", "|---|---|---|---|---|---|---|"]
    for t in tests: L.append(f"| {t[0]} | {t[1]} | {t[2]:+.1f} | {t[3]} | {t[4]} | {t[5]:.3g} | {t[6]:.3g} |")
    open(os.path.join(RES, "semantic_summary.md"), "w").write("\n".join(L) + "\n")
    json.dump(dict(cells=summ, tests=tests), open(os.path.join(RES, "semantic_summary.json"), "w"), indent=1)
    print("\n".join(L))


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("mode"); ap.add_argument("--budget", type=float, default=150)
    a = ap.parse_args()
    if a.mode == "prepare": prepare(a.budget)
    elif a.mode == "run": run(a.budget)
    else: report()
