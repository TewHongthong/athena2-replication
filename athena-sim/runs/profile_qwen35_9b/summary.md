# Athena Sim summary

12 successful trials, 0 trial keys with only errors. Rates are per trial; repeats of the same unit are pooled (treat CIs and p-values as exploratory).

Split: dev.

## rename - pack `gscs`

### By condition and backend

| backend | condition | n | parsed | exact match [95% CI] | violated rule ok | all core rules ok [95% CI] | type prefix kept | collision | similarity idx before -> after | retrieval hit | latency s | tokens in/out | cost USD |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| openai:qwen3.5-9b-ud-q8_k_xl | none | 12 | 100.0% | 25.0% [9-53] | 25.0% | 25.0% [9-53] | 11.1% | 0.0% | 0.993 -> 0.993 | - | 7.71 | 6112/1928 | - |

### By language (all core rules ok; n in brackets)

| backend | condition | cpp | java | python |
|---|---|---|---|---|
| openai:qwen3.5-9b-ud-q8_k_xl | none | 50.0% [4] | 25.0% [4] | 0.0% [4] |
