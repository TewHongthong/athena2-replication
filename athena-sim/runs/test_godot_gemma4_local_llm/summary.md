# Athena Sim summary

210 successful trials, 0 trial keys with only errors. Rates are per trial; repeats of the same unit are pooled (treat CIs and p-values as exploratory).

Split: test.

> Run `test_godot_gemma4_local_llm` (test split) was started from freeze `frozen_godot_gemma4_local_llm.json` (sha256 d13567869460).

## rename - pack `godot`

### By condition and backend

| backend | condition | n | parsed | exact match [95% CI] | violated rule ok | all core rules ok [95% CI] | type prefix kept | collision | similarity idx before -> after | retrieval hit | latency s | tokens in/out | cost USD |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| openai:gemma-4-26b-a4b-it-ud-q4_k_m | graph[llm] | 210 | 99.0% | 81.9% [76-87] | 99.0% | 99.0% [97-100] | - | 0.0% | 0.931 -> 0.997 | - | 3.04 | 103485/28850 | - |

### By language (all core rules ok; n in brackets)

| backend | condition | cpp |
|---|---|---|
| openai:gemma-4-26b-a4b-it-ud-q4_k_m | graph[llm] | 99.0% [210] |
