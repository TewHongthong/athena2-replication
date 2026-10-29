"""Smoke tests for Athena Sim.  Run:  python -m unittest discover -s tests -v   (from the athena-sim folder)

No API key and no network are needed: the OpenAI / Gemini code paths are exercised against a tiny fake HTTP server
running on localhost.  The public5 tests are skipped when athena-corpus cannot be found.
"""
from __future__ import annotations

import http.server
import io
import json
import os
import re
import sys
import tempfile
import threading
import unittest
from contextlib import redirect_stdout, redirect_stderr

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

import athena_sim  # noqa: E402
from athena.evaluate import apply_rename, parse_completion, sim_char  # noqa: E402
from athena.llm import autofix_name, is_reasoning_model  # noqa: E402
from athena.packs import load_pack  # noqa: E402
from athena.report import load_trials, mcnemar_p, wilson  # noqa: E402
from output_validator import check_naming_compliance  # noqa: E402


def cli(*argv):
    out, err = io.StringIO(), io.StringIO()
    with redirect_stdout(out), redirect_stderr(err):
        rc = athena_sim.main(list(argv))
    return rc, out.getvalue(), err.getvalue()


def count_lines(path):
    with open(path, encoding="utf-8") as f:
        return sum(1 for _ in f)


# --------------------------------------------------------------------------------------- fake LLM server
class FakeLLM(http.server.BaseHTTPRequestHandler):
    requests: list = []
    fail_first = 0            # answer this many requests with HTTP 429 first

    def log_message(self, *a):  # silence
        pass

    def do_POST(self):
        body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        FakeLLM.requests.append({"path": self.path, "body": body, "headers": dict(self.headers)})
        if FakeLLM.fail_first > 0:
            FakeLLM.fail_first -= 1
            self.send_response(429)
            self.send_header("Retry-After", "0")
            self.end_headers()
            self.wfile.write(b'{"error":"slow down"}')
            return
        if "/chat/completions" in self.path:
            prompt = body["messages"][0]["content"]
            resp = {"model": body["model"], "usage": {"prompt_tokens": 111, "completion_tokens": 22},
                    "choices": [{"finish_reason": "stop", "message": {"content": self.answer(prompt)}}]}
        else:
            prompt = body["contents"][0]["parts"][0]["text"]
            resp = {"usageMetadata": {"promptTokenCount": 50, "candidatesTokenCount": 10, "thoughtsTokenCount": 5},
                    "candidates": [{"finishReason": "STOP", "content": {"parts": [{"text": self.answer(prompt)}]}}]}
        raw = json.dumps(resp).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    @staticmethod
    def answer(prompt):
        m = re.search(r'"original_name": "([^"]+)"', prompt)
        if m:   # rename task: append a marker so the answer is never an exact match
            data = {"original_name": m.group(1), "suggested_name": m.group(1) + "_x", "rule_ids_applied": [],
                    "reasoning": "fake"}
        else:
            data = {"comment": "/* Function Objective: x\nInput parameters : x\nFunction description: x\n"
                               "Return Value : x\nCreated By : x\nCreate Date: x\nRevised By:\nRevised Date:\n*/",
                    "format": "block", "rule_ids_applied": [], "reasoning": "fake"}
        return "<think>hidden</think>Reasoning: fake.\nFINAL ANSWER:\n```json\n" + json.dumps(data) + "\n```"


class Server:
    def __enter__(self):
        FakeLLM.requests, FakeLLM.fail_first = [], 0
        self.httpd = http.server.ThreadingHTTPServer(("127.0.0.1", 0), FakeLLM)
        self.url = f"http://127.0.0.1:{self.httpd.server_address[1]}"
        threading.Thread(target=self.httpd.serve_forever, daemon=True).start()
        return self

    def __exit__(self, *a):
        self.httpd.shutdown()
        self.httpd.server_close()


# --------------------------------------------------------------------------------------- unit tests
class Helpers(unittest.TestCase):
    def test_apply_rename_word_boundaries(self):
        code = "int foo = foo_bar + foo; // foo\nfoo2 = $foo;"
        new, n = apply_rename(code, "foo", "i_foo")
        self.assertEqual(n, 3)
        self.assertIn("foo_bar", new)
        self.assertIn("foo2", new)
        self.assertIn("$foo", new)

    def test_parse_completion_variants(self):
        good = 'Reasoning: r\nFINAL ANSWER:\n```json\n{"original_name":"a","suggested_name":"b","rule_ids_applied":[],"reasoning":"r"}\n```'
        self.assertTrue(parse_completion("rename", good).ok)
        self.assertTrue(parse_completion("rename", "<think>x</think>" + good).ok)
        self.assertFalse(parse_completion("rename", "I would call it b").ok)
        self.assertFalse(parse_completion("rename", "").ok)

    def test_stats(self):
        lo, hi = wilson(0, 10)
        self.assertEqual(lo, 0.0)
        self.assertGreater(hi, 0.2)
        self.assertAlmostEqual(mcnemar_p(0, 0), 1.0)
        self.assertLess(mcnemar_p(12, 1), 0.01)
        self.assertEqual(sim_char("abc", "abc"), 1.0)

    def test_reasoning_model_detection(self):
        for m in ("o3-mini", "o1", "o4-mini", "gpt-5", "openai/gpt-5-mini"):
            self.assertTrue(is_reasoning_model(m), m)
        for m in ("gpt-4o", "gpt-4.1", "llama-3", "qwen3-coder"):
            self.assertFalse(is_reasoning_model(m), m)


class GscsPack(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.pack = load_pack("gscs", None)

    def test_counts(self):
        self.assertEqual(len(self.pack.comment_units()), 18)
        self.assertGreaterEqual(len(self.pack.rename_units()), 150)

    def test_split_is_per_snippet_and_stable(self):
        units = self.pack.rename_units()
        by_snip = {}
        for u in units:
            by_snip.setdefault(u.snippet_id, set()).add(u.split)
        self.assertTrue(all(len(v) == 1 and v <= {"dev", "test"} for v in by_snip.values()))
        dev = {k for k, v in by_snip.items() if v == {"dev"}}
        self.assertEqual(dev, {f"gscs_{l}_{n}" for l in ("java", "python", "cpp") for n in ("003", "006")})
        self.assertEqual({u.split for u in self.pack.comment_units() if u.snippet_id in dev}, {"dev"})
        from athena.packs import split_of
        self.assertEqual(split_of("csharp_005"), split_of("csharp_005"))
        share = sum(split_of(f"x_{i}") == "dev" for i in range(2000)) / 2000
        self.assertTrue(0.25 < share < 0.35, share)

    def test_every_violation_is_real_and_fixable(self):
        """original name passes the checker, injected name fails it, and the oracle answer is accepted."""
        for u in self.pack.rename_units():
            rules = [self.pack.ontology.rule(rid) for rid in self.pack.core_rules(u.language, u.kind)]
            self.assertTrue(rules, u.unit_id)
            bad = [r["id"] for r in rules if not check_naming_compliance(u.injected, r)[0]]
            self.assertTrue(bad, f"{u.unit_id}: injected name {u.injected} passes all core rules")
            good = [r["id"] for r in rules if not check_naming_compliance(u.original, r)[0]]
            self.assertFalse(good, f"{u.unit_id}: original name {u.original} fails {good}")
            self.assertIn(u.injected, u.code_violation)
            self.assertIn(u.original, u.code_original)
            self.assertNotRegex(u.code_violation, r"(?<![\w$])" + re.escape(u.original) + r"(?![\w$])")

    def test_autofix_cannot_infer_type_prefix(self):
        r = self.pack.ontology.rule("GSCS-VAR-TYPED-PREFIX")
        self.assertFalse(check_naming_compliance(autofix_name("gpax", r), r)[0])

    def test_prompt_conditions_differ(self):
        prompts = {}
        for c in ("none", "fulldoc", "chunk", "graph"):
            rc, out, _ = cli("show", "--pack", "gscs", "--condition", c)
            self.assertEqual(rc, 0)
            prompts[c] = out
        uid = re.match(r"# unit (\S+)", prompts["graph"]).group(1)
        u = next(x for x in self.pack.rename_units() if x.unit_id == uid)
        self.assertEqual(len(set(prompts.values())), 4)
        self.assertNotIn("GSCS-VAR-TYPED-PREFIX", prompts["none"])
        self.assertIn("GSCS-", prompts["graph"])
        self.assertNotIn("(?!", prompts["graph"], "hidden regexes must not leak into the prompt")
        self.assertGreater(len(prompts["fulldoc"]), len(prompts["graph"]))
        self.assertIn(u.injected, prompts["graph"])
        self.assertNotIn(u.original, prompts["graph"].split("CODE")[-1].replace(u.injected, ""))


class TestSplitGuard(unittest.TestCase):
    """dev by default; the test split needs a freeze for real models and is only run once per freeze."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        os.environ["OPENAI_API_KEY"] = "sk-test"
        self.frozen = os.path.join(self.tmp.name, "frozen.json")

    def opts(self, url, **over):
        o = ["--pack", "gscs", "--backend", "openai:gpt-4o", "--base-url", url + "/v1", "--limit", "3",
             "--conditions", "graph", "--out", self.tmp.name, "--progress", "100000"]
        for k, v in over.items():
            o += [k, v]
        return o

    def test_default_is_dev_and_mock_may_use_test(self):
        rc, out, _ = cli("run", "--pack", "gscs", "--backend", "mock:oracle", "--limit", "5", "--out", self.tmp.name,
                         "--run-id", "d", "--progress", "100000")
        self.assertEqual(rc, 0)
        recs = load_trials([os.path.join(self.tmp.name, "d")])[0]
        self.assertEqual({r["split"] for r in recs}, {"dev"})
        rc, *_ = cli("run", "--pack", "gscs", "--backend", "mock:oracle", "--limit", "5", "--split", "test",
                     "--out", self.tmp.name, "--run-id", "t", "--progress", "100000")
        self.assertEqual(rc, 0)          # mocks carry no tuning risk

    def test_real_model_on_test_needs_freeze_and_runs_once(self):
        with Server() as s:
            # 1. no freeze -> refused, and nothing was sent to the model
            rc, out, err = cli("run", *self.opts(s.url), "--split", "test", "--run-id", "a")
            self.assertEqual(rc, 2)
            self.assertIn("frozen", err)
            self.assertEqual(len(FakeLLM.requests), 0)
            rc, out, err = cli("run", *self.opts(s.url), "--split", "all", "--run-id", "a")
            self.assertEqual(rc, 2)
            # 2. freeze, then run once
            rc, out, err = cli("freeze", *self.opts(s.url)[:-4], "--out-file", self.frozen, "--note", "unit test")
            self.assertEqual(rc, 0, out + err)
            rc, out, err = cli("run", *self.opts(s.url), "--split", "test", "--frozen", self.frozen, "--run-id", "a")
            self.assertEqual(rc, 0, out + err)
            self.assertEqual(len(FakeLLM.requests), 3)
            recs = load_trials([os.path.join(self.tmp.name, "a")])[0]
            self.assertEqual({r["split"] for r in recs}, {"test"})
            # 3. same run id = resume (allowed, nothing left to do); a new run id = refused
            rc, *_ = cli("run", *self.opts(s.url), "--split", "test", "--frozen", self.frozen, "--run-id", "a")
            self.assertEqual(rc, 0)
            self.assertEqual(len(FakeLLM.requests), 3)
            rc, out, err = cli("run", *self.opts(s.url), "--split", "test", "--frozen", self.frozen, "--run-id", "b")
            self.assertEqual(rc, 2)
            self.assertIn("already run", err)
            self.assertEqual(len(FakeLLM.requests), 3)
            # 4. an explicit rerun goes through and is flagged in the report
            rc, out, err = cli("run", *self.opts(s.url), "--split", "test", "--frozen", self.frozen, "--run-id", "b",
                               "--allow-rerun")
            self.assertEqual(rc, 0, out + err)
            with open(os.path.join(self.tmp.name, "b", "summary.md"), encoding="utf-8") as f:
                self.assertIn("RERUN", f.read())
            with open(self.frozen + ".ledger.jsonl", encoding="utf-8") as f:
                events = [json.loads(l) for l in f]
            self.assertEqual([e["event"] for e in events], ["start", "end"] * 3)         # a, a (resume), b
            self.assertEqual([e["run_id"] for e in events][::2], ["a", "a", "b"])
            self.assertEqual([bool(e["rerun"]) for e in events if e["event"] == "start"], [False, False, True])

    def test_changing_anything_after_freeze_is_refused(self):
        with Server() as s:
            rc, *_ = cli("freeze", *self.opts(s.url)[:-4], "--out-file", self.frozen)
            self.assertEqual(rc, 0)
            rc, out, err = cli("run", *self.opts(s.url, **{"--examples": "1"}), "--split", "test", "--frozen",
                               self.frozen, "--run-id", "c")
            self.assertEqual(rc, 2)
            self.assertIn("examples", err)
            self.assertEqual(len(FakeLLM.requests), 0)


class Report(unittest.TestCase):
    def test_paired_table_counts_units_not_repeats(self):
        with tempfile.TemporaryDirectory() as d:
            rc, *_ = cli("run", "--pack", "gscs", "--backend", "mock:autofix", "--limit", "8", "--repeats", "3",
                         "--conditions", "none,graph", "--out", d, "--run-id", "r", "--progress", "100000")
            self.assertEqual(rc, 0)
            with open(os.path.join(d, "r", "summary.md"), encoding="utf-8") as f:
                md = f.read()
        self.assertIn("exact two-sided sign test", md)
        self.assertIn("| mock:autofix | graph vs none | core_ok | 8 |", md)
        self.assertIn("Split: dev.", md)

    def test_holm(self):
        from athena.report import holm
        self.assertEqual(holm([0.01, 0.04, 0.03]), [0.03, 0.06, 0.06])


class EndToEnd(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)

    def run_cli(self, *extra, rid="r"):
        rc, out, err = cli("run", "--pack", "gscs", "--out", self.tmp.name, "--run-id", rid, "--progress", "100000", *extra)
        self.assertEqual(rc, 0, out + err)
        return os.path.join(self.tmp.name, rid)

    def test_mock_oracle_resume_and_report(self):
        d = self.run_cli("--backend", "mock:oracle", "--limit", "10", "--conditions", "none,graph")
        for f in ("config.json", "trials.jsonl", "trials.csv", "summary.md"):
            self.assertTrue(os.path.exists(os.path.join(d, f)), f)
        recs = load_trials([d])[0]
        self.assertEqual(len(recs), 20)
        self.assertTrue(all(r["metrics"]["exact_match"] for r in recs))
        n_before = count_lines(os.path.join(d, "trials.jsonl"))
        d2 = self.run_cli("--backend", "mock:oracle", "--limit", "10", "--conditions", "none,graph")   # resume
        self.assertEqual(d, d2)
        self.assertEqual(n_before, count_lines(os.path.join(d, "trials.jsonl")))
        rc, out, _ = cli("report", d)
        self.assertEqual(rc, 0)
        self.assertIn("mock", out)

    def test_repeats_are_separate_trials(self):
        d = self.run_cli("--backend", "mock:echo", "--limit", "4", "--conditions", "none", "--repeats", "3", rid="rep")
        self.assertEqual(len(load_trials([d])[0]), 12)

    def test_export_prompts_and_replay_roundtrip(self):
        """prompts --export -> fill 'response' by hand (here: the true answer) -> run --backend replay:<file>."""
        p = os.path.join(self.tmp.name, "prompts.jsonl")
        rc, out, err = cli("prompts", "--pack", "gscs", "--limit", "3", "--conditions", "none,graph", "--export", p)
        self.assertEqual(rc, 0, out + err)
        with open(p, encoding="utf-8") as f:
            rows = [json.loads(l) for l in f]
        self.assertEqual(len(rows), 6)
        pack = load_pack("gscs", None)
        units = {u.unit_id: u for u in pack.rename_units()}
        for r in rows:
            u = units[r["unit_id"]]
            ans = {"original_name": u.injected, "suggested_name": u.original, "rule_ids_applied": [], "reasoning": "pasted"}
            r["response"] = "Reasoning: pasted.\nFINAL ANSWER:\n" + json.dumps(ans)
        with open(p, "w", encoding="utf-8") as f:
            f.write("\n".join(json.dumps(r) for r in rows) + "\n")
        d = self.run_cli("--backend", "replay:" + p, "--limit", "3", "--conditions", "none,graph", rid="rp")
        recs = load_trials([d])[0]
        self.assertEqual(len(recs), 6)
        self.assertTrue(all(r["metrics"]["exact_match"] for r in recs))

    def test_openai_reasoning_model_request_shape_and_retry(self):
        os.environ["OPENAI_API_KEY"] = "sk-test"
        with Server() as s:
            FakeLLM.fail_first = 1
            d = self.run_cli("--backend", "openai:o3-mini", "--base-url", s.url + "/v1", "--limit", "2",
                             "--conditions", "graph", "--reasoning-effort", "low", "--max-tokens", "1234",
                             "--price-in", "1.1", "--price-out", "4.4", rid="oa")
        reqs = FakeLLM.requests
        self.assertEqual(len(reqs), 3)                       # 1 x 429, then 2 successful calls
        body = reqs[-1]["body"]
        self.assertEqual(body["model"], "o3-mini")
        self.assertEqual(body["max_completion_tokens"], 1234)
        self.assertEqual(body["reasoning_effort"], "low")
        self.assertNotIn("temperature", body)
        self.assertNotIn("max_tokens", body)
        self.assertEqual({k.lower(): v for k, v in reqs[-1]["headers"].items()}["authorization"], "Bearer sk-test")
        self.assertTrue(reqs[-1]["path"].endswith("/v1/chat/completions"))
        recs = load_trials([d])[0]
        self.assertEqual(len(recs), 2)
        self.assertEqual(recs[0]["prompt_tokens"], 111)
        self.assertTrue(recs[0]["metrics"]["parse_ok"])
        self.assertFalse(recs[0]["metrics"]["exact_match"])
        self.assertGreater(recs[0]["cost_usd"], 0)

    def test_openai_classic_model_uses_temperature(self):
        os.environ["OPENAI_API_KEY"] = "sk-test"
        with Server() as s:
            self.run_cli("--backend", "openai:gpt-4o", "--base-url", s.url + "/v1", "--limit", "1",
                         "--conditions", "none", "--temperature", "0", rid="oa2")
        body = FakeLLM.requests[-1]["body"]
        self.assertEqual(body["temperature"], 0.0)
        self.assertIn("max_tokens", body)
        self.assertNotIn("max_completion_tokens", body)

    def test_gemini_path(self):
        os.environ["GEMINI_API_KEY"] = "g-test"
        os.environ["GEMINI_BASE_URL"] = ""
        with Server() as s:
            os.environ["GEMINI_BASE_URL"] = s.url + "/v1beta"
            try:
                d = self.run_cli("--task", "comment", "--backend", "gemini:gemini-2.5-flash", "--limit", "2",
                                 "--conditions", "graph", rid="gm")
            finally:
                os.environ.pop("GEMINI_BASE_URL", None)
        r = FakeLLM.requests[-1]
        self.assertIn(":generateContent", r["path"])
        self.assertEqual({k.lower(): v for k, v in r["headers"].items()}.get("x-goog-api-key"), "g-test")
        recs = load_trials([d])[0]
        self.assertEqual(len(recs), 2)
        self.assertEqual(recs[0]["completion_tokens"], 15)
        self.assertTrue(recs[0]["metrics"]["comment_ok"])

    def test_abort_after_consecutive_errors(self):
        os.environ["OPENAI_API_KEY"] = "sk-test"
        rc, out, err = cli("run", "--pack", "gscs", "--out", self.tmp.name, "--run-id", "dead", "--progress", "100000",
                           "--backend", "openai:gpt-4o", "--base-url", "http://127.0.0.1:9/v1", "--retries", "0",
                           "--limit", "6", "--conditions", "none", "--max-errors", "3")
        self.assertNotEqual(rc, 0)
        self.assertIn("consecutive", out + err)


@unittest.skipUnless(os.path.isdir(os.path.join(os.environ.get("ATHENA_CORPUS", os.path.join(ROOT, "..", "athena-corpus")), "benchmark")),
                     "athena-corpus/benchmark not found (set ATHENA_CORPUS)")
class Public5(unittest.TestCase):
    def test_pack_loads_and_graph_hits_expected_rule(self):
        pack = load_pack("public5", None)
        units = pack.rename_units()
        self.assertGreater(len(units), 100)
        u = units[0]
        core = pack.core_rules(u.language, u.kind)
        self.assertTrue(core)
        d = tempfile.mkdtemp()
        rc, out, err = cli("run", "--pack", "public5", "--backend", "mock:oracle", "--per-language", "3", "--out", d,
                           "--run-id", "p5", "--progress", "100000")
        self.assertEqual(rc, 0, out + err)
        recs = load_trials([os.path.join(d, "p5")])[0]
        graph = [r for r in recs if r["condition"] == "graph"]
        self.assertTrue(graph and all(r["metrics"]["core_ok"] for r in graph))


if __name__ == "__main__":
    unittest.main()
