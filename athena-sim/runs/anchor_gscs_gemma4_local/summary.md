# Athena Sim summary

732 successful trials, 0 trial keys with only errors. Rates are per trial; repeats of the same unit are pooled (treat CIs and p-values as exploratory).

Split: test.

> Run `anchor_gscs_gemma4_local` (test split) was started from freeze `frozen_anchor_gscs_gemma4_local.json` (sha256 e1551a5baff2).

## rename - pack `gscs`

### By condition and backend

| backend | condition | n | parsed | exact match [95% CI] | violated rule ok | all core rules ok [95% CI] | type prefix kept | collision | similarity idx before -> after | retrieval hit | latency s | tokens in/out | cost USD |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| openai:gemma-4-26b-a4b-it-ud-q4_k_m | none | 366 | 99.5% | 33.6% [29-39] | 35.5% | 35.5% [31-41] | 38.0% | 3.3% | 0.990 -> 0.994 | - | 3.39 | 194526/55377 | - |
| openai:gemma-4-26b-a4b-it-ud-q4_k_m | graph | 366 | 100.0% | 90.7% [87-93] | 100.0% | 100.0% [99-100] | 100.0% | 0.0% | 0.990 -> 0.999 | 100.0% | 3.10 | 242685/48544 | - |

### By language (all core rules ok; n in brackets)

| backend | condition | cpp | java | python |
|---|---|---|---|---|
| openai:gemma-4-26b-a4b-it-ud-q4_k_m | none | 35.7% [126] | 32.5% [123] | 38.5% [117] |
| openai:gemma-4-26b-a4b-it-ud-q4_k_m | graph | 100.0% [126] | 100.0% [123] | 100.0% [117] |

### Paired comparison against `none` (per unit, repeats averaged; exact two-sided sign test)

| backend | comparison | metric | units | better | worse | tied | mean diff (pp) | p | p (Holm) |
|---|---|---|---|---|---|---|---|---|---|
| openai:gemma-4-26b-a4b-it-ud-q4_k_m | graph vs none | core_ok | 122 | 85 | 0 | 37 | +64.5 | 5.17e-26 | 1.03e-25 |
| openai:gemma-4-26b-a4b-it-ud-q4_k_m | graph vs none | exact_match | 122 | 77 | 0 | 45 | +57.1 | 1.32e-23 | 1.32e-23 |

`better`/`worse` count units. `p (Holm)` corrects for all comparisons in this table; only hypotheses written in HYPOTHESES.md before the test run are confirmatory.
