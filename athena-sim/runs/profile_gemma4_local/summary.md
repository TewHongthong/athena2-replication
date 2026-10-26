# Athena Sim summary

12 successful trials, 0 trial keys with only errors. Rates are per trial; repeats of the same unit are pooled (treat CIs and p-values as exploratory).

Split: dev.

## rename - pack `gscs`

### By condition and backend

| backend | condition | n | parsed | exact match [95% CI] | violated rule ok | all core rules ok [95% CI] | type prefix kept | collision | similarity idx before -> after | retrieval hit | latency s | tokens in/out | cost USD |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| openai:gemma-4-26b-a4b-it-ud-q4_k_m | none | 12 | 100.0% | 33.3% [14-61] | 33.3% | 33.3% [14-61] | 33.3% | 0.0% | 0.993 -> 0.995 | - | 3.02 | 6458/1665 | - |

### By language (all core rules ok; n in brackets)

| backend | condition | cpp | java | python |
|---|---|---|---|---|
| openai:gemma-4-26b-a4b-it-ud-q4_k_m | none | 25.0% [4] | 25.0% [4] | 50.0% [4] |
