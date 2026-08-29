"""CTD section code ordering utilities."""

from __future__ import annotations

import re


def ctd_code_sort_key(code: str | None) -> tuple:
    """Sort CTD codes numerically (e.g. 3.2.S.4.2 before 3.2.S.4.10)."""
    if not code:
        return ((9999,),)
    tokens: list[tuple[int, int | str]] = []
    for part in code.split("."):
        for match in re.finditer(r"\d+|[A-Za-z]+", part):
            token = match.group()
            if token.isdigit():
                tokens.append((0, int(token)))
            else:
                tokens.append((1, token))
    return tuple(tokens)  # type: ignore[return-value]
