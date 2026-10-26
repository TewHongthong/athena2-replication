"""Tests for model pins and the request options of pinned hosted models.
Run:  python -m unittest discover -s tests -v   (from the athena-sim folder)

No API key and no network are needed: a fake OpenAI-compatible server runs on localhost.
"""
from __future__ import annotations

import http.server
import io
import json
import os
import sys
import tempfile
import threading
import unittest
from contextlib import redirect_stderr, redirect_stdout

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

import athena_sim  # noqa: E402
from athena import freeze  # noqa: E402
from athena.pins import DEFAULT_PINS, entry_sha256, load_pins  # noqa: E402

ANSWER = ('FINAL ANSWER:\n```json\n{"original_name": "a", "suggested_name": "b", "rule_ids_applied": [], '
          '"reasoning": "x"}\n```')


class Fake(http.server.BaseHTTPRequestHandler):
    bodies: list = []
    send_meta = True

    def log_message(self, *a):
        pass

    def do_POST(self):
        body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        Fake.bodies.append(body)
        resp = {"model": body["model"], "usage": {"prompt_tokens": 10, "completion_tokens": 5},
                "choices": [{"finish_reason": "stop", "message": {"content": ANSWER}}]}
        if Fake.send_meta:
            resp.update(id=f"gen-{len(Fake.bodies)}", provider="FakeProvider", system_fingerprint="fp_1")
        raw = json.dumps(resp).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)


class Server:
    def __enter__(self):
        Fake.bodies, Fake.send_meta = [], True
        self.httpd = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Fake)
        self.url = f"http://127.0.0.1:{self.httpd.server_address[1]}/v1"
        threading.Thread(target=self.httpd.serve_forever, daemon=True).start()
        return self

    def __exit__(self, *a):
        self.httpd.shutdown()
        self.httpd.server_close()


def cli(*argv):
    out, err = io.StringIO(), io.StringIO()
    with redirect_stdout(out), redirect_stderr(err):
        rc = athena_sim.main(list(argv))
    return rc, out.getvalue(), err.getvalue()


def trials(run_dir):
    with open(os.path.join(run_dir, "trials.jsonl"), encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()

    def tearDown(self):
        self.tmp.cleanup()

    def run_cli(self, *extra, rid="r", cmd="run"):
        return cli(cmd, "--pack", "gscs", "--out", self.tmp.name, "--run-id", rid, "--progress", "100000",
                   "--limit", "2", "--conditions", "none", *extra)

    def write_pins(self, url, **request_overrides):
        request = {"backend": "openai:vendor/model-x", "base_url": url, "omit_temperature": True, "max_tokens": 321,
                   "extra_body": {"provider": {"order": ["fakeprovider"], "allow_fallbacks": False,
                                               "require_parameters": True}, "reasoning": {"effort": "medium"}},
                   "price_in": 1.0, "price_out": 2.0}
        request.update(request_overrides)
        pins = {"schema": "athena2-model-pins/1", "models": {
            "fake": {"panel_name": "Fake", "status": "pinned", "request": request},
            "local": {"panel_name": "Local", "status": "incomplete", "missing": "file hash",
                      "request": {"backend": "openai:local", "base_url": url}}}}
        path = os.path.join(self.tmp.name, "pins.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(pins, f)
        return path, pins


class TestRequestOptions(Base):
    def test_options_shape_the_request_and_the_record(self):
        with Server() as s:
            rc, out, err = self.run_cli("--backend", "openai:vendor/model-x", "--base-url", s.url, "--omit-temperature",
                                        "--no-think", "--extra-body", '{"provider": {"order": ["p"], "allow_fallbacks": false}}')
            self.assertEqual(rc, 0, out + err)
        body = Fake.bodies[-1]
        self.assertNotIn("temperature", body)
        self.assertEqual(body["chat_template_kwargs"], {"enable_thinking": False})
        self.assertEqual(body["provider"], {"order": ["p"], "allow_fallbacks": False})
        recs = trials(os.path.join(self.tmp.name, "r"))
        self.assertTrue(recs and all(r["provider"] == "FakeProvider" and r["system_fingerprint"] == "fp_1"
                                     and r["response_id"].startswith("gen-") for r in recs))
        with open(os.path.join(self.tmp.name, "r", "config.json"), encoding="utf-8") as f:
            backend = json.load(f)["backend"]
        self.assertTrue(backend["omit_temperature"] and backend["no_think"])
        self.assertIsNone(backend["temperature"])
        self.assertEqual(backend["extra_body"]["provider"]["order"], ["p"])

    def test_default_request_is_unchanged(self):
        with Server() as s:
            Fake.send_meta = False
            rc, out, err = self.run_cli("--backend", "openai:gpt-4o", "--base-url", s.url, "--temperature", "0.3")
            self.assertEqual(rc, 0, out + err)
        body = Fake.bodies[-1]
        self.assertEqual(set(body), {"model", "messages", "max_tokens", "temperature"})
        self.assertEqual(body["temperature"], 0.3)
        recs = trials(os.path.join(self.tmp.name, "r"))
        self.assertTrue(all("provider" not in r and "response_id" not in r for r in recs))
        with open(os.path.join(self.tmp.name, "r", "config.json"), encoding="utf-8") as f:
            backend = json.load(f)["backend"]
        self.assertFalse({"omit_temperature", "no_think", "extra_body"} & set(backend))

    def test_settings_without_new_options_keep_the_earlier_keys(self):
        class A:
            pass
        a = A()
        for k in freeze.SETTING_KEYS:
            setattr(a, k, None)
        a.conditions, a.omit_temperature, a.extra_body, a.no_think = "none", False, None, False
        self.assertEqual(set(freeze.settings_of(a)), set(freeze.SETTING_KEYS) | {"split"})


class TestModelPin(Base):
    def test_pin_expands_into_the_request(self):
        with Server() as s:
            path, pins = self.write_pins(s.url)
            rc, out, err = self.run_cli("--model-pin", "fake", "--pins", path)
            self.assertEqual(rc, 0, out + err)
        body = Fake.bodies[-1]
        self.assertEqual(body["model"], "vendor/model-x")
        self.assertNotIn("temperature", body)
        self.assertEqual(body["max_tokens"], 321)
        self.assertEqual(body["provider"]["order"], ["fakeprovider"])
        self.assertEqual(body["reasoning"], {"effort": "medium"})
        with open(os.path.join(self.tmp.name, "r", "config.json"), encoding="utf-8") as f:
            cfg = json.load(f)
        self.assertEqual(cfg["args"]["model_pin_sha256"], entry_sha256(pins["models"]["fake"]))
        self.assertEqual(cfg["args"]["price_in"], 1.0)

    def test_freeze_records_the_pin_and_refuses_a_changed_one(self):
        with Server() as s:
            path, _ = self.write_pins(s.url)
            frozen = os.path.join(self.tmp.name, "frozen.json")
            rc, out, err = cli("freeze", "--pack", "gscs", "--limit", "2", "--conditions", "none",
                               "--model-pin", "fake", "--pins", path, "--out-file", frozen)
            self.assertEqual(rc, 0, out + err)
            with open(frozen, encoding="utf-8") as f:
                settings = json.load(f)["settings"]
            self.assertEqual(settings["model_pin"], "fake")
            self.assertTrue(settings["omit_temperature"])
            self.assertIsNone(settings["temperature"])
            self.assertEqual(settings["backend"], "openai:vendor/model-x")
            rc, out, err = self.run_cli("--model-pin", "fake", "--pins", path, "--split", "test", "--frozen", frozen,
                                        rid="t1")
            self.assertEqual(rc, 0, out + err)
            self.write_pins(s.url, max_tokens=999)
            rc, out, err = self.run_cli("--model-pin", "fake", "--pins", path, "--split", "test", "--frozen", frozen,
                                        rid="t2")
            self.assertEqual(rc, 2)
            self.assertIn("model_pin_sha256", err)

    def test_errors(self):
        with Server() as s:
            path, _ = self.write_pins(s.url)
            cases = [
                ("--backend", "openai:x", "--model-pin", "fake", "--pins", path),
                ("--model-pin", "nope", "--pins", path),
                ("--model-pin", "local", "--pins", path),
                ("--backend", "openai:x", "--base-url", s.url, "--extra-body", "{not json"),
                ("--backend", "openai:x", "--base-url", s.url, "--extra-body", "[1, 2]"),
                ("--backend", "gemini:x", "--omit-temperature"),
                (),
            ]
            for i, extra in enumerate(cases):
                rc, out, err = self.run_cli(*extra, rid=f"e{i}")
                self.assertEqual(rc, 2, f"{extra}: {out}{err}")


class TestShippedPins(unittest.TestCase):
    def test_pin_file(self):
        pins = load_pins(DEFAULT_PINS)["models"]
        self.assertEqual(set(pins), {"luna", "luna_draft", "gemini31fl", "deepseek41f", "gemma4", "gemma4_local", "mistral_large4", "qwen35_9b"})
        for name, e in pins.items():
            req = e["request"]
            self.assertTrue(req["backend"].startswith("openai:"), name)
            self.assertTrue(e.get("sources"), name)
            self.assertFalse(req.get("omit_temperature") and "temperature" in req, name)
            if "openrouter.ai" in req.get("base_url", ""):
                prov = req["extra_body"]["provider"]
                self.assertEqual(len(prov["order"]), 1, name)
                self.assertIs(prov["allow_fallbacks"], False, name)
                self.assertIs(prov["require_parameters"], True, name)
                self.assertEqual(e["status"], "pinned", name)
        qwen = pins["qwen35_9b"]
        self.assertEqual(qwen["status"], "pinned")
        self.assertTrue(qwen["request"]["no_think"])
        self.assertNotIn("base_url", qwen["request"])          # local endpoint comes from $OPENAI_BASE_URL
        self.assertEqual(qwen["identity"]["gguf_sha256_local"], qwen["identity"]["gguf_sha256_listed"])
        self.assertIn(qwen["identity"]["server_alias"], qwen["request"]["backend"])
        gemma = pins["gemma4_local"]
        self.assertTrue(gemma["request"]["no_think"])
        self.assertNotIn("base_url", gemma["request"])         # local endpoint comes from $OPENAI_BASE_URL
        self.assertEqual(gemma["identity"]["gguf_sha256_local"], gemma["identity"]["gguf_sha256_listed"])
        self.assertIn(gemma["identity"]["server_alias"], gemma["request"]["backend"])
        self.assertTrue(all(e["status"] == "pinned" for e in pins.values()))


if __name__ == "__main__":
    unittest.main()
