"""Tests for draft_ontology.py (the LLM draft of an ontology).  No network and no API key: a fake backend answers.
Run:  python -m unittest discover -s tests -p "test_draft_ontology.py" -v   (from the athena-sim folder)
"""
from __future__ import annotations

import json
import os
import shutil
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

import draft_ontology as D  # noqa: E402
from athena import llm, pins  # noqa: E402


def good(std="godot"):
    s = D.SUBJECTS[std]
    sid, lid = s["standard_id"], s["language_id"]
    return {
        "directed": True, "multigraph": False, "graph": {},
        "nodes": [
            {"id": sid, "type": "Standard", "name": "n", "publisher": "p", "url": "u", "retrievedDate": "d", "scopeLanguages": [lid]},
            {"id": lid, "type": "Language", "name": s["language_name"], "fileExtensions": [".x"], "defaultStandardId": sid},
            {"id": "method", "type": "IdentifierKind", "name": "Method", "applicableLanguages": [lid]},
            {"id": sid + "-METHOD-CASE", "type": "NamingRule", "casing": "snake_case", "prefix": None, "suffix": None,
             "minLength": None, "maxLength": None, "forbiddenPatterns": [], "description": "d", "rationale": None,
             "severity": "MUST", "sourceStandardId": sid, "sourceSection": "Naming"},
        ],
        "links": [
            {"source": sid + "-METHOD-CASE", "target": lid, "relation": "APPLIES_TO"},
            {"source": sid + "-METHOD-CASE", "target": "method", "relation": "APPLIES_TO"},
            {"source": sid + "-METHOD-CASE", "target": sid, "relation": "DEFINED_IN"},
        ],
    }


class Fake(llm.Backend):
    spec = "fake:x"

    def __init__(self, text, finish="stop"):
        self.text, self.finish, self.calls = text, finish, 0

    def complete(self, prompt, ctx):
        self.calls += 1
        return llm.Completion(self.text, 100, 50, 0.1, "fake-model", self.finish, "gen-1", "FakeProvider", "fp")


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self._freeze, self._out = D.FREEZE, D.out_dir
        D.FREEZE = os.path.join(self.tmp.name, "freeze.json")
        D.out_dir = lambda std: os.path.join(self.tmp.name, "packs", std, "llm")

    def tearDown(self):
        D.FREEZE, D.out_dir = self._freeze, self._out
        self.tmp.cleanup()

    def freeze(self):
        with open(D.FREEZE, "w", encoding="utf-8") as f:
            json.dump(D.freeze_record(), f)


class TestPrompt(Base):
    def test_all_standards_build_without_leftover_placeholders(self):
        for std in D.SUBJECTS:
            p = D.build_prompt(std)
            sid = D.SUBJECTS[std]["standard_id"]
            self.assertIn(f'"id": "{sid}", "type": "Standard"', p)
            for ph in ("<STANDARD_ID>", "<STANDARD_NAME>", "<PUBLISHER>", "<URL>", "<RETRIEVED_DATE>", "<LANGUAGE_ID>",
                       "<LANGUAGE_NAME>", "<EXTENSIONS>"):
                self.assertNotIn(ph, p)

    def test_document_text_is_inserted_unchanged(self):
        e = D.load_standard_entry("godot")
        text = D.read_document("godot", e)
        self.assertIn(text, D.build_prompt("godot"))

    def test_prompt_is_deterministic(self):
        self.assertEqual(D.build_prompt("odoo"), D.build_prompt("odoo"))

    def test_prompt_does_not_mention_the_human_ontology(self):
        for std in D.SUBJECTS:
            p = D.build_prompt(std).lower()
            self.assertNotIn("human ontology", p)

    def test_document_hash_mismatch_is_refused(self):
        src = tempfile.TemporaryDirectory()
        try:
            e = D.load_standard_entry("godot")
            name = os.path.basename(e["doc_path"])
            os.makedirs(os.path.join(src.name, "godot"))
            with open(os.path.join(src.name, "godot", name), "w", encoding="utf-8") as f:
                f.write("altered")
            old = D.SRC_DIR
            D.SRC_DIR = src.name
            try:
                with self.assertRaises(D.DraftError):
                    D.build_prompt("godot")
            finally:
                D.SRC_DIR = old
        finally:
            src.cleanup()


class TestFreeze(Base):
    def test_run_needs_a_freeze(self):
        with self.assertRaises(D.DraftError):
            D.run("godot", backend=Fake("{}"), use_graph_loader=False)

    def test_template_change_after_freeze_is_refused(self):
        self.freeze()
        old = D.TEMPLATE
        alt = os.path.join(self.tmp.name, "t.md")
        shutil.copy(old, alt)
        with open(alt, "a", encoding="utf-8") as f:
            f.write("\nextra line")
        D.TEMPLATE = alt
        try:
            with self.assertRaises(D.DraftError):
                D.run("godot", backend=Fake("{}"), use_graph_loader=False)
        finally:
            D.TEMPLATE = old

    def test_pin_change_after_freeze_is_refused(self):
        self.freeze()
        d = pins.load_pins()
        d["models"]["luna_draft"]["request"]["max_tokens"] = 1
        alt = os.path.join(self.tmp.name, "pins.json")
        with open(alt, "w", encoding="utf-8") as f:
            json.dump(d, f)
        with self.assertRaises(D.DraftError):
            D.run("godot", pins_path=alt, backend=Fake("{}"), use_graph_loader=False)

    def test_pin_differs_from_luna_only_in_max_tokens(self):
        m = pins.load_pins()["models"]
        a, b = json.loads(json.dumps(m["luna"])), json.loads(json.dumps(m["luna_draft"]))
        self.assertEqual(b["request"].pop("max_tokens"), 32768)
        a["request"].pop("max_tokens")
        for k in ("panel_name", "drafting_note"):
            a.pop(k, None)
            b.pop(k, None)
        self.assertEqual(a, b)


class TestRun(Base):
    def test_accepted_draft_is_stored_unedited(self):
        self.freeze()
        text = json.dumps(good(), indent=1)
        r = D.run("godot", backend=Fake(text), use_graph_loader=False)
        odir = D.out_dir("godot")
        self.assertTrue(r["check"]["accepted"], r["check"])
        self.assertEqual(open(os.path.join(odir, "response.txt"), encoding="utf-8").read(), text)
        self.assertEqual(json.load(open(os.path.join(odir, "llm_ontology.json"), encoding="utf-8")), good())
        meta = json.load(open(os.path.join(odir, "meta.json"), encoding="utf-8"))
        self.assertEqual(meta["response_id"], "gen-1")
        self.assertEqual(meta["prompt_sha256"], D.freeze_record()["prompt_sha256"]["godot"])
        self.assertEqual(r["check"]["checks"]["harness_reader"], "ok")
        self.assertEqual(r["check"]["checks"]["curation_reader"], "ok")
        self.assertEqual(r["check"]["checks"]["n_rules"], 1)
        self.assertEqual(r["check"]["schema_findings"], [])

    def test_second_pass_is_refused(self):
        self.freeze()
        b = Fake(json.dumps(good()))
        D.run("godot", backend=b, use_graph_loader=False)
        with self.assertRaises(D.DraftError):
            D.run("godot", backend=b, use_graph_loader=False)
        self.assertEqual(b.calls, 1)

    def test_one_code_fence_is_removed_and_nothing_else(self):
        self.freeze()
        body = json.dumps(good())
        r = D.run("godot", backend=Fake("```json\n" + body + "\n```\n"), use_graph_loader=False)
        self.assertTrue(r["check"]["accepted"])
        self.assertEqual(D.strip_fence("```json\n{}\n```"), "{}")
        self.assertEqual(D.strip_fence("{}"), "{}")

    def test_text_around_the_json_is_rejected_not_repaired(self):
        self.freeze()
        r = D.run("godot", backend=Fake("Here is the ontology:\n" + json.dumps(good())), use_graph_loader=False)
        self.assertFalse(r["check"]["accepted"])
        self.assertFalse(os.path.exists(os.path.join(D.out_dir("godot"), "llm_ontology.json")))
        self.assertTrue(os.path.exists(os.path.join(D.out_dir("godot"), "response.txt")))

    def test_truncated_answer_is_rejected(self):
        self.freeze()
        r = D.run("godot", backend=Fake(json.dumps(good()), finish="length"), use_graph_loader=False)
        self.assertFalse(r["check"]["accepted"])
        self.assertIn("output limit", r["check"]["rejected_because"])

    def test_loader_failure_is_rejected(self):
        self.freeze()
        bad = good()
        del bad["nodes"][1]["id"]                    # a node without an id
        r = D.run("godot", backend=Fake(json.dumps(bad)), use_graph_loader=False)
        self.assertFalse(r["check"]["accepted"])
        self.assertTrue(any(v != "ok" for k, v in r["check"]["checks"].items() if k in ("harness_reader", "curation_reader")))

    def test_schema_findings_do_not_decide_acceptance(self):
        self.freeze()
        d = good()
        d["links"].append({"source": "GODOT-METHOD-CASE", "target": "GODOT", "relation": "HAS_EXAMPLE"})
        d["nodes"][3]["severity"] = "ALWAYS"
        r = D.run("godot", backend=Fake(json.dumps(d)), use_graph_loader=False)
        self.assertTrue(r["check"]["accepted"])
        self.assertGreaterEqual(len(r["check"]["schema_findings"]), 2)

    def test_mock_backend_is_refused(self):
        self.freeze()
        with self.assertRaises(D.DraftError):
            D.run("godot", backend=llm.make_backend("mock:echo"), use_graph_loader=False)

    def test_check_command_repeats_the_checks(self):
        self.freeze()
        D.run("godot", backend=Fake(json.dumps(good())), use_graph_loader=False)
        self.assertEqual(D.main(["check", "--standard", "godot"]), 0)


if __name__ == "__main__":
    unittest.main()
