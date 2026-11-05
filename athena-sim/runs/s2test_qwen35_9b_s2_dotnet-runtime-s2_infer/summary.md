# Athena Sim summary

135 successful trials, 0 trial keys with only errors. Rates are per trial; repeats of the same unit are pooled (treat CIs and p-values as exploratory).

Split: test.

> Run `s2test_qwen35_9b_s2_dotnet-runtime-s2_infer` (test split) was started from freeze `frozen_dotnet-runtime-s2_qwen35_9b_s2_infer.json` (sha256 97eb50bd53e3).

## rename - pack `dotnet-runtime-s2`

### By condition and backend

| backend | condition | n | parsed | exact match [95% CI] | violated rule ok | all core rules ok [95% CI] | type prefix kept | collision | similarity idx before -> after | retrieval hit | latency s | tokens in/out | cost USD |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| openai:qwen3.5-9b-ud-q8_k_xl | graph[infer] | 135 | 99.3% | 94.1% [89-97] | 99.3% | 99.3% [96-100] | - | 0.0% | 0.997 -> 1.000 | 100.0% | 7.59 | 80421/21035 | - |

### By language (all core rules ok; n in brackets)

| backend | condition | csharp |
|---|---|---|
| openai:qwen3.5-9b-ud-q8_k_xl | graph[infer] | 99.3% [135] |

## No-oracle diagnostics

The identifier kind in these prompts was inferred from the code, not read from the benchmark. `kind matches` compares the inferred kind with the benchmark's kind (grading only); scope verdicts are those of `check_rename` for the model's suggestion (an unchanged name is not checked).

| condition | trials | kind matches | kind unknown | kind outside pack | scope-checked | scope ok | scope conflict | unchecked |
|---|---|---|---|---|---|---|---|---|
| graph[infer] | 135 | 100.0% | 0.0% | 0.0% | 134 | 100.0% | 0.0% | 0.0% |
