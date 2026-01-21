# tokenizer/__init__.py
"""
Tokenizer package: exposes main API for tokenization and grouping.
All functionality is now consolidated in base.py.
"""

from .base import (
    # Core tokenization
    tokenize,
    tokenize_with_types,
    get_token_type,
    # Types and classes
    Token,
    TokenType,
    TokenGroup,
    GroupType,
    SemanticLevel,
    TokenPattern,
    # Grouping functions
    group_parentheses,
    group_by_statements,
    group_by_clauses,
    group_tokens,
    # Utility functions
    print_token_tree,
    is_keyword,
    # Token patterns
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

__all__ = [
    # Core tokenization
    "tokenize",
    "tokenize_with_types",
    "get_token_type",
    # Types and classes
    "Token",
    "TokenType",
    "TokenGroup",
    "GroupType",
    "SemanticLevel",
    "TokenPattern",
    # Grouping functions
    "group_parentheses",
    "group_by_statements",
    "group_by_clauses",
    "group_tokens",
    # Utility functions
    "print_token_tree",
    "is_keyword",
    # Token patterns
    "TOKEN_PATTERNS",
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
