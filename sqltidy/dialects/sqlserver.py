"""
SQL Server dialect implementation.
"""

import re
from typing import Set, TYPE_CHECKING
from .base import SQLDialect
from ..constructs.base import Construct

if TYPE_CHECKING:
    pass


class SQLServerDialect(SQLDialect):
    """
    Microsoft SQL Server / T-SQL dialect.
    """

    def _register_token_patterns(self):
        """Register SQL Server specific token patterns."""
        # Import at runtime to avoid circular import
        from ..tokenizer.base import TokenPattern

        # Comments
        self.register_token_pattern(
            TokenPattern(name="Single Line Comment", pattern=re.compile(r"--[^\n]*"))
        )
        self.register_token_pattern(
            TokenPattern(
                name="Multi Line Comment", pattern=re.compile(r"/\*[\s\S]*?\*/")
            )
        )

        # Whitespace
        self.register_token_pattern(
            TokenPattern(name="Newline", pattern=re.compile(r"\n"))
        )
        self.register_token_pattern(
            TokenPattern(name="Whitespace", pattern=re.compile(r"\s+"))
        )

        # Operators
        self.register_token_pattern(
            TokenPattern(name="Multi-char Operator", pattern=re.compile(r"<=|>=|<>|!="))
        )
        self.register_token_pattern(
            TokenPattern(
                name="Single-char Punctuation",
                pattern=re.compile(r"[(),.;\[\]*=<>+-/]"),
            )
        )

        # Strings
        self.register_token_pattern(
            TokenPattern(name="Single-quoted String", pattern=re.compile(r"'[^']*'"))
        )
        self.register_token_pattern(
            TokenPattern(name="Double-quoted String", pattern=re.compile(r'"[^"]*"'))
        )

        # Identifiers and numbers
        self.register_token_pattern(
            TokenPattern(
                name="Identifier", pattern=re.compile(r"[A-Za-z_@#][A-Za-z0-9_@#$]*")
            )
        )
        self.register_token_pattern(
            TokenPattern(name="Number", pattern=re.compile(r"[0-9]+(?:\.[0-9]+)?"))
        )
        self.register_token_pattern(
            TokenPattern(name="Comma", pattern=re.compile(r","))
        )

        # Fallback
        self.register_token_pattern(
            TokenPattern(name="Fallback", pattern=re.compile(r"\S"))
        )

    def _register_constructs(self):
        """Register SQL Server specific constructs."""
        # First register common constructs (CTE, WindowFunction, Subquery)
        super()._register_constructs()

        # Then register SQL Server-specific constructs
        # JOIN_CLAUSE
        self.register_construct(
            Construct(
                name="Join Clause",
                type="clause",
                dialect="sqlserver",
                pattern=re.compile(
                    r"""
            \b(?P<join_type>INNER\s+JOIN|LEFT\s+(?:OUTER\s+)?JOIN|RIGHT\s+(?:OUTER\s+)?JOIN|FULL\s+(?:OUTER\s+)?JOIN|CROSS\s+JOIN)\b\s+  # JOIN type
            (?P<table>\w+(?:\.\w+)?)\s*  # Table name (optionally schema-qualified)
            (?:(?:AS\s+)?(?P<alias>\w+))?\s*  # Optional alias (with or without AS)
            (?:ON\s+(?P<on_condition>[^\n;]+?))?  # Optional ON condition
            (?=\s*(?:WHERE|GROUP|HAVING|ORDER|UNION|EXCEPT|INTERSECT|LIMIT|OFFSET|FETCH|INNER\s+JOIN|LEFT\s+JOIN|RIGHT\s+JOIN|FULL\s+JOIN|CROSS\s+JOIN|;|\n|$)) # Lookahead for clause end
            """,
                    re.VERBOSE | re.IGNORECASE | re.MULTILINE,
                ),
            )
        )

        # CASE_EXPRESSION
        self.register_construct(
            Construct(
                name="CASE_EXPRESSION",
                type="clause",
                dialect="sqlserver",
                pattern=re.compile(
                    r"""
            ^\s*CASE\s+                             # CASE keyword
            (?P<case_body>.*?)                      # Body of CASE expression
            \s*END\s*                              # END keyword
            """,
                    re.VERBOSE | re.IGNORECASE | re.DOTALL | re.MULTILINE,
                ),
            )
        )

        # TRY_CATCH
        self.register_construct(
            Construct(
                name="Try Catch",
                type="clause",
                dialect="sqlserver",
                pattern=re.compile(
                    r"""
            ^\s*BEGIN\s+TRY\s+                     # BEGIN TRY
            (?P<try_block>.*?)                      # TRY block content
            \s*END\s+TRY\s+                        # END TRY
            \s*BEGIN\s+CATCH\s+                    # BEGIN CATCH
            (?P<catch_block>.*?)                    # CATCH block content
            \s*END\s+CATCH\s*                      # END CATCH
            """,
                    re.VERBOSE | re.IGNORECASE | re.DOTALL | re.MULTILINE,
                ),
            )
        )

        # PIVOT
        self.register_construct(
            Construct(
                name="Pivot",
                type="clause",
                dialect="sqlserver",
                pattern=re.compile(
                    r"""
            ^\s*PIVOT\s*                           # PIVOT keyword
            \(\s*(?P<aggregate_function>.*?)\s+FOR\s+(?P<pivot_column>\w+)\s+IN\s*\((?P<values>.*?)\)\s*\) # PIVOT details
            """,
                    re.VERBOSE | re.IGNORECASE | re.MULTILINE,
                ),
            )
        )

        # UNPIVOT
        self.register_construct(
            Construct(
                name="Unpivot",
                type="clause",
                dialect="sqlserver",
                pattern=re.compile(
                    r"""
            ^\s*UNPIVOT\s*                         # UNPIVOT keyword
            \(\s*(?P<value_column>\w+)\s+FOR\s+(?P<pivot_column>\w+)\s+IN\s*\((?P<columns>.*?)\)\s*\) # UNPIVOT details
            """,
                    re.VERBOSE | re.IGNORECASE | re.MULTILINE,
                ),
            )
        )

        # OUTPUT_CLAUSE
        self.register_construct(
            Construct(
                name="Output Clause",
                type="clause",
                dialect="sqlserver",
                pattern=re.compile(
                    r"""
            ^\s*OUTPUT\s+                          # OUTPUT keyword
            (?P<output_list>.*?)                    # List of output columns
            (\s+INTO\s+(?P<into_table>\w+))?       # Optional INTO clause
            """,
                    re.VERBOSE | re.IGNORECASE | re.MULTILINE,
                ),
            )
        )

    @property
    def name(self) -> str:
        return "sqlserver"

    @property
    def ddl_keywords(self) -> Set[str]:
        """DDL (Data Definition Language) keywords."""
        return {
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
            "identity",
            "clustered",
            "nonclustered",
        }

    @property
    def dml_keywords(self) -> Set[str]:
        """DML (Data Manipulation Language) keywords."""
        return {
            "select",
            "insert",
            "update",
            "delete",
            "merge",
            "truncate",
            "into",
            "values",
            "output",
            "from",
            "where",
            "having",
            "group",
            "order",
            "by",
        }

    @property
    def query_keywords(self) -> Set[str]:
        """Query syntax keywords."""
        return {
            "distinct",
            "top",
            "with",
            "as",
            "all",
            "any",
            "some",
            "exists",
            "in",
            "between",
            "like",
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
        }

    @property
    def join_keywords_category(self) -> Set[str]:
        """Join operation keywords."""
        return {
            "join",
            "inner",
            "left",
            "right",
            "full",
            "outer",
            "cross",
            "apply",
            "on",
            "using",
        }

    @property
    def set_operation_keywords(self) -> Set[str]:
        """Set operation keywords."""
        return {
            "union",
            "intersect",
            "except",
        }

    @property
    def transaction_keywords(self) -> Set[str]:
        """Transaction control keywords."""
        return {
            "begin",
            "commit",
            "rollback",
            "transaction",
            "tran",
            "save",
            "savepoint",
        }

    @property
    def data_type_keywords(self) -> Set[str]:
        """Data type keywords."""
        return {
            "int",
            "bigint",
            "smallint",
            "tinyint",
            "bit",
            "decimal",
            "numeric",
            "money",
            "smallmoney",
            "float",
            "real",
            "date",
            "time",
            "datetime",
            "datetime2",
            "smalldatetime",
            "datetimeoffset",
            "char",
            "varchar",
            "nchar",
            "nvarchar",
            "text",
            "ntext",
            "binary",
            "varbinary",
            "image",
            "uniqueidentifier",
            "xml",
            "json",
            "sql_variant",
            "cursor",
            "timestamp",
            "rowversion",
            "hierarchyid",
            "geometry",
            "geography",
        }

    @property
    def function_keywords(self) -> Set[str]:
        """Function-related keywords."""
        return {
            "cast",
            "convert",
            "coalesce",
            "nullif",
            "isnull",
            "try_cast",
            "try_convert",
            "try_parse",
            "parse",
            "count",
            "sum",
            "avg",
            "min",
            "max",
            "stdev",
            "stdevp",
            "var",
            "varp",
            "count_big",
            "grouping",
            "grouping_id",
            "checksum",
            "checksum_agg",
            "string_agg",
        }

    @property
    def control_flow_keywords(self) -> Set[str]:
        """Control flow keywords."""
        return {
            "if",
            "else",
            "while",
            "break",
            "continue",
            "return",
            "goto",
            "waitfor",
            "try",
            "catch",
            "throw",
            "raiserror",
            "print",
        }

    @property
    def cursor_keywords(self) -> Set[str]:
        """Cursor operation keywords."""
        return {
            "declare",
            "open",
            "fetch",
            "next",
            "prior",
            "first",
            "last",
            "absolute",
            "relative",
            "close",
            "deallocate",
        }

    @property
    def advanced_feature_keywords(self) -> Set[str]:
        """Advanced feature keywords."""
        return {
            "pivot",
            "unpivot",
            "for",
            "offset",
            "fetch",
            "rows",
            "only",
            "option",
            "plan",
            "use",
            "exec",
            "execute",
            "sp_executesql",
        }

    @property
    def security_keywords(self) -> Set[str]:
        """Security and permissions keywords."""
        return {
            "grant",
            "deny",
            "revoke",
            "to",
            "public",
            "schema_name",
            "user",
            "login",
            "role",
            "authorization",
        }

    @property
    def backup_restore_keywords(self) -> Set[str]:
        """Backup and restore keywords."""
        return {
            "backup",
            "restore",
            "database",
            "log",
            "file",
            "filegroup",
        }

    @property
    def index_statistics_keywords(self) -> Set[str]:
        """Index and statistics keywords."""
        return {
            "statistics",
            "rebuild",
            "reorganize",
            "update_statistics",
            "disable",
            "enable",
            "resume",
            "pause",
        }

    @property
    def temporal_table_keywords(self) -> Set[str]:
        """Temporal table keywords."""
        return {
            "system_time",
            "period",
            "generated",
            "always",
            "start",
            "end",
            "hidden",
        }

    @property
    def window_function_keywords(self) -> Set[str]:
        """Window function keywords."""
        return {
            "rows",
            "range",
            "unbounded",
            "preceding",
            "following",
            "current",
        }

    @property
    def misc_keywords(self) -> Set[str]:
        """Miscellaneous keywords."""
        return {
            "go",
            "use",
            "set",
            "nocount",
            "on",
            "off",
            "quoted_identifier",
            "ansi_nulls",
            "ansi_padding",
            "ansi_warnings",
            "arithabort",
            "concat_null_yields_null",
            "numeric_roundabort",
            "xact_abort",
            "nolock",
            "readuncommitted",
            "readcommitted",
            "repeatableread",
            "serializable",
            "snapshot",
            "rowlock",
            "paglock",
            "tablock",
            "tablockx",
            "updlock",
            "xlock",
            "holdlock",
            "nowait",
            "readpast",
            "within",
            "contains",
            "freetext",
            "containstable",
            "freetexttable",
            "without",
            "encryption",
            "schemabinding",
            "returns",
            "language",
        }

    @property
    def additional_tsql_keywords(self) -> Set[str]:
        """Additional T-SQL specific keywords."""
        return {
            "openxml",
            "openquery",
            "openrowset",
            "opendatasource",
            "bulk",
            "formatfile",
            "errorfile",
            "maxerrors",
            "firstrow",
            "lastrow",
            "fieldterminator",
            "rowterminator",
            "codepage",
            "datafiletype",
            "batchsize",
            "keepnulls",
            "keepidentity",
            "kilobytes_per_batch",
            "rows_per_batch",
            "order",
            "check_constraints",
            "fire_triggers",
            "tablock",
            "tabblock",
        }

    @property
    def keywords(self) -> Set[str]:
        """Comprehensive SQL Server keywords (combines all sub-categories)."""
        return (
            self.ddl_keywords
            | self.dml_keywords
            | self.query_keywords
            | self.join_keywords_category
            | self.set_operation_keywords
            | self.transaction_keywords
            | self.data_type_keywords
            | self.function_keywords
            | self.control_flow_keywords
            | self.cursor_keywords
            | self.advanced_feature_keywords
            | self.security_keywords
            | self.backup_restore_keywords
            | self.index_statistics_keywords
            | self.temporal_table_keywords
            | self.window_function_keywords
            | self.misc_keywords
            | self.additional_tsql_keywords
        )

    @property
    def data_types(self) -> Set[str]:
        """SQL Server data types."""
        return {
            "int",
            "bigint",
            "smallint",
            "tinyint",
            "bit",
            "decimal",
            "numeric",
            "money",
            "smallmoney",
            "float",
            "real",
            "date",
            "time",
            "datetime",
            "datetime2",
            "smalldatetime",
            "datetimeoffset",
            "char",
            "varchar",
            "nchar",
            "nvarchar",
            "text",
            "ntext",
            "binary",
            "varbinary",
            "image",
            "uniqueidentifier",
            "xml",
            "json",
            "sql_variant",
            "cursor",
            "timestamp",
            "rowversion",
            "hierarchyid",
            "geometry",
            "geography",
        }

    @property
    def functions(self) -> Set[str]:
        """SQL Server built-in functions."""
        return {
            # Aggregate Functions
            "count",
            "sum",
            "avg",
            "min",
            "max",
            "stdev",
            "stdevp",
            "var",
            "varp",
            "count_big",
            "grouping",
            "grouping_id",
            "checksum_agg",
            "string_agg",
            # Conversion Functions
            "cast",
            "convert",
            "try_cast",
            "try_convert",
            "try_parse",
            "parse",
            # Null Functions
            "coalesce",
            "nullif",
            "isnull",
            # Window Functions
            "row_number",
            "rank",
            "dense_rank",
            "ntile",
            "lag",
            "lead",
            "first_value",
            "last_value",
            # Date Functions
            "dateadd",
            "datediff",
            "getdate",
            "sysdatetime",
            "year",
            "month",
            "day",
            "datename",
            "datepart",
            "eomonth",
            "datefromparts",
            "datetimefromparts",
            # String Functions
            "upper",
            "lower",
            "substring",
            "replace",
            "trim",
            "ltrim",
            "rtrim",
            "len",
            "charindex",
            "patindex",
            "concat",
            "concat_ws",
            "format",
            "left",
            "right",
            "reverse",
            "replicate",
            "space",
            "stuff",
            # Math Functions
            "abs",
            "ceiling",
            "floor",
            "round",
            "power",
            "sqrt",
            "square",
            "exp",
            "log",
            "log10",
            "sign",
            "pi",
            "rand",
            "sin",
            "cos",
            "tan",
            # System Functions
            "checksum",
            "newid",
            "scope_identity",
            "ident_current",
        }

    @property
    def ddl_object_keywords(self) -> Set[str]:
        """SQL Server DDL object keywords that precede object definitions."""
        return {
            "table",
            "index",
            "view",
            "procedure",
            "function",
            "trigger",
            "type",
            "schema",
            "database",
            "assembly",
            "certificate",
            "credential",
            "cryptographic",
            "endpoint",
            "event",
            "login",
            "master",
            "message",
            "partition",
            "queue",
            "remote",
            "role",
            "route",
            "rule",
            "sequence",
            "server",
            "service",
            "signature",
            "statistics",
            "symmetric",
            "synonym",
            "user",
            "workload",
            "xml",
            "references",  # FOREIGN KEY ... REFERENCES table(col)
        }

    @property
    def join_keywords(self) -> Set[str]:
        """SQL Server JOIN keywords for various join types."""
        return {
            "join",
            "inner",
            "left",
            "right",
            "full",
            "outer",
            "cross",
            "apply",
            "on",
            "using",
        }

    @property
    def identifier_chars(self) -> str:
        """SQL Server allows @, #, and $ in identifiers."""
        return "@#$"

    @property
    def quote_chars(self) -> dict:
        """SQL Server uses square brackets for identifiers, single quotes for strings."""
        return {
            "identifier": "[",  # Also supports double quotes with QUOTED_IDENTIFIER ON
            "string": "'",
        }

    @property
    def comment_styles(self) -> list:
        """SQL Server supports -- and /* */ comments."""
        return ["--", "/*"]
