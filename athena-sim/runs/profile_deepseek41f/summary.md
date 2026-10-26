# Athena Sim summary

12 successful trials, 0 trial keys with only errors. Rates are per trial; repeats of the same unit are pooled (treat CIs and p-values as exploratory).

Split: dev.

## rename - pack `gscs`

### By condition and backend

| backend | condition | n | parsed | exact match [95% CI] | violated rule ok | all core rules ok [95% CI] | type prefix kept | collision | similarity idx before -> after | retrieval hit | latency s | tokens in/out | cost USD |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| openai:deepseek/deepseek-v4.1-flash | none | 12 | 50.0% | 16.7% [5-45] | 16.7% | 16.7% [5-45] | 22.2% | 0.0% | 0.993 -> 0.994 | - | 25.40 | 6137/60033 | 0.0739 |

### By language (all core rules ok; n in brackets)

| backend | condition | cpp | java | python |
|---|---|---|---|---|
| openai:deepseek/deepseek-v4.1-flash | none | 0.0% [4] | 25.0% [4] | 25.0% [4] |
