#!/usr/bin/env python3
"""Fetch the pinned guideline documents listed in standards.json.

Usage:
    python fetch_standards.py [--out DIR] [--only ID ...] [--write-hashes | --verify-only]

For every standard it downloads the guideline document and the repository's
license file at the pinned commit (git, blobless shallow fetch of that exact
commit), writes them under DIR/<id>/, and checks SHA-256 against standards.json.
--write-hashes records the hashes instead (use once, right after pinning).
--verify-only checks files already in DIR against the recorded hashes (no network).
Needs only git and the Python standard library. Nothing is committed: the
default output directory (standards/src) is git-ignored, so license-restricted
text is never redistributed from this repository.
"""
import argparse
import hashlib
import json
import os
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
PINS = os.path.join(HERE, "standards.json")


def run(args, cwd=None, binary=False):
    p = subprocess.run(args, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if p.returncode != 0:
        raise RuntimeError("%s failed: %s" % (" ".join(args), p.stderr.decode("utf8", "replace").strip()))
    return p.stdout if binary else p.stdout.decode("utf8", "replace")


def fetch_blobs(entry):
    """Return {name: bytes} for the doc and the license at the pinned commit."""
    with tempfile.TemporaryDirectory(prefix="athena2_fetch_") as tmp:
        run(["git", "init", "-q", tmp])
        run(["git", "remote", "add", "origin", entry["doc_repo"]], cwd=tmp)
        run(["git", "fetch", "-q", "--depth", "1", "--filter=blob:none", "origin", entry["commit"]], cwd=tmp)
        got_commit = run(["git", "rev-parse", "FETCH_HEAD"], cwd=tmp).strip()
        if got_commit != entry["commit"]:
            raise RuntimeError("fetched %s, expected %s" % (got_commit, entry["commit"]))
        out = {}
        for key in ("doc_path", "license_path"):
            path = entry[key]
            base = os.path.basename(path)
            name = base if key == "doc_path" else "LICENSE" + os.path.splitext(base)[1]
            out[name] = run(["git", "show", "%s:%s" % (entry["commit"], path)], cwd=tmp, binary=True)
        return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", default=os.path.join(HERE, "src"))
    ap.add_argument("--only", nargs="*", default=None)
    ap.add_argument("--write-hashes", action="store_true")
    ap.add_argument("--verify-only", action="store_true")
    a = ap.parse_args()

    pins = json.load(open(PINS, encoding="utf8"))
    bad = 0
    for e in pins["standards"]:
        if a.only and e["id"] not in a.only:
            continue
        d = os.path.join(a.out, e["id"])
        if a.verify_only:
            blobs = {}
            for name in e.get("sha256", {}):
                fp = os.path.join(d, name)
                blobs[name] = open(fp, "rb").read() if os.path.exists(fp) else b""
        else:
            blobs = fetch_blobs(e)
            os.makedirs(d, exist_ok=True)
            for name, data in blobs.items():
                with open(os.path.join(d, name), "wb") as f:
                    f.write(data)
        digest = {n: hashlib.sha256(b).hexdigest() for n, b in blobs.items()}
        if a.write_hashes:
            e["sha256"] = digest
            print("%-15s hashes recorded (%d files)" % (e["id"], len(digest)))
        else:
            ok = e.get("sha256") == digest
            bad += 0 if ok else 1
            print("%-15s %s  commit %s  %s" % (e["id"], "OK      " if ok else "MISMATCH", e["commit"][:10],
                                               ", ".join(sorted(blobs))))
    if a.write_hashes:
        with open(PINS, "w", encoding="utf8") as f:
            json.dump(pins, f, indent=2, ensure_ascii=False)
            f.write("\n")
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
