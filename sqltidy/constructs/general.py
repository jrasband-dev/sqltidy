import re
from . import Construct, register_construct


CTE = Construct(
    name="CTE",
    dialect="all",
    pattern=re.compile(r"""
    ^\s*WITH\s+                # WITH keyword at start
    (?P<cte_name>\w+)          # CTE name (identifier)
    (?:\s*\((?P<columns>[^)]*)\))?  # Optional column list
    \s+AS\s*                   # AS keyword
    \(\s*                      # Opening parenthesis for subquery
    (?P<subquery>.*?)          # Subquery (non-greedy)
    \)\s*                      # Closing parenthesis
    """, re.VERBOSE | re.IGNORECASE | re.DOTALL | re.MULTILINE)
)

WINDOW_FUNCTION = Construct(
    name="WindowFunction",
    dialect="all",
    pattern=re.compile(r"""
    ^(?P<function_name>\w+)\s*     # Function name
    \(\s*(?P<arguments>.*?)\s*\)\s* # Function arguments
    OVER\s*                        # OVER keyword
    \(\s*(?P<over_clause>.*?)\s*\)  # OVER clause content
    """, re.VERBOSE | re.IGNORECASE | re.DOTALL | re.MULTILINE)
)

SUBQUERY = Construct(
    name="Subquery",
    dialect="all",
    pattern=re.compile(r"""
    ^\(\s*                         # Opening parenthesis
    (?P<select_statement>SELECT\s+.*?) # SELECT statement
    \s*\)\s*                       # Closing parenthesis
    (AS\s+(?P<alias>\w+))?         # Optional alias
    """, re.VERBOSE | re.IGNORECASE | re.DOTALL | re.MULTILINE)
)

# Register all constructs
for construct in [CTE, WINDOW_FUNCTION, SUBQUERY]:
    register_construct(construct)
