import re
from . import Construct, register_construct

JOIN_CLAUSE = Construct(
    name="Join Clause",
    dialect="sqlserver",
    pattern=re.compile(r"""
    \b(?P<join_type>INNER\s+JOIN|LEFT\s+(?:OUTER\s+)?JOIN|RIGHT\s+(?:OUTER\s+)?JOIN|FULL\s+(?:OUTER\s+)?JOIN|CROSS\s+JOIN)\b\s+  # JOIN type
    (?P<table>\w+(?:\.\w+)?)\s*  # Table name (optionally schema-qualified)
    (?:(?:AS\s+)?(?P<alias>\w+))?\s*  # Optional alias (with or without AS)
    (?:ON\s+(?P<on_condition>[^\n;]+?))?  # Optional ON condition
    (?=\s*(?:WHERE|GROUP|HAVING|ORDER|UNION|EXCEPT|INTERSECT|LIMIT|OFFSET|FETCH|INNER\s+JOIN|LEFT\s+JOIN|RIGHT\s+JOIN|FULL\s+JOIN|CROSS\s+JOIN|;|\n|$)) # Lookahead for clause end
    """, re.VERBOSE | re.IGNORECASE | re.MULTILINE)
)

CASE_EXPRESSION = Construct(
    name="Case Expression",
    dialect="sqlserver",
    pattern=re.compile(r"""
    ^\s*CASE\s+                             # CASE keyword
    (?P<case_body>.*?)                      # Body of CASE expression
    \s*END\s*                              # END keyword
    """, re.VERBOSE | re.IGNORECASE | re.DOTALL | re.MULTILINE)
)

TRY_CATCH = Construct(
    name="Try Catch",
    dialect="sqlserver",
    pattern=re.compile(r"""
    ^\s*BEGIN\s+TRY\s+                     # BEGIN TRY
    (?P<try_block>.*?)                      # TRY block content
    \s*END\s+TRY\s+                        # END TRY
    \s*BEGIN\s+CATCH\s+                    # BEGIN CATCH
    (?P<catch_block>.*?)                    # CATCH block content
    \s*END\s+CATCH\s*                      # END CATCH
    """, re.VERBOSE | re.IGNORECASE | re.DOTALL | re.MULTILINE)
)

PIVOT = Construct(
    name="Pivot",
    dialect="sqlserver",
    pattern=re.compile(r"""
    ^\s*PIVOT\s*                           # PIVOT keyword
    \(\s*(?P<aggregate_function>.*?)\s+FOR\s+(?P<pivot_column>\w+)\s+IN\s*\((?P<values>.*?)\)\s*\) # PIVOT details
    """, re.VERBOSE | re.IGNORECASE | re.MULTILINE)
)

UNPIVOT = Construct(
    name="Unpivot",
    dialect="sqlserver",
    pattern=re.compile(r"""
    ^\s*UNPIVOT\s*                         # UNPIVOT keyword
    \(\s*(?P<value_column>\w+)\s+FOR\s+(?P<pivot_column>\w+)\s+IN\s*\((?P<columns>.*?)\)\s*\) # UNPIVOT details
    """, re.VERBOSE | re.IGNORECASE | re.MULTILINE)
)

OUTPUT_CLAUSE = Construct(
    name="Output Clause",
    dialect="sqlserver",
    pattern=re.compile(r"""
    ^\s*OUTPUT\s+                          # OUTPUT keyword
    (?P<output_list>.*?)                    # List of output columns
    (\s+INTO\s+(?P<into_table>\w+))?       # Optional INTO clause
    """, re.VERBOSE | re.IGNORECASE | re.MULTILINE)
)

# Register all constructs
for construct in [JOIN_CLAUSE, CASE_EXPRESSION, TRY_CATCH, PIVOT, UNPIVOT, OUTPUT_CLAUSE]:
    register_construct(construct)

__all__ = [
    "JOIN_CLAUSE",
    "CASE_EXPRESSION",
    "TRY_CATCH",
    "PIVOT",
    "UNPIVOT",
    "OUTPUT_CLAUSE",
]