# Athena Sim summary

210 successful trials, 0 trial keys with only errors. Rates are per trial; repeats of the same unit are pooled (treat CIs and p-values as exploratory).

Split: dev.

## rename - pack `godot-s2`

### By condition and backend

| backend | condition | n | parsed | exact match [95% CI] | violated rule ok | all core rules ok [95% CI] | type prefix kept | collision | similarity idx before -> after | retrieval hit | latency s | tokens in/out | cost USD |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| openai:qwen3.5-9b-ud-q8_k_xl | none | 30 | 100.0% | 40.0% [25-58] | 43.3% | 43.3% [27-61] | - | 10.0% | 0.991 -> 0.988 | - | 10.44 | 12101/6611 | - |
| openai:qwen3.5-9b-ud-q8_k_xl | fulldoc | 30 | 100.0% | 70.0% [52-83] | 76.7% | 76.7% [59-88] | - | 6.7% | 0.991 -> 0.993 | - | 11.99 | 63281/7089 | - |
| openai:qwen3.5-9b-ud-q8_k_xl | chunk | 30 | 100.0% | 70.0% [52-83] | 73.3% | 73.3% [56-86] | - | 6.7% | 0.991 -> 0.995 | - | 7.79 | 18014/4767 | - |
| openai:qwen3.5-9b-ud-q8_k_xl | bm25 | 30 | 100.0% | 63.3% [46-78] | 66.7% | 66.7% [49-81] | - | 6.7% | 0.991 -> 0.995 | - | 10.90 | 18175/7065 | - |
| openai:qwen3.5-9b-ud-q8_k_xl | dense | 30 | 100.0% | 63.3% [46-78] | 73.3% | 73.3% [56-86] | - | 0.0% | 0.991 -> 0.995 | - | 20.12 | 15574/5009 | - |
| openai:qwen3.5-9b-ud-q8_k_xl | graph | 30 | 100.0% | 90.0% [74-97] | 100.0% | 100.0% [89-100] | - | 0.0% | 0.991 -> 0.999 | 100.0% | 8.36 | 16811/5086 | - |
| openai:qwen3.5-9b-ud-q8_k_xl | naming | 30 | 100.0% | 60.0% [42-75] | 83.3% | 83.3% [66-93] | - | 0.0% | 0.991 -> 0.991 | - | 7.42 | 16481/4526 | - |

### By language (all core rules ok; n in brackets)

| backend | condition | cpp |
|---|---|---|
| openai:qwen3.5-9b-ud-q8_k_xl | none | 43.3% [30] |
| openai:qwen3.5-9b-ud-q8_k_xl | fulldoc | 76.7% [30] |
| openai:qwen3.5-9b-ud-q8_k_xl | chunk | 73.3% [30] |
| openai:qwen3.5-9b-ud-q8_k_xl | bm25 | 66.7% [30] |
| openai:qwen3.5-9b-ud-q8_k_xl | dense | 73.3% [30] |
| openai:qwen3.5-9b-ud-q8_k_xl | graph | 100.0% [30] |
| openai:qwen3.5-9b-ud-q8_k_xl | naming | 83.3% [30] |

### Paired comparison against `none` (per unit, repeats averaged; exact two-sided sign test)

| backend | comparison | metric | units | better | worse | tied | mean diff (pp) | p | p (Holm) |
|---|---|---|---|---|---|---|---|---|---|
| openai:qwen3.5-9b-ud-q8_k_xl | fulldoc vs none | core_ok | 30 | 13 | 3 | 14 | +33.3 | 0.0213 | 0.191 |
| openai:qwen3.5-9b-ud-q8_k_xl | chunk vs none | core_ok | 30 | 12 | 3 | 15 | +30.0 | 0.0352 | 0.281 |
| openai:qwen3.5-9b-ud-q8_k_xl | bm25 vs none | core_ok | 30 | 9 | 2 | 19 | +23.3 | 0.0654 | 0.281 |
| openai:qwen3.5-9b-ud-q8_k_xl | dense vs none | core_ok | 30 | 12 | 3 | 15 | +30.0 | 0.0352 | 0.281 |
| openai:qwen3.5-9b-ud-q8_k_xl | graph vs none | core_ok | 30 | 17 | 0 | 13 | +56.7 | 1.53e-05 | 0.000183 |
| openai:qwen3.5-9b-ud-q8_k_xl | naming vs none | core_ok | 30 | 16 | 4 | 10 | +40.0 | 0.0118 | 0.118 |
| openai:qwen3.5-9b-ud-q8_k_xl | fulldoc vs none | exact_match | 30 | 12 | 3 | 15 | +30.0 | 0.0352 | 0.281 |
| openai:qwen3.5-9b-ud-q8_k_xl | chunk vs none | exact_match | 30 | 13 | 4 | 13 | +30.0 | 0.049 | 0.281 |
| openai:qwen3.5-9b-ud-q8_k_xl | bm25 vs none | exact_match | 30 | 8 | 1 | 21 | +23.3 | 0.0391 | 0.281 |
| openai:qwen3.5-9b-ud-q8_k_xl | dense vs none | exact_match | 30 | 10 | 3 | 17 | +23.3 | 0.0923 | 0.281 |
| openai:qwen3.5-9b-ud-q8_k_xl | graph vs none | exact_match | 30 | 15 | 0 | 15 | +50.0 | 6.1e-05 | 0.000671 |
| openai:qwen3.5-9b-ud-q8_k_xl | naming vs none | exact_match | 30 | 9 | 3 | 18 | +20.0 | 0.146 | 0.281 |

`better`/`worse` count units. `p (Holm)` corrects for all comparisons in this table; only hypotheses written in HYPOTHESES.md before the test run are confirmatory.
