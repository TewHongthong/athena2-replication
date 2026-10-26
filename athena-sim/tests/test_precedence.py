"""Tests for OVERRIDES / CONFLICTS_WITH handling in the graph condition.
Run:  python -m unittest discover -s tests -v   (from the athena-sim folder)

No API key, no network and no corpus are needed: the ontologies are built here.
"""
from __future__ import annotations

import json
import os
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from athena.ontology import Ontology, OverrideCycleError, rank_key  # noqa: E402
from athena.retrieval import Retriever  # noqa: E402


def build(rules, edges, *, standards=("STD", "PROJ")):
    """rules: {id: (severity, standard, [(language, kind), ...])}; edges: [(relation, source, target)]."""
    nodes = [{"id": "py", "type": "Language"}, {"id": "cs", "type": "Language"},
             {"id": "variable", "type": "IdentifierKind"}, {"id": "class", "type": "IdentifierKind"}]
    nodes += [{"id": s, "type": "Standard", "name": f"Standard {s}"} for s in standards]
    links = []
    for rid, (sev, std, applies) in rules.items():
        nodes.append({"id": rid, "type": "NamingRule", "severity": sev, "description": f"rule {rid}",
                      "casing": "snake_case"})
        links.append({"source": rid, "target": std, "relation": "DEFINED_IN"})
        for lang, kind in applies:
            links.append({"source": rid, "target": lang, "relation": "APPLIES_TO"})
            links.append({"source": rid, "target": kind, "relation": "APPLIES_TO"})
    for rel, s, t in edges:
        links.append({"source": s, "target": t, "relation": rel})
    return nodes, links


def load(nodes, links):
    fd, path = tempfile.mkstemp(suffix=".json")
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        json.dump({"directed": True, "multigraph": False, "graph": {"name": "t"}, "nodes": nodes, "links": links}, f)
    try:
        return Ontology(path)
    finally:
        os.remove(path)


PV = [("py", "variable")]
RULES = {"A": ("MUST", "PROJ", PV), "B": ("SHOULD", "STD", PV), "C": ("SHOULD", "STD", PV),
         "D": ("MAY", "STD", [("py", "class")]), "E": ("MAY", "STD", [("cs", "variable")])}


def ids(rules):
    return [r["id"] for r in rules]


class TestResolution(unittest.TestCase):
    def test_without_edges_the_result_is_the_ranked_applicable_set(self):
        onto = load(*build(RULES, []))
        got = onto.rules_for("py", "variable")
        self.assertEqual(sorted(ids(got)), ["A", "B", "C"])
        self.assertEqual(got, sorted(got, key=rank_key))
        res = onto.resolve_rules("py", "variable")
        self.assertEqual((res.overridden, res.conflicts), ([], []))

    def test_override_drops_the_target(self):
        onto = load(*build(RULES, [("OVERRIDES", "A", "B")]))
        res = onto.resolve_rules("py", "variable")
        self.assertEqual(sorted(ids(res.rules)), ["A", "C"])
        self.assertEqual(res.overridden, [("B", "A")])

    def test_override_between_rules_that_do_not_apply_here_has_no_effect(self):
        onto = load(*build(RULES, [("OVERRIDES", "D", "B"), ("OVERRIDES", "A", "E")]))
        self.assertEqual(sorted(ids(onto.rules_for("py", "variable"))), ["A", "B", "C"])
        self.assertEqual(onto.resolve_rules("py", "variable").overridden, [])

    def test_a_chain_leaves_only_the_head(self):
        onto = load(*build(RULES, [("OVERRIDES", "A", "B"), ("OVERRIDES", "B", "C")]))
        res = onto.resolve_rules("py", "variable")
        self.assertEqual(ids(res.rules), ["A"])
        self.assertEqual(res.overridden, [("B", "A"), ("C", "B")])

    def test_a_cycle_is_an_error(self):
        onto = load(*build(RULES, [("OVERRIDES", "A", "B"), ("OVERRIDES", "B", "C"), ("OVERRIDES", "C", "A")]))
        with self.assertRaises(OverrideCycleError):
            onto.rules_for("py", "variable")
        # a cycle among rules that do not apply to the query is not reached
        self.assertEqual(ids(onto.rules_for("cs", "variable")), ["E"])

    def test_bad_edges_are_rejected_at_load(self):
        with self.assertRaises(ValueError):
            load(*build(RULES, [("OVERRIDES", "A", "ZZ")]))
        with self.assertRaises(ValueError):
            load(*build(RULES, [("CONFLICTS_WITH", "A", "A")]))

    def test_standard_filter_and_active_standards(self):
        onto = load(*build(RULES, [("OVERRIDES", "A", "B")]))
        # the built-in standard alone: A is not defined there, so B stays
        self.assertEqual(sorted(ids(onto.rules_for("py", "variable", standard_id="STD"))), ["B", "C"])
        # the project standard alone: only A
        self.assertEqual(ids(onto.rules_for("py", "variable", standard_id="PROJ")), ["A"])
        # both active: A overrides B
        both = onto.rules_for("py", "variable", active_standards=("STD", "PROJ"))
        self.assertEqual(sorted(ids(both)), ["A", "C"])
        # only the built-in one is active
        self.assertEqual(sorted(ids(onto.rules_for("py", "variable", active_standards=("STD",)))), ["B", "C"])

    def test_conflicts_are_reported_and_both_rules_survive(self):
        onto = load(*build(RULES, [("CONFLICTS_WITH", "C", "B")]))
        res = onto.resolve_rules("py", "variable")
        self.assertEqual(sorted(ids(res.rules)), ["A", "B", "C"])
        self.assertEqual(res.conflicts, [("B", "C")])
        self.assertEqual(onto.conflicts_among(["B", "C", "A"]), [("B", "C")])
        self.assertEqual(onto.conflicts_among(["B", "A"]), [])

    def test_a_conflict_with_an_overridden_rule_disappears(self):
        onto = load(*build(RULES, [("CONFLICTS_WITH", "B", "C"), ("OVERRIDES", "A", "B")]))
        res = onto.resolve_rules("py", "variable")
        self.assertEqual(ids(sorted(res.rules, key=lambda r: r["id"])), ["A", "C"])
        self.assertEqual(res.conflicts, [])

    def test_deterministic(self):
        edges = [("OVERRIDES", "A", "B"), ("CONFLICTS_WITH", "A", "C")]
        a = load(*build(RULES, edges)).resolve_rules("py", "variable")
        b = load(*build(RULES, list(reversed(edges)))).resolve_rules("py", "variable")
        self.assertEqual(a, b)


class FakePack:
    def __init__(self, onto):
        self.ontology = onto

    def standard_name(self, sid):
        return f"Standard {sid}"


def context(onto, **kw):
    return Retriever(FakePack(onto), **kw).context("graph", task="rename", standard_id="STD", language="py",
                                                   kind="variable", name="x", code="x = 1")


class TestContext(unittest.TestCase):
    def test_no_edges_no_extra_fields(self):
        c = context(load(*build(RULES, [])))
        self.assertEqual(set(c.meta), {"n_items", "retrieved_ids"})
        self.assertNotIn("Note:", c.text)

    def test_override_is_recorded_and_the_target_is_not_shown(self):
        c = context(load(*build(RULES, [("OVERRIDES", "B", "C")])), top_k=None)
        self.assertEqual(c.meta["overridden"], [["C", "B"]])
        self.assertNotIn("rule C", c.text)
        self.assertNotIn("C", c.meta["retrieved_ids"])

    def test_conflict_note(self):
        c = context(load(*build(RULES, [("CONFLICTS_WITH", "B", "C")])))
        self.assertEqual(c.meta["conflicts"], [["B", "C"]])
        self.assertIn("Note: B and C disagree, and the standard does not say which one prevails.", c.text)
        self.assertTrue(c.text.endswith("prevails."))

    def test_conflict_with_a_rule_cut_by_top_k_is_not_mentioned(self):
        onto = load(*build(RULES, [("CONFLICTS_WITH", "B", "C")]))
        c = context(onto, top_k=1)
        self.assertEqual(len(c.meta["retrieved_ids"]), 1)
        self.assertNotIn("conflicts", c.meta)
        self.assertNotIn("Note:", c.text)


if __name__ == "__main__":
    unittest.main()
