# Athena Sim summary

1260 successful trials, 0 trial keys with only errors. Rates are per trial; repeats of the same unit are pooled (treat CIs and p-values as exploratory).

Split: test.

> Run `test_dotnet-runtime_luna_meta` (test split) was started from freeze `frozen_dotnet-runtime_luna_meta.json` (sha256 9a71d09a2cb9).

## rename - pack `dotnet-runtime`

### By condition and backend

| backend | condition | n | parsed | exact match [95% CI] | violated rule ok | all core rules ok [95% CI] | type prefix kept | collision | similarity idx before -> after | retrieval hit | latency s | tokens in/out | cost USD |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| openai:openai/gpt-6-luna | none | 210 | 100.0% | 98.6% [96-100] | 100.0% | 100.0% [98-100] | - | 0.0% | 0.988 -> 1.000 | - | 3.85 | 83607/39616 | 0.0282 |
| openai:openai/gpt-6-luna | fulldoc | 210 | 100.0% | 98.6% [96-100] | 100.0% | 100.0% [98-100] | - | 0.0% | 0.988 -> 1.000 | - | 3.24 | 447537/29272 | 0.0594 |
| openai:openai/gpt-6-luna | chunk | 210 | 100.0% | 98.6% [96-100] | 100.0% | 100.0% [98-100] | - | 0.0% | 0.988 -> 1.000 | - | 3.60 | 130671/34195 | 0.0302 |
| openai:openai/gpt-6-luna | bm25 | 210 | 100.0% | 98.6% [96-100] | 100.0% | 100.0% [98-100] | - | 0.0% | 0.988 -> 1.000 | - | 3.94 | 148470/39562 | 0.0346 |
| openai:openai/gpt-6-luna | dense | 210 | 99.5% | 97.1% [94-99] | 99.5% | 99.5% [97-100] | - | 0.0% | 0.988 -> 1.000 | - | 4.48 | 122517/51924 | 0.0382 |
| openai:openai/gpt-6-luna | graph | 210 | 100.0% | 98.6% [96-100] | 100.0% | 100.0% [98-100] | - | 0.0% | 0.988 -> 1.000 | 100.0% | 3.08 | 86757/28352 | 0.0229 |

### By language (all core rules ok; n in brackets)

| backend | condition | csharp |
|---|---|---|
| openai:openai/gpt-6-luna | none | 100.0% [210] |
| openai:openai/gpt-6-luna | fulldoc | 100.0% [210] |
| openai:openai/gpt-6-luna | chunk | 100.0% [210] |
| openai:openai/gpt-6-luna | bm25 | 100.0% [210] |
| openai:openai/gpt-6-luna | dense | 99.5% [210] |
| openai:openai/gpt-6-luna | graph | 100.0% [210] |

### Paired comparison against `none` (per unit, repeats averaged; exact two-sided sign test)

| backend | comparison | metric | units | better | worse | tied | mean diff (pp) | p | p (Holm) |
|---|---|---|---|---|---|---|---|---|---|
| openai:openai/gpt-6-luna | fulldoc vs none | core_ok | 70 | 0 | 0 | 70 | +0.0 | 1 | 1 |
| openai:openai/gpt-6-luna | chunk vs none | core_ok | 70 | 0 | 0 | 70 | +0.0 | 1 | 1 |
| openai:openai/gpt-6-luna | bm25 vs none | core_ok | 70 | 0 | 0 | 70 | +0.0 | 1 | 1 |
| openai:openai/gpt-6-luna | dense vs none | core_ok | 70 | 0 | 1 | 69 | -0.5 | 1 | 1 |
| openai:openai/gpt-6-luna | graph vs none | core_ok | 70 | 0 | 0 | 70 | +0.0 | 1 | 1 |
| openai:openai/gpt-6-luna | fulldoc vs none | exact_match | 70 | 0 | 0 | 70 | +0.0 | 1 | 1 |
| openai:openai/gpt-6-luna | chunk vs none | exact_match | 70 | 0 | 0 | 70 | +0.0 | 1 | 1 |
| openai:openai/gpt-6-luna | bm25 vs none | exact_match | 70 | 0 | 0 | 70 | +0.0 | 1 | 1 |
| openai:openai/gpt-6-luna | dense vs none | exact_match | 70 | 1 | 2 | 67 | -1.4 | 1 | 1 |
| openai:openai/gpt-6-luna | graph vs none | exact_match | 70 | 0 | 0 | 70 | +0.0 | 1 | 1 |

`better`/`worse` count units. `p (Holm)` corrects for all comparisons in this table; only hypotheses written in HYPOTHESES.md before the test run are confirmatory.
