# Athena Sim summary

210 successful trials, 0 trial keys with only errors. Rates are per trial; repeats of the same unit are pooled (treat CIs and p-values as exploratory).

Split: test.

> Run `s2test_gemma4_local_s2_godot-s2_infer` (test split) was started from freeze `frozen_godot-s2_gemma4_local_s2_infer.json` (sha256 c954ea07217a).

## rename - pack `godot-s2`

### By condition and backend

| backend | condition | n | parsed | exact match [95% CI] | violated rule ok | all core rules ok [95% CI] | type prefix kept | collision | similarity idx before -> after | retrieval hit | latency s | tokens in/out | cost USD |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| openai:gemma-4-26b-a4b-it-ud-q4_k_m | graph[infer] | 210 | 99.5% | 82.4% [77-87] | 87.6% | 87.6% [82-91] | - | 2.9% | 0.990 -> 0.997 | 81.4% | 3.40 | 120054/31362 | - |

### By language (all core rules ok; n in brackets)

| backend | condition | cpp |
|---|---|---|
| openai:gemma-4-26b-a4b-it-ud-q4_k_m | graph[infer] | 87.6% [210] |

## No-oracle diagnostics

The identifier kind in these prompts was inferred from the code, not read from the benchmark. `kind matches` compares the inferred kind with the benchmark's kind (grading only); scope verdicts are those of `check_rename` for the model's suggestion (an unchanged name is not checked).

| condition | trials | kind matches | kind unknown | kind outside pack | scope-checked | scope ok | scope conflict | unchecked |
|---|---|---|---|---|---|---|---|---|
| graph[infer] | 210 | 81.4% | 0.0% | 0.0% | 209 | 97.1% | 2.9% | 0.0% |
