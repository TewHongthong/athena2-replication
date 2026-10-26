# Athena Sim summary

210 successful trials, 0 trial keys with only errors. Rates are per trial; repeats of the same unit are pooled (treat CIs and p-values as exploratory).

Split: test.

> Run `test_dotnet-runtime_qwen35_9b_infer` (test split) was started from freeze `frozen_dotnet-runtime_qwen35_9b_infer.json` (sha256 b161f2bc9836).

## rename - pack `dotnet-runtime`

### By condition and backend

| backend | condition | n | parsed | exact match [95% CI] | violated rule ok | all core rules ok [95% CI] | type prefix kept | collision | similarity idx before -> after | retrieval hit | latency s | tokens in/out | cost USD |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| openai:qwen3.5-9b-ud-q8_k_xl | graph[infer] | 210 | 100.0% | 95.2% [91-97] | 98.6% | 98.6% [96-100] | - | 0.5% | 0.988 -> 1.000 | 100.0% | 6.12 | 93165/26084 | - |

### By language (all core rules ok; n in brackets)

| backend | condition | csharp |
|---|---|---|
| openai:qwen3.5-9b-ud-q8_k_xl | graph[infer] | 98.6% [210] |

## No-oracle diagnostics

The identifier kind in these prompts was inferred from the code, not read from the benchmark. `kind matches` compares the inferred kind with the benchmark's kind (grading only); scope verdicts are those of `check_rename` for the model's suggestion (an unchanged name is not checked).

| condition | trials | kind matches | kind unknown | kind outside pack | scope-checked | scope ok | scope conflict | unchecked |
|---|---|---|---|---|---|---|---|---|
| graph[infer] | 210 | 100.0% | 0.0% | 0.0% | 210 | 98.1% | 1.9% | 0.0% |
