import json
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from athena import agreement  # noqa: E402


def onto(rules, kinds=("method", "field")):
    nodes = [{"id": "cpp", "type": "Language"}] + [{"id": k, "type": "IdentifierKind"} for k in kinds]
    links = []
    for rid, attrs, applies in rules:
        base = {"id": rid, "type": "NamingRule", "casing": None, "prefix": None, "suffix": None,
                "minLength": None, "maxLength": None, "forbiddenPatterns": [], "severity": "MUST"}
        base.update(attrs)
        nodes.append(base)
        links.append({"source": rid, "target": "cpp", "relation": "APPLIES_TO"})
        for k in applies:
            links.append({"source": rid, "target": k, "relation": "APPLIES_TO"})
    return {"nodes": nodes, "links": links}


def load(data):
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8") as fh:
        json.dump(data, fh)
    try:
        return agreement.load(fh.name)
    finally:
        os.unlink(fh.name)


def write_pack(root, pack, human, llm):
    os.makedirs(os.path.join(root, pack, "llm"))
    with open(os.path.join(root, pack, f"{pack}_ontology.json"), "w", encoding="utf-8") as fh:
        json.dump(human, fh)
    with open(os.path.join(root, pack, "llm", "llm_ontology.json"), "w", encoding="utf-8") as fh:
        json.dump(llm, fh)


class AgreementTest(unittest.TestCase):
    def test_compare_packs_pooled_and_errors(self):
        a = onto([("A", {"casing": "snake_case"}, ["method"]), ("B", {"prefix": "m_"}, ["field"])])
        b = onto([("X", {"casing": "PascalCase"}, ["method"]), ("Y", {"prefix": "m_"}, ["field"])])
        with tempfile.TemporaryDirectory() as d:
            write_pack(d, "p1", a, a)
            write_pack(d, "p2", a, b)
            res = agreement.compare_packs(d, ["p1", "p2"], boot=50)
            self.assertEqual(res["p1"]["observed_agreement"], 1.0)
            self.assertLess(res["p2"]["observed_agreement"], 1.0)
            self.assertEqual(res["pooled"]["n_items"], res["p1"]["n_items"] + res["p2"]["n_items"])
            with self.assertRaises(ValueError):
                agreement.compare_packs(d, ["missing"], boot=50)
            os.unlink(os.path.join(d, "p1", "llm", "llm_ontology.json"))
            with self.assertRaises(ValueError):
                agreement.compare_packs(d, ["p1"], boot=50)

    def test_identical_ontologies(self):
        d = onto([("A", {"casing": "snake_case"}, ["method"]), ("B", {"prefix": "m_"}, ["field"])])
        r = agreement.compare(load(d), load(d), boot=50)
        self.assertEqual(r["observed_agreement"], 1.0)
        self.assertEqual(len(r["matched_units"]), 2)
        self.assertEqual(r["disagreements"], [])

    def test_casing_alias_and_set_label(self):
        h = onto([("A", {"casing": "UPPER_SNAKE_CASE"}, ["method"])])
        l = onto([("X", {"casing": "SCREAMING_SNAKE_CASE"}, ["method"])])
        r = agreement.compare(load(h), load(l), boot=50)
        self.assertEqual(r["per_attribute"]["casing"]["agreement"], 1.0)

    def test_one_sided_kinds_reported_not_scored(self):
        h = onto([("A", {"casing": "snake_case"}, ["method"])])
        l = onto([("X", {"casing": "snake_case"}, ["field"])])
        r = agreement.compare(load(h), load(l), boot=50)
        self.assertEqual(r["matched_units"], [])
        self.assertEqual(r["human_only_units"], [["cpp", "method"]])
        self.assertEqual(r["llm_only_units"], [["cpp", "field"]])
        self.assertIsNone(r["kappa"])

    def test_disagreement_listed_and_kappa_below_one(self):
        h = onto([("A", {"casing": "snake_case"}, ["method"]), ("B", {"prefix": "m_"}, ["field"])])
        l = onto([("X", {"casing": "PascalCase"}, ["method"]), ("Y", {"prefix": "m_"}, ["field"])])
        r = agreement.compare(load(h), load(l), boot=50)
        self.assertEqual([d["attribute"] for d in r["disagreements"]], ["casing"])
        self.assertLess(r["kappa"], 1.0)

    def test_kappa_by_hand(self):
        pairs = [("a", "a"), ("a", "b"), ("b", "b"), ("b", "b")]
        po, k = agreement.cohen_kappa(pairs)
        self.assertAlmostEqual(po, 0.75)
        self.assertAlmostEqual(k, 0.5)

    def test_degenerate_kappa_is_none(self):
        self.assertIsNone(agreement.cohen_kappa([("a", "a")] * 3)[1])


if __name__ == "__main__":
    unittest.main()
