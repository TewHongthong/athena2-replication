"""Athena Sim - a headless stand-in for the (lost) Athena VS Code extension.

It replays the extension's workflow (pick a violating identifier -> retrieve the coding
standard -> build a prompt -> call an LLM -> validate -> propose a rename) without any UI and
records every step so experiments can be analysed afterwards.  Standard library only.
"""

__version__ = "0.1.0"
