#!/usr/bin/env python3
"""
Merge the 5 per-standard rule-extraction files into one unified Athena
coding-standard ontology, conforming to ontology_schema.md (Task B.1/B.2).

Adds the shared Language and IdentifierKind nodes, converts each standard's
namingRules/commentRules/examples into schema-compliant nodes, and generates
the APPLIES_TO / DEFINED_IN / HAS_EXAMPLE edges. Writes a single node-link
JSON file loadable via networkx.readwrite.json_graph.node_link_graph.
"""
import json
import os
import sys

SCRATCH = os.path.dirname(os.path.abspath(__file__))
STANDARDS_DIR = os.path.join(SCRATCH, "standards")
OUT_PATH = os.path.join(SCRATCH, "athena_ontology.json")

STANDARD_FILES = [
    "pep8.json",
    "google_java.json",
    "dotnet.json",
    "google_ts.json",
    "airbnb_js.json",
]

# --- Shared Language nodes -------------------------------------------------
LANGUAGES = [
    {"id": "python", "type": "Language", "name": "Python", "fileExtensions": [".py"], "defaultStandardId": "PEP8"},
    {"id": "java", "type": "Language", "name": "Java", "fileExtensions": [".java"], "defaultStandardId": "GOOGLE_JAVA"},
    {"id": "csharp", "type": "Language", "name": "C#", "fileExtensions": [".cs"], "defaultStandardId": "DOTNET_DESIGN"},
    {"id": "typescript", "type": "Language", "name": "TypeScript", "fileExtensions": [".ts", ".tsx"], "defaultStandardId": "GOOGLE_TS"},
    {"id": "javascript", "type": "Language", "name": "JavaScript", "fileExtensions": [".js", ".jsx"], "defaultStandardId": "AIRBNB_JS"},
]
LANGUAGE_IDS = {l["id"] for l in LANGUAGES}

# The full set of IdentifierKind ids allowed anywhere in the ontology
# (per ontology_schema.md and the agents' extraction instructions).
ALL_KIND_IDS = [
    "class", "interface", "method", "function", "variable", "constant",
    "parameter", "field", "property", "module", "package", "namespace",
    "enum", "enum_member", "boolean_variable", "type_parameter",
]

KIND_DISPLAY_NAMES = {
    "class": "Class", "interface": "Interface", "method": "Method",
    "function": "Function", "variable": "Variable", "constant": "Constant",
    "parameter": "Parameter", "field": "Field", "property": "Property",
    "module": "Module", "package": "Package", "namespace": "Namespace",
    "enum": "Enum", "enum_member": "Enum Member",
    "boolean_variable": "Boolean Variable", "type_parameter": "Type Parameter",
}


def load_standards():
    docs = []
    for fname in STANDARD_FILES:
        path = os.path.join(STANDARDS_DIR, fname)
        with open(path, "r", encoding="utf-8") as f:
            docs.append(json.load(f))
    return docs


def build():
    docs = load_standards()

    nodes = []
    links = []
    seen_node_ids = set()
    unknown_kinds = set()

    def add_node(n):
        if n["id"] in seen_node_ids:
            raise ValueError(f"Duplicate node id across standards: {n['id']}")
        seen_node_ids.add(n["id"])
        nodes.append(n)

    # 1. Language nodes
    for lang in LANGUAGES:
        add_node(lang)

    # 2. IdentifierKind nodes — applicableLanguages computed from which
    #    standards actually used that kind (a standard's scopeLanguages[0]
    #    is that language).
    kind_to_languages = {k: set() for k in ALL_KIND_IDS}

    for doc in docs:
        lang_id = doc["standard"]["scopeLanguages"][0]
        for rule in doc.get("namingRules", []) + doc.get("commentRules", []):
            k = rule["identifierKind"]
            if k not in kind_to_languages:
                unknown_kinds.add(k)
                kind_to_languages[k] = set()
            kind_to_languages[k].add(lang_id)

    for kind_id in ALL_KIND_IDS:
        add_node({
            "id": kind_id,
            "type": "IdentifierKind",
            "name": KIND_DISPLAY_NAMES[kind_id],
            "applicableLanguages": sorted(kind_to_languages.get(kind_id, set())),
        })

    # 3. Per-standard: Standard node, rule nodes, example nodes, and edges
    rule_id_to_lang = {}
    for doc in docs:
        std = doc["standard"]
        add_node(std)
        lang_id = std["scopeLanguages"][0]
        if lang_id not in LANGUAGE_IDS:
            raise ValueError(f"Standard {std['id']} references unknown language {lang_id}")

        all_rules = doc.get("namingRules", []) + doc.get("commentRules", [])
        rule_ids_this_doc = set()
        for rule in all_rules:
            kind_id = rule["identifierKind"]
            rule_ids_this_doc.add(rule["id"])
            rule_id_to_lang[rule["id"]] = lang_id
            add_node(rule)  # keep identifierKind as a convenience attribute too
            links.append({"source": rule["id"], "target": lang_id, "relation": "APPLIES_TO"})
            links.append({"source": rule["id"], "target": kind_id, "relation": "APPLIES_TO"})
            links.append({"source": rule["id"], "target": std["id"], "relation": "DEFINED_IN"})

        for ex in doc.get("examples", []):
            add_node(ex)
            if ex["ruleId"] not in rule_ids_this_doc:
                raise ValueError(f"Example {ex['id']} references unknown ruleId {ex['ruleId']} in {std['id']}")
            links.append({"source": ex["ruleId"], "target": ex["id"], "relation": "HAS_EXAMPLE"})

    if unknown_kinds:
        print(f"WARNING: identifierKind values not in the schema's allowed set: {sorted(unknown_kinds)}", file=sys.stderr)

    graph_doc = {
        "directed": True,
        "multigraph": False,
        "graph": {
            "name": "Athena Coding-Standard Ontology",
            "version": "1.0",
            "generatedDate": "2026-09-25",
            "schemaRef": "ontology_schema.md (Task B.1)",
        },
        "nodes": nodes,
        "links": links,
    }

    with open(OUT_PATH, "w", encoding="utf-8") as f:
        json.dump(graph_doc, f, indent=2, ensure_ascii=False)

    # --- Summary stats ---
    type_counts = {}
    for n in nodes:
        type_counts[n["type"]] = type_counts.get(n["type"], 0) + 1
    rel_counts = {}
    for l in links:
        rel_counts[l["relation"]] = rel_counts.get(l["relation"], 0) + 1

    print(f"Wrote {OUT_PATH}")
    print(f"Total nodes: {len(nodes)}  |  Total edges: {len(links)}")
    print("Nodes by type:", type_counts)
    print("Edges by relation:", rel_counts)
    coverage = {}
    for doc in docs:
        std_id = doc["standard"]["id"]
        coverage[std_id] = {
            "namingRules": len(doc.get("namingRules", [])),
            "commentRules": len(doc.get("commentRules", [])),
            "examples": len(doc.get("examples", [])),
        }
    print("Per-standard rule/example counts:")
    for k, v in coverage.items():
        print(f"  {k}: {v}")


if __name__ == "__main__":
    build()
