"""Tests for the HTTP helper: the User-Agent header is not the default Python-urllib agent.
Run:  python -m unittest discover -s tests -v   (from the athena-sim folder)

No API key and no network are needed: a fake server runs on localhost.
"""
from __future__ import annotations

import http.server
import json
import os
import sys
import threading
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from athena import llm  # noqa: E402


class _Handler(http.server.BaseHTTPRequestHandler):
    seen: list = []

    def do_POST(self):
        self.rfile.read(int(self.headers.get("Content-Length", 0)))
        _Handler.seen.append(self.headers.get("User-Agent"))
        body = json.dumps({"ok": True}).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *args):
        pass


class UserAgentTest(unittest.TestCase):
    def setUp(self):
        _Handler.seen = []
        self.server = http.server.HTTPServer(("127.0.0.1", 0), _Handler)
        threading.Thread(target=self.server.serve_forever, daemon=True).start()
        self.url = f"http://127.0.0.1:{self.server.server_port}/v1/chat/completions"
        self.saved = os.environ.pop("ATHENA_USER_AGENT", None)

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        os.environ.pop("ATHENA_USER_AGENT", None)
        if self.saved is not None:
            os.environ["ATHENA_USER_AGENT"] = self.saved

    def test_default_agent_is_not_python_urllib(self):
        llm._post_json(self.url, {"a": 1}, {}, 10.0, 0)
        self.assertEqual(_Handler.seen, [llm.DEFAULT_USER_AGENT])
        self.assertNotIn("urllib", _Handler.seen[0])

    def test_environment_override(self):
        os.environ["ATHENA_USER_AGENT"] = "custom-agent/1"
        llm._post_json(self.url, {"a": 1}, {}, 10.0, 0)
        self.assertEqual(_Handler.seen, ["custom-agent/1"])


if __name__ == "__main__":
    unittest.main()
