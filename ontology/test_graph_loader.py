"""Tests for the OVERRIDES / CONFLICTS_WITH step of graph_loader.get_applicable_rules.
Run:  python3 test_graph_loader.py   (from this folder; skipped when networkx is not installed)
"""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    import networkx as nx
    from networkx.readwrite import json_graph
    import graph_loader
except SystemExit:          # graph_loader exits when networkx is missing
    nx = None


def make(rules, edges):
    """rules: {id: standard}; every rule applies to (py, variable)."""
    nodes = [{"id": "py", "type": "Language"}, {"id": "variable", "type": "IdentifierKind"},
             {"id": "S1", "type": "Standard"}, {"id": "S2", "type": "Standard"}]
    links = []
    for rid, std in rules.items():
        nodes.append({"id": rid, "type": "NamingRule", "severity": "MUST", "description": rid})
        links += [{"source": rid, "target": "py", "relation": "APPLIES_TO"},
                  {"source": rid, "target": "variable", "relation": "APPLIES_TO"},
                  {"source": rid, "target": std, "relation": "DEFINED_IN"}]
    links += [{"source": s, "target": t, "relation": r} for r, s, t in edges]
    data = {"directed": True, "multigraph": False, "graph": {}, "nodes": nodes, "links": links}
    return json_graph.node_link_graph(data, edges="links")


def ids(results):
    return [r["rule"]["id"] for r in results]


@unittest.skipIf(nx is None, "networkx is not installed")
class TestPrecedence(unittest.TestCase):
    RULES = {"A": "S2", "B": "S1", "C": "S1"}

    def test_no_edges(self):
        res = graph_loader.get_applicable_rules(make(self.RULES, []), "py", "variable")
        self.assertEqual(ids(res), ["A", "B", "C"])
        self.assertTrue(all(r["conflicts_with"] == [] for r in res))

    def test_override_needs_an_active_standard_that_defines_the_overrider(self):
        g = make(self.RULES, [("OVERRIDES", "A", "B")])
        self.assertEqual(ids(graph_loader.get_applicable_rules(g, "py", "variable")), ["A", "B", "C"])
        self.assertEqual(ids(graph_loader.get_applicable_rules(g, "py", "variable", "S1")), ["A", "B", "C"])
        self.assertEqual(ids(graph_loader.get_applicable_rules(g, "py", "variable", "S2")), ["A", "C"])

    def test_chain_leaves_the_head(self):
        g = make({"A": "S2", "B": "S2", "C": "S1"}, [("OVERRIDES", "A", "B"), ("OVERRIDES", "B", "C")])
        self.assertEqual(ids(graph_loader.get_applicable_rules(g, "py", "variable", "S2")), ["A"])

    def test_cycle(self):
        g = make({"A": "S2", "B": "S2"}, [("OVERRIDES", "A", "B"), ("OVERRIDES", "B", "A")])
        with self.assertRaises(ValueError):
            graph_loader.get_applicable_rules(g, "py", "variable", "S2")

    def test_conflicts_are_flagged_on_both_ends(self):
        g = make(self.RULES, [("CONFLICTS_WITH", "B", "C")])
        res = {r["rule"]["id"]: r["conflicts_with"] for r in graph_loader.get_applicable_rules(g, "py", "variable")}
        self.assertEqual(res, {"A": [], "B": ["C"], "C": ["B"]})

    def test_conflict_with_an_overridden_rule_is_dropped(self):
        g = make(self.RULES, [("CONFLICTS_WITH", "B", "C"), ("OVERRIDES", "A", "B")])
        res = {r["rule"]["id"]: r["conflicts_with"] for r in graph_loader.get_applicable_rules(g, "py", "variable", "S2")}
        self.assertEqual(res, {"A": [], "C": []})

    def test_the_shipped_ontology_is_unaffected(self):
        g = graph_loader.load_graph()
        for lang, kind in (("python", "variable"), ("csharp", "boolean_variable"), ("javascript", "class")):
            res = graph_loader.get_applicable_rules(g, lang, kind)
            self.assertTrue(res)
            self.assertTrue(all(r["conflicts_with"] == [] for r in res))


if __name__ == "__main__":
    unittest.main()
