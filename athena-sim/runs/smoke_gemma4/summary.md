# Athena Sim summary

2 successful trials, 0 trial keys with only errors. Rates are per trial; repeats of the same unit are pooled (treat CIs and p-values as exploratory).

Split: dev.

## rename - pack `gscs`

### By condition and backend

| backend | condition | n | parsed | exact match [95% CI] | violated rule ok | all core rules ok [95% CI] | type prefix kept | collision | similarity idx before -> after | retrieval hit | latency s | tokens in/out | cost USD |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| openai:google/gemma-4-26b-a4b-it | none | 2 | 100.0% | 0.0% [0-66] | 0.0% | 0.0% [0-66] | 0.0% | 0.0% | 0.983 -> 0.980 | - | 3.46 | 980/276 | 0.0002 |

### By language (all core rules ok; n in brackets)

| backend | condition | cpp |
|---|---|---|
| openai:google/gemma-4-26b-a4b-it | none | 0.0% [2] |
