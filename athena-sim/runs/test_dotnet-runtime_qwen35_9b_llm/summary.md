# Athena Sim summary

210 successful trials, 0 trial keys with only errors. Rates are per trial; repeats of the same unit are pooled (treat CIs and p-values as exploratory).

Split: test.

> Run `test_dotnet-runtime_qwen35_9b_llm` (test split) was started from freeze `frozen_dotnet-runtime_qwen35_9b_llm.json` (sha256 55b152a6cd7a).

## rename - pack `dotnet-runtime`

### By condition and backend

| backend | condition | n | parsed | exact match [95% CI] | violated rule ok | all core rules ok [95% CI] | type prefix kept | collision | similarity idx before -> after | retrieval hit | latency s | tokens in/out | cost USD |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| openai:qwen3.5-9b-ud-q8_k_xl | graph[llm] | 210 | 100.0% | 97.1% [94-99] | 98.6% | 98.6% [96-100] | - | 0.0% | 0.988 -> 1.000 | - | 6.15 | 94635/26314 | - |

### By language (all core rules ok; n in brackets)

| backend | condition | csharp |
|---|---|---|
| openai:qwen3.5-9b-ud-q8_k_xl | graph[llm] | 98.6% [210] |
