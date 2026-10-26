# Athena Sim summary

210 successful trials, 0 trial keys with only errors. Rates are per trial; repeats of the same unit are pooled (treat CIs and p-values as exploratory).

Split: test.

> Run `test_godot_gemini31fl_llm` (test split) was started from freeze `frozen_godot_gemini31fl_llm.json` (sha256 9dde523f1058).

## rename - pack `godot`

### By condition and backend

| backend | condition | n | parsed | exact match [95% CI] | violated rule ok | all core rules ok [95% CI] | type prefix kept | collision | similarity idx before -> after | retrieval hit | latency s | tokens in/out | cost USD |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| openai:google/gemini-3.1-flash-lite | graph[llm] | 210 | 100.0% | 79.0% [73-84] | 100.0% | 100.0% [98-100] | - | 1.0% | 0.931 -> 0.994 | - | 1.68 | 100755/27564 | 0.0665 |

### By language (all core rules ok; n in brackets)

| backend | condition | cpp |
|---|---|---|
| openai:google/gemini-3.1-flash-lite | graph[llm] | 100.0% [210] |
