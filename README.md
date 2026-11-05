# Athena-2 replication package

Replication package of "Rule Selection from a Coding-Standard Ontology: A Pre-Registered Study of Identifier Naming on Three Project Standards".
It holds the harness, the registered hypotheses and their freeze, the ontologies, the model pins, the trial
records of every run, the benchmark files, and the scripts and outputs of the analyses.

## Contents

- HYPOTHESES_v2.md: the registered hypotheses and analysis plan; its hash is stored in every freeze file.
- ADDENDUM_v2.md: the analysis steps added after the freeze (A1 to A14).
- athena-sim/: the harness; packs/ (human and LLM-drafted ontologies, core rules, the prompt used to draft them);
  frozen_*.json and their ledgers; runs/ (test_*, canary_*, pilot_*); the analysis scripts; tests/.
- athena-corpus/: pins/ (commit, path and git blob identifier of every file), curation/ (including
  tools/fetch_corpus_pins.py and tools/export_tasks.py), corpus_index.tsv.
- models/: model_pins.json (request settings of the hosted models, file hashes of the local models) and README.md.
- ontology/, standards/: the ontology schema and loader, and the pinned standard documents with their licenses.
- benchmark/: the benchmark of each pack (100 tasks per pack: 30 development, 70 test). The curation report is benchmark/CURATION_REPORT.md.
- analysis/: outputs of the analyses (renames.csv, renames_all.csv, h6.md, dose.md, dose.json, and the tables).
- LICENSE, THIRD_PARTY_NOTICES.md, SHA256SUMS.txt.

## Not included

The source files of the three repositories. The corpus is rebuilt from the pinned commits:

    python3 athena-corpus/curation/tools/fetch_corpus_pins.py --out corpus_v2

Every fetched file is checked against the git blob identifier recorded in athena-corpus/pins/. The script needs git
and network access on the first run. Odoo (LGPL-3.0) is distributed as commit, path and script only.

## Checking the package

    sha256sum -c SHA256SUMS.txt

## Reproducing the analyses (no API key needed)

Run from athena-sim/. The trial records of the test runs are in runs/test_<pack>_<model>_<meta|llm|infer>/trials.jsonl.

    export ATHENA_V2_BENCH=../benchmark
    python3 athena_sim.py report runs/test_*
    python3 analyse_confirmatory.py runs/test_* --models luna,gemini,qwen3.5-9b,gemma-4
    python3 analyse_secondary.py h2 runs/test_*_meta
    python3 analyse_secondary.py h4 --human runs/test_*_meta --llm runs/test_*_llm --agreement-root
    python3 analyse_secondary.py h5 --metadata runs/test_*_meta --inferred runs/test_*_infer
    python3 analyse_secondary.py h6 --labels ../analysis/renames.csv
    python3 analyse_secondary.py dose runs/test_*_meta

HYPOTHESES_v2.md (section 6) and ADDENDUM_v2.md (A1) explain the options. The labelled cases of the scope-aware check
are made by make_h6_labels.py; the hand-written conflict cases are in the same script.

## Running the models again

This needs API keys for the hosted models and a llama.cpp server for the two local models (models/README.md and
Appendix D of the paper). A test run refuses to start if a pinned file changed since its freeze, and a second run of
the test split needs --allow-rerun.

## Requirements

Python 3.12 or later (under Python 3.10, five Odoo files that hold 57 of the 1,680 units cannot be parsed),
networkx 3.4 or later, and git. The tree-sitter library athena-corpus/curation/libtsall.so is built for Linux x86-64;
its build script is in the same folder.

## Study 2 (registered amendment)

HYPOTHESES_v2_study2.md registers a second study of Vol. 2, written after the results of the registered study were known; it was added to this package before the benchmark of Study 2 was built. The additions to its plan are in ADDENDUM_study2.md (S2-A1 to S2-A13), and every command of Study 2 is in athena-sim/README_study2.md.

Study 2 adds: the harness (athena-sim/athena2_s2.py, athena-sim/athena_s2/); the packs (athena-sim/packs/godot-s2/, athena-sim/packs/dotnet-runtime-s2/); the benchmark construction (athena-corpus/curation/facets_s2.py, kind_infer_s2.py, tools/*_s2.py); the benchmark (benchmark/godot-s2/, benchmark/dotnet-runtime-s2/); the model pins (models/model_pins_s2.json, models/model_pins_s2_or.json); the frozen setups (athena-sim/frozen_*-s2_*.json with their ledgers); the runs (athena-sim/runs/s2dev_*, s2canary_*, s2test_*); the analysis (athena-sim/analyse_study2.py, analyse_s2_a12.py, analyse_s2_a13.py and their outputs in analysis/); and the tests (athena-sim/tests_s2/, athena-corpus/curation/tests_s2/).

The runs of qwen35_9b_s2 under s2test_ and s2canary_before_ are the local runs of Qwen3.5-9B that stopped when the serving machine failed; they are kept and are not read by the analysis, which uses the hosted runs of qwen35_9b_or_s2 (ADDENDUM_study2.md, S2-A11). To reproduce the analysis, run the commands of athena-sim/README_study2.md from athena-sim/ with ATHENA_S2_BENCH set to the folder benchmark/ of this package.

## License

Code: MIT (LICENSE). Ontologies and standard documents: the license of the source document, and code excerpts: the
license of their repository (THIRD_PARTY_NOTICES.md).

## Additional analyses after the freeze
ADDENDUM_v2.md records every step taken after the freeze (A1-A14). Eight of them have their own scripts, and one further script draws the figures of the paper:
  python3 count_godot_prefix.py runs/test_godot_*_meta    (A8)
  python3 analyse_a9.py --meta runs/test_*_meta --llm runs/test_*_llm --labels ../analysis/renames_all.csv --out ../analysis/a9.md --json ../analysis/a9.json    (A9)
  python3 repair_baseline.py --meta runs/test_*_meta --out ../analysis/a10.md --json ../analysis/a10.json    (A10)
  python3 analyse_a11.py --meta runs/test_*_meta --out ../analysis/a11.md --json ../analysis/a11.json    (A11)
  python3 analyse_a12.py --meta runs/test_*_meta --llm runs/test_*_llm --out ../analysis/a12.md --json ../analysis/a12.json    (A12)
  python3 analyse_a13.py --meta runs/test_*_meta --infer runs/test_*_infer --canary runs/canary_before_* runs/canary_after_* --supplementary runs/pilot_tank* --anchors runs/anchor_* --out ../analysis/a13.md --json ../analysis/a13.json    (A13)
  python3 analyse_a14.py --meta runs/test_*_meta --out ../analysis/a14.md --json ../analysis/a14.json    (A14)
  python3 make_figures.py --a13 ../analysis/a13.json --out ../figures    (the two figures of the paper)
The commands are run in athena-sim/. Their outputs are in analysis/ (a9.md, a9.json, a10.md, a10.json, a11.md, a11.json, a12.md, a12.json, a13.md, a13.json, a14.md, a14.json).
  python3 make_blind_sheet.py --out-dir DIR    and    python3 score_blind.py --sheet SHEET --key KEY --report REPORT    (A7)
The files of the review of the verdicts of core_ok are in analysis/blind*/. Only the third round is used as evidence; the first two rounds are kept for the record (ADDENDUM_v2.md, A7).
The labels of A14 are in analysis/a14_rule_sources.csv. They were given in a form that mark_a14.py makes and reads
(python3 mark_a14.py --make-form FORM.xlsx, then --read-form FORM.xlsx; the form needs openpyxl), and the same
script can be answered in the terminal (python3 mark_a14.py). python3 analyse_a14.py --check validates the labels and
looks up their quotes in the pinned documents when standards/src exists (fetch_standards.py).
