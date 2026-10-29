"""Tests for the Task RQ2 comment-unit pipeline.

- Extraction (make_comment_units.py in athena-corpus/curation): tiny fixtures for each of the
  five languages, exercised directly against the extraction functions. Skipped if athena-corpus
  or its compiled tree-sitter library is not available -- this suite must still run standalone.
- expected_elements / signature-aware grading: athena.evaluate.grade_comment and n_checks_for,
  using small fake rules so this does not depend on the ontology file.
- Loader: athena.packs.BenchmarkDir / Public5Pack wiring expectedElements through to CommentUnit
  (skipped if athena-corpus is not available, same guard the existing Public5 tests use).
"""
from __future__ import annotations

import os
import sys
import types
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from athena.evaluate import grade_comment, n_checks_for  # noqa: E402
from athena.packs import CommentUnit, load_pack  # noqa: E402
from output_validator import ParsedOutput  # noqa: E402

CORPUS = os.environ.get("ATHENA_CORPUS", os.path.join(ROOT, "..", "athena-corpus"))
CURATION = os.path.join(CORPUS, "curation")


def _load_make_comment_units():
    if not os.path.isdir(CURATION):
        return None
    sys.path.insert(0, CURATION)
    try:
        import make_comment_units as M
        from tsbind import TreeSitter, find_library
        M.TS = TreeSitter(find_library(None))
        return M
    except Exception:  # noqa: BLE001 - genuinely optional in this environment
        return None


M = _load_make_comment_units()


def fake_pack(rules):
    """A minimal pack-like object exposing only what grade_comment needs."""
    ontology = types.SimpleNamespace(rules_for=lambda lang, kind, types=(): rules)
    return types.SimpleNamespace(ontology=ontology)


def fake_unit(language="java", kind="method", expected_elements=None, reference_comment="Do the thing."):
    return CommentUnit(unit_id="u1", snippet_id="s1", language=language, standard_id="X", kind=kind,
                      name="foo", code_bare="void foo() {}", reference_comment=reference_comment,
                      expected_elements=expected_elements)


JAVADOC_METHOD_RULE = {"id": "R-METHOD", "severity": "MUST", "format": "javadoc",
                       "requiredElements": ["summary", "params", "returns", "throws"]}


class ExpectedElementsGrading(unittest.TestCase):
    def _parsed(self, comment):
        return ParsedOutput(ok=True, data={"comment": comment}, raw="")

    def test_void_method_not_penalized_for_missing_return_or_throws(self):
        comment = "/** Does the thing.\n * @param x the value\n */"
        unit = fake_unit(expected_elements=["summary", "params"])
        m = grade_comment(unit, self._parsed(comment), fake_pack([JAVADOC_METHOD_RULE]))
        self.assertTrue(m["comment_ok"], m["failed_rules"])

    def test_same_comment_fails_without_expected_elements_filtering(self):
        comment = "/** Does the thing.\n * @param x the value\n */"
        unit = fake_unit(expected_elements=None)   # legacy / gscs behaviour: unchanged
        m = grade_comment(unit, self._parsed(comment), fake_pack([JAVADOC_METHOD_RULE]))
        self.assertFalse(m["comment_ok"])
        self.assertIn("R-METHOD", m["failed_rules"])

    def test_returns_and_throws_still_required_when_expected(self):
        comment = "/** Does the thing.\n * @param x the value\n */"
        unit = fake_unit(expected_elements=["summary", "params", "returns", "throws"])
        m = grade_comment(unit, self._parsed(comment), fake_pack([JAVADOC_METHOD_RULE]))
        self.assertFalse(m["comment_ok"])

    def test_n_checks_counts_delimiter_and_recognizable_tags_only(self):
        unit_expected = ["summary", "params"]
        n = n_checks_for([JAVADOC_METHOD_RULE], unit_expected)
        # delimiter (javadoc) + params tag; summary has no tag hint, returns/throws filtered out
        self.assertEqual(n, 2)

    def test_n_checks_zero_for_vacuous_rule(self):
        vacuous = {"id": "PEP8-DOC-FUNC", "severity": "MUST", "format": "plain-line-comment",
                  "requiredElements": ["one-line summary"]}
        self.assertEqual(n_checks_for([vacuous], None), 0)

    def test_missing_comment_still_reports_n_checks(self):
        unit = fake_unit(expected_elements=["summary", "params"])
        m = grade_comment(unit, ParsedOutput(ok=False, data=None, raw=""), fake_pack([JAVADOC_METHOD_RULE]))
        self.assertFalse(m["comment_ok"])
        self.assertEqual(m["n_checks"], 2)


@unittest.skipUnless(M is not None, "athena-corpus/curation or its tree-sitter library is not available")
class ExtractionFixtures(unittest.TestCase):
    def test_python_docstring_and_signature(self):
        code = (
            "def add(a, b):\n"
            "    \"\"\"Add two numbers together and return the sum.\"\"\"\n"
            "    if a < 0:\n"
            "        raise ValueError('negative')\n"
            "    return a + b\n"
        )
        text, reason = M.python_docstring(code)
        self.assertIsNone(reason)
        self.assertIn("Add two numbers", text)
        import ast
        node = ast.parse(code).body[0]
        sig = M.python_signature(node, "function")
        self.assertEqual(sig, {"params": 2, "returns": True, "throws": True})

    def test_python_method_ignores_self(self):
        code = (
            "def bump(self, n):\n"
            "    \"\"\"Increase the internal counter by n.\"\"\"\n"
            "    self.count += n\n"
        )
        import ast
        node = ast.parse(code).body[0]
        sig = M.python_signature(node, "method")
        self.assertEqual(sig["params"], 1)
        self.assertFalse(sig["returns"])

    def test_python_rejects_short_docstring(self):
        code = "def f(x):\n    \"\"\"ok\"\"\"\n    return x\n"
        text, reason = M.python_docstring(code)
        self.assertIsNone(text)
        self.assertEqual(reason, "comment_too_short")

    def test_python_rejects_empty_body_after_removal(self):
        code = "def f():\n    \"\"\"This function intentionally does absolutely nothing at all.\"\"\"\n"
        text, reason = M.python_docstring(code)
        self.assertIsNone(text)
        self.assertEqual(reason, "empty_body_after_removal")

    def test_java_leading_javadoc_with_annotation_between(self):
        lines = [
            "class C {",
            "    /**",
            "     * Computes the checksum of the given payload.",
            "     */",
            "    @Override",
            "    public int checksum(byte[] payload) {",
            "        if (payload == null) throw new IllegalArgumentException();",
            "        return payload.length;",
            "    }",
            "}",
        ]
        text, reason = M.leading_comment(lines, 5, "java")
        self.assertIsNone(reason)
        self.assertTrue(text.strip().startswith("/**"))
        sig = M.ts_signature("java", "method", "\n".join(lines[5:9]), "C.java", M.TS)
        self.assertEqual(sig, {"params": 1, "returns": True, "throws": True})

    def test_java_ordinary_comment_rejected(self):
        lines = ["class C {", "    // just a note", "    void m() {}", "}"]
        text, reason = M.leading_comment(lines, 2, "java")
        self.assertIsNone(text)
        self.assertEqual(reason, "ordinary_comment")

    def test_csharp_contiguous_triple_slash(self):
        lines = [
            "class C {",
            "    /// <summary>",
            "    /// Adapts the underlying stream for reading.",
            "    /// </summary>",
            "    public int Read() { return 0; }",
            "}",
        ]
        text, reason = M.leading_comment(lines, 4, "csharp")
        self.assertIsNone(reason)
        self.assertIn("<summary>", text)
        sig = M.ts_signature("csharp", "method", lines[4], "C.cs", M.TS)
        self.assertEqual(sig["returns"], True)

    def test_csharp_void_and_task_are_not_returns(self):
        code_void = "public void Save() { }"
        code_task = "public Task Save() { return Task.CompletedTask; }"
        self.assertFalse(M.ts_signature("csharp", "method", code_void, "C.cs", M.TS)["returns"])
        self.assertFalse(M.ts_signature("csharp", "method", code_task, "C.cs", M.TS)["returns"])

    def test_typescript_jsdoc_function(self):
        lines = [
            "/**",
            " * Formats a duration in seconds as a human-readable string.",
            " */",
            "export function formatDuration(seconds: number): string {",
            "    return seconds + 's';",
            "}",
        ]
        text, reason = M.leading_comment(lines, 3, "typescript")
        self.assertIsNone(reason)
        sig = M.ts_signature("typescript", "function", "\n".join(lines[3:6]), "d.ts", M.TS)
        self.assertEqual(sig, {"params": 1, "returns": True, "throws": False})

    def test_javascript_no_mechanical_delimiter_marker_is_still_extracted(self):
        lines = [
            "/**",
            " * Clamps a value between a minimum and a maximum bound.",
            " */",
            "function clamp(x, lo, hi) {",
            "    if (x < lo) return lo;",
            "    return x;",
            "}",
        ]
        text, reason = M.leading_comment(lines, 3, "javascript")
        self.assertIsNone(reason)
        sig = M.ts_signature("javascript", "function", "\n".join(lines[3:7]), "d.js", M.TS)
        self.assertEqual(sig, {"params": 3, "returns": True, "throws": False})


@unittest.skipUnless(os.path.isdir(os.path.join(CORPUS, "benchmark")),
                     "athena-corpus/benchmark not found (set ATHENA_CORPUS)")
class Loader(unittest.TestCase):
    def test_public5_comment_units_carry_expected_elements(self):
        pack = load_pack("public5", None)
        units = pack.comment_units()
        self.assertGreater(len(units), 50)
        by_kind = {u.kind for u in units}
        self.assertTrue(by_kind <= {"function", "method", "class"})
        classes = [u for u in units if u.kind == "class"]
        self.assertTrue(classes)
        for u in classes:
            self.assertEqual(u.expected_elements, ["summary"])
        non_class = [u for u in units if u.kind != "class" and u.expected_elements is not None]
        self.assertTrue(non_class)
        for u in non_class:
            self.assertIn("summary", u.expected_elements)

    def test_fingerprint_includes_comment_units_index_hash(self):
        pack = load_pack("public5", None)
        fp = pack.fingerprint()
        self.assertIn("comment_units_index_sha256", fp)
        self.assertTrue(fp["comment_units_index_sha256"])


if __name__ == "__main__":
    unittest.main()
