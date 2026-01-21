# tokenizer/__init__.py
"""
Tokenizer package init: exposes main API for tokenization and grouping.
"""
from .base import (
    tokenize_with_types, 
    TokenType, 
    Token, 
    SemanticLevel, 
    tokenize,
    get_token_type,
    TokenPattern,
    TOKEN_PATTERNS,
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
    COMMA,
    FALLBACK,
)
from .grouping import group_parentheses, group_by_statements, group_by_clauses, group_tokens, TokenGroup, GroupType
from .patterns import apply_patterns

__all__ = [
    "tokenize",
    "tokenize_with_types",
    "get_token_type",
    "TokenType",
    "Token",
    "TokenPattern",
    "TOKEN_PATTERNS",
    "SemanticLevel",
    "TokenGroup",
    "GroupType",
    "group_parentheses",
    "group_by_statements",
    "group_by_clauses",
    "group_tokens",
    "apply_patterns",
    # Token patterns
    "SINGLE_LINE_COMMENT",
    "MULTI_LINE_COMMENT",
    "NEWLINE",
    "WHITESPACE",
    "MULTI_CHAR_OPERATOR",
    "SINGLE_CHAR_PUNCTUATION",
    "SINGLE_QUOTE",
    "DOUBLE_QUOTE",
    "IDENTIFIER",
    "NUMBER",
    "COMMA",
    "FALLBACK",
]
