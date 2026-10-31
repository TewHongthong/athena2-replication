# Registered Amendment: Study 2 of Vol. 2

Status: registered amendment to HYPOTHESES_v2.md. It was written after the results of the registered study (Study 1) were known and before the benchmark of Study 2 was built. HYPOTHESES_v2.md is not changed. This file is included in the hash of the Study 2 freeze; after the freeze it is not edited, and any later analysis is written in a separate addendum before it is scored.
What was known when this file was written is stated in Section 0, because it shaped the design.

## 0. What Study 2 tests

Study 1 left RQ1 without a confirmatory answer. Zero-shot compliance on the development units was 95.0% (Godot), 97.5% (dotnet-runtime) and 98.3% (Odoo), so no standard was eligible for H1. Every injected violation was a change of casing, and a program that knows the kind and the rule restores every test task (addendum A10). The rules that a model cannot infer from a common convention were outside the core, because the kind alone does not tell when they apply: the Godot prefixes p_ and r_ for parameters, and the dotnet-runtime prefixes _, s_ and t_ for internal and private fields. Among the Godot parameter trials that passed core_ok, 27.7% of the names proposed with no standard in the prompt lacked the prefix, against 0% with selection (addendum A8).

Study 2 asks the question of RQ1 where these rules apply: on rules whose applicability depends on more than the identifier kind, does selection give higher compliance than no standard, the naming sections of the document, the whole document, and lexical or dense retrieval? The violations are a missing or a wrong prefix, not a change of casing.

Odoo is not part of Study 2: its human ontology holds no rule whose applicability depends on more than the kind.

## 1. Data and split

- Standards and code: the Godot C++ guidelines and the dotnet/runtime coding style, with the documents and the corpus pins of Study 1.
- Ontologies: the author adds finer identifier kinds for the cases above to the human ontologies of the two standards, as new files; the Study 1 files are unchanged. The rules of HYPOTHESES_v2 Section 3.1 apply: no LLM drafts, proposes or edits their content. Godot: input_parameter and output_parameter. dotnet-runtime: fields by accessibility and storage (instance, static, thread-static, public, constant). The author decides which rules enter the core and records the reason for each excluded rule, as in Study 1. The core table is generated from the ontology.
- Facets from the code: for C#, the accessibility modifiers, static, const and the ThreadStatic attribute, read from the syntax. For a Godot parameter the standard says "used to return a value", which the syntax does not show. The metadata label is taken from the prefix of the original name (the gate ensures that every original name passes the Study 2 core); the inferred label is output for a reference or a pointer that is not const, and input otherwise. The agreement of the inferred label with the metadata label is reported.
- Units: for Godot, the unit of Study 1 (a function or method of 6 to 40 lines with no parse error); for dotnet-runtime, a type declaration (class or struct) of 6 to 60 lines with no parse error. A unit qualifies if it holds at least one identifier of a Study 2 kind.
- Gate: a unit enters the pool only if every identifier that the Study 2 core checks passes the core rules.
- Split: the rule of Study 1 (SHA-256 of the UTF-8 path mod 100 < 30 = dev), so a file is on the same side in both studies. Units that were Study 1 tasks may be drawn; their number is reported.
- Selection: as D13 of Study 1, with the seed athena2-s2-v1: 30 dev and 70 test tasks per pack, at most 3 tasks per file, and the same policy if the pool is short.
- Injection: one violation per task, on a target of a Study 2 kind drawn with the seed of the task draw. The method is drawn with a fixed seed so that half of the tasks of each pack remove the required prefix and half replace it with the prefix of a sibling kind (p_ and r_; _, s_ and t_). The checks of D18 apply: the new name is a valid identifier, is not already in the unit, fails the rule under the checker, keeps the parse-tree shape after every occurrence is renamed, and gives no conflict in the scope-aware check. Changes of casing are not used.
- Reported for each pack: the qualifying units, the units after the gate, and the tasks by kind and by injection method.
- Trials: 8 conditions × (70 test tasks × 3 rounds + 30 dev tasks × 1 round) × 2 packs = 3,840 trials per model.

## 2. Hypotheses

### 2.1 Models and drift check

The four panel models of Study 1. The hosted models use their Study 1 pins. The locally served models use new pins that differ from Study 1 only in the output limit, 8,192 tokens, after 14 test trials of Study 1 ended at 1,024 (addendum A11). The canary and drift rules of HYPOTHESES_v2 Section 2.1 apply, with 30 dev units of each of the two packs (60 units).

### 2.2 Conditions

none; fulldoc; naming (the passages of the pinned document whose heading path or own text matches the fixed expression of addendum A11); TF-IDF, BM25 and dense, as in Study 1; selection with the Study 2 human ontology and the kind and its facets from metadata; and the same selection with the kind and its facets inferred from the code. No setting of any condition is changed from Study 1 (number of passages, instruction of the embedding model, prompt wording).

Primary metric core_ok_s2: the proposed name passes every core rule of the Study 2 core for its kind (unparseable = fail). Secondary: Study 1 core_ok (casing only), the share of names with the right prefix, exact_match, tokens and cost. A program that applies the rule from the kind and its facets, as in addendum A10, is reported as a reference, not as a hypothesis.

| # | Hypothesis | Status |
|---|---|---|
| H1-S2 | For every standard included by Section 2.3: selection > none in core_ok_s2 | confirmatory (the only one) |
| H2-S2 | selection is no more than 2 pp below naming | secondary |
| H3-S2 | selection is no more than 2 pp below fulldoc, and higher than TF-IDF, BM25 and dense | secondary |
| H4-S2 | Inferring the kind and its facets from the code lowers core_ok_s2 by at most 5 pp relative to metadata | exploratory |

### 2.3 Eligibility, decided before the freeze

A standard is included in H1-S2 if the mean core_ok_s2 of condition none on its 30 dev units, over the four panel models, is below 90%. The decision is made on the development split before the freeze and is reported. If no standard is included, Study 2 stops before any test trial and that result is reported; the threshold, the metric and the benchmark are not changed to reach eligibility.
Defects found in the development round may be fixed before the freeze. If a fix changes the task set, the core, the checker or a prompt, the development round is repeated in full, both rounds are reported, and eligibility is decided on the repeated round.

### 2.4 Decision criteria

A cell is one (standard, model) pair on the test split; at most 2 standards × 4 models = 8 cells. Intervals are 95% cluster-bootstrap intervals over source files. The verdicts of H2-S2 to H4-S2 are given per cell and summarised as in HYPOTHESES_v2 Section 2.4.

| H | Quantity | Supported when | Clearly against when |
|---|---|---|---|
| H1-S2 | selection − none, per included standard and model | exact two-sided sign test, Holm-adjusted p < 0.05, and a positive mean difference | — |
| H2-S2 | selection − naming; mean prompt length of both | lower CI limit > −2 pp | upper CI limit < −2 pp |
| H3-S2 | selection − fulldoc; selection − each of TF-IDF, BM25, dense | lower CI limit > −2 pp against fulldoc, and a positive mean difference with Holm-adjusted exact sign test p < 0.05 against each retrieval condition | upper CI limit < −2 pp against fulldoc |
| H4-S2 | infer − metadata | lower CI limit > −5 pp | upper CI limit < −5 pp |

A result in the "clearly against" column is reported in the same way as a supported one.

## 3. Rules that apply in every case

- HYPOTHESES_v2 Section 3 applies to Study 2.
- The development round is the pilot. It is used to check that the procedure runs and to decide eligibility (Section 2.3), not to tune any condition.
- Nothing from Study 1 is rerun or rescored; Study 1 is reported as registered.
- The Study 2 ontologies, core tables, benchmark and pins are new files; no file under the freeze of Study 1 is changed.

## 4. Analysis plan

- As HYPOTHESES_v2 Section 4: the unit is the task (mean of core_ok_s2 over three rounds), paired with none on the same task; the cluster bootstrap resamples source files with the resamples and the seed of Study 1. H1-S2 has its own Holm family of at most 8 tests. All other comparisons are exploratory, with Holm within each report table.
- Reported for each pack and model next to the results: the tasks whose snippet holds another identifier that carries the prefix the task requires; the agreement of the inferred facets with metadata; the result of the reference program; the trials that ended at the output limit.

## 5. Limitations

- The design of Study 2 was chosen after the results of Study 1 were known, including results on its test split (addenda A8, A10, A11). The tasks are new, but the rules tested were chosen because they separated the conditions in Study 1.
- Two standards in two languages, one family of rules per standard; the results do not extend to Odoo or to other kinds of rules.
- One human encoder; the core rules that score the answers come from the same ontology that selection reads.
- A program that knows the kind and its facets restores the required prefix, as in Study 1; the tasks ask whether a model applies a rule it may not know, not whether a repair exists.
- The snippet may show the required prefix on other identifiers, which a model can copy without the standard; the number of such tasks is reported.
- The Godot standard defines an output parameter by its use; the metadata label is read from the original name and the inferred label from the type, and either can differ from the use.
- The locally served models differ from Study 1 in their output limit.
- The standards and repositories are public, so training-data leakage remains an alternative explanation.
- With 70 test tasks per standard, the 2 pp margins can be confirmed only where the per-task differences vary little.
- The hosted models have no dated snapshots; the drift check uses 60 paired units and detects only large shifts.

## 6. Procedure

Notation: PACK is godot-s2 or dotnet-runtime-s2; PIN is luna, gemini31fl, qwen35_9b_s2 or gemma4_local_s2; FAMILY is meta or infer. These names are those planned for the harness; the commands are checked against its command-line interface with a mock backend before the freeze, and a name that differs is corrected in this text, not in the code.

1. Record this file in version control before the benchmark is built.
2. The author writes the Study 2 ontologies; the core tables are generated from them and pass the loader checks.
3. Build the benchmark: facets in the extractors, type-declaration units for C#, gate, task selection, injection, and validation with validate_benchmark.py --core (0 errors).
4. Pin the locally served models at an output limit of 8,192 tokens.
5. Development round: each PIN on each PACK, all eight conditions, one round, on the 30 dev tasks. Decide eligibility (Section 2.3); stop if no standard is included.
6. Close the code and the documents. Freeze once for each (PACK, PIN, FAMILY), 16 files: meta = none, fulldoc, naming, chunk, bm25, dense, graph; infer = graph with --no-oracle.
7. Canary before the first test trial of a model; test runs with --frozen; canary after the last test trial; apply the drift criteria.
8. Analyse with the commands listed in the README of the package, written before the freeze.
9. Evidence kept: the frozen files and their ledgers, runs/, the pins, the Study 2 ontologies and benchmark, and this file.
