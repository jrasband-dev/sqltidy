# tokenizer/core.py
"""
Core tokenization logic and types.
"""

import re
from typing import Union, NamedTuple, Pattern, Literal, List, Dict
from enum import Enum
from ..dialects import get_dialect, SQLDialect
from .types import TokenType
from dataclasses import dataclass


# Token pattern definition (similar to Construct)
@dataclass(frozen=True)
class TokenPattern:
    """Defines a pattern for matching tokens."""

    name: str
    pattern: Pattern
    dialect: Literal["all", "sqlserver", "postgres", "mysql", "sqlite", "oracle"] = (
        "all"
    )

    @property
    def regex(self) -> Pattern:
        return self.pattern


# Define token patterns
SINGLE_LINE_COMMENT = TokenPattern(
    name="Single Line Comment", pattern=re.compile(r"--[^\n]*"), dialect="all"
)
MULTI_LINE_COMMENT = TokenPattern(
    name="Multi Line Comment", pattern=re.compile(r"/\*[\s\S]*?\*/"), dialect="all"
)
NEWLINE = TokenPattern(name="Newline", pattern=re.compile(r"\n"), dialect="all")
WHITESPACE = TokenPattern(name="Whitespace", pattern=re.compile(r"\s+"), dialect="all")
MULTI_CHAR_OPERATOR = TokenPattern(
    name="Multi-char Operator", pattern=re.compile(r"<=|>=|<>|!="), dialect="all"
)
SINGLE_CHAR_PUNCTUATION = TokenPattern(
    name="Single-char Punctuation",
    pattern=re.compile(r"[(),.;\[\]*=<>+-/]"),
    dialect="all",
)
SINGLE_QUOTE = TokenPattern(
    name="Single-quoted String", pattern=re.compile(r"'[^']*'"), dialect="all"
)
DOUBLE_QUOTE = TokenPattern(
    name="Double-quoted String", pattern=re.compile(r'"[^"]*"'), dialect="all"
)
IDENTIFIER = TokenPattern(
    name="Identifier", pattern=re.compile(r"[A-Za-z_@#][A-Za-z0-9_@#$]*"), dialect="all"
)
NUMBER = TokenPattern(
    name="Number", pattern=re.compile(r"[0-9]+(?:\.[0-9]+)?"), dialect="all"
)
COMMA = TokenPattern(name="Comma", pattern=re.compile(r","), dialect="all")
FALLBACK = TokenPattern(name="Fallback", pattern=re.compile(r"\S"), dialect="all")


# Token instance (actual token with value and type)
class Token(NamedTuple):
    """Represents a single SQL token instance with its value and type."""

    value: str
    type: TokenType


# Registry of token patterns in order
TOKEN_PATTERNS: List[TokenPattern] = [
    SINGLE_LINE_COMMENT,
    MULTI_LINE_COMMENT,
    NEWLINE,
    WHITESPACE,
    MULTI_CHAR_OPERATOR,
    SINGLE_CHAR_PUNCTUATION,
    SINGLE_QUOTE,
    DOUBLE_QUOTE,
    IDENTIFIER,
    NUMBER,
    FALLBACK,
]


def tokenize(sql: str, dialect: str = "sqlserver") -> List[Token]:
    """
    Tokenize SQL string using TokenPattern definitions.

    Iterates through the input SQL and matches each position against
    TOKEN_PATTERNS in order. The first matching pattern is used.

    Args:
        sql: SQL string to tokenize
        dialect: SQL dialect for keyword detection

    Returns:
        List of Token instances
    """
    if isinstance(dialect, str):
        dialect_obj = get_dialect(dialect)
    else:
        dialect_obj = dialect

    tokens = []
    position = 0

    while position < len(sql):
        matched = False

        # Try each pattern in order
        for token_pattern in TOKEN_PATTERNS:
            match = token_pattern.pattern.match(sql, position)
            if match:
                token_value = match.group(0)
                token_type = get_token_type(token_value, dialect_obj)
                tokens.append(Token(token_value, token_type))
                position = match.end()
                matched = True
                break

        if not matched:
            # Should never happen if FALLBACK pattern is properly defined
            position += 1

    return tokens


class SemanticLevel(Enum):
    """Semantic processing levels for tokenization."""

    BASIC = "basic"
    GROUPED = "grouped"
    STRUCTURED = "structured"
    SEMANTIC = "semantic"


def get_token_type(
    token: str, dialect: Union[str, SQLDialect] = "sqlserver"
) -> TokenType:
    if not token:
        return TokenType.UNKNOWN
    if isinstance(dialect, str):
        dialect_obj = get_dialect(dialect)
    else:
        dialect_obj = dialect
    if token.startswith("--") or (token.startswith("/*") and token.endswith("*/")):
        return TokenType.COMMENT
    if token.isspace():
        if "\n" in token:
            return TokenType.NEWLINE
        return TokenType.WHITESPACE
    if (token.startswith("'") and token.endswith("'")) or (
        token.startswith('"') and token.endswith('"')
    ):
        return TokenType.STRING
    if token.replace(".", "", 1).isdigit():
        return TokenType.NUMBER
    if token in ("<=", ">=", "<>", "!=", "<", ">", "=", "+", "-", "*", "/"):
        return TokenType.OPERATOR
    if token in ("(", ")", ",", ".", ";", "[", "]"):
        return TokenType.PUNCTUATION
    if dialect_obj.is_keyword(token):
        return TokenType.KEYWORD
    id_chars = dialect_obj.identifier_chars
    if id_chars:
        pattern = f"^[A-Za-z_{id_chars}][A-Za-z0-9_{id_chars}]*$"
    else:
        pattern = r"^[A-Za-z_][A-Za-z0-9_]*$"
    if re.match(pattern, token):
        return TokenType.IDENTIFIER
    return TokenType.UNKNOWN


def tokenize_with_types(
    sql: str,
    dialect: Union[str, SQLDialect] = "sqlserver",
    level: Union[str, SemanticLevel] = SemanticLevel.BASIC,
) -> List[Token]:
    """
    Tokenize SQL with type information.

    Args:
        sql: SQL string to tokenize
        dialect: SQL dialect for keyword detection
        level: Semantic processing level (currently delegates to tokenize)

    Returns:
        List of Token instances
    """
    # Currently semantic level processing is done separately
    # This function maintains backward compatibility
    return tokenize(sql, dialect)
