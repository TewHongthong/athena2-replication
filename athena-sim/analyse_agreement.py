"""Attribute-level agreement between the human and the LLM-drafted ontology.

    python analyse_agreement.py [--packs godot,dotnet-runtime,odoo] [--out FILE]

Reads packs/<pack>/*_ontology.json (human) and packs/<pack>/llm/llm_ontology.json.
"""
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from athena import agreement  # noqa: E402


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--packs", default="godot,dotnet-runtime,odoo")
    ap.add_argument("--root", default=os.path.join(os.path.dirname(os.path.abspath(__file__)), "packs"))
    ap.add_argument("--out", default=None)
    args = ap.parse_args(argv)
    try:
        result = agreement.compare_packs(args.root, [p for p in args.packs.split(",") if p])
    except ValueError as exc:
        raise SystemExit(str(exc))
    text = json.dumps(result, indent=2, ensure_ascii=False)
    if args.out:
        with open(args.out, "w", encoding="utf-8") as fh:
            fh.write(text + "\n")
    print(text)
    return result


if __name__ == "__main__":
    main()
