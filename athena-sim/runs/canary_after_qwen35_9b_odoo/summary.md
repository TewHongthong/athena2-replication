# Athena Sim summary

30 successful trials, 0 trial keys with only errors. Rates are per trial; repeats of the same unit are pooled (treat CIs and p-values as exploratory).

Split: dev.

## rename - pack `odoo`

### By condition and backend

| backend | condition | n | parsed | exact match [95% CI] | violated rule ok | all core rules ok [95% CI] | type prefix kept | collision | similarity idx before -> after | retrieval hit | latency s | tokens in/out | cost USD |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| openai:qwen3.5-9b-ud-q8_k_xl | none | 30 | 90.0% | 63.3% [46-78] | 86.7% | 86.7% [70-95] | - | 3.3% | 0.952 -> 0.991 | - | 6.99 | 13229/4322 | - |

### By language (all core rules ok; n in brackets)

| backend | condition | python |
|---|---|---|
| openai:qwen3.5-9b-ud-q8_k_xl | none | 86.7% [30] |
