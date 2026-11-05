# Athena Sim summary

135 successful trials, 0 trial keys with only errors. Rates are per trial; repeats of the same unit are pooled (treat CIs and p-values as exploratory).

Split: test.

> Run `s2test_luna_dotnet-runtime-s2_infer` (test split) was started from freeze `frozen_dotnet-runtime-s2_luna_infer.json` (sha256 68bc6e41a298).

## rename - pack `dotnet-runtime-s2`

### By condition and backend

| backend | condition | n | parsed | exact match [95% CI] | violated rule ok | all core rules ok [95% CI] | type prefix kept | collision | similarity idx before -> after | retrieval hit | latency s | tokens in/out | cost USD |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| openai:openai/gpt-6-luna | graph[infer] | 135 | 100.0% | 91.9% [86-95] | 100.0% | 100.0% [97-100] | - | 0.0% | 0.997 -> 0.999 | 100.0% | 3.27 | 75243/18964 | 0.0170 |

### By language (all core rules ok; n in brackets)

| backend | condition | csharp |
|---|---|---|
| openai:openai/gpt-6-luna | graph[infer] | 100.0% [135] |

## No-oracle diagnostics

The identifier kind in these prompts was inferred from the code, not read from the benchmark. `kind matches` compares the inferred kind with the benchmark's kind (grading only); scope verdicts are those of `check_rename` for the model's suggestion (an unchanged name is not checked).

| condition | trials | kind matches | kind unknown | kind outside pack | scope-checked | scope ok | scope conflict | unchecked |
|---|---|---|---|---|---|---|---|---|
| graph[infer] | 135 | 100.0% | 0.0% | 0.0% | 135 | 100.0% | 0.0% | 0.0% |
