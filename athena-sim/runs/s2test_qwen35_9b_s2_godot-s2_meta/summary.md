# Athena Sim summary

63 successful trials, 20 trial keys with only errors. Rates are per trial; repeats of the same unit are pooled (treat CIs and p-values as exploratory).

Split: test.

> Run `s2test_qwen35_9b_s2_godot-s2_meta` (test split) was started from freeze `frozen_godot-s2_qwen35_9b_s2_meta.json` (sha256 eada5a683057).

## rename - pack `godot-s2`

### By condition and backend

| backend | condition | n | parsed | exact match [95% CI] | violated rule ok | all core rules ok [95% CI] | type prefix kept | collision | similarity idx before -> after | retrieval hit | latency s | tokens in/out | cost USD |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| openai:qwen3.5-9b-ud-q8_k_xl | none | 9 | 100.0% | 33.3% [12-65] | 33.3% | 33.3% [12-65] | - | 11.1% | 0.990 -> 0.990 | - | 7.69 | 3895/1438 | - |
| openai:qwen3.5-9b-ud-q8_k_xl | fulldoc | 9 | 100.0% | 44.4% [19-73] | 44.4% | 44.4% [19-73] | - | 0.0% | 0.990 -> 0.990 | - | 10.41 | 19249/1813 | - |
| openai:qwen3.5-9b-ud-q8_k_xl | chunk | 9 | 100.0% | 44.4% [19-73] | 44.4% | 44.4% [19-73] | - | 0.0% | 0.990 -> 0.993 | - | 7.88 | 5521/1457 | - |
| openai:qwen3.5-9b-ud-q8_k_xl | bm25 | 9 | 100.0% | 55.6% [27-81] | 55.6% | 55.6% [27-81] | - | 0.0% | 0.990 -> 0.993 | - | 9.67 | 5782/1859 | - |
| openai:qwen3.5-9b-ud-q8_k_xl | dense | 9 | 100.0% | 44.4% [19-73] | 44.4% | 44.4% [19-73] | - | 0.0% | 0.990 -> 0.993 | - | 15.16 | 4903/2934 | - |
| openai:qwen3.5-9b-ud-q8_k_xl | graph | 9 | 100.0% | 100.0% [70-100] | 100.0% | 100.0% [70-100] | - | 0.0% | 0.990 -> 1.000 | 100.0% | 8.03 | 5308/1492 | - |
| openai:qwen3.5-9b-ud-q8_k_xl | naming | 9 | 100.0% | 44.4% [19-73] | 66.7% | 66.7% [35-88] | - | 0.0% | 0.990 -> 0.989 | - | 31.30 | 5209/2128 | - |

### By language (all core rules ok; n in brackets)

| backend | condition | cpp |
|---|---|---|
| openai:qwen3.5-9b-ud-q8_k_xl | none | 33.3% [9] |
| openai:qwen3.5-9b-ud-q8_k_xl | fulldoc | 44.4% [9] |
| openai:qwen3.5-9b-ud-q8_k_xl | chunk | 44.4% [9] |
| openai:qwen3.5-9b-ud-q8_k_xl | bm25 | 55.6% [9] |
| openai:qwen3.5-9b-ud-q8_k_xl | dense | 44.4% [9] |
| openai:qwen3.5-9b-ud-q8_k_xl | graph | 100.0% [9] |
| openai:qwen3.5-9b-ud-q8_k_xl | naming | 66.7% [9] |

### Paired comparison against `none` (per unit, repeats averaged; exact two-sided sign test)

| backend | comparison | metric | units | better | worse | tied | mean diff (pp) | p | p (Holm) |
|---|---|---|---|---|---|---|---|---|---|
| openai:qwen3.5-9b-ud-q8_k_xl | fulldoc vs none | core_ok | 9 | 1 | 0 | 8 | +11.1 | 1 | 1 |
| openai:qwen3.5-9b-ud-q8_k_xl | chunk vs none | core_ok | 9 | 1 | 0 | 8 | +11.1 | 1 | 1 |
| openai:qwen3.5-9b-ud-q8_k_xl | bm25 vs none | core_ok | 9 | 2 | 0 | 7 | +22.2 | 0.5 | 1 |
| openai:qwen3.5-9b-ud-q8_k_xl | dense vs none | core_ok | 9 | 2 | 1 | 6 | +11.1 | 1 | 1 |
| openai:qwen3.5-9b-ud-q8_k_xl | graph vs none | core_ok | 9 | 6 | 0 | 3 | +66.7 | 0.0312 | 0.375 |
| openai:qwen3.5-9b-ud-q8_k_xl | naming vs none | core_ok | 9 | 3 | 0 | 6 | +33.3 | 0.25 | 1 |
| openai:qwen3.5-9b-ud-q8_k_xl | fulldoc vs none | exact_match | 9 | 1 | 0 | 8 | +11.1 | 1 | 1 |
| openai:qwen3.5-9b-ud-q8_k_xl | chunk vs none | exact_match | 9 | 1 | 0 | 8 | +11.1 | 1 | 1 |
| openai:qwen3.5-9b-ud-q8_k_xl | bm25 vs none | exact_match | 9 | 2 | 0 | 7 | +22.2 | 0.5 | 1 |
| openai:qwen3.5-9b-ud-q8_k_xl | dense vs none | exact_match | 9 | 2 | 1 | 6 | +11.1 | 1 | 1 |
| openai:qwen3.5-9b-ud-q8_k_xl | graph vs none | exact_match | 9 | 6 | 0 | 3 | +66.7 | 0.0312 | 0.375 |
| openai:qwen3.5-9b-ud-q8_k_xl | naming vs none | exact_match | 9 | 2 | 1 | 6 | +11.1 | 1 | 1 |

`better`/`worse` count units. `p (Holm)` corrects for all comparisons in this table; only hypotheses written in HYPOTHESES.md before the test run are confirmatory.

## Trials that only have errors (20)

- `godot-s2|rename|cpp_080__p_sink__GODOT-PARAM-INPUT-PREFIX|none|openai:qwen3.5-9b-ud-q8_k_xl|0`
- `godot-s2|rename|cpp_080__p_sink__GODOT-PARAM-INPUT-PREFIX|fulldoc|openai:qwen3.5-9b-ud-q8_k_xl|0`
- `godot-s2|rename|cpp_080__p_sink__GODOT-PARAM-INPUT-PREFIX|naming|openai:qwen3.5-9b-ud-q8_k_xl|0`
- `godot-s2|rename|cpp_080__p_sink__GODOT-PARAM-INPUT-PREFIX|chunk|openai:qwen3.5-9b-ud-q8_k_xl|0`
- `godot-s2|rename|cpp_080__p_sink__GODOT-PARAM-INPUT-PREFIX|bm25|openai:qwen3.5-9b-ud-q8_k_xl|0`
- `godot-s2|rename|cpp_080__p_sink__GODOT-PARAM-INPUT-PREFIX|dense|openai:qwen3.5-9b-ud-q8_k_xl|0`
- `godot-s2|rename|cpp_080__p_sink__GODOT-PARAM-INPUT-PREFIX|graph|openai:qwen3.5-9b-ud-q8_k_xl|0`
- `godot-s2|rename|cpp_037__p_stream_id__GODOT-PARAM-INPUT-PREFIX|none|openai:qwen3.5-9b-ud-q8_k_xl|0`
- `godot-s2|rename|cpp_037__p_stream_id__GODOT-PARAM-INPUT-PREFIX|fulldoc|openai:qwen3.5-9b-ud-q8_k_xl|0`
- `godot-s2|rename|cpp_037__p_stream_id__GODOT-PARAM-INPUT-PREFIX|naming|openai:qwen3.5-9b-ud-q8_k_xl|0`
- `godot-s2|rename|cpp_037__p_stream_id__GODOT-PARAM-INPUT-PREFIX|chunk|openai:qwen3.5-9b-ud-q8_k_xl|0`
- `godot-s2|rename|cpp_037__p_stream_id__GODOT-PARAM-INPUT-PREFIX|bm25|openai:qwen3.5-9b-ud-q8_k_xl|0`
- `godot-s2|rename|cpp_037__p_stream_id__GODOT-PARAM-INPUT-PREFIX|dense|openai:qwen3.5-9b-ud-q8_k_xl|0`
- `godot-s2|rename|cpp_037__p_stream_id__GODOT-PARAM-INPUT-PREFIX|graph|openai:qwen3.5-9b-ud-q8_k_xl|0`
- `godot-s2|rename|cpp_076__p_session__GODOT-PARAM-INPUT-PREFIX|none|openai:qwen3.5-9b-ud-q8_k_xl|0`
- `godot-s2|rename|cpp_076__p_session__GODOT-PARAM-INPUT-PREFIX|fulldoc|openai:qwen3.5-9b-ud-q8_k_xl|0`
- `godot-s2|rename|cpp_076__p_session__GODOT-PARAM-INPUT-PREFIX|naming|openai:qwen3.5-9b-ud-q8_k_xl|0`
- `godot-s2|rename|cpp_076__p_session__GODOT-PARAM-INPUT-PREFIX|chunk|openai:qwen3.5-9b-ud-q8_k_xl|0`
- `godot-s2|rename|cpp_076__p_session__GODOT-PARAM-INPUT-PREFIX|bm25|openai:qwen3.5-9b-ud-q8_k_xl|0`
- `godot-s2|rename|cpp_076__p_session__GODOT-PARAM-INPUT-PREFIX|dense|openai:qwen3.5-9b-ud-q8_k_xl|0`
