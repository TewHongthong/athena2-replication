#!/usr/bin/env python3
"""Study 2 harness (athena_s2, athena2_s2.py) on a small hand-made benchmark and on the pinned standard documents.

  python3 -m unittest discover -s tests_s2       (from the athena-sim folder)
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
SIM = os.path.dirname(HERE)
sys.path.insert(0, SIM)

GODOT_ORIG_1 = "void Node3D::set_position(const Vector3 &p_position) {\n\tdata.origin = p_position;\n\tdirty = true;\n}"
GODOT_ORIG_2 = "void Mesh::get_bounds(AABB &r_aabb) const {\n\tr_aabb = aabb;\n}"
DOTNET_ORIG = ("internal sealed class Counter\n{\n    private int _count;\n\n    public void Add(int n)\n    {\n"
               "        _count += n;\n    }\n}")

# pack -> list of (snippet id, split, language, standard, code, original, injected, kind, rule, method)
TASKS = {
    "godot-s2": [
        ("cpp_001", "dev", "cpp", "GODOT", GODOT_ORIG_1, "p_position", "position", "input_parameter",
         "GODOT-PARAM-INPUT-PREFIX", "prefix_strip"),
        ("cpp_002", "test", "cpp", "GODOT", GODOT_ORIG_2, "r_aabb", "p_aabb", "output_parameter",
         "GODOT-PARAM-OUTPUT-PREFIX", "prefix_swap"),
    ],
    "dotnet-runtime-s2": [
        ("csharp_001", "dev", "csharp", "DOTNET", DOTNET_ORIG, "_count", "s_count", "instance_field",
         "DOTNET-FIELD-INSTANCE-PREFIX", "prefix_swap"),
    ],
}
CONDS = "none,fulldoc,naming,chunk,bm25,graph"


def write_bench(root):
    for pack, tasks in TASKS.items():
        b = os.path.join(root, pack, "bench")
        for sid, split, lang, std, code, orig, inj, kind, rule, method in tasks:
            os.makedirs(os.path.join(b, "snippets", lang), exist_ok=True)
            os.makedirs(os.path.join(b, "violations", lang), exist_ok=True)
            snip = {"id": sid, "language": lang, "standardId": std, "codeContext": code, "split": split,
                    "identifiers": [{"name": orig, "kind": kind, "isCompliant": True}],
                    "provenance": {"repo": "fixture/repo", "path": sid + "." + lang}}
            viol = {"snippetId": sid, "language": lang, "originalName": orig, "injectedName": inj,
                    "identifierKind": kind, "violatedRuleId": rule, "injectionMethod": method,
                    "codeContextWithViolation": code.replace(orig, inj), "split": split}
            with open(os.path.join(b, "snippets", lang, sid + ".json"), "w", encoding="utf-8") as f:
                json.dump(snip, f)
            with open(os.path.join(b, "violations", lang, "%s__%s__%s.json" % (sid, orig, rule)), "w",
                      encoding="utf-8") as f:
                json.dump(viol, f)
        for n in ("snippets_index.tsv", "violations_index.tsv", "tasks.tsv"):
            with open(os.path.join(b, n), "w", encoding="utf-8") as f:
                f.write("header\n" + "".join(t[0] + "\n" for t in tasks))


def cli(*args, env=None):
    e = dict(os.environ, **(env or {}))
    return subprocess.run([sys.executable, os.path.join(SIM, "athena2_s2.py"), *args], capture_output=True,
                          text=True, env=e, cwd=SIM)


class _Bench(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.mkdtemp(prefix="athena_s2_test_")
        write_bench(cls.tmp)
        cls.env = {"ATHENA_S2_BENCH": cls.tmp, "ATHENA_SIM_CACHE": os.path.join(cls.tmp, ".cache")}

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmp, ignore_errors=True)


class TestNaming(unittest.TestCase):
    def test_expression_is_that_of_a11(self):
        import analyse_a11
        from athena_s2.retrieval import NAMING_RE
        self.assertEqual((NAMING_RE.pattern, NAMING_RE.flags), (analyse_a11.NAMING_RE.pattern, analyse_a11.NAMING_RE.flags))

    def test_passages_of_the_two_documents(self):
        from athena_s2 import packs, retrieval
        got = {}
        for name in packs.S2_PACKS:
            p = packs.Study2Pack.__new__(packs.Study2Pack)          # the document only; no benchmark needed
            p.standard_doc_id, p._doc = packs.S2_PACKS[name][0], None
            got[name] = [pid for pid, _ in retrieval.naming_passages(packs.Vol2Pack.chunks(p, None))]
        self.assertEqual(got, {"godot-s2": ["p017", "p018", "p019", "p020", "p031"],
                               "dotnet-runtime-s2": ["p004", "p013", "p014", "p021"]})

    def test_conditions(self):
        from athena_s2 import retrieval
        self.assertEqual(retrieval.CONDITIONS, ("none", "fulldoc", "naming", "chunk", "bm25", "dense", "graph"))
        self.assertEqual(retrieval.DEFAULT_CONDITIONS, ("none", "fulldoc", "naming", "chunk", "bm25", "graph"))


class TestIsolation(unittest.TestCase):
    def test_import_changes_nothing_in_study1(self):
        code = ("import sys; sys.path.insert(0, %r)\n"
                "import athena_s2.packs, athena_s2.retrieval, athena_s2.pipeline, athena_s2.freeze\n"
                "import athena_sim, athena.runner as R, athena.freeze as F, athena.pipeline as P\n"
                "print(R.load_pack.__module__, R.Retriever.__module__, R.oracle_free_kind.__module__, R.CONDITIONS,"
                " F.code_hashes.__module__, P.curation_fingerprint.__module__, athena_sim.VOL2_PACKS)") % SIM
        out = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, cwd=SIM)
        self.assertEqual(out.stdout.strip(), "athena.packs athena.retrieval athena.runner "
                         "('none', 'fulldoc', 'chunk', 'bm25', 'dense', 'graph') athena.freeze athena.pipeline "
                         "('godot', 'dotnet-runtime', 'odoo')", out.stderr)

    def test_study1_frozen_files_still_verify(self):
        import glob
        from athena import freeze as F1
        code = F1.code_hashes() if F1.code_hashes.__module__ == "athena.freeze" else None
        if code is None:
            self.skipTest("hooks installed in this process")
        files = sorted(f for f in glob.glob(os.path.join(SIM, "frozen_*.json")) if "-s2_" not in os.path.basename(f))
        self.assertGreater(len(files), 0)
        for f in files:
            with open(f, encoding="utf-8") as fh:
                self.assertEqual(json.load(fh)["code_sha256"], code, f)

    def test_study2_frozen_files_still_verify(self):
        import glob
        from athena_s2 import freeze as F2
        code = F2.code_hashes()
        files = sorted(glob.glob(os.path.join(SIM, "frozen_*-s2_*.json")))
        self.assertGreater(len(files), 0)
        for f in files:
            with open(f, encoding="utf-8") as fh:
                self.assertEqual(json.load(fh)["code_sha256"], code, f)


class TestRetrieverParity(_Bench):
    def test_study1_conditions_unchanged(self):
        from athena.retrieval import Retriever
        from athena_s2.packs import load_pack
        from athena_s2.retrieval import RetrieverS2
        for name in TASKS:
            pack = load_pack(name, os.path.join(self.tmp, name))
            r1, r2 = Retriever(pack), RetrieverS2(pack)
            for u in pack.rename_units():
                for c in ("none", "fulldoc", "chunk", "bm25", "graph"):
                    kw = dict(task="rename", standard_id=u.standard_id, language=u.language, kind=u.kind,
                              name=u.injected, code=u.code_violation)
                    a, b = r1.context(c, **kw), r2.context(c, **kw)
                    self.assertEqual((a.text, a.meta), (b.text, b.meta), (name, c))
                n = r2.context("naming", task="rename", standard_id=u.standard_id, language=u.language, kind=u.kind,
                               name=u.injected, code=u.code_violation)
                self.assertTrue(n.text.startswith(pack.standard_name(u.standard_id) + " - the %d passage(s) of the "
                                                  "standard about naming:\n" % n.meta["n_items"]))


class TestRuns(_Bench):
    def run_cli(self, pack, *extra):
        out_dir = os.path.join(self.tmp, "runs")
        r = cli("run", "--pack", pack, "--backend", "mock:oracle", "--split", "all", "--per-language", "0",
                "--out", out_dir, "--run-id", "%s-%d" % (pack, len(os.listdir(out_dir)) if os.path.isdir(out_dir) else 0),
                *extra, env=self.env)
        self.assertEqual(r.returncode, 0, r.stderr + r.stdout)
        run_dir = sorted((os.path.join(out_dir, d) for d in os.listdir(out_dir)), key=os.path.getmtime)[-1]
        with open(os.path.join(run_dir, "trials.jsonl"), encoding="utf-8") as f:
            trials = [json.loads(l) for l in f if l.strip()]
        with open(os.path.join(run_dir, "config.json"), encoding="utf-8") as f:
            cfg = json.load(f)
        return trials, cfg

    def test_meta_family_oracle(self):
        for pack in TASKS:
            trials, cfg = self.run_cli(pack, "--conditions", CONDS)
            self.assertEqual(len(trials), len(TASKS[pack]) * 6)
            self.assertTrue(all(t["error"] is None and t["metrics"]["core_ok"] is True for t in trials))
            self.assertEqual({t["pack"] for t in trials}, {pack})
            naming = [t for t in trials if t["condition"] == "naming"]
            self.assertTrue(all(t["retrieval"]["n_items"] > 0 and t["retrieval"]["hit"] is None for t in naming))
            self.assertEqual(cfg["pack"]["standard_document_id"], pack[:-3])

    def test_core_ok_is_the_study2_core(self):
        trials, _ = self.run_cli("godot-s2", "--conditions", "none", "--backend", "mock:echo")
        for t in trials:            # the injected name keeps snake_case and fails only the prefix rule
            self.assertFalse(t["metrics"]["core_ok"])
            self.assertEqual(t["metrics"]["core_failed"], [t["rule_id"]])

    def test_infer_family(self):
        trials, cfg = self.run_cli("godot-s2", "--conditions", "graph", "--no-oracle")
        got = {t["unit_id"].split("__")[0]: (t["kind_inferred"], t["kind_inferred_s1"], t["kind_ok"]) for t in trials}
        self.assertEqual(got, {"cpp_001": ("input_parameter", "parameter", True),
                               "cpp_002": ("output_parameter", "parameter", True)})
        self.assertIn("kind_infer_s2.py", cfg["oracle_free"]["curation_sha256"])
        self.assertTrue(cfg["oracle_free"]["pipeline_version"].endswith("+s2"))
        trials, _ = self.run_cli("dotnet-runtime-s2", "--conditions", "graph", "--no-oracle")
        self.assertEqual([(t["kind_inferred"], t["kind_ok"]) for t in trials], [("instance_field", True)])

    def test_pack_required_and_listed(self):
        self.assertEqual(cli("run", "--backend", "mock:oracle", env=self.env).returncode, 2)
        out = cli("packs", env=self.env).stdout
        self.assertIn("godot-s2:", out)
        self.assertIn("rename units: 2 (dev=1 test=1)", out)


class TestFreeze(_Bench):
    def test_freeze_records_study2_and_guards_the_test_split(self):
        frozen = os.path.join(self.tmp, "frozen_test.json")
        replay = os.path.join(self.tmp, "replay.jsonl")
        r = cli("prompts", "--pack", "godot-s2", "--conditions", "graph", "--split", "test", "--per-language", "0",
                "--export", replay, env=self.env)
        self.assertEqual(r.returncode, 0, r.stderr)
        with open(replay, encoding="utf-8") as f:
            rows = [json.loads(l) for l in f]
        with open(replay, "w", encoding="utf-8") as f:
            for row in rows:
                row["response"] = ('FINAL ANSWER:\n```json\n{"original_name": "p_aabb", "suggested_name": "r_aabb", '
                                   '"rule_ids_applied": [], "reasoning": "x"}\n```')
                f.write(json.dumps(row) + "\n")
        common = ["--pack", "godot-s2", "--conditions", "graph", "--per-language", "0", "--backend", "replay:" + replay]
        r = cli("freeze", *common, "--out-file", frozen, env=self.env)
        self.assertEqual(r.returncode, 0, r.stderr)
        with open(frozen, encoding="utf-8") as f:
            fp = json.load(f)
        self.assertIn("athena_s2/freeze.py", fp["code_sha256"])
        self.assertIn("athena2_s2.py", fp["code_sha256"])
        self.assertIn("athena/runner.py", fp["code_sha256"])
        self.assertEqual(fp["harness_s2_version"], "0.1.0")
        self.assertEqual(len(fp["hypotheses_s2_sha256"] or ""), 64)
        out_dir = os.path.join(self.tmp, "frozen_runs")
        r = cli("run", *common, "--split", "test", "--frozen", frozen, "--out", out_dir, "--run-id", "t1", env=self.env)
        self.assertEqual(r.returncode, 0, r.stderr)
        fp["hypotheses_s2_sha256"] = "0" * 64                 # a changed registration must stop the test run
        with open(frozen, "w", encoding="utf-8") as f:
            json.dump(fp, f)
        r = cli("run", *common, "--split", "test", "--frozen", frozen, "--out", out_dir, "--run-id", "t2",
                "--allow-rerun", env=self.env)
        self.assertEqual(r.returncode, 2)
        self.assertIn("hypotheses_s2_sha256", r.stderr)


if __name__ == "__main__":
    unittest.main()
