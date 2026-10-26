# Athena Sim summary

210 successful trials, 0 trial keys with only errors. Rates are per trial; repeats of the same unit are pooled (treat CIs and p-values as exploratory).

Split: test.

> Run `test_godot_gemini31fl_infer` (test split) was started from freeze `frozen_godot_gemini31fl_infer.json` (sha256 c0304d93d642).

## rename - pack `godot`

### By condition and backend

| backend | condition | n | parsed | exact match [95% CI] | violated rule ok | all core rules ok [95% CI] | type prefix kept | collision | similarity idx before -> after | retrieval hit | latency s | tokens in/out | cost USD |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| openai:google/gemini-3.1-flash-lite | graph[infer] | 210 | 100.0% | 88.1% [83-92] | 100.0% | 100.0% [98-100] | - | 0.0% | 0.931 -> 0.998 | 98.6% | 1.36 | 114951/27272 | 0.0696 |

### By language (all core rules ok; n in brackets)

| backend | condition | cpp |
|---|---|---|
| openai:google/gemini-3.1-flash-lite | graph[infer] | 100.0% [210] |

## No-oracle diagnostics

The identifier kind in these prompts was inferred from the code, not read from the benchmark. `kind matches` compares the inferred kind with the benchmark's kind (grading only); scope verdicts are those of `check_rename` for the model's suggestion (an unchanged name is not checked).

| condition | trials | kind matches | kind unknown | kind outside pack | scope-checked | scope ok | scope conflict | unchecked |
|---|---|---|---|---|---|---|---|---|
| graph[infer] | 210 | 98.6% | 0.0% | 0.0% | 210 | 100.0% | 0.0% | 0.0% |
