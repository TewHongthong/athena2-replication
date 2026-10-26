"""Tests for the BM25 retrieval condition.  Run:  python -m unittest discover -s tests -v   (from the athena-sim folder)

No API key and no network are needed.
"""
from __future__ import annotations

import io
import math
import os
import re
import sys
import unittest
from contextlib import redirect_stderr, redirect_stdout

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

import athena_sim  # noqa: E402
from athena.packs import load_pack  # noqa: E402
from athena.retrieval import BM25_B, BM25_K1, CONDITIONS, BM25Index, ChunkIndex, Retriever, retrieval_query  # noqa: E402


def cli(*argv):
    out, err = io.StringIO(), io.StringIO()
    with redirect_stdout(out), redirect_stderr(err):
        rc = athena_sim.main(list(argv))
    return rc, out.getvalue(), err.getvalue()


class TestBM25Index(unittest.TestCase):
    CHUNKS = [("a", "apple banana"), ("b", "banana cherry cherry"), ("c", "durian")]

    def test_score_matches_hand_computation(self):
        idx = BM25Index(self.CHUNKS)
        # N = 3, n(apple) = 1, |a| = 2, avgdl = (2 + 3 + 1) / 3 = 2
        idf = math.log(1 + (3 - 1 + 0.5) / (1 + 0.5))
        norm = BM25_K1 * (1 - BM25_B + BM25_B * 2 / 2)
        expected = idf * 1 * (BM25_K1 + 1) / (1 + norm)
        self.assertAlmostEqual(idx.scores(["apple"])[0], expected, places=12)
        self.assertEqual(idx.scores(["apple"])[1:], [0.0, 0.0])

    def test_idf_is_never_negative(self):
        idx = BM25Index([("a", "alpha beta"), ("b", "alpha gamma")])      # alpha occurs in every chunk
        self.assertGreater(idx.idf["alpha"], 0.0)
        self.assertGreater(idx.scores(["alpha"])[0], 0.0)

    def test_rare_term_outranks_common_term(self):
        idx = BM25Index([("a", "alpha beta"), ("b", "alpha gamma"), ("c", "alpha delta")])
        self.assertEqual(idx.top(["alpha", "beta"], 3)[0], 0)

    def test_length_normalisation(self):
        short = ("s", "alpha beta")
        long = ("l", "alpha " + " ".join(f"filler{i}" for i in range(40)))
        idx = BM25Index([long, short])
        self.assertEqual(idx.top(["alpha"], 2), [1, 0])

    def test_term_frequency_saturates(self):
        idx = BM25Index([("a", "alpha " * 3 + "beta"), ("b", "alpha " * 30 + "beta"), ("c", "gamma delta")])
        s = idx.scores(["alpha"])
        self.assertLess(s[1] / s[0], 3.0)        # ten times the occurrences, far less than three times the score

    def test_repeated_query_token_counts_once_per_occurrence(self):
        idx = BM25Index(self.CHUNKS)
        self.assertAlmostEqual(idx.scores(["apple"] * 3)[0], 3 * idx.scores(["apple"])[0], places=12)

    def test_no_overlap_returns_nothing(self):
        self.assertEqual(BM25Index(self.CHUNKS).top(["zzz"], 3), [])

    def test_k_limit_and_tie_break_by_position(self):
        idx = BM25Index([("a", "alpha"), ("b", "alpha"), ("c", "alpha")])
        self.assertEqual(idx.top(["alpha"], 2), [0, 1])
        self.assertEqual(idx.top(["alpha"], 5), [0, 1, 2])

    def test_empty_inputs(self):
        self.assertEqual(BM25Index([]).top(["alpha"], 3), [])
        self.assertEqual(BM25Index([("a", "the of and")]).top(["alpha"], 3), [])       # stop words only
        self.assertEqual(BM25Index(self.CHUNKS).top([], 3), [])

    def test_deterministic(self):
        a, b = BM25Index(self.CHUNKS), BM25Index(self.CHUNKS)
        q = ["banana", "cherry", "apple"]
        self.assertEqual(a.scores(q), b.scores(q))
        self.assertEqual(a.top(q, 3), b.top(q, 3))

    def test_same_interface_as_tfidf_index(self):
        q = ["banana", "cherry"]
        tfidf, bm25 = ChunkIndex(self.CHUNKS), BM25Index(self.CHUNKS)
        self.assertEqual(tfidf.chunks, bm25.chunks)
        self.assertEqual(set(tfidf.top(q, 3)), set(bm25.top(q, 3)))


class TestBM25Condition(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.pack = load_pack("gscs")
        cls.unit = cls.pack.rename_units()[0]

    def context(self, condition):
        u = self.unit
        r = Retriever(self.pack)
        return r.context(condition, task="rename", standard_id=u.standard_id, language=u.language, kind=u.kind,
                         name=u.injected, code=u.code_violation)

    def test_condition_is_registered(self):
        self.assertIn("bm25", CONDITIONS)

    def test_uses_the_same_query_and_chunks_as_chunk(self):
        u = self.unit
        q = retrieval_query(u.language, u.kind, u.injected, u.code_violation)
        self.assertEqual(q[:1], [u.language.lower()])
        ids = {cid for cid, _ in self.pack.chunks(u.standard_id)}
        ctx = self.context("bm25")
        self.assertLessEqual(ctx.meta["n_items"], 3)
        self.assertTrue(set(ctx.meta["retrieved_ids"]) <= ids)
        self.assertEqual(ctx.meta["n_items"], len(ctx.meta["retrieved_ids"]))

    def test_prompt_wording_is_identical_to_chunk(self):
        # the two lexical conditions must differ only in which passages are retrieved
        strip = lambda t: re.sub(r"\d+ passage", "N passage", t.split("\n", 1)[0])    # noqa: E731
        self.assertEqual(strip(self.context("bm25").text), strip(self.context("chunk").text))

    def test_chunk_condition_is_untouched(self):
        u = self.unit
        r = Retriever(self.pack)
        ctx = r.context("chunk", task="rename", standard_id=u.standard_id, language=u.language, kind=u.kind,
                        name=u.injected, code=u.code_violation)
        idx = ChunkIndex(self.pack.chunks(u.standard_id))
        want = idx.top(retrieval_query(u.language, u.kind, u.injected, u.code_violation), 3)
        self.assertEqual(ctx.meta["retrieved_ids"], [idx.chunks[i][0] for i in want])

    def test_cli_show_and_run(self):
        rc, out, _ = cli("show", "--pack", "gscs", "--condition", "bm25")
        self.assertEqual(rc, 0)
        self.assertIn("most similar to the code", out)
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            rc, _, err = cli("run", "--pack", "gscs", "--backend", "mock:oracle", "--limit", "4", "--conditions",
                             "chunk,bm25", "--out", tmp, "--run-id", "b", "--progress", "100000")
            self.assertEqual(rc, 0, err)
            from athena.report import load_trials
            recs = load_trials([os.path.join(tmp, "b")])[0]
            self.assertEqual({r["condition"] for r in recs}, {"chunk", "bm25"})
            self.assertEqual(len(recs), 8)

    def test_unknown_condition_is_rejected(self):
        rc, _, err = cli("run", "--pack", "gscs", "--backend", "mock:oracle", "--limit", "1", "--conditions", "bm26")
        self.assertEqual(rc, 2)
        self.assertIn("bm25", err)


if __name__ == "__main__":
    unittest.main()
