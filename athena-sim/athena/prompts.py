"""Prompt templates.  Same skeleton for every condition - only the CODING STANDARD block changes -
so differences in results come from the retrieval condition, not from prompt wording.

Output contract matches vendor/output_validator.py: free-text 'Reasoning:' then 'FINAL ANSWER:' + JSON.
"""
from __future__ import annotations

RENAME_TEMPLATE = """You are Athena, a code assistant that makes source code follow a team's coding standard.

TASK
The {kind} `{name}` in the {language} code below breaks the coding standard. Propose ONE replacement name for it.
- Change only this identifier (every occurrence will be renamed for you); do not rewrite other code.
- Keep the meaning: reuse the words of the current name and adapt case, prefixes, suffixes or wording as the standard requires.
- The new name must be a valid {language} identifier and must not clash with a name already used in the code.

CODING STANDARD
{context}

CODE
```{language}
{code}
```

OUTPUT FORMAT
First write "Reasoning:" and 1-3 sentences naming the rule(s) you applied.
Then write "FINAL ANSWER:" followed by one JSON object and nothing after it:
{{"original_name": "{name}", "suggested_name": "<the new name>", "rule_ids_applied": ["<rule id or section, if known>"], "reasoning": "<one sentence>"}}
"""

COMMENT_TEMPLATE = """You are Athena, a code assistant that makes source code follow a team's coding standard.

TASK
Write the documentation comment for the {kind} `{name}` in the {language} code below, following the coding standard.
- Return the complete comment (including its delimiters); it will be inserted directly above the {kind}.
- Do not change any code. Describe what the code actually does; do not invent behaviour.

CODING STANDARD
{context}

CODE
```{language}
{code}
```

OUTPUT FORMAT
First write "Reasoning:" and 1-3 sentences naming the rule(s) you applied.
Then write "FINAL ANSWER:" followed by one JSON object and nothing after it (escape newlines inside strings as \\n):
{{"comment": "<the full comment text>", "format": "<comment style, e.g. block, javadoc, docstring>", "rule_ids_applied": ["<rule id or section, if known>"], "reasoning": "<one sentence>"}}
"""


def build_prompt(task: str, *, language: str, kind: str, name: str, code: str, context: str) -> str:
    tpl = {"rename": RENAME_TEMPLATE, "comment": COMMENT_TEMPLATE}[task]
    return tpl.format(language=language, kind=kind, name=name, code=code, context=context)
