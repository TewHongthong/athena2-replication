# Athena Sim summary

210 successful trials, 0 trial keys with only errors. Rates are per trial; repeats of the same unit are pooled (treat CIs and p-values as exploratory).

Split: test.

> Run `test_odoo_gemma4_local_infer` (test split) was started from freeze `frozen_odoo_gemma4_local_infer.json` (sha256 ca43dfa8e071).

## rename - pack `odoo`

### By condition and backend

| backend | condition | n | parsed | exact match [95% CI] | violated rule ok | all core rules ok [95% CI] | type prefix kept | collision | similarity idx before -> after | retrieval hit | latency s | tokens in/out | cost USD |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| openai:gemma-4-26b-a4b-it-ud-q4_k_m | graph[infer] | 210 | 100.0% | 98.6% [96-100] | 100.0% | 100.0% [98-100] | - | 0.0% | 0.956 -> 1.000 | 100.0% | 2.52 | 106431/22687 | - |

### By language (all core rules ok; n in brackets)

| backend | condition | python |
|---|---|---|
| openai:gemma-4-26b-a4b-it-ud-q4_k_m | graph[infer] | 100.0% [210] |

## No-oracle diagnostics

The identifier kind in these prompts was inferred from the code, not read from the benchmark. `kind matches` compares the inferred kind with the benchmark's kind (grading only); scope verdicts are those of `check_rename` for the model's suggestion (an unchanged name is not checked).

| condition | trials | kind matches | kind unknown | kind outside pack | scope-checked | scope ok | scope conflict | unchecked |
|---|---|---|---|---|---|---|---|---|
| graph[infer] | 210 | 100.0% | 0.0% | 0.0% | 210 | 100.0% | 0.0% | 0.0% |
