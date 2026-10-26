# LLM-drafted ontologies

`draft_ontology.py` (one folder up) produces the LLM ontology of each independent standard. One model drafts each ontology in a single pass; the prompt is fixed before any request is sent; the draft is used as produced.

## Inputs

- `draft_prompt.md`: the prompt template. It holds the task, the ontology format (four node types: Standard, Language, IdentifierKind, NamingRule; two relations: APPLIES_TO, DEFINED_IN), the identifier-kind list of the Vol. 1 schema, the scope (naming rules only, only what the standard states), the Standard and Language values, and the text of the pinned standard document.
- The pinned standard document, read from `standards/src/<id>/` and checked against the SHA-256 in `standards/standards.json`.
- Model pin `luna_draft` in `models/model_pins.json`: the request of the `luna` pin with `max_tokens` raised to 32,768, because the answer holds hidden reasoning and a complete ontology in one request and a cut answer is not repeated.

The human ontology is not read by the script and is not part of the prompt.

## Procedure

1. `freeze` records the SHA-256 of the template, of the three documents, of the three rendered prompts and of the pin entry in `draft_freeze.json`. `run` refuses to start if any of them differs from the freeze.
2. `run --standard <id>` sends one request. Transport errors (HTTP 429 and 5xx, network) are retried by the client; an answer that has been received is never requested again. The run refuses to start if `packs/<id>/llm/response.txt` already exists.
3. The only permitted transformation of the answer is the removal of one Markdown code fence around the whole answer. Text around the JSON is not repaired.
4. Acceptance is decided by the loader checks: the JSON parses into a node-link object, the harness reader (`athena/ontology.py`) and the curation reader (`rules.Ontology`) load it, the language of the standard is present, the answer was not cut by the output limit (`finish_reason` is not `length`), and, where networkx is installed, `graph_loader` agrees with the curation reader (networkx before 3.4 is used through the `edges=` to `link=` adapter of the check, and the check records that). A draft that fails is reported as rejected and is not edited.
5. Departures from the prompt (a node type or relation outside the four and two, a casing or severity outside the lists, a rule without an identifier kind, an id without the standard prefix) are listed in `check.json` as schema findings. They are reported and do not decide acceptance.

## Outputs, in `packs/<id>/llm/`

| file | content |
|---|---|
| `prompt.txt` | the prompt as sent |
| `response.txt` | the raw answer |
| `meta.json` | pin and its hash, model, provider, response identifier, system fingerprint, finish reason, token counts, latency, cost estimate, hashes of prompt and response |
| `llm_ontology.json` | the answer after the removal of the code fence |
| `check.json` | loader checks, acceptance, schema findings |

## Commands

From the `athena-sim` folder (the request goes to OpenRouter; `OPENAI_API_KEY` holds the OpenRouter key):

    python3 draft_ontology.py prompt --standard godot
    python3 draft_ontology.py freeze
    python3 draft_ontology.py run --standard godot
    python3 draft_ontology.py run --standard dotnet-runtime
    python3 draft_ontology.py run --standard odoo
    python3 draft_ontology.py check --standard godot

Tests: `python3 -m unittest tests.test_draft_ontology` (a fake backend answers; no network).
