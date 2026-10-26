"""Tests for the passages of a standard document and for the Vol. 2 packs (godot, dotnet-runtime, odoo).
Run:  python3 -B -m unittest tests.test_vol2_pack -v   (from the athena-sim folder)

No API key, no network and no corpus are needed: the benchmark folder is written here in the layout of
tools/export_tasks.py; the ontologies, the core tables and the standard documents are those of the repository.
"""
from __future__ import annotations

import io
import json
import os
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

import athena_sim  # noqa: E402
from athena import freeze  # noqa: E402
from athena.packs import BENCH_ROOT_ENV, VOL2_PACKS, load_pack  # noqa: E402
from athena.passages import split_passages  # noqa: E402
from athena.retrieval import Retriever  # noqa: E402

RST = """.. _label:

Title
=====

Intro paragraph
over two lines.

Section
-------

Text before a literal block::

    code line one

    code line two

- first item
  continued
- second item

.. highlight:: python

Later
-----

Last paragraph.
"""

MD = """Setext title
============

First paragraph.

## Part

1. one
2. two

```
fenced

block
```
"""

# one benchmark task per pack: (language, kind, original, injected, violated rule)
TASKS = {"godot": ("cpp", "parameter", "p_value", "pValue", "GODOT-PARAMETER-CASE"),
         "dotnet-runtime": ("csharp", "method", "DoWork", "do_work", "DOTNET-METHOD-CASE"),
         "odoo": ("python", "parameter", "partner_id", "PartnerId", "ODOO-PARAMETER-CASE")}
STANDARD_OF = {"godot": "GODOT", "dotnet-runtime": "DOTNET", "odoo": "ODOO"}


def write_bench(root, pack):
    lang, kind, orig, inj, rule = TASKS[pack]
    for sub in ("snippets", "violations"):
        os.makedirs(os.path.join(root, sub, lang), exist_ok=True)
    code = "int f(int %s) { return %s; }"
    with open(os.path.join(root, "snippets", lang, "t_001.json"), "w", encoding="utf-8") as f:
        json.dump({"snippetId": "t_001", "standardId": STANDARD_OF[pack], "codeContext": code % (orig, orig),
                   "provenance": {"repo": "r", "path": "a/b.cc"}}, f)
    with open(os.path.join(root, "violations", lang, "t_001__%s__%s.json" % (orig, rule)), "w", encoding="utf-8") as f:
        json.dump({"snippetId": "t_001", "identifierKind": kind, "originalName": orig, "injectedName": inj,
                   "violatedRuleId": rule, "injectionMethod": "casing_swap", "split": "test",
                   "codeContextWithViolation": code % (inj, inj)}, f)
    return root


def cli(*argv):
    out, err = io.StringIO(), io.StringIO()
    with redirect_stdout(out), redirect_stderr(err):
        rc = athena_sim.main(list(argv))
    return rc, out.getvalue(), err.getvalue()


class PassageTests(unittest.TestCase):
    def test_rst_headings_lists_literal_blocks_and_noise(self):
        ps = dict(split_passages(RST, "rst"))
        texts = list(ps.values())
        self.assertEqual(texts[0], "Title\n\nIntro paragraph\nover two lines.")
        lit = [t for t in texts if t.startswith("Title > Section\n\nText before")][0]
        self.assertIn("code line one\n\n    code line two", lit)           # the literal block stays with its paragraph
        self.assertIn("Title > Section\n\n- first item\n  continued", texts)  # one passage per list item, continuation kept
        self.assertIn("Title > Section\n\n- second item", texts)
        self.assertFalse(any("highlight" in t or "_label" in t for t in texts))
        self.assertEqual(texts[-1], "Title > Later\n\nLast paragraph.")     # a sibling heading replaces the section

    def test_markdown_setext_atx_lists_and_fences(self):
        texts = [t for _, t in split_passages(MD, "md")]
        self.assertEqual(texts[0], "Setext title\n\nFirst paragraph.")
        self.assertIn("Setext title > Part\n\n1. one", texts)
        self.assertIn("Setext title > Part\n\n2. two", texts)
        self.assertIn("Setext title > Part\n\n```\nfenced\n\nblock\n```", texts)   # a fence is never cut

    def test_ids_are_sequential_and_the_split_is_deterministic(self):
        a = split_passages(RST, "rst")
        self.assertEqual([i for i, _ in a], ["p%03d" % n for n in range(1, len(a) + 1)])
        self.assertEqual(a, split_passages(RST.replace("\n", "\r\n"), "rst"))

    def test_unknown_format(self):
        with self.assertRaises(ValueError):
            split_passages("x", "html")

    def test_the_three_standards_give_passages(self):
        base = os.path.normpath(os.path.join(ROOT, "..", "standards", "src"))
        for std, f, fmt in (("godot", "cpp_usage_guidelines.rst", "rst"), ("dotnet-runtime", "coding-style.md", "md"),
                            ("odoo", "coding_guidelines.rst", "rst")):
            with open(os.path.join(base, std, f), encoding="utf-8") as fh:
                ps = split_passages(fh.read(), fmt)
            self.assertGreater(len(ps), 10, std)
            self.assertLess(max(len(t) for _, t in ps), 5000, std)
            self.assertTrue(all(t.strip() for _, t in ps), std)


class Vol2PackTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.bench = {p: write_bench(os.path.join(self.tmp.name, p), p) for p in VOL2_PACKS}

    def pack(self, name, variant="human"):
        return load_pack(name, self.bench[name], variant)

    def test_units_core_and_standard_text(self):
        for name in VOL2_PACKS:
            pk = self.pack(name)
            lang, kind, orig, inj, rule = TASKS[name]
            (u,) = pk.rename_units()
            self.assertEqual((u.language, u.kind, u.original, u.injected, u.rule_id, u.split),
                             (lang, kind, orig, inj, rule, "test"))
            self.assertEqual(u.file, "r:a/b.cc")
            self.assertIn(rule, pk.core_rules(lang, kind))
            self.assertEqual(pk.core_rules(lang, "no_such_kind"), [])
            self.assertEqual(pk.id, name)
            self.assertGreater(len(pk.fulltext(STANDARD_OF[name])), 5000)
            self.assertGreater(len(pk.chunks(STANDARD_OF[name])), 10)

    def test_the_human_variant_shows_the_rule_of_the_author(self):
        pk = self.pack("godot")
        ctx = Retriever(pk, 3, None, 0).context("graph", task="rename", standard_id="GODOT", language="cpp",
                                                kind="parameter", name="pValue", code="x")
        self.assertIn("GODOT-PARAMETER-CASE", ctx.meta["retrieved_ids"])

    def test_the_llm_variant_shows_the_drafted_rules_and_is_graded_with_the_human_core(self):
        pk = self.pack("godot", "llm")
        ctx = Retriever(pk, 3, None, 0).context("graph", task="rename", standard_id="GODOT", language="cpp",
                                                kind="parameter", name="pValue", code="x")
        self.assertIn("GODOT-OTHER-CASE", ctx.meta["retrieved_ids"])
        self.assertNotIn("GODOT-PARAMETER-CASE", ctx.meta["retrieved_ids"])
        self.assertIn("GODOT-PARAMETER-CASE", pk.core_rules("cpp", "parameter"))     # grading is unchanged
        self.assertIsNot(pk.rules_ontology, pk.ontology)
        self.assertFalse(pk.rules_comparable)
        self.assertTrue(self.pack("godot").rules_comparable)

    def test_the_drafted_ontology_without_a_rule_for_the_kind(self):
        pk = self.pack("odoo", "llm")
        ctx = Retriever(pk, 3, None, 0).context("graph", task="rename", standard_id="ODOO", language="python",
                                                kind="parameter", name="PartnerId", code="x")
        self.assertEqual(ctx.meta["n_items"], 0)
        self.assertIn("holds no specific rule", ctx.text)
        self.assertEqual(self.pack("odoo").rules_ontology.rules_for("python", "parameter", standard_id="ODOO")[0]["id"],
                         "ODOO-PARAMETER-CASE")

    def test_the_other_conditions_do_not_depend_on_the_variant(self):
        for cond in ("none", "fulldoc", "chunk", "bm25"):
            texts = []
            for variant in ("human", "llm"):
                pk = self.pack("dotnet-runtime", variant)
                ctx = Retriever(pk, 3, None, 0).context(cond, task="rename", standard_id="DOTNET", language="csharp",
                                                        kind="method", name="do_work", code="void do_work() {}")
                texts.append(ctx.text)
            self.assertEqual(texts[0], texts[1], cond)

    def test_chunk_retrieval_returns_passages_of_the_document(self):
        pk = self.pack("dotnet-runtime")
        ctx = Retriever(pk, 3, None, 0).context("bm25", task="rename", standard_id="DOTNET", language="csharp",
                                                kind="field", name="x", code="private int _x;")
        self.assertEqual(len(ctx.meta["retrieved_ids"]), 3)
        self.assertTrue(all(i.startswith("p") for i in ctx.meta["retrieved_ids"]))

    def test_fingerprint_separates_the_variants(self):
        h, l = self.pack("godot").fingerprint(), self.pack("godot", "llm").fingerprint()
        self.assertEqual((h["ontology_variant"], l["ontology_variant"]), ("human", "llm"))
        self.assertEqual(h["ontology_sha256"], l["ontology_sha256"])
        self.assertNotEqual(h["rules_ontology_sha256"], l["rules_ontology_sha256"])
        for k in ("core_rules_sha256", "standard_document_sha256"):
            self.assertTrue(h[k])

    def test_errors(self):
        with self.assertRaises(FileNotFoundError):
            load_pack("godot", os.path.join(self.tmp.name, "missing"))
        with self.assertRaises(ValueError):
            load_pack("godot", self.bench["godot"], "robot")
        with self.assertRaises(ValueError):
            load_pack("gscs", None, "llm")
        old = os.environ.get(BENCH_ROOT_ENV)
        os.environ[BENCH_ROOT_ENV] = self.tmp.name
        try:
            self.assertEqual(load_pack("odoo").bench.root, self.bench["odoo"])
        finally:
            if old is None:
                os.environ.pop(BENCH_ROOT_ENV)
            else:
                os.environ[BENCH_ROOT_ENV] = old

    def test_bench_root_accepts_the_pool_layout(self):
        import shutil
        root = os.path.join(self.tmp.name, "pool")
        shutil.copytree(self.bench["odoo"], os.path.join(root, "odoo", "bench"))
        old = os.environ.get(BENCH_ROOT_ENV)
        os.environ[BENCH_ROOT_ENV] = root
        try:
            self.assertEqual(load_pack("odoo").bench.root, os.path.join(root, "odoo", "bench"))
        finally:
            if old is None:
                os.environ.pop(BENCH_ROOT_ENV)
            else:
                os.environ[BENCH_ROOT_ENV] = old

    def test_a_mock_run_records_no_rule_hit_for_the_drafted_ontology(self):
        out = os.path.join(self.tmp.name, "runs")
        rows = {}
        for variant in ("human", "llm"):
            rc, _, err = cli("run", "--pack", "godot", "--corpus", self.bench["godot"], "--ontology-variant", variant,
                             "--backend", "mock:oracle", "--split", "all", "--conditions", "none,graph", "--per-language", "0",
                             "--run-id", variant, "--out", out)
            self.assertEqual(rc, 0, err)
            with open(os.path.join(out, variant, "trials.jsonl"), encoding="utf-8") as f:
                rows[variant] = {json.loads(l)["condition"]: json.loads(l) for l in f}
        self.assertTrue(rows["human"]["graph"]["retrieval"]["hit"])
        self.assertIsNone(rows["llm"]["graph"]["retrieval"]["hit"])
        self.assertEqual(rows["human"]["graph"]["pack"], "godot")
        with open(os.path.join(out, "llm", "config.json"), encoding="utf-8") as f:
            self.assertEqual(json.load(f)["pack"]["ontology_variant"], "llm")


if __name__ == "__main__":
    unittest.main()
