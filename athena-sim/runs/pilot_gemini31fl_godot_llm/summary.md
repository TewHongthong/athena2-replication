# Athena Sim summary

30 successful trials, 0 trial keys with only errors. Rates are per trial; repeats of the same unit are pooled (treat CIs and p-values as exploratory).

Split: dev.

## rename - pack `godot`

### By condition and backend

| backend | condition | n | parsed | exact match [95% CI] | violated rule ok | all core rules ok [95% CI] | type prefix kept | collision | similarity idx before -> after | retrieval hit | latency s | tokens in/out | cost USD |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| openai:google/gemini-3.1-flash-lite | graph | 30 | 100.0% | 83.3% [66-93] | 100.0% | 100.0% [89-100] | - | 0.0% | 0.926 -> 0.992 | - | 1.57 | 15008/3991 | 0.0097 |

### By language (all core rules ok; n in brackets)

| backend | condition | cpp |
|---|---|---|
| openai:google/gemini-3.1-flash-lite | graph | 100.0% [30] |
