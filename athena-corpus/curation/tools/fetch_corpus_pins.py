#!/usr/bin/env python3
"""Rebuild the Athena Vol. 2 corpus from the pinned commits (WP2, decision C6).

Reads pins/corpus_pins.json + pins/<id>_units.tsv (path, git blob id, status per file that still exists at the
pin) + pins/<id>_new_files.tsv (commit / date at which the file was added), fetches the pinned commit of each
repository (blobless, depth 1), reads every file's bytes at that commit, and writes one markdown file per source
file in the same layout as Vol. 1's athena-corpus/corpus/<lang>/*.md (header, code fence, EXACT source bytes,
closing fence), plus corpus_index.tsv with the same columns as Vol. 1. curate.py --corpus <OUT> can then read
the result with its existing loader.

  python tools/fetch_corpus_pins.py [--only godot dotnet-runtime odoo] [--out DIR] [--clone-dir DIR]
                                    [--eligible-only] [--include-generated] [--verify-only]

Defaults: --out athena-corpus/corpus_v2, --clone-dir ~/.cache/athena2 (one bare repo per id).
Nothing here is committed: OUT gets its own .gitignore ('*'), because the corpus is rebuilt from the pins and
repositories whose code license is not MIT/Apache (Odoo, LGPL-3.0) are distributed as hash + path + script only.

Integrity: the blob id of every file read from git must equal the blob id recorded in <id>_units.tsv
(the run stops on any mismatch). Language directory names: godot -> cpp, dotnet-runtime -> csharp, odoo -> python.
Header field 'created_at' holds the date the file was ADDED to the repository (Vol. 1: repository creation date).
Needs git and the Python standard library; needs network on the first run only (per id, until the pin is cached).
"""
import argparse
import csv
import hashlib
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
CUR = os.path.dirname(HERE)                    # athena-corpus/curation
AC = os.path.dirname(CUR)                      # athena-corpus
PINS = os.path.join(AC, "pins")
LANG_DIR = {"godot": "cpp", "dotnet-runtime": "csharp", "odoo": "python"}
FENCE_LANG = {"cpp": "cpp", "csharp": "csharp", "python": "python"}
INDEX_COLS = ["language", "md_file", "source_path", "repo", "license", "created_at", "commit12",
              "code_bytes", "code_lines", "git_blob_sha1_12", "md_sha256_16"]
MAX_NAME = 200   # bytes; longer file names are shortened (keeps Windows/drvfs paths usable)


def git(*args, cwd=None, inp=None, check=True):
    p = subprocess.run(["git", *args], cwd=cwd, input=inp, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if check and p.returncode != 0:
        raise RuntimeError("git %s failed: %s" % (" ".join(args), p.stderr.decode("utf8", "replace").strip()))
    return p


def read_tsv(path):
    with open(path, encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f, delimiter="\t"))


def blob_id(data):
    return hashlib.sha1(b"blob %d\0" % len(data) + data).hexdigest()


def ensure_pin(entry, clone_dir):
    """Bare repo with the pinned commit (tree only, blobs lazily). Returns its path."""
    repo = os.path.join(clone_dir, entry["id"] + ".git")
    commit = entry["pinned_commit"]
    if not os.path.isdir(repo):
        os.makedirs(repo, exist_ok=True)
        git("init", "-q", "--bare", repo)
        git("remote", "add", "origin", entry["repo"], cwd=repo)
    # 'cat-file -e' does not trigger a lazy fetch (the fetch below marks the remote as promisor itself)
    have = git("cat-file", "-e", commit + "^{commit}", cwd=repo, check=False)
    if have.returncode != 0:
        print("  fetching %s @ %s (blobless, depth 1) ..." % (entry["repo"], commit[:12]), flush=True)
        git("fetch", "-q", "--depth", "1", "--filter=blob:none", "--no-tags", "origin", commit, cwd=repo)
        got = git("rev-parse", "FETCH_HEAD", cwd=repo).stdout.decode().strip()
        if got != commit:
            raise RuntimeError("fetched %s, expected %s" % (got, commit))
    return repo


def prefetch_blobs(repo, blobs):
    """Fetch all needed blobs in a few requests; without this git fetches a missing blob per request (slow).
    Objects already present are skipped by git, so this is cheap on a cached clone."""
    print("  fetching %d blobs ..." % len(blobs), flush=True)
    step = 400
    for i in range(0, len(blobs), step):
        r = git("-c", "gc.auto=0", "fetch", "-q", "--no-tags", "--no-write-fetch-head", "origin",
                *blobs[i:i + step], cwd=repo, check=False)
        if r.returncode != 0:
            print("  batch fetch refused (%s); falling back to one request per blob (slow)"
                  % r.stderr.decode("utf8", "replace").strip()[:120], flush=True)
            return


def read_blobs(repo, blobs):
    """-> {blob_id: bytes} via one git cat-file --batch process."""
    p = subprocess.Popen(["git", "-c", "gc.auto=0", "cat-file", "--batch"], cwd=repo, stdin=subprocess.PIPE,
                         stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out = {}
    try:
        for b in blobs:
            p.stdin.write((b + "\n").encode())
            p.stdin.flush()
            head = p.stdout.readline().decode().split()
            if len(head) != 3 or head[1] != "blob":
                raise RuntimeError("cannot read blob %s: %s" % (b, " ".join(head)))
            size = int(head[2])
            data = p.stdout.read(size)
            p.stdout.read(1)
            out[b] = data
    finally:
        p.stdin.close()
        p.wait()
    return out


def parse_md(path):
    """Recover the source bytes the way curate.py's parse_corpus_md does (None if no intact code block)."""
    data = open(path, "rb").read()
    pos, opener = 0, None
    for line in data.split(b"\n"):
        if line.startswith(b"```"):
            opener = line
            break
        pos += len(line) + 1
    if opener is None:
        return None
    closer = b"`" * (len(opener) - len(opener.lstrip(b"`"))) + b"\n"
    if not data.endswith(closer):
        return None
    return data[pos + len(opener) + 1: len(data) - len(closer)]


def md_name(entry, path, blob, used):
    owner_repo = entry["repo"].rstrip("/")
    if owner_repo.endswith(".git"):
        owner_repo = owner_repo[:-4]
    owner, repo = owner_repo.split("/")[-2:]
    name = "%s__%s__%s.md" % (owner, repo, path.replace("/", "__"))
    if len(name.encode("utf8")) > MAX_NAME or name in used:
        stem = ("%s__%s__%s" % (owner, repo, os.path.basename(path)))[:MAX_NAME - 30]
        name = "%s~%s.md" % (stem, blob[:12])
    if name in used:
        raise RuntimeError("file name collision: %s" % name)
    used.add(name)
    return name


def render(entry, path, added, content):
    """Same layout as Vol. 1: header, opening fence, exact bytes, closing fence + newline."""
    lang = LANG_DIR[entry["id"]]
    owner_repo = entry["repo"].rstrip("/")
    if owner_repo.endswith(".git"):
        owner_repo = owner_repo[:-4]
    short = "/".join(owner_repo.split("/")[-2:])
    ticks = 3
    for line in content.split(b"\n"):
        n = len(line) - len(line.lstrip(b"`"))
        if n >= ticks:                      # source contains a fence-like line: use a longer fence
            ticks = n + 1
    fence = b"`" * ticks
    head = ("# %s\n\n- source repo: %s\n- repo url: %s\n- license: %s\n- created_at: %s\n- file path: %s\n"
            "- commit: %s\n- added in commit: %s\n\n"
            % (path, short, owner_repo, entry["code_license"], added.get("add_date", ""), path,
               entry["pinned_commit"], added.get("add_commit", ""))).encode("utf8")
    return head + fence + FENCE_LANG[lang].encode() + b"\n" + content + fence + b"\n", short


def build(entry, a):
    eid = entry["id"]
    lang = LANG_DIR[eid]
    units = read_tsv(os.path.join(PINS, "%s_units.tsv" % eid))
    added = {r["path"]: r for r in read_tsv(os.path.join(PINS, "%s_new_files.tsv" % eid))}
    rows = [r for r in units if (a.include_generated or r["status"] == "ok")
            and (not a.eligible_only or int(r["units_eligible"]) > 0)]
    print("[%s] %s: %d of %d files at pin selected%s%s" % (
        eid, lang, len(rows), len(units), " (eligible units only)" if a.eligible_only else "",
        " (generated included)" if a.include_generated else ""))
    ldir = os.path.join(a.out, "corpus", lang)
    index = []

    if a.verify_only:
        used = set()
        bad = 0
        for r in rows:
            name = md_name(entry, r["path"], r["blob"], used)
            p = os.path.join(ldir, name)
            if not os.path.exists(p):
                print("  missing: " + name)
                bad += 1
                continue
            content = parse_md(p)
            if content is None:
                print("  no code block: " + name)
                bad += 1
            elif blob_id(content) != r["blob"]:
                print("  blob mismatch: " + name)
                bad += 1
        print("[%s] verify: %d files checked, %d problems" % (eid, len(rows), bad))
        return bad == 0, []

    repo = ensure_pin(entry, a.clone_dir)
    blobs = sorted({r["blob"] for r in rows})
    prefetch_blobs(repo, blobs)
    data = read_blobs(repo, blobs)
    for b, d in data.items():
        if blob_id(d) != b:
            raise RuntimeError("blob %s content hash mismatch" % b)
    os.makedirs(ldir, exist_ok=True)
    used = set()
    nbytes = 0
    for r in rows:
        content = data[r["blob"]]
        text, short = render(entry, r["path"], added.get(r["path"], {}), content)
        name = md_name(entry, r["path"], r["blob"], used)
        with open(os.path.join(ldir, name), "wb") as f:
            f.write(text)
        nbytes += len(content)
        nl = content.count(b"\n")
        lines = nl + (0 if (not content or content.endswith(b"\n")) else 1)
        index.append([lang, name, r["path"], short, entry["code_license"],
                      (added.get(r["path"], {}).get("add_date") or "")[:10], entry["pinned_commit"][:12],
                      len(content), lines, r["blob"][:12], hashlib.sha256(text).hexdigest()[:16]])
    print("[%s] wrote %d files (%d source bytes) to %s" % (eid, len(index), nbytes, ldir))
    return True, index


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--only", nargs="*", default=None, choices=sorted(LANG_DIR))
    ap.add_argument("--out", default=os.path.join(AC, "corpus_v2"))
    ap.add_argument("--clone-dir", default=os.path.expanduser("~/.cache/athena2"))
    ap.add_argument("--eligible-only", action="store_true",
                    help="only files that have >= 1 eligible unit (6-40 lines, no parse error)")
    ap.add_argument("--include-generated", action="store_true")
    ap.add_argument("--verify-only", action="store_true", help="re-check files already in --out; no network")
    a = ap.parse_args()

    pins = json.load(open(os.path.join(PINS, "corpus_pins.json"), encoding="utf-8"))
    entries = [e for e in pins["repos"] if a.only is None or e["id"] in a.only]
    os.makedirs(a.out, exist_ok=True)
    if not a.verify_only:
        with open(os.path.join(a.out, ".gitignore"), "w", newline="\n") as f:
            f.write("*\n")
    all_ok = True
    index_path = os.path.join(a.out, "corpus_index.tsv")
    kept = []
    if not a.verify_only and os.path.exists(index_path):          # keep rows of ids not rebuilt now
        with open(index_path, encoding="utf-8", newline="") as f:
            keep_langs = {LANG_DIR[e["id"]] for e in entries}
            kept = [r for r in csv.reader(f, delimiter="\t")][1:]
            kept = [r for r in kept if r and r[0] not in keep_langs]
    rows = []
    for e in entries:
        ok, idx = build(e, a)
        all_ok &= ok
        rows += idx
    if not a.verify_only:
        with open(index_path, "w", encoding="utf-8", newline="") as f:
            f.write("\t".join(INDEX_COLS) + "\n")
            for r in kept + rows:
                f.write("\t".join(str(x) for x in r) + "\n")
        print("wrote %s (%d rows)" % (index_path, len(kept) + len(rows)))
    sys.exit(0 if all_ok else 1)


if __name__ == "__main__":
    main()
