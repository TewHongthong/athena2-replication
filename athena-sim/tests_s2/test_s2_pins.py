#!/usr/bin/env python3
"""The Study 2 pin file (models/model_pins_s2.json) and its use by athena2_s2.py.

  python3 -m unittest discover -s tests_s2       (from the athena-sim folder)
"""
import copy
import json
import os
import subprocess
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
SIM = os.path.dirname(HERE)
sys.path.insert(0, SIM)
sys.path.insert(0, HERE)

from athena.pins import entry_sha256, load_pins  # noqa: E402

STUDY1 = os.path.join(SIM, "..", "models", "model_pins.json")
STUDY2 = os.path.join(SIM, "..", "models", "model_pins_s2.json")


class TestPinFile(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.p1, cls.p2 = load_pins(STUDY1), load_pins(STUDY2)

    def test_panel(self):
        self.assertEqual(list(self.p2["models"]), ["luna", "gemini31fl", "qwen35_9b_s2", "gemma4_local_s2"])
        self.assertEqual(self.p2["schema"], self.p1["schema"])

    def test_hosted_pins_and_embeddings_are_those_of_study1(self):
        for k in ("luna", "gemini31fl"):
            self.assertEqual(entry_sha256(self.p2["models"][k]), entry_sha256(self.p1["models"][k]), k)
        self.assertEqual({k: entry_sha256(v) for k, v in self.p2["embeddings"].items()},
                         {k: entry_sha256(v) for k, v in self.p1["embeddings"].items()})

    def test_local_pins_differ_only_in_the_output_limit(self):
        for base in ("qwen35_9b", "gemma4_local"):
            e = copy.deepcopy(self.p2["models"][base + "_s2"])
            self.assertEqual(e["request"]["max_tokens"], 8192)
            self.assertEqual(e.pop("study2"), {"base_pin": base, "change": "request.max_tokens %d -> 8192"
                                               % self.p1["models"][base]["request"]["max_tokens"]})
            e["request"]["max_tokens"] = self.p1["models"][base]["request"]["max_tokens"]
            self.assertEqual(e, self.p1["models"][base])
            self.assertGreaterEqual(e["identity"]["server_context"], 8192 + 8192)

    def test_study1_pin_file_unchanged(self):
        self.assertEqual(set(self.p1["models"]), {"luna", "luna_draft", "gemini31fl", "deepseek41f", "gemma4",
                                                  "gemma4_local", "mistral_large4", "qwen35_9b"})


class TestDefaultPinFile(unittest.TestCase):
    def test_freeze_with_a_study2_pin(self):
        import tempfile
        import shutil
        from test_s2_harness import write_bench
        tmp = tempfile.mkdtemp(prefix="athena_s2_pins_")
        try:
            write_bench(tmp)
            env = dict(os.environ, ATHENA_S2_BENCH=tmp, ATHENA_SIM_CACHE=os.path.join(tmp, ".cache"))
            out = os.path.join(tmp, "frozen.json")
            r = subprocess.run([sys.executable, os.path.join(SIM, "athena2_s2.py"), "freeze", "--pack", "godot-s2",
                                "--model-pin", "qwen35_9b_s2", "--conditions", "none", "--per-language", "0",
                                "--out-file", out], capture_output=True, text=True, env=env, cwd=SIM)
            self.assertEqual(r.returncode, 0, r.stderr)
            with open(out, encoding="utf-8") as f:
                s = json.load(f)["settings"]
            p2 = load_pins(STUDY2)["models"]["qwen35_9b_s2"]
            self.assertEqual((s["model_pin"], s["model_pin_sha256"], s["max_tokens"], s["backend"]),
                             ("qwen35_9b_s2", entry_sha256(p2), 8192, p2["request"]["backend"]))
        finally:
            shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
