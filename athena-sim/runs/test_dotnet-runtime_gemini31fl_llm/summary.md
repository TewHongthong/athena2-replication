# Athena Sim summary

210 successful trials, 0 trial keys with only errors. Rates are per trial; repeats of the same unit are pooled (treat CIs and p-values as exploratory).

Split: test.

> Run `test_dotnet-runtime_gemini31fl_llm` (test split) was started from freeze `frozen_dotnet-runtime_gemini31fl_llm.json` (sha256 4a55ddea4de8).

## rename - pack `dotnet-runtime`

### By condition and backend

| backend | condition | n | parsed | exact match [95% CI] | violated rule ok | all core rules ok [95% CI] | type prefix kept | collision | similarity idx before -> after | retrieval hit | latency s | tokens in/out | cost USD |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| openai:google/gemini-3.1-flash-lite | graph[llm] | 210 | 100.0% | 99.5% [97-100] | 100.0% | 100.0% [98-100] | - | 0.0% | 0.988 -> 1.000 | - | 1.25 | 97170/25133 | 0.0620 |

### By language (all core rules ok; n in brackets)

| backend | condition | csharp |
|---|---|---|
| openai:google/gemini-3.1-flash-lite | graph[llm] | 100.0% [210] |
