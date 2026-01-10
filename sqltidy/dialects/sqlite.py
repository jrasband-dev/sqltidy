"""
SQLite dialect support.

This module provides SQLite-specific SQL dialect support including:
- SQLite keywords
- SQLite data types (simplified type system)
- SQLite built-in functions
- SQLite-specific features (PRAGMA, AUTOINCREMENT, etc.)
"""

from typing import Dict, List, Set
from .base import SQLDialect


class SQLiteDialect(SQLDialect):
    """SQLite database dialect."""

    @property
    def name(self) -> str:
        return "sqlite"

    @property
    def keywords(self) -> Set[str]:
        """SQLite keywords."""
        # Convert all keywords to lowercase for case-insensitive matching
        return {
            kw.lower()
            for kw in {
                # Core SQL keywords
                "SELECT",
                "FROM",
                "WHERE",
                "INSERT",
                "UPDATE",
                "DELETE",
                "CREATE",
                "ALTER",
                "DROP",
                "TRUNCATE",
                "RENAME",
                "TABLE",
                "VIEW",
                "INDEX",
                "TRIGGER",
                "VIRTUAL",
                # Join keywords
                "JOIN",
                "INNER",
                "LEFT",
                "RIGHT",
                "FULL",
                "OUTER",
                "CROSS",
                "NATURAL",
                "ON",
                "USING",
                # Set operations
                "UNION",
                "INTERSECT",
                "EXCEPT",
                # Clauses
                "DISTINCT",
                "ALL",
                "AS",
                "INTO",
                "VALUES",
                "SET",
                "ORDER",
                "BY",
                "GROUP",
                "HAVING",
                "LIMIT",
                "OFFSET",
                "ASC",
                "DESC",
                # Conditional
                "CASE",
                "WHEN",
                "THEN",
                "ELSE",
                "END",
                # Logical operators
                "AND",
                "OR",
                "NOT",
                "IN",
                "EXISTS",
                "BETWEEN",
                "LIKE",
                "IS",
                "NULL",
                "GLOB",
                "MATCH",
                "REGEXP",
                # Constraints
                "CONSTRAINT",
                "PRIMARY",
                "KEY",
                "FOREIGN",
                "REFERENCES",
                "UNIQUE",
                "CHECK",
                "DEFAULT",
                "NOT",
                "AUTOINCREMENT",
                "COLLATE",
                # Data types (SQLite has dynamic typing, but these are type affinities)
                "INTEGER",
                "INT",
                "TINYINT",
                "SMALLINT",
                "MEDIUMINT",
                "BIGINT",
                "UNSIGNED",
                "BIG",
                "INT2",
                "INT8",
                "TEXT",
                "CHARACTER",
                "VARCHAR",
                "VARYING",
                "NCHAR",
                "NATIVE",
                "NVARCHAR",
                "CLOB",
                "REAL",
                "DOUBLE",
                "PRECISION",
                "FLOAT",
                "NUMERIC",
                "DECIMAL",
                "BOOLEAN",
                "DATE",
                "DATETIME",
                "BLOB",
                # Transaction control
                "BEGIN",
                "COMMIT",
                "ROLLBACK",
                "SAVEPOINT",
                "RELEASE",
                "TRANSACTION",
                "DEFERRED",
                "IMMEDIATE",
                "EXCLUSIVE",
                # SQLite-specific keywords
                "PRAGMA",
                "DATABASE",
                "SCHEMA",
                "ATTACH",
                "DETACH",
                "VACUUM",
                "ANALYZE",
                "REINDEX",
                "EXPLAIN",
                "QUERY",
                "PLAN",
                # Table options
                "TEMPORARY",
                "TEMP",
                "IF",
                "ELSE",
                "ELSIF",
                "WITHOUT",
                "ROWID",
                # Column options
                "GENERATED",
                "ALWAYS",
                "STORED",
                "VIRTUAL",
                # Conflict resolution
                "ON",
                "CONFLICT",
                "ROLLBACK",
                "ABORT",
                "FAIL",
                "IGNORE",
                "REPLACE",
                # Window functions
                "OVER",
                "PARTITION",
                "ROWS",
                "RANGE",
                "UNBOUNDED",
                "PRECEDING",
                "FOLLOWING",
                "CURRENT",
                "ROW",
                "GROUPS",
                "EXCLUDE",
                "TIES",
                "OTHERS",
                "NO",
                # CTEs
                "WITH",
                "RECURSIVE",
                # Cast and type conversion
                "CAST",
                "TYPEOF",
                # Aggregate functions
                "COUNT",
                "SUM",
                "AVG",
                "MIN",
                "MAX",
                "TOTAL",
                "GROUP_CONCAT",
                # Filtering
                "FILTER",
                # Other keywords
                "INDEXED",
                "BY",
                "ESCAPE",
                "ISNULL",
                "NOTNULL",
                "RAISE",
                "EACH",
                "FOR",
                "INSTEAD",
                "OF",
                "BEFORE",
                "AFTER",
                "OLD",
                "NEW",
                "RETURNING",
            }
        }

    @property
    def data_types(self) -> Set[str]:
        """
        SQLite data types.

        SQLite uses a dynamic type system with type affinities:
        - INTEGER
        - TEXT
        - REAL
        - BLOB
        - NUMERIC
        """
        # Convert all data types to lowercase for case-insensitive matching
        return {
            dt.lower()
            for dt in {
                # Primary type affinities
                "INTEGER",
                "TEXT",
                "REAL",
                "BLOB",
                "NUMERIC",
                # Integer variants (all have INTEGER affinity)
                "INT",
                "TINYINT",
                "SMALLINT",
                "MEDIUMINT",
                "BIGINT",
                "UNSIGNED",
                "INT2",
                "INT8",
                # Text variants (all have TEXT affinity)
                "CHARACTER",
                "VARCHAR",
                "VARYING",
                "NCHAR",
                "NATIVE",
                "NVARCHAR",
                "CLOB",
                # Real variants (all have REAL affinity)
                "DOUBLE",
                "FLOAT",
                # Numeric variants (all have NUMERIC affinity)
                "DECIMAL",
                "BOOLEAN",
                "DATE",
                "DATETIME",
            }
        }

    @property
    def functions(self) -> Set[str]:
        """SQLite built-in functions."""
        # Convert all functions to lowercase for case-insensitive matching
        return {
            fn.lower()
            for fn in {
                # Aggregate functions
                "COUNT",
                "SUM",
                "AVG",
                "MIN",
                "MAX",
                "TOTAL",
                "GROUP_CONCAT",
                # Core functions
                "ABS",
                "CHANGES",
                "CHAR",
                "COALESCE",
                "GLOB",
                "HEX",
                "IFNULL",
                "IIF",
                "INSTR",
                "LAST_INSERT_ROWID",
                "LENGTH",
                "LIKE",
                "LIKELIHOOD",
                "LIKELY",
                "LOAD_EXTENSION",
                "LOWER",
                "LTRIM",
                "NULLIF",
                "PRINTF",
                "QUOTE",
                "RANDOM",
                "RANDOMBLOB",
                "REPLACE",
                "ROUND",
                "RTRIM",
                "SIGN",
                "SOUNDEX",
                "SQLITE_COMPILEOPTION_GET",
                "SQLITE_COMPILEOPTION_USED",
                "SQLITE_OFFSET",
                "SQLITE_SOURCE_ID",
                "SQLITE_VERSION",
                "SUBSTR",
                "SUBSTRING",
                "TOTAL_CHANGES",
                "TRIM",
                "TYPEOF",
                "UNICODE",
                "UNLIKELY",
                "UPPER",
                "ZEROBLOB",
                # Date/Time functions
                "DATE",
                "TIME",
                "DATETIME",
                "JULIANDAY",
                "STRFTIME",
                "UNIXEPOCH",
                # Math functions (SQLite 3.35.0+)
                "ACOS",
                "ACOSH",
                "ASIN",
                "ASINH",
                "ATAN",
                "ATAN2",
                "ATANH",
                "CEIL",
                "CEILING",
                "COS",
                "COSH",
                "DEGREES",
                "EXP",
                "FLOOR",
                "LN",
                "LOG",
                "LOG10",
                "LOG2",
                "MOD",
                "PI",
                "POW",
                "POWER",
                "RADIANS",
                "SIN",
                "SINH",
                "SQRT",
                "TAN",
                "TANH",
                "TRUNC",
                # Window functions
                "ROW_NUMBER",
                "RANK",
                "DENSE_RANK",
                "PERCENT_RANK",
                "CUME_DIST",
                "NTILE",
                "LAG",
                "LEAD",
                "FIRST_VALUE",
                "LAST_VALUE",
                "NTH_VALUE",
                # JSON functions (SQLite 3.38.0+)
                "JSON",
                "JSON_ARRAY",
                "JSON_ARRAY_LENGTH",
                "JSON_EXTRACT",
                "JSON_INSERT",
                "JSON_OBJECT",
                "JSON_PATCH",
                "JSON_REMOVE",
                "JSON_REPLACE",
                "JSON_SET",
                "JSON_TYPE",
                "JSON_VALID",
                "JSON_QUOTE",
                "JSON_GROUP_ARRAY",
                "JSON_GROUP_OBJECT",
                "JSON_EACH",
                "JSON_TREE",
                # String functions
                "CONCAT",
                "CONCAT_WS",
                "FORMAT",
                "LPAD",
                "RPAD",
                # Other functions
                "CAST",
                "TYPEOF",
            }
        }

    @property
    def identifier_chars(self) -> str:
        """SQLite doesn't use special identifier characters."""
        return ""

    @property
    def quote_chars(self) -> Dict[str, str]:
        """
        SQLite quote characters for identifiers.

        SQLite supports multiple quoting styles:
        - Double quotes: "identifier"
        - Backticks: `identifier` (MySQL compatibility)
        - Square brackets: [identifier] (SQL Server compatibility)
        """
        return {
            '"': '"',  # Standard SQL quoted identifiers
            "`": "`",  # MySQL-style backticks
            "[": "]",  # SQL Server-style brackets
        }

    @property
    def comment_styles(self) -> List[str]:
        """SQLite supports -- and /* */ comments."""
        return ["--", "/*"]

    def normalize_identifier(self, identifier: str) -> str:
        """
        Normalize a SQLite identifier.

        SQLite identifiers:
        - Case-insensitive by default (but preserved)
        - Can be quoted with ", `, or []
        - Maximum length is unlimited (but practical limits apply)
        """
        if not identifier:
            return identifier

        # Remove surrounding quotes if present
        if identifier.startswith('"') and identifier.endswith('"'):
            return identifier[1:-1]
        if identifier.startswith("`") and identifier.endswith("`"):
            return identifier[1:-1]
        if identifier.startswith("[") and identifier.endswith("]"):
            return identifier[1:-1]

        # Unquoted identifier - SQLite is case-insensitive but preserves case
        # For comparison purposes, we'll uppercase it
        return identifier.upper()
