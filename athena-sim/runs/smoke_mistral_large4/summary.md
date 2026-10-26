# Athena Sim summary

2 successful trials, 0 trial keys with only errors. Rates are per trial; repeats of the same unit are pooled (treat CIs and p-values as exploratory).

Split: dev.

## rename - pack `gscs`

### By condition and backend

| backend | condition | n | parsed | exact match [95% CI] | violated rule ok | all core rules ok [95% CI] | type prefix kept | collision | similarity idx before -> after | retrieval hit | latency s | tokens in/out | cost USD |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| openai:mistralai/mistral-large-4-0 | none | 2 | 100.0% | 50.0% [9-91] | 50.0% | 50.0% [9-91] | 0.0% | 0.0% | 0.983 -> 0.996 | - | 94.21 | 891/9875 | 0.0212 |

### By language (all core rules ok; n in brackets)

| backend | condition | cpp |
|---|---|---|
| openai:mistralai/mistral-large-4-0 | none | 50.0% [2] |
