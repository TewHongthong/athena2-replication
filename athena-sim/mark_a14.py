#!/usr/bin/env python3
"""mark_a14 - fill the label and quote columns of the sheet of addendum A14 by picking passages.

  python mark_a14.py [--sources SHEET] [--root DIR]                  answer in the terminal
  python mark_a14.py --make-form FORM.xlsx [--sources SHEET]         write a spreadsheet form to fill in
  python mark_a14.py --read-form FORM.xlsx [--sources SHEET]         copy a filled form into the sheet

For each naming rule of the sheet, the passages of the pinned document that mention the casing or the prefix of
the rule, or a kind it applies to, are listed, those that mention the casing or the prefix first (at most eight).
The labeller picks the passages that support the rule, or none, and gives the label: stated if a picked passage
names the kind of identifier, covered if a general statement includes it, inferred if no passage supports it. In
the terminal any word can be searched as well; in the form the words of the document can be given in a column of
their own. The passages are those the retrieval conditions use (athena.passages, split by the file extension of
the document); the words of each picked passage, without its headings, become the quote, with runs of white space
joined. The sheet is written once, when every rule has an answer; only its label, quote and note columns change.
The form needs openpyxl; the terminal mode uses the standard library only.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import math
import os
import re
import sys
import textwrap

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from athena.passages import split_passages  # noqa: E402
from analyse_a14 import (COLUMNS, DEFAULT_ROOT, DEFAULT_SOURCES, LABELS, NEEDS_QUOTE, _ws, doc_path,  # noqa: E402
                         find_quote, read_sheet, sha256_of)

LIST_MAX = 8
WIDTH = 100
FORM_SHEET = "Marking"
FORM_HEADERS = ("No.", "Rule", "Passage of the pinned document (or, in a blue row, the rule)", "x", "Label",
                "Other quote (optional)", "Note (optional, English)", "key")


# ---------------------------------------------------------------- passages

def head_body(passage):
    return passage.split("\n\n", 1) if "\n\n" in passage else ("", passage)


def _loose(s):
    return re.sub(r"[\s_\-`*]", "", s.lower())


def terms_of(row):
    """The casing or prefix of the rule (a prefix of one character is not searched) and the kinds it applies to."""
    req, terms = row["requirement"], []
    m = re.search(r"casing (\S+)", req)
    if m:
        terms.append(("casing", m.group(1).rstrip(";")))
    m = re.search(r"prefix (\S+)", req)
    if m and len(m.group(1).rstrip(";")) >= 2:
        terms.append(("prefix", m.group(1).rstrip(";")))
    return terms, row["applies_to"].split()


def search_words(row):
    terms, kinds = terms_of(row)
    return [t for _typ, t in terms] + [k.replace("_", " ") for k in kinds]


def score(passage, terms, kinds):
    """10 for the casing (matched without its final e, so that PascalCase also finds PascalCasing) or the prefix,
    and 1 for each kind named."""
    s = 0
    for typ, t in terms:
        if (typ == "casing" and _loose(t).rstrip("e") in _loose(passage)) or (typ == "prefix" and t in passage):
            s += 10
    for k in kinds:
        if re.search(r"\b" + re.escape(k.replace("_", " ")), passage, re.I):
            s += 1
    return s


def candidates(row, passages):
    """(index, passage) of every passage that scores above 0, best first and then in document order."""
    terms, kinds = terms_of(row)
    ranked = sorted(((score(p, terms, kinds), i, p) for i, p in enumerate(passages)), key=lambda x: (-x[0], x[1]))
    return [(i, p) for s, i, p in ranked if s > 0]


def load_docs(rows, root):
    docs = {}
    for r in rows:
        path = os.path.join(root, doc_path(r["source_document"]))
        if path not in docs:
            if not os.path.exists(path):
                sys.exit(f"pinned document not found: {path} (run fetch_standards.py)")
            with open(path, "rb") as f:
                raw = f.read()
            text = raw.decode("utf-8")
            docs[path] = {"text": text, "sha": hashlib.sha256(raw).hexdigest(),
                          "passages": [p for _pid, p in split_passages(text, "md" if path.endswith(".md") else "rst")]}
    return docs


def doc_of(docs, root, row):
    return docs[os.path.join(root, doc_path(row["source_document"]))]


def write_sheet(path, header, rows):
    with open(path, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(header), lineterminator="\n")
        w.writeheader()
        w.writerows(rows)
    print(f"\nWritten: {path}\nsha256: {sha256_of(path)}\nCheck it with: python3 -B analyse_a14.py --check")


# ---------------------------------------------------------------- terminal

def show(items, total):
    for i, p in enumerate(items, 1):
        head, body = head_body(p)
        print(f"\n  {i}. [{head}]" if head else f"\n  {i}.")
        for line in textwrap.wrap(_ws(body), WIDTH - 6):
            print("      " + line)
    if total > len(items):
        print(f"\n  ({total - len(items)} more passages match; type a word to narrow the search)")
    if not items:
        print("\n  No passage matches.")


def ask(prompt):
    return input(prompt).strip()


def ask_rule(n, total, row, passages):
    kinds = row["applies_to"].split()
    hits = [p for _i, p in candidates(row, passages)]
    shown, count = hits[:LIST_MAX], len(hits)
    title = "mention " + " or ".join(f'"{w}"' for w in search_words(row))
    while True:
        print("\n" + "=" * WIDTH)
        print(f"[{n}/{total}] {row['rule_id']}   kind: {row['applies_to'] or '-'}   rule: {row['requirement']}"
              f"   test tasks: {row['test_tasks']}")
        print(f"Your ontology says: {row['description']}")
        if len(kinds) > 1:
            print("This rule applies to several kinds: label it by the kind with the weakest support.")
        print(f"\nPassages of {os.path.basename(doc_path(row['source_document']))} that {title}:")
        show(shown, count)
        a = ask("\nPassage number(s) that support the rule (e.g. 1 or 1 3), 0 if none, or a word to search: ")
        if not a:
            continue
        if a == "0":
            return "inferred", []
        if re.fullmatch(r"[0-9][0-9 ,]*", a):
            nums = list(dict.fromkeys(int(x) for x in re.split(r"[ ,]+", a) if x))
            if 0 in nums or not all(1 <= x <= len(shown) for x in nums):
                print(f"\n>> Type numbers from 1 to {len(shown)}, or 0 alone.")
                continue
            picked = [shown[x - 1] for x in nums]
            break
        found = [p for p in passages if a.lower() in p.lower()]
        shown, count, title = found[:LIST_MAX], len(found), f'contain "{a}"'
    while True:
        lab = ask("Label: s = a picked passage names the kind of this rule, "
                  "c = a general statement covers it: ").lower()
        if lab in ("s", "c"):
            return ("stated" if lab == "s" else "covered"), picked
        print(">> Type s or c.")


def summary(rows, answers):
    print("\n" + "=" * WIDTH + "\nSummary\n")
    for i, r in enumerate(rows, 1):
        lab, picked = answers[i - 1]
        first = _ws(head_body(picked[0])[1])[:60] + "..." if picked else "(no passage)"
        print(f"  {i:2d}. {r['rule_id']:38s} {lab:9s} {len(picked)}  {first}")


def terminal(a, header, rows, docs):
    print(f"{len(rows)} rules. Nothing is written until you type 'save' at the end. Ctrl+C stops without saving.")
    answers = []
    try:
        for i, r in enumerate(rows, 1):
            answers.append(ask_rule(i, len(rows), r, doc_of(docs, a.root, r)["passages"]))
        while True:
            summary(rows, answers)
            c = ask("\nType 'save' to write the sheet, a number to answer that rule again, "
                    "or 'quit' to leave without saving: ").lower()
            if c == "save":
                break
            if c == "quit":
                sys.exit("Stopped; nothing was written.")
            if c.isdigit() and 1 <= int(c) <= len(rows):
                k = int(c)
                answers[k - 1] = ask_rule(k, len(rows), rows[k - 1], doc_of(docs, a.root, rows[k - 1])["passages"])
    except (KeyboardInterrupt, EOFError):
        sys.exit("\nStopped; nothing was written.")
    for r, (lab, picked) in zip(rows, answers):
        quote = " | ".join(_ws(head_body(p)[1]) for p in picked)
        if picked and "not found" in find_quote(quote, doc_of(docs, a.root, r)["text"]):
            sys.exit(f"{r['rule_id']}: a picked passage was not found in the document; nothing was written.")
        r["label"], r["quote"], r["note"] = lab, quote, ""
    write_sheet(a.sources, header, rows)


# ---------------------------------------------------------------- spreadsheet form

def _lines(text, width):
    return sum(max(1, math.ceil(len(part) / width)) for part in str(text).split("\n"))


def make_form(a, rows, docs):
    from openpyxl import Workbook
    from openpyxl.styles import Alignment, Border, Font, PatternFill, Protection, Side
    from openpyxl.worksheet.datavalidation import DataValidation

    if os.path.exists(a.make_form) and not a.force:
        sys.exit(f"{a.make_form} exists; it may hold answers. Pass --force to replace it.")
    wb = Workbook()
    ws = wb.active
    ws.title = FORM_SHEET
    ws.append(["A14 marking form. For each rule (blue row): put x next to every passage that supports the rule, "
               "then choose the label in the blue row. Only the yellow cells can be changed."])
    ws.append(list(FORM_HEADERS))
    widths = {"A": 6, "B": 30, "C": 85, "D": 5, "E": 12, "F": 30, "G": 24, "H": 10}
    for col, w in widths.items():
        ws.column_dimensions[col].width = w
    ws.column_dimensions["H"].hidden = True
    dv_x = DataValidation(type="list", formula1='"x"', allow_blank=True)
    dv_label = DataValidation(type="list", formula1='"stated,covered,inferred"', allow_blank=True,
                              showErrorMessage=True, error="Choose stated, covered or inferred.")
    ws.add_data_validation(dv_x)
    ws.add_data_validation(dv_label)
    blue = PatternFill("solid", fgColor="DDEBF7")
    yellow = PatternFill("solid", fgColor="FFF2CC")
    thin = Side(style="thin", color="BFBFBF")
    box = Border(top=thin, bottom=thin, left=thin, right=thin)
    top = Alignment(wrap_text=True, vertical="top")
    ws["A1"].font = Font(bold=True)
    for c in ws[2]:
        c.font = Font(bold=True)
        c.alignment = top
        c.border = box
    for n, r in enumerate(rows, 1):
        d = doc_of(docs, a.root, r)
        hits = candidates(r, d["passages"])
        shown = hits[:LIST_MAX]
        name = os.path.basename(doc_path(r["source_document"]))
        words = ", ".join(search_words(r))
        found = (f"{len(hits)} passage(s) of {name} mention: {words}"
                 + (f" (the first {LIST_MAX} are shown below)" if len(hits) > LIST_MAX else " (shown below)")
                 if hits else f"No passage of {name} mentions: {words}. Use 'Other quote' or choose inferred.")
        info = (f"Kind: {r['applies_to'] or '-'}   |   Rule: {r['requirement']}   |   Test tasks: {r['test_tasks']}\n"
                f"Your ontology says: {r['description']}\n{found}")
        if len(r["applies_to"].split()) > 1:
            info += "\nThis rule applies to several kinds: label it by the kind with the weakest support."
        ws.append([n, r["rule_id"], info, None, None, None, None, f"rule|{r['rule_id']}|{d['sha']}"])
        i = ws.max_row
        for c in ws[i]:
            c.fill, c.alignment, c.border = blue, top, box
        ws[f"A{i}"].font = ws[f"B{i}"].font = Font(bold=True)
        for col in "EFG":
            ws[f"{col}{i}"].fill = yellow
            ws[f"{col}{i}"].protection = Protection(locked=False)
        dv_label.add(f"E{i}")
        ws.row_dimensions[i].height = 15 * _lines(info, 80)
        for j, (idx, p) in enumerate(shown, 1):
            head, body = head_body(p)
            text = (f"[{head}]\n" if head else "") + _ws(body)
            ws.append([f"{n}.{j}", None, text, None, None, None, None, f"passage|{r['rule_id']}|{idx}"])
            k = ws.max_row
            for c in ws[k]:
                c.alignment, c.border = top, box
            ws[f"D{k}"].fill = yellow
            ws[f"D{k}"].protection = Protection(locked=False)
            ws[f"D{k}"].alignment = Alignment(horizontal="center", vertical="top")
            dv_x.add(f"D{k}")
            ws.row_dimensions[k].height = 15 * _lines(text, 80)
    ws.freeze_panes = "C3"
    ws.protection.sheet = True
    ws.protection.formatColumns = False
    ws.protection.formatRows = False
    ws.protection.formatCells = False
    ws.page_setup.orientation = "landscape"
    ws.page_setup.fitToWidth = 1
    ws.page_setup.fitToHeight = 0
    ws.sheet_properties.pageSetUpPr.fitToPage = True

    ins = wb.create_sheet("How to fill")
    for line in ["How to fill the form",
                 "",
                 "1. Each rule has a blue row; the passages of the pinned document listed under it are numbered 1.1, 1.2, ...",
                 "2. Read the passages. Put x (column D) next to every passage that supports the rule.",
                 "3. In the blue row, choose the label (column E):",
                 "   stated   = a passage with x names the kind of identifier of this rule",
                 "   covered  = a passage with x is a general statement that includes the kind (for example all other identifiers)",
                 "   inferred = no passage supports the rule (leave column D empty)",
                 "4. If the words that support the rule are in the document but not in the list, copy them from the "
                 "document into 'Other quote' (column F).",
                 "5. Notes (column G) are optional and must be in English.",
                 "6. Save the file in this format (.xlsx) under the same name."]:
        ins.append([line])
    ins.column_dimensions["A"].width = 120
    wb.active = 0
    wb.save(a.make_form)
    print(f"Written: {a.make_form} ({len(rows)} rules)")


def read_form(a, header, rows, docs):
    from openpyxl import load_workbook

    wb = load_workbook(a.read_form, data_only=True)
    if FORM_SHEET not in wb.sheetnames:
        sys.exit(f"no sheet named {FORM_SHEET} in {a.read_form}")
    ws = wb[FORM_SHEET]
    head = [str(c.value or "").strip() for c in ws[2]]
    if tuple(head[:len(FORM_HEADERS)]) != FORM_HEADERS:
        sys.exit("the form's header row was changed")
    col = {h: i for i, h in enumerate(FORM_HEADERS)}
    answers = {}
    for row in ws.iter_rows(min_row=3, values_only=True):
        key = row[col["key"]] if len(row) > col["key"] else None
        if not key:
            continue
        kind, rid, rest = str(key).split("|", 2)
        if kind == "rule":
            answers[rid] = {"label": str(row[col["Label"]] or "").strip().lower(),
                            "other": str(row[col["Other quote (optional)"]] or "").strip(),
                            "note": str(row[col["Note (optional, English)"]] or "").strip(),
                            "sha": rest, "picked": []}
        elif kind == "passage" and str(row[col["x"]] or "").strip():
            answers[rid]["picked"].append(int(rest))
    errors = []
    for r in rows:
        rid, ans = r["rule_id"], answers.get(r["rule_id"])
        if ans is None:
            errors.append(f"{rid}: not in the form")
            continue
        d = doc_of(docs, a.root, r)
        if ans["sha"] != d["sha"]:
            errors.append(f"{rid}: the pinned document changed after the form was made")
        lab, picked, other = ans["label"], sorted(set(ans["picked"])), ans["other"]
        if lab not in LABELS:
            errors.append(f"{rid}: choose a label (stated, covered or inferred)")
        elif lab == "inferred" and (picked or other):
            errors.append(f"{rid}: inferred, but a passage has x or an other quote is given")
        elif lab in NEEDS_QUOTE and not (picked or other):
            errors.append(f"{rid}: {lab} needs an x on a passage or an other quote")
        if any(ord(ch) > 127 for ch in ans["note"]):
            errors.append(f"{rid}: write the note in English")
        if other and "not found" in find_quote(other, d["text"]):
            errors.append(f"{rid}: the other quote was not found in {os.path.basename(doc_path(r['source_document']))}")
        quote = " | ".join([_ws(head_body(d["passages"][i])[1]) for i in picked] + ([other] if other else []))
        r["label"], r["quote"], r["note"] = lab, quote, ans["note"]
    if errors:
        sys.exit("The sheet was not written:\n  - " + "\n  - ".join(errors))
    for r in rows:
        print(f"  {r['rule_id']:38s} {r['label']:9s} {r['quote'].count(' | ') + 1 if r['quote'] else 0} passage(s)")
    write_sheet(a.sources, header, rows)


# ---------------------------------------------------------------- main

def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--sources", default=DEFAULT_SOURCES)
    ap.add_argument("--root", default=DEFAULT_ROOT)
    g = ap.add_mutually_exclusive_group()
    g.add_argument("--make-form", default=None)
    g.add_argument("--read-form", default=None)
    ap.add_argument("--force", action="store_true", help="replace an existing form")
    a = ap.parse_args()
    try:
        header, rows = read_sheet(a.sources)
    except UnicodeDecodeError:
        sys.exit("The sheet is not saved as UTF-8; restore the empty sheet before marking.")
    missing = [c for c in COLUMNS if c not in header]
    if missing:
        sys.exit("columns missing from the sheet: " + ", ".join(missing))
    docs = load_docs(rows, a.root)
    if a.make_form:
        make_form(a, rows, docs)
    elif a.read_form:
        read_form(a, header, rows, docs)
    else:
        terminal(a, header, rows, docs)


if __name__ == "__main__":
    main()
