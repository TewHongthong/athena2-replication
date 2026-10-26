# Athena Sim summary

180 successful trials, 0 trial keys with only errors. Rates are per trial; repeats of the same unit are pooled (treat CIs and p-values as exploratory).

Split: dev.

## rename - pack `dotnet-runtime`

### By condition and backend

| backend | condition | n | parsed | exact match [95% CI] | violated rule ok | all core rules ok [95% CI] | type prefix kept | collision | similarity idx before -> after | retrieval hit | latency s | tokens in/out | cost USD |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| openai:qwen3.5-9b-ud-q8_k_xl | none | 30 | 96.7% | 53.3% [36-70] | 90.0% | 90.0% [74-97] | - | 3.3% | 0.987 -> 0.996 | - | 8.07 | 11937/5050 | - |
| openai:qwen3.5-9b-ud-q8_k_xl | fulldoc | 30 | 96.7% | 90.0% [74-97] | 96.7% | 96.7% [83-99] | - | 3.3% | 0.987 -> 0.999 | - | 7.20 | 66417/3849 | - |
| openai:qwen3.5-9b-ud-q8_k_xl | chunk | 30 | 100.0% | 83.3% [66-93] | 100.0% | 100.0% [89-100] | - | 0.0% | 0.987 -> 0.999 | - | 6.68 | 20586/4005 | - |
| openai:qwen3.5-9b-ud-q8_k_xl | bm25 | 30 | 96.7% | 76.7% [59-88] | 96.7% | 96.7% [83-99] | - | 3.3% | 0.987 -> 0.998 | - | 8.24 | 23738/5074 | - |
| openai:qwen3.5-9b-ud-q8_k_xl | dense | 30 | 100.0% | 66.7% [49-81] | 86.7% | 86.7% [70-95] | - | 3.3% | 0.987 -> 0.995 | - | 7.61 | 16958/4685 | - |
| openai:qwen3.5-9b-ud-q8_k_xl | graph | 30 | 100.0% | 93.3% [79-98] | 100.0% | 100.0% [89-100] | - | 0.0% | 0.987 -> 0.999 | 100.0% | 6.06 | 12357/3701 | - |

### By language (all core rules ok; n in brackets)

| backend | condition | csharp |
|---|---|---|
| openai:qwen3.5-9b-ud-q8_k_xl | none | 90.0% [30] |
| openai:qwen3.5-9b-ud-q8_k_xl | fulldoc | 96.7% [30] |
| openai:qwen3.5-9b-ud-q8_k_xl | chunk | 100.0% [30] |
| openai:qwen3.5-9b-ud-q8_k_xl | bm25 | 96.7% [30] |
| openai:qwen3.5-9b-ud-q8_k_xl | dense | 86.7% [30] |
| openai:qwen3.5-9b-ud-q8_k_xl | graph | 100.0% [30] |

### Paired comparison against `none` (per unit, repeats averaged; exact two-sided sign test)

| backend | comparison | metric | units | better | worse | tied | mean diff (pp) | p | p (Holm) |
|---|---|---|---|---|---|---|---|---|---|
| openai:qwen3.5-9b-ud-q8_k_xl | fulldoc vs none | core_ok | 30 | 3 | 1 | 26 | +6.7 | 0.625 | 1 |
| openai:qwen3.5-9b-ud-q8_k_xl | chunk vs none | core_ok | 30 | 3 | 0 | 27 | +10.0 | 0.25 | 1 |
| openai:qwen3.5-9b-ud-q8_k_xl | bm25 vs none | core_ok | 30 | 3 | 1 | 26 | +6.7 | 0.625 | 1 |
| openai:qwen3.5-9b-ud-q8_k_xl | dense vs none | core_ok | 30 | 2 | 3 | 25 | -3.3 | 1 | 1 |
| openai:qwen3.5-9b-ud-q8_k_xl | graph vs none | core_ok | 30 | 3 | 0 | 27 | +10.0 | 0.25 | 1 |
| openai:qwen3.5-9b-ud-q8_k_xl | fulldoc vs none | exact_match | 30 | 11 | 0 | 19 | +36.7 | 0.000977 | 0.00879 |
| openai:qwen3.5-9b-ud-q8_k_xl | chunk vs none | exact_match | 30 | 10 | 1 | 19 | +30.0 | 0.0117 | 0.0938 |
| openai:qwen3.5-9b-ud-q8_k_xl | bm25 vs none | exact_match | 30 | 9 | 2 | 19 | +23.3 | 0.0654 | 0.458 |
| openai:qwen3.5-9b-ud-q8_k_xl | dense vs none | exact_match | 30 | 8 | 4 | 18 | +13.3 | 0.388 | 1 |
| openai:qwen3.5-9b-ud-q8_k_xl | graph vs none | exact_match | 30 | 12 | 0 | 18 | +40.0 | 0.000488 | 0.00488 |

`better`/`worse` count units. `p (Holm)` corrects for all comparisons in this table; only hypotheses written in HYPOTHESES.md before the test run are confirmatory.
