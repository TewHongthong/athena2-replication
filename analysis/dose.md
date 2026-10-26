# Dose-response: compliance against the size of the context

Exploratory: thresholds are those of HYPOTHESES_v2.md, no multiplicity correction, and nothing here enters the Holm family of H1.

Dose = mean number of characters of the prompt the model received (`prompt_chars`), on the units that every condition has. The conditions differ in how the context is chosen as well as in its size, so the curves describe the conditions and do not show a causal effect of size. Each cell has one point per condition; the permutation p-value is exact up to 8 conditions. The cells of one standard share their tasks across models, so they are not independent.

| pack | model | units | conditions | rho | p | best | largest context | largest is best |
|---|---|---|---|---|---|---|---|---|
| godot | openai:gemma-4-26b-a4b-it-ud-q4_k_m | 70 | 6 | +0.655 | 0.333 | graph (1.000) | fulldoc (1.000) | yes |
| godot | openai:google/gemini-3.1-flash-lite | 70 | 6 | +0.068 | 0.933 | graph (1.000) | fulldoc (1.000) | yes |
| godot | openai:openai/gpt-6-luna | 70 | 6 | +0.304 | 0.6 | graph (1.000) | fulldoc (1.000) | yes |
| godot | openai:qwen3.5-9b-ud-q8_k_xl | 70 | 6 | -0.087 | 0.861 | graph (0.995) | fulldoc (0.962) | no |
| dotnet-runtime | openai:gemma-4-26b-a4b-it-ud-q4_k_m | 70 | 6 | +0.577 | 0.25 | graph (1.000) | fulldoc (1.000) | yes |
| dotnet-runtime | openai:google/gemini-3.1-flash-lite | 70 | 6 | +0.207 | 0.8 | graph (1.000) | fulldoc (1.000) | yes |
| dotnet-runtime | openai:openai/gpt-6-luna | 70 | 6 | +0.131 | 1 | none (1.000) | fulldoc (1.000) | yes |
| dotnet-runtime | openai:qwen3.5-9b-ud-q8_k_xl | 70 | 6 | +0.086 | 0.919 | graph (0.986) | fulldoc (0.929) | no |
| odoo | openai:gemma-4-26b-a4b-it-ud-q4_k_m | 70 | 6 | - | - | none (1.000) | fulldoc (1.000) | yes |
| odoo | openai:google/gemini-3.1-flash-lite | 70 | 6 | - | - | none (1.000) | fulldoc (1.000) | yes |
| odoo | openai:openai/gpt-6-luna | 70 | 6 | -0.778 | 0.133 | none (1.000) | fulldoc (0.986) | no |
| odoo | openai:qwen3.5-9b-ud-q8_k_xl | 70 | 6 | +0.203 | 0.7 | graph (1.000) | fulldoc (1.000) | yes |

Spearman rho between context size and compliance: positive in 8 and negative in 2 of 10 cells, median +0.167. The largest context is the best condition in 9 of 12 cells.

## Curves

| pack | model | condition | prompt chars | added chars | compliance | effect (pp) |
|---|---|---|---|---|---|---|
| godot | openai:gemma-4-26b-a4b-it-ud-q4_k_m | none | 1469 | 0 | 0.986 | +0.0 |
| godot | openai:gemma-4-26b-a4b-it-ud-q4_k_m | graph | 2018 | 549 | 1.000 | +1.4 |
| godot | openai:gemma-4-26b-a4b-it-ud-q4_k_m | dense | 2042 | 573 | 1.000 | +1.4 |
| godot | openai:gemma-4-26b-a4b-it-ud-q4_k_m | chunk | 2086 | 617 | 1.000 | +1.4 |
| godot | openai:gemma-4-26b-a4b-it-ud-q4_k_m | bm25 | 2143 | 674 | 1.000 | +1.4 |
| godot | openai:gemma-4-26b-a4b-it-ud-q4_k_m | fulldoc | 8664 | 7195 | 1.000 | +1.4 |
| godot | openai:google/gemini-3.1-flash-lite | none | 1469 | 0 | 0.990 | +0.0 |
| godot | openai:google/gemini-3.1-flash-lite | graph | 2018 | 549 | 1.000 | +1.0 |
| godot | openai:google/gemini-3.1-flash-lite | dense | 2042 | 573 | 1.000 | +1.0 |
| godot | openai:google/gemini-3.1-flash-lite | chunk | 2086 | 617 | 1.000 | +1.0 |
| godot | openai:google/gemini-3.1-flash-lite | bm25 | 2143 | 674 | 0.986 | -0.5 |
| godot | openai:google/gemini-3.1-flash-lite | fulldoc | 8664 | 7195 | 1.000 | +1.0 |
| godot | openai:openai/gpt-6-luna | none | 1469 | 0 | 0.995 | +0.0 |
| godot | openai:openai/gpt-6-luna | graph | 2018 | 549 | 1.000 | +0.5 |
| godot | openai:openai/gpt-6-luna | dense | 2042 | 573 | 1.000 | +0.5 |
| godot | openai:openai/gpt-6-luna | chunk | 2086 | 617 | 0.990 | -0.5 |
| godot | openai:openai/gpt-6-luna | bm25 | 2143 | 674 | 1.000 | +0.5 |
| godot | openai:openai/gpt-6-luna | fulldoc | 8664 | 7195 | 1.000 | +0.5 |
| godot | openai:qwen3.5-9b-ud-q8_k_xl | none | 1469 | 0 | 0.929 | +0.0 |
| godot | openai:qwen3.5-9b-ud-q8_k_xl | graph | 2018 | 549 | 0.995 | +6.7 |
| godot | openai:qwen3.5-9b-ud-q8_k_xl | dense | 2042 | 573 | 0.967 | +3.8 |
| godot | openai:qwen3.5-9b-ud-q8_k_xl | chunk | 2086 | 617 | 0.952 | +2.4 |
| godot | openai:qwen3.5-9b-ud-q8_k_xl | bm25 | 2143 | 674 | 0.929 | +0.0 |
| godot | openai:qwen3.5-9b-ud-q8_k_xl | fulldoc | 8664 | 7195 | 0.962 | +3.3 |
| dotnet-runtime | openai:gemma-4-26b-a4b-it-ud-q4_k_m | none | 1703 | 0 | 0.986 | +0.0 |
| dotnet-runtime | openai:gemma-4-26b-a4b-it-ud-q4_k_m | graph | 1750 | 47 | 1.000 | +1.4 |
| dotnet-runtime | openai:gemma-4-26b-a4b-it-ud-q4_k_m | dense | 2469 | 766 | 0.995 | +1.0 |
| dotnet-runtime | openai:gemma-4-26b-a4b-it-ud-q4_k_m | chunk | 2705 | 1002 | 0.990 | +0.5 |
| dotnet-runtime | openai:gemma-4-26b-a4b-it-ud-q4_k_m | bm25 | 3141 | 1438 | 1.000 | +1.4 |
| dotnet-runtime | openai:gemma-4-26b-a4b-it-ud-q4_k_m | fulldoc | 9721 | 8018 | 1.000 | +1.4 |
| dotnet-runtime | openai:google/gemini-3.1-flash-lite | none | 1703 | 0 | 0.986 | +0.0 |
| dotnet-runtime | openai:google/gemini-3.1-flash-lite | graph | 1750 | 47 | 1.000 | +1.4 |
| dotnet-runtime | openai:google/gemini-3.1-flash-lite | dense | 2469 | 766 | 0.986 | +0.0 |
| dotnet-runtime | openai:google/gemini-3.1-flash-lite | chunk | 2705 | 1002 | 0.986 | +0.0 |
| dotnet-runtime | openai:google/gemini-3.1-flash-lite | bm25 | 3141 | 1438 | 0.986 | +0.0 |
| dotnet-runtime | openai:google/gemini-3.1-flash-lite | fulldoc | 9721 | 8018 | 1.000 | +1.4 |
| dotnet-runtime | openai:openai/gpt-6-luna | none | 1703 | 0 | 1.000 | +0.0 |
| dotnet-runtime | openai:openai/gpt-6-luna | graph | 1750 | 47 | 1.000 | +0.0 |
| dotnet-runtime | openai:openai/gpt-6-luna | dense | 2469 | 766 | 0.995 | -0.5 |
| dotnet-runtime | openai:openai/gpt-6-luna | chunk | 2705 | 1002 | 1.000 | +0.0 |
| dotnet-runtime | openai:openai/gpt-6-luna | bm25 | 3141 | 1438 | 1.000 | +0.0 |
| dotnet-runtime | openai:openai/gpt-6-luna | fulldoc | 9721 | 8018 | 1.000 | +0.0 |
| dotnet-runtime | openai:qwen3.5-9b-ud-q8_k_xl | none | 1703 | 0 | 0.914 | +0.0 |
| dotnet-runtime | openai:qwen3.5-9b-ud-q8_k_xl | graph | 1750 | 47 | 0.986 | +7.1 |
| dotnet-runtime | openai:qwen3.5-9b-ud-q8_k_xl | dense | 2469 | 766 | 0.848 | -6.7 |
| dotnet-runtime | openai:qwen3.5-9b-ud-q8_k_xl | chunk | 2705 | 1002 | 0.948 | +3.3 |
| dotnet-runtime | openai:qwen3.5-9b-ud-q8_k_xl | bm25 | 3141 | 1438 | 0.938 | +2.4 |
| dotnet-runtime | openai:qwen3.5-9b-ud-q8_k_xl | fulldoc | 9721 | 8018 | 0.929 | +1.4 |
| odoo | openai:gemma-4-26b-a4b-it-ud-q4_k_m | none | 1730 | 0 | 1.000 | +0.0 |
| odoo | openai:gemma-4-26b-a4b-it-ud-q4_k_m | graph | 1884 | 154 | 1.000 | +0.0 |
| odoo | openai:gemma-4-26b-a4b-it-ud-q4_k_m | dense | 2600 | 870 | 1.000 | +0.0 |
| odoo | openai:gemma-4-26b-a4b-it-ud-q4_k_m | chunk | 3334 | 1604 | 1.000 | +0.0 |
| odoo | openai:gemma-4-26b-a4b-it-ud-q4_k_m | bm25 | 3612 | 1882 | 1.000 | +0.0 |
| odoo | openai:gemma-4-26b-a4b-it-ud-q4_k_m | fulldoc | 49713 | 47983 | 1.000 | +0.0 |
| odoo | openai:google/gemini-3.1-flash-lite | none | 1730 | 0 | 1.000 | +0.0 |
| odoo | openai:google/gemini-3.1-flash-lite | graph | 1884 | 154 | 1.000 | +0.0 |
| odoo | openai:google/gemini-3.1-flash-lite | dense | 2600 | 870 | 1.000 | +0.0 |
| odoo | openai:google/gemini-3.1-flash-lite | chunk | 3334 | 1604 | 1.000 | +0.0 |
| odoo | openai:google/gemini-3.1-flash-lite | bm25 | 3612 | 1882 | 1.000 | +0.0 |
| odoo | openai:google/gemini-3.1-flash-lite | fulldoc | 49713 | 47983 | 1.000 | +0.0 |
| odoo | openai:openai/gpt-6-luna | none | 1730 | 0 | 1.000 | +0.0 |
| odoo | openai:openai/gpt-6-luna | graph | 1884 | 154 | 1.000 | +0.0 |
| odoo | openai:openai/gpt-6-luna | dense | 2600 | 870 | 1.000 | +0.0 |
| odoo | openai:openai/gpt-6-luna | chunk | 3334 | 1604 | 1.000 | +0.0 |
| odoo | openai:openai/gpt-6-luna | bm25 | 3612 | 1882 | 0.981 | -1.9 |
| odoo | openai:openai/gpt-6-luna | fulldoc | 49713 | 47983 | 0.986 | -1.4 |
| odoo | openai:qwen3.5-9b-ud-q8_k_xl | none | 1730 | 0 | 0.971 | +0.0 |
| odoo | openai:qwen3.5-9b-ud-q8_k_xl | graph | 1884 | 154 | 1.000 | +2.9 |
| odoo | openai:qwen3.5-9b-ud-q8_k_xl | dense | 2600 | 870 | 0.962 | -1.0 |
| odoo | openai:qwen3.5-9b-ud-q8_k_xl | chunk | 3334 | 1604 | 0.943 | -2.9 |
| odoo | openai:qwen3.5-9b-ud-q8_k_xl | bm25 | 3612 | 1882 | 0.976 | +0.5 |
| odoo | openai:qwen3.5-9b-ud-q8_k_xl | fulldoc | 49713 | 47983 | 1.000 | +2.9 |

## Within `graph`: added context against gain

| pack | model | units | median added chars | rho | p | method |
|---|---|---|---|---|---|---|
| godot | openai:gemma-4-26b-a4b-it-ud-q4_k_m | 70 | 473 | -0.130 | 0.725 | monte-carlo |
| godot | openai:google/gemini-3.1-flash-lite | 70 | 473 | -0.130 | 0.725 | monte-carlo |
| godot | openai:openai/gpt-6-luna | 70 | 473 | -0.130 | 0.737 | monte-carlo |
| godot | openai:qwen3.5-9b-ud-q8_k_xl | 70 | 473 | -0.079 | 0.516 | monte-carlo |
| dotnet-runtime | openai:gemma-4-26b-a4b-it-ud-q4_k_m | 70 | 47 | - | - | constant |
| dotnet-runtime | openai:google/gemini-3.1-flash-lite | 70 | 47 | - | - | constant |
| dotnet-runtime | openai:openai/gpt-6-luna | 70 | 47 | - | - | constant |
| dotnet-runtime | openai:qwen3.5-9b-ud-q8_k_xl | 70 | 47 | - | - | constant |
| odoo | openai:gemma-4-26b-a4b-it-ud-q4_k_m | 70 | 154 | - | - | constant |
| odoo | openai:google/gemini-3.1-flash-lite | 70 | 154 | - | - | constant |
| odoo | openai:openai/gpt-6-luna | 70 | 154 | - | - | constant |
| odoo | openai:qwen3.5-9b-ud-q8_k_xl | 70 | 154 | - | - | constant |

Gain = unit mean of selection minus unit mean of `none`. A unit that `none` already gets right cannot gain, so most gains are zero and the correlation is weak by construction.
