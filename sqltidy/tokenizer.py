import re
from typing import List

TOKEN_RE = re.compile(
    r"""
    (--[^\n]*)                      |  # single-line comment
    (/\*[\s\S]*?\*/)                |  # multi-line comment

    (\n)                            |  # newline
    (\s+)                           |  # other whitespace

    (<=|>=|<>|!=)                   |  # multi-char operators
    ([(),.;\[\]*=<>+-/])            |  # single-char punctuation/operators

    ('[^']*')                       |  # single-quoted string
    ("[^"]*")                       |  # double-quoted string

    ([A-Za-z_][A-Za-z0-9_]*)        |  # identifiers/keywords
    ([0-9]+(?:\.[0-9]+)?)           |  # numbers

    (\S)                               # fallback: any other non-space
    """,
    re.VERBOSE,
)


def tokenize(sql: str) -> List[str]:
    tokens = []
    for groups in TOKEN_RE.findall(sql):
        # Find the first non-empty capturing group
        for t in groups:
            if t == "":
                continue
            # normalize whitespace
            if t.isspace():
                if "\n" in t:
                    tokens.append("\n")
                else:
                    tokens.append(" ")
            else:
                tokens.append(t)
            break

    return tokens
