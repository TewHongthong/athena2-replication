"""Aggregate judge ratings (see ADDENDUM.md):  python aggregate.py [--judges granite42 museglimmer]"""
import argparse, glob, json, math, os
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__)); RES = os.path.join(HERE, "results")
CRIT = ["accuracy", "completeness", "clarity", "conformance"]
CONDS = ["none", "fulldoc", "chunk", "graph"]
SELF_FAMILY = {"Gemma 4 26B": "gemma", "Qwen3.5-9B": "qwen"}


def load_judgments(keys):
    out = {}
    for k in keys:
        d = {}
        for l in open(os.path.join(RES, f"judgments_{k}.jsonl"), encoding="utf-8"):
            r = json.loads(l)
            if r.get("ok"): d[r["item"]] = r["scores"]
        out[k] = d
    return out


def qwk(a, b, k=5):
    n = len(a)
    if n == 0: return float("nan")
    O = [[0] * k for _ in range(k)]
    for x, y in zip(a, b): O[x - 1][y - 1] += 1
    ra = [sum(r) for r in O]; cb = [sum(O[i][j] for i in range(k)) for j in range(k)]
    num = sum((i - j) ** 2 * O[i][j] for i in range(k) for j in range(k))
    den = sum((i - j) ** 2 * ra[i] * cb[j] / n for i in range(k) for j in range(k))
    return 1 - num / den if den else float("nan")


def sign_p(b, w):
    n = b + w
    if n == 0: return 1.0
    return min(1.0, 2 * sum(math.comb(n, i) for i in range(min(b, w) + 1)) / 2 ** n)


def holm(ps):
    order = sorted(range(len(ps)), key=lambda i: ps[i]); adj = [0] * len(ps); prev = 0
    for r, i in enumerate(order):
        prev = max(prev, min(1.0, (len(ps) - r) * ps[i])); adj[i] = prev
    return adj


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--judges", nargs="+", default=None)
    a = ap.parse_args()
    keys = a.judges or sorted(os.path.basename(p)[10:-6] for p in glob.glob(os.path.join(RES, "judgments_*.jsonl")))
    cfg = json.load(open(os.path.join(HERE, "judges.json"), encoding="utf-8"))
    fam = {k: cfg.get(k, {}).get("family") for k in keys}
    J = load_judgments(keys)
    mp = [json.loads(l) for l in open(os.path.join(HERE, "item_map.jsonl"), encoding="utf-8")]
    items = {json.loads(l)["id"] for l in open(os.path.join(HERE, "items.jsonl"), encoding="utf-8")}
    L = [f"# Rubric rating of generated comments (exploratory; see ADDENDUM.md)", "",
         f"Judges: {', '.join(f'{k} ({len(J[k])}/{len(items)} items rated)' for k in keys)}", ""]

    # agreement
    if len(keys) >= 2:
        k1, k2 = keys[:2]; both = [i for i in items if i in J[k1] and i in J[k2]]
        L += [f"## Agreement between {k1} and {k2} ({len(both)} items)", "", "| Criterion | weighted kappa | exact % | within 1 % |", "|---|---|---|---|"]
        for c in CRIT + ["overall"]:
            if c == "overall":
                x = [round(sum(J[k1][i].values()) / 4) for i in both]; y = [round(sum(J[k2][i].values()) / 4) for i in both]
            else:
                x = [J[k1][i][c] for i in both]; y = [J[k2][i][c] for i in both]
            ex = 100 * sum(p == q for p, q in zip(x, y)) / max(1, len(x)); w1 = 100 * sum(abs(p - q) <= 1 for p, q in zip(x, y)) / max(1, len(x))
            L.append(f"| {c} | {qwk(x, y):.2f} | {ex:.1f} | {w1:.1f} |")
        L.append("")

    # judge-unparsed counts and discrimination check (reference vs linter-autofix floor, GSCS)
    for k in keys:
        bad = sum(1 for l in open(os.path.join(RES, f"judgments_{k}.jsonl"), encoding="utf-8") if not json.loads(l).get("ok"))
        L.append(f"- {k}: unparsed/failed judge calls recorded: {bad}")
    def mean_overall(src, pack):
        v = [sum(sum(J[k][r["item"]].values()) / 4 for k in keys if r["item"] in J[k]) / max(1, sum(r["item"] in J[k] for k in keys))
             for r in mp if r["source"] == src and r["pack"] == pack and r["item"] and any(r["item"] in J[k] for k in keys)]
        return sum(v) / len(v) if v else float("nan")
    ref, flo = mean_overall("reference", "gscs"), mean_overall("linter autofix", "gscs")
    L += [f"- Discrimination check (GSCS): reference overall {ref:.2f} vs linter-autofix floor {flo:.2f} -> "
          + ("PASS" if ref > flo else "FAIL: judges do not discriminate; do not interpret the rubric results"), ""]

    def score(item, source, use):
        """mean over the judges in `use` that rated the item; per criterion + overall."""
        rs = [J[k][item] for k in use if item in J[k]]
        if not rs: return None
        s = {c: sum(r[c] for r in rs) / len(rs) for c in CRIT}; s["overall"] = sum(s.values()) / 4
        return s

    def judges_for(source, mode):
        if mode == "sensitivity" and source in SELF_FAMILY:
            return [k for k in keys if fam.get(k) != SELF_FAMILY[source]]
        return keys

    def table(mode):
        cells = defaultdict(list); per_unit = defaultdict(list); missing = 0
        for r in mp:
            use = judges_for(r["source"], mode)
            if r["item"] is None:
                s = {c: 1.0 for c in CRIT + ["overall"]}; answered = False
            else:
                s = score(r["item"], r["source"], use)
                if s is None: missing += 1; continue
                answered = True
            cells[(r["pack"], r["source"], r["condition"])].append((s, answered))
            per_unit[(r["pack"], r["source"], r["condition"], r["unit"])].append(s["overall"])
        return cells, per_unit, missing

    modes = ["main"] + (["sensitivity"] if any(fam.get(k) in SELF_FAMILY.values() for k in keys) else [])
    if len(modes) == 1:
        L += ["No judge shares a model family with any generator, so the self-family sensitivity analysis is not needed.", ""]
    for mode in modes:
        cells, per_unit, missing = table(mode)
        title = "All judges" if mode == "main" else "Sensitivity: self-family judge removed (Gemma 4 26B and Qwen3.5-9B outputs only)"
        L += [f"## {title}", "", f"Rows not yet rated by any judge: {missing}", "",
              "| Pack | Source | Condition | n | answered | accuracy | completeness | clarity | conformance | overall (all) | overall (answered) |",
              "|---|---|---|---|---|---|---|---|---|---|---|"]
        for (pack, src, cond), v in sorted(cells.items(), key=lambda kv: (kv[0][0], kv[0][1], (CONDS + ["reference"]).index(kv[0][2]))):
            if mode == "sensitivity" and src not in SELF_FAMILY: continue
            n = len(v); ans = [s for s, a in v if a]
            m = {c: sum(s[c] for s, _ in v) / n for c in CRIT + ["overall"]}
            oa = sum(s["overall"] for s in ans) / len(ans) if ans else float("nan")
            L.append(f"| {pack} | {src} | {cond} | {n} | {len(ans)} | " + " | ".join(f"{m[c]:.2f}" for c in CRIT) + f" | {m['overall']:.2f} | {oa:.2f} |")
        L.append("")
        tests = []
        for pack, src in sorted({(p, s) for (p, s, c, u) in per_unit if c in CONDS and s not in ("linter autofix",)}):
            if mode == "sensitivity" and src not in SELF_FAMILY: continue
            units = sorted({u for (p, s, c, u) in per_unit if p == pack and s == src})
            for other in ("none", "fulldoc"):
                b = w = 0; diffs = []
                for u in units:
                    g = per_unit.get((pack, src, "graph", u)); o = per_unit.get((pack, src, other, u))
                    if not g or not o: continue
                    d = sum(g) / len(g) - sum(o) / len(o); diffs.append(d); b += d > 0; w += d < 0
                tests.append([pack, src, other, sum(diffs) / max(1, len(diffs)), b, w, sign_p(b, w)])
        adj = holm([t[6] for t in tests])
        L += ["Paired exact sign tests, per-unit mean overall score, graph vs other (Holm within this table):", "",
              "| Pack | Source | graph vs | mean diff | units better | units worse | p | Holm p |", "|---|---|---|---|---|---|---|---|"]
        for t, h in zip(tests, adj):
            L.append(f"| {t[0]} | {t[1]} | {t[2]} | {t[3]:+.2f} | {t[4]} | {t[5]} | {t[6]:.3g} | {h:.3g} |")
        L.append("")
    open(os.path.join(RES, "rubric_summary.md"), "w", encoding="utf-8").write("\n".join(L) + "\n")
    print("\n".join(L))


if __name__ == "__main__":
    main()
