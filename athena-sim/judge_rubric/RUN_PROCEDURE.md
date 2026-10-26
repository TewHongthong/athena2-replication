# Run procedure: rubric judging

Goal: run two LLM judges through OpenRouter over the fixed, frozen item set, then aggregate the results.

Folder: `athena-sim/judge_rubric`
Read `ADDENDUM.md` and `README.md` first. Judges: `muse` (meta/muse-glimmer-30b, DeepInfra) and `haiku` (anthropic/claude-haiku-4.5).

Rules:
- Do not edit `items.jsonl`, `item_map.jsonl`, `judge.py`, `aggregate.py`, `build_items.py` or `judges.json` (frozen and hashed in `ADDENDUM.md`).
- The OpenRouter key must come from the `OPENROUTER_API_KEY` environment variable. Never write it to a file, a log or a chat.
- If something looks wrong (many "not ok", HTTP errors, cost far above $0.003 per item, the cost cap reached), stop and investigate instead of changing settings.

Steps (`README.md` has the exact commands):
1. In the folder, check `python --version` (3.8+). If Python is missing, use "Option 2" in `README.md` (GPU machine).
2. Quick check: `python judge.py --judge muse --limit 20 --workers 4` and the same for haiku. Inspect 2 sample lines per judge from `results\judgments_*.jsonl` (justification, scores, provider, format, cost_usd) and the total spent.
3. Full run: `.\run_all.cmd` (muse, then haiku, then aggregate). It resumes if started again.
4. Record: the agreement table, the discrimination-check line, the unparsed counts, the total cost per judge, and the path of `results\rubric_summary.md`.
