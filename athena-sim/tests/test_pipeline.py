"""Tests for the pipeline without the Vol. 1 oracles (athena2 v0.1).
Run:  python -m unittest discover -s tests -v   (from the athena-sim folder)

No API key, no network and no corpus are needed: the pack, the ontology and the model answers are built here.
The kind and scope steps run the real curation modules (../athena-corpus/curation); the tests are skipped if those
cannot be loaded on this platform.
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

import athena2  # noqa: E402
from athena import freeze, pipeline, runner  # noqa: E402
from athena.llm import Backend, Completion, MockBackend  # noqa: E402
from athena.ontology import Ontology  # noqa: E402
from athena.packs import Pack, Unit  # noqa: E402
from athena.report import _oracle_free_section  # noqa: E402
from athena.retrieval import Retriever  # noqa: E402

ONTO = {
    "directed": True, "multigraph": False, "graph": {"name": "tiny"},
    "nodes": [
        {"id": "python", "type": "Language"},
        {"id": "variable", "type": "IdentifierKind"}, {"id": "function", "type": "IdentifierKind"},
        {"id": "S", "type": "Standard", "name": "Tiny standard"},
        {"id": "R-VAR", "type": "NamingRule", "severity": "MUST", "casing": "snake_case",
         "description": "Variables use snake_case."},
        {"id": "R-FUN", "type": "NamingRule", "severity": "MUST", "casing": "snake_case",
         "description": "Functions use snake_case."},
    ],
    "links": [
        {"source": "R-VAR", "target": "S", "relation": "DEFINED_IN"},
        {"source": "R-VAR", "target": "python", "relation": "APPLIES_TO"},
        {"source": "R-VAR", "target": "variable", "relation": "APPLIES_TO"},
        {"source": "R-FUN", "target": "S", "relation": "DEFINED_IN"},
        {"source": "R-FUN", "target": "python", "relation": "APPLIES_TO"},
        {"source": "R-FUN", "target": "function", "relation": "APPLIES_TO"},
    ],
}


class TinyPack(Pack):
    id = "tiny"
    title = "test pack"

    def core_rules(self, lang, kind):
        return [r["id"] for r in self.ontology.rules_for(lang, kind)]

    def rename_units(self, languages=None):
        return [UNIT]


CODE_BAD = "def total(items):\n    SumX = 0\n    for it in items:\n        SumX += it\n    return SumX\n"
CODE_OK = CODE_BAD.replace("SumX", "sum_x")
UNIT = Unit(unit_id="u1", snippet_id="s1", language="python", standard_id="S", kind="variable", original="sum_x",
            injected="SumX", rule_id="R-VAR", method="recase", code_original=CODE_OK, code_violation=CODE_BAD,
            split="dev")


class Stub(Backend):
    """A model that always answers with the given text."""
    is_llm = True

    def __init__(self, answer):
        self.spec, self.answer, self.prompts = "stub:test", answer, []

    def describe(self):
        return {"spec": self.spec, "is_llm": True}

    def complete(self, prompt, ctx):
        self.prompts.append(prompt)
        return Completion(self.answer, 10, 5, 0.0, "stub", "stop")


def say(name, orig="SumX"):
    d = {"original_name": orig, "suggested_name": name, "rule_ids_applied": ["R-VAR"], "reasoning": "r"}
    return "Reasoning: x\nFINAL ANSWER:\n```json\n" + json.dumps(d) + "\n```"


def make_pack():
    fd, path = tempfile.mkstemp(suffix=".json")
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        json.dump(ONTO, f)
    try:
        return TinyPack(Ontology(path))
    finally:
        os.remove(path)


def setUpModule():
    try:
        pipeline._load()
    except pipeline.PipelineError as e:
        raise unittest.SkipTest(str(e))


class TestSteps(unittest.TestCase):
    def test_kind_comes_from_the_code(self):
        self.assertEqual(pipeline.infer("python", CODE_BAD, "SumX")["kind"], "variable")
        self.assertEqual(pipeline.infer("python", "def MyFunc():\n    return 1\n", "MyFunc")["kind"], "function")

    def test_unknown_kind_falls_back_to_a_neutral_word(self):
        inf = pipeline.infer("python", CODE_BAD, "Missing")
        self.assertIsNone(inf["kind"])
        self.assertEqual(pipeline.kind_for_prompt(inf), pipeline.UNKNOWN_KIND)
        self.assertEqual(pipeline.infer("fortran", "x", "x")["status"], "error")

    def test_scope_verdicts(self):
        s = pipeline.scope("python", CODE_BAD, "SumX", "sum_x")
        self.assertEqual(s["verdict"], "ok")
        s = pipeline.scope("python", CODE_BAD, "SumX", "items")
        self.assertEqual(s["verdict"], "conflict")
        self.assertTrue(s["reasons"])
        self.assertEqual(pipeline.scope("python", CODE_BAD, "SumX", "SumX"), {"verdict": "no_change"})
        self.assertIsNone(pipeline.scope("python", CODE_BAD, "SumX", "not valid"))
        self.assertEqual(pipeline.scope("java", "class A { int Bad; }", "Bad", "bad")["verdict"], "unchecked")

    def test_gscs_cannot_run_without_its_oracle_kind(self):
        class G:
            id = "gscs"
        with self.assertRaises(pipeline.PipelineError):
            pipeline.check_pack(G())


class TestProposal(unittest.TestCase):
    def propose(self, answer, code=CODE_BAD, name="SumX", condition="graph", pack=None):
        pack = pack or make_pack()
        backend = Stub(answer)
        p = pipeline.propose_rename(pack, Retriever(pack), backend, language="python", code=code, name=name,
                                    condition=condition)
        return p, backend

    def test_accepted(self):
        p, _ = self.propose(say("sum_x"))
        self.assertEqual((p.status, p.suggested, p.kind, p.standard_id), ("accepted", "sum_x", "variable", "S"))
        self.assertEqual(p.scope["verdict"], "ok")
        self.assertEqual(p.rules_failed, [])

    def test_inferred_kind_drives_the_retrieved_rules(self):
        p, b = self.propose(say("sum_x"))
        self.assertEqual(p.retrieval["retrieved_ids"], ["R-VAR"])
        self.assertIn("The variable `SumX`", b.prompts[0])
        p, b = self.propose(say("my_func", "MyFunc"), code="def MyFunc():\n    return 1\n", name="MyFunc")
        self.assertEqual(p.retrieval["retrieved_ids"], ["R-FUN"])
        self.assertIn("The function `MyFunc`", b.prompts[0])

    def test_unknown_kind_retrieves_nothing_specific(self):
        code = CODE_BAD + "\nclass Box:\n    pass\n"
        p, b = self.propose(say("box", "Box"), code=code, name="Box")      # a class: the tiny ontology has no class rule
        self.assertEqual(p.retrieval["retrieved_ids"], [])
        self.assertIn("class", b.prompts[0])

    def test_scope_conflict_rejects_a_suggestion_that_follows_the_rules(self):
        p, _ = self.propose(say("items"))
        self.assertEqual(p.status, "rejected")
        self.assertIn("scope check", p.reason)
        self.assertEqual(p.rules_failed, [])

    def test_rule_failure_rejects(self):
        p, _ = self.propose(say("SumY"))
        self.assertEqual(p.status, "rejected")
        self.assertEqual(p.rules_failed, ["R-VAR"])

    def test_no_proposal_and_no_change(self):
        self.assertEqual(self.propose("I cannot help with that.")[0].status, "no_proposal")
        self.assertEqual(self.propose(say("not an identifier"))[0].status, "no_proposal")
        self.assertEqual(self.propose(say("SumX"))[0].status, "no_change")

    def test_unchecked_when_the_scope_checker_does_not_cover_the_language(self):
        pack = make_pack()
        pack.ontology._applies["R-VAR"]["lang"].add("java")        # pretend the standard also covers java
        p = pipeline.propose_rename(pack, Retriever(pack), Stub(say("sum_x")), language="java",
                                    code="class A { void f() { int SumX = 0; } }", name="SumX", standard_id="S")
        self.assertEqual(p.status, "unchecked")

    def test_mock_and_replay_backends_are_refused(self):
        pack = make_pack()
        with self.assertRaises(pipeline.PipelineError):
            pipeline.propose_rename(pack, Retriever(pack), MockBackend("oracle"), language="python", code=CODE_BAD,
                                    name="SumX")

    def test_name_must_be_in_the_code(self):
        with self.assertRaises(pipeline.PipelineError):
            self.propose(say("x"), name="Nope")

    def test_standard_for(self):
        self.assertEqual(pipeline.standard_for(make_pack(), "python"), "S")
        with self.assertRaises(pipeline.PipelineError):
            pipeline.standard_for(make_pack(), "cpp")


class TestVol2Packs(unittest.TestCase):
    """--no-oracle accepts the Vol. 2 packs and records whether the inferred kind is a kind of the pack."""

    def pack(self, pack_id):
        p = make_pack()
        p.id = pack_id
        return p

    def test_vol2_packs_are_accepted_and_gscs_is_not(self):
        for pid in ("godot", "dotnet-runtime", "odoo"):
            pipeline.check_pack(self.pack(pid))
        with self.assertRaises(pipeline.PipelineError) as cm:
            pipeline.check_pack(self.pack("gscs"))
        self.assertIn("godot", str(cm.exception))

    def test_trial_records_kind_in_pack(self):
        pack = self.pack("odoo")
        rec = runner.run_trial(pack, Retriever(pack), MockBackend("oracle"), "rename", UNIT, "graph", 0, "r", None,
                               None, True, True)
        self.assertIsNone(rec["error"])
        self.assertIs(rec["kind_in_pack"], True)
        pack.ontology.kinds.remove("variable")
        _, fields = runner.oracle_free_kind("rename", UNIT, pack)
        self.assertIs(fields["kind_in_pack"], False)
        md = "\n".join(_oracle_free_section([rec]))
        self.assertIn("kind outside pack", md)

    def test_public5_trials_have_no_kind_in_pack(self):
        pack = make_pack()
        pack.id = "public5"
        _, fields = runner.oracle_free_kind("rename", UNIT, pack)
        self.assertNotIn("kind_in_pack", fields)


class TestRunner(unittest.TestCase):
    def trial(self, no_oracle):
        pack = make_pack()
        return runner.run_trial(pack, Retriever(pack), MockBackend("oracle"), "rename", UNIT, "graph", 0, "r", None,
                                None, True, no_oracle)

    def test_no_oracle_trial_records_the_inferred_kind_and_the_scope_verdict(self):
        rec = self.trial(True)
        self.assertIsNone(rec["error"])
        self.assertEqual((rec["kind_used"], rec["kind_inferred"], rec["kind_ok"]), ("variable", "variable", True))
        self.assertEqual(rec["scope"]["verdict"], "ok")
        self.assertTrue(rec["metrics"]["exact_match"])
        md = "\n".join(_oracle_free_section([rec]))
        self.assertIn("No-oracle diagnostics", md)
        self.assertIn("| graph | 1 | 100.0% |", md)

    def test_the_default_trial_is_unchanged(self):
        rec = self.trial(False)
        self.assertFalse({"kind_used", "kind_inferred", "kind_status", "scope"} & set(rec))
        self.assertEqual(_oracle_free_section([rec]), [])

    def test_the_prompt_is_the_same_when_the_inferred_kind_equals_the_benchmark_kind(self):
        a, b = self.trial(True), self.trial(False)
        self.assertEqual(a["prompt"], b["prompt"])


class TestFreeze(unittest.TestCase):
    def args(self, **kw):
        ns = type("A", (), {})()
        for k, v in dict(pack="tiny", task="rename", conditions="graph", languages=None, per_language=1, limit=0,
                         seed=1, top_k=None, chunk_k=3, examples=2, backend="mock:echo", temperature=0.2,
                         max_tokens=None, reasoning_effort=None, repeats=1).items():
            setattr(ns, k, v)
        for k, v in kw.items():
            setattr(ns, k, v)
        return ns

    def test_no_oracle_is_part_of_the_freeze_only_when_used(self):
        pack = make_pack()
        plain = freeze.fingerprint(self.args(), pack)
        self.assertNotIn("no_oracle", plain["settings"])
        self.assertNotIn("curation_sha256", plain)
        used = freeze.fingerprint(self.args(no_oracle=True), pack)
        self.assertTrue(used["settings"]["no_oracle"])
        self.assertEqual(len(used["curation_sha256"]["ALL"]), 64)
        self.assertIsNotNone(used["curation_sha256"]["kind_infer.py"])


class TestCli(unittest.TestCase):
    def run_cli(self, *argv):
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            rc = athena2.main(list(argv))
        return rc, out.getvalue(), err.getvalue()

    def test_version(self):
        with self.assertRaises(SystemExit):
            with redirect_stdout(io.StringIO()):
                athena2.main(["--version"])

    def test_experiment_commands_run_without_the_oracle_and_refuse_gscs(self):
        rc, _, err = self.run_cli("run", "--pack", "gscs", "--backend", "mock:echo", "--limit", "1")
        self.assertEqual(rc, 2)
        self.assertIn("--no-oracle", err)

    def test_packs_is_delegated(self):
        rc, out, _ = self.run_cli("packs")
        self.assertEqual(rc, 0)
        self.assertIn("gscs", out)

    def test_rename_needs_a_model(self):
        rc, _, err = self.run_cli("rename", "--language", "python", "--code", CODE_BAD, "--name", "SumX")
        self.assertEqual(rc, 2)
        self.assertIn("--backend or --model-pin", err)


if __name__ == "__main__":
    unittest.main()
