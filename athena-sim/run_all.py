#!/usr/bin/env python3
"""Run the pre-registered TEST sets of plan A (see HYPOTHESES.md) in order, with a budget guard.

  python run_all.py --dry-run                 # only print what would run (no key needed, nothing is written)
  python run_all.py --budget 9.5              # real run; needs OPENAI_API_KEY (= your OpenRouter key)
  python run_all.py --only luna_p5_rename     # a single set

Plan A: o3-mini on GSCS (H1-H5), gpt-6-luna on GSCS (replication) and public5 (H6), all via OpenRouter.
No dev tuning: every set uses default prompts/retrieval settings, --repeats 3, --max-tokens 8192.

Safe to run again: an existing frozen_*.json is kept, finished sets are skipped, an interrupted set resumes
(same run id). This script only calls `athena_sim.py freeze` and `athena_sim.py run --split test --frozen ...`
and does not touch the Sim's code. Progress goes to the console and to runs/run_all.log.
"""
import argparse
import datetime
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
RUNS = os.path.join(HERE, "runs")
LOG = os.path.join(RUNS, "run_all.log")
BASE_URL = "https://openrouter.ai/api/v1"
REPEATS = 3
MAX_TOKENS = 8192

MODELS = {
    "o3mini": dict(backend="openai:openai/o3-mini", price_in=1.1, price_out=4.4),
    "luna": dict(backend="openai:openai/gpt-6-luna", price_in=0.1, price_out=0.5),
}
# (model, set, pack, task, per_language, estimated_cost_usd)  -- order = priority (H1 first)
PLAN_A = [
    ("o3mini", "gscs_rename", "gscs", "rename", 0, 6.1),
    ("o3mini", "gscs_comment", "gscs", "comment", 0, 0.9),
    ("luna", "gscs_rename", "gscs", "rename", 0, 0.35),
    ("luna", "gscs_comment", "gscs", "comment", 0, 0.05),
    ("luna", "p5_rename", "public5", "rename", 20, 1.0),
    ("luna", "p5_comment", "public5", "comment", 0, 1.0),
]


def now():
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def emit(msg, dry=False):
    line = "[%s] %s" % (now(), msg)
    print(line, flush=True)
    if not dry:
        os.makedirs(RUNS, exist_ok=True)
        with open(LOG, "a", encoding="utf-8") as f:
            f.write(line + "\n")


def run_cost(run_id):
    p = os.path.join(RUNS, run_id, "trials.jsonl")
    total = 0.0
    if os.path.exists(p):
        with open(p, encoding="utf-8") as f:
            for line in f:
                try:
                    total += float(json.loads(line).get("cost_usd") or 0)
                except (ValueError, TypeError):
                    pass
    return total


def is_done(frozen_path, run_id):
    p = frozen_path + ".ledger.jsonl"
    done = False
    if os.path.exists(p):
        with open(p, encoding="utf-8") as f:
            for line in f:
                try:
                    e = json.loads(line)
                except ValueError:
                    continue
                if e.get("run_id") == run_id and e.get("event") == "end":
                    done = e.get("status") == "complete" and not e.get("trials_error")
    return done


def call(cmd, dry):
    emit("$ " + subprocess.list2cmdline(cmd), dry)
    if dry:
        return 0
    env = dict(os.environ, PYTHONUTF8="1", PYTHONIOENCODING="utf-8")
    p = subprocess.Popen(cmd, cwd=HERE, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                         text=True, encoding="utf-8", errors="replace")
    with open(LOG, "a", encoding="utf-8") as lf:
        for line in p.stdout:
            line = line.rstrip("\n")
            print(line, flush=True)
            lf.write("    " + line + "\n")
    return p.wait()


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--budget", type=float, default=9.5, help="stop starting new sets when spent + estimate > budget (USD)")
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--only", help="run one set, e.g. o3mini_gscs_rename")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--yes", action="store_true", help="do not ask for confirmation")
    a = ap.parse_args()

    entries = []
    for model, sname, pack, task, per_lang, est in PLAN_A:
        sid = "%s_%s" % (model, sname)
        entries.append(dict(id=sid, model=model, pack=pack, task=task, per_lang=per_lang, est=est,
                            run_id="test_" + sid, frozen=os.path.join(HERE, "frozen_%s.json" % sid), **MODELS[model]))
    if a.only:
        entries = [e for e in entries if e["id"] == a.only]
        if not entries:
            sys.exit("unknown set: %s (choose from: %s)" % (a.only, ", ".join("%s_%s" % (m, s) for m, s, *_ in PLAN_A)))
    if not a.dry_run and not os.environ.get("OPENAI_API_KEY"):
        sys.exit("OPENAI_API_KEY is not set in this window (put your OpenRouter key in it first).")

    spent = sum(run_cost(e["run_id"]) for e in entries)
    print("\nPlan A (%s)   budget $%.2f   already spent by these sets $%.4f\n" % (BASE_URL, a.budget, spent))
    print("%-22s %-26s %-9s %s" % ("set", "backend", "est. $", "state"))
    for e in entries:
        state = "DONE" if is_done(e["frozen"], e["run_id"]) else ("resume" if os.path.exists(os.path.join(RUNS, e["run_id"])) else "new")
        print("%-22s %-26s %-9.2f %s" % (e["id"], e["backend"], e["est"], state))
    print("  (estimates: o3-mini ~$0.004/call, luna ~$0.0002/call at short prompts)\n")
    if not a.dry_run and not a.yes:
        if input("Start? [y/N] ").strip().lower() != "y":
            sys.exit("cancelled")

    skipped, failed = [], None
    try:
        for e in entries:
            rid, fz = e["run_id"], e["frozen"]
            if is_done(fz, rid):
                emit("SKIP %s: already complete" % e["id"], a.dry_run)
                continue
            remaining = max(e["est"] - run_cost(rid), 0.0)
            if spent + remaining > a.budget:
                emit("SKIP %s: spent $%.2f + est. $%.2f > budget $%.2f (re-run later with a higher --budget)"
                     % (e["id"], spent, remaining, a.budget), a.dry_run)
                skipped.append(e["id"])
                continue
            common = ["--pack", e["pack"], "--task", e["task"], "--backend", e["backend"],
                      "--per-language", str(e["per_lang"]), "--repeats", str(REPEATS),
                      "--max-tokens", str(MAX_TOKENS), "--base-url", BASE_URL]
            if not os.path.exists(fz):
                note = "plan A %s: default settings, no dev tuning, via OpenRouter (run_all.py)" % e["id"]
                rc = call([sys.executable, "athena_sim.py", "freeze"] + common +
                          ["--out-file", fz, "--note", note], a.dry_run)
                if rc:
                    failed = "%s: freeze failed (rc=%s)" % (e["id"], rc)
                    break
            emit("START %s (run id %s)" % (e["id"], rid), a.dry_run)
            rc = call([sys.executable, "athena_sim.py", "run"] + common +
                      ["--split", "test", "--workers", str(a.workers), "--max-errors", "10",
                       "--price-in", str(e["price_in"]), "--price-out", str(e["price_out"]),
                       "--frozen", fz, "--run-id", rid], a.dry_run)
            spent = sum(run_cost(x["run_id"]) for x in entries)
            emit("END %s rc=%s   this set $%.4f   total spent $%.4f" % (e["id"], rc, run_cost(rid), spent), a.dry_run)
            if rc:
                failed = "%s: run failed (rc=%s) - see the messages above; fix, then run this script again to resume" % (e["id"], rc)
                break
    except KeyboardInterrupt:
        emit("INTERRUPTED - progress is saved; run this script again to resume", a.dry_run)
        sys.exit(130)

    emit("SUMMARY total spent $%.4f of budget $%.2f; skipped: %s" % (spent, a.budget, ", ".join(skipped) or "none"), a.dry_run)
    if failed:
        emit("FAILED " + failed, a.dry_run)
        sys.exit(1)


if __name__ == "__main__":
    main()
