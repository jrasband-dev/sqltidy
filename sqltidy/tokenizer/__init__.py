# tokenizer/__init__.py
"""
Tokenizer package: exposes main API for tokenization and grouping.
All functionality is now consolidated in base.py.

Note: Token patterns are now defined in dialect classes via dialect.get_token_patterns().
The global TOKEN_PATTERNS list and individual pattern constants have been removed.
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
]
