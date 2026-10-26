#!/usr/bin/env python3
"""Tests of core_table.py and of the cpp wiring in curate.py / validate_benchmark.py.

The ontology used here is the Vol. 1 ontology plus a C++ language and a handful of generic TESTONLY-* rules
added in memory. They exist only to exercise the code; they are not naming rules of any real standard.

  python3 -m unittest tests_core/test_core_table.py      (from the curation folder)
"""
import copy
import json
import os
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
CUR = os.path.dirname(HERE)
sys.path.insert(0, CUR)

import core_table  # noqa: E402
import rules as R  # noqa: E402

# (rule id, kind, casing, suffix)
MOCK_RULES = [
    ("TESTONLY-CLASS", "class", "PascalCase", None),
    ("TESTONLY-ENUM", "enum", "PascalCase", None),
    ("TESTONLY-ENUM-MEMBER", "enum_member", "UPPER_SNAKE_CASE", None),
    ("TESTONLY-FUNCTION", "function", "snake_case", None),
    ("TESTONLY-METHOD", "method", "snake_case", None),
    ("TESTONLY-FIELD", "field", "snake_case", None),
    ("TESTONLY-CONSTANT", "constant", "UPPER_SNAKE_CASE", None),
    ("TESTONLY-PARAM", "parameter", "snake_case", None),
    ("TESTONLY-VARIABLE", "variable", "snake_case", None),
    ("TESTONLY-CLASS-NODE", "class", None, "Node"),       # stands for a conditional rule: excluded below
]


def mock_ontology_dict():
    with open(R.DEFAULT_ONTOLOGY, "rb") as f:
        d = json.loads(f.read().decode("utf-8"))
    d["nodes"].append({"id": "cpp", "type": "Language", "name": "C++", "fileExtensions": [".cpp"],
                       "defaultStandardId": "TESTSTD"})
    for rid, kind, casing, suffix in MOCK_RULES:
        d["nodes"].append({"id": rid, "type": "NamingRule", "identifierKind": kind, "casing": casing, "prefix": None,
                           "suffix": suffix, "minLength": None, "maxLength": None, "forbiddenPatterns": [],
                           "description": "test only", "rationale": "test only", "severity": "SHOULD",
                           "sourceStandardId": "TESTSTD", "sourceSection": "test"})
        d["links"].append({"source": rid, "target": "cpp", "relation": "APPLIES_TO"})
        d["links"].append({"source": rid, "target": kind, "relation": "APPLIES_TO"})
    return d


def mock_core_dict():
    core = {kind: [rid] for rid, kind, casing, _ in MOCK_RULES if casing}
    return {"schema": 1, "core": {"cpp": core},
            "excluded": {"TESTONLY-CLASS-NODE": "conditional: only classes that are tree nodes"}}


class CoreState(unittest.TestCase):
    """Restores the module-level tables that set_core() replaces."""

    def setUp(self):
        self._core = copy.deepcopy(R.CORE)
        self._excl = dict(R.EXCLUDED)
        self._kinds = list(R.TARGET_KINDS)
        self._spec = R._SPECIALS

    def tearDown(self):
        R.CORE.clear(); R.CORE.update(self._core)
        R.EXCLUDED.clear(); R.EXCLUDED.update(self._excl)
        R.TARGET_KINDS[:] = self._kinds
        R._SPECIALS = self._spec

    def onto(self, d=None):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        p = os.path.join(self._tmp.name, "onto.json")
        with open(p, "w", encoding="utf-8") as f:
            json.dump(d or mock_ontology_dict(), f)
        return R.Ontology(p)


class TestValidate(CoreState):
    def problems(self, mutate):
        c = mock_core_dict()
        mutate(c)
        return core_table.validate(c, self.onto())

    def test_consistent_table_has_no_problems(self):
        self.assertEqual(core_table.validate(mock_core_dict(), self.onto()), [])

    def test_unknown_language(self):
        p = self.problems(lambda c: c["core"].update({"cobol": {"class": ["TESTONLY-CLASS"]}}))
        self.assertTrue(any("'cobol' is not in the ontology" in x for x in p), p)

    def test_unknown_rule(self):
        p = self.problems(lambda c: c["core"]["cpp"].update({"class": ["NO-SUCH-RULE"]}))
        self.assertTrue(any("NO-SUCH-RULE is not a NamingRule" in x for x in p), p)

    def test_rule_of_another_kind(self):
        p = self.problems(lambda c: c["core"]["cpp"].update({"method": ["TESTONLY-CLASS"]}))
        self.assertTrue(any("does not apply to this language and kind" in x for x in p), p)

    def test_rule_of_another_language(self):
        p = self.problems(lambda c: c["core"]["cpp"].update({"class": ["PEP8-CLASS-CAPWORDS"]}))
        self.assertTrue(any("PEP8-CLASS-CAPWORDS" in x and "does not apply" in x for x in p), p)

    def test_unclassified_rule_is_reported(self):
        p = self.problems(lambda c: c["excluded"].clear())
        self.assertTrue(any("TESTONLY-CLASS-NODE is neither core nor excluded" in x for x in p), p)

    def test_core_and_excluded_at_once(self):
        p = self.problems(lambda c: c["core"]["cpp"].update({"class": ["TESTONLY-CLASS", "TESTONLY-CLASS-NODE"]}))
        self.assertTrue(any("both core and excluded" in x for x in p), p)

    def test_excluded_needs_reason(self):
        p = self.problems(lambda c: c["excluded"].update({"TESTONLY-CLASS-NODE": " "}))
        self.assertTrue(any("needs a reason" in x for x in p), p)

    def test_custom_casing_is_not_checkable(self):
        d = mock_ontology_dict()
        next(n for n in d["nodes"] if n["id"] == "TESTONLY-VARIABLE")["casing"] = "custom"
        p = core_table.validate(mock_core_dict(), self.onto(d))
        self.assertTrue(any("no mechanically checkable attribute" in x for x in p), p)

    def test_duplicate_ids_and_empty_list(self):
        p = self.problems(lambda c: c["core"]["cpp"].update({"class": ["TESTONLY-CLASS", "TESTONLY-CLASS"]}))
        self.assertTrue(any("distinct" in x for x in p), p)
        p = self.problems(lambda c: c["core"]["cpp"].update({"class": []}))
        self.assertTrue(any("non-empty list" in x for x in p), p)

    def test_schema_version(self):
        p = self.problems(lambda c: c.update({"schema": 2}))
        self.assertTrue(any("schema must be 1" in x for x in p), p)

    def test_vol1_ontology_has_no_cpp(self):
        p = core_table.validate(mock_core_dict(), R.Ontology(R.DEFAULT_ONTOLOGY))
        self.assertTrue(any("'cpp' is not in the ontology" in x for x in p), p)


class TestApply(CoreState):
    class D:  # minimal stand-in for a facts.Decl
        def __init__(self, name, kind, extra=None):
            self.name, self.kind, self.extra = name, kind, extra or {}

    def write_core(self, d):
        t = tempfile.TemporaryDirectory(); self.addCleanup(t.cleanup)
        p = os.path.join(t.name, "core_rules.json")
        with open(p, "w", encoding="utf-8") as f:
            json.dump(d, f)
        return p

    def test_apply_installs_table_and_switches_specials_off(self):
        onto = self.onto()
        self.assertEqual(core_table.apply(self.write_core(mock_core_dict()), onto), [])
        self.assertEqual(set(k[0] for k in R.CORE), {"cpp"})
        self.assertEqual(R.CORE[("cpp", "class")], ["TESTONLY-CLASS"])
        self.assertEqual(R.EXCLUDED, {"TESTONLY-CLASS-NODE": "conditional: only classes that are tree nodes"})
        self.assertIn("class", R.TARGET_KINDS)
        self.assertFalse(R._SPECIALS)
        # the Vol. 1 Python exception special case is gone
        d = self.D("MyError", "class", {"bases": ["ValueError"]})
        self.assertEqual(R.rules_for_check("python", d), [])
        self.assertEqual(R.rules_for_check("cpp", self.D("Foo", "class")), ["TESTONLY-CLASS"])

    def test_inconsistent_table_installs_nothing(self):
        bad = mock_core_dict(); bad["excluded"] = {}
        before = copy.deepcopy(R.CORE)
        self.assertTrue(core_table.apply(self.write_core(bad), self.onto()))
        self.assertEqual(R.CORE, before)
        self.assertTrue(R._SPECIALS)

    def test_vol1_defaults_untouched_without_core(self):
        self.assertTrue(R._SPECIALS)
        self.assertEqual(R.CORE[("python", "class")], ["PEP8-CLASS-CAPWORDS"])
        d = self.D("MyError", "class", {"bases": ["ValueError"]})
        self.assertEqual(R.rules_for_check("python", d), ["PEP8-CLASS-CAPWORDS", "PEP8-EXCEPTION-ERROR-SUFFIX"])
        self.assertNotIn("cpp", R.ID_PREFIX if hasattr(R, "ID_PREFIX") else {})

    def test_cpp_reserved_words(self):
        self.assertFalse(R.is_valid_new_name("cpp", "namespace"))
        self.assertFalse(R.is_valid_new_name("cpp", "nullptr"))
        self.assertTrue(R.is_valid_new_name("cpp", "item_count"))


CPP_SOURCE = """\
class Counter {
public:
	int total_count = 0;
	int last_amount = 0;

	void add_amount(int amount_value) {
		int new_total = total_count + amount_value;
		total_count = new_total;
		last_amount = amount_value;
		if (new_total > 100) {
			total_count = 0;
		}
	}

	int get_total() const {
		int current_total = total_count;
		int adjusted_total = current_total + last_amount;
		return adjusted_total;
	}
};

int compute_sum(int first_value, int second_value) {
	int sum_value = first_value + second_value;
	int double_value = sum_value * 2;
	int result_value = double_value - first_value;
	return result_value;
}
"""


def corpus_md(content):
    return ("# test\n\n- source repo: acme/demo\n- repo url: https://example.invalid/acme/demo\n"
            "- file path: src/counter.cpp\n- commit: 0123456789abcdef0123456789abcdef01234567\n"
            "- license: MIT\n- created_at: 2026-07-01\n\n```cpp\n" + content + "```\n")


class TestCppEndToEnd(unittest.TestCase):
    """curate.py --core on a tiny C++ corpus, then validate_benchmark.py --core on its output."""

    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        t = cls.tmp.name
        cls.onto = os.path.join(t, "onto.json")
        with open(cls.onto, "w", encoding="utf-8") as f:
            json.dump(mock_ontology_dict(), f)
        cls.core = os.path.join(t, "core_rules.json")
        with open(cls.core, "w", encoding="utf-8") as f:
            json.dump(mock_core_dict(), f)
        cls.corpus = os.path.join(t, "corpus_root")
        os.makedirs(os.path.join(cls.corpus, "corpus", "cpp"))
        with open(os.path.join(cls.corpus, "corpus", "cpp", "demo__counter.cpp.md"), "w", encoding="utf-8", newline="\n") as f:
            f.write(corpus_md(CPP_SOURCE))
        cls.out = os.path.join(t, "out")

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def run_py(self, script, *args):
        return subprocess.run([sys.executable, os.path.join(CUR, script), *args], capture_output=True, text=True)

    def test_1_curate_requires_core_for_cpp(self):
        r = self.run_py("curate.py", "--corpus", self.corpus, "--out", self.out + "_no_core", "--ontology", self.onto,
                        "--languages", "cpp")
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("--core", r.stderr)

    def test_2_vol1_ontology_cannot_run_cpp(self):
        r = self.run_py("curate.py", "--corpus", self.corpus, "--out", self.out + "_vol1", "--languages", "cpp",
                        "--core", self.core)
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("not in the ontology", r.stderr)

    def test_3_unknown_language(self):
        r = self.run_py("curate.py", "--corpus", self.corpus, "--out", self.out + "_x", "--ontology", self.onto,
                        "--languages", "cobol", "--core", self.core)
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("unknown language", r.stderr)

    def test_4_curate_then_validate(self):
        r = self.run_py("curate.py", "--corpus", self.corpus, "--out", self.out, "--ontology", self.onto,
                        "--languages", "cpp", "--core", self.core, "--per-language", "5")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertEqual(os.listdir(os.path.join(self.out, "snippets")), ["cpp"])      # only the requested language
        snips = sorted(os.listdir(os.path.join(self.out, "snippets", "cpp")))
        self.assertTrue(snips and all(s.startswith("cpp_") for s in snips), snips)
        with open(os.path.join(self.out, "snippets", "cpp", snips[0]), encoding="utf-8") as f:
            s = json.load(f)
        self.assertEqual(s["standardId"], "TESTSTD")
        viols = os.listdir(os.path.join(self.out, "violations", "cpp"))
        self.assertTrue(viols)
        for fn in viols:
            with open(os.path.join(self.out, "violations", "cpp", fn), encoding="utf-8") as f:
                v = json.load(f)
            self.assertTrue(v["violatedRuleId"].startswith("TESTONLY-"))
            self.assertNotEqual(v["violatedRuleId"], "TESTONLY-CLASS-NODE")                   # excluded rules never targeted
        v = self.run_py("validate_benchmark.py", "--benchmark", self.out, "--ontology", self.onto, "--languages", "cpp",
                        "--core", self.core, "--corpus", self.corpus)
        self.assertEqual(v.returncode, 0, v.stdout + v.stderr)
        self.assertIn("VALIDATION PASSED", v.stdout)

    def test_5_validate_rejects_a_foreign_rule(self):
        # same output, a core table that no longer lists the rule an injected violation used
        r = self.run_py("curate.py", "--corpus", self.corpus, "--out", self.out + "_b", "--ontology", self.onto,
                        "--languages", "cpp", "--core", self.core, "--per-language", "5")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        other = mock_core_dict()
        other["core"]["cpp"]["method"] = ["TESTONLY-FUNCTION"]
        p = os.path.join(self.tmp.name, "core_other.json")
        with open(p, "w", encoding="utf-8") as f:
            json.dump(other, f)
        v = self.run_py("validate_benchmark.py", "--benchmark", self.out + "_b", "--ontology", self.onto,
                        "--languages", "cpp", "--core", p)
        self.assertNotEqual(v.returncode, 0)
        self.assertIn("TESTONLY-METHOD is not a core rule", v.stdout)


if __name__ == "__main__":
    unittest.main()
