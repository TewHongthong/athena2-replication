# Athena Sim summary

945 successful trials, 0 trial keys with only errors. Rates are per trial; repeats of the same unit are pooled (treat CIs and p-values as exploratory).

Split: test.

> Run `s2test_qwen35_9b_or_s2_dotnet-runtime-s2_meta` (test split) was started from freeze `frozen_dotnet-runtime-s2_qwen35_9b_or_s2_meta.json` (sha256 2de1daf96d74).

## rename - pack `dotnet-runtime-s2`

### By condition and backend

| backend | condition | n | parsed | exact match [95% CI] | violated rule ok | all core rules ok [95% CI] | type prefix kept | collision | similarity idx before -> after | retrieval hit | latency s | tokens in/out | cost USD |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| openai:qwen/qwen3.5-9b | none | 135 | 95.6% | 37.0% [29-45] | 38.5% | 38.5% [31-47] | - | 17.8% | 0.997 -> 0.995 | - | 8.47 | 73107/22336 | 0.0107 |
| openai:qwen/qwen3.5-9b | fulldoc | 135 | 100.0% | 99.3% [96-100] | 100.0% | 100.0% [97-100] | - | 0.0% | 0.997 -> 1.000 | - | 5.31 | 318267/17187 | 0.0344 |
| openai:qwen/qwen3.5-9b | chunk | 135 | 93.3% | 74.1% [66-81] | 75.6% | 75.6% [68-82] | - | 7.4% | 0.997 -> 0.998 | - | 15.26 | 122691/64878 | 0.0220 |
| openai:qwen/qwen3.5-9b | bm25 | 135 | 95.6% | 72.6% [65-79] | 74.1% | 74.1% [66-81] | - | 4.4% | 0.997 -> 0.997 | - | 11.84 | 131784/48877 | 0.0205 |
| openai:qwen/qwen3.5-9b | dense | 135 | 98.5% | 80.7% [73-87] | 81.5% | 81.5% [74-87] | - | 5.9% | 0.997 -> 0.999 | - | 7.38 | 101256/28071 | 0.0143 |
| openai:qwen/qwen3.5-9b | graph | 135 | 100.0% | 91.1% [85-95] | 99.3% | 99.3% [96-100] | - | 0.7% | 0.997 -> 1.000 | 100.0% | 5.36 | 80421/21019 | 0.0112 |
| openai:qwen/qwen3.5-9b | naming | 135 | 96.3% | 94.1% [89-97] | 96.3% | 96.3% [92-98] | - | 0.0% | 0.997 -> 1.000 | - | 5.58 | 109557/17970 | 0.0137 |

### By language (all core rules ok; n in brackets)

| backend | condition | csharp |
|---|---|---|
| openai:qwen/qwen3.5-9b | none | 38.5% [135] |
| openai:qwen/qwen3.5-9b | fulldoc | 100.0% [135] |
| openai:qwen/qwen3.5-9b | chunk | 75.6% [135] |
| openai:qwen/qwen3.5-9b | bm25 | 74.1% [135] |
| openai:qwen/qwen3.5-9b | dense | 81.5% [135] |
| openai:qwen/qwen3.5-9b | graph | 99.3% [135] |
| openai:qwen/qwen3.5-9b | naming | 96.3% [135] |

### Paired comparison against `none` (per unit, repeats averaged; exact two-sided sign test)

| backend | comparison | metric | units | better | worse | tied | mean diff (pp) | p | p (Holm) |
|---|---|---|---|---|---|---|---|---|---|
| openai:qwen/qwen3.5-9b | fulldoc vs none | core_ok | 45 | 38 | 0 | 7 | +61.5 | 7.28e-12 | 8.73e-11 |
| openai:qwen/qwen3.5-9b | chunk vs none | core_ok | 45 | 30 | 5 | 10 | +37.0 | 2.24e-05 | 0.000134 |
| openai:qwen/qwen3.5-9b | bm25 vs none | core_ok | 45 | 31 | 6 | 8 | +35.6 | 4.13e-05 | 0.000165 |
| openai:qwen/qwen3.5-9b | dense vs none | core_ok | 45 | 31 | 8 | 6 | +43.0 | 0.000294 | 0.000588 |
| openai:qwen/qwen3.5-9b | graph vs none | core_ok | 45 | 38 | 0 | 7 | +60.7 | 7.28e-12 | 8.73e-11 |
| openai:qwen/qwen3.5-9b | naming vs none | core_ok | 45 | 37 | 3 | 5 | +57.8 | 1.95e-08 | 1.56e-07 |
| openai:qwen/qwen3.5-9b | fulldoc vs none | exact_match | 45 | 38 | 1 | 6 | +62.2 | 1.46e-10 | 1.46e-09 |
| openai:qwen/qwen3.5-9b | chunk vs none | exact_match | 45 | 30 | 5 | 10 | +37.0 | 2.24e-05 | 0.000134 |
| openai:qwen/qwen3.5-9b | bm25 vs none | exact_match | 45 | 29 | 6 | 10 | +35.6 | 0.000117 | 0.000351 |
| openai:qwen/qwen3.5-9b | dense vs none | exact_match | 45 | 31 | 8 | 6 | +43.7 | 0.000294 | 0.000588 |
| openai:qwen/qwen3.5-9b | graph vs none | exact_match | 45 | 36 | 2 | 7 | +54.1 | 5.4e-09 | 4.86e-08 |
| openai:qwen/qwen3.5-9b | naming vs none | exact_match | 45 | 37 | 5 | 3 | +57.0 | 4.43e-07 | 3.1e-06 |

`better`/`worse` count units. `p (Holm)` corrects for all comparisons in this table; only hypotheses written in HYPOTHESES.md before the test run are confirmatory.
