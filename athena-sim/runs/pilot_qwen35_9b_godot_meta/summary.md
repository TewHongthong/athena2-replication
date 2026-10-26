# Athena Sim summary

180 successful trials, 0 trial keys with only errors. Rates are per trial; repeats of the same unit are pooled (treat CIs and p-values as exploratory).

Split: dev.

## rename - pack `godot`

### By condition and backend

| backend | condition | n | parsed | exact match [95% CI] | violated rule ok | all core rules ok [95% CI] | type prefix kept | collision | similarity idx before -> after | retrieval hit | latency s | tokens in/out | cost USD |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| openai:qwen3.5-9b-ud-q8_k_xl | none | 30 | 93.3% | 50.0% [33-67] | 83.3% | 83.3% [66-93] | - | 6.7% | 0.926 -> 0.981 | - | 7.66 | 11800/4785 | - |
| openai:qwen3.5-9b-ud-q8_k_xl | fulldoc | 30 | 100.0% | 70.0% [52-83] | 96.7% | 96.7% [83-99] | - | 0.0% | 0.926 -> 0.982 | - | 7.94 | 62980/4409 | - |
| openai:qwen3.5-9b-ud-q8_k_xl | chunk | 30 | 93.3% | 66.7% [49-81] | 93.3% | 93.3% [79-98] | - | 6.7% | 0.926 -> 0.988 | - | 9.52 | 16635/5965 | - |
| openai:qwen3.5-9b-ud-q8_k_xl | bm25 | 30 | 100.0% | 66.7% [49-81] | 100.0% | 100.0% [89-100] | - | 3.3% | 0.926 -> 0.991 | - | 6.84 | 17025/4318 | - |
| openai:qwen3.5-9b-ud-q8_k_xl | dense | 30 | 96.7% | 66.7% [49-81] | 86.7% | 86.7% [70-95] | - | 0.0% | 0.926 -> 0.987 | - | 8.43 | 15764/5260 | - |
| openai:qwen3.5-9b-ud-q8_k_xl | graph | 30 | 100.0% | 90.0% [74-97] | 100.0% | 100.0% [89-100] | - | 0.0% | 0.926 -> 0.994 | 100.0% | 8.37 | 16258/5217 | - |

### By language (all core rules ok; n in brackets)

| backend | condition | cpp |
|---|---|---|
| openai:qwen3.5-9b-ud-q8_k_xl | none | 83.3% [30] |
| openai:qwen3.5-9b-ud-q8_k_xl | fulldoc | 96.7% [30] |
| openai:qwen3.5-9b-ud-q8_k_xl | chunk | 93.3% [30] |
| openai:qwen3.5-9b-ud-q8_k_xl | bm25 | 100.0% [30] |
| openai:qwen3.5-9b-ud-q8_k_xl | dense | 86.7% [30] |
| openai:qwen3.5-9b-ud-q8_k_xl | graph | 100.0% [30] |

### Paired comparison against `none` (per unit, repeats averaged; exact two-sided sign test)

| backend | comparison | metric | units | better | worse | tied | mean diff (pp) | p | p (Holm) |
|---|---|---|---|---|---|---|---|---|---|
| openai:qwen3.5-9b-ud-q8_k_xl | fulldoc vs none | core_ok | 30 | 5 | 1 | 24 | +13.3 | 0.219 | 1 |
| openai:qwen3.5-9b-ud-q8_k_xl | chunk vs none | core_ok | 30 | 4 | 1 | 25 | +10.0 | 0.375 | 1 |
| openai:qwen3.5-9b-ud-q8_k_xl | bm25 vs none | core_ok | 30 | 5 | 0 | 25 | +16.7 | 0.0625 | 0.562 |
| openai:qwen3.5-9b-ud-q8_k_xl | dense vs none | core_ok | 30 | 5 | 4 | 21 | +3.3 | 1 | 1 |
| openai:qwen3.5-9b-ud-q8_k_xl | graph vs none | core_ok | 30 | 5 | 0 | 25 | +16.7 | 0.0625 | 0.562 |
| openai:qwen3.5-9b-ud-q8_k_xl | fulldoc vs none | exact_match | 30 | 8 | 2 | 20 | +20.0 | 0.109 | 0.766 |
| openai:qwen3.5-9b-ud-q8_k_xl | chunk vs none | exact_match | 30 | 7 | 2 | 21 | +16.7 | 0.18 | 1 |
| openai:qwen3.5-9b-ud-q8_k_xl | bm25 vs none | exact_match | 30 | 7 | 2 | 21 | +16.7 | 0.18 | 1 |
| openai:qwen3.5-9b-ud-q8_k_xl | dense vs none | exact_match | 30 | 9 | 4 | 17 | +16.7 | 0.267 | 1 |
| openai:qwen3.5-9b-ud-q8_k_xl | graph vs none | exact_match | 30 | 12 | 0 | 18 | +40.0 | 0.000488 | 0.00488 |

`better`/`worse` count units. `p (Holm)` corrects for all comparisons in this table; only hypotheses written in HYPOTHESES.md before the test run are confirmatory.
