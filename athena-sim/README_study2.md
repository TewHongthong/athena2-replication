# Study 2: commands

Study 2 is registered in `../HYPOTHESES_v2_study2.md`. This file lists the commands of its procedure (Section 6 of
that file) and the commands of its analysis. It was written before the freeze, and the analysis is computed with the
commands below and no other options.

Notation: PACK is `godot-s2` or `dotnet-runtime-s2`; PIN is `luna`, `gemini31fl`, `qwen35_9b_s2` or
`gemma4_local_s2`; FAMILY is `meta` or `infer`. For each pack, LANG is `cpp` or `csharp`, STD is `godot` or
`dotnet-runtime`, and ONTO is `godot_ontology.json` or `dotnet_ontology.json`.

The commands of the harness are run from `athena-sim`, with `ATHENA_S2_BENCH` set to the folder that holds one
benchmark folder per pack. `athena2_s2.py` takes the commands and options of `athena_sim.py` and reads the model
pins from `../models/model_pins_s2.json`. The embedding pin, its server and the serving of the local models are
described in `../models/README.md`.

## Benchmark (Section 6, step 3)

From `athena-corpus/curation`, for each pack, with `O=$ATHENA_S2_BENCH/PACK` and `P=../../athena-sim/packs/PACK`:

```
python3 tools/build_pool_s2.py --pack PACK --language LANG --corpus ../corpus_v2 --ontology $P/ONTO --core $P/core_rules.json --out-dir $O/pool
python3 tools/select_tasks_s2.py --pack PACK --pool $O/pool/PACK_pool.tsv --out-dir $O/sel
python3 tools/export_tasks_s2.py --pack PACK --language LANG --selection $O/sel/PACK_selection.tsv --pool-units $O/pool/PACK_pool_units.jsonl --ontology $P/ONTO --core $P/core_rules.json --out-dir $O/bench --study1-tasks <Study 1 benchmark of STD>/tasks.tsv
python3 tools/validate_benchmark_s2.py --benchmark $O/bench --corpus ../corpus_v2 --ontology $P/ONTO --languages LANG --core $P/core_rules.json
```

The pool, the selection and the method of every task are deterministic; `--study1-tasks` only adds the overlap with
the Study 1 tasks to `study2_report.json`. Family options of the commands below:

- meta: `--conditions none,fulldoc,naming,chunk,bm25,dense,graph --embed-pin qwen3_embedding_06b`
- infer: `--conditions graph --no-oracle`

## Development round and eligibility (Section 6, step 5; Section 2.3)

```
python athena2_s2.py run --pack PACK --model-pin PIN --split dev --per-language 0 --repeats 1 --seed 42 <family options> --run-id s2dev_PIN_PACK_FAMILY
python analyse_study2.py runs/s2dev_* --compare-split dev
```

The eligibility table of the report decides which standards enter H1-S2. With `--compare-split dev` the comparisons
are computed on the development round as a check of the procedure; they are not results.

## Freeze (Section 6, step 6)

Once for each (PACK, PIN, FAMILY), 16 files:

```
python athena2_s2.py freeze --pack PACK --model-pin PIN --split test --per-language 0 --repeats 3 --seed 42 <family options> --out-file frozen_PACK_PIN_FAMILY.json
```

The freeze records the code of Study 1 and of Study 2 (`athena_s2/*.py`, including the analysis, and
`athena2_s2.py`), the pack, the settings, the pins and `HYPOTHESES_v2_study2.md`. A test run that differs in any of
them does not start.

## Canary and test (Section 6, step 7)

Before the first test trial of a model, for each PACK:

```
python athena2_s2.py run --pack PACK --model-pin PIN --split dev --conditions none --per-language 0 --repeats 1 --seed 42 --run-id s2canary_before_PIN_PACK
```

Test, once for each (PACK, PIN, FAMILY), with the options of its freeze:

```
python athena2_s2.py run --pack PACK --model-pin PIN --split test --per-language 0 --repeats 3 --seed 42 <family options> --frozen frozen_PACK_PIN_FAMILY.json --run-id s2test_PIN_PACK_FAMILY
```

A run that stops is resumed with the same `--run-id`. A second run of the test split needs `--allow-rerun` and is
reported as a rerun. After the last test trial of a model, the canary command is run again with
`--run-id s2canary_after_PIN_PACK`. The canary set is every dev task of the two packs (30 and 19).

Qwen3.5-9B ran its test round on the hosted pin `qwen35_9b_or_s2` (ADDENDUM_study2.md, S2-A11). Its freeze,
canary and test commands are those above with PIN = qwen35_9b_or_s2 and `--pins ../models/model_pins_s2_or.json`
added; its four frozen setups are `frozen_PACK_qwen35_9b_or_s2_FAMILY.json`.

## Analysis (Section 6, step 8)

```
python analyse_study2.py runs/s2dev_* runs/s2test_luna_* runs/s2test_gemini31fl_* runs/s2test_gemma4_local_s2_* runs/s2test_qwen35_9b_or_s2_* --canary runs/s2canary_*_luna_* runs/s2canary_*_gemini31fl_* runs/s2canary_*_gemma4_local_s2_* runs/s2canary_*_qwen35_9b_or_s2_* --out ../analysis/study2.md --json ../analysis/study2.json
```

The run folders are named so that the incomplete local test runs of Qwen3.5-9B (`qwen35_9b_s2`) and its local
canary are left out; the hosted runs of `qwen35_9b_or_s2` take their place (ADDENDUM_study2.md, S2-A11).

The files in `../analysis/` were written under Python 3.10. Under Python 3.12 or later, `sum()` adds floating-point
numbers with compensation, so some cost values in `study2.json` differ in the last digits; `study2.md`,
`s2_a12.*` and `s2_a13.*` are identical.

One report holds the eligibility, H1-S2 to H4-S2 with their verdicts, the drift check, the sensitivity analysis
without a flagged model, and the reports of Sections 2.2 and 4 of the amendment (Study 1 core_ok, the required
prefix, exact_match, tokens and cost, trials at the output limit, tasks whose snippet shows the required prefix on
another identifier, the agreement of the inferred kind with metadata, and the reference program). The rules for
reading the trials are in `athena_s2/analysis.py`: the family of a run comes from its `config.json`; when a key was
written more than once, the first record without an error by time stamp is used and the others are counted; the
canary runs are given with `--canary` only, because they share their keys with the development round.

## Descriptive counts in the addendum
python analyse_s2_a12.py --out ../analysis/s2_a12.md --json ../analysis/s2_a12.json
python analyse_s2_a13.py --out ../analysis/s2_a13.md --json ../analysis/s2_a13.json

`analyse_s2_a12.py` compares the local and the hosted deployment of Qwen3.5-9B on its canary before (S2-A12);
`analyse_s2_a13.py` counts the kind that the condition with the inferred kind used on the test tasks (S2-A13). Both
read the trials with the rules of `athena_s2/analysis.py`, and neither enters a hypothesis.

## Tests

```
python3 -m unittest discover -s tests_s2                        (athena-sim)
python3 -m unittest discover -s tests_s2                        (athena-corpus/curation)
```
