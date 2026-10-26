# Athena-2 replication package

Replication package of "Does Ontology-Guided Rule Selection Generalize to Independent Coding Standards?".
It holds the harness, the registered hypotheses and their freeze, the ontologies, the model pins, the trial
records of every run, the benchmark files, and the scripts and outputs of the analyses.

## Contents

- HYPOTHESES_v2.md: the registered hypotheses and analysis plan; its hash is stored in every freeze file.
- ADDENDUM_v2.md: the analysis steps added after the freeze (A1 to A6).
- athena-sim/: the harness; packs/ (human and LLM-drafted ontologies, core rules, the prompt used to draft them);
  frozen_*.json and their ledgers; runs/ (test_*, canary_*, pilot_*); the analysis scripts; tests/.
- athena-corpus/: pins/ (commit, path and git blob identifier of every file), curation/ (including
  tools/fetch_corpus_pins.py and tools/export_tasks.py), corpus_index.tsv.
- models/: model_pins.json (request settings of the hosted models, file hashes of the local models) and README.md.
- ontology/, standards/: the ontology schema and loader, and the pinned standard documents with their licenses.
- benchmark/: the benchmark of each pack (100 tasks per pack: 30 development, 70 test).
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

## License

Code: MIT (LICENSE). Ontologies and standard documents: the license of the source document, and code excerpts: the
license of their repository (THIRD_PARTY_NOTICES.md).
