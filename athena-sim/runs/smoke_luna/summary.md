# Athena Sim summary

2 successful trials, 0 trial keys with only errors. Rates are per trial; repeats of the same unit are pooled (treat CIs and p-values as exploratory).

Split: dev.

## rename - pack `gscs`

### By condition and backend

| backend | condition | n | parsed | exact match [95% CI] | violated rule ok | all core rules ok [95% CI] | type prefix kept | collision | similarity idx before -> after | retrieval hit | latency s | tokens in/out | cost USD |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| openai:openai/gpt-6-luna | none | 2 | 100.0% | 50.0% [9-91] | 50.0% | 50.0% [9-91] | 0.0% | 0.0% | 0.983 -> 0.996 | - | 15.26 | 879/755 | 0.0005 |

### By language (all core rules ok; n in brackets)

| backend | condition | cpp |
|---|---|---|
| openai:openai/gpt-6-luna | none | 50.0% [2] |
