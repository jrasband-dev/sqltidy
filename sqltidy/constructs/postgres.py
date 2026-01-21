"""
PostgreSQL specific patterns.

These patterns handle PostgreSQL-specific syntax and constructs.
"""

import re
from . import Construct, register_construct


# ARRAY = Construct(
#     name="Array", 
#     dialect="postgresql",
#     pattern=re.compile(r"""
#     ^\s*ARRAY\s*                           # ARRAY keyword)
#     (\[.*?\]|\(.*?\))                      # Array content in [] or ()
#     """, re.VERBOSE | re.IGNORECASE)
# )

RETURNING = Construct(
    name="Returning Clause",
    dialect="postgresql",
    pattern=re.compile(r"""
    ^\s*RETURNING\s+                       # RETURNING keyword
    (?P<returning_list>.*?)                 # List of returning columns
    """, re.VERBOSE | re.IGNORECASE | re.MULTILINE)
)

JSON_OPERATOR = Construct(
    name="Json Operator",
    dialect="postgresql",
    pattern=re.compile(r"""
    ^\s*(?P<left_operand>\w+)\s*           # Left operand (column name)
    (?P<operator>->|->>|\#>|\#>>|@>|<@|\?|\?\||\?\&|\|\|)\s*  # JSON operators
    (?P<right_operand>.+)                   # Right operand (key, path, etc.)
    """, re.VERBOSE | re.IGNORECASE | re.MULTILINE)
)

ON_CONFLICT = Construct(
    name="On Conflict Clause",
    dialect="postgresql",
    pattern=re.compile(r"""
    ^\s*ON\s+CONFLICT\s*                   # ON CONFLICT keywords
    (\(.*?\))?                             # Optional conflict target
    \s*DO\s+                               # DO keyword
    (NOTHING|UPDATE\s+SET\s+.*?)           # Action: NOTHING or UPDATE SET ...
    """, re.VERBOSE | re.IGNORECASE | re.DOTALL | re.MULTILINE)
)

# Register all constructs
for construct in [RETURNING, JSON_OPERATOR, ON_CONFLICT]:
    register_construct(construct)

__all__ = [
    "RETURNING",
    "JSON_OPERATOR",
    "ON_CONFLICT",
]
