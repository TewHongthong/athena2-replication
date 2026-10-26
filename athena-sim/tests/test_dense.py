"""Tests for the dense retrieval condition and its embedding pin.
Run:  python -m unittest discover -s tests -v   (from the athena-sim folder)

No model and no network are needed: a fake OpenAI-compatible embedding server runs on localhost and returns hashed
bag-of-words vectors, so related texts are close and the tests can predict the ranking.
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
import zlib
from contextlib import redirect_stderr, redirect_stdout

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

import athena_sim  # noqa: E402
from athena import embed, freeze  # noqa: E402
from athena.packs import load_pack  # noqa: E402
from athena.pins import DEFAULT_PINS, load_pins  # noqa: E402
from athena.retrieval import CONDITIONS, DEFAULT_CONDITIONS, Retriever, retrieval_query  # noqa: E402

DIM = 64
ENTRY = {"panel_name": "fake", "status": "pinned",
         "request": {"model": "fake-embed", "query_template": "Instruct: find the passage\nQuery:{query}",
                     "document_template": "{text}", "batch": 2},
         "identity": {"note": "test"}}


def vec(text: str) -> list:
    v = [0.0] * DIM
    for w in re.findall(r"[a-z0-9]+", text.lower()):
        v[zlib.crc32(w.encode()) % DIM] += 1.0
    return v


class Fake(http.server.BaseHTTPRequestHandler):
    bodies: list = []
    fail_with = None

    def log_message(self, *a):
        pass

    def do_POST(self):
        body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        Fake.bodies.append((self.path, body))
        if Fake.fail_with:
            self.send_response(Fake.fail_with)
            self.end_headers()
            self.wfile.write(b"no")
            return
        data = [{"index": i, "embedding": vec(t)} for i, t in reversed(list(enumerate(body["input"])))]  # out of order
        raw = json.dumps({"data": data}).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)


class WithServer(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.srv = http.server.HTTPServer(("127.0.0.1", 0), Fake)
        cls.url = f"http://127.0.0.1:{cls.srv.server_port}/v1"
        threading.Thread(target=cls.srv.serve_forever, daemon=True).start()

    @classmethod
    def tearDownClass(cls):
        cls.srv.shutdown()

    def setUp(self):
        Fake.bodies, Fake.fail_with = [], None
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.env = {k: os.environ.get(k) for k in (embed.ENV_BASE_URL, embed.ENV_CACHE)}
        os.environ[embed.ENV_BASE_URL] = self.url
        os.environ[embed.ENV_CACHE] = os.path.join(self.tmp.name, "cache")
        self.addCleanup(self.restore)

    def restore(self):
        for k, v in self.env.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v

    def emb(self, **kw):
        return embed.Embedder("fake", ENTRY, **kw)

    def pins_file(self, entry=ENTRY):
        path = os.path.join(self.tmp.name, "pins.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump({"schema": "x", "models": {}, "embeddings": {"fake": entry}}, f)
        return path


class TestEmbedder(WithServer):
    def test_vectors_are_normalised_and_in_order(self):
        e = self.emb()
        vs = e.embed(["alpha beta", "gamma", "alpha beta delta"], "document")
        for v in vs:
            self.assertAlmostEqual(sum(x * x for x in v), 1.0, places=9)
        self.assertGreater(embed._dot(vs[0], vs[2]), embed._dot(vs[0], vs[1]))     # the server answers out of order

    def test_query_gets_the_instruction_and_a_passage_does_not(self):
        e = self.emb()
        e.embed(["some code"], "query")
        e.embed(["some passage"], "document")
        self.assertEqual(Fake.bodies[0][1]["input"], ["Instruct: find the passage\nQuery:some code"])
        self.assertEqual(Fake.bodies[1][1]["input"], ["some passage"])
        self.assertEqual(Fake.bodies[0][0], "/v1/embeddings")
        self.assertEqual(Fake.bodies[0][1]["model"], "fake-embed")

    def test_batching(self):
        self.emb().embed([f"text {i}" for i in range(5)], "document")      # batch = 2
        self.assertEqual([len(b["input"]) for _, b in Fake.bodies], [2, 2, 1])

    def test_a_text_is_embedded_once(self):
        e = self.emb()
        a = e.embed(["x y", "x y", "z"], "document")
        self.assertEqual(sum(len(b["input"]) for _, b in Fake.bodies), 2)       # the duplicate is not sent twice
        self.assertEqual(a[0], a[1])
        e.embed(["x y"], "document")
        self.assertEqual(len(Fake.bodies), 1)                                    # memory cache

    def test_role_is_part_of_the_cache_key(self):
        e = self.emb()
        q, d = e.embed(["same text"], "query")[0], e.embed(["same text"], "document")[0]
        self.assertNotEqual(q, d)

    def test_disk_cache_serves_a_new_embedder_without_a_server(self):
        self.emb().embed(["alpha", "beta"], "document")
        n = len(Fake.bodies)
        del os.environ[embed.ENV_BASE_URL]
        again = self.emb().embed(["alpha", "beta"], "document")
        self.assertEqual(len(Fake.bodies), n)
        self.assertEqual(len(again), 2)
        with self.assertRaises(embed.EmbedError):
            self.emb().embed(["never seen"], "document")                        # not cached and no server address

    def test_cache_is_keyed_by_the_pin(self):
        self.emb().embed(["alpha"], "document")
        other = dict(ENTRY, request=dict(ENTRY["request"], query_template="Q:{query}"))
        e2 = embed.Embedder("fake", other)
        self.assertNotEqual(e2.sha256, self.emb().sha256)
        e2.embed(["alpha"], "document")
        self.assertEqual(len(Fake.bodies), 2)                                    # another pin starts from an empty cache

    def test_server_error_is_reported(self):
        Fake.fail_with = 400
        with self.assertRaises(embed.EmbedError) as cm:
            self.emb(retries=2).embed(["alpha"], "document")
        self.assertIn("400", str(cm.exception))
        self.assertEqual(len(Fake.bodies), 1)                                    # a 4xx is not retried

    def test_incomplete_entry_is_refused(self):
        with self.assertRaises(embed.EmbedError):
            embed.Embedder("fake", dict(ENTRY, status="incomplete", missing="the hash"))

    def test_templates_are_checked(self):
        bad = dict(ENTRY, request=dict(ENTRY["request"], query_template="no placeholder"))
        with self.assertRaises(embed.EmbedError):
            embed.Embedder("fake", bad)


class TestDenseIndex(WithServer):
    CHUNKS = [("a", "variables use snake case names"), ("b", "classes use pascal case"), ("c", "constants are upper case")]

    def test_ranking_and_limit(self):
        idx = embed.DenseIndex(self.CHUNKS, self.emb())
        self.assertEqual(idx.top("classes pascal", 3)[0], 1)
        self.assertEqual(len(idx.top("classes pascal", 2)), 2)
        self.assertEqual(len(idx.top("classes pascal", 10)), 3)      # no zero score to stop at: always min(k, n)

    def test_ties_are_broken_by_position(self):
        idx = embed.DenseIndex([("a", "same words"), ("b", "same words"), ("c", "other")], self.emb())
        self.assertEqual(idx.top("same words", 2), [0, 1])

    def test_deterministic(self):
        idx = embed.DenseIndex(self.CHUNKS, self.emb())
        self.assertEqual(idx.top("constants upper", 3), idx.top("constants upper", 3))

    def test_empty(self):
        self.assertEqual(embed.DenseIndex([], self.emb()).top("anything", 3), [])


class TestDenseCondition(WithServer):
    def test_registered_but_not_a_default(self):
        self.assertIn("dense", CONDITIONS)
        self.assertNotIn("dense", DEFAULT_CONDITIONS)
        self.assertEqual(set(CONDITIONS) - set(DEFAULT_CONDITIONS), {"dense"})

    def test_context_reports_retrieved_ids_and_uses_the_chunk_wording(self):
        pack = load_pack("gscs")
        sid = pack.standard_ids()[0]
        r = Retriever(pack, chunk_k=2, embedder=self.emb())
        ctx = r.context("dense", task="rename", standard_id=sid, language="python", kind="variable",
                        name="MyValue", code="def f():\n    MyValue = 1")
        self.assertEqual(len(ctx.meta["retrieved_ids"]), 2)
        self.assertIn("passage(s) most similar to the code", ctx.text)
        self.assertEqual(ctx.meta["n_items"], 2)

    def test_chunk_and_bm25_are_untouched_by_the_embedder(self):
        pack = load_pack("gscs")
        sid = pack.standard_ids()[0]
        kw = dict(task="rename", standard_id=sid, language="python", kind="variable", name="MyValue",
                  code="def f():\n    MyValue = 1")
        plain, with_emb = Retriever(pack), Retriever(pack, embedder=self.emb())
        for c in ("chunk", "bm25", "graph", "fulldoc", "none"):
            self.assertEqual(plain.context(c, **kw).text, with_emb.context(c, **kw).text)
        self.assertEqual(Fake.bodies, [])

    def test_dense_without_an_embedder_is_an_error(self):
        pack = load_pack("gscs")
        with self.assertRaises(ValueError):
            Retriever(pack).context("dense", task="rename", standard_id=pack.standard_ids()[0], language="python",
                                    kind="variable", name="x", code="x = 1")

    def test_default_conditions_run_without_an_embedding_model(self):
        rc, out, err = cli("show", "--pack", "gscs", "--condition", "graph")
        self.assertEqual(rc, 0, err)

    def test_cli_requires_a_pin_for_dense(self):
        rc, _, err = cli("show", "--pack", "gscs", "--condition", "dense")
        self.assertEqual(rc, 2)
        self.assertIn("--embed-pin", err)

    def test_cli_refuses_an_incomplete_pin(self):
        pins = self.pins_file(dict(ENTRY, status="incomplete", missing="the hash"))
        rc, _, err = cli("show", "--pack", "gscs", "--condition", "dense", "--embed-pin", "fake", "--pins", pins)
        self.assertEqual(rc, 2)
        self.assertIn("incomplete", err)

    def test_cli_show_run_and_freeze(self):
        pins = self.pins_file()
        rc, out, err = cli("show", "--pack", "gscs", "--condition", "dense", "--embed-pin", "fake", "--pins", pins)
        self.assertEqual(rc, 0, err)
        self.assertIn("most similar to the code", out)
        out_dir = os.path.join(self.tmp.name, "runs")
        rc, _, err = cli("run", "--pack", "gscs", "--backend", "mock:oracle", "--limit", "4", "--conditions",
                         "bm25,dense", "--embed-pin", "fake", "--pins", pins, "--out", out_dir, "--run-id", "d",
                         "--progress", "100000")
        self.assertEqual(rc, 0, err)
        from athena.report import load_trials
        recs = load_trials([os.path.join(out_dir, "d")])[0]
        self.assertEqual({r["condition"] for r in recs}, {"bm25", "dense"})
        self.assertEqual(len(recs), 8)
        self.assertTrue(all("retrieved_ids" in r["retrieval"] for r in recs))
        with open(os.path.join(out_dir, "d", "config.json"), encoding="utf-8") as f:
            cfg = json.load(f)
        self.assertEqual(cfg["embedding"]["embed_pin"], "fake")
        frozen = os.path.join(self.tmp.name, "frozen.json")
        rc, _, err = cli("freeze", "--pack", "gscs", "--backend", "mock:oracle", "--limit", "4", "--conditions",
                         "bm25,dense", "--embed-pin", "fake", "--pins", pins, "--out-file", frozen)
        self.assertEqual(rc, 0, err)
        with open(frozen, encoding="utf-8") as f:
            settings = json.load(f)["settings"]
        self.assertEqual(settings["embed_pin"], "fake")
        self.assertEqual(settings["embed_pin_sha256"], self.emb().sha256)

    def test_freeze_without_dense_records_no_embedding_pin(self):
        frozen = os.path.join(self.tmp.name, "frozen.json")
        rc, _, err = cli("freeze", "--pack", "gscs", "--backend", "mock:oracle", "--limit", "4", "--conditions",
                         "none,bm25", "--out-file", frozen)
        self.assertEqual(rc, 0, err)
        with open(frozen, encoding="utf-8") as f:
            settings = json.load(f)["settings"]
        self.assertNotIn("embed_pin", settings)
        self.assertNotIn("embed_pin_sha256", settings)

    def test_embed_check_reports_the_expected_passages(self):
        rc, out, err = cli("embed-check", "--embed-pin", "fake", "--pins", self.pins_file())
        self.assertIn("queries found the expected passage", out)


class TestPinFile(unittest.TestCase):
    def test_the_shipped_entry_is_well_formed(self):
        entry = load_pins(DEFAULT_PINS)["embeddings"]["qwen3_embedding_06b"]
        req = entry["request"]
        self.assertIn("{query}", req["query_template"])
        self.assertEqual(req["document_template"], "{text}")
        self.assertEqual(entry["identity"]["gguf_sha256_listed"],
                         "06507c7b42688469c4e7298b0a1e16deff06caf291cf0a5b278c308249c3e439")
        self.assertIn(entry["status"], ("incomplete", "pinned"))
        if entry["status"] == "pinned":      # once pinned, the local hash must match the listed one
            self.assertEqual(entry["identity"]["gguf_sha256_local"], entry["identity"]["gguf_sha256_listed"])

    def test_an_incomplete_shipped_entry_is_refused(self):
        entry = load_pins(DEFAULT_PINS)["embeddings"]["qwen3_embedding_06b"]
        if entry["status"] == "incomplete":
            with self.assertRaises(embed.EmbedError):
                embed.load_embedder("qwen3_embedding_06b")


def cli(*argv):
    out, err = io.StringIO(), io.StringIO()
    with redirect_stdout(out), redirect_stderr(err):
        rc = athena_sim.main(list(argv))
    return rc, out.getvalue(), err.getvalue()


if __name__ == "__main__":
    unittest.main()
