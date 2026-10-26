# Athena Sim summary

180 successful trials, 0 trial keys with only errors. Rates are per trial; repeats of the same unit are pooled (treat CIs and p-values as exploratory).

Split: dev.

## rename - pack `odoo`

### By condition and backend

| backend | condition | n | parsed | exact match [95% CI] | violated rule ok | all core rules ok [95% CI] | type prefix kept | collision | similarity idx before -> after | retrieval hit | latency s | tokens in/out | cost USD |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| openai:qwen3.5-9b-ud-q8_k_xl | none | 30 | 93.3% | 73.3% [56-86] | 93.3% | 93.3% [79-98] | - | 3.3% | 0.952 -> 0.990 | - | 7.24 | 13229/4484 | - |
| openai:qwen3.5-9b-ud-q8_k_xl | fulldoc | 30 | 100.0% | 83.3% [66-93] | 100.0% | 100.0% [89-100] | - | 3.3% | 0.952 -> 0.995 | - | 12.65 | 371519/4100 | - |
| openai:qwen3.5-9b-ud-q8_k_xl | chunk | 30 | 93.3% | 53.3% [36-70] | 93.3% | 93.3% [79-98] | - | 3.3% | 0.952 -> 0.988 | - | 10.01 | 23351/6143 | - |
| openai:qwen3.5-9b-ud-q8_k_xl | bm25 | 30 | 96.7% | 60.0% [42-75] | 96.7% | 96.7% [83-99] | - | 3.3% | 0.952 -> 0.992 | - | 7.41 | 25863/4483 | - |
| openai:qwen3.5-9b-ud-q8_k_xl | dense | 30 | 96.7% | 66.7% [49-81] | 96.7% | 96.7% [83-99] | - | 6.7% | 0.952 -> 0.989 | - | 8.33 | 21742/5134 | - |
| openai:qwen3.5-9b-ud-q8_k_xl | graph | 30 | 100.0% | 96.7% [83-99] | 100.0% | 100.0% [89-100] | - | 3.3% | 0.952 -> 1.000 | 100.0% | 5.86 | 14249/3540 | - |

### By language (all core rules ok; n in brackets)

| backend | condition | python |
|---|---|---|
| openai:qwen3.5-9b-ud-q8_k_xl | none | 93.3% [30] |
| openai:qwen3.5-9b-ud-q8_k_xl | fulldoc | 100.0% [30] |
| openai:qwen3.5-9b-ud-q8_k_xl | chunk | 93.3% [30] |
| openai:qwen3.5-9b-ud-q8_k_xl | bm25 | 96.7% [30] |
| openai:qwen3.5-9b-ud-q8_k_xl | dense | 96.7% [30] |
| openai:qwen3.5-9b-ud-q8_k_xl | graph | 100.0% [30] |

### Paired comparison against `none` (per unit, repeats averaged; exact two-sided sign test)

| backend | comparison | metric | units | better | worse | tied | mean diff (pp) | p | p (Holm) |
|---|---|---|---|---|---|---|---|---|---|
| openai:qwen3.5-9b-ud-q8_k_xl | fulldoc vs none | core_ok | 30 | 2 | 0 | 28 | +6.7 | 0.5 | 1 |
| openai:qwen3.5-9b-ud-q8_k_xl | chunk vs none | core_ok | 30 | 2 | 2 | 26 | +0.0 | 1 | 1 |
| openai:qwen3.5-9b-ud-q8_k_xl | bm25 vs none | core_ok | 30 | 2 | 1 | 27 | +3.3 | 1 | 1 |
| openai:qwen3.5-9b-ud-q8_k_xl | dense vs none | core_ok | 30 | 2 | 1 | 27 | +3.3 | 1 | 1 |
| openai:qwen3.5-9b-ud-q8_k_xl | graph vs none | core_ok | 30 | 2 | 0 | 28 | +6.7 | 0.5 | 1 |
| openai:qwen3.5-9b-ud-q8_k_xl | fulldoc vs none | exact_match | 30 | 5 | 2 | 23 | +10.0 | 0.453 | 1 |
| openai:qwen3.5-9b-ud-q8_k_xl | chunk vs none | exact_match | 30 | 4 | 10 | 16 | -20.0 | 0.18 | 1 |
| openai:qwen3.5-9b-ud-q8_k_xl | bm25 vs none | exact_match | 30 | 5 | 9 | 16 | -13.3 | 0.424 | 1 |
| openai:qwen3.5-9b-ud-q8_k_xl | dense vs none | exact_match | 30 | 4 | 6 | 20 | -6.7 | 0.754 | 1 |
| openai:qwen3.5-9b-ud-q8_k_xl | graph vs none | exact_match | 30 | 7 | 0 | 23 | +23.3 | 0.0156 | 0.156 |

`better`/`worse` count units. `p (Holm)` corrects for all comparisons in this table; only hypotheses written in HYPOTHESES.md before the test run are confirmatory.
