# Athena Sim summary

181 successful trials, 20 trial keys with only errors. Rates are per trial; repeats of the same unit are pooled (treat CIs and p-values as exploratory).

Split: test.

> Run `s2test_qwen35_9b_s2_godot-s2_infer` (test split) was started from freeze `frozen_godot-s2_qwen35_9b_s2_infer.json` (sha256 24037252bdd3).

## rename - pack `godot-s2`

### By condition and backend

| backend | condition | n | parsed | exact match [95% CI] | violated rule ok | all core rules ok [95% CI] | type prefix kept | collision | similarity idx before -> after | retrieval hit | latency s | tokens in/out | cost USD |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| openai:qwen3.5-9b-ud-q8_k_xl | graph[infer] | 181 | 100.0% | 70.7% [64-77] | 82.9% | 82.9% [77-88] | - | 1.7% | 0.990 -> 0.991 | 82.3% | 8.27 | 97867/31147 | - |

### By language (all core rules ok; n in brackets)

| backend | condition | cpp |
|---|---|---|
| openai:qwen3.5-9b-ud-q8_k_xl | graph[infer] | 82.9% [181] |

## No-oracle diagnostics

The identifier kind in these prompts was inferred from the code, not read from the benchmark. `kind matches` compares the inferred kind with the benchmark's kind (grading only); scope verdicts are those of `check_rename` for the model's suggestion (an unchanged name is not checked).

| condition | trials | kind matches | kind unknown | kind outside pack | scope-checked | scope ok | scope conflict | unchecked |
|---|---|---|---|---|---|---|---|---|
| graph[infer] | 181 | 82.3% | 0.0% | 0.0% | 180 | 98.3% | 1.7% | 0.0% |

## Trials that only have errors (20)

- `godot-s2|rename|cpp_055__p_name__GODOT-PARAM-INPUT-PREFIX|graph|openai:qwen3.5-9b-ud-q8_k_xl|2|infer`
- `godot-s2|rename|cpp_075__p_viewport__GODOT-PARAM-INPUT-PREFIX|graph|openai:qwen3.5-9b-ud-q8_k_xl|2|infer`
- `godot-s2|rename|cpp_099__p_tool__GODOT-PARAM-INPUT-PREFIX|graph|openai:qwen3.5-9b-ud-q8_k_xl|2|infer`
- `godot-s2|rename|cpp_086__p_version__GODOT-PARAM-INPUT-PREFIX|graph|openai:qwen3.5-9b-ud-q8_k_xl|2|infer`
- `godot-s2|rename|cpp_092__p_exclude__GODOT-PARAM-INPUT-PREFIX|graph|openai:qwen3.5-9b-ud-q8_k_xl|2|infer`
- `godot-s2|rename|cpp_073__p_result__GODOT-PARAM-INPUT-PREFIX|graph|openai:qwen3.5-9b-ud-q8_k_xl|2|infer`
- `godot-s2|rename|cpp_042__p_show_navigation__GODOT-PARAM-INPUT-PREFIX|graph|openai:qwen3.5-9b-ud-q8_k_xl|2|infer`
- `godot-s2|rename|cpp_053__p_next_pointer__GODOT-PARAM-INPUT-PREFIX|graph|openai:qwen3.5-9b-ud-q8_k_xl|2|infer`
- `godot-s2|rename|cpp_050__p_exclude__GODOT-PARAM-INPUT-PREFIX|graph|openai:qwen3.5-9b-ud-q8_k_xl|2|infer`
- `godot-s2|rename|cpp_095__p_control__GODOT-PARAM-INPUT-PREFIX|graph|openai:qwen3.5-9b-ud-q8_k_xl|2|infer`
- `godot-s2|rename|cpp_078__p_name__GODOT-PARAM-INPUT-PREFIX|graph|openai:qwen3.5-9b-ud-q8_k_xl|2|infer`
- `godot-s2|rename|cpp_072__p_event__GODOT-PARAM-INPUT-PREFIX|graph|openai:qwen3.5-9b-ud-q8_k_xl|2|infer`
- `godot-s2|rename|cpp_054__p_visible__GODOT-PARAM-INPUT-PREFIX|graph|openai:qwen3.5-9b-ud-q8_k_xl|2|infer`
- `godot-s2|rename|cpp_079__p_hash__GODOT-PARAM-INPUT-PREFIX|graph|openai:qwen3.5-9b-ud-q8_k_xl|2|infer`
- `godot-s2|rename|cpp_049__p_bone__GODOT-PARAM-INPUT-PREFIX|graph|openai:qwen3.5-9b-ud-q8_k_xl|2|infer`
- `godot-s2|rename|cpp_051__p_line__GODOT-PARAM-INPUT-PREFIX|graph|openai:qwen3.5-9b-ud-q8_k_xl|2|infer`
- `godot-s2|rename|cpp_062__p_viewport__GODOT-PARAM-INPUT-PREFIX|graph|openai:qwen3.5-9b-ud-q8_k_xl|2|infer`
- `godot-s2|rename|cpp_066__p_sink__GODOT-PARAM-INPUT-PREFIX|graph|openai:qwen3.5-9b-ud-q8_k_xl|2|infer`
- `godot-s2|rename|cpp_040__p_enabled__GODOT-PARAM-INPUT-PREFIX|graph|openai:qwen3.5-9b-ud-q8_k_xl|2|infer`
- `godot-s2|rename|cpp_084__p_other__GODOT-PARAM-INPUT-PREFIX|graph|openai:qwen3.5-9b-ud-q8_k_xl|2|infer`
