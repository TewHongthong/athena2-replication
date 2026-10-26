# Athena Sim summary

210 successful trials, 0 trial keys with only errors. Rates are per trial; repeats of the same unit are pooled (treat CIs and p-values as exploratory).

Split: test.

> Run `test_odoo_gemini31fl_llm` (test split) was started from freeze `frozen_odoo_gemini31fl_llm.json` (sha256 aae32fe18b42).

## rename - pack `odoo`

### By condition and backend

| backend | condition | n | parsed | exact match [95% CI] | violated rule ok | all core rules ok [95% CI] | type prefix kept | collision | similarity idx before -> after | retrieval hit | latency s | tokens in/out | cost USD |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| openai:google/gemini-3.1-flash-lite | graph[llm] | 210 | 100.0% | 94.8% [91-97] | 100.0% | 100.0% [98-100] | - | 2.4% | 0.956 -> 0.999 | - | 1.30 | 95718/22982 | 0.0584 |

### By language (all core rules ok; n in brackets)

| backend | condition | python |
|---|---|---|
| openai:google/gemini-3.1-flash-lite | graph[llm] | 100.0% [210] |
