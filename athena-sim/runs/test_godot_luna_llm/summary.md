# Athena Sim summary

210 successful trials, 0 trial keys with only errors. Rates are per trial; repeats of the same unit are pooled (treat CIs and p-values as exploratory).

Split: test.

> Run `test_godot_luna_llm` (test split) was started from freeze `frozen_godot_luna_llm.json` (sha256 2044804d4889).

## rename - pack `godot`

### By condition and backend

| backend | condition | n | parsed | exact match [95% CI] | violated rule ok | all core rules ok [95% CI] | type prefix kept | collision | similarity idx before -> after | retrieval hit | latency s | tokens in/out | cost USD |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| openai:openai/gpt-6-luna | graph[llm] | 210 | 100.0% | 78.6% [73-84] | 100.0% | 100.0% [98-100] | - | 0.0% | 0.931 -> 0.995 | - | 3.80 | 91128/38128 | 0.0282 |

### By language (all core rules ok; n in brackets)

| backend | condition | cpp |
|---|---|---|
| openai:openai/gpt-6-luna | graph[llm] | 100.0% [210] |
