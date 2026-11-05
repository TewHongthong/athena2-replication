# Athena Sim summary

130 successful trials, 20 trial keys with only errors. Rates are per trial; repeats of the same unit are pooled (treat CIs and p-values as exploratory).

Split: test.

> Run `s2test_qwen35_9b_s2_dotnet-runtime-s2_meta` (test split) was started from freeze `frozen_dotnet-runtime-s2_qwen35_9b_s2_meta.json` (sha256 68f419783478).

## rename - pack `dotnet-runtime-s2`

### By condition and backend

| backend | condition | n | parsed | exact match [95% CI] | violated rule ok | all core rules ok [95% CI] | type prefix kept | collision | similarity idx before -> after | retrieval hit | latency s | tokens in/out | cost USD |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| openai:qwen3.5-9b-ud-q8_k_xl | none | 19 | 94.7% | 26.3% [12-49] | 26.3% | 26.3% [12-49] | - | 42.1% | 0.997 -> 0.997 | - | 10.79 | 9963/4338 | - |
| openai:qwen3.5-9b-ud-q8_k_xl | fulldoc | 19 | 100.0% | 100.0% [83-100] | 100.0% | 100.0% [83-100] | - | 0.0% | 0.997 -> 1.000 | - | 7.11 | 44467/2426 | - |
| openai:qwen3.5-9b-ud-q8_k_xl | chunk | 19 | 94.7% | 63.2% [41-81] | 68.4% | 68.4% [46-85] | - | 5.3% | 0.997 -> 0.994 | - | 10.77 | 17357/4252 | - |
| openai:qwen3.5-9b-ud-q8_k_xl | bm25 | 18 | 100.0% | 77.8% [55-91] | 77.8% | 77.8% [55-91] | - | 5.6% | 0.997 -> 0.996 | - | 10.33 | 17691/3891 | - |
| openai:qwen3.5-9b-ud-q8_k_xl | dense | 18 | 100.0% | 72.2% [49-88] | 77.8% | 77.8% [55-91] | - | 11.1% | 0.997 -> 0.999 | - | 6.96 | 13551/2521 | - |
| openai:qwen3.5-9b-ud-q8_k_xl | graph | 18 | 100.0% | 94.4% [74-99] | 100.0% | 100.0% [82-100] | - | 0.0% | 0.997 -> 1.000 | 100.0% | 7.64 | 10554/2835 | - |
| openai:qwen3.5-9b-ud-q8_k_xl | naming | 19 | 100.0% | 94.7% [75-99] | 100.0% | 100.0% [83-100] | - | 0.0% | 0.997 -> 1.000 | - | 6.49 | 15093/2451 | - |

### By language (all core rules ok; n in brackets)

| backend | condition | csharp |
|---|---|---|
| openai:qwen3.5-9b-ud-q8_k_xl | none | 26.3% [19] |
| openai:qwen3.5-9b-ud-q8_k_xl | fulldoc | 100.0% [19] |
| openai:qwen3.5-9b-ud-q8_k_xl | chunk | 68.4% [19] |
| openai:qwen3.5-9b-ud-q8_k_xl | bm25 | 77.8% [18] |
| openai:qwen3.5-9b-ud-q8_k_xl | dense | 77.8% [18] |
| openai:qwen3.5-9b-ud-q8_k_xl | graph | 100.0% [18] |
| openai:qwen3.5-9b-ud-q8_k_xl | naming | 100.0% [19] |

### Paired comparison against `none` (per unit, repeats averaged; exact two-sided sign test)

| backend | comparison | metric | units | better | worse | tied | mean diff (pp) | p | p (Holm) |
|---|---|---|---|---|---|---|---|---|---|
| openai:qwen3.5-9b-ud-q8_k_xl | fulldoc vs none | core_ok | 19 | 14 | 0 | 5 | +73.7 | 0.000122 | 0.00146 |
| openai:qwen3.5-9b-ud-q8_k_xl | chunk vs none | core_ok | 19 | 9 | 1 | 9 | +42.1 | 0.0215 | 0.0645 |
| openai:qwen3.5-9b-ud-q8_k_xl | bm25 vs none | core_ok | 18 | 11 | 1 | 6 | +55.6 | 0.00635 | 0.0381 |
| openai:qwen3.5-9b-ud-q8_k_xl | dense vs none | core_ok | 18 | 12 | 2 | 4 | +55.6 | 0.0129 | 0.0518 |
| openai:qwen3.5-9b-ud-q8_k_xl | graph vs none | core_ok | 18 | 14 | 0 | 4 | +77.8 | 0.000122 | 0.00146 |
| openai:qwen3.5-9b-ud-q8_k_xl | naming vs none | core_ok | 19 | 14 | 0 | 5 | +73.7 | 0.000122 | 0.00146 |
| openai:qwen3.5-9b-ud-q8_k_xl | fulldoc vs none | exact_match | 19 | 14 | 0 | 5 | +73.7 | 0.000122 | 0.00146 |
| openai:qwen3.5-9b-ud-q8_k_xl | chunk vs none | exact_match | 19 | 8 | 1 | 10 | +36.8 | 0.0391 | 0.0703 |
| openai:qwen3.5-9b-ud-q8_k_xl | bm25 vs none | exact_match | 18 | 11 | 1 | 6 | +55.6 | 0.00635 | 0.0381 |
| openai:qwen3.5-9b-ud-q8_k_xl | dense vs none | exact_match | 18 | 12 | 3 | 3 | +50.0 | 0.0352 | 0.0703 |
| openai:qwen3.5-9b-ud-q8_k_xl | graph vs none | exact_match | 18 | 13 | 0 | 5 | +72.2 | 0.000244 | 0.00195 |
| openai:qwen3.5-9b-ud-q8_k_xl | naming vs none | exact_match | 19 | 13 | 0 | 6 | +68.4 | 0.000244 | 0.00195 |

`better`/`worse` count units. `p (Holm)` corrects for all comparisons in this table; only hypotheses written in HYPOTHESES.md before the test run are confirmatory.

## Trials that only have errors (20)

- `dotnet-runtime-s2|rename|csharp_039___usage__DOTNET-FIELD-INSTANCE-PREFIX|bm25|openai:qwen3.5-9b-ud-q8_k_xl|0`
- `dotnet-runtime-s2|rename|csharp_039___usage__DOTNET-FIELD-INSTANCE-PREFIX|dense|openai:qwen3.5-9b-ud-q8_k_xl|0`
- `dotnet-runtime-s2|rename|csharp_039___usage__DOTNET-FIELD-INSTANCE-PREFIX|graph|openai:qwen3.5-9b-ud-q8_k_xl|0`
- `dotnet-runtime-s2|rename|csharp_020___method__DOTNET-FIELD-INSTANCE-PREFIX|none|openai:qwen3.5-9b-ud-q8_k_xl|0`
- `dotnet-runtime-s2|rename|csharp_020___method__DOTNET-FIELD-INSTANCE-PREFIX|fulldoc|openai:qwen3.5-9b-ud-q8_k_xl|0`
- `dotnet-runtime-s2|rename|csharp_020___method__DOTNET-FIELD-INSTANCE-PREFIX|naming|openai:qwen3.5-9b-ud-q8_k_xl|0`
- `dotnet-runtime-s2|rename|csharp_020___method__DOTNET-FIELD-INSTANCE-PREFIX|chunk|openai:qwen3.5-9b-ud-q8_k_xl|0`
- `dotnet-runtime-s2|rename|csharp_020___method__DOTNET-FIELD-INSTANCE-PREFIX|bm25|openai:qwen3.5-9b-ud-q8_k_xl|0`
- `dotnet-runtime-s2|rename|csharp_020___method__DOTNET-FIELD-INSTANCE-PREFIX|dense|openai:qwen3.5-9b-ud-q8_k_xl|0`
- `dotnet-runtime-s2|rename|csharp_020___method__DOTNET-FIELD-INSTANCE-PREFIX|graph|openai:qwen3.5-9b-ud-q8_k_xl|0`
- `dotnet-runtime-s2|rename|csharp_064___name__DOTNET-FIELD-INSTANCE-PREFIX|none|openai:qwen3.5-9b-ud-q8_k_xl|0`
- `dotnet-runtime-s2|rename|csharp_064___name__DOTNET-FIELD-INSTANCE-PREFIX|fulldoc|openai:qwen3.5-9b-ud-q8_k_xl|0`
- `dotnet-runtime-s2|rename|csharp_064___name__DOTNET-FIELD-INSTANCE-PREFIX|naming|openai:qwen3.5-9b-ud-q8_k_xl|0`
- `dotnet-runtime-s2|rename|csharp_064___name__DOTNET-FIELD-INSTANCE-PREFIX|chunk|openai:qwen3.5-9b-ud-q8_k_xl|0`
- `dotnet-runtime-s2|rename|csharp_064___name__DOTNET-FIELD-INSTANCE-PREFIX|bm25|openai:qwen3.5-9b-ud-q8_k_xl|0`
- `dotnet-runtime-s2|rename|csharp_064___name__DOTNET-FIELD-INSTANCE-PREFIX|dense|openai:qwen3.5-9b-ud-q8_k_xl|0`
- `dotnet-runtime-s2|rename|csharp_064___name__DOTNET-FIELD-INSTANCE-PREFIX|graph|openai:qwen3.5-9b-ud-q8_k_xl|0`
- `dotnet-runtime-s2|rename|csharp_050___padding__DOTNET-FIELD-INSTANCE-PREFIX|none|openai:qwen3.5-9b-ud-q8_k_xl|0`
- `dotnet-runtime-s2|rename|csharp_050___padding__DOTNET-FIELD-INSTANCE-PREFIX|fulldoc|openai:qwen3.5-9b-ud-q8_k_xl|0`
- `dotnet-runtime-s2|rename|csharp_050___padding__DOTNET-FIELD-INSTANCE-PREFIX|naming|openai:qwen3.5-9b-ud-q8_k_xl|0`
