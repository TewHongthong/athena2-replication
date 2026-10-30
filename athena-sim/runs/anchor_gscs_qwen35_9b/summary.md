# Athena Sim summary

732 successful trials, 0 trial keys with only errors. Rates are per trial; repeats of the same unit are pooled (treat CIs and p-values as exploratory).

Split: test.

> Run `anchor_gscs_qwen35_9b` (test split) was started from freeze `frozen_anchor_gscs_qwen35_9b.json` (sha256 11b25cfbca2f).

## rename - pack `gscs`

### By condition and backend

| backend | condition | n | parsed | exact match [95% CI] | violated rule ok | all core rules ok [95% CI] | type prefix kept | collision | similarity idx before -> after | retrieval hit | latency s | tokens in/out | cost USD |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| openai:qwen3.5-9b-ud-q8_k_xl | none | 366 | 94.5% | 13.1% [10-17] | 18.9% | 18.9% [15-23] | 15.6% | 2.7% | 0.990 -> 0.987 | - | 9.72 | 184119/74487 | - |
| openai:qwen3.5-9b-ud-q8_k_xl | graph | 366 | 98.6% | 68.6% [64-73] | 95.9% | 95.9% [93-98] | 96.6% | 0.0% | 0.990 -> 0.996 | 100.0% | 7.99 | 231660/59834 | - |

### By language (all core rules ok; n in brackets)

| backend | condition | cpp | java | python |
|---|---|---|---|---|
| openai:qwen3.5-9b-ud-q8_k_xl | none | 19.0% [126] | 21.1% [123] | 16.2% [117] |
| openai:qwen3.5-9b-ud-q8_k_xl | graph | 95.2% [126] | 96.7% [123] | 95.7% [117] |

### Paired comparison against `none` (per unit, repeats averaged; exact two-sided sign test)

| backend | comparison | metric | units | better | worse | tied | mean diff (pp) | p | p (Holm) |
|---|---|---|---|---|---|---|---|---|---|
| openai:qwen3.5-9b-ud-q8_k_xl | graph vs none | core_ok | 122 | 114 | 0 | 8 | +77.0 | 9.63e-35 | 1.93e-34 |
| openai:qwen3.5-9b-ud-q8_k_xl | graph vs none | exact_match | 122 | 97 | 3 | 22 | +55.5 | 2.63e-25 | 2.63e-25 |

`better`/`worse` count units. `p (Holm)` corrects for all comparisons in this table; only hypotheses written in HYPOTHESES.md before the test run are confirmatory.
