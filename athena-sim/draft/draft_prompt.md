You are building a machine-readable ontology of the naming rules of one coding standard. The ontology is a property graph in node-link JSON. Read the standard below and write the ontology.

## What to produce

Output exactly one JSON object and nothing else: no explanation, no comments, no text before or after it. A Markdown code fence around the object is allowed. The object has these keys:

- "directed": true
- "multigraph": false
- "graph": {}
- "nodes": a list of node objects
- "links": a list of link objects

## Nodes

Every node has "id" (unique string) and "type". Use only these four node types.

1. Standard (exactly one):
   {"id": "<STANDARD_ID>", "type": "Standard", "name": "<name>", "publisher": "<publisher>", "url": "<url>", "retrievedDate": "<date>", "scopeLanguages": ["<LANGUAGE_ID>"]}
   Use the values given under "Standard and language" below.

2. Language (exactly one):
   {"id": "<LANGUAGE_ID>", "type": "Language", "name": "<name>", "fileExtensions": [<extensions>], "defaultStandardId": "<STANDARD_ID>"}
   Use the values given under "Standard and language" below.

3. IdentifierKind (one for each identifier kind that at least one rule applies to):
   {"id": "<kind id>", "type": "IdentifierKind", "name": "<display name>", "applicableLanguages": ["<LANGUAGE_ID>"]}

4. NamingRule (one for each distinct naming requirement of the standard):
   {"id": "<STANDARD_ID>-<SHORT-NAME>", "type": "NamingRule", "casing": <casing or null>, "prefix": <string or null>, "suffix": <string or null>, "minLength": <integer or null>, "maxLength": <integer or null>, "forbiddenPatterns": [<strings>], "description": "<one sentence>", "rationale": <string or null>, "severity": "<severity>", "sourceStandardId": "<STANDARD_ID>", "sourceSection": "<section of the standard>"}

Field rules for NamingRule:
- "casing" is one of "PascalCase", "camelCase", "snake_case", "SCREAMING_SNAKE_CASE", "kebab-case", or null when the rule does not fix a casing.
- "prefix" and "suffix" are the literal strings the name must start or end with, or null.
- "minLength" and "maxLength" are bounds on the length of the name, or null.
- "forbiddenPatterns" is a list of regular expressions or literal words that a name must not match; use [] when there are none.
- "description" is a paraphrase in your own words, not a quotation.
- "rationale" is a short paraphrase of the reason when the standard states one, otherwise null.
- "severity" is "MUST", "SHOULD" or "MAY", taken from the normative language of the standard: flat imperatives and "must" and "always" map to "MUST"; "should", "prefer" and "recommended" map to "SHOULD"; "may", "can" and "optional" map to "MAY".
- "sourceSection" names the section of the standard where the rule is stated.
- Rule ids are unique and start with "<STANDARD_ID>-".

## Links

Every link has "source", "target" and "relation". Use only these two relations.

- {"source": "<rule id>", "target": "<LANGUAGE_ID>", "relation": "APPLIES_TO"} and {"source": "<rule id>", "target": "<kind id>", "relation": "APPLIES_TO"}: one link to the language and one link for each identifier kind the rule applies to. A rule that applies to several kinds has one link per kind.
- {"source": "<rule id>", "target": "<STANDARD_ID>", "relation": "DEFINED_IN"}: one link for each rule.

## Identifier kinds

Use these kind ids where they fit: class, interface, method, function, variable, constant, parameter, field, property, module, package, namespace, enum, enum_member, boolean_variable, type_parameter.
If the standard needs an identifier kind that is not in this list, add it with a new lowercase snake_case id. Do not add a kind that the standard does not need.

## Scope

- Include only rules about the spelling of identifiers: casing, prefix, suffix, length, and forbidden or required words in a name.
- Do not include rules about comments, documentation, formatting, spacing, file layout, language features, or design.
- Include only what the standard states. Do not add rules from your own knowledge of the language or of other standards. If the standard is silent on a kind, add no rule for it.
- Do not add examples, comment rules, or other node types, and do not add other relations.

## Standard and language

- Standard id: <STANDARD_ID>
- Standard name: <STANDARD_NAME>
- Publisher: <PUBLISHER>
- URL: <URL>
- Retrieved date: <RETRIEVED_DATE>
- Language id: <LANGUAGE_ID>
- Language name: <LANGUAGE_NAME>
- File extensions: <EXTENSIONS>

## The standard

<<<STANDARD_TEXT
<STANDARD_TEXT>
STANDARD_TEXT>>>
