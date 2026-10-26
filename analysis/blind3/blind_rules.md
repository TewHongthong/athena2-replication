# Naming rules of the three standards (quoted from the pinned documents)

Judge only the name in the column name_to_judge. The code is context for the kind of identifier.
If the quoted text does not decide the case, answer unsure and write a note.

## Godot (C++) - cpp_usage_guidelines.rst, section Naming

    - Types and namespaces use ``PascalCase``, and macros and constants use ``UPPER_SNAKE_CASE``.
      All other identifiers use ``snake_case``.
    - Method parameters start with ``p_*``, or ``r_*`` (if they are used to return a value).
    - Use full words. Avoid abbreviations except when the full name makes the code hard to read.
    - Pointer and reference operators are affixed to the variable identifier, not
      to the type name.

## .NET runtime (C#) - coding-style.md, rules 3, 12 and 13

    3. We use `_camelCase` for internal and private fields and use `readonly` where possible. Prefix internal and private instance fields with `_`, static fields with `s_` and thread static fields with `t_`. When used on static fields, `readonly` should come after `static` (e.g. `static readonly` not `readonly static`).  Public fields should be used sparingly and should use PascalCasing with no prefix when used.

    12. We use PascalCasing to name all our constant local variables and fields. The only exception is for interop code where the constant value should exactly match the name and value of the code you are calling via interop.

    13. We use PascalCasing for all method names, including local functions.

## Odoo (Python) - coding_guidelines.rst, Variable name

    - Variable name :
        - use Pascal case for model variable
        - use underscore lowercase notation for common variable.
        - suffix your variable name with *_id* or *_ids* if it contains a record id or list of id. Don't use ``partner_id`` to contain a record of res.partner
