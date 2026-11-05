# Athena Sim summary

19 successful trials, 0 trial keys with only errors. Rates are per trial; repeats of the same unit are pooled (treat CIs and p-values as exploratory).

Split: dev.

## rename - pack `dotnet-runtime-s2`

### By condition and backend

| backend | condition | n | parsed | exact match [95% CI] | violated rule ok | all core rules ok [95% CI] | type prefix kept | collision | similarity idx before -> after | retrieval hit | latency s | tokens in/out | cost USD |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| openai:qwen/qwen3.5-9b | none | 19 | 94.7% | 15.8% [6-38] | 21.1% | 21.1% [9-43] | - | 26.3% | 0.998 -> 0.993 | - | 11.60 | 10602/4910 | 0.0018 |

### By language (all core rules ok; n in brackets)

| backend | condition | csharp |
|---|---|---|
| openai:qwen/qwen3.5-9b | none | 21.1% [19] |
