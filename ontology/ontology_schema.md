# Athena Ontology Schema — v1 (Task B.1)

Status: draft for implementation. Expands the sketch in `Athena Journal Outline.md`
into a full, implementable property-graph schema for the coding-standard ontology that the
Graph RAG retriever queries.

## Design goals

1. **Language- and standard-agnostic core.** The same six node types and five edge types must
   represent PEP 8, Google Java Style, .NET naming guidelines, Google TypeScript Style, and
   Airbnb JavaScript Style without special-casing any one of them, so a 6th language/standard can
   be added later without a schema change.
2. **Traceable provenance.** Every rule must be traceable back to the exact standard + section it
   came from, both for the paper's methodology section and so a human reviewer (or Athena's
   validator) can explain *why* a suggestion was made.
3. **Override-aware.** A user's project-specific standard (e.g. the MFU construction-course
   standard mentioned as future work) must be able to *override* or *conflict with* a
   built-in language standard for the same (Language, IdentifierKind) pair, so the retriever can
   resolve precedence deterministically rather than concatenating contradictory rules into the
   prompt.
4. **Retrieval-shaped.** Node/edge structure should map directly onto the query the Graph RAG
   retriever runs at generation time: "given this Language and this IdentifierKind (and any
   active custom standard), return the applicable NamingRule/CommentRule nodes, their compliant
   and non-compliant Examples, ranked by specificity."

## Node types

### 1. `Standard`
Provenance node — one per source document.

| Attribute | Type | Notes |
|---|---|---|
| `id` | string | e.g. `PEP8`, `GOOGLE_JAVA`, `DOTNET_DESIGN`, `GOOGLE_TS`, `AIRBNB_JS` |
| `name` | string | full title |
| `publisher` | string | e.g. "Python Software Foundation", "Google", "Microsoft", "Airbnb" |
| `url` | string | canonical source URL |
| `retrievedDate` | date | date Athena's authors last checked it (these are living/versionless web documents, not dated releases) |
| `scopeLanguages` | [Language.id] | languages this standard governs |

### 2. `Language`
| Attribute | Type | Notes |
|---|---|---|
| `id` | string | `python`, `java`, `csharp`, `typescript`, `javascript` |
| `name` | string | display name |
| `fileExtensions` | [string] | e.g. `[".py"]` |
| `defaultStandardId` | Standard.id | the standard Athena applies by default for this language in the benchmark |

### 3. `IdentifierKind`
The syntactic category a naming/comment rule targets. Kept language-agnostic; not every kind
applies to every language (see `applicableLanguages`).

| Attribute | Type | Notes |
|---|---|---|
| `id` | string | `class`, `interface`, `method`, `function`, `variable`, `constant`, `parameter`, `field`, `property`, `module`, `package`, `namespace`, `enum`, `enum_member`, `boolean_variable`, `type_parameter` |
| `name` | string | display name |
| `applicableLanguages` | [Language.id] | e.g. `interface` → `[java, typescript, csharp]` only |

### 4. `NamingRule`
| Attribute | Type | Notes |
|---|---|---|
| `id` | string | unique, e.g. `PEP8-VAR-SNAKE` |
| `casing` | enum | `PascalCase, camelCase, snake_case, SCREAMING_SNAKE_CASE, kebab-case, none` |
| `prefix` / `suffix` | string \| null | e.g. `I` prefix for C# interfaces, `_` prefix for Python "internal" names |
| `minLength` / `maxLength` | int \| null | |
| `forbiddenPatterns` | [string] | regexes or literal words, e.g. single-char names outside loop counters |
| `description` | string | **paraphrased** rule statement (not verbatim guide text — see §Extraction methodology) |
| `rationale` | string | why the rule exists, when the source states one |
| `severity` | enum | `MUST, SHOULD, MAY` — normalized from the source's own normative language |
| `sourceStandardId` | Standard.id | |
| `sourceSection` | string | e.g. "PEP 8 § Naming Conventions" |

### 5. `CommentRule`
| Attribute | Type | Notes |
|---|---|---|
| `id` | string | |
| `format` | enum | `docstring-google, docstring-numpy, javadoc, jsdoc, xmldoc, plain-line-comment, none` |
| `requiredElements` | [string] | subset of `summary, params, returns, raises, type, example` |
| `triggerCondition` | string | when the rule fires, e.g. "all public modules, functions, classes, methods" |
| `description` | string | paraphrased |
| `severity` | enum | `MUST, SHOULD, MAY` |
| `sourceStandardId` | Standard.id | |
| `sourceSection` | string | |

### 6. `Example`
| Attribute | Type | Notes |
|---|---|---|
| `id` | string | |
| `code` | string | short snippet, **original**, written by the Athena authors to illustrate the rule — never copied verbatim from a copyrighted style guide |
| `isCompliant` | bool | |
| `explanation` | string | one line |

## Edge types

| Edge | From → To | Semantics |
|---|---|---|
| `APPLIES_TO` | `NamingRule\|CommentRule` → `Language`, and → `IdentifierKind` | rule is active for this (language, kind) pair |
| `DEFINED_IN` | `NamingRule\|CommentRule` → `Standard` | provenance |
| `HAS_EXAMPLE` | `NamingRule\|CommentRule` → `Example` | illustrative example(s), both compliant and non-compliant |
| `OVERRIDES` | `NamingRule\|CommentRule` → `NamingRule\|CommentRule` | a project-specific rule supersedes a built-in one for the same (language, kind); retriever suppresses the overridden node when an override is active |
| `CONFLICTS_WITH` | `NamingRule\|CommentRule` ↔ `NamingRule\|CommentRule` | two *simultaneously active* rules disagree and neither overrides the other (surfaced to the user rather than silently resolved) |

## Retrieval query shape

Given a code element with `(language, identifierKind)` and an optional active custom `Standard`:

1. Find all `NamingRule`/`CommentRule` nodes with `APPLIES_TO → language` and
   `APPLIES_TO → identifierKind`.
2. If an active custom standard defines an `OVERRIDES` edge onto any node in that set, drop the
   overridden node and keep the override.
3. Flag any remaining pair connected by `CONFLICTS_WITH`.
4. Walk `HAS_EXAMPLE` on the surviving nodes to assemble few-shot (compliant, non-compliant)
   pairs for the prompt builder (chain-of-thought over: rule → rationale → example → target
   identifier).

## Serialization

Interchange format is a flat node-link JSON document (directly loadable via
`networkx.readwrite.json_graph.node_link_graph`):

```json
{
  "directed": true,
  "multigraph": false,
  "graph": {},
  "nodes": [
    {"id": "PEP8", "type": "Standard", "name": "...", "publisher": "...", "url": "...", "retrievedDate": "2026-09-25", "scopeLanguages": ["python"]},
    {"id": "python", "type": "Language", "name": "Python", "fileExtensions": [".py"], "defaultStandardId": "PEP8"},
    {"id": "variable", "type": "IdentifierKind", "name": "Variable", "applicableLanguages": ["python","java","csharp","typescript","javascript"]},
    {"id": "PEP8-VAR-SNAKE", "type": "NamingRule", "casing": "snake_case", "prefix": null, "suffix": null, "minLength": null, "maxLength": null, "forbiddenPatterns": [], "description": "...", "rationale": "...", "severity": "SHOULD", "sourceStandardId": "PEP8", "sourceSection": "..."},
    {"id": "EX-PEP8-VAR-1", "type": "Example", "code": "user_count = 0", "isCompliant": true, "explanation": "..."}
  ],
  "links": [
    {"source": "PEP8-VAR-SNAKE", "target": "python", "relation": "APPLIES_TO"},
    {"source": "PEP8-VAR-SNAKE", "target": "variable", "relation": "APPLIES_TO"},
    {"source": "PEP8-VAR-SNAKE", "target": "PEP8", "relation": "DEFINED_IN"},
    {"source": "PEP8-VAR-SNAKE", "target": "EX-PEP8-VAR-1", "relation": "HAS_EXAMPLE"}
  ]
}
```

`NetworkX` is sufficient at this scale (5 standards × ~10-15 rules each ≈ 60-80 rule nodes, a few
hundred nodes total) — no need for a Neo4j server for the benchmark; the paper can note Neo4j as
a drop-in path for scaling to many more standards, matching the outline's original note.

## Rule-extraction methodology (Task B.2)

Because PEP 8, the Google style guides, the .NET design guidelines, and the Airbnb guide are each
copyrighted running prose (not machine-readable rule tables), extraction is **manual/semi-
automated with a fixed template**, not scraped verbatim:

1. **Source of record.** Use each standard's current canonical web page (URLs recorded on the
   `Standard` node) as of the `retrievedDate`, since three of the five are living documents with
   no version-pinned release.
2. **One rule = one template instance.** For every distinct naming or commenting requirement,
   fill the `NamingRule`/`CommentRule` attribute template above by hand, writing `description`
   and `rationale` as **paraphrase**, not verbatim quotation, and citing `sourceSection` precisely
   enough for a reviewer to locate the original passage.
3. **Original examples only.** `Example.code` snippets are written fresh by the authors to
   illustrate the paraphrased rule — never lifted from the guide's own code blocks — both to
   avoid reproducing copyrighted example code and to keep examples short and uniform in style
   across all five standards.
4. **Severity normalization.** Map each source's own normative language onto `MUST/SHOULD/MAY`
   (RFC 2119-style): PEP 8 mostly uses "should"; the Google guides mostly state rules as flat
   imperatives (treated as `MUST` unless hedged with "prefer" / "if possible", which map to
   `SHOULD`); the .NET guidelines explicitly label items "Do" / "Consider" / "Avoid" / "Do not",
   which map to `MUST` / `SHOULD` / `SHOULD NOT` / `MUST NOT` respectively (`SHOULD NOT`/`MUST
   NOT` folded into `severity` with an inverted `forbiddenPatterns`-style rule where applicable);
   Airbnb's ESLint-derived rules map by their reported severity (`error` → `MUST`, `warn` →
   `SHOULD`).
5. **Correctness check.** Each extracted rule is spot-checked against the live source page a
   second time before being marked verified (mirrors the WebSearch cross-verification discipline
   already used for the Sonar Deep Research reference list).
6. **Known gaps documented, not silently dropped.** Where a standard is silent on something the
   other four cover (e.g. Airbnb's guide says little about comment *format* beyond brace/spacing
   style), the gap is recorded as `coverage: none` rather than inferring a rule that was never
   stated — this becomes a documented limitation in the paper's benchmark-design section rather
   than a fabricated rule.

## Open items carried to Task B.3/B.4

- Graph RAG retriever implementation (ranking when multiple examples match, top-k selection).
- Prompt-builder template consuming the retrieved subgraph (few-shot + chain-of-thought, per the
  outline's Section 3 "things to add" list).
- Ontology construction tooling to make step 2 above less manual for future standards (out of
  scope for the benchmark's fixed 5-language/5-standard set, but worth a Discussion-section
  mention as a limitation/threat to validity: manual extraction doesn't scale to arbitrary
  organizational standards without tooling).
