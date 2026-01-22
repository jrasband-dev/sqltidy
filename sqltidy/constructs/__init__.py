"""
SQL construct matching system.

Constructs are patterns that match specific SQL syntax elements.
All constructs (both common and dialect-specific) are now registered in their respective dialect classes.

Example:
    from sqltidy.dialects import get_dialect

    # Get all constructs for a dialect (includes common + dialect-specific)
    dialect = get_dialect('sqlserver')
    all_constructs = dialect.get_constructs()
"""

from .base import (
    Construct,
    register_construct,
    get_pattern,
    get_all_constructs,
    clear_constructs,
    match_constructs,
)

# Note: All constructs (common and dialect-specific) are now registered
# in their respective dialect classes via SQLDialect._register_constructs()
# Common constructs (CTE, WindowFunction, Subquery) are in the base SQLDialect class
# Dialect-specific constructs are in subclasses (e.g., SQLServerDialect, PostgreSQLDialect)

__all__ = [
    # Base infrastructure
    "Construct",
    "register_construct",
    "get_pattern",
    "get_all_constructs",
    "clear_constructs",
    "match_constructs",
]
