# Athena Sim summary

30 successful trials, 0 trial keys with only errors. Rates are per trial; repeats of the same unit are pooled (treat CIs and p-values as exploratory).

Split: dev.

## rename - pack `dotnet-runtime`

### By condition and backend

| backend | condition | n | parsed | exact match [95% CI] | violated rule ok | all core rules ok [95% CI] | type prefix kept | collision | similarity idx before -> after | retrieval hit | latency s | tokens in/out | cost USD |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| openai:google/gemini-3.1-flash-lite | none | 30 | 100.0% | 90.0% [74-97] | 100.0% | 100.0% [89-100] | - | 0.0% | 0.987 -> 0.999 | - | 1.24 | 12146/3230 | 0.0079 |

### By language (all core rules ok; n in brackets)

| backend | condition | csharp |
|---|---|---|
| openai:google/gemini-3.1-flash-lite | none | 100.0% [30] |
