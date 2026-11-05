# Athena Sim summary

30 successful trials, 0 trial keys with only errors. Rates are per trial; repeats of the same unit are pooled (treat CIs and p-values as exploratory).

Split: dev.

## rename - pack `godot-s2`

### By condition and backend

| backend | condition | n | parsed | exact match [95% CI] | violated rule ok | all core rules ok [95% CI] | type prefix kept | collision | similarity idx before -> after | retrieval hit | latency s | tokens in/out | cost USD |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| openai:qwen/qwen3.5-9b | none | 30 | 96.7% | 36.7% [22-54] | 40.0% | 40.0% [25-58] | - | 6.7% | 0.991 -> 0.984 | - | 28.00 | 12101/13450 | 0.0032 |

### By language (all core rules ok; n in brackets)

| backend | condition | cpp |
|---|---|---|
| openai:qwen/qwen3.5-9b | none | 40.0% [30] |
