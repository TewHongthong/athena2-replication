# Athena Sim summary

30 successful trials, 0 trial keys with only errors. Rates are per trial; repeats of the same unit are pooled (treat CIs and p-values as exploratory).

Split: dev.

## rename - pack `godot`

### By condition and backend

| backend | condition | n | parsed | exact match [95% CI] | violated rule ok | all core rules ok [95% CI] | type prefix kept | collision | similarity idx before -> after | retrieval hit | latency s | tokens in/out | cost USD |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| openai:flashnext:instruct | graph | 30 | 100.0% | 80.0% [63-90] | 93.3% | 93.3% [79-98] | - | 0.0% | 0.926 -> 0.996 | - | 27.33 | 14290/5154 | - |

### By language (all core rules ok; n in brackets)

| backend | condition | cpp |
|---|---|---|
| openai:flashnext:instruct | graph | 93.3% [30] |
