"""
SQL Server dialect implementation.
"""

from typing import Set
from .base import SQLDialect


class SQLServerDialect(SQLDialect):
    """
    Microsoft SQL Server / T-SQL dialect.
    
    Includes comprehensive T-SQL keyword support with 279 keywords covering:
    - DDL/DML operations
    - Query syntax
    - Data types
    - Functions
    - Control flow
    - Advanced features (window functions, temporal tables, etc.)
    """
    
    @property
    def name(self) -> str:
        return 'sqlserver'
    
    @property
    def keywords(self) -> Set[str]:
        """Comprehensive SQL Server keywords."""
        return {
            # DDL Keywords
            "add", "alter", "column", "constraint", "create", "database", "drop", 
            "index", "schema", "table", "view", "procedure", "function", "trigger",
            "default", "check", "unique", "primary", "foreign", "key", "references",
            "cascade", "set", "null", "not", "identity", "clustered", "nonclustered",
            
            # DML Keywords
            "select", "insert", "update", "delete", "merge", "truncate", "into", 
            "values", "output", "from", "where", "having", "group", "order", "by",
            
            # Query Keywords
            "distinct", "top", "with", "as", "all", "any", "some", "exists",
            "in", "between", "like", "is", "and", "or", "not", "case", "when",
            "then", "else", "end", "over", "partition", "row_number", "rank",
            "dense_rank", "ntile", "lag", "lead", "first_value", "last_value",
            
            # Join Keywords
            "join", "inner", "left", "right", "full", "outer", "cross", "apply",
            "on", "using",
            
            # Set Operations
            "union", "intersect", "except",
            
            # Transaction Keywords
            "begin", "commit", "rollback", "transaction", "tran", "save", "savepoint",
            
            # Data Types
            "int", "bigint", "smallint", "tinyint", "bit", "decimal", "numeric",
            "money", "smallmoney", "float", "real", "date", "time", "datetime",
            "datetime2", "smalldatetime", "datetimeoffset", "char", "varchar",
            "nchar", "nvarchar", "text", "ntext", "binary", "varbinary", "image",
            "uniqueidentifier", "xml", "json", "sql_variant", "cursor", "timestamp",
            "rowversion", "hierarchyid", "geometry", "geography",
            
            # Function Keywords
            "cast", "convert", "coalesce", "nullif", "isnull", "try_cast",
            "try_convert", "try_parse", "parse", "count", "sum", "avg", "min",
            "max", "stdev", "stdevp", "var", "varp", "count_big", "grouping",
            "grouping_id", "checksum", "checksum_agg", "string_agg",
            
            # Control Flow
            "if", "else", "while", "break", "continue", "return", "goto",
            "waitfor", "try", "catch", "throw", "raiserror", "print",
            
            # Cursor Keywords
            "declare", "open", "fetch", "next", "prior", "first", "last",
            "absolute", "relative", "close", "deallocate",
            
            # Advanced Features
            "pivot", "unpivot", "for", "offset", "fetch", "rows", "only",
            "option", "plan", "use", "exec", "execute", "sp_executesql",
            
            # Security & Permissions
            "grant", "deny", "revoke", "to", "public", "schema_name",
            "user", "login", "role", "authorization",
            
            # Backup & Restore
            "backup", "restore", "database", "log", "file", "filegroup",
            
            # Index & Statistics
            "statistics", "rebuild", "reorganize", "update_statistics",
            "disable", "enable", "resume", "pause",
            
            # Temporal Tables
            "system_time", "period", "generated", "always", "start", "end",
            "hidden",
            
            # Window Functions
            "rows", "range", "unbounded", "preceding", "following", "current",
            
            # Misc Keywords
            "go", "use", "set", "nocount", "on", "off", "quoted_identifier",
            "ansi_nulls", "ansi_padding", "ansi_warnings", "arithabort",
            "concat_null_yields_null", "numeric_roundabort", "xact_abort",
            "nolock", "readuncommitted", "readcommitted", "repeatableread",
            "serializable", "snapshot", "rowlock", "paglock", "tablock",
            "tablockx", "updlock", "xlock", "holdlock", "nowait", "readpast",
            "within", "contains", "freetext", "containstable", "freetexttable",
            "without", "encryption", "schemabinding", "returns", "language",
            
            # Additional T-SQL Keywords
            "openxml", "openquery", "openrowset", "opendatasource", "bulk",
            "formatfile", "errorfile", "maxerrors", "firstrow", "lastrow",
            "fieldterminator", "rowterminator", "codepage", "datafiletype",
            "batchsize", "keepnulls", "keepidentity", "kilobytes_per_batch",
            "rows_per_batch", "order", "check_constraints", "fire_triggers",
            "tablock", "tabblock",
        }
    
    @property
    def data_types(self) -> Set[str]:
        """SQL Server data types."""
        return {
            "int", "bigint", "smallint", "tinyint", "bit",
            "decimal", "numeric", "money", "smallmoney", "float", "real",
            "date", "time", "datetime", "datetime2", "smalldatetime", "datetimeoffset",
            "char", "varchar", "nchar", "nvarchar", "text", "ntext",
            "binary", "varbinary", "image",
            "uniqueidentifier", "xml", "json", "sql_variant",
            "cursor", "timestamp", "rowversion",
            "hierarchyid", "geometry", "geography",
        }
    
    @property
    def functions(self) -> Set[str]:
        """SQL Server built-in functions."""
        return {
            # Aggregate Functions
            "count", "sum", "avg", "min", "max", "stdev", "stdevp", "var", "varp",
            "count_big", "grouping", "grouping_id", "checksum_agg", "string_agg",
            
            # Conversion Functions
            "cast", "convert", "try_cast", "try_convert", "try_parse", "parse",
            
            # Null Functions
            "coalesce", "nullif", "isnull",
            
            # Window Functions
            "row_number", "rank", "dense_rank", "ntile", "lag", "lead",
            "first_value", "last_value",
            
            # Date Functions
            "dateadd", "datediff", "getdate", "sysdatetime", "year", "month", "day",
            "datename", "datepart", "eomonth", "datefromparts", "datetimefromparts",
            
            # String Functions
            "upper", "lower", "substring", "replace", "trim", "ltrim", "rtrim",
            "len", "charindex", "patindex", "concat", "concat_ws", "format",
            "left", "right", "reverse", "replicate", "space", "stuff",
            
            # Math Functions
            "abs", "ceiling", "floor", "round", "power", "sqrt", "square",
            "exp", "log", "log10", "sign", "pi", "rand", "sin", "cos", "tan",
            
            # System Functions
            "checksum", "newid", "scope_identity", "ident_current",
        }
    
    @property
    def ddl_object_keywords(self) -> Set[str]:
        """SQL Server DDL object keywords that precede object definitions."""
        return {
            'table', 'index', 'view', 'procedure', 'function', 'trigger',
            'type', 'schema', 'database', 'assembly', 'certificate',
            'credential', 'cryptographic', 'endpoint', 'event', 'login',
            'master', 'message', 'partition', 'queue', 'remote', 'role',
            'route', 'rule', 'sequence', 'server', 'service', 'signature',
            'statistics', 'symmetric', 'synonym', 'user', 'workload',
            'xml', 'references'  # FOREIGN KEY ... REFERENCES table(col)
        }
    
    @property
    def identifier_chars(self) -> str:
        """SQL Server allows @, #, and $ in identifiers."""
        return '@#$'
    
    @property
    def quote_chars(self) -> dict:
        """SQL Server uses square brackets for identifiers, single quotes for strings."""
        return {
            'identifier': '[',  # Also supports double quotes with QUOTED_IDENTIFIER ON
            'string': "'"
        }
    
    @property
    def comment_styles(self) -> list:
        """SQL Server supports -- and /* */ comments."""
        return ['--', '/*']
