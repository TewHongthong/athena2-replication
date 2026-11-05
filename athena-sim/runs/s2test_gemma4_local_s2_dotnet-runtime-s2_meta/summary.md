# Athena Sim summary

945 successful trials, 0 trial keys with only errors. Rates are per trial; repeats of the same unit are pooled (treat CIs and p-values as exploratory).

Split: test.

> Run `s2test_gemma4_local_s2_dotnet-runtime-s2_meta` (test split) was started from freeze `frozen_dotnet-runtime-s2_gemma4_local_s2_meta.json` (sha256 f226b6bd8f29).

## rename - pack `dotnet-runtime-s2`

### By condition and backend

| backend | condition | n | parsed | exact match [95% CI] | violated rule ok | all core rules ok [95% CI] | type prefix kept | collision | similarity idx before -> after | retrieval hit | latency s | tokens in/out | cost USD |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| openai:gemma-4-26b-a4b-it-ud-q4_k_m | none | 135 | 98.5% | 93.3% [88-96] | 93.3% | 93.3% [88-96] | - | 2.2% | 0.997 -> 1.000 | - | 3.05 | 76416/17441 | - |
| openai:gemma-4-26b-a4b-it-ud-q4_k_m | fulldoc | 135 | 100.0% | 100.0% [97-100] | 100.0% | 100.0% [97-100] | - | 0.0% | 0.997 -> 1.000 | - | 3.56 | 331431/14610 | - |
| openai:gemma-4-26b-a4b-it-ud-q4_k_m | chunk | 135 | 100.0% | 97.8% [94-99] | 97.8% | 97.8% [94-99] | - | 2.2% | 0.997 -> 1.000 | - | 3.04 | 128940/15673 | - |
| openai:gemma-4-26b-a4b-it-ud-q4_k_m | bm25 | 135 | 100.0% | 100.0% [97-100] | 100.0% | 100.0% [97-100] | - | 0.0% | 0.997 -> 1.000 | - | 3.00 | 138678/16154 | - |
| openai:gemma-4-26b-a4b-it-ud-q4_k_m | dense | 135 | 100.0% | 97.8% [94-99] | 97.8% | 97.8% [94-99] | - | 0.0% | 0.997 -> 1.000 | - | 2.89 | 105684/15068 | - |
| openai:gemma-4-26b-a4b-it-ud-q4_k_m | graph | 135 | 100.0% | 93.3% [88-96] | 100.0% | 100.0% [97-100] | - | 0.0% | 0.997 -> 0.999 | 100.0% | 3.12 | 84006/17759 | - |
| openai:gemma-4-26b-a4b-it-ud-q4_k_m | naming | 135 | 100.0% | 100.0% [97-100] | 100.0% | 100.0% [97-100] | - | 0.0% | 0.997 -> 1.000 | - | 2.88 | 114486/14445 | - |

### By language (all core rules ok; n in brackets)

| backend | condition | csharp |
|---|---|---|
| openai:gemma-4-26b-a4b-it-ud-q4_k_m | none | 93.3% [135] |
| openai:gemma-4-26b-a4b-it-ud-q4_k_m | fulldoc | 100.0% [135] |
| openai:gemma-4-26b-a4b-it-ud-q4_k_m | chunk | 97.8% [135] |
| openai:gemma-4-26b-a4b-it-ud-q4_k_m | bm25 | 100.0% [135] |
| openai:gemma-4-26b-a4b-it-ud-q4_k_m | dense | 97.8% [135] |
| openai:gemma-4-26b-a4b-it-ud-q4_k_m | graph | 100.0% [135] |
| openai:gemma-4-26b-a4b-it-ud-q4_k_m | naming | 100.0% [135] |

### Paired comparison against `none` (per unit, repeats averaged; exact two-sided sign test)

| backend | comparison | metric | units | better | worse | tied | mean diff (pp) | p | p (Holm) |
|---|---|---|---|---|---|---|---|---|---|
| openai:gemma-4-26b-a4b-it-ud-q4_k_m | fulldoc vs none | core_ok | 45 | 4 | 0 | 41 | +6.7 | 0.125 | 1 |
| openai:gemma-4-26b-a4b-it-ud-q4_k_m | chunk vs none | core_ok | 45 | 3 | 1 | 41 | +4.4 | 0.625 | 1 |
| openai:gemma-4-26b-a4b-it-ud-q4_k_m | bm25 vs none | core_ok | 45 | 4 | 0 | 41 | +6.7 | 0.125 | 1 |
| openai:gemma-4-26b-a4b-it-ud-q4_k_m | dense vs none | core_ok | 45 | 3 | 0 | 42 | +4.4 | 0.25 | 1 |
| openai:gemma-4-26b-a4b-it-ud-q4_k_m | graph vs none | core_ok | 45 | 4 | 0 | 41 | +6.7 | 0.125 | 1 |
| openai:gemma-4-26b-a4b-it-ud-q4_k_m | naming vs none | core_ok | 45 | 4 | 0 | 41 | +6.7 | 0.125 | 1 |
| openai:gemma-4-26b-a4b-it-ud-q4_k_m | fulldoc vs none | exact_match | 45 | 4 | 0 | 41 | +6.7 | 0.125 | 1 |
| openai:gemma-4-26b-a4b-it-ud-q4_k_m | chunk vs none | exact_match | 45 | 3 | 1 | 41 | +4.4 | 0.625 | 1 |
| openai:gemma-4-26b-a4b-it-ud-q4_k_m | bm25 vs none | exact_match | 45 | 4 | 0 | 41 | +6.7 | 0.125 | 1 |
| openai:gemma-4-26b-a4b-it-ud-q4_k_m | dense vs none | exact_match | 45 | 3 | 0 | 42 | +4.4 | 0.25 | 1 |
| openai:gemma-4-26b-a4b-it-ud-q4_k_m | graph vs none | exact_match | 45 | 4 | 5 | 36 | -0.0 | 1 | 1 |
| openai:gemma-4-26b-a4b-it-ud-q4_k_m | naming vs none | exact_match | 45 | 4 | 0 | 41 | +6.7 | 0.125 | 1 |

`better`/`worse` count units. `p (Holm)` corrects for all comparisons in this table; only hypotheses written in HYPOTHESES.md before the test run are confirmatory.
