"""Extension of lookup_compare.py to the logged GSCS prompts of all six models (see ADDENDUM.md, Extension)."""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE); sys.path.insert(0, ROOT)
from lookup_compare import flatten, build_index, lookup_block, load_logged
from athena.packs import load_pack, select_split

RUNS = {"rename": ["runs/test_o3mini_gscs_rename", "runs/test_luna_gscs_rename", "qwen_plan_a/runs/qwen_gscs_rename",
                   "gemini31fl/runs/gemini31fl_gscs_rename", "dsv4f_v2/runs/dsv4f_gscs_rename", "gemma4/gemma4_gscs_rename"],
        "comment": ["runs/test_o3mini_gscs_comment", "runs/test_luna_gscs_comment", "qwen_plan_a/runs/qwen_gscs_comment",
                    "gemini31fl/runs/gemini31fl_gscs_comment", "dsv4f_v2/runs/dsv4f_gscs_comment", "gemma4/gemma4_gscs_comment"]}
os.chdir(ROOT)
pack = load_pack("gscs"); table = flatten(pack.ontology.path); index = build_index(table)
L = ["# Lookup vs logged graph prompts, GSCS, all six models", "", "| task | run | units identical / units | graph trials |", "|---|---|---|---|"]
tot_trials = tot_ok = 0
for task, dirs in RUNS.items():
    units = select_split(pack.rename_units() if task == "rename" else pack.comment_units(), "test")
    for d in dirs:
        logged = load_logged(d); ok = n = trials = 0
        for u in units:
            text, _, _ = lookup_block(table, index, standard=u.standard_id, language=u.language, kind=u.kind, task=task)
            tr = logged.get(u.unit_id, [])
            if not tr:
                continue
            n += 1; trials += len(tr); ok += all(b == text for _, b, _ in tr)
            tot_ok += sum(b == text for _, b, _ in tr)
        tot_trials += trials
        L.append(f"| {task} | {d} | {ok}/{n} | {trials} |")
L += ["", f"All graph trials identical: {tot_ok}/{tot_trials}"]
open(os.path.join(HERE, "results_allmodels.md"), "w", encoding="utf-8").write("\n".join(L) + "\n")
print("\n".join(L))
