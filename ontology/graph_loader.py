#!/usr/bin/env python3
"""
NetworkX loader + retrieval demo for the Athena coding-standard ontology
(athena_ontology.json), implementing the retrieval query shape described in
ontology_schema.md § "Retrieval query shape" (Task B.3 groundwork).

Usage:
    python3 graph_loader.py                       # load + print summary stats
    python3 graph_loader.py python variable        # demo retrieval query
    python3 graph_loader.py csharp boolean_variable
"""
import json
import os
import sys

try:
    import networkx as nx
    from networkx.readwrite import json_graph
except ImportError:
    sys.exit("networkx is required: pip install networkx --break-system-packages")

SCRATCH = os.path.dirname(os.path.abspath(__file__))
ONTOLOGY_PATH = os.path.join(SCRATCH, "athena_ontology.json")


def load_graph(path=ONTOLOGY_PATH):
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return json_graph.node_link_graph(data, edges="links")


def get_applicable_rules(graph, language_id, identifier_kind_id, active_standard_id=None):
    """
    Implements the 4-step retrieval query from ontology_schema.md:
      1. Find NamingRule/CommentRule nodes APPLIES_TO both language and kind.
      2. Drop every candidate that is the target of an OVERRIDES edge whose source is also a candidate and
         is defined in the active standard (`active_standard_id`). Without an active standard no override
         is in force. An overridden rule is dropped even when its own overrider is overridden (A -> B -> C
         leaves A when A and B are both defined in the active standard); a cycle among the overriding
         rules raises ValueError.
      3. Flag CONFLICTS_WITH pairs among the survivors.
      4. Walk HAS_EXAMPLE on survivors and return (rule, examples) pairs.

    Returns a list of dicts: {"rule": {...attrs}, "examples": [{...attrs}, ...],
    "conflicts_with": [ids of surviving rules joined to this one by CONFLICTS_WITH]}
    """
    if language_id not in graph:
        raise ValueError(f"Unknown language id: {language_id!r}")
    if identifier_kind_id not in graph:
        raise ValueError(f"Unknown identifierKind id: {identifier_kind_id!r}")

    # Step 1: rules that APPLIES_TO both the language and the kind.
    rules_for_language = {
        u for u, v, d in graph.in_edges(language_id, data=True)
        if d.get("relation") == "APPLIES_TO"
    }
    rules_for_kind = {
        u for u, v, d in graph.in_edges(identifier_kind_id, data=True)
        if d.get("relation") == "APPLIES_TO"
    }
    candidate_rule_ids = sorted(rules_for_language & rules_for_kind)
    candidates = set(candidate_rule_ids)

    def defined_in(rid):
        return next((t for _, t, d in graph.out_edges(rid, data=True) if d.get("relation") == "DEFINED_IN"), None)

    # Step 2: override resolution.
    overrides = {}
    if active_standard_id:
        for rid in candidate_rule_ids:
            if defined_in(rid) != active_standard_id:
                continue
            for _, target, d in graph.out_edges(rid, data=True):
                if d.get("relation") == "OVERRIDES" and target in candidates:
                    overrides.setdefault(rid, set()).add(target)
    _check_acyclic(overrides)
    overridden = {t for targets in overrides.values() for t in targets}
    active_rule_ids = [r for r in candidate_rule_ids if r not in overridden]

    # Step 3: conflicts among the survivors (an edge in either direction counts).
    survivors = set(active_rule_ids)
    conflicts = {r: set() for r in active_rule_ids}
    for u, v, d in graph.edges(data=True):
        if d.get("relation") == "CONFLICTS_WITH" and u in survivors and v in survivors:
            conflicts[u].add(v)
            conflicts[v].add(u)

    results = []
    for rid in active_rule_ids:
        rule_attrs = {"id": rid, **graph.nodes[rid]}
        examples = []
        for _, target, d in graph.out_edges(rid, data=True):
            if d.get("relation") == "HAS_EXAMPLE":
                examples.append({"id": target, **graph.nodes[target]})
        results.append({"rule": rule_attrs, "examples": examples, "conflicts_with": sorted(conflicts[rid])})
    return results


def _check_acyclic(overrides):
    state = {}

    def visit(rid, path):
        state[rid] = 1
        for tgt in sorted(overrides.get(rid, ())):
            if state.get(tgt) == 1:
                raise ValueError("OVERRIDES cycle: " + " -> ".join(path + [rid, tgt]))
            if tgt not in state:
                visit(tgt, path + [rid])
        state[rid] = 2

    for rid in sorted(overrides):
        if rid not in state:
            visit(rid, [])


def print_summary(graph):
    type_counts = {}
    for _, attrs in graph.nodes(data=True):
        type_counts[attrs.get("type", "?")] = type_counts.get(attrs.get("type", "?"), 0) + 1
    rel_counts = {}
    for _, _, attrs in graph.edges(data=True):
        rel_counts[attrs.get("relation", "?")] = rel_counts.get(attrs.get("relation", "?"), 0) + 1

    print(f"Loaded graph: {graph.number_of_nodes()} nodes, {graph.number_of_edges()} edges")
    print("Nodes by type:", type_counts)
    print("Edges by relation:", rel_counts)


def print_query_demo(graph, language_id, kind_id):
    results = get_applicable_rules(graph, language_id, kind_id)
    print(f"\nRules applicable to (language={language_id!r}, identifierKind={kind_id!r}): {len(results)} found\n")
    for r in results:
        rule = r["rule"]
        print(f"- [{rule['id']}] ({rule['type']}, severity={rule.get('severity')}) {rule.get('description', '')[:110]}")
        for ex in r["examples"]:
            mark = "OK " if ex["isCompliant"] else "BAD"
            print(f"    {mark} {ex['code']!r} — {ex['explanation']}")
        if r["conflicts_with"]:
            print(f"    conflicts with: {', '.join(r['conflicts_with'])}")


if __name__ == "__main__":
    g = load_graph()
    print_summary(g)
    if len(sys.argv) == 3:
        print_query_demo(g, sys.argv[1], sys.argv[2])
    else:
        # Sanity-check demo queries across a few languages/kinds.
        for lang, kind in [("python", "variable"), ("csharp", "boolean_variable"), ("javascript", "class")]:
            print_query_demo(g, lang, kind)
