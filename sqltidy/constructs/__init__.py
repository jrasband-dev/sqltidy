"""
Declarative, reusable, dialect-aware pattern system for SQL parsing.

Patterns are tiny building blocks that can match and group SQL tokens.
They are composed into larger patterns to recognize complex SQL constructs.

Example:
    from sqltidy.patterns import Pattern, MatchContext
    from sqltidy.patterns.tsql import CaseExpressionPattern

    construct = CaseExpressionConstruct()
    matches = construct.match(context)
"""

from .base import (
    Construct,
    register_construct,
    get_pattern,
    get_all_constructs,
    clear_constructs,
)

from .general import (
    CTE,
    WINDOW_FUNCTION,
    SUBQUERY,
)

from .postgres import (
    # ARRAY,
    RETURNING,
    JSON_OPERATOR,
    ON_CONFLICT,
)

from .sqlserver import (
    JOIN_CLAUSE,
    CASE_EXPRESSION,
    TRY_CATCH,
    PIVOT,
    UNPIVOT,
    OUTPUT_CLAUSE,
)

__all__ = [
    # Base
    "Construct",
    "register_construct",
    "get_pattern",
    "get_all_constructs",
    "clear_constructs",
    # General Constructs
    "CTE",
    "WINDOW_FUNCTION",
    "SUBQUERY",
    # PostgreSQL Constructs
    "ARRAY",
    "RETURNING",
    "JSON_OPERATOR",
    "ON_CONFLICT",
    # SQL Server Constructs
    "JOIN_CLAUSE",
    "CASE_EXPRESSION",
    "TRY_CATCH",
    "PIVOT",
    "UNPIVOT",
    "OUTPUT_CLAUSE",

]
