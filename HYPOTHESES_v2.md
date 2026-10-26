# Hypotheses and Analysis Plan, Vol. 2

Status: pre-registration of the Vol. 2 study, written before any test-split trial. The numeric thresholds are nominal values fixed in advance; the pilot on the development split was used to check that the procedure runs, not to tune them.
This file is included in the hash of the freeze (`hypotheses_v2_sha256`). After the freeze it is not edited; any change is made in a separate ADDENDUM.
Goal, same as Vol. 1: if selection wins, the result must be defensible; if it does not win, that is reported just as completely.
Vol. 1 frozen files are not touched.

## 0. What Vol. 2 tests

Does the Vol. 1 result (ontology-guided rule selection) still hold when the oracles are removed one at a time: hand-built ontology, kind from metadata, author-prepared standards/seeds, synthetic violations, checking snippets only?
Everything is evaluated automatically; there are no human subjects (the user study is Vol. 3).

| RQ | Question |
|---|---|
| RQ1 Generalization | On independent organizational standards, does selection give higher core-rule compliance than none, fulldoc, and lexical/dense retrieval, and does the effect size vary with how well the model already follows that standard? |
| RQ2 Encoding cost | How long does converting a standard into an ontology take, how closely does an LLM-drafted ontology match the human one at the attribute level, and how close is the compliance it yields to that of the human ontology? |
| RQ3 Without oracles | When kind comes from inference and the rules come from an LLM-drafted ontology, how much does the result drop, and how well does a scope-aware check catch renames that change behaviour? |
| RQ4 Real changes | On real rename commits in mature repos, how often does a proposed name pass the rules, match the developer's name? (Should level; build and test are not run, D19) |

## 1. Data and split  (D12 + D13 fix the size, proportions, split key, task selection method and number of trials of B1; D14 fixes the size of B2 (deferred by D16))

Independent standards (D3): Godot C++ guidelines (C++), dotnet/runtime coding style (C#), Odoo coding guidelines (Python)
Reserve: Mozilla, WebKit, AOSP

| pack | language | rename tasks (S) | dev 30% (tuning) | test 70% (reported once) |
|---|---|---|---|---|
| godot | C++ | 100 | 30 | 70 |
| dotnet-runtime | C# | 100 | 30 | 70 |
| odoo | Python | 100 | 30 | 70 |

- D12: S = 100 rename tasks per pack (300 in total), 1 injected violation per task; dev 30% / test 70% (same proportions as Public5 in Vol. 1)

- Code comes from real repos; only files/commits after the single cutoff_date shared by all models = 2026-06-01 are used (D9, WP2); units meeting the size criterion of 6–40 lines with no parse error (before the identifier-consistency gate) at the pinned commit: godot 771, dotnet-runtime 2,895, odoo 1,680 — the number of units after the identifier-consistency gate and the injection check is given below (godot 356, dotnet-runtime 2,228, odoo 848); the policy of D13 below applies if either side has fewer than 30 / 70 units
- The split (D12) is determined by a hash of the file path: tasks from the same file fall on the same side (this covers violations of the same snippet), fixed before running any model
  - Hash function (no salt): SHA-256 of the UTF-8 path (as in the `path` column of `*_units.tsv`) taken as an integer mod 100; value < 30 = dev, the rest = test
  - Results measured from `pins/*_units.tsv` (before the identifier-consistency gate): godot dev 30 files / 324 units, test 45 files / 447 units; dotnet-runtime dev 138 / 814, test 342 / 2,081; odoo dev 157 / 620, test 301 / 1,060 — the godot dev side is the smallest (it needs 30 tasks from 30 files)
- Task selection method (D13): within each pack and each side (dev / test), sample without replacement from the units that pass the criteria, using the fixed seed `athena2-b1-v1`, with at most 3 tasks per file, until 30 (dev) and 70 (test) are reached; no stratification by module
  - 1 unit (a function/method meeting the criteria) = 1 task
  - Sampling details (implemented in `athena-corpus/curation/tools/select_tasks.py`): sort the pool by (path, order of the unit in the file), shuffle with Python `random.Random("athena2-b1-v1:<pack>:<side>")`, take units in shuffled order, skipping units whose file has already been taken 3 times, until the count is reached
  - If the pool is too small (decided in advance, before the post-gate results are seen): if the greedy pass with the cap of 3 per file leaves any pack/side short because the pool is exhausted, relax the cap to 4 and then 5 in turn, for that pack/side only, restarting the sampling from the beginning with the same seed at the new cap; if it is still short at a cap of 5, use what is available while keeping the dev:test ratio at 30:70: S′ is the largest integer ≤ 100 for which both sides can reach their targets at some cap in {3, 4, 5}, with dev = ⌊0.3·S′⌋ and test = S′ − dev (the realised ratio differs from 30:70 by less than one task); at S′ each side uses the smallest cap in {3, 4, 5} that reaches its own target, drawing from the same shuffled order; files are not moved across splits and units are not borrowed across sides; report the cap actually used and the actual number of tasks per pack as a threat
  - Reason for the cap of 3 per file: godot is clustered (75 files with qualifying units, 57% of the units are in `modules/`); in a simulation on the godot test side (200 seeds), unrestricted sampling gave on average ~28 files per 70 tasks, while the cap of 3 gave ~32 files (the share of the largest top-level directory group is on average ~56% and ~46% respectively); capacity at a cap of 3 before the gate: godot dev 70 / test 115 against the 30 / 70 needed
  - Caveat: the numbers above come from a simulation and are not the result of the actual selection; the real pool will be smaller after the gate and after checking that injection is possible (godot has the least slack); the selection does not weight modules equally, so it still leans toward modules with many units
- Violation injection for B1 (D18): one injected violation per task. The rules are the core naming rules of the human ontology of the pack's standard that apply to the kind of the target (the CORE table is generated from the ontology, not written by hand). Gate as in Vol. 1: a unit enters the pool only if every identifier that the ontology checks passes the core rules. The target is drawn at random from the eligible identifiers of the unit with the fixed seed of the task draw (not diversity-first as in Vol. 1). Candidate names are tried in the Vol. 1 order of `violation_injector` (casing swap, forbidden pattern, abbreviation, prefix strip, suffix strip); the first candidate is accepted that is a valid identifier, is not already in the unit, fails the rule under the checker, keeps the parse-tree shape after renaming every occurrence and re-parsing, and gives no conflict in the scope-aware check. Deterministic, no LLM; done after the dev/test split and before the freeze; the number of tasks by kind and by injection method is reported. Status: implemented in `athena-corpus/curation/tools/build_pool.py` (gate, target draw, injection, scope-aware check) and `tools/export_tasks.py` (snippet and violation files), without changes to `curate.py`; run on the three real corpora, and the output of each pack passed `validate_benchmark.py --core` with 0 errors.
- Kinds without an injection target (D20): the extractors and `curate.py` are not changed to add targets. A core slot of the human ontology with no injection target is reported as untested. Godot: struct, union, type_alias, macro and namespace (the C++ extractor gives no kind to the last three and merges struct and union into class). dotnet-runtime: local_function (declarations with the exempt label are skipped), so the injected core is method only. Odoo: module and package (the Python extractor gives no such kinds). The kinds covered by each pack are reported next to the task counts.
- Odoo parameter rule moved into the core (D22): `ODOO-PARAMETER-CASE` was first left out of the core because the gate was thought unable to separate the exception for `self` and `cls`. The extractor already marks the first parameter named `self`, `cls`, `mcs` or `metacls` of a method as exempt, so the rule was moved into the core. This was decided after the pool had been counted: with the original core (constant, module, package) the Odoo pool held 5 units and gave 3 tasks, none on the development side; with the rule moved it holds 848 units. The `core_rules.json` of Odoo changed from sha256 `82279a45…` to `8f32b8ff…`; the ontology file is unchanged. Because the decision follows the pool count, it is reported as a threat.
- Pool and tasks after the gate and the injection: godot 356 units in 64 files give 100 tasks (dev 30 / test 70; parameter 34, method 39, variable 24, function 3); dotnet-runtime 2,228 units in 375 files give 100 tasks (method 100); odoo 848 units in 260 files give 100 tasks (parameter 100). The cap is 3 per file in all packs. All 300 violations were made by a change of casing, the first method in the order of D18.
- Number of trials: 8 conditions (none, fulldoc, TF-IDF, BM25, dense, selection with the human ontology, selection with the LLM-drafted ontology, selection + kind inference) × 3 test rounds + 1 dev round = 5,760 trials per model (test 5,040 + dev 720); this is also used for the budget calculation — details are in the B1 budget document
- B2, real rename commits (D14, deferred by D16; Should level, mined in WP4): B2 is not part of the planned runs; it is run only if resources remain after B1, and then it is registered in an addendum before any model is run on it. Sizing if run: at most 50 commits per pack, in two packs only: C++ (Godot) and Python (Odoo); C# is excluded because RefactoringMiner does not support it; the same 8 conditions and 3 rounds as the B1 test side, with no dev/test split, so at most 2 packs × 50 commits × 8 conditions × 3 rounds = 2,400 trials per model; the cap is a ceiling, not a guaranteed count: the number of commits that actually qualify is known only after mining, and the actual number per pack is reported as a threat; if it falls far below the cap, whether B2 still supports a statistical comparison is decided before any model is run; the commit selection criteria are registered in the addendum, with the mined pool, before any model is run on B2; the cost estimate uses the per-trial token counts of B1 (single snippets), and real commit contexts may be longer — details are in the B1 budget document
- B3, build and test after a repository-wide rename (D19): not part of this study; it is future work. No design, budget or repository set exists for it, and the three packs (C++, C#, Python) are heavy to build (Godot, .NET runtime, Odoo). WP5 is dropped from the plan. The behaviour check stays at snippet level (scope-aware check, Section III-F), so H6 is measured on the hand-written cases and on renames to fresh names, not on build or test results.
- Anchors from Vol. 1 (GSCS / Public5): use both; rerun the new models and the models whose deployment differs from Vol. 1 (D15: Gemma 4 26B, Vol. 1 local Ollama Q4_K_M → local llama.cpp UD-Q4_K_M with pin `gemma4_local`; Qwen3.5-9B, Vol. 1 Q4_K_M → UD-Q8_K_XL), each with its Vol. 2 model pin (`models/model_pins.json`); not counted in H1, used as the extreme points for H2; the reuse is disclosed and Vol. 1 results are not reported again
- Odoo (LGPL-3.0): the artifact keeps only the commit hash + path + fetch script; the code itself is not distributed

## 2. Hypotheses

Models (D6, revised by D16): GPT-6 Luna and Gemini 3.1 Flash-Lite (hosted), Gemma 4 26B (A4B) and Qwen3.5-9B (open weights, served locally, one model at a time on one GPU). DeepSeek V4.1-Flash and Mistral Large 4 are not part of the panel. Three further open-weight models served from a borrowed GPU endpoint (Qwen3.5 35B-A3B at Q6, Qwen3.8 Flash-Next at Q4 and Qwen3.8 27B, as named by the endpoint) were run on the development units only, in the pilot. Their development results are reported as supplementary results outside the panel. They are not run on the test split, are not frozen, and enter neither the eligibility rule of Section 2.3 nor any hypothesis.
Coding assistants that read project-level rules files are outside the scope of this study and are left to future work.
Comparison conditions include at least `none`, `fulldoc`, `selection`, and lexical/dense retrieval (TF-IDF, BM25, dense)
Primary metric `core_ok` = the proposed name passes every core rule for the language/identifier kind (unparseable = fail); the unit of analysis is program/repo level

| # | Hypothesis | Status | RQ |
|---|---|---|---|
| H1 | For every independent standard with zero-shot compliance < 90% (Section 2.3): selection (human ontology, kind from metadata) > none at program/repo level; if no standard qualifies, H1 is reported as not testable | **confirmatory (the only one); conditional on Section 2.3** | RQ1 |
| H2 | (selection − none) is negatively correlated with zero-shot compliance across standard × model | secondary | RQ1 |
| H3 | selection is no more than 2 pp below fulldoc (non-inferiority margin, Section 4) with a shorter prompt, and higher than TF-IDF, BM25, dense | secondary | RQ1 |
| H4 | The LLM-drafted ontology yields compliance within 5 pp of the human one; human–LLM attribute-level agreement κ ≥ 0.6 | exploratory | RQ2 |
| H5 | kind inference lowers compliance by ≤ 5 pp relative to kind from metadata | exploratory | RQ3 |
| H6 | The scope-aware check flags every conflict in the hand-written test cases and raises fewer false alarms than the scope-blind check, measured on renames to fresh names (no conflict by construction) (D19) | exploratory | RQ3 |

Results are written up as they are, in both directions: if H1 does not hold on a standard, report that selection gives no benefit on that standard and discuss it in terms of the knowledge gap.

### 2.1 Model pins and drift check

- Every model is run through its entry in `models/model_pins.json` (`--model-pin`). The SHA-256 of the entry is part of the freeze, and a test run does not start if the entry has changed since the freeze. A pin fixes the request (model slug, endpoint, serving provider with fallbacks disabled, sampling and reasoning settings), not the model itself: none of the hosted vendor identifiers is a dated snapshot. The locally served models are pinned by file hash, llama.cpp build and server command.
- Canary: before its first test trial and after its last one, each model is run on the same canary set with the same pin: 30 dev units of each pack (90 units), condition `none`, 1 repeat, seed 42. The canary trials are not part of any hypothesis test and are not counted in the number of trials in Section 1.
- A model is flagged as drifted if either of the following holds:
  1. the `model`, `provider` or `system_fingerprint` recorded per trial differs between the first and the last trial of that model, canary trials included (for the locally served models, Gemma 4 26B and Qwen3.5-9B, which are served from pinned files, a change of the llama.cpp build or of the server command counts instead);
  2. a two-sided exact McNemar test on the paired `core_ok` outcomes of the two canary runs (same 90 units) gives p < 0.05. No multiplicity correction is applied, because the check is a safeguard and not a hypothesis test. The share of units whose proposed name is identical in both runs is reported but is not a criterion: models that are called without a temperature do not reproduce their answers exactly even when nothing has changed.
- Action: a flag changes nothing in the data. All trials of every model are kept and reported, and no model is excluded from the primary analysis or rerun. A flagged model is marked in every table, and H1, H2 and H3 are recomputed without it as a sensitivity analysis reported next to the primary result. For every model, flagged or not, the change in `core_ok` between the two canary runs and any change of `model`, `provider` or `system_fingerprint` are reported.
- Limitation: with 90 paired units the test detects only large shifts, so the absence of a flag is not evidence that a model did not change; this is listed among the limitations in Section 5.

### 2.2 Dense retrieval baseline

- The `dense` condition uses the same passages, the same number of passages per prompt (3) and the same prompt wording as `chunk` and `bm25`; only the ranking differs. The ranker is cosine similarity of embeddings from Qwen3-Embedding-0.6B (Q8_0 GGUF), served locally and pinned in `models/model_pins.json` (`embeddings` section) with the revision, the SHA-256 of the file and the llama.cpp build; the SHA-256 of the entry is part of the freeze.
- The query is the language, the kind, the name and the code written as text, preceded by one fixed instruction sentence; passages are embedded without an instruction. The instruction, the number of passages and the embedding model are fixed before any run on dev and are not tuned; the tuning budget on dev is the same as for the other retrieval conditions (Section 3).
- Unlike the lexical rankers, `dense` always returns the requested number of passages. Vectors are cached by the hash of the pin, so each text is embedded once.
- Passages for `chunk`, `bm25` and `dense`: a standard is split by a fixed rule that uses no model. A passage is one paragraph, one list item or one fenced code block of the pinned document, preceded by the headings that contain it (for example "Title > Section"). A block indented after a line ending in `::` or after a directive stays with its paragraph; adornment, directive and label lines are dropped, and a heading with no text under it is not a passage. The rule gives 35 passages for Godot, 28 for the .NET runtime and 215 for Odoo (longest 672, 1,498 and 1,719 characters). It is fixed before any run on dev and is not tuned; the passages are the same in every condition that uses them.

### 2.3 Eligibility of a standard for H1

- A standard is included in H1 if its zero-shot compliance is below 90%. Zero-shot compliance of a standard is the mean `core_ok` of condition `none` on the dev units of its pack, averaged over the four panel models (one dev round per model, so at most 4 × 30 trials per pack; the trials are not independent because every model sees the same units).
- The test side is not used for this decision, so that the choice of standards does not depend on the outcome of the comparisons. The threshold is applied to the point estimate; no interval is used.
- A standard excluded by the rule is still run and reported with the others; it only does not enter H1. The dev value of every standard and the resulting list of included standards are reported.
- The rule is imprecise near the threshold: with 30 dev units per model, a standard whose true zero-shot compliance is close to 90% can be included or excluded by chance (Section 5).
- If no standard has zero-shot compliance below 90%, H1 has no eligible standard and is reported as not testable; the threshold and the metric are not changed. On the dev units the mean zero-shot `core_ok` is 95.0% (Godot), 97.5% (dotnet-runtime) and 98.3% (Odoo), so no standard is eligible.
- In that case no confirmatory test is performed. The comparisons of selection with `none` are reported as secondary comparisons, without the Holm family of H1, and H2–H6 are unchanged.

### 2.4 Decision criteria

All intervals are 95% cluster-bootstrap intervals over source files (Section 4). A cell is one (standard, model) pair on the test split; at most 3 standards × 4 panel models = 12 cells. The verdict of H3, H4 and H5 is given per cell and then summarised: supported if every cell is supported, not supported if any cell is clearly against the hypothesis, inconclusive otherwise.

| H | Quantity | Supported when | Clearly against when |
|---|---|---|---|
| H1 | selection (human ontology, kind from metadata) − none, per eligible standard and model | exact two-sided sign test, Holm-adjusted p < 0.05 and a positive mean difference (Section 4); not testable if no standard is eligible (Section 2.3) | — |
| H2 | Spearman ρ between zero-shot compliance (none, test units) and the effect (selection − none, pp) over the cells | ρ < 0 and two-sided permutation p < 0.05 (Monte Carlo, 10,000 permutations, seed 20261020, because 12 cells exceed the exact limit of 8) | ρ ≥ 0, or p ≥ 0.05 |
| H3 | selection − fulldoc in core_ok; mean prompt length of selection against fulldoc; selection − each of TF-IDF, BM25, dense | lower CI limit > −2 pp, prompt shorter than fulldoc, and a positive mean difference with Holm-adjusted exact sign test p < 0.05 against each retrieval baseline | upper CI limit < −2 pp (inferior to fulldoc) |
| H4 | core_ok with the LLM-drafted ontology − with the human ontology; pooled attribute-level κ | CI inside ±5 pp in the cell, and pooled κ ≥ 0.6 | CI wholly beyond ±5 pp, or pooled κ < 0.6 |
| H5 | core_ok with kind inferred from the code − with kind from metadata | lower CI limit > −5 pp | upper CI limit < −5 pp |
| H6 | scope-aware against scope-blind check on the labelled cases (hand-written conflict cases and renames to fresh names) | the scope-aware check flags every conflict case, flags fewer fresh-name renames than the scope-blind check, and the exact two-sided sign test on the discordant fresh-name renames gives p < 0.05 | the scope-aware check misses a conflict case |

For H6 the catch rate is reported with its one-sided 95% Clopper–Pearson lower limit. H2 is computed on cells that share their tasks across models, so its p-value is optimistic and is reported as such. A result in the "clearly against" column is reported in the same way as a supported one (the paragraph after the hypothesis table in Section 2).

## 3. Rules that apply in every case (adapted from the Vol. 1 practices)

- Report every condition and every metric; do not drop units or languages, and do not change the checker after seeing test results
- Unparseable results count as failures; trials with API errors are rerun until complete
- The tuning budget on dev is the same for every condition (including lexical/dense retrieval)
- Must not be adjusted after seeing results: seeds, split, ontology rules, the CORE table, the rule checker, metric definitions, this list of hypotheses
- Bugs after freezing: fix, re-freeze, rerun, report both runs (the ledger keeps the history)
- Results on dev are not the main results of the paper
- Analyses added after seeing the data are exploratory and are written as an ADDENDUM before scoring

### 3.1 Independence of the human ontologies (WP1)

- The author (Tew) builds the godot, dotnet-runtime and odoo ontologies himself, **before seeing the LLM's draft**; an assistant only records his answers on a fixed form and does not propose content
- The LLM drafts a separate set; the human ontology is not used as its input
- No LLM is used to draft, propose, or edit the content of the human ontologies of these 3 standards (rules, kinds, attribute values, core/excluded split). An assistant only writes the answers into the ontology file and runs the checks.
- Human–LLM agreement is measured at the attribute level (Cohen's κ); the author adjudicates; the advisor (co-author) reviews/advises only and does not create ontologies
- The author is an annotator, not a research participant
- The LLM ontology of each standard is drafted by one model in a single pass. The drafting model is GPT-6 Luna, which is also a panel model (circularity is a threat to validity). The draft is used as produced; a draft that the loader rejects is reported, not edited by hand. The prompt, which contains the schema and the text of the standard, is fixed before any trial is run. The same LLM ontology is used for every panel model. Request: the `luna_draft` pin (the `luna` request with an output limit of 32,768 tokens). Scope: naming rules only (Standard, Language, IdentifierKind and NamingRule nodes; APPLIES_TO and DEFINED_IN links); the identifier-kind list of Vol. 1 is given and new kinds may be added only where the standard needs them. The only change allowed to the answer is the removal of one Markdown code fence; text around the JSON is not repaired. Acceptance is decided by the loader checks, and departures from the prompt are reported as findings. One request per standard; a received answer is never requested again. The template, the three prompts and the pin entry are hashed in a freeze file before the first request.
- The encoding time of the human ontology is the author's own estimate for each block of the form (self-reported), not a measurement; the timestamps of the recording session are kept and cover only the recording of the answers. Cohen's κ is computed by identifier kind. A unit is a kind with the same id in both ontologies for the same language. For each unit and each attribute (casing, prefix, suffix, severity, presence of a length bound, presence of a forbidden pattern), the label of an ontology is the set of values fixed by the naming rules that apply to the kind, empty if there is none; the two names of upper snake case (UPPER_SNAKE_CASE and SCREAMING_SNAKE_CASE) are one value. κ is computed over all unit–attribute pairs, for each standard and pooled over the standards that have at least one common kind; the pooled value is the κ of H4. The observed agreement, the agreement per attribute and a 95% percentile bootstrap interval over units are reported, and κ over the pairs in which at least one ontology fixes a value is reported as a secondary figure. Kinds present in one ontology only are listed and counted separately (not in κ); a standard with no common kind has no κ. The units are kinds, not source sections, because the section labels of the drafts cannot be compared; this was decided after the drafts existed and before κ was computed. The differences on the shared kinds are adjudicated by the author and reported; adjudication changes neither ontology and neither κ.
- The schema is that of Vol. 1 (six node types and five edge types). Identifier kinds are added only where a standard needs them.

## 4. Analysis plan

- Unit of analysis = program/repo; paired comparison against `none` on the same unit, exact two-sided sign test, α = 0.05; H1 is the only hypothesis designated confirmatory; when no standard is eligible (Section 2.3), all comparisons are secondary or exploratory
- Multiplicity: H1 has its own Holm family, made of the comparisons selection (human ontology, kind from metadata) vs `none` for every standard included by Section 2.3 and every panel model (at most 3 standards × 4 models = 12 tests). All other comparisons in the report tables (other conditions, other metrics, anchors) are exploratory; Holm is applied separately within each of those tables, and their p-values never enter the H1 family; the variants with the LLM-drafted ontology and with kind inference are not part of H1 (they are addressed by H4 and H5)
- H3, non-inferiority: for each model and pack, the paired per-unit difference in `core_ok` (selection − fulldoc, mean over rounds) is estimated with a cluster bootstrap 95% CI whose clusters are the source files of the tasks (repository and path). Selection is reported as non-inferior if the lower limit of the CI is above −2 pp; as inferior if the upper limit is below −2 pp; otherwise as inconclusive. No multiplicity correction is applied to this reporting. The part of H3 that compares selection with TF-IDF, BM25 and dense uses the paired exact sign test, with Holm over those comparisons
- Tasks taken from the same file are not independent: confidence intervals use a cluster bootstrap that resamples whole source files (repository and path, recorded in every trial); a trial without a file is clustered by its snippet, and the report states how many were
- Report effect size (pp) + CI per condition
- Secondary metrics: exact_match (added after inspection of the dev results (pilot-informed); a secondary metric, not a confirmatory one), type/kind prefix kept, collision, tokens and cost, scope-aware check (behaviour change / false alarm)
- H4: attribute-level κ (Section 3.1) + the compliance difference between the two ontologies. The condition is selection with the kind taken from metadata, run twice on the same tasks: once with the human ontology and once with the LLM-drafted ontology as the source of the rules shown to the model. Compliance is always scored with the core rules of the human ontology of the pack, so the benchmark and the checker do not depend on the drafted ontology. For each model and pack, the paired per-unit difference in `core_ok` (LLM − human, mean over rounds) is estimated with the cluster bootstrap 95% CI used for H3. The two ontologies are reported as within the margin if the CI lies inside ±5 pp, outside it if the CI lies wholly beyond ±5 pp, and inconclusive otherwise. Where the drafted ontology has no rule for the kind of a task (the Odoo draft has none for `parameter`), the prompt says that the ontology holds no specific rule, the task stays in the comparison, and the number of such tasks is reported next to the result.
- RQ4 (if done): name match against real commits and rule compliance (build/test pass rate is not measured, D19)

## 5. Limitations

- The human ontologies are built by a single author (self-adjudicated) — this is not inter-annotator agreement between two people
- Leakage: the original identifier names of mature repos may be in training data even when files after the cutoff are used
- Violations are still synthetic injections (except WP4)
- Few rules of some standards can be checked mechanically (only mechanically checkable core rules are counted)
- The zero-shot rule of H1 (Section 2.3) is decided on 30 dev units per model, so a standard near 90% can be misclassified in either direction
- With 70 test units per pack, the 2 pp margin of H3 can be confirmed only for models whose paired per-unit differences vary little; for the others H3 is reported as inconclusive rather than as a pass
- Hosted models have no dated snapshots; the drift check (Section 2.1) uses 90 paired units and detects only large shifts
- The panel has four models, two hosted and two open-weight models served locally; larger open-weight models and other hosted families are not covered
- Zero-shot `core_ok` is close to its ceiling on the dev units of all three standards, which leaves little room for any condition to improve it
- The standards are public, so training-data leakage is an alternative explanation of the high zero-shot compliance
- `exact_match` as a secondary metric was chosen after the dev results were seen
- The supplementary models were served from a borrowed endpoint; their names are those given by the endpoint, and the weights, revisions and quantisation are not verified or pinned. They were run on the development units only, so their results are descriptive. The pilot results of both the panel and the supplementary models were seen before the panel was confirmed
- Results on models outside the panel need replication

## 6. Procedure

Notation: PACK is godot, dotnet-runtime or odoo; PIN is luna, gemini31fl, qwen35_9b or gemma4_local; FAMILY is meta, llm or infer. Commands are run from `athena-sim`. The options that change the numbers are identical in `freeze` and `run`; a difference stops the run.

1. Close the code and the documents. No file under `athena/` and no pin, pack, ontology or this file is changed after step 2.
2. Freeze, once for each (PACK, PIN, FAMILY), 36 files in all:
   `python athena_sim.py freeze --pack PACK --model-pin PIN --split test --per-language 0 --repeats 3 --seed 42 <family options> --out-file frozen_PACK_PIN_FAMILY.json`
   Family options: meta = `--conditions none,fulldoc,chunk,bm25,dense,graph --embed-pin qwen3_embedding_06b`; llm = `--conditions graph --ontology-variant llm`; infer = `--conditions graph --no-oracle`.
3. Canary before the first test trial of a model (Section 2.1), for each PACK:
   `python athena_sim.py run --pack PACK --model-pin PIN --split dev --conditions none --per-language 0 --repeats 1 --seed 42 --run-id canary_before_PIN_PACK`
4. Test, once for each (PACK, PIN, FAMILY): the `run` command with the same options as the freeze, plus `--frozen frozen_PACK_PIN_FAMILY.json --run-id test_PACK_PIN_FAMILY`. A run that stops is resumed with the same `--run-id`. A second run of the test split needs `--allow-rerun` and is reported as a RERUN.
5. Canary after the last test trial of a model: step 3 with `--run-id canary_after_PIN_PACK`; apply the drift criteria of Section 2.1.
6. Analysis, on all test run folders (the report tables label the variants `graph[llm]` and `graph[infer]`):
   `python athena_sim.py report runs/test_*`
   `python analyse_confirmatory.py runs/test_* --models luna,gemini31fl,qwen35_9b,gemma4_local`
   `python analyse_secondary.py h2 runs/test_*`
   `python analyse_secondary.py h4 --human <meta runs> --llm <llm runs> --agreement-root`
   `python analyse_secondary.py h5 --metadata <meta runs> --inferred <infer runs>`
   `python analyse_secondary.py h6 --labels renames.csv`
7. Evidence kept: the frozen files and their ledgers, `runs/`, the model and embedding pins, and this file. Analyses added after seeing the data are written as an ADDENDUM before they are scored.
