# Athena Sim summary

210 successful trials, 0 trial keys with only errors. Rates are per trial; repeats of the same unit are pooled (treat CIs and p-values as exploratory).

Split: test.

> Run `test_odoo_qwen35_9b_llm` (test split) was started from freeze `frozen_odoo_qwen35_9b_llm.json` (sha256 1b35ff96823b).

## rename - pack `odoo`

### By condition and backend

| backend | condition | n | parsed | exact match [95% CI] | violated rule ok | all core rules ok [95% CI] | type prefix kept | collision | similarity idx before -> after | retrieval hit | latency s | tokens in/out | cost USD |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| openai:qwen3.5-9b-ud-q8_k_xl | graph[llm] | 210 | 94.3% | 70.5% [64-76] | 94.3% | 94.3% [90-97] | - | 2.9% | 0.956 -> 0.993 | - | 6.88 | 90864/29784 | - |

### By language (all core rules ok; n in brackets)

| backend | condition | python |
|---|---|---|
| openai:qwen3.5-9b-ud-q8_k_xl | graph[llm] | 94.3% [210] |
