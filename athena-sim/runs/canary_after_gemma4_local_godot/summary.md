# Athena Sim summary

30 successful trials, 0 trial keys with only errors. Rates are per trial; repeats of the same unit are pooled (treat CIs and p-values as exploratory).

Split: dev.

## rename - pack `godot`

### By condition and backend

| backend | condition | n | parsed | exact match [95% CI] | violated rule ok | all core rules ok [95% CI] | type prefix kept | collision | similarity idx before -> after | retrieval hit | latency s | tokens in/out | cost USD |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| openai:gemma-4-26b-a4b-it-ud-q4_k_m | none | 30 | 100.0% | 86.7% [70-95] | 100.0% | 100.0% [89-100] | - | 3.3% | 0.926 -> 0.994 | - | 2.79 | 12884/3788 | - |

### By language (all core rules ok; n in brackets)

| backend | condition | cpp |
|---|---|---|
| openai:gemma-4-26b-a4b-it-ud-q4_k_m | none | 100.0% [30] |
