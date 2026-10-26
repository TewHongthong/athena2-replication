# C++ extractor plan (Athena-2, WP2/WP3)

Status: **Phases 1–4 are implemented; the branch `wp2-cpp-extractor` is merged into `master`. The measured results are summarized in §10.** The original text of §0–§8 is the pre-implementation plan, except where it was corrected to match the code and noted in §10.4 and §10.6. This file is at `athena-corpus/curation/CPP_EXTRACTOR_PLAN.md`.

## 0. Status (after Phase 4 and the H2 causal test)

| Done | Not yet done |
|---|---|
| tree-sitter-cpp in `libtsall.so` + symbol `cpp` in `tsbind.py` | `syntax_check.py` and `make_index.py` still list the five Vol. 1 languages only (`curate.py`, `rules.py`, `validate_benchmark.py` are wired; `make_report.py` only knows the display name "C++": `cpp` in `ALL_LANGS`/`ID_PREFIX`, `_RESERVED["cpp"]`, the per-pack `core_rules.json` loaded by `core_table.py`) |
| `lang_ts.py`: `IDENT_TYPES/STRING_TYPES["cpp"]`, roles in `_classify_tokens`, `_cpp(cx)` (decl + facet + unit), `CPP_COARSE`, `extract()` supports `cpp` | The Godot ontology (built by the author by hand, without LLM assistance) |
| `curate.py`: guard C5 in `plan_rename` only for `lang == "cpp"` (7 lines); `tools/fetch_corpus_pins.py` (C6) — builds `corpus_v2/` from the pins; tested on Godot on a local machine (167 files, verify 0 problems) and on all 3 repos in the cloud | |
| `tools/cpp_census.py`, `tools/dump_facts.py` (A3 reason breakdown), `tools/check_rename_roundtrip.py` (A2+A4), `tools/h2_causal.py` (read-only H2 causal test) | Running `curate.py` on the pinned C++ corpus (needs the author's ontology and `core_rules.json`; the code path is tested on a mock ontology in `tests_core/`) |
| `tests_cpp/`: fixture, `test_cpp_extractor.py` (A1), `test_cpp_hazards.py` (H1–H8 etc.) — 25 tests | |

**Constraints:** the human ontologies of the 3 standards are authored independently and are not drafted or edited here; do not touch the frozen Vol. 1 files; do not over-claim in the manuscript; Odoo is distributed only as hash + path + script.

## 1. Principles

1. **The extractor emits only structural facts** — construct kind + facets (`Decl.extra`); it does not embed Godot's naming conventions (`p_`, `r_`, leading `_`, `GDCLASS`) in code. Those belong to the ontology.
2. `Decl.kind` uses the pipeline's existing coarse vocabulary (`class interface enum enum_member function method property field constant variable parameter boolean_variable`) through **one** table, `CPP_COARSE` in `lang_ts.py`; the fine-grained name is in `extra["cpp_kind"]`; constructs the existing vocabulary lacks → `kind=None`.
3. `CORE[("cpp", kind)]`, `default_standard["cpp"]` and any new kinds all **come from the author's ontology** — once it is done, adjust `CPP_COARSE` in that single place to match the kind ids in the ontology.
4. **No guessing**: inside an ERROR span no decl is emitted and tokens are `other`.
5. **Vol. 1 must not be affected**: the facts dump before/after the change must be identical byte for byte (A5).

## 2. Evidence (Godot census at pin `5ec712e220b7`, 167 files still present at the pin)

| Item | Value |
|---|---|
| Files with a parse error | 42 / 167 |
| All `function_definition` / without ERROR | 1,995 / 1,935 (97.0%) |
| Macro-like declarators (UPPER_SNAKE without a return type, e.g. `GDCLASS(...)`) | 140 |
| `template_function` (real templates + casts + misread `a<b`) | 341 |
| Most common parents of ERROR nodes | `qualified_identifier` 234, `expression_statement` 146, `initializer_list` 69 |

Re-run: §7 Step 1 · the number of qualifying units, 771 (6–40 lines, no error; before the consistency gate), is in `pins/godot_units.tsv`

**Additional hazards probed** (tree-sitter-cpp `c0092228`):

| # | Code | tree-sitter gives | Effect on the extractor |
|---|---|---|---|
| H1 | `GDCLASS(Widget, Base);` in a class body | `declaration` + `function_declarator` named `GDCLASS`, arguments as `parameter_declaration` (type_identifier) | Must not be emitted as a method; all tokens are `other` |
| H2 | `_FORCE_INLINE_ int get_size() const {…}` | `function_definition` with an **ERROR** (type = `_FORCE_INLINE_`, `int` inside the ERROR) | This unit falls out at the parse-error gate → **a bias to record in Threats**: inline functions in headers that use this macro are dropped from the benchmark |
| H3 | `a < b` in an expression | Sometimes a `template_function` with no ERROR | The token `b` may be a `type_identifier` although it is a variable → a guard is needed when renaming (C5) |
| H4 | `String name(p_a);` in a function body | `declaration` + `function_declarator` (`p_a` = `type_identifier` in a parameter_declaration) | Inside a compound_statement treat it as the **local variable** `name`; tokens in the parameter_list are `ref`, not `type` |
| H5 | `Foo() = default;` / `Foo::Foo() : a(0) {…}` / `~Foo()` / `operator==` | Name = class name / `destructor_name` / `operator_name` | No decl; `Foo` is `type` (goes with the class), `~Foo` tokenizes only the inner identifier, `operator_name` = `other` |
| H6 | `int (*callback)(int);` | `function_declarator` whose `.declarator` is a `parenthesized_declarator` | It is a **field/variable**, not a method (walk down the declarator chain to the real name) |
| H7 | `sizeof(Node)` | `Node` is an `identifier` in a `parenthesized_expression` | A type name may be `ref` — handled by guard C5 |
| H8 | `#define`, `#if DEBUG`, `#ifdef X` | identifiers in `preproc_*` | All `other` |

## 3. Design decisions (the first option of each is the one adopted)

| # | Topic | Options |
|---|---|---|
| **C1** Unit | **(a) `function_definition` only** — free functions, out-of-class methods, inline methods in a class; use the existing 6–40-line range · (b) also add small class/struct — not recommended (macros in the body + H1) |
| **C2** Coarse kind | **(a) Emit the fine-grained `cpp_kind` + `kind` from the `CPP_COARSE` table** (struct/union→`class`, `enum class`→`enum`, `static const`/`constexpr`→`constant`, free function→`function`, namespace/typedef/using/macro/template param→`None`) · (b) emit `kind=None` for everything until the ontology is done — safest, but rename cannot be tested through `curate.py` |
| **C3** Macros | **(a) A macro invocation in a class body → no decl, tokens `other`; `#define` → decl `kind=None, exempt="macro"`; a macro call inside a function body (`ERR_FAIL_COND(x)`) emits its arguments as `ref` as usual** · (b) drop every unit containing a macro call — drops almost all, not recommended |
| **C4** ERROR | **(a) Strict: no decl inside an ERROR span, tokens `other`, units overlapping an ERROR fall out at the existing gate** · (b) best-effort — risks wrong renames |
| **C5** Misparse (H3/H7) | **(a) Add a guard only for `cpp` in `plan_rename`: if there is a token with the same name that is not counted in the span (and is not a decl) → reject with reason `unclaimed_token:<role>`** (does not change other languages' behaviour) · (b) no guard — the rename will be incomplete but the shape fingerprint cannot catch it |
| **C6** Vol. 2 corpus | **(a) `tools/fetch_corpus_pins.py` builds `corpus/<lang>/*.md` in the same format as Vol. 1 from the pins (Odoo is built on the machine, not committed)** → `curate.py`'s loader needs no change · (b) make `curate.py` read directly from git — change the loader + tie it to a clone |

These are the options adopted for the implementation phases in §8.

## 4. Spec

### 4.1 construct → decl (node names follow tree-sitter-cpp)

| construct | name node | `cpp_kind` | `kind` | `ns` | `exempt` | facets in `extra` |
|---|---|---|---|---|---|---|
| `#define NAME…` (`preproc_def`, `preproc_function_def`) | `.name` | `macro` | `None` | type | `macro` | — |
| `namespace N` / `A::B` | `namespace_identifier` | `namespace` | `None` | type | — | — |
| `class/struct/union X {…}` (with a body) | `.name` | `class`/`struct`/`union` | `class` | type | — | `template`, `bases` (text) |
| `enum E` / `enum class E` | `.name` | `enum`/`enum_class` | `enum` | type | — | `scoped` |
| enumerator | `enumerator.name` | `enum_member` | `enum_member` | member | — | `enum` |
| data member | declarator chain → `field_identifier` | `field` | `field` | member | — | `access`, `static`, `const_obj`, `ptr`, `ref_kind`, `type_class` (`bool`/`other`), `array` |
| data member that is `static const` or `constexpr` | same as above | `static_const_field` | `constant` | member | — | same as above |
| method (declared or defined in a class) | `function_declarator.declarator` = `field_identifier` | `method` | `method` | member | — | `access`, `static`, `virtual`, `override`, `pure`, `const_method`, `in_class_def`, `proto` |
| method defined outside the class | `qualified_identifier.name` | `method` | `method` | member | — | `out_of_class`, `scope` (text), `const_method` |
| free function | `function_declarator.declarator` = `identifier` | `free_function` | `function` | type | — | `static`, `inline_kw`, `proto` |
| ctor / dtor / `operator…` / conversion | — | — | **no decl** (H5) | | | |
| function pointer member/variable (H6) | name in the chain | `field`/`variable` | `field`/`variable` | member/local | — | `fnptr` |
| `typedef … X;` / `using X = …;` | `type_identifier` | `type_alias` | `None` | type | — | — |
| template parameter (`typename T`, `int N`) | `type_identifier` / `identifier` | `template_param` | `None` | type | — | — |
| parameter | `parameter_declaration` declarator chain | `param` | `parameter` | local | — | `ptr`, `ref_kind` (`lref`/`rref`/`none`), `const_ref`, `proto` |
| lambda parameter | same as above | `param` | `parameter` | local | `lambda_param` | — |
| local variable (including `auto`, range-for, `if (auto x = …)`, catch, structured binding, H4) | declarator chain | `local` | `variable` | local | — | `static`, `const_obj`, `ptr`, `ref_kind`, `type_class` |
| local `const`/`constexpr` | same as above | `local_const` | `constant` | local | — | same as above |
| label | `statement_identifier` | — | no decl; token `other` | | | |

Notes: `access` = `public/protected/private` (default for `class` = private, for `struct` = public); decls with the same name (declared in a header + defined outside the class) are separate decls in the same ns — the existing `plan_rename` already handles this.

### 4.2 Token roles

| Context | role |
|---|---|
| A position that is a decl (per §4.1) | `decl` |
| `type_identifier`; `namespace_identifier` (the scope of `::`); the identifier inside `destructor_name`; the class name in a ctor/dtor that matches the class | `type` |
| `field_expression.field` (`.x`, `->x`); `field_initializer` (member name in an initializer list); `field_designator`; `qualified_identifier.name` | `member` |
| `using namespace X;` / `using X::y;` | `import` |
| Ordinary identifiers (variables, called function names, bare enumerators, arguments of a macro call inside a function body, H4/H7) | `ref` |
| Every identifier in `preproc_*`; in a macro-like declaration (H1); `statement_identifier`; `operator_name`; attributes `[[…]]`; inside ERROR/MISSING | `other` |

The token-emission scope = the types in `IDENT_TYPES["cpp"]` = `identifier, field_identifier, type_identifier, namespace_identifier, statement_identifier, destructor_name` (the token of `destructor_name` = the child identifier, excluding `~`); `STRING_TYPES["cpp"]` = `string_content, raw_string_content, character, system_lib_string` (**to be confirmed with the fixture + census in Phase 1**); the existing `COMMENT_TYPES` works (`comment`).

### 4.3 Units

- Emit a `UnitCand` for every `function_definition` (curate filters to 6–40 lines itself)
- label: `function name` (free) · `method Scope::name` (out of class) · `method Class.name` (inline in a class)
- `top_level=True` for namespace/global scope and outside a class; `False` for inline in a class
- Do not emit units for class/struct (C1a); do not emit lambdas as units

### 4.4 `shape` / `reverify`

Same as the other languages: `shape = tuple(node.type for node in root.walk())`; `reverify(new_src)` re-parses with the `cpp` grammar and compares the shape.

## 5. Places to change (file : location)

| File | Change |
|---|---|
| `lang_ts.py` | `IDENT_TYPES["cpp"]`, `STRING_TYPES["cpp"]` · `_classify_tokens`: a `lang == "cpp"` branch · function `_cpp(cx)` + the `CPP_COARSE` table · `extract()`: add `elif lang == "cpp": _cpp(cx)` **before** `else: _tsjs(cx)` (currently the `else` catches every remaining language) · the file-header docstring |
| `curate.py` (Phase 3–4) | `plan_rename`: guard C5 only for `lang == "cpp"` · (once the ontology exists) `LANGS`, `ID_PREFIX` (lines 41–42) |
| `rules.py` (once the ontology exists) | `_RESERVED["cpp"]` (C++ keywords) · `CORE[("cpp", …)]` — **from the author's ontology** |
| `make_report.py` (8–9), `syntax_check.py` (32), `validate_benchmark.py` (34, 39), `make_index.py` (18) | Hard-coded language lists — add `cpp` only at wire-up |
| **Do not touch** | `lang_python.py`, `make_comment_units.py`, `validate_comment_units.py`, `pipeline/`, `benchmark/`, `corpus/` of Vol. 1 |

`curate.py` cannot run on `cpp` until the ontology has a `cpp` language node + `CORE` → in the meantime test the extractor through `tools/dump_facts.py`.

## 6. Acceptance criteria

| # | Criterion | How measured |
|---|---|---|
| **A1** | Fixture `godot_like.cpp`: 0 ERROR and decls match every row of the table below (34 decls) | a test comparing `dump_facts` with the table |
| **A2** | Every pinned Godot file: no extractor exception; every `function_definition` without an ERROR gets a `UnitCand` | `dump_facts --pin godot --strict` |
| **A3** | Every ident token that is `other` must have an identifiable reason (`error_span` / `macro_like` / `preproc` / `label` / `attribute`) → `unexplained = 0`; report the share of each reason among all ident tokens (no ceiling — `error_span` is a consequence of C4 strict and must be reported as a bias) | the A3 line of `--summary` (reasons are derived from tree-sitter node names, not from `lang_ts.py` code) — measured in Phase 1: other 1,171/91,996 = 1.27% (error_span 0.52%, macro_like 0.47%, preproc 0.21%, label 0.07%, attribute 0.01%), unexplained 0; error_span 245 of 482 comes from a single file (`winrt_defines.h`) |
| **A4** | Rename round-trip for every target that enters the plan: shape unchanged and **every reject has a named reason** (no empty rejects) | tested in Phase 3 with a script that calls `plan_rename` + `reverify` on the decls the extractor emits (no ontology needed) |
| **A5** | Vol. 1: the `diff -r` of the facts dump before/after is empty; after touching `curate.py`, also compare the output of a full Vol. 1 `curate.py` run before/after (see §7 Step 2) | `diff -r` — tested: facts dump of 792 files run twice identical byte for byte; `curate.py --languages python --per-language 20` run twice, `diff -r` empty (repeatability of the other languages not yet tested) |

**Table A1** (line numbers refer to `godot_like.cpp`):

| line | name | cpp_kind | kind | ns | exempt |
|---|---|---|---|---|---|
| 1 | MY_MAX | macro | None | type | macro |
| 3 | Demo | namespace | None | type | — |
| 5 | Mode | enum | enum | type | — |
| 6, 7 | MODE_IDLE, MODE_RUN | enum_member | enum_member | member | — |
| 10 | T | template_param | None | type | — |
| 11 | Holder | class | class | type | — |
| 12 | value | field | field | member | — |
| 15 | get | method | method | member | — |
| 18 | Widget | class | class | type | — |
| 21 | MAX_ITEMS | static_const_field | constant | member | — |
| 22, 23, 24 | item_count, items, _dirty | field | field | member | — |
| 27 | State | enum | enum | type | — |
| 27 | STATE_OFF, STATE_ON | enum_member | enum_member | member | — |
| 32 | set_count (declaration) / p_count | method / param | method / parameter | member / local | — |
| 33 | get_count | method | method | member | — |
| 34 | p_other | param | parameter | local | — |
| 35 | create / p_name / r_error | method / param / param | method / parameter / parameter | member / local / local | — |
| 47 | set_count (definition outside the class) / p_count | method / param | method / parameter | member / local | — |
| 49 | old_count | local | variable | local | — |
| 51 | notify | local | variable | local | — |
| 51 | p_value | param | parameter | local | lambda_param |
| 54 | name | local | variable | local | — |
| 62 | create (definition outside the class) / p_name / r_error | method / param / param | method / parameter / parameter | member / local / local | — |
| 63 | result | local | variable | local | — |

There must be **no** decl for: `GDCLASS` (line 19), ctor/dtor (29, 30, 38, 43), `operator==` (34), `a`/`b` in the macro (1), `names` (not declared). The 5 units that should be emitted: `get` (15), `Widget::Widget` (38–41), `Widget::~Widget` (43–45), `Widget::set_count` (47–60), `Widget::create` (62–66); only `set_count`, being ≥ 6 lines long, qualifies.

## 7. Steps + commands (copy-paste)

The commands are written for bash (WSL or Git Bash) — if the machine is not WSL, adjust `A2`/`V1` to the real paths.

### Step 0 — Setup + branch + parser check

```bash
export A2=/mnt/c/Users/tew_hon/Desktop/project2/athena2
export V1=/mnt/c/Users/tew_hon/Desktop/project2/coding/athena-corpus
export GIT_AUTHOR_NAME="Tew Hongthong" GIT_AUTHOR_EMAIL=tew.hon@mfu.ac.th
export GIT_COMMITTER_NAME="Tew Hongthong" GIT_COMMITTER_EMAIL=tew.hon@mfu.ac.th
cd $A2 && git status --short && git switch -c wp2-cpp-extractor
cd $A2/athena-corpus/curation && python3 tools/smoke_test_treesitter.py
```

### Step 1 — Census (read-only, no code changes)

```bash
cd $A2/athena-corpus/curation
python3 tools/cpp_census.py --files tests_cpp/fixtures/godot_like.cpp --top 5     # no network
python3 tools/cpp_census.py --json ~/godot_census.json --top 60                    # the first run clones Godot as a blobless clone into ~/.cache/athena2/godot.git
```

### Step 2 — Vol. 1 baseline (always do this **before** changing `lang_ts.py`)

```bash
cd $A2/athena-corpus/curation
python3 tools/dump_facts.py --corpus $V1 --out ~/athena2_facts/before --strict --summary     # ~30 seconds, 792 files
# Second layer: a full curate.py run (takes a long time — on the VM, csharp alone took 89 seconds and python 55 seconds;
# the full 5 languages did not finish within 3 minutes). Run it before touching curate.py and again after Phase 3
python3 curate.py --corpus $V1 --out ~/athena2_facts/curate_before --per-language 100
```

### Step 3 — Implementation (4 phases, each reviewed before the next starts)

The phases and their constraints are described in §8. After each phase, run Step 4 before starting the next one.

### Step 4 — Check after each phase

```bash
cd $A2/athena-corpus/curation
python3 tools/dump_facts.py --corpus $V1 --out ~/athena2_facts/after --strict
diff -r ~/athena2_facts/before ~/athena2_facts/after && echo "A5 OK: Vol. 1 unchanged"
python3 tools/dump_facts.py --lang cpp --files tests_cpp/fixtures/godot_like.cpp --out - --summary --strict | head -80
```

### Step 5 — Sweep Godot (from Phase 2 onwards)

```bash
cd $A2/athena-corpus/curation
python3 tools/dump_facts.py --lang cpp --pin godot --out ~/athena2_facts/godot --summary --strict
```

Look at the A2/A3 lines of the summary; if `unexplained` > 0 the summary prints sample `file:line token` entries — go back and fix the rule in §4.2 for that token.

### Step 6 — Commit per phase (after the results have been reviewed)

```bash
cd $A2 && git add athena-corpus/curation && git status --short
git commit -m "WP2: C++ extractor phase N — <short summary>"
```

### Step 7 — After Phase 3 (separate work)

`tools/fetch_corpus_pins.py` (C6) builds `corpus/cpp/*.md` from `pins/godot_units.tsv` + `godot_new_files.tsv` + a clone — done (output in `corpus_v2/`); then wait for the author's ontology before wiring up (`LANGS`, `ID_PREFIX`, `_RESERVED`, `CORE`, the language lists in 4 scripts).

### Rollback

```bash
cd $A2 && git switch master        # all the work is on the branch wp2-cpp-extractor
```

## 8. Implementation phases and constraints

Follow §4 (spec) and §6 (acceptance criteria), using the option adopted in every item of §3 (no exceptions).

Constraints (apply to every phase):
- No ontology is created or edited; no `CORE[("cpp", …)]` or `default_standard["cpp"]` is added; no Godot naming rules are put into code.
- `lang_python.py`, `make_comment_units.py`, `validate_comment_units.py`, `pipeline/` and the Vol. 1 benchmark/corpus folders are not touched.
- The behaviour for java/csharp/typescript/javascript/python must not change. After every phase run

  ```bash
  python3 tools/dump_facts.py --corpus $V1 --out ~/athena2_facts/after --strict && diff -r ~/athena2_facts/before ~/athena2_facts/after
  ```

  and the result must be empty (set `$V1` first).
- Each phase is committed only after the results of the check commands have been reviewed.
- `tests_cpp/fixtures/godot_like.cpp`, `tools/dump_facts.py` and `tools/cpp_census.py` are not modified; if a change turns out to be necessary, the reason is documented first.
- Anything the spec does not cover is raised for a decision rather than guessed.

Phase 1 — skeleton (no decls emitted yet): `IDENT_TYPES["cpp"]`, `STRING_TYPES["cpp"]`, a `cpp` branch in `_classify_tokens` per §4.2, a `_cpp(cx)` that emits only tokens/error_spans/comment_spans/string_spans, and `elif lang == "cpp"` in `extract()` before the `else`. Check: no exception on the fixture, the role histogram is sensible, the Vol. 1 diff is empty.

Phase 2 — decls per §4.1 + facets + `CPP_COARSE` + tests: `tests_cpp/test_cpp_extractor.py` compares the fixture with table A1 (the table is kept in the test as data and is not read from the extractor's output). Check: A1 passes, the Vol. 1 diff is empty.

Phase 3 — units + reverify + hazards + guard: `UnitCand` per §4.3, shape/reverify, a small test for each of H1–H8 (hand-written snippets, not Godot code), guard C5 in `curate.plan_rename` only for `lang == "cpp"`, and the A4 script (`tools/check_rename_roundtrip.py`) that calls `plan_rename` + `reverify` on the decls the extractor emits on the pinned Godot without using an ontology. Check: A2, A3, A4, and a full Vol. 1 `curate.py` run with an empty diff against `~/athena2_facts/curate_before`.

Phase 4 — summary at the end of this file (actual A1–A5 measurements, the biases found such as H2, what has not been done). Only what was measured is reported.

## 9. Unknowns / risks

- A3 has been measured (§10.2) — the criterion was changed to "every `other` has an identifiable reason", with no ceiling; the share of `error_span` is still a bias that must be reported
- The §4.2 table came from small probe snippets and was adjusted after sweeping Godot (added the macro-like rule with a type, dropped whole `preproc_*` nodes) — repos other than the pinned Godot have not been swept
- The H2 bias was counted in §10.3 (both for all `function_definition` and for the 6–40-line range only: 27 of 798 fall out = 3.38%, concentrated in header files; causally tested, see the paragraph "Causal test" at the end of §10.3)
- The figure of 97.0% of `function_definition` without ERROR was measured only on files after the cutoff (167 files), not on the whole repo
- For Qwen3.5-9B the cutoff has no official date (see the WP2 doc) — unrelated to the extractor, but it affects the meaning of "after the cutoff" for this Godot set

## 10. Summary of Phases 1–4 and the H2 causal test

Only measured values are reported. All C++ data come from the pinned Godot commit `5ec712e220b7` (167 files). The A1–A5 results are in §10.2 (including the A3 reason breakdown in `tools/dump_facts.py`); the H2 bias for the 6–40-line range and the causal test are in §10.3.

### 10.1 What was done

- **Phase 1** — token roles, spans, shape · **Phases 2–3** — decl + facets + `CPP_COARSE`, `UnitCand`, reverify, H1–H8, guard C5, A2/A4 scripts
- No `CORE[("cpp", …)]`, `default_standard["cpp"]` or Godot naming rules in the code; `lang_python.py`, `make_comment_units.py`, `validate_comment_units.py`, `pipeline/`, `benchmark/`, and Vol. 1 `corpus/` were not touched

### 10.2 A1–A5 measurements

| # | Result | How measured |
|---|---|---|
| **A1** | **Pass** — fixture 0 ERROR, 34 decl rows match every row of the §6 table (kind, ns, exempt), no decl for `GDCLASS`/ctor/dtor/`operator==`/`a`,`b` in the macro/`names`, tokens of every decl have role `decl`; the 5 units match what was expected | `python3 -m unittest tests_cpp/test_cpp_extractor.py` (6 tests; the table is data in the test) |
| **A2** | **Pass** — extractor exceptions 0; `function_definition` 1,995 (60 with ERROR, 1,935 without); without ERROR but without a UnitCand = 0; total units 1,995 | `tools/check_rename_roundtrip.py` + `dump_facts --pin godot --strict` |
| **A3** | **Pass** — ident tokens 91,996; `other` 1,188 (1.29%): error_span 482 (0.52%), macro_like 473 (0.51%), preproc 163 (0.18%), label 63 (0.07%), attribute 7 (0.01%); unexplained **0**. Before the A3 patch to `dump_facts.py`, unexplained = 7 (macros chained without `;` and `MACRO("str")` that the old classifier did not recognize); `error_span` 245 of 482 comes from a single file (`winrt_defines.h`) — that figure is carried over from the Phase 1 measurement in §6 and was not re-measured | `dump_facts --lang cpp --pin godot --summary --strict` |
| **A4** | **Pass** — qualifying units (6–40 lines, not overlapping an ERROR) 771; targets 2,407 (≤ 6 per unit, distinct names, length ≥ 3, kind ≠ None, not exempt); entered the plan 2,386; after reparse the shape is unchanged 2,386; **shape changed 0**; rejects without a reason 0; all 21 rejects are `unclaimed_token:member` (see §10.5); uses synthetic new names, no ontology; run time 901 seconds | `tools/check_rename_roundtrip.py` |
| **A5** | **Pass** — (a) Vol. 1 facts dump, 792 files, 5 languages, `diff -r` against `~/athena2_facts/before` is empty after every phase and after the A3 patch (0 exceptions); (b) full `curate.py --corpus $V1 --per-language 100` on a local machine → 5 languages, 500 snippets, 2,957 violation files, `diff -r` against `~/athena2_facts/curate_before` (created before the code change) is empty | `diff -r` |

All tests: 25 tests pass (`tests_cpp/test_cpp_extractor.py` 6 + `tests_cpp/test_cpp_hazards.py` 19)

### 10.3 The H2 bias (`_FORCE_INLINE_` / a leading macro) — counted

60 of 1,995 `function_definition`s (3.0%) with an ERROR fall out at the `parse_error_in_unit` gate, broken down by cause (classified from the text of the function **header**, before the `{…}` body; this is a classification by text and does not prove that the macro caused the ERROR):

| Cause | Count |
|---|---|
| Header contains `_FORCE_INLINE_` | **43** |
| Header contains another UPPER_SNAKE macro (occurrences in these headers: `_ALWAYS_INLINE_` 5, `PHYSICS_2D_DISABLED` 4 — `#ifndef` inserted in a ctor's initializer list, `API_AVAILABLE` 3, `JPH_IF_DEBUG_RENDERER` 1; the total exceeds 11 because some functions have several) | **11** |
| The ERROR is only inside the function body, not the header | **6** |

**6–40-line range only (the figures Threats should use)** — counted with the same definition as `curate.py` (line count = end − start + 1; a unit falls out when an error span overlaps it) on the 167 pinned Godot files. The original counting script (`h2_count.py`) is not in the repo, but `tools/h2_causal.py` reports the same before-figures (798 / 771 / 27):

- `function_definition`s in the 6–40-line range **798** → entered the plan **771** → fell out because of ERROR **27 (3.38%)**; of all 60: short (<6) 29, in range 27, long (>40) 4
- Cross-check: totals over all 167 files match those measured before (1,995 / ERROR 60 / 43-11-6 / kept 771); the nodes that contain an ERROR and the nodes whose error span overlaps are the same set (60 = 60); the extractor's units match the `function_definition`s in every file

| Cause of the 27 (classified by header text, checked by hand) | Count |
|---|---|
| Preceded by `_FORCE_INLINE_` | **17** |
| ERROR only inside the function body (`_bind_methods`, `_notification`, `_install_android_sdk_packages`) | 4 |
| Preceded by `_ALWAYS_INLINE_` | 2 |
| `class API_AVAILABLE(…)` — the node is a **class** parsed as a `function_definition` (`metal_allocator.h:98,122`) | 2 |
| `#ifndef PHYSICS_2D_DISABLED` splitting a ctor's initializer list (`tile_map_layer.h:150,165`) | 2 |

Excluding the 2 class nodes, the figure is 25 of 796 (3.1%).

**The effect is concentrated in header files** (a selection effect that must be reported):

| File type | Candidates in range | Fell out | Share that fell out |
|---|---|---|---|
| header (`.h` / `.hpp` / `.inc`) | 45 | **22** | 48.9% |
| source (`.cpp` / `.mm` / `.cc`) | 753 | 5 | 0.66% |

- Share of units from headers: 45/798 (5.6%) of the candidates, but 23 (3.0%) of the remaining 771 — about half of the inline functions in headers are lost, while functions in `.cpp` are barely affected
- Split by whether the header text contains `::` (a heuristic): without `::` (in-class/free) 20 of 49 fell out (41%); with `::` 7 of 749 (0.9%) — correlated with the point above because most out-of-class definitions are in `.cpp`
- The 27 are in 11 files out of the 79 files that have candidates in this range (`texture_streaming.h` alone has 6)

Limitation: counted only on the 167 pinned post-cutoff Godot files; Godot uses `_FORCE_INLINE_`-style macros heavily, and a repo that does not would give different numbers.

**Causal test** — the first round ran in a cloud sandbox with the tree-sitter v0.27.1 runtime + a freshly built tree-sitter-cpp `c0092228`, on a regenerated file list (`.cpp`/`.h` added after 1 Jun 2026 and still present at the pin), and obtained a baseline matching the above on every value: 167 files, `function_definition` 1,995, ERROR 60 (43/11/6), 6–40-line range 798 → 771 → 27 fell out (17/6/4); the second round ran `tools/h2_causal.py` on the project's own `libtsall.so` and `pins/godot_new_files.tsv` gave matching numbers on all 12 values the script reports (compared by counts, not by byte-for-byte parse trees). Then `_FORCE_INLINE_`/`_ALWAYS_INLINE_` were replaced with `inline` (keeping byte positions the same) and the files re-parsed:
- Headers containing `_FORCE_INLINE_`: 44, ERROR in 43; `_ALWAYS_INLINE_`: 5, ERROR in 5
- Whole corpus: functions with an ERROR 60 → 14 (46 disappeared, no function started a new ERROR); 6–40-line range fell out 27 → 10; candidate functions in `.h` (6–40-line range) surviving 23/45 (51%) → 39/45 (87%)
- In the group of 43 with `_FORCE_INLINE_`, 40 disappeared; the other 3 (`texture_streaming.h`) still have an ERROR at the `->*` operator, which is a different cause
- The remaining 10 in range: ERROR inside the function body 4, `->*` 2, `class API_AVAILABLE(…)` parsed as a function 2, `#ifndef` in an initializer list 2 (they disappear when the preprocessor lines are removed, which is not real preprocessing)

Limitations: measured at the parse level only; compilability and preservation of meaning were not checked; only the 167 pinned Godot files; grouping is by header text (one function classified as ERROR-in-body, outside the 6–40-line range, disappeared after the macro replacement because there is a macro in its body); the script is at `tools/h2_causal.py`; 5 functions without a body cannot be matched before/after by body position, so the conclusion "no new ERROR started" covers only the functions that could be matched.

### 10.4 Changes from the §4 spec

- The facet `inline_def`, which had two meanings, was split into **`in_class_def`** (method: defined inside the class body) and **`inline_kw`** (free function: has the word `inline`) — `inline_def` was removed
- A field uses **`ref_kind`** (`none`/`lref`/`rref`) + `ptr` like param/local; there is no bool facet `ref`
- The macro-like rule (H1) was extended to cover (a) `NAME(args)` whose type is a macro (e.g. `GDVIRTUAL0_REQUIRED`) when several macros are chained without `;` and (b) `MACRO0(x)` / `MACRO("str")` whose type is UPPER_SNAKE with a digit or `_` + a parenthesized declarator, at class/namespace level; the ctor of a class with an UPPER name (e.g. `RID();`) is not treated as a macro; a method declaration with a leading macro (`_FORCE_INLINE_ Stream *f(int);`) is **not** macro-like and still gets a decl
- `Foo() = default;` is a `function_definition` in tree-sitter-cpp and therefore also gets a UnitCand (it is too short to pass the 6-line minimum anyway)

### 10.5 Limitations and known gaps

**No decl emitted (measured; differs from the 43 / 25 / 1 in an earlier Phase 2 note, see the remark):**

| Case | Count | Definition used for measuring |
|---|---|---|
| Global/namespace-level variables (`int g = 1;`, `static const int h`) | **38** | a `declaration` at translation_unit/namespace/`#if` level (skipping `linkage_specification`), no ERROR in the node, not macro-like/function/typedef; 44 if declarations that also contain an ERROR are counted |
| Static members outside the class (`int Foo::count = 0;`) | **28** | the name is a `qualified_identifier` in the definition (same count whether or not ERROR is included) |
| Class that is a template specialization / qualified name | **1** (`is_zero_constructible<AudioFrame>`, `audio_frame.h:152`) | a `class_specifier` with a body whose name is not a `type_identifier` |

Remark: an earlier Phase 2 note gave 43 / 25 / 1 without stating the counting method. Under the definitions above the measured values are 38 / 28 / 1; the method that would give 43 and 25 is unknown, so the measured values are used. If 43 / 25 are cited, the counting method must be stated.

**Guard C5 (not relaxed):**
- It rejects 21 of 2,407 targets (0.87%), all `unclaimed_token:member`, and all 21 targets are `local` — local variables with the same name as a member accessed via `x.size()`, `a->node`, `String::utf16(…)`; the tokens the guard refuses to accept (checked ≤ 2 tokens per target) are all in `field_expression.field` or `qualified_identifier.name`, i.e. a different member from the variable. No misparse was found among those checked, so this is **lost recall**, not a bug, and it is a selection effect that must be reported (targets whose name collides with a member are dropped)
- **The guard never caught a real H3/H7 misparse in the pinned Godot** — protection against H3/H7 can be confirmed only through unit tests on hand-written snippets
- **A4 checks only the shape of the parse** — a rename that is incomplete but still parses with the same shape would not be caught, so **the 2,386 that passed do not prove that the rename was complete**; the only evidence of completeness is guard C5 + unit tests

### 10.6 Not yet done

- No ontology / `CORE[("cpp", …)]` / `default_standard["cpp"]` / `_RESERVED["cpp"]`; no `cpp` in `LANGS`, `ID_PREFIX` and the 4 scripts (`make_report.py`, `syntax_check.py`, `validate_benchmark.py`, `make_index.py`) → `curate.py` still cannot run on `cpp` and the full pipeline on C++ has never been measured (consistency gate, selection, the number of usable units after the gate)
- `tools/fetch_corpus_pins.py` (C6) has been added (not yet tied to `curate.py` — waiting for the ontology); the extractor has not been tested on Odoo (Python) or dotnet/runtime (C#), which use the existing Vol. 1 extractors
- All of §4.1 has been checked only against the fixture, the test snippets and the pinned Godot; constructs that do not appear in these three sources (e.g. `template_template_parameter_declaration`, conversion operators, `friend` with a definition) have not been checked
