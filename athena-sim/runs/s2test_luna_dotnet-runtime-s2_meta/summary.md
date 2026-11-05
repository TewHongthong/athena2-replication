# Athena Sim summary

945 successful trials, 0 trial keys with only errors. Rates are per trial; repeats of the same unit are pooled (treat CIs and p-values as exploratory).

Split: test.

> Run `s2test_luna_dotnet-runtime-s2_meta` (test split) was started from freeze `frozen_dotnet-runtime-s2_luna_meta.json` (sha256 ca4d559edff2).

## rename - pack `dotnet-runtime-s2`

### By condition and backend

| backend | condition | n | parsed | exact match [95% CI] | violated rule ok | all core rules ok [95% CI] | type prefix kept | collision | similarity idx before -> after | retrieval hit | latency s | tokens in/out | cost USD |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| openai:openai/gpt-6-luna | none | 135 | 100.0% | 100.0% [97-100] | 100.0% | 100.0% [97-100] | - | 0.0% | 0.997 -> 1.000 | - | 4.17 | 68067/24346 | 0.0190 |
| openai:openai/gpt-6-luna | fulldoc | 135 | 100.0% | 100.0% [97-100] | 100.0% | 100.0% [97-100] | - | 0.0% | 0.997 -> 1.000 | - | 3.68 | 302022/18981 | 0.0397 |
| openai:openai/gpt-6-luna | chunk | 135 | 100.0% | 100.0% [97-100] | 100.0% | 100.0% [97-100] | - | 0.0% | 0.997 -> 1.000 | - | 3.53 | 113967/21970 | 0.0224 |
| openai:openai/gpt-6-luna | bm25 | 135 | 100.0% | 100.0% [97-100] | 100.0% | 100.0% [97-100] | - | 0.0% | 0.997 -> 1.000 | - | 3.65 | 122052/22021 | 0.0232 |
| openai:openai/gpt-6-luna | dense | 135 | 100.0% | 98.5% [95-100] | 98.5% | 98.5% [95-100] | - | 0.0% | 0.997 -> 1.000 | - | 3.76 | 95862/22685 | 0.0209 |
| openai:openai/gpt-6-luna | graph | 135 | 100.0% | 93.3% [88-96] | 100.0% | 100.0% [97-100] | - | 0.0% | 0.997 -> 1.000 | 100.0% | 3.20 | 75243/18524 | 0.0168 |
| openai:openai/gpt-6-luna | naming | 135 | 100.0% | 100.0% [97-100] | 100.0% | 100.0% [97-100] | - | 0.0% | 0.997 -> 1.000 | - | 3.56 | 104382/19015 | 0.0199 |

### By language (all core rules ok; n in brackets)

| backend | condition | csharp |
|---|---|---|
| openai:openai/gpt-6-luna | none | 100.0% [135] |
| openai:openai/gpt-6-luna | fulldoc | 100.0% [135] |
| openai:openai/gpt-6-luna | chunk | 100.0% [135] |
| openai:openai/gpt-6-luna | bm25 | 100.0% [135] |
| openai:openai/gpt-6-luna | dense | 98.5% [135] |
| openai:openai/gpt-6-luna | graph | 100.0% [135] |
| openai:openai/gpt-6-luna | naming | 100.0% [135] |

### Paired comparison against `none` (per unit, repeats averaged; exact two-sided sign test)

| backend | comparison | metric | units | better | worse | tied | mean diff (pp) | p | p (Holm) |
|---|---|---|---|---|---|---|---|---|---|
| openai:openai/gpt-6-luna | fulldoc vs none | core_ok | 45 | 0 | 0 | 45 | +0.0 | 1 | 1 |
| openai:openai/gpt-6-luna | chunk vs none | core_ok | 45 | 0 | 0 | 45 | +0.0 | 1 | 1 |
| openai:openai/gpt-6-luna | bm25 vs none | core_ok | 45 | 0 | 0 | 45 | +0.0 | 1 | 1 |
| openai:openai/gpt-6-luna | dense vs none | core_ok | 45 | 0 | 1 | 44 | -1.5 | 1 | 1 |
| openai:openai/gpt-6-luna | graph vs none | core_ok | 45 | 0 | 0 | 45 | +0.0 | 1 | 1 |
| openai:openai/gpt-6-luna | naming vs none | core_ok | 45 | 0 | 0 | 45 | +0.0 | 1 | 1 |
| openai:openai/gpt-6-luna | fulldoc vs none | exact_match | 45 | 0 | 0 | 45 | +0.0 | 1 | 1 |
| openai:openai/gpt-6-luna | chunk vs none | exact_match | 45 | 0 | 0 | 45 | +0.0 | 1 | 1 |
| openai:openai/gpt-6-luna | bm25 vs none | exact_match | 45 | 0 | 0 | 45 | +0.0 | 1 | 1 |
| openai:openai/gpt-6-luna | dense vs none | exact_match | 45 | 0 | 1 | 44 | -1.5 | 1 | 1 |
| openai:openai/gpt-6-luna | graph vs none | exact_match | 45 | 0 | 4 | 41 | -6.7 | 0.125 | 1 |
| openai:openai/gpt-6-luna | naming vs none | exact_match | 45 | 0 | 0 | 45 | +0.0 | 1 | 1 |

`better`/`worse` count units. `p (Holm)` corrects for all comparisons in this table; only hypotheses written in HYPOTHESES.md before the test run are confirmatory.
