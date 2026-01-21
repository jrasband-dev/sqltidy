# tokenizer/core.py
"""
Core tokenization logic and types.
"""
import re
from typing import Union, NamedTuple
from enum import Enum
from ..dialects import get_dialect, SQLDialect
from .types import TokenType



class Token(NamedTuple):
    value: str
    type: TokenType

def tokenize(sql: str, dialect: str = "sqlserver"):
    if isinstance(dialect, str):
        dialect_obj = get_dialect(dialect)
    else:
        dialect_obj = dialect
    tokens = []
    for groups in TOKEN_RE.findall(sql):
        for t in groups:
            if t == "":
                continue
            if t.isspace():
                if "\n" in t:
                    tokens.append(Token("\n", TokenType.NEWLINE))
                else:
                    tokens.append(Token(" ", TokenType.WHITESPACE))
            else:
                token_type = get_token_type(t, dialect_obj)
                tokens.append(Token(t, token_type))
        
            break

    return tokens
    

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
    ([A-Za-z_@#][A-Za-z0-9_@#$]*)   |  # identifiers/keywords
    ([0-9]+(?:\.[0-9]+)?)           |  # numbers
    (\S)                               # fallback: any other non-space
    """,
    re.VERBOSE,
)

class SemanticLevel(Enum):
    BASIC = "basic"
    GROUPED = "grouped"
    STRUCTURED = "structured"
    SEMANTIC = "semantic"

def get_token_type(token: str, dialect: Union[str, SQLDialect] = "sqlserver") -> TokenType:
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
):
    if isinstance(dialect, str):
        dialect_obj = get_dialect(dialect)
    else:
        dialect_obj = dialect
    if isinstance(level, str):
        try:
            level = SemanticLevel(level.lower())
        except ValueError:
            level = SemanticLevel.BASIC
    tokens = []
    for groups in TOKEN_RE.findall(sql):
        for t in groups:
            if t == "":
                continue
            if t.isspace():
                if "\n" in t:
                    tokens.append(Token("\n", TokenType.NEWLINE))
                else:
                    tokens.append(Token(" ", TokenType.WHITESPACE))
            else:
                token_type = get_token_type(t, dialect_obj)
                tokens.append(Token(t, token_type))
            break
    return tokens
