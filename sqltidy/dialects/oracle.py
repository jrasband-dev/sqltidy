"""
Oracle Database / PL/SQL dialect support.

This module provides Oracle-specific SQL dialect support including:
- 400+ PL/SQL keywords
- Oracle data types (NUMBER, VARCHAR2, CLOB, BLOB, etc.)
- Oracle built-in functions
- PL/SQL language features
- Oracle-specific syntax (DUAL, CONNECT BY, ROWNUM, etc.)
"""

from typing import Dict, List, Set
from .base import SQLDialect


class OracleDialect(SQLDialect):
    """Oracle Database / PL/SQL dialect."""

    @property
    def name(self) -> str:
        return "oracle"

    @property
    def keywords(self) -> Set[str]:
        """Oracle PL/SQL keywords."""
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
                "SEQUENCE",
                "TRIGGER",
                "PROCEDURE",
                "FUNCTION",
                "PACKAGE",
                "BODY",
                "TYPE",
                "SYNONYM",
                "DATABASE",
                "SCHEMA",
                "TABLESPACE",
                "USER",
                "ROLE",
                "PROFILE",
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
                "MINUS",
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
                "NULLS",
                "FIRST",
                "LAST",
                # Conditional
                "CASE",
                "WHEN",
                "THEN",
                "ELSE",
                "END",
                "IF",
                "ELSIF",
                "ELSEIF",
                "ENDIF",
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
                "ANY",
                "SOME",
                "ALL",
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
                "DEFERRABLE",
                "INITIALLY",
                "DEFERRED",
                "IMMEDIATE",
                # Oracle-specific hierarchical queries
                "CONNECT",
                "START",
                "WITH",
                "PRIOR",
                "LEVEL",
                "NOCYCLE",
                "SYS_CONNECT_BY_PATH",
                # Oracle-specific keywords
                "DUAL",
                "ROWNUM",
                "ROWID",
                "UROWID",
                "NEXTVAL",
                "CURRVAL",
                "SYSDATE",
                "SYSTIMESTAMP",
                "CURRENT_DATE",
                "CURRENT_TIMESTAMP",
                # PL/SQL block structure
                "DECLARE",
                "BEGIN",
                "END",
                "EXCEPTION",
                "RAISE",
                "PRAGMA",
                "AUTONOMOUS_TRANSACTION",
                # PL/SQL control flow
                "LOOP",
                "WHILE",
                "FOR",
                "EXIT",
                "CONTINUE",
                "GOTO",
                "RETURN",
                "EXECUTE",
                "IMMEDIATE",
                # PL/SQL cursors
                "CURSOR",
                "OPEN",
                "FETCH",
                "CLOSE",
                "BULK",
                "COLLECT",
                "FORALL",
                "SAVE",
                "EXCEPTIONS",
                # Data types
                "VARCHAR2",
                "NVARCHAR2",
                "CHAR",
                "NCHAR",
                "NUMBER",
                "INTEGER",
                "INT",
                "SMALLINT",
                "FLOAT",
                "REAL",
                "DOUBLE",
                "PRECISION",
                "DATE",
                "TIMESTAMP",
                "INTERVAL",
                "DAY",
                "MONTH",
                "YEAR",
                "TO",
                "CLOB",
                "NCLOB",
                "BLOB",
                "BFILE",
                "RAW",
                "LONG",
                "BINARY_FLOAT",
                "BINARY_DOUBLE",
                "BOOLEAN",
                "PLS_INTEGER",
                "BINARY_INTEGER",
                "ROWTYPE",
                "RECORD",
                "REF",
                "VARRAY",
                "NESTED",
                # Table/Index options
                "COMPRESS",
                "NOCOMPRESS",
                "LOGGING",
                "NOLOGGING",
                "CACHE",
                "NOCACHE",
                "PARALLEL",
                "NOPARALLEL",
                "PCTFREE",
                "PCTUSED",
                "INITRANS",
                "MAXTRANS",
                "STORAGE",
                "INITIAL",
                "NEXT",
                "MINEXTENTS",
                "MAXEXTENTS",
                # Partitioning
                "PARTITION",
                "SUBPARTITION",
                "RANGE",
                "LIST",
                "HASH",
                "PARTITIONS",
                "SUBPARTITIONS",
                "STORE",
                "OVERFLOW",
                # Privileges
                "GRANT",
                "REVOKE",
                "PRIVILEGES",
                "ADMIN",
                "OPTION",
                "CASCADE",
                "RESTRICT",
                # Transaction control
                "COMMIT",
                "ROLLBACK",
                "SAVEPOINT",
                "WORK",
                "READ",
                "WRITE",
                "ONLY",
                "SERIALIZABLE",
                "ISOLATION",
                # Lock
                "LOCK",
                "SHARE",
                "EXCLUSIVE",
                "MODE",
                "NOWAIT",
                "WAIT",
                # Analytics/Window functions
                "OVER",
                "PARTITION",
                "ROWS",
                "RANGE",
                "UNBOUNDED",
                "PRECEDING",
                "FOLLOWING",
                "CURRENT",
                "ROW",
                "RANK",
                "DENSE_RANK",
                "ROW_NUMBER",
                "NTILE",
                "LEAD",
                "LAG",
                "FIRST_VALUE",
                "LAST_VALUE",
                "LISTAGG",
                "WITHIN",
                # Aggregate functions
                "COUNT",
                "SUM",
                "AVG",
                "MIN",
                "MAX",
                "STDDEV",
                "VARIANCE",
                "MEDIAN",
                "GROUPING",
                "ROLLUP",
                "CUBE",
                "SETS",
                # String functions
                "SUBSTR",
                "INSTR",
                "LENGTH",
                "TRIM",
                "LTRIM",
                "RTRIM",
                "UPPER",
                "LOWER",
                "INITCAP",
                "REPLACE",
                "TRANSLATE",
                "CONCAT",
                "LPAD",
                "RPAD",
                "ASCII",
                "CHR",
                # Conversion functions
                "TO_CHAR",
                "TO_DATE",
                "TO_NUMBER",
                "TO_TIMESTAMP",
                "TO_CLOB",
                "TO_BLOB",
                "CAST",
                "CONVERT",
                # Null handling
                "NVL",
                "NVL2",
                "COALESCE",
                "NULLIF",
                "DECODE",
                # Date functions
                "ADD_MONTHS",
                "MONTHS_BETWEEN",
                "NEXT_DAY",
                "LAST_DAY",
                "TRUNC",
                "ROUND",
                "EXTRACT",
                # Numeric functions
                "ABS",
                "CEIL",
                "FLOOR",
                "MOD",
                "POWER",
                "SQRT",
                "SIGN",
                "EXP",
                "LN",
                "LOG",
                # Other functions
                "GREATEST",
                "LEAST",
                "DUMP",
                "VSIZE",
                "USER",
                "UID",
                # Metadata/System
                "COMMENT",
                "ANALYZE",
                "VALIDATE",
                "STRUCTURE",
                "COMPUTE",
                "STATISTICS",
                "ESTIMATE",
                # Materialized views
                "MATERIALIZED",
                "REFRESH",
                "FAST",
                "COMPLETE",
                "FORCE",
                "ON",
                "DEMAND",
                "COMMIT",
                "BUILD",
                "DEFERRED",
                # Flashback
                "FLASHBACK",
                "VERSIONS",
                "SCN",
                "TIMESTAMP",
                "AS OF",
                # Oracle Text
                "CONTAINS",
                "CATSEARCH",
                "MATCHES",
                # XML
                "XMLTYPE",
                "XMLELEMENT",
                "XMLATTRIBUTES",
                "XMLFOREST",
                "XMLAGG",
                "XMLPARSE",
                "XMLSERIALIZE",
                # Collections
                "TABLE",
                "CAST",
                "MULTISET",
                "MEMBER",
                "SUBMULTISET",
                "THE",
                "CARDINALITY",
                # Advanced features
                "PIVOT",
                "UNPIVOT",
                "MODEL",
                "DIMENSION",
                "MEASURES",
                "RULES",
                "AUTOMATIC",
                "SEQUENTIAL",
                # Hints (common ones)
                "FULL",
                "INDEX",
                "PARALLEL",
                "USE_NL",
                "USE_HASH",
                "USE_MERGE",
                "APPEND",
                "CACHE",
                "NOCACHE",
                "FIRST_ROWS",
                "ALL_ROWS",
                "CHOOSE",
                # PL/SQL exceptions
                "NO_DATA_FOUND",
                "TOO_MANY_ROWS",
                "INVALID_CURSOR",
                "VALUE_ERROR",
                "INVALID_NUMBER",
                "ZERO_DIVIDE",
                "DUP_VAL_ON_INDEX",
                "TIMEOUT_ON_RESOURCE",
                "OTHERS",
                # Additional Oracle keywords
                "ACCESSIBLE",
                "IDENTIFIED",
                "PASSWORD",
                "EXPIRE",
                "ACCOUNT",
                "UNLOCK",
                "TEMPORARY",
                "GLOBAL",
                "PRIVATE",
                "PUBLIC",
                "AUTHID",
                "CURRENT_USER",
                "DEFINER",
                "DETERMINISTIC",
                "PARALLEL_ENABLE",
                "RESULT_CACHE",
                "PIPELINED",
                "AGGREGATE",
            }
        }

    @property
    def data_types(self) -> Set[str]:
        """Oracle data types."""
        # Convert all data types to lowercase for case-insensitive matching
        return {
            dt.lower()
            for dt in {
                # Character types
                "VARCHAR2",
                "NVARCHAR2",
                "CHAR",
                "NCHAR",
                # Numeric types
                "NUMBER",
                "INTEGER",
                "INT",
                "SMALLINT",
                "FLOAT",
                "REAL",
                "DOUBLE",
                "BINARY_FLOAT",
                "BINARY_DOUBLE",
                "PLS_INTEGER",
                "BINARY_INTEGER",
                # Date/Time types
                "DATE",
                "TIMESTAMP",
                "INTERVAL DAY TO SECOND",
                "INTERVAL YEAR TO MONTH",
                # LOB types
                "CLOB",
                "NCLOB",
                "BLOB",
                "BFILE",
                # Binary types
                "RAW",
                "LONG RAW",
                "LONG",
                # Boolean (PL/SQL only)
                "BOOLEAN",
                # Special types
                "ROWID",
                "UROWID",
                "XMLTYPE",
                # User-defined types
                "RECORD",
                "REF",
                "VARRAY",
            }
        }

    @property
    def functions(self) -> Set[str]:
        """Oracle built-in functions."""
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
                "STDDEV",
                "VARIANCE",
                "MEDIAN",
                "LISTAGG",
                "GROUPING",
                "GROUPING_ID",
                # Window/Analytic functions
                "RANK",
                "DENSE_RANK",
                "ROW_NUMBER",
                "NTILE",
                "LEAD",
                "LAG",
                "FIRST_VALUE",
                "LAST_VALUE",
                "PERCENT_RANK",
                "CUME_DIST",
                "PERCENTILE_CONT",
                "PERCENTILE_DISC",
                "RATIO_TO_REPORT",
                # String functions
                "SUBSTR",
                "INSTR",
                "LENGTH",
                "TRIM",
                "LTRIM",
                "RTRIM",
                "UPPER",
                "LOWER",
                "INITCAP",
                "REPLACE",
                "TRANSLATE",
                "CONCAT",
                "LPAD",
                "RPAD",
                "ASCII",
                "CHR",
                "REGEXP_SUBSTR",
                "REGEXP_INSTR",
                "REGEXP_REPLACE",
                "REGEXP_LIKE",
                "REGEXP_COUNT",
                # Conversion functions
                "TO_CHAR",
                "TO_DATE",
                "TO_NUMBER",
                "TO_TIMESTAMP",
                "TO_CLOB",
                "TO_BLOB",
                "TO_NCHAR",
                "TO_NCLOB",
                "CAST",
                "CONVERT",
                "HEXTORAW",
                "RAWTOHEX",
                # Null handling
                "NVL",
                "NVL2",
                "COALESCE",
                "NULLIF",
                "DECODE",
                "LNNVL",
                "NANVL",
                # Date/Time functions
                "SYSDATE",
                "SYSTIMESTAMP",
                "CURRENT_DATE",
                "CURRENT_TIMESTAMP",
                "ADD_MONTHS",
                "MONTHS_BETWEEN",
                "NEXT_DAY",
                "LAST_DAY",
                "TRUNC",
                "ROUND",
                "EXTRACT",
                "NEW_TIME",
                "TZ_OFFSET",
                "FROM_TZ",
                "TO_TIMESTAMP_TZ",
                "NUMTODSINTERVAL",
                "NUMTOYMINTERVAL",
                # Numeric functions
                "ABS",
                "CEIL",
                "FLOOR",
                "MOD",
                "POWER",
                "SQRT",
                "SIGN",
                "EXP",
                "LN",
                "LOG",
                "ROUND",
                "TRUNC",
                "SIN",
                "COS",
                "TAN",
                "ASIN",
                "ACOS",
                "ATAN",
                "ATAN2",
                "SINH",
                "COSH",
                "TANH",
                # Comparison functions
                "GREATEST",
                "LEAST",
                # Environment/System functions
                "USER",
                "UID",
                "USERENV",
                "SYS_CONTEXT",
                "SYS_GUID",
                "DUMP",
                "VSIZE",
                # Hierarchical functions
                "SYS_CONNECT_BY_PATH",
                "CONNECT_BY_ROOT",
                "CONNECT_BY_ISCYCLE",
                "CONNECT_BY_ISLEAF",
                # XML functions
                "XMLELEMENT",
                "XMLATTRIBUTES",
                "XMLFOREST",
                "XMLAGG",
                "XMLPARSE",
                "XMLSERIALIZE",
                "XMLQUERY",
                "XMLTABLE",
                "EXTRACTVALUE",
                "XMLCAST",
                "XMLCOLATTVAL",
                "XMLCONCAT",
                # JSON functions (Oracle 12c+)
                "JSON_VALUE",
                "JSON_QUERY",
                "JSON_TABLE",
                "JSON_OBJECT",
                "JSON_ARRAY",
                "JSON_ARRAYAGG",
                "JSON_OBJECTAGG",
                # Collection functions
                "CARDINALITY",
                "COLLECT",
                "POWERMULTISET",
                "POWERMULTISET_BY_CARDINALITY",
                # Other functions
                "SOUNDEX",
                "BITAND",
                "BITOR",
                "BITXOR",
                "BITNOT",
                "EMPTY_BLOB",
                "EMPTY_CLOB",
            }
        }

    @property
    def identifier_chars(self) -> str:
        """Oracle doesn't use special identifier characters like $ or @."""
        return ""

    @property
    def quote_chars(self) -> Dict[str, str]:
        """Oracle uses double quotes for identifiers."""
        return {
            '"': '"',  # Quoted identifiers: "TableName"
        }

    @property
    def comment_styles(self) -> List[str]:
        """Oracle supports -- and /* */ comments."""
        return ["--", "/*"]

    def normalize_identifier(self, identifier: str) -> str:
        """
        Normalize an Oracle identifier.

        Oracle identifiers:
        - Unquoted identifiers are case-insensitive (converted to uppercase)
        - Quoted identifiers preserve case
        - Maximum 30 characters (128 in Oracle 12.2+)
        """
        if not identifier:
            return identifier

        # Remove surrounding quotes if present
        if identifier.startswith('"') and identifier.endswith('"'):
            # Quoted identifier - preserve case, remove quotes
            return identifier[1:-1]

        # Unquoted identifier - convert to uppercase (Oracle convention)
        return identifier.upper()
