# Athena Sim summary

210 successful trials, 0 trial keys with only errors. Rates are per trial; repeats of the same unit are pooled (treat CIs and p-values as exploratory).

Split: test.

> Run `test_odoo_luna_llm` (test split) was started from freeze `frozen_odoo_luna_llm.json` (sha256 256a52e89d29).

## rename - pack `odoo`

### By condition and backend

| backend | condition | n | parsed | exact match [95% CI] | violated rule ok | all core rules ok [95% CI] | type prefix kept | collision | similarity idx before -> after | retrieval hit | latency s | tokens in/out | cost USD |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| openai:openai/gpt-6-luna | graph[llm] | 210 | 100.0% | 98.6% [96-100] | 100.0% | 100.0% [98-100] | - | 0.0% | 0.956 -> 1.000 | - | 3.72 | 85371/38479 | 0.0278 |

### By language (all core rules ok; n in brackets)

| backend | condition | python |
|---|---|---|
| openai:openai/gpt-6-luna | graph[llm] | 100.0% [210] |
