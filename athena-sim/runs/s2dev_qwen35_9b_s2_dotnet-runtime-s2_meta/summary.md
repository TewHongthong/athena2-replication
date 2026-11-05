# Athena Sim summary

133 successful trials, 0 trial keys with only errors. Rates are per trial; repeats of the same unit are pooled (treat CIs and p-values as exploratory).

Split: dev.

## rename - pack `dotnet-runtime-s2`

### By condition and backend

| backend | condition | n | parsed | exact match [95% CI] | violated rule ok | all core rules ok [95% CI] | type prefix kept | collision | similarity idx before -> after | retrieval hit | latency s | tokens in/out | cost USD |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| openai:qwen3.5-9b-ud-q8_k_xl | none | 19 | 84.2% | 31.6% [15-54] | 31.6% | 31.6% [15-54] | - | 26.3% | 0.998 -> 0.997 | - | 11.70 | 10602/4670 | - |
| openai:qwen3.5-9b-ud-q8_k_xl | fulldoc | 19 | 100.0% | 100.0% [83-100] | 100.0% | 100.0% [83-100] | - | 0.0% | 0.998 -> 1.000 | - | 7.33 | 45106/2427 | - |
| openai:qwen3.5-9b-ud-q8_k_xl | chunk | 19 | 100.0% | 73.7% [51-88] | 73.7% | 73.7% [51-88] | - | 15.8% | 0.998 -> 0.995 | - | 7.00 | 18714/2604 | - |
| openai:qwen3.5-9b-ud-q8_k_xl | bm25 | 19 | 94.7% | 73.7% [51-88] | 78.9% | 78.9% [57-91] | - | 5.3% | 0.998 -> 0.997 | - | 7.63 | 19039/2941 | - |
| openai:qwen3.5-9b-ud-q8_k_xl | dense | 19 | 100.0% | 63.2% [41-81] | 73.7% | 73.7% [51-88] | - | 5.3% | 0.998 -> 0.993 | - | 8.87 | 14146/3440 | - |
| openai:qwen3.5-9b-ud-q8_k_xl | graph | 19 | 100.0% | 94.7% [75-99] | 100.0% | 100.0% [83-100] | - | 0.0% | 0.998 -> 1.000 | 100.0% | 7.67 | 11636/2919 | - |
| openai:qwen3.5-9b-ud-q8_k_xl | naming | 19 | 94.7% | 78.9% [57-91] | 89.5% | 89.5% [69-97] | - | 0.0% | 0.998 -> 0.999 | - | 6.50 | 15732/2418 | - |

### By language (all core rules ok; n in brackets)

| backend | condition | csharp |
|---|---|---|
| openai:qwen3.5-9b-ud-q8_k_xl | none | 31.6% [19] |
| openai:qwen3.5-9b-ud-q8_k_xl | fulldoc | 100.0% [19] |
| openai:qwen3.5-9b-ud-q8_k_xl | chunk | 73.7% [19] |
| openai:qwen3.5-9b-ud-q8_k_xl | bm25 | 78.9% [19] |
| openai:qwen3.5-9b-ud-q8_k_xl | dense | 73.7% [19] |
| openai:qwen3.5-9b-ud-q8_k_xl | graph | 100.0% [19] |
| openai:qwen3.5-9b-ud-q8_k_xl | naming | 89.5% [19] |

### Paired comparison against `none` (per unit, repeats averaged; exact two-sided sign test)

| backend | comparison | metric | units | better | worse | tied | mean diff (pp) | p | p (Holm) |
|---|---|---|---|---|---|---|---|---|---|
| openai:qwen3.5-9b-ud-q8_k_xl | fulldoc vs none | core_ok | 19 | 13 | 0 | 6 | +68.4 | 0.000244 | 0.00293 |
| openai:qwen3.5-9b-ud-q8_k_xl | chunk vs none | core_ok | 19 | 9 | 1 | 9 | +42.1 | 0.0215 | 0.129 |
| openai:qwen3.5-9b-ud-q8_k_xl | bm25 vs none | core_ok | 19 | 11 | 2 | 6 | +47.4 | 0.0225 | 0.129 |
| openai:qwen3.5-9b-ud-q8_k_xl | dense vs none | core_ok | 19 | 8 | 0 | 11 | +42.1 | 0.00781 | 0.0591 |
| openai:qwen3.5-9b-ud-q8_k_xl | graph vs none | core_ok | 19 | 13 | 0 | 6 | +68.4 | 0.000244 | 0.00293 |
| openai:qwen3.5-9b-ud-q8_k_xl | naming vs none | core_ok | 19 | 13 | 2 | 4 | +57.9 | 0.00739 | 0.0591 |
| openai:qwen3.5-9b-ud-q8_k_xl | fulldoc vs none | exact_match | 19 | 13 | 0 | 6 | +68.4 | 0.000244 | 0.00293 |
| openai:qwen3.5-9b-ud-q8_k_xl | chunk vs none | exact_match | 19 | 9 | 1 | 9 | +42.1 | 0.0215 | 0.129 |
| openai:qwen3.5-9b-ud-q8_k_xl | bm25 vs none | exact_match | 19 | 10 | 2 | 7 | +42.1 | 0.0386 | 0.129 |
| openai:qwen3.5-9b-ud-q8_k_xl | dense vs none | exact_match | 19 | 7 | 1 | 11 | +31.6 | 0.0703 | 0.129 |
| openai:qwen3.5-9b-ud-q8_k_xl | graph vs none | exact_match | 19 | 12 | 0 | 7 | +63.2 | 0.000488 | 0.00439 |
| openai:qwen3.5-9b-ud-q8_k_xl | naming vs none | exact_match | 19 | 12 | 3 | 4 | +47.4 | 0.0352 | 0.129 |

`better`/`worse` count units. `p (Holm)` corrects for all comparisons in this table; only hypotheses written in HYPOTHESES.md before the test run are confirmatory.
