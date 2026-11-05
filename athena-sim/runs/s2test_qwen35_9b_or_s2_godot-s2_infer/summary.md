# Athena Sim summary

210 successful trials, 0 trial keys with only errors. Rates are per trial; repeats of the same unit are pooled (treat CIs and p-values as exploratory).

Split: test.

> Run `s2test_qwen35_9b_or_s2_godot-s2_infer` (test split) was started from freeze `frozen_godot-s2_qwen35_9b_or_s2_infer.json` (sha256 7a98042784ca).

## rename - pack `godot-s2`

### By condition and backend

| backend | condition | n | parsed | exact match [95% CI] | violated rule ok | all core rules ok [95% CI] | type prefix kept | collision | similarity idx before -> after | retrieval hit | latency s | tokens in/out | cost USD |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| openai:qwen/qwen3.5-9b | graph[infer] | 210 | 99.5% | 74.3% [68-80] | 82.4% | 82.4% [77-87] | - | 1.4% | 0.990 -> 0.992 | 81.4% | 6.16 | 112389/44927 | 0.0180 |

### By language (all core rules ok; n in brackets)

| backend | condition | cpp |
|---|---|---|
| openai:qwen/qwen3.5-9b | graph[infer] | 82.4% [210] |

## No-oracle diagnostics

The identifier kind in these prompts was inferred from the code, not read from the benchmark. `kind matches` compares the inferred kind with the benchmark's kind (grading only); scope verdicts are those of `check_rename` for the model's suggestion (an unchanged name is not checked).

| condition | trials | kind matches | kind unknown | kind outside pack | scope-checked | scope ok | scope conflict | unchecked |
|---|---|---|---|---|---|---|---|---|
| graph[infer] | 210 | 81.4% | 0.0% | 0.0% | 209 | 98.6% | 1.4% | 0.0% |
