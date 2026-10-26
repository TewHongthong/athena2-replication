# Athena Sim

A headless simulator that stands in for the lost Athena VS Code extension so that experiments can be run and **their results recorded systematically**.
Python 3.9+, standard library only (no `pip install` needed).

## What the original Athena did and what Sim does instead

| Athena (extension) | Athena Sim |
|---|---|
| The user selects code in VS Code | Samples a "unit" from the benchmark (a name made non-compliant / a function whose header comment was removed) |
| Retrieves the relevant part of the coding standard (RAG) | `retrieval.py` implements 6 conditions: `none`, `fulldoc`, `chunk` (plain RAG, TF-IDF), `bm25` (plain RAG, BM25), `dense` (plain RAG, embeddings), `graph` (ontology-guided) |
| Sends a prompt to GPT (o3-mini) with an API key | `llm.py` calls an OpenAI-compatible API / Gemini with a key from an environment variable |
| Shows the result for the user to accept/reject | `evaluate.py` checks automatically with a rule checker (no human judgement needed) |
| — | `runner.py` / `report.py` store every trial in `trials.jsonl` and summarize as tables + CIs + paired tests |

## Getting started

```bash
python athena_sim.py packs                                        # list the available data
python athena_sim.py show --pack gscs --condition graph           # show the prompt the LLM will see

# 1) Dry run without calling an LLM (no key needed) - proves the pipeline scores correctly
python athena_sim.py run --pack gscs --backend mock:oracle  --per-language 0   # must give 100%
python athena_sim.py run --pack gscs --backend mock:echo    --per-language 0   # must give 0%
python athena_sim.py run --pack gscs --backend mock:autofix --per-language 0   # linter --fix style baseline

# 2) The real thing: o3-mini, as used in the Athena pilot (the default is the dev split = the tuning set)
export OPENAI_API_KEY=sk-...                       # Windows PowerShell:  $env:OPENAI_API_KEY="sk-..."
python athena_sim.py run --pack gscs --backend openai:o3-mini --per-language 0 --repeats 3 --workers 4
python athena_sim.py run --pack gscs --backend openai:o3-mini --task comment --per-language 0 --repeats 3

# 2b) Results for the paper: freeze, then run the test split once (see "Protocol dev -> freeze -> test")

# 3) The 5 public standards (needs the athena-corpus folder alongside, or --corpus / $ATHENA_CORPUS)
python athena_sim.py run --pack public5 --backend openai:o3-mini --per-language 20 --workers 4

python athena_sim.py report runs/<run-id> [runs/<run-id-2> ...]   # regenerate trials.csv + summary.md
```

Re-running with the same `--run-id` **resumes where it stopped** (finished trials are skipped), which is useful after a network drop or rate limit.
`--max-errors N` stops by itself after N consecutive failed API calls (to avoid wasting money).

**Using Cursor / Copilot / ChatGPT instead of an API:**
`python athena_sim.py prompts --pack gscs --export prompts.jsonl` → paste the `prompt` into that tool → put the answer in the `response` field
→ `python athena_sim.py run --pack gscs --backend replay:prompts.jsonl` scores it with the same checker.

**Using a lab LLM (llama-server):** `OPENAI_BASE_URL=http://localhost:8080/v1 python athena_sim.py run --backend openai:<model name> ...`
(add `--no-think` to switch off the thinking mode of a thinking model through `chat_template_kwargs`).

**Pinned models:** `python athena_sim.py run --model-pin <name> ...` takes the backend, endpoint, sampling settings and
extra request body (e.g. an OpenRouter provider lock) from `../models/model_pins.json` (see `../models/README.md`);
the entry's SHA-256 goes into the run config and into a freeze. The same options exist one by one:
`--omit-temperature` (send no temperature), `--extra-body '<JSON>'` (merged into the request) and `--no-think`.
When the endpoint reports them, every trial records `provider`, `response_id` and `system_fingerprint`.

## Retrieval conditions

| condition | what is in the prompt | question it answers |
|---|---|---|
| `none` | only the name of the standard | how much the LLM knows the standard on its own (lower bound) |
| `fulldoc` | the whole standard | does stuffing in the whole document help |
| `chunk` | the 3 paragraphs most similar to the code (TF-IDF cosine) | plain RAG = the Athena design at the start of the project |
| `bm25` | the same passages and query as `chunk`, ranked with Okapi BM25 (k1 = 1.2, b = 0.75, fixed in code) | does a stronger lexical ranker close the gap to ontology-guided selection |
| `dense` | the same passages as `chunk`, ranked by cosine similarity of embeddings from a pinned local model (`--embed-pin`); the query is the language, kind, name and code written as text, with the instruction of the pin | does a semantic ranker close the gap to ontology-guided selection |
| `graph` | the rules that `APPLIES_TO` (language, identifier kind), ordered by severity > specificity, + 2 examples per rule; a rule that another applicable rule `OVERRIDES` is dropped, and `CONFLICTS_WITH` pairs are flagged in the context | ontology-guided Graph RAG as in the paper |

The prompt skeleton is the same for every condition (TASK / CODING STANDARD / CODE / OUTPUT FORMAT); only the CODING STANDARD section differs.

`dense` is not in the default list of `--conditions` because it needs an embedding model: ask for it by name together with `--embed-pin NAME`
(an entry under `embeddings` in `../models/model_pins.json`; its SHA-256 is recorded in the run configuration and in a freeze). The embedding server
address is read from `$ATHENA_EMBED_BASE_URL`, and every vector is cached under `$ATHENA_EMBED_CACHE` (default `~/.cache/athena2/embeddings`) by the hash
of the pin, so a text is embedded once per pin. Unlike the lexical rankers, `dense` always returns `--chunk-k` passages, because a cosine score has no
zero to stop at. `python athena_sim.py embed-check --embed-pin NAME` checks the serving setup with a few obvious passages. See `../models/README.md`.

## Tasks and metrics

**`rename`** – the LLM fixes a non-compliant name: exact match with the original name, passes the rule checker of the violated rule, passes every core rule (`core_ok`),
collision with an existing name, Similarity Index before/after the rename, retrieval hit (was the right rule retrieved).

**`comment`** – the LLM writes a function header comment: only the *structure* is checked (all labels present, labels non-empty, starts with the correct delimiter) + similarity to the reference.
`Revised By` / `Revised Date` may be left empty (per the template in the document), so they are not counted in the "labels filled" metric.
**The content quality of comments is not scored** — that needs a rubric + human raters or an LLM-as-judge (not written yet).

Statistics: Wilson 95% CI per condition (per trial, repeats pooled) and paired comparison against a baseline (default `none`) **at unit level**:
average the `--repeats` per unit, then an exact two-sided sign test + mean difference (percentage points) + Holm-adjusted p.
Supplementary metric `type prefix kept` (only for GSCS rules that have a prefix): does the model keep the original data-type prefix (`i_`, `f_`, `bln_`)? Stricter than `core_ok`, which accepts any prefix in the list.

## Data packs

**`gscs`** – the standard in the attached docx (General Style and Coding Standards, 2015), used as the pilot's starting standard
- Separate ontology (`packs/gscs/gscs_ontology.json`); the project's main ontology is untouched
- Automatically checked rules: data-type prefix of variables/parameters, `bln_` for booleans, UPPER_SNAKE_CASE constants, procedure name = Verb_Object,
  return-type prefix of functions, type names ending in `_Type`, header comment with 8 labels
- The sample code consists of **seeds written by hand to follow the standard** (Java / Python / C++, 6 each, 18 in total), because real code on the internet did not follow this 2015 internal standard.
  To add code: edit `packs/gscs/seeds.py` and run `python packs/gscs/build_gscs_pack.py`
  (the builder verifies every violation with the same checker used for scoring: the original name must pass and the injected name must fail)
- Assumptions from interpreting the document (recorded in `gscs_standard.json` → `assumptions`):
  - The table in the document has no prefix for integer (`i`) and date-time (`dt`), but the document's examples use them, so both are accepted
  - The document uses lower case after the prefix in variables but upper case in functions/booleans; the system enforces only the prefix and `_`, not the case of the word after the prefix
  - Both `bl` and `bln` are accepted; a function that returns a value = kind `function`, one that does not = `procedure`
  - The document's own `calcSqrt` example does not match the document's rules; the text of the rule takes precedence
  - Structural rules (an else is required, a comment before if/loop, try-catch-finally) are recorded but **not evaluated**; they are reachable only through the `fulldoc` / `chunk` conditions
- Languages: the proceedings (`LLM_Powered_Code_Documentation_Tool.docx`) state that the Athena pilot supports **Python, Java, C++**, matching the seeds used

**`public5`** – the benchmark already in the project (`athena-corpus`): PEP 8, Google Java, .NET, Google TypeScript, Airbnb JavaScript
Judged by the `CORE` table in `curation/rules.py` (read with `ast.literal_eval`, not imported)
The first load of ~3,500 JSON files from the OneDrive folder takes ~1 minute; after that the `athena-sim/.cache/` cache is used (rebuilt automatically when the benchmark files change; safe to delete at any time)
- The `comment` task of `public5` uses `athena-corpus/benchmark/comment_units/` (120 units; built by `curation/make_comment_units.py`, see details/rejection reasons in `curation_report.md` § 7)
  Each unit has `expectedElements`/`signature` (params/returns/throws inferred from the code, not from the comment), so `grade_comment` does not penalize a void method without `@return`
  A new metric `n_checks` (in `trials.csv` as column `m_n_checks`, summarized as `vacuous (n_checks=0)` in `summary.md`) says how many mechanically checkable MUST rules the unit really has — some formats (Python `plain-line-comment`, most of Airbnb JS) have no mechanical check at all, which makes `comment_ok` true regardless of the answer

## Vol. 2 packs (`godot`, `dotnet-runtime`, `odoo`)

One pack per standard of the pool benchmark written by `tools/export_tasks.py`. The benchmark folder is not part of the
repository (the task files live where they were built); give it with `--corpus` or with `$ATHENA_V2_BENCH` (a folder
that holds one sub-folder per pack, each with the benchmark itself or with a `bench/` folder inside it):

```bash
export ATHENA_V2_BENCH=~/athena_pool_run
python athena_sim.py run --pack odoo --backend mock:oracle --conditions none,graph --out runs --run-id try
python athena_sim.py run --pack odoo --ontology-variant llm ...    # H4: rules from the LLM-drafted ontology
```

- Rules for the `graph` condition (selection) come from `packs/<std>/<std>_ontology.json`; `--ontology-variant llm` takes
  them from `packs/<std>/llm/llm_ontology.json` instead. **Grading never changes**: `core_ok` uses the core rules of the
  human ontology (`packs/<std>/core_rules.json`) in both variants. A kind with no rule in the draft (Odoo `parameter`)
  makes the prompt say that no specific rule exists; the task stays in the run.
- With the `llm` variant the rule ids differ from the benchmark's, so the retrieval hit is recorded as `None`
  (not comparable); only `core_ok` is compared. The variant is part of the pack fingerprint, so a freeze made with one
  variant refuses a run with the other.
- `fulldoc`, `chunk`, `bm25` and `dense` use the pinned standard document in `standards/src/<std>/`. It is split by
  `athena/passages.py` into passages: one paragraph (or list item, or fenced code block) each, with its heading path in
  front ("Title > Section"); an indented block after `::` or a directive stays with its paragraph; adornment and
  directive lines are dropped. No model is used, so the passages are identical on every machine.
- `--no-oracle` (`athena2.py`) still supports only `public5`.
- Tests: `python3 -B -m unittest tests.test_vol2_pack` (synthetic benchmark; needs no corpus and no key).

## Pipeline without the Vol. 1 oracles (`athena2`, v0.1)

In the Vol. 1 runs the identifier kind of every unit was read from the benchmark and a suggestion was graded only
against the rules and the original name. `athena2.py` and the flag `--no-oracle` replace both with the editor's view:

```bash
# one identifier of one snippet (needs a model; mock and replay backends are refused)
python athena2.py rename --language python --file snippet.py --name SumX --model-pin gemma4
# the experiment commands, always with --no-oracle (default pack public5)
python athena2.py run --backend mock:autofix --conditions none,graph --per-language 20
python athena2.py freeze ... ; python athena2.py run ... --split test --frozen frozen.json
```

- The kind is inferred from the snippet (`athena-corpus/curation/kind_infer.py`); the prompt and the retrieval use it.
  If no kind is inferred the prompt says "identifier" and the graph condition retrieves no specific rule.
- `rename` checks the suggestion against the rules of the inferred kind and with the scope-aware check
  (`curation/scope_check.py`, C++, C# and Python). Status: `accepted`, `rejected` (rule or scope conflict),
  `unchecked` (rules pass, no scope checker for the language), `no_change`, `no_proposal`. A rejected suggestion
  is reported, not retried.
- A `--no-oracle` run records, per trial, `kind_used`, `kind_inferred`, `kind_status`, `kind_ok` (inferred = benchmark
  kind; used for reporting only) and `scope` (verdict of the scope check for the suggestion); `summary.md` gets a
  "No-oracle diagnostics" table. Grading is unchanged and still uses the benchmark's kind and rules.
- A freeze made with `--no-oracle` also records the hashes of the curation files that decide the kind and the scope
  verdict, and a test run refuses to start if they differ. Without the flag nothing changes: the prompts of the
  Vol. 1 packs are byte-identical.
- Only the public5 pack is supported (the inference produces its kind vocabulary). The curation folder is
  `../athena-corpus/curation`, or `$ATHENA_CURATION`. `athena/pipeline.py` has the limits of v0.1.

## Confirmatory analysis across runs (`analyse_confirmatory.py`)

```
python analyse_confirmatory.py runs/<dev-run> runs/<test-run> ... --out analysis.md --json analysis.json
```

Computes what `HYPOTHESES_v2.md` Sections 2.3 and 4 register: the eligibility of each standard for H1 (mean `core_ok` of `none` on dev, over the models, below 0.90), H1 (selection vs `none` on test, per eligible standard and model, exact two-sided sign test, one Holm family made of exactly these tests), and H3 (selection vs `fulldoc` as a non-inferiority estimate with a cluster-bootstrap 95% CI and a 2 pp margin; selection vs the retrieval baselines with the paired sign test and a separate Holm family). Pass the runs of the selection variant that defines H1 only (human ontology, kind from metadata). Bootstrap clusters are the source files of the tasks (`--cluster-field`, default `file`, written to every trial as `<repo>:<path>` from the snippet provenance); a trial without that field is clustered by its snippet id, and the report says how many units were. `report.py` keeps its per-run tables, which are exploratory.

## Secondary and exploratory analyses (`analyse_secondary.py`)

```
python analyse_secondary.py h2 runs/<run> ... [--packs godot,dotnet-runtime,odoo]
python analyse_secondary.py h4 --human runs/<run> ... --llm runs/<run> ... [--agreement-root [DIR] | --kappa labels.csv]
python analyse_secondary.py h5 --metadata runs/<run> ... --inferred runs/<run> ...
python analyse_secondary.py h6 --labels renames.csv
python analyse_secondary.py dose runs/<run> ... [--packs godot,dotnet-runtime,odoo]
python analyse_secondary.py h7 --assistant runs/<run> ... --ref runs/<run> ... --assistant-label A --ref-label M --rules-cond C --norules-cond C --margin-pp X [--unknown-packs p1,p2]
```

Statistical skeleton for the hypotheses that are not confirmatory (`HYPOTHESES_v2.md`, hypothesis table). None of the results enters the Holm family of H1, and the numeric thresholds are provisional until the pilot on dev: the defaults are the nominal values of the table (H4: 5 pp and kappa 0.6; H5: 5 pp) and can be overridden; H7 has no default margin and the command refuses to run without `--margin-pp`.

- **H2**: Spearman correlation between the zero-shot compliance (`none`) and the effect of selection (selection - none) across (standard, model) cells on the test split, with a permutation p-value (exact up to 8 cells, Monte Carlo otherwise, fixed seed). Anchor packs can be added with `--packs`. The cells of one standard share their tasks across models, so they are not independent.
- **H4**: LLM-drafted ontology minus human ontology in `core_ok` (cluster-bootstrap 95% CI, equivalence margin) and the agreement of the two ontologies: with `--agreement-root` (default folder `packs`), Cohen's kappa by identifier kind (`athena/agreement.py`) over the packs of `--packs`, pooled kappa compared with the threshold and per-pack figures plus the secondary kappa reported; alternatively `--kappa`, a CSV with the columns `human` and `llm`, one row per attribute.
- **H5**: kind inferred from the code minus kind from metadata (non-inferiority: lower limit of the CI above the negative margin).
- **H6**: catch rate and false alarms of the scope-aware check against the scope-blind check, from a CSV with the columns `breaks`, `aware`, `blind` (0/1) per labelled case; `breaks` is 1 for a conflict case and 0 for a rename to a fresh name, and the labels come from the hand-written cases, which the trials do not contain.
- **Assistant comparison** (`h7`; outside the scope of the study, kept for future work): assistant with a rules file against full document, assistant without one against `none` (equivalence within the margin), and selection against both on the packs whose standard the model does not know (superiority).
- **Dose-response** (`dose`): the dose is the size of the prompt the model received (`prompt_chars` of the trial), which puts every condition on one scale. For each (standard, model) cell it lists the compliance of every condition against its mean prompt size, on the units that all conditions have, with the Spearman correlation across the conditions (exact permutation p-value) and whether the largest context is the best one. Within selection (`--selection`, against `--none`) it also correlates the context that selection adds with the gain of each unit. The conditions differ in how the context is chosen as well as in its size, so this describes the conditions and is not a causal estimate of size; it needs no extra runs.

For H4, H5 and `h7` give the runs of each variant as a separate group: the task ids must be the same in both groups (the same benchmark) and the condition names are taken from the options. Pairs are made per unit (mean over the repeats); clusters are the source files of the tasks, as in the confirmatory analysis. `tests/test_secondary.py` covers the statistics with synthetic trials only; none of this has been run on real trials.

## Comparison with the Athena pilot in the proceedings

| Athena pilot (proceedings, Fig 1-4) | Athena Sim |
|---|---|
| Upload the standard as a PDF → the PDF Parser extracts the text → sent to the LLM | Closest is the `fulldoc` condition (`gscs` uses the real text of the docx) |
| No upload → use the "default documentation" built into the system (contents unknown) | `none` is not the same thing (none = no standard at all); to compare against the "default" you must specify what the default is |
| Feature "Change Variable Names": rename every occurrence of a symbol (e.g. `time → currentTime`) and let the user Apply/Reject | Task `rename` (renames every occurrence, checked automatically instead of by user judgement) |
| Feature "Generate Comment" + Detail Level: inline comments per line/block | Task `comment` measures only the function header (see limitations) |
| 20 users, measuring time + acceptance rate + Likert | No humans: automatically checked compliance/exact match, so results cannot be compared directly with the proceedings' acceptance numbers |
| LLM provider selectable (dropdown, includes OpenAI), key entered in settings | `--backend openai:o3-mini` / `gemini:...`, key from an environment variable |

## Recorded outputs

`runs/<run-id>/`
- `config.json` – every parameter, backend, split, freeze information, hashes of the ontology and data (reproducible)
- `trials.jsonl` – every trial: prompt, raw answer, parsed values, metrics, tokens, latency, cost (use `--no-store-prompt` to omit the prompt)
- `trials.csv` – flat table (UTF-8 BOM, opens in Excel)
- `summary.md` – summary tables by condition/language + paired comparisons

## Protocol dev -> freeze -> test

Every unit is split into **dev** (used to tune Athena) and **test** (used to report results) by snippet, fixed in advance (see `HYPOTHESES.md`).
`run` uses dev by default; test for real models (including answers pasted from Cursor/Copilot via `replay:`) must be run from a freeze file:

1. **dev**: try tuning `--examples`, `--top-k`, `--chunk-k`, the wording in `prompts.py`, etc. on `--split dev`, giving every condition (none/fulldoc/chunk/graph) the same tuning budget
2. **freeze**: `python athena_sim.py freeze <same options as the run> --out-file frozen_x.json --note "..."`
   records hashes of the code/prompt/ontology/data/options/`HYPOTHESES.md`
3. **test**: `python athena_sim.py run <same options> --split test --frozen frozen_x.json`; if anything differs from what was frozen the run does not start;
   re-running test requires `--allow-rerun` and the report is labelled RERUN; the full history is in `frozen_x.json.ledger.jsonl`
4. Report all test results per `HYPOTHESES.md` (H1 is the only confirmatory test), including those where Athena does not win

The mock backend can be used on test without a freeze because it involves no tuning.

## Suggested experiment plan

1. `mock:oracle` / `mock:echo` / `mock:autofix` to check the pipeline and obtain non-LLM baselines (done in the dry run: oracle 100%, echo 0%)
2. `openai:o3-mini` on `gscs`: dev tuning -> freeze -> test with 4 conditions, `--repeats 3` (test: 122 rename units, 12 comment units; small, used as a pilot/case study)
3. `public5` with the same protocol, to see how much Athena helps when the standard is already well known
4. Add models (`gpt-4o`, `gemini:gemini-2.5-flash`, lab models) as replications, then combine with `report runs/a runs/b`

Cost estimation: use `--price-in` / `--price-out` (USD per 1M tokens) to get a cost column; always try `--limit 5` first.

## Limitations to be aware of (should be written in the paper)

- No real LLM has been called yet: the OpenAI/Gemini paths were tested only against a fake server
- `chunk` uses TF-IDF (lexical), not embeddings; the proceedings do not describe chunking/embedding at all (they only say the PDF Parser extracts text from the standard's PDF and passes it to the LLM), so how the original RAG worked is unknown
- The original comment feature generated *inline comments* according to the Detail Level the user chose (Fig 3), but Sim measures only the *function header comment* per the GSCS standard; there is no Detail Level and no inline-comment / comment-before-if-loop task yet
- The `fulldoc` of `public5` is the rules flattened from the ontology, not an official document; the `fulldoc` of `gscs` is the real text of the docx
- The `comment` metrics are structural only; semantic preservation and judge-based evaluation are not measured
- The benchmark uses *synthetic injection* of violations into short code, not violations that programmers actually made
- `mock:*` results are not LLM results; the report always carries a warning label

## Tests

```bash
python -m unittest discover -s tests -v      # no key/network needed; the public5 tests need $ATHENA_CORPUS
```

## Layout

```
athena_sim.py        CLI (run / report / prompts / show / embed-check / packs)
athena2.py           CLI of the pipeline without the oracles (rename, and the experiment commands with --no-oracle)
athena/              ontology, packs, retrieval, embed, prompts, llm, evaluate, runner, report, freeze, pins, pipeline
packs/gscs/          the standard from the docx: source text, standard JSON, seeds, pack builder, generated ontology + benchmark
vendor/              output_validator.py (a copy from the project, not modified)
tests/               smoke tests
HYPOTHESES.md        hypotheses and analysis plan written before the runs (counted in the freeze hash)
runs/                experiment results (created when running)
```
