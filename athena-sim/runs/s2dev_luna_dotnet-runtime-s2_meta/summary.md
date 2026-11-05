# Athena Sim summary

133 successful trials, 0 trial keys with only errors. Rates are per trial; repeats of the same unit are pooled (treat CIs and p-values as exploratory).

Split: dev.

## rename - pack `dotnet-runtime-s2`

### By condition and backend

| backend | condition | n | parsed | exact match [95% CI] | violated rule ok | all core rules ok [95% CI] | type prefix kept | collision | similarity idx before -> after | retrieval hit | latency s | tokens in/out | cost USD |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| openai:openai/gpt-6-luna | none | 19 | 100.0% | 100.0% [83-100] | 100.0% | 100.0% [83-100] | - | 0.0% | 0.998 -> 1.000 | - | 3.48 | 9874/3648 | 0.0028 |
| openai:openai/gpt-6-luna | fulldoc | 19 | 100.0% | 100.0% [83-100] | 100.0% | 100.0% [83-100] | - | 0.0% | 0.998 -> 1.000 | - | 2.88 | 42801/2579 | 0.0056 |
| openai:openai/gpt-6-luna | chunk | 19 | 100.0% | 94.7% [75-99] | 94.7% | 94.7% [75-99] | - | 0.0% | 0.998 -> 1.000 | - | 3.23 | 17376/3117 | 0.0033 |
| openai:openai/gpt-6-luna | bm25 | 19 | 100.0% | 94.7% [75-99] | 94.7% | 94.7% [75-99] | - | 0.0% | 0.998 -> 1.000 | - | 3.20 | 17661/3022 | 0.0033 |
| openai:openai/gpt-6-luna | dense | 19 | 100.0% | 100.0% [83-100] | 100.0% | 100.0% [83-100] | - | 0.0% | 0.998 -> 1.000 | - | 3.34 | 13367/3568 | 0.0031 |
| openai:openai/gpt-6-luna | graph | 19 | 100.0% | 89.5% [69-97] | 100.0% | 100.0% [83-100] | - | 0.0% | 0.998 -> 1.000 | 100.0% | 2.92 | 10888/2718 | 0.0024 |
| openai:openai/gpt-6-luna | naming | 19 | 100.0% | 100.0% [83-100] | 100.0% | 100.0% [83-100] | - | 0.0% | 0.998 -> 1.000 | - | 2.78 | 14985/2681 | 0.0028 |

### By language (all core rules ok; n in brackets)

| backend | condition | csharp |
|---|---|---|
| openai:openai/gpt-6-luna | none | 100.0% [19] |
| openai:openai/gpt-6-luna | fulldoc | 100.0% [19] |
| openai:openai/gpt-6-luna | chunk | 94.7% [19] |
| openai:openai/gpt-6-luna | bm25 | 94.7% [19] |
| openai:openai/gpt-6-luna | dense | 100.0% [19] |
| openai:openai/gpt-6-luna | graph | 100.0% [19] |
| openai:openai/gpt-6-luna | naming | 100.0% [19] |

### Paired comparison against `none` (per unit, repeats averaged; exact two-sided sign test)

| backend | comparison | metric | units | better | worse | tied | mean diff (pp) | p | p (Holm) |
|---|---|---|---|---|---|---|---|---|---|
| openai:openai/gpt-6-luna | fulldoc vs none | core_ok | 19 | 0 | 0 | 19 | +0.0 | 1 | 1 |
| openai:openai/gpt-6-luna | chunk vs none | core_ok | 19 | 0 | 1 | 18 | -5.3 | 1 | 1 |
| openai:openai/gpt-6-luna | bm25 vs none | core_ok | 19 | 0 | 1 | 18 | -5.3 | 1 | 1 |
| openai:openai/gpt-6-luna | dense vs none | core_ok | 19 | 0 | 0 | 19 | +0.0 | 1 | 1 |
| openai:openai/gpt-6-luna | graph vs none | core_ok | 19 | 0 | 0 | 19 | +0.0 | 1 | 1 |
| openai:openai/gpt-6-luna | naming vs none | core_ok | 19 | 0 | 0 | 19 | +0.0 | 1 | 1 |
| openai:openai/gpt-6-luna | fulldoc vs none | exact_match | 19 | 0 | 0 | 19 | +0.0 | 1 | 1 |
| openai:openai/gpt-6-luna | chunk vs none | exact_match | 19 | 0 | 1 | 18 | -5.3 | 1 | 1 |
| openai:openai/gpt-6-luna | bm25 vs none | exact_match | 19 | 0 | 1 | 18 | -5.3 | 1 | 1 |
| openai:openai/gpt-6-luna | dense vs none | exact_match | 19 | 0 | 0 | 19 | +0.0 | 1 | 1 |
| openai:openai/gpt-6-luna | graph vs none | exact_match | 19 | 0 | 2 | 17 | -10.5 | 0.5 | 1 |
| openai:openai/gpt-6-luna | naming vs none | exact_match | 19 | 0 | 0 | 19 | +0.0 | 1 | 1 |

`better`/`worse` count units. `p (Holm)` corrects for all comparisons in this table; only hypotheses written in HYPOTHESES.md before the test run are confirmatory.
