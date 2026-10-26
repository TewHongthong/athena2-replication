# Athena Sim summary

210 successful trials, 0 trial keys with only errors. Rates are per trial; repeats of the same unit are pooled (treat CIs and p-values as exploratory).

Split: test.

> Run `test_godot_qwen35_9b_llm` (test split) was started from freeze `frozen_godot_qwen35_9b_llm.json` (sha256 c97cdc635cf5).

## rename - pack `godot`

### By condition and backend

| backend | condition | n | parsed | exact match [95% CI] | violated rule ok | all core rules ok [95% CI] | type prefix kept | collision | similarity idx before -> after | retrieval hit | latency s | tokens in/out | cost USD |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| openai:qwen3.5-9b-ud-q8_k_xl | graph[llm] | 210 | 99.0% | 85.7% [80-90] | 99.0% | 99.0% [97-100] | - | 1.0% | 0.931 -> 0.997 | - | 8.04 | 96570/35094 | - |

### By language (all core rules ok; n in brackets)

| backend | condition | cpp |
|---|---|---|
| openai:qwen3.5-9b-ud-q8_k_xl | graph[llm] | 99.0% [210] |
