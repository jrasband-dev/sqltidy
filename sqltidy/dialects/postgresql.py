"""
PostgreSQL dialect implementation.
"""

import re
from typing import Set, TYPE_CHECKING
from .base import SQLDialect
from ..constructs.base import Construct

if TYPE_CHECKING:
    from ..tokenizer.base import TokenPattern


class PostgreSQLDialect(SQLDialect):
    """
    PostgreSQL dialect.

    Includes comprehensive PostgreSQL keyword support with 250+ keywords covering:
    - DDL/DML operations
    - Query syntax
    - Data types (including advanced types like JSON, ARRAY, HSTORE)
    - Functions (string, date, aggregate, window, etc.)
    - PostgreSQL-specific features (RETURNING, LISTEN/NOTIFY, etc.)
    """

    def _register_token_patterns(self):
        """Register PostgreSQL specific token patterns."""
        # Import at runtime to avoid circular import
        from ..tokenizer.base import TokenPattern
        
        # Comments
        self.register_token_pattern(TokenPattern(
            name="Single Line Comment",
            pattern=re.compile(r"--[^\n]*")
        ))
        self.register_token_pattern(TokenPattern(
            name="Multi Line Comment",
            pattern=re.compile(r"/\*[\s\S]*?\*/")
        ))
        
        # Whitespace
        self.register_token_pattern(TokenPattern(
            name="Newline",
            pattern=re.compile(r"\n")
        ))
        self.register_token_pattern(TokenPattern(
            name="Whitespace",
            pattern=re.compile(r"\s+")
        ))
        
        # Operators
        self.register_token_pattern(TokenPattern(
            name="Multi-char Operator",
            pattern=re.compile(r"<=|>=|<>|!=")
        ))
        self.register_token_pattern(TokenPattern(
            name="Single-char Punctuation",
            pattern=re.compile(r"[(),.;\[\]*=<>+-/]")
        ))
        
        # Strings
        self.register_token_pattern(TokenPattern(
            name="Single-quoted String",
            pattern=re.compile(r"'[^']*'")
        ))
        self.register_token_pattern(TokenPattern(
            name="Double-quoted String",
            pattern=re.compile(r'"[^"]*"')
        ))
        
        # Identifiers and numbers
        self.register_token_pattern(TokenPattern(
            name="Identifier",
            pattern=re.compile(r"[A-Za-z_$][A-Za-z0-9_$]*")  # PostgreSQL allows $
        ))
        self.register_token_pattern(TokenPattern(
            name="Number",
            pattern=re.compile(r"[0-9]+(?:\.[0-9]+)?")
        ))
        self.register_token_pattern(TokenPattern(
            name="Comma",
            pattern=re.compile(r",")
        ))
        
        # Fallback
        self.register_token_pattern(TokenPattern(
            name="Fallback",
            pattern=re.compile(r"\S")
        ))

    def _register_constructs(self):
        """Register PostgreSQL specific constructs."""
        # First register common constructs (CTE, WindowFunction, Subquery)
        super()._register_constructs()
        
        # Then register PostgreSQL-specific constructs
        # RETURNING clause
        self.register_construct(Construct(
            name="Returning Clause",
            type="clause",
            dialect="postgresql",
            pattern=re.compile(
                r"""
            ^\s*RETURNING\s+                       # RETURNING keyword
            (?P<returning_list>.*?)                 # List of returning columns
            """,
                re.VERBOSE | re.IGNORECASE | re.MULTILINE,
            ),
        ))

        # JSON operators
        self.register_construct(Construct(
            name="Json Operator",
            type="clause",
            dialect="postgresql",
            pattern=re.compile(
                r"""
            ^\s*(?P<left_operand>\w+)\s*           # Left operand (column name)
            (?P<operator>->|->>|\#>|\#>>|@>|<@|\?|\?\||\?\&|\|\|)\s*  # JSON operators
            (?P<right_operand>.+)                   # Right operand (key, path, etc.)
            """,
                re.VERBOSE | re.IGNORECASE | re.MULTILINE,
            ),
        ))

        # ON CONFLICT clause
        self.register_construct(Construct(
            name="On Conflict Clause",
            type="clause",
            dialect="postgresql",
            pattern=re.compile(
                r"""
            ^\s*ON\s+CONFLICT\s*                   # ON CONFLICT keywords
            (\(.*?\))?                             # Optional conflict target
            \s*DO\s+                               # DO keyword
            (NOTHING|UPDATE\s+SET\s+.*?)           # Action: NOTHING or UPDATE SET ...
            """,
                re.VERBOSE | re.IGNORECASE | re.DOTALL | re.MULTILINE,
            ),
        ))

    @property
    def name(self) -> str:
        return "postgresql"

    @property
    def keywords(self) -> Set[str]:
        """Comprehensive PostgreSQL keywords."""
        return {
            # DDL Keywords
            "add",
            "alter",
            "column",
            "constraint",
            "create",
            "database",
            "drop",
            "index",
            "schema",
            "table",
            "view",
            "sequence",
            "procedure",
            "function",
            "trigger",
            "default",
            "check",
            "unique",
            "primary",
            "foreign",
            "key",
            "references",
            "cascade",
            "set",
            "null",
            "not",
            "serial",
            "bigserial",
            # DML Keywords
            "select",
            "insert",
            "update",
            "delete",
            "merge",
            "truncate",
            "into",
            "values",
            "returning",
            "from",
            "where",
            "having",
            "group",
            "order",
            "by",
            # Query Keywords
            "distinct",
            "limit",
            "offset",
            "with",
            "as",
            "all",
            "any",
            "some",
            "exists",
            "in",
            "between",
            "like",
            "ilike",
            "similar",
            "is",
            "and",
            "or",
            "not",
            "case",
            "when",
            "then",
            "else",
            "end",
            "over",
            "partition",
            "row_number",
            "rank",
            "dense_rank",
            "ntile",
            "lag",
            "lead",
            "first_value",
            "last_value",
            # Join Keywords
            "join",
            "inner",
            "left",
            "right",
            "full",
            "outer",
            "cross",
            "natural",
            "on",
            "using",
            # Set Operations
            "union",
            "intersect",
            "except",
            # Transaction Keywords
            "begin",
            "commit",
            "rollback",
            "transaction",
            "savepoint",
            "release",
            "start",
            "work",
            "isolation",
            "level",
            "read",
            "write",
            "only",
            "serializable",
            "repeatable",
            "committed",
            "uncommitted",
            # Data Types
            "integer",
            "int",
            "smallint",
            "bigint",
            "decimal",
            "numeric",
            "real",
            "double",
            "precision",
            "float",
            "serial",
            "bigserial",
            "smallserial",
            "money",
            "char",
            "varchar",
            "character",
            "varying",
            "text",
            "bytea",
            "timestamp",
            "timestamptz",
            "date",
            "time",
            "timetz",
            "interval",
            "boolean",
            "bool",
            "bit",
            "varbit",
            "uuid",
            "xml",
            "json",
            "jsonb",
            "array",
            "hstore",
            "inet",
            "cidr",
            "macaddr",
            "tsvector",
            "tsquery",
            "point",
            "line",
            "lseg",
            "box",
            "path",
            "polygon",
            "circle",
            # Aggregate Functions
            "count",
            "sum",
            "avg",
            "min",
            "max",
            "array_agg",
            "string_agg",
            "json_agg",
            "jsonb_agg",
            "json_object_agg",
            "jsonb_object_agg",
            "every",
            "bool_and",
            "bool_or",
            "stddev",
            "variance",
            "corr",
            "covar_pop",
            # Conversion Functions
            "cast",
            "convert",
            "to_char",
            "to_date",
            "to_timestamp",
            "to_number",
            # Null Functions
            "coalesce",
            "nullif",
            "greatest",
            "least",
            # Window Functions
            "row_number",
            "rank",
            "dense_rank",
            "ntile",
            "lag",
            "lead",
            "first_value",
            "last_value",
            "nth_value",
            "cume_dist",
            "percent_rank",
            # String Functions
            "upper",
            "lower",
            "substring",
            "replace",
            "trim",
            "ltrim",
            "rtrim",
            "length",
            "char_length",
            "octet_length",
            "position",
            "concat",
            "concat_ws",
            "left",
            "right",
            "reverse",
            "repeat",
            "split_part",
            "regexp_replace",
            "regexp_match",
            "regexp_split_to_array",
            "regexp_split_to_table",
            # Date/Time Functions
            "now",
            "current_date",
            "current_time",
            "current_timestamp",
            "localtime",
            "localtimestamp",
            "age",
            "date_part",
            "date_trunc",
            "extract",
            "make_date",
            "make_time",
            "make_timestamp",
            # Math Functions
            "abs",
            "ceil",
            "ceiling",
            "floor",
            "round",
            "trunc",
            "power",
            "sqrt",
            "exp",
            "ln",
            "log",
            "log10",
            "pi",
            "random",
            "setseed",
            "div",
            "mod",
            "sin",
            "cos",
            "tan",
            "asin",
            "acos",
            "atan",
            "atan2",
            # JSON Functions
            "json_build_array",
            "json_build_object",
            "json_extract_path",
            "json_extract_path_text",
            "json_array_elements",
            "json_array_elements_text",
            "json_object_keys",
            "json_populate_record",
            "json_populate_recordset",
            "jsonb_set",
            "jsonb_insert",
            "jsonb_pretty",
            # Array Functions
            "array_append",
            "array_cat",
            "array_dims",
            "array_length",
            "array_lower",
            "array_upper",
            "array_prepend",
            "array_remove",
            "array_replace",
            "unnest",
            # Control Flow
            "if",
            "case",
            "when",
            "then",
            "else",
            "end",
            "loop",
            "while",
            "for",
            "foreach",
            "continue",
            "exit",
            "return",
            "raise",
            "assert",
            # Advanced Features
            "lateral",
            "tablesample",
            "fetch",
            "first",
            "next",
            "rows",
            "only",
            "window",
            "materialized",
            "recursive",
            "ordinality",
            # Security & Permissions
            "grant",
            "revoke",
            "to",
            "public",
            "usage",
            "execute",
            "all",
            "privileges",
            "role",
            "user",
            "group",
            "owner",
            "authorization",
            # PostgreSQL-Specific
            "listen",
            "notify",
            "unlisten",
            "explain",
            "analyze",
            "vacuum",
            "cluster",
            "reindex",
            "copy",
            "do",
            "language",
            "plpgsql",
            "sql",
            "perform",
            "found",
            "get",
            "diagnostics",
            "foreach",
            "slice",
            # Operators as keywords
            "overlaps",
            "similar",
            "isnull",
            "notnull",
            # Lock modes
            "lock",
            "share",
            "exclusive",
            "access",
            "nowait",
            # Storage
            "tablespace",
            "unlogged",
            "temporary",
            "temp",
            # Misc
            "prepare",
            "execute",
            "deallocate",
            "declare",
            "cursor",
            "fetch",
            "move",
            "close",
            "comment",
            "statistics",
            "analyze",
            "checkpoint",
            "discard",
            "load",
            "reset",
            "show",
            "set",
        }

    @property
    def data_types(self) -> Set[str]:
        """PostgreSQL data types."""
        return {
            # Numeric Types
            "integer",
            "int",
            "smallint",
            "bigint",
            "decimal",
            "numeric",
            "real",
            "double",
            "precision",
            "float",
            "serial",
            "bigserial",
            "smallserial",
            "money",
            # Character Types
            "char",
            "varchar",
            "character",
            "varying",
            "text",
            # Binary Data
            "bytea",
            # Date/Time Types
            "timestamp",
            "timestamptz",
            "date",
            "time",
            "timetz",
            "interval",
            # Boolean
            "boolean",
            "bool",
            # Bit String
            "bit",
            "varbit",
            # UUID
            "uuid",
            # JSON
            "json",
            "jsonb",
            # Array
            "array",
            # Network Address Types
            "inet",
            "cidr",
            "macaddr",
            "macaddr8",
            # Text Search
            "tsvector",
            "tsquery",
            # XML
            "xml",
            # Geometric Types
            "point",
            "line",
            "lseg",
            "box",
            "path",
            "polygon",
            "circle",
            # Range Types
            "int4range",
            "int8range",
            "numrange",
            "tsrange",
            "tstzrange",
            "daterange",
            # Object Identifier Types
            "oid",
            "regclass",
            "regproc",
            "regprocedure",
            "regoper",
            "regoperator",
            "regconfig",
            "regdictionary",
            # Special Types
            "hstore",
            "ltree",
            "cube",
            "seg",
            "isn",
        }

    @property
    def functions(self) -> Set[str]:
        """PostgreSQL built-in functions."""
        return {
            # Aggregate Functions
            "count",
            "sum",
            "avg",
            "min",
            "max",
            "array_agg",
            "string_agg",
            "json_agg",
            "jsonb_agg",
            "json_object_agg",
            "jsonb_object_agg",
            "every",
            "bool_and",
            "bool_or",
            "stddev",
            "variance",
            # Conversion Functions
            "cast",
            "convert",
            "to_char",
            "to_date",
            "to_timestamp",
            "to_number",
            # Null Functions
            "coalesce",
            "nullif",
            "greatest",
            "least",
            # Window Functions
            "row_number",
            "rank",
            "dense_rank",
            "ntile",
            "lag",
            "lead",
            "first_value",
            "last_value",
            "nth_value",
            "cume_dist",
            "percent_rank",
            # String Functions
            "upper",
            "lower",
            "substring",
            "replace",
            "trim",
            "ltrim",
            "rtrim",
            "length",
            "char_length",
            "position",
            "concat",
            "concat_ws",
            "left",
            "right",
            "reverse",
            "repeat",
            "split_part",
            # Date/Time Functions
            "now",
            "current_date",
            "current_time",
            "current_timestamp",
            "age",
            "date_part",
            "date_trunc",
            "extract",
            # Math Functions
            "abs",
            "ceil",
            "ceiling",
            "floor",
            "round",
            "trunc",
            "power",
            "sqrt",
            "exp",
            "ln",
            "log",
            "pi",
            "random",
            # JSON Functions
            "json_build_array",
            "json_build_object",
            "jsonb_set",
            "jsonb_insert",
            # Array Functions
            "array_append",
            "array_cat",
            "array_length",
            "unnest",
            # System Functions
            "version",
            "current_user",
            "current_schema",
            "current_database",
            "pg_backend_pid",
            "pg_sleep",
        }

    @property
    def identifier_chars(self) -> str:
        """PostgreSQL allows $ in identifiers."""
        return "$"

    @property
    def quote_chars(self) -> dict:
        """PostgreSQL uses double quotes for identifiers, single quotes for strings."""
        return {"identifier": '"', "string": "'"}

    @property
    def comment_styles(self) -> list:
        """PostgreSQL supports -- and /* */ comments."""
        return ["--", "/*"]
