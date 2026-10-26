@echo off
rem Runs both judges one after the other; safe to start again (resumes). Needs OPENROUTER_API_KEY set in this window.
cd /d %~dp0
if not exist results mkdir results
if "%OPENROUTER_API_KEY%"=="" (echo Set OPENROUTER_API_KEY first & exit /b 1)
python -u judge.py --judge muse --workers 8
python -u judge.py --judge haiku --workers 8
python -u aggregate.py --judges muse haiku
