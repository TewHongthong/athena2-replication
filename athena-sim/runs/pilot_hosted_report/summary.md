# Athena Sim summary

1080 successful trials, 0 trial keys with only errors. Rates are per trial; repeats of the same unit are pooled (treat CIs and p-values as exploratory).

Split: dev.

## rename - pack `dotnet-runtime`

### By condition and backend

| backend | condition | n | parsed | exact match [95% CI] | violated rule ok | all core rules ok [95% CI] | type prefix kept | collision | similarity idx before -> after | retrieval hit | latency s | tokens in/out | cost USD |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| openai:google/gemini-3.1-flash-lite | none | 30 | 100.0% | 90.0% [74-97] | 100.0% | 100.0% [89-100] | - | 0.0% | 0.987 -> 0.999 | - | 1.33 | 12146/3139 | 0.0077 |
| openai:google/gemini-3.1-flash-lite | fulldoc | 30 | 100.0% | 96.7% [83-99] | 100.0% | 100.0% [89-100] | - | 0.0% | 0.987 -> 1.000 | - | 1.37 | 68816/3258 | 0.0221 |
| openai:google/gemini-3.1-flash-lite | chunk | 30 | 100.0% | 96.7% [83-99] | 100.0% | 100.0% [89-100] | - | 0.0% | 0.987 -> 1.000 | - | 1.36 | 21335/3246 | 0.0102 |
| openai:google/gemini-3.1-flash-lite | bm25 | 30 | 100.0% | 96.7% [83-99] | 100.0% | 100.0% [89-100] | - | 0.0% | 0.987 -> 1.000 | - | 1.44 | 24742/3278 | 0.0111 |
| openai:google/gemini-3.1-flash-lite | dense | 30 | 100.0% | 96.7% [83-99] | 100.0% | 100.0% [89-100] | - | 0.0% | 0.987 -> 1.000 | - | 1.35 | 17387/3260 | 0.0092 |
| openai:google/gemini-3.1-flash-lite | graph | 30 | 100.0% | 96.7% [83-99] | 100.0% | 100.0% [89-100] | - | 0.0% | 0.987 -> 1.000 | 100.0% | 1.34 | 12596/3373 | 0.0082 |
| openai:openai/gpt-6-luna | none | 30 | 100.0% | 100.0% [89-100] | 100.0% | 100.0% [89-100] | - | 0.0% | 0.987 -> 1.000 | - | 4.51 | 11080/5302 | 0.0038 |
| openai:openai/gpt-6-luna | fulldoc | 30 | 100.0% | 96.7% [83-99] | 100.0% | 100.0% [89-100] | - | 0.0% | 0.987 -> 1.000 | - | 4.55 | 63070/3938 | 0.0083 |
| openai:openai/gpt-6-luna | chunk | 30 | 100.0% | 96.7% [83-99] | 100.0% | 100.0% [89-100] | - | 0.0% | 0.987 -> 1.000 | - | 3.83 | 19070/4845 | 0.0043 |
| openai:openai/gpt-6-luna | bm25 | 30 | 100.0% | 96.7% [83-99] | 100.0% | 100.0% [89-100] | - | 0.0% | 0.987 -> 1.000 | - | 4.00 | 21852/5077 | 0.0047 |
| openai:openai/gpt-6-luna | dense | 30 | 100.0% | 100.0% [89-100] | 100.0% | 100.0% [89-100] | - | 0.0% | 0.987 -> 1.000 | - | 4.95 | 16016/7037 | 0.0051 |
| openai:openai/gpt-6-luna | graph | 30 | 100.0% | 96.7% [83-99] | 100.0% | 100.0% [89-100] | - | 0.0% | 0.987 -> 1.000 | 100.0% | 3.30 | 11530/3837 | 0.0031 |

### By language (all core rules ok; n in brackets)

| backend | condition | csharp |
|---|---|---|
| openai:google/gemini-3.1-flash-lite | none | 100.0% [30] |
| openai:google/gemini-3.1-flash-lite | fulldoc | 100.0% [30] |
| openai:google/gemini-3.1-flash-lite | chunk | 100.0% [30] |
| openai:google/gemini-3.1-flash-lite | bm25 | 100.0% [30] |
| openai:google/gemini-3.1-flash-lite | dense | 100.0% [30] |
| openai:google/gemini-3.1-flash-lite | graph | 100.0% [30] |
| openai:openai/gpt-6-luna | none | 100.0% [30] |
| openai:openai/gpt-6-luna | fulldoc | 100.0% [30] |
| openai:openai/gpt-6-luna | chunk | 100.0% [30] |
| openai:openai/gpt-6-luna | bm25 | 100.0% [30] |
| openai:openai/gpt-6-luna | dense | 100.0% [30] |
| openai:openai/gpt-6-luna | graph | 100.0% [30] |

### Paired comparison against `none` (per unit, repeats averaged; exact two-sided sign test)

| backend | comparison | metric | units | better | worse | tied | mean diff (pp) | p | p (Holm) |
|---|---|---|---|---|---|---|---|---|---|
| openai:google/gemini-3.1-flash-lite | fulldoc vs none | core_ok | 30 | 0 | 0 | 30 | +0.0 | 1 | 1 |
| openai:google/gemini-3.1-flash-lite | chunk vs none | core_ok | 30 | 0 | 0 | 30 | +0.0 | 1 | 1 |
| openai:google/gemini-3.1-flash-lite | bm25 vs none | core_ok | 30 | 0 | 0 | 30 | +0.0 | 1 | 1 |
| openai:google/gemini-3.1-flash-lite | dense vs none | core_ok | 30 | 0 | 0 | 30 | +0.0 | 1 | 1 |
| openai:google/gemini-3.1-flash-lite | graph vs none | core_ok | 30 | 0 | 0 | 30 | +0.0 | 1 | 1 |
| openai:google/gemini-3.1-flash-lite | fulldoc vs none | exact_match | 30 | 2 | 0 | 28 | +6.7 | 0.5 | 1 |
| openai:google/gemini-3.1-flash-lite | chunk vs none | exact_match | 30 | 2 | 0 | 28 | +6.7 | 0.5 | 1 |
| openai:google/gemini-3.1-flash-lite | bm25 vs none | exact_match | 30 | 2 | 0 | 28 | +6.7 | 0.5 | 1 |
| openai:google/gemini-3.1-flash-lite | dense vs none | exact_match | 30 | 2 | 0 | 28 | +6.7 | 0.5 | 1 |
| openai:google/gemini-3.1-flash-lite | graph vs none | exact_match | 30 | 2 | 0 | 28 | +6.7 | 0.5 | 1 |
| openai:openai/gpt-6-luna | fulldoc vs none | core_ok | 30 | 0 | 0 | 30 | +0.0 | 1 | 1 |
| openai:openai/gpt-6-luna | chunk vs none | core_ok | 30 | 0 | 0 | 30 | +0.0 | 1 | 1 |
| openai:openai/gpt-6-luna | bm25 vs none | core_ok | 30 | 0 | 0 | 30 | +0.0 | 1 | 1 |
| openai:openai/gpt-6-luna | dense vs none | core_ok | 30 | 0 | 0 | 30 | +0.0 | 1 | 1 |
| openai:openai/gpt-6-luna | graph vs none | core_ok | 30 | 0 | 0 | 30 | +0.0 | 1 | 1 |
| openai:openai/gpt-6-luna | fulldoc vs none | exact_match | 30 | 0 | 1 | 29 | -3.3 | 1 | 1 |
| openai:openai/gpt-6-luna | chunk vs none | exact_match | 30 | 0 | 1 | 29 | -3.3 | 1 | 1 |
| openai:openai/gpt-6-luna | bm25 vs none | exact_match | 30 | 0 | 1 | 29 | -3.3 | 1 | 1 |
| openai:openai/gpt-6-luna | dense vs none | exact_match | 30 | 0 | 0 | 30 | +0.0 | 1 | 1 |
| openai:openai/gpt-6-luna | graph vs none | exact_match | 30 | 0 | 1 | 29 | -3.3 | 1 | 1 |

`better`/`worse` count units. `p (Holm)` corrects for all comparisons in this table; only hypotheses written in HYPOTHESES.md before the test run are confirmatory.

## rename - pack `godot`

### By condition and backend

| backend | condition | n | parsed | exact match [95% CI] | violated rule ok | all core rules ok [95% CI] | type prefix kept | collision | similarity idx before -> after | retrieval hit | latency s | tokens in/out | cost USD |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| openai:google/gemini-3.1-flash-lite | none | 30 | 100.0% | 80.0% [63-90] | 96.7% | 96.7% [83-99] | - | 6.7% | 0.926 -> 0.995 | - | 1.43 | 12494/3720 | 0.0087 |
| openai:google/gemini-3.1-flash-lite | fulldoc | 30 | 100.0% | 93.3% [79-98] | 100.0% | 100.0% [89-100] | - | 0.0% | 0.926 -> 0.997 | - | 1.54 | 65924/3603 | 0.0219 |
| openai:google/gemini-3.1-flash-lite | chunk | 30 | 100.0% | 100.0% [89-100] | 100.0% | 100.0% [89-100] | - | 0.0% | 0.926 -> 1.000 | - | 1.39 | 17591/3673 | 0.0099 |
| openai:google/gemini-3.1-flash-lite | bm25 | 30 | 100.0% | 96.7% [83-99] | 100.0% | 100.0% [89-100] | - | 0.0% | 0.926 -> 0.997 | - | 1.57 | 18028/3628 | 0.0099 |
| openai:google/gemini-3.1-flash-lite | dense | 30 | 100.0% | 96.7% [83-99] | 100.0% | 100.0% [89-100] | - | 0.0% | 0.926 -> 0.997 | - | 1.44 | 16686/3690 | 0.0097 |
| openai:google/gemini-3.1-flash-lite | graph | 30 | 100.0% | 93.3% [79-98] | 100.0% | 100.0% [89-100] | - | 0.0% | 0.926 -> 0.997 | 100.0% | 1.45 | 17054/4094 | 0.0104 |
| openai:openai/gpt-6-luna | none | 30 | 100.0% | 93.3% [79-98] | 100.0% | 100.0% [89-100] | - | 3.3% | 0.926 -> 0.999 | - | 4.65 | 11067/7467 | 0.0048 |
| openai:openai/gpt-6-luna | fulldoc | 30 | 100.0% | 90.0% [74-97] | 100.0% | 100.0% [89-100] | - | 0.0% | 0.926 -> 0.996 | - | 4.33 | 60657/4616 | 0.0084 |
| openai:openai/gpt-6-luna | chunk | 30 | 100.0% | 100.0% [89-100] | 100.0% | 100.0% [89-100] | - | 0.0% | 0.926 -> 1.000 | - | 4.15 | 15835/5878 | 0.0045 |
| openai:openai/gpt-6-luna | bm25 | 30 | 100.0% | 96.7% [83-99] | 100.0% | 100.0% [89-100] | - | 0.0% | 0.926 -> 1.000 | - | 4.23 | 16219/6265 | 0.0048 |
| openai:openai/gpt-6-luna | dense | 30 | 100.0% | 96.7% [83-99] | 100.0% | 100.0% [89-100] | - | 0.0% | 0.926 -> 1.000 | - | 4.68 | 14983/6117 | 0.0046 |
| openai:openai/gpt-6-luna | graph | 30 | 100.0% | 93.3% [79-98] | 100.0% | 100.0% [89-100] | - | 0.0% | 0.926 -> 0.997 | 100.0% | 4.26 | 15483/5011 | 0.0041 |

### By language (all core rules ok; n in brackets)

| backend | condition | cpp |
|---|---|---|
| openai:google/gemini-3.1-flash-lite | none | 96.7% [30] |
| openai:google/gemini-3.1-flash-lite | fulldoc | 100.0% [30] |
| openai:google/gemini-3.1-flash-lite | chunk | 100.0% [30] |
| openai:google/gemini-3.1-flash-lite | bm25 | 100.0% [30] |
| openai:google/gemini-3.1-flash-lite | dense | 100.0% [30] |
| openai:google/gemini-3.1-flash-lite | graph | 100.0% [30] |
| openai:openai/gpt-6-luna | none | 100.0% [30] |
| openai:openai/gpt-6-luna | fulldoc | 100.0% [30] |
| openai:openai/gpt-6-luna | chunk | 100.0% [30] |
| openai:openai/gpt-6-luna | bm25 | 100.0% [30] |
| openai:openai/gpt-6-luna | dense | 100.0% [30] |
| openai:openai/gpt-6-luna | graph | 100.0% [30] |

### Paired comparison against `none` (per unit, repeats averaged; exact two-sided sign test)

| backend | comparison | metric | units | better | worse | tied | mean diff (pp) | p | p (Holm) |
|---|---|---|---|---|---|---|---|---|---|
| openai:google/gemini-3.1-flash-lite | fulldoc vs none | core_ok | 30 | 1 | 0 | 29 | +3.3 | 1 | 1 |
| openai:google/gemini-3.1-flash-lite | chunk vs none | core_ok | 30 | 1 | 0 | 29 | +3.3 | 1 | 1 |
| openai:google/gemini-3.1-flash-lite | bm25 vs none | core_ok | 30 | 1 | 0 | 29 | +3.3 | 1 | 1 |
| openai:google/gemini-3.1-flash-lite | dense vs none | core_ok | 30 | 1 | 0 | 29 | +3.3 | 1 | 1 |
| openai:google/gemini-3.1-flash-lite | graph vs none | core_ok | 30 | 1 | 0 | 29 | +3.3 | 1 | 1 |
| openai:google/gemini-3.1-flash-lite | fulldoc vs none | exact_match | 30 | 5 | 1 | 24 | +13.3 | 0.219 | 1 |
| openai:google/gemini-3.1-flash-lite | chunk vs none | exact_match | 30 | 6 | 0 | 24 | +20.0 | 0.0312 | 0.625 |
| openai:google/gemini-3.1-flash-lite | bm25 vs none | exact_match | 30 | 5 | 0 | 25 | +16.7 | 0.0625 | 1 |
| openai:google/gemini-3.1-flash-lite | dense vs none | exact_match | 30 | 5 | 0 | 25 | +16.7 | 0.0625 | 1 |
| openai:google/gemini-3.1-flash-lite | graph vs none | exact_match | 30 | 5 | 1 | 24 | +13.3 | 0.219 | 1 |
| openai:openai/gpt-6-luna | fulldoc vs none | core_ok | 30 | 0 | 0 | 30 | +0.0 | 1 | 1 |
| openai:openai/gpt-6-luna | chunk vs none | core_ok | 30 | 0 | 0 | 30 | +0.0 | 1 | 1 |
| openai:openai/gpt-6-luna | bm25 vs none | core_ok | 30 | 0 | 0 | 30 | +0.0 | 1 | 1 |
| openai:openai/gpt-6-luna | dense vs none | core_ok | 30 | 0 | 0 | 30 | +0.0 | 1 | 1 |
| openai:openai/gpt-6-luna | graph vs none | core_ok | 30 | 0 | 0 | 30 | +0.0 | 1 | 1 |
| openai:openai/gpt-6-luna | fulldoc vs none | exact_match | 30 | 2 | 3 | 25 | -3.3 | 1 | 1 |
| openai:openai/gpt-6-luna | chunk vs none | exact_match | 30 | 2 | 0 | 28 | +6.7 | 0.5 | 1 |
| openai:openai/gpt-6-luna | bm25 vs none | exact_match | 30 | 2 | 1 | 27 | +3.3 | 1 | 1 |
| openai:openai/gpt-6-luna | dense vs none | exact_match | 30 | 2 | 1 | 27 | +3.3 | 1 | 1 |
| openai:openai/gpt-6-luna | graph vs none | exact_match | 30 | 2 | 2 | 26 | +0.0 | 1 | 1 |

`better`/`worse` count units. `p (Holm)` corrects for all comparisons in this table; only hypotheses written in HYPOTHESES.md before the test run are confirmatory.

## rename - pack `odoo`

### By condition and backend

| backend | condition | n | parsed | exact match [95% CI] | violated rule ok | all core rules ok [95% CI] | type prefix kept | collision | similarity idx before -> after | retrieval hit | latency s | tokens in/out | cost USD |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| openai:google/gemini-3.1-flash-lite | none | 30 | 100.0% | 96.7% [83-99] | 100.0% | 100.0% [89-100] | - | 3.3% | 0.952 -> 1.000 | - | 1.38 | 14066/3428 | 0.0087 |
| openai:google/gemini-3.1-flash-lite | fulldoc | 30 | 100.0% | 96.7% [83-99] | 100.0% | 100.0% [89-100] | - | 3.3% | 0.952 -> 1.000 | - | 1.61 | 399176/3399 | 0.1049 |
| openai:google/gemini-3.1-flash-lite | chunk | 30 | 100.0% | 93.3% [79-98] | 100.0% | 100.0% [89-100] | - | 3.3% | 0.952 -> 1.000 | - | 1.35 | 25372/3556 | 0.0117 |
| openai:google/gemini-3.1-flash-lite | bm25 | 30 | 100.0% | 96.7% [83-99] | 100.0% | 100.0% [89-100] | - | 3.3% | 0.952 -> 1.000 | - | 1.48 | 28186/3443 | 0.0122 |
| openai:google/gemini-3.1-flash-lite | dense | 30 | 100.0% | 93.3% [79-98] | 100.0% | 100.0% [89-100] | - | 3.3% | 0.952 -> 0.999 | - | 1.42 | 23263/3537 | 0.0111 |
| openai:google/gemini-3.1-flash-lite | graph | 30 | 100.0% | 96.7% [83-99] | 100.0% | 100.0% [89-100] | - | 3.3% | 0.952 -> 1.000 | 100.0% | 1.34 | 15116/3357 | 0.0088 |
| openai:openai/gpt-6-luna | none | 30 | 100.0% | 96.7% [83-99] | 100.0% | 100.0% [89-100] | - | 0.0% | 0.952 -> 0.999 | - | 5.19 | 12412/6330 | 0.0044 |
| openai:openai/gpt-6-luna | fulldoc | 30 | 100.0% | 90.0% [74-97] | 96.7% | 96.7% [83-99] | - | 3.3% | 0.952 -> 0.998 | - | 4.59 | 355192/5031 | 0.0380 |
| openai:openai/gpt-6-luna | chunk | 30 | 100.0% | 93.3% [79-98] | 100.0% | 100.0% [89-100] | - | 0.0% | 0.952 -> 0.996 | - | 4.84 | 21954/5728 | 0.0051 |
| openai:openai/gpt-6-luna | bm25 | 30 | 100.0% | 96.7% [83-99] | 100.0% | 100.0% [89-100] | - | 0.0% | 0.952 -> 0.999 | - | 4.74 | 24284/5901 | 0.0054 |
| openai:openai/gpt-6-luna | dense | 30 | 100.0% | 93.3% [79-98] | 100.0% | 100.0% [89-100] | - | 0.0% | 0.952 -> 0.999 | - | 4.62 | 20510/6177 | 0.0051 |
| openai:openai/gpt-6-luna | graph | 30 | 100.0% | 93.3% [79-98] | 100.0% | 100.0% [89-100] | - | 0.0% | 0.952 -> 0.998 | 100.0% | 3.87 | 13432/4540 | 0.0036 |

### By language (all core rules ok; n in brackets)

| backend | condition | python |
|---|---|---|
| openai:google/gemini-3.1-flash-lite | none | 100.0% [30] |
| openai:google/gemini-3.1-flash-lite | fulldoc | 100.0% [30] |
| openai:google/gemini-3.1-flash-lite | chunk | 100.0% [30] |
| openai:google/gemini-3.1-flash-lite | bm25 | 100.0% [30] |
| openai:google/gemini-3.1-flash-lite | dense | 100.0% [30] |
| openai:google/gemini-3.1-flash-lite | graph | 100.0% [30] |
| openai:openai/gpt-6-luna | none | 100.0% [30] |
| openai:openai/gpt-6-luna | fulldoc | 96.7% [30] |
| openai:openai/gpt-6-luna | chunk | 100.0% [30] |
| openai:openai/gpt-6-luna | bm25 | 100.0% [30] |
| openai:openai/gpt-6-luna | dense | 100.0% [30] |
| openai:openai/gpt-6-luna | graph | 100.0% [30] |

### Paired comparison against `none` (per unit, repeats averaged; exact two-sided sign test)

| backend | comparison | metric | units | better | worse | tied | mean diff (pp) | p | p (Holm) |
|---|---|---|---|---|---|---|---|---|---|
| openai:google/gemini-3.1-flash-lite | fulldoc vs none | core_ok | 30 | 0 | 0 | 30 | +0.0 | 1 | 1 |
| openai:google/gemini-3.1-flash-lite | chunk vs none | core_ok | 30 | 0 | 0 | 30 | +0.0 | 1 | 1 |
| openai:google/gemini-3.1-flash-lite | bm25 vs none | core_ok | 30 | 0 | 0 | 30 | +0.0 | 1 | 1 |
| openai:google/gemini-3.1-flash-lite | dense vs none | core_ok | 30 | 0 | 0 | 30 | +0.0 | 1 | 1 |
| openai:google/gemini-3.1-flash-lite | graph vs none | core_ok | 30 | 0 | 0 | 30 | +0.0 | 1 | 1 |
| openai:google/gemini-3.1-flash-lite | fulldoc vs none | exact_match | 30 | 0 | 0 | 30 | +0.0 | 1 | 1 |
| openai:google/gemini-3.1-flash-lite | chunk vs none | exact_match | 30 | 0 | 1 | 29 | -3.3 | 1 | 1 |
| openai:google/gemini-3.1-flash-lite | bm25 vs none | exact_match | 30 | 0 | 0 | 30 | +0.0 | 1 | 1 |
| openai:google/gemini-3.1-flash-lite | dense vs none | exact_match | 30 | 0 | 1 | 29 | -3.3 | 1 | 1 |
| openai:google/gemini-3.1-flash-lite | graph vs none | exact_match | 30 | 0 | 0 | 30 | +0.0 | 1 | 1 |
| openai:openai/gpt-6-luna | fulldoc vs none | core_ok | 30 | 0 | 1 | 29 | -3.3 | 1 | 1 |
| openai:openai/gpt-6-luna | chunk vs none | core_ok | 30 | 0 | 0 | 30 | +0.0 | 1 | 1 |
| openai:openai/gpt-6-luna | bm25 vs none | core_ok | 30 | 0 | 0 | 30 | +0.0 | 1 | 1 |
| openai:openai/gpt-6-luna | dense vs none | core_ok | 30 | 0 | 0 | 30 | +0.0 | 1 | 1 |
| openai:openai/gpt-6-luna | graph vs none | core_ok | 30 | 0 | 0 | 30 | +0.0 | 1 | 1 |
| openai:openai/gpt-6-luna | fulldoc vs none | exact_match | 30 | 1 | 3 | 26 | -6.7 | 0.625 | 1 |
| openai:openai/gpt-6-luna | chunk vs none | exact_match | 30 | 1 | 2 | 27 | -3.3 | 1 | 1 |
| openai:openai/gpt-6-luna | bm25 vs none | exact_match | 30 | 0 | 0 | 30 | +0.0 | 1 | 1 |
| openai:openai/gpt-6-luna | dense vs none | exact_match | 30 | 0 | 1 | 29 | -3.3 | 1 | 1 |
| openai:openai/gpt-6-luna | graph vs none | exact_match | 30 | 0 | 1 | 29 | -3.3 | 1 | 1 |

`better`/`worse` count units. `p (Holm)` corrects for all comparisons in this table; only hypotheses written in HYPOTHESES.md before the test run are confirmatory.
