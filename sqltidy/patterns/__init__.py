"""
Declarative, reusable, dialect-aware pattern system for SQL parsing.

Patterns are tiny building blocks that can match and group SQL tokens.
They are composed into larger patterns to recognize complex SQL constructs.

Example:
    from sqltidy.patterns import Pattern, MatchContext
    from sqltidy.patterns.tsql import CaseExpressionPattern

    pattern = CaseExpressionPattern()
    matches = pattern.match(context)
"""

from .base import (
    Pattern,
    MatchResult,
    MatchContext,
    PatternRegistry,
    register_pattern,
    get_pattern,
    get_all_patterns,
    clear_patterns,
)

__all__ = [
    "Pattern",
    "MatchResult",
    "MatchContext",
    "PatternRegistry",
    "register_pattern",
    "get_pattern",
    "get_all_patterns",
    "clear_patterns",
]
