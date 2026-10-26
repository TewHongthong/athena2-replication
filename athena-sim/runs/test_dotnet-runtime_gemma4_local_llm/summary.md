# Athena Sim summary

210 successful trials, 0 trial keys with only errors. Rates are per trial; repeats of the same unit are pooled (treat CIs and p-values as exploratory).

Split: test.

> Run `test_dotnet-runtime_gemma4_local_llm` (test split) was started from freeze `frozen_dotnet-runtime_gemma4_local_llm.json` (sha256 0c1b110eee59).

## rename - pack `dotnet-runtime`

### By condition and backend

| backend | condition | n | parsed | exact match [95% CI] | violated rule ok | all core rules ok [95% CI] | type prefix kept | collision | similarity idx before -> after | retrieval hit | latency s | tokens in/out | cost USD |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| openai:gemma-4-26b-a4b-it-ud-q4_k_m | graph[llm] | 210 | 100.0% | 98.6% [96-100] | 100.0% | 100.0% [98-100] | - | 0.0% | 0.988 -> 1.000 | - | 2.55 | 99900/23298 | - |

### By language (all core rules ok; n in brackets)

| backend | condition | csharp |
|---|---|---|
| openai:gemma-4-26b-a4b-it-ud-q4_k_m | graph[llm] | 100.0% [210] |
