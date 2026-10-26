# Athena Sim summary

1260 successful trials, 0 trial keys with only errors. Rates are per trial; repeats of the same unit are pooled (treat CIs and p-values as exploratory).

Split: test.

> Run `test_dotnet-runtime_gemma4_local_meta` (test split) was started from freeze `frozen_dotnet-runtime_gemma4_local_meta.json` (sha256 130381990477).

## rename - pack `dotnet-runtime`

### By condition and backend

| backend | condition | n | parsed | exact match [95% CI] | violated rule ok | all core rules ok [95% CI] | type prefix kept | collision | similarity idx before -> after | retrieval hit | latency s | tokens in/out | cost USD |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| openai:gemma-4-26b-a4b-it-ud-q4_k_m | none | 210 | 100.0% | 95.2% [91-97] | 98.6% | 98.6% [96-100] | - | 0.0% | 0.988 -> 1.000 | - | 2.54 | 95070/22564 | - |
| openai:gemma-4-26b-a4b-it-ud-q4_k_m | fulldoc | 210 | 100.0% | 99.5% [97-100] | 100.0% | 100.0% [98-100] | - | 0.0% | 0.988 -> 1.000 | - | 3.55 | 491760/22911 | - |
| openai:gemma-4-26b-a4b-it-ud-q4_k_m | chunk | 210 | 100.0% | 96.2% [93-98] | 99.0% | 99.0% [97-100] | - | 0.0% | 0.988 -> 1.000 | - | 2.81 | 148782/22453 | - |
| openai:gemma-4-26b-a4b-it-ud-q4_k_m | bm25 | 210 | 100.0% | 99.0% [97-100] | 100.0% | 100.0% [98-100] | - | 0.0% | 0.988 -> 1.000 | - | 2.74 | 170202/23032 | - |
| openai:gemma-4-26b-a4b-it-ud-q4_k_m | dense | 210 | 100.0% | 95.7% [92-98] | 99.5% | 99.5% [97-100] | - | 0.0% | 0.988 -> 1.000 | - | 2.81 | 136935/23884 | - |
| openai:gemma-4-26b-a4b-it-ud-q4_k_m | graph | 210 | 100.0% | 98.1% [95-99] | 100.0% | 100.0% [98-100] | - | 0.0% | 0.988 -> 1.000 | 100.0% | 2.55 | 98220/22393 | - |

### By language (all core rules ok; n in brackets)

| backend | condition | csharp |
|---|---|---|
| openai:gemma-4-26b-a4b-it-ud-q4_k_m | none | 98.6% [210] |
| openai:gemma-4-26b-a4b-it-ud-q4_k_m | fulldoc | 100.0% [210] |
| openai:gemma-4-26b-a4b-it-ud-q4_k_m | chunk | 99.0% [210] |
| openai:gemma-4-26b-a4b-it-ud-q4_k_m | bm25 | 100.0% [210] |
| openai:gemma-4-26b-a4b-it-ud-q4_k_m | dense | 99.5% [210] |
| openai:gemma-4-26b-a4b-it-ud-q4_k_m | graph | 100.0% [210] |

### Paired comparison against `none` (per unit, repeats averaged; exact two-sided sign test)

| backend | comparison | metric | units | better | worse | tied | mean diff (pp) | p | p (Holm) |
|---|---|---|---|---|---|---|---|---|---|
| openai:gemma-4-26b-a4b-it-ud-q4_k_m | fulldoc vs none | core_ok | 70 | 1 | 0 | 69 | +1.4 | 1 | 1 |
| openai:gemma-4-26b-a4b-it-ud-q4_k_m | chunk vs none | core_ok | 70 | 1 | 0 | 69 | +0.5 | 1 | 1 |
| openai:gemma-4-26b-a4b-it-ud-q4_k_m | bm25 vs none | core_ok | 70 | 1 | 0 | 69 | +1.4 | 1 | 1 |
| openai:gemma-4-26b-a4b-it-ud-q4_k_m | dense vs none | core_ok | 70 | 1 | 0 | 69 | +1.0 | 1 | 1 |
| openai:gemma-4-26b-a4b-it-ud-q4_k_m | graph vs none | core_ok | 70 | 1 | 0 | 69 | +1.4 | 1 | 1 |
| openai:gemma-4-26b-a4b-it-ud-q4_k_m | fulldoc vs none | exact_match | 70 | 4 | 0 | 66 | +4.3 | 0.125 | 1 |
| openai:gemma-4-26b-a4b-it-ud-q4_k_m | chunk vs none | exact_match | 70 | 3 | 1 | 66 | +1.0 | 0.625 | 1 |
| openai:gemma-4-26b-a4b-it-ud-q4_k_m | bm25 vs none | exact_match | 70 | 4 | 0 | 66 | +3.8 | 0.125 | 1 |
| openai:gemma-4-26b-a4b-it-ud-q4_k_m | dense vs none | exact_match | 70 | 3 | 2 | 65 | +0.5 | 1 | 1 |
| openai:gemma-4-26b-a4b-it-ud-q4_k_m | graph vs none | exact_match | 70 | 4 | 1 | 65 | +2.9 | 0.375 | 1 |

`better`/`worse` count units. `p (Holm)` corrects for all comparisons in this table; only hypotheses written in HYPOTHESES.md before the test run are confirmatory.
