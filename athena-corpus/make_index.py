#!/usr/bin/env python3
"""Build corpus_index.tsv (one row per file) and corpus_repos.tsv (one row per repo)
for the athena-corpus folder. Standard library only.

Each corpus file is: a small markdown header, an opening code fence, the EXACT source
bytes, then a closing fence + newline appended directly after the source. The script
recovers the exact source bytes, so code_bytes can be compared with the size from
`git ls-tree -l <commit> <path>` and git_blob_sha1 with the blob id from
`git ls-tree <commit> <path>` on the cloned repo.

Usage (run inside the athena-corpus folder):
    python make_index.py
"""
import hashlib
import os
from collections import OrderedDict

LANGS = ["python", "java", "javascript", "typescript", "csharp"]
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "corpus")
NL, TAB, CR = chr(10), chr(9), chr(13)
NLB, BT = bytes([10]), bytes([96])


def parse(path):
    data = open(path, "rb").read()
    pos, opener = 0, None
    for line in data.split(NLB):
        if line.startswith(BT * 3):
            opener = line
            break
        pos += len(line) + 1
    meta = {}
    for s in data[:pos].decode("utf-8", errors="replace").split(NL):
        s = s.rstrip(CR)
        if s.startswith("- ") and ": " in s:
            k, v = s[2:].split(": ", 1)
            meta[k.strip()] = v.strip()
    content = None
    if opener is not None:
        closer = BT * (len(opener) - len(opener.lstrip(BT))) + NLB
        if data.endswith(closer):
            content = data[pos + len(opener) + 1 : len(data) - len(closer)]
    return meta, data, content


def main():
    rows, problems = [], []
    for lang in LANGS:
        d = os.path.join(ROOT, lang)
        if not os.path.isdir(d):
            problems.append("missing folder: " + d)
            continue
        for name in sorted(os.listdir(d)):
            if not name.endswith(".md"):
                continue
            meta, data, content = parse(os.path.join(d, name))
            miss = [k for k in ["source repo", "license", "created_at", "file path", "commit"] if k not in meta]
            if content is None:
                miss.append("code block")
            if miss:
                problems.append(lang + "/" + name + ": missing " + ",".join(miss))
            if content is None:
                cb = cl = blob = ""
            else:
                cb = len(content)
                cl = content.count(NLB) + (0 if (not content or content.endswith(NLB)) else 1)
                blob = hashlib.sha1(("blob %d" % cb).encode() + bytes([0]) + content).hexdigest()[:12]
            rows.append([lang, name, meta.get("file path", ""), meta.get("source repo", ""),
                         meta.get("license", ""), meta.get("created_at", "")[:10],
                         meta.get("commit", "")[:12], cb, cl, blob, hashlib.sha256(data).hexdigest()[:16]])

    cols = ["language", "md_file", "source_path", "repo", "license", "created_at", "commit12",
            "code_bytes", "code_lines", "git_blob_sha1_12", "md_sha256_16"]
    with open(os.path.join(HERE, "corpus_index.tsv"), "w", encoding="utf-8", newline="") as f:
        f.write(TAB.join(cols) + NL)
        for r in rows:
            f.write(TAB.join(str(x) for x in r) + NL)

    repos = OrderedDict()
    for r in rows:
        g = repos.setdefault((r[0], r[3]), {"n": 0, "b": 0, "lic": set(), "cr": set(), "cm": set()})
        g["n"] += 1
        g["b"] += r[7] if isinstance(r[7], int) else 0
        g["lic"].add(r[4]); g["cr"].add(r[5]); g["cm"].add(r[6])
    with open(os.path.join(HERE, "corpus_repos.tsv"), "w", encoding="utf-8", newline="") as f:
        f.write(TAB.join(["language", "repo", "files", "code_bytes_total", "license", "created_at", "commit12"]) + NL)
        for (lang, repo), g in repos.items():
            f.write(TAB.join([lang, repo, str(g["n"]), str(g["b"]), "/".join(sorted(g["lic"])),
                              "/".join(sorted(g["cr"])), "/".join(sorted(g["cm"]))]) + NL)

    print("files per language:")
    tot = 0
    for lang in LANGS:
        n = sum(1 for r in rows if r[0] == lang)
        tot += n
        print("  %-11s %4d   repos: %d" % (lang, n, sum(1 for k in repos if k[0] == lang)))
    print("  %-11s %4d   repos: %d" % ("TOTAL", tot, len(repos)))
    print("problems: %d" % len(problems))
    for p in problems[:20]:
        print("  " + p)
    print("wrote corpus_index.tsv, corpus_repos.tsv")


if __name__ == "__main__":
    main()
