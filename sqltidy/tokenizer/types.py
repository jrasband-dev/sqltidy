from typing import NamedTuple
from enum import Enum


class TokenType(Enum):
    KEYWORD = "keyword"
    IDENTIFIER = "identifier"
    STRING = "string"
    NUMBER = "number"
    OPERATOR = "operator"
    PUNCTUATION = "punctuation"
    COMMENT = "comment"
    WHITESPACE = "whitespace"
    NEWLINE = "newline"
    UNKNOWN = "unknown"
