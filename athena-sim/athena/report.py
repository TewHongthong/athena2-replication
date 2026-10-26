"""Turn trials.jsonl into trials.csv + summary.md (+ summary.csv).  Works on one or several run folders."""
from __future__ import annotations

import csv
import json
import math
import os
from collections import defaultdict

COND_ORDER = ["none", "fulldoc", "chunk", "bm25", "dense", "graph"]


def run_variant(run_dir: str) -> str:
    """Label of the setup of a run folder, read from its config.json: "" for the default setup (human ontology, kind
    from metadata), "llm" for the LLM-drafted ontology, "infer" for --no-oracle (kind inferred from the code),
    "llm+infer" for both.  A folder without a readable config.json counts as the default setup."""
    try:
        with open(os.path.join(run_dir, "config.json"), "r", encoding="utf-8") as f:
            args = (json.load(f) or {}).get("args") or {}
    except (OSError, json.JSONDecodeError, AttributeError):
        return ""
    parts = []
    if args.get("ontology_variant") == "llm":
        parts.append("llm")
    if args.get("no_oracle"):
        parts.append("infer")
    return "+".join(parts)


def load_trials(run_dirs, label_variants: bool = False) -> tuple:
    """Last record per key wins (so a retried failure replaces the error).  Returns (ok_records, error_keys).

    The key does not say which setup a run used, so records of runs that differ only in the ontology or in the kind
    source share keys and the last one read wins.  With `label_variants` the records of a run with a non-default setup
    (see `run_variant`) get a labelled condition such as `graph[llm]` or `graph[infer]` and a key with the same label,
    so that they stay apart; the unlabelled condition is kept in `condition_base`."""
    last: dict = {}
    for d in run_dirs:
        path = os.path.join(d, "trials.jsonl")
        if not os.path.exists(path):
            continue
        variant = run_variant(d) if label_variants else ""
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        r = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    if variant:
                        r["condition_base"] = r.get("condition")
                        r["condition"] = f"{r.get('condition')}[{variant}]"
                        r["key"] = f"{r['key']}|{variant}"
                    last[r["key"]] = r
    ok = [r for r in last.values() if not r.get("error")]
    err = [k for k, r in last.items() if r.get("error")]
    return ok, err


def wilson(k: int, n: int, z: float = 1.96):
    if n == 0:
        return (0.0, 0.0)
    p = k / n
    den = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / den
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    return (max(0.0, centre - half), min(1.0, centre + half))


def pct(k, n, ci=False):
    if n == 0:
        return "-"
    s = f"{100 * k / n:.1f}%"
    if ci:
        lo, hi = wilson(k, n)
        s += f" [{100 * lo:.0f}-{100 * hi:.0f}]"
    return s


def mean(xs):
    xs = [x for x in xs if x is not None]
    return sum(xs) / len(xs) if xs else None


def fmt(x, d=3):
    return "-" if x is None else f"{x:.{d}f}"


def mcnemar_p(b: int, c: int) -> float:
    n = b + c
    if n == 0:
        return 1.0
    k = min(b, c)
    return min(1.0, 2 * sum(math.comb(n, i) for i in range(k + 1)) / 2 ** n)


sign_test_p = mcnemar_p      # with one repeat per unit the two are the same exact test


def holm(ps: list) -> list:
    """Holm-Bonferroni adjusted p-values, same order as the input."""
    m, order, adj, run = len(ps), sorted(range(len(ps)), key=lambda i: ps[i]), [1.0] * len(ps), 0.0
    for rank, i in enumerate(order):
        run = max(run, min(1.0, (m - rank) * ps[i]))
        adj[i] = run
    return adj


def _cond_key(c):
    base = c.split("[", 1)[0]
    return (COND_ORDER.index(base) if base in COND_ORDER else 99, c)


def _table(headers, rows):
    out = ["| " + " | ".join(headers) + " |", "|" + "|".join(["---"] * len(headers)) + "|"]
    out += ["| " + " | ".join(str(c) for c in r) + " |" for r in rows]
    return "\n".join(out)


def _group(recs, keyfn):
    g = defaultdict(list)
    for r in recs:
        g[keyfn(r)].append(r)
    return g


def _rename_row(rs):
    n = len(rs)
    m = [r["metrics"] for r in rs]
    hits = [r["retrieval"].get("hit") for r in rs if r.get("retrieval", {}).get("hit") is not None]
    toks_in = sum(r.get("prompt_tokens") or 0 for r in rs)
    toks_out = sum(r.get("completion_tokens") or 0 for r in rs)
    cost = sum(r.get("cost_usd") or 0 for r in rs)
    pm = [x["prefix_match"] for x in m if x.get("prefix_match") is not None]
    return [n, pct(sum(x["parse_ok"] for x in m), n), pct(sum(x["exact_match"] for x in m), n, True),
            pct(sum(bool(x["violated_rule_ok"]) for x in m), n),
            pct(sum(bool(x["core_ok"]) for x in m), n, True), pct(sum(pm), len(pm)) if pm else "-",
            pct(sum(x["collision"] for x in m), n),
            f"{fmt(mean([x['sim_char_before'] for x in m]))} -> {fmt(mean([x['sim_char_after'] for x in m]))}",
            pct(sum(hits), len(hits)) if hits else "-",
            fmt(mean([r.get("latency_s") for r in rs]), 2), f"{toks_in}/{toks_out}", f"{cost:.4f}" if cost else "-"]


RENAME_HEAD = ["n", "parsed", "exact match [95% CI]", "violated rule ok", "all core rules ok [95% CI]",
               "type prefix kept", "collision", "similarity idx before -> after", "retrieval hit", "latency s", "tokens in/out", "cost USD"]


def _comment_row(rs):
    n = len(rs)
    m = [r["metrics"] for r in rs]
    lp, lt = sum(x["labels_present"] for x in m), sum(x["labels_total"] for x in m)
    lf, lft = sum(x["labels_filled"] for x in m), sum(x.get("labels_fill_total", x["labels_total"]) for x in m)
    ok = [x["comment_ok"] for x in m if x["comment_ok"] is not None]
    return [n, pct(sum(x["parse_ok"] for x in m), n), pct(sum(ok), len(ok), True), pct(lp, lt), pct(lf, lft),
            pct(sum(x["delimiter_ok"] for x in m), n), fmt(mean([x["sim_reference"] for x in m])),
            fmt(mean([r.get("latency_s") for r in rs]), 2),
            f"{sum(r.get('prompt_tokens') or 0 for r in rs)}/{sum(r.get('completion_tokens') or 0 for r in rs)}"]


COMMENT_HEAD = ["n", "parsed", "structure ok [95% CI]", "labels present", "labels filled", "delimiter ok",
                "similarity to reference", "latency s", "tokens in/out"]


def summarize(recs: list, errors: list, baseline: str | None = None, notes: list | None = None) -> str:
    if not recs:
        return "# Athena Sim summary\n\nNo successful trials yet.\n"
    out = ["# Athena Sim summary", ""]
    out.append(f"{len(recs)} successful trials, {len(errors)} trial keys with only errors. "
               "Rates are per trial; repeats of the same unit are pooled (treat CIs and p-values as exploratory).")
    if any(r["backend"].startswith("mock:") for r in recs):
        out.append("\n> Contains mock backends: **mock rows are deterministic stand-ins, not LLM results.**")
    splits = sorted({r.get("split") or "unspecified" for r in recs})
    out.append(f"\nSplit: {', '.join(splits)}.")
    if "dev" in splits and "test" in splits:
        out.append("\n> **This report mixes dev and test trials. Do not quote the pooled numbers; report the splits separately.**")
    for n in notes or []:
        out.append(f"\n> {n}")
    for task in sorted({r["task"] for r in recs}):
        tr = [r for r in recs if r["task"] == task]
        row_fn, head = (_rename_row, RENAME_HEAD) if task == "rename" else (_comment_row, COMMENT_HEAD)
        for pack in sorted({r["pack"] for r in tr}):
            pr = [r for r in tr if r["pack"] == pack]
            out += ["", f"## {task} - pack `{pack}`", "", "### By condition and backend", ""]
            g = _group(pr, lambda r: (r["backend"], r["condition"]))
            rows = [[b, c] + row_fn(g[(b, c)]) for (b, c) in sorted(g, key=lambda k: (k[0], _cond_key(k[1])))]
            out.append(_table(["backend", "condition"] + head, rows))
            key_metric = "core_ok" if task == "rename" else "comment_ok"
            langs = sorted({r["language"] for r in pr})
            out += ["", f"### By language ({'all core rules ok' if task == 'rename' else 'structure ok'}; "
                    f"n in brackets)", ""]
            rows = []
            for (b, c) in sorted(g, key=lambda k: (k[0], _cond_key(k[1]))):
                cells = []
                for lg in langs:
                    xs = [r for r in g[(b, c)] if r["language"] == lg]
                    vals = [bool(r["metrics"][key_metric]) for r in xs if r["metrics"].get(key_metric) is not None]
                    cells.append(f"{pct(sum(vals), len(vals))} [{len(vals)}]" if vals else "-")
                rows.append([b, c] + cells)
            out.append(_table(["backend", "condition"] + langs, rows))
            if task == "comment":
                out += ["", "### Per-language, per-condition (comment_ok, delimiter_ok, vacuous-check share)", "",
                       "`vacuous (n_checks=0)` is the share of units whose applicable MUST comment rules have no "
                       "mechanical check today (e.g. Python's plain-line-comment format, most Airbnb JS comment "
                       "rules) -- comment_ok is trivially true for those regardless of what the model writes.", ""]
                rows2 = []
                for (b, c) in sorted(g, key=lambda k: (k[0], _cond_key(k[1]))):
                    for lg in langs:
                        xs = [r for r in g[(b, c)] if r["language"] == lg]
                        if not xs:
                            continue
                        ms = [r["metrics"] for r in xs]
                        n = len(ms)
                        ok = [x["comment_ok"] for x in ms if x["comment_ok"] is not None]
                        vac = sum(1 for x in ms if x.get("n_checks", 0) == 0)
                        comment_ok_cell = f"{pct(sum(ok), len(ok), True)} [{len(ok)}]" if ok else "- [0]"
                        rows2.append([b, c, lg, n, comment_ok_cell,
                                     pct(sum(x["delimiter_ok"] for x in ms), n), pct(vac, n)])
                out.append(_table(["backend", "condition", "language", "n", "comment_ok [95% CI] [n scored]",
                                  "delimiter_ok", "vacuous (n_checks=0)"], rows2))
            # paired comparison against the baseline condition, per unit (repeats averaged)
            conds = sorted({r["condition"] for r in pr}, key=_cond_key)
            base = baseline if baseline in conds else ("none" if "none" in conds else conds[0])
            if len(conds) > 1:
                metrics = ["core_ok", "exact_match"] if task == "rename" else ["comment_ok"]
                rows, pvals = [], []
                for bk in sorted({r["backend"] for r in pr}):
                    for mt in metrics:
                        rate = defaultdict(list)
                        for r in pr:
                            v = r["metrics"].get(mt)
                            if r["backend"] == bk and v is not None:
                                rate[(r["unit_id"], r["condition"])].append(bool(v))
                        for c in conds:
                            if c == base:
                                continue
                            up = dn = tie = 0
                            deltas = []
                            for uid in sorted({u for (u, cd) in rate if cd == c}):
                                if (uid, base) not in rate:
                                    continue
                                rc, rb = mean(rate[(uid, c)]), mean(rate[(uid, base)])
                                deltas.append(rc - rb)
                                up += rc > rb
                                dn += rc < rb
                                tie += rc == rb
                            if deltas:
                                p = sign_test_p(up, dn)
                                pvals.append(p)
                                rows.append([bk, f"{c} vs {base}", mt, len(deltas), up, dn, tie,
                                             f"{100 * mean(deltas):+.1f}", f"{p:.3g}"])
                if rows:
                    for row, ap in zip(rows, holm(pvals)):
                        row.append(f"{ap:.3g}")
                    out += ["", f"### Paired comparison against `{base}` (per unit, repeats averaged; exact two-sided sign test)",
                            "", _table(["backend", "comparison", "metric", "units", "better", "worse", "tied",
                                       "mean diff (pp)", "p", "p (Holm)"], rows),
                            "", "`better`/`worse` count units. `p (Holm)` corrects for all comparisons in this table; "
                            "only hypotheses written in HYPOTHESES.md before the test run are confirmatory."]
    out += _oracle_free_section(recs)
    if errors:
        out += ["", f"## Trials that only have errors ({len(errors)})", ""] + [f"- `{k}`" for k in errors[:20]]
        if len(errors) > 20:
            out.append(f"- ... and {len(errors) - 20} more (see trials.jsonl; rerun with the same --run-id to retry)")
    return "\n".join(out) + "\n"


def _oracle_free_section(recs: list) -> list:
    """Kind inference and scope check of runs started with --no-oracle (empty list for the other runs)."""
    rs = [r for r in recs if "kind_status" in r]
    if not rs:
        return []
    out = ["", "## No-oracle diagnostics", "",
           "The identifier kind in these prompts was inferred from the code, not read from the benchmark. "
           "`kind matches` compares the inferred kind with the benchmark's kind (grading only); "
           "scope verdicts are those of `check_rename` for the model's suggestion (an unchanged name is not checked).", ""]
    rows = []
    in_pack = any("kind_in_pack" in r for r in rs)          # only runs of the Vol. 2 packs record it
    for c in sorted({r["condition"] for r in rs}, key=_cond_key):
        g = [r for r in rs if r["condition"] == c]
        n = len(g)
        sc = [r["scope"]["verdict"] for r in g if r.get("scope") and r["scope"]["verdict"] in ("ok", "conflict", "unchecked")]
        row = [c, n, pct(sum(bool(r["kind_ok"]) for r in g), n),
               pct(sum(r["kind_inferred"] is None for r in g), n)]
        if in_pack:
            row.append(pct(sum(r.get("kind_in_pack") is False for r in g), n))
        rows.append(row + [len(sc), pct(sc.count("ok"), len(sc)), pct(sc.count("conflict"), len(sc)),
                           pct(sc.count("unchecked"), len(sc))])
    head = ["condition", "trials", "kind matches", "kind unknown"] + (["kind outside pack"] if in_pack else [])
    out.append(_table(head + ["scope-checked", "scope ok", "scope conflict", "unchecked"], rows))
    return out


def _flat(r: dict) -> dict:
    m = r.get("metrics", {})
    row = {k: r.get(k) for k in ("key", "pack", "task", "unit_id", "snippet_id", "language", "standard_id", "kind",
                                 "condition", "condition_base", "backend", "model", "repeat", "rule_id", "original", "injected",
                                 "injection", "name", "prompt_chars", "prompt_tokens", "completion_tokens",
                                 "latency_s", "cost_usd", "finish")}
    for k in ("kind_used", "kind_inferred", "kind_status", "kind_ok", "kind_in_pack"):
        if k in r:
            row[k] = r[k]
    if r.get("scope"):
        row["scope_verdict"] = r["scope"].get("verdict")
    row["retrieved_n"] = (r.get("retrieval") or {}).get("n_items")
    row["retrieval_hit"] = (r.get("retrieval") or {}).get("hit")
    for k, v in m.items():
        if k in ("comment", "violated_rule_reasons"):
            continue
        row["m_" + k] = ";".join(map(str, v)) if isinstance(v, list) else v
    return row


def write_reports(run_dirs, out_dir: str | None = None, baseline: str | None = None) -> str:
    if isinstance(run_dirs, str):
        run_dirs = [run_dirs]
    out_dir = out_dir or run_dirs[0]
    os.makedirs(out_dir, exist_ok=True)
    recs, errors = load_trials(run_dirs, label_variants=True)
    rows = [_flat(r) for r in sorted(recs, key=lambda r: r["key"])]
    if rows:
        cols = []
        for r in rows:
            for k in r:
                if k not in cols:
                    cols.append(k)
        with open(os.path.join(out_dir, "trials.csv"), "w", encoding="utf-8-sig", newline="") as f:
            w = csv.DictWriter(f, fieldnames=cols)
            w.writeheader()
            w.writerows(rows)
    notes = []
    for d in run_dirs:
        cp = os.path.join(d, "config.json")
        if os.path.exists(cp):
            try:
                with open(cp, "r", encoding="utf-8") as f:
                    cfg = json.load(f)
            except (OSError, json.JSONDecodeError):
                continue
            fz = cfg.get("frozen")
            if fz:
                notes.append(f"Run `{cfg.get('run_id')}` ({cfg.get('split')} split) was started from freeze "
                             f"`{fz.get('file')}` (sha256 {str(fz.get('sha256'))[:12]})"
                             + (" - **this is a RERUN of the test split**" if fz.get("rerun") else "") + ".")
    md = summarize(recs, errors, baseline, notes)
    with open(os.path.join(out_dir, "summary.md"), "w", encoding="utf-8") as f:
        f.write(md)
    return md
