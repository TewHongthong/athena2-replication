# Athena Sim summary

1470 successful trials, 0 trial keys with only errors. Rates are per trial; repeats of the same unit are pooled (treat CIs and p-values as exploratory).

Split: test.

> Run `s2test_qwen35_9b_or_s2_godot-s2_meta` (test split) was started from freeze `frozen_godot-s2_qwen35_9b_or_s2_meta.json` (sha256 50f50b8d8fb5).

## rename - pack `godot-s2`

### By condition and backend

| backend | condition | n | parsed | exact match [95% CI] | violated rule ok | all core rules ok [95% CI] | type prefix kept | collision | similarity idx before -> after | retrieval hit | latency s | tokens in/out | cost USD |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| openai:qwen/qwen3.5-9b | none | 210 | 99.0% | 39.5% [33-46] | 49.5% | 49.5% [43-56] | - | 9.5% | 0.990 -> 0.986 | - | 10.62 | 80472/41152 | 0.0142 |
| openai:qwen/qwen3.5-9b | fulldoc | 210 | 97.1% | 64.8% [58-71] | 72.4% | 72.4% [66-78] | - | 2.4% | 0.990 -> 0.987 | - | 16.66 | 438732/83029 | 0.0563 |
| openai:qwen/qwen3.5-9b | chunk | 210 | 100.0% | 71.4% [65-77] | 73.3% | 73.3% [67-79] | - | 3.3% | 0.990 -> 0.994 | - | 8.78 | 120228/39498 | 0.0179 |
| openai:qwen/qwen3.5-9b | bm25 | 210 | 99.0% | 72.4% [66-78] | 73.3% | 73.3% [67-79] | - | 4.3% | 0.990 -> 0.994 | - | 9.94 | 122241/44393 | 0.0189 |
| openai:qwen/qwen3.5-9b | dense | 210 | 98.1% | 62.9% [56-69] | 63.8% | 63.8% [57-70] | - | 1.0% | 0.990 -> 0.988 | - | 11.61 | 106989/51130 | 0.0184 |
| openai:qwen/qwen3.5-9b | graph | 210 | 100.0% | 91.4% [87-95] | 100.0% | 100.0% [98-100] | - | 0.0% | 0.990 -> 0.998 | 100.0% | 7.43 | 113442/36054 | 0.0168 |
| openai:qwen/qwen3.5-9b | naming | 210 | 99.0% | 67.1% [61-73] | 85.2% | 85.2% [80-89] | - | 1.4% | 0.990 -> 0.992 | - | 11.78 | 111132/57194 | 0.0197 |

### By language (all core rules ok; n in brackets)

| backend | condition | cpp |
|---|---|---|
| openai:qwen/qwen3.5-9b | none | 49.5% [210] |
| openai:qwen/qwen3.5-9b | fulldoc | 72.4% [210] |
| openai:qwen/qwen3.5-9b | chunk | 73.3% [210] |
| openai:qwen/qwen3.5-9b | bm25 | 73.3% [210] |
| openai:qwen/qwen3.5-9b | dense | 63.8% [210] |
| openai:qwen/qwen3.5-9b | graph | 100.0% [210] |
| openai:qwen/qwen3.5-9b | naming | 85.2% [210] |

### Paired comparison against `none` (per unit, repeats averaged; exact two-sided sign test)

| backend | comparison | metric | units | better | worse | tied | mean diff (pp) | p | p (Holm) |
|---|---|---|---|---|---|---|---|---|---|
| openai:qwen/qwen3.5-9b | fulldoc vs none | core_ok | 70 | 39 | 14 | 17 | +22.9 | 0.000802 | 0.00235 |
| openai:qwen/qwen3.5-9b | chunk vs none | core_ok | 70 | 33 | 10 | 27 | +23.8 | 0.000606 | 0.00235 |
| openai:qwen/qwen3.5-9b | bm25 vs none | core_ok | 70 | 37 | 12 | 21 | +23.8 | 0.00047 | 0.00235 |
| openai:qwen/qwen3.5-9b | dense vs none | core_ok | 70 | 32 | 18 | 20 | +14.3 | 0.0649 | 0.0649 |
| openai:qwen/qwen3.5-9b | graph vs none | core_ok | 70 | 53 | 0 | 17 | +50.5 | 2.22e-16 | 2.66e-15 |
| openai:qwen/qwen3.5-9b | naming vs none | core_ok | 70 | 43 | 5 | 22 | +35.7 | 1.37e-08 | 1.37e-07 |
| openai:qwen/qwen3.5-9b | fulldoc vs none | exact_match | 70 | 40 | 12 | 18 | +25.2 | 0.000128 | 0.000765 |
| openai:qwen/qwen3.5-9b | chunk vs none | exact_match | 70 | 39 | 10 | 21 | +31.9 | 3.85e-05 | 0.000269 |
| openai:qwen/qwen3.5-9b | bm25 vs none | exact_match | 70 | 43 | 9 | 18 | +32.9 | 2.04e-06 | 1.77e-05 |
| openai:qwen/qwen3.5-9b | dense vs none | exact_match | 70 | 37 | 12 | 21 | +23.3 | 0.00047 | 0.00235 |
| openai:qwen/qwen3.5-9b | graph vs none | exact_match | 70 | 51 | 0 | 19 | +51.9 | 8.88e-16 | 9.77e-15 |
| openai:qwen/qwen3.5-9b | naming vs none | exact_match | 70 | 41 | 8 | 21 | +27.6 | 1.96e-06 | 1.77e-05 |

`better`/`worse` count units. `p (Holm)` corrects for all comparisons in this table; only hypotheses written in HYPOTHESES.md before the test run are confirmatory.
