"""
SQL Server dialect implementation.
"""

from typing import Set
from .base import SQLDialect


class SQLServerDialect(SQLDialect):
    """
    Microsoft SQL Server / T-SQL dialect.
    """

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

    def _register_patterns(self):
        """Register T-SQL specific patterns."""
        from ..patterns.tsql import (
            JoinClausePattern,
            CaseExpressionPattern,
            TrycatchPattern,
            PivotUnpivotPattern,
            OutputClausePattern,
        )

        self.register_pattern(JoinClausePattern())
        self.register_pattern(CaseExpressionPattern())
        self.register_pattern(TrycatchPattern())
        self.register_pattern(PivotUnpivotPattern())
        self.register_pattern(OutputClausePattern())
