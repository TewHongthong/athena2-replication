# Rubric judging (RQ2 part A) — run through OpenRouter

Judges: Meta Muse Glimmer 30B (`muse`) and Anthropic Claude Haiku 4.5 (`haiku`) via OpenRouter
Estimated cost $1 + $3.5 (caps in judges.json: $3 and $5) — the plan, rubric and hashes are in ADDENDUM.md
Do not edit the prompt, the items or the values in judges.json

## Option 1: run on this machine in the OneDrive folder (recommended — results land right here)
```powershell
cd "C:\Users\tew_hon\OneDrive - Mae Fah Luang University\DAMT2026\LLM coding standard\athena-sim\judge_rubric"
python --version
$env:OPENROUTER_API_KEY = "sk-or-v1-<your key>"
```
Test 20 items per judge:
```powershell
python judge.py --judge muse --limit 20 --workers 4
python judge.py --judge haiku --limit 20 --workers 4
Get-Content results\judgments_muse.jsonl -TotalCount 2
Get-Content results\judgments_haiku.jsonl -TotalCount 2
```
You should see `not ok 0` and a cost of a few cents; then run the full set (muse → haiku → summary):
```powershell
.\run_all.cmd
```
If it stops midway or you open a new window: set `$env:OPENROUTER_API_KEY` again and rerun `.\run_all.cmd` — it continues from where it stopped.
The summary is in `results\rubric_summary.md`.

## Option 2: if this machine has no Python, run on the GPU machine
```powershell
$SRC = "C:\Users\tew_hon\OneDrive - Mae Fah Luang University\DAMT2026\LLM coding standard\athena-sim\judge_rubric"
scp "$SRC\judge.py" "$SRC\judges.json" "$SRC\items.jsonl" "$SRC\run_all.cmd" se@DESKTOP-8UMBG13:C:/athena_judge/
ssh se@DESKTOP-8UMBG13
```
```powershell
powershell
cd C:\athena_judge
$env:OPENROUTER_API_KEY = "sk-or-v1-<your key>"
python judge.py --judge muse --limit 20 --workers 4
python judge.py --judge haiku --limit 20 --workers 4
.\run_all.cmd
```
(The final summary line of run_all will error on the GPU machine because there is no item_map.jsonl — that is fine.) Then copy the results back (PowerShell on this machine):
```powershell
scp "se@DESKTOP-8UMBG13:C:/athena_judge/results/*" "$SRC\results\"
```

Never put the API key in a file or in the chat — set it only as a variable in the PowerShell window.
