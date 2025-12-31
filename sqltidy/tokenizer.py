import re
from typing import List, NamedTuple, Optional, Union
from enum import Enum


class TokenType(Enum):
    """Token types for SQL parsing"""
    KEYWORD = "keyword"
    IDENTIFIER = "identifier"
    STRING = "string"
    NUMBER = "number"
    OPERATOR = "operator"
    PUNCTUATION = "punctuation"
    COMMENT = "comment"
    WHITESPACE = "whitespace"
    NEWLINE = "newline"
    UNKNOWN = "unknown"


class Token(NamedTuple):
    """Represents a SQL token with type information"""
    value: str
    type: TokenType


class GroupType(Enum):
    """Types of token groups"""
    STATEMENT = "statement"           # Complete SQL statement
    CLAUSE = "clause"                 # SQL clause (SELECT, FROM, WHERE, etc.)
    PARENTHESIS = "parenthesis"       # Content within parentheses
    FUNCTION = "function"             # Function call with arguments
    EXPRESSION = "expression"         # Expression or value list
    IDENTIFIER_LIST = "identifier_list"  # Comma-separated identifiers
    CONDITION = "condition"           # Boolean condition
    COMMENT_BLOCK = "comment_block"   # Comment or block of comments


class TokenGroup:
    """Represents a group of related tokens"""
    
    def __init__(self, group_type: GroupType, tokens: List[Union[Token, 'TokenGroup']], 
                 name: Optional[str] = None):
        self.group_type = group_type
        self.tokens = tokens
        self.name = name  # Optional name (e.g., clause name like "SELECT", "FROM")
    
    def __repr__(self):
        token_count = len(self.tokens)
        name_str = f" '{self.name}'" if self.name else ""
        return f"<TokenGroup {self.group_type.value}{name_str} ({token_count} tokens)>"
    
    def get_text(self) -> str:
        """Get the text representation of this group"""
        result = []
        for item in self.tokens:
            if isinstance(item, Token):
                result.append(item.value)
            elif isinstance(item, TokenGroup):
                result.append(item.get_text())
        return ''.join(result)
    
    def flatten(self) -> List[Token]:
        """Flatten the group to get all tokens (recursive)"""
        result = []
        for item in self.tokens:
            if isinstance(item, Token):
                result.append(item)
            elif isinstance(item, TokenGroup):
                result.extend(item.flatten())
        return result
    
    def filter_type(self, token_type: TokenType) -> List[Token]:
        """Get all tokens of a specific type from this group"""
        return [t for t in self.flatten() if t.type == token_type]
    
    def get_keywords(self) -> List[str]:
        """Get all keyword values from this group"""
        return [t.value.upper() for t in self.filter_type(TokenType.KEYWORD)]
    
    def get_identifiers(self) -> List[str]:
        """Get all identifier values from this group"""
        return [t.value for t in self.filter_type(TokenType.IDENTIFIER)]
    

# Comprehensive SQL Server Keywords
# Reference: https://learn.microsoft.com/en-us/sql/t-sql/language-elements/reserved-keywords-transact-sql
SQL_SERVER_KEYWORDS = {
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


TOKEN_RE = re.compile(
    r"""
    (--[^\n]*)                      |  # single-line comment
    (/\*[\s\S]*?\*/)                |  # multi-line comment

    (\n)                            |  # newline
    (\s+)                           |  # other whitespace

    (<=|>=|<>|!=)                   |  # multi-char operators
    ([(),.;\[\]*=<>+-/])            |  # single-char punctuation/operators

    ('[^']*')                       |  # single-quoted string
    ("[^"]*")                       |  # double-quoted string

    ([A-Za-z_@#][A-Za-z0-9_@#$]*)   |  # identifiers/keywords (including @var, #temp)
    ([0-9]+(?:\.[0-9]+)?)           |  # numbers

    (\S)                               # fallback: any other non-space
    """,
    re.VERBOSE,
)


def get_token_type(token: str) -> TokenType:
    """Determine the type of a token"""
    if not token:
        return TokenType.UNKNOWN
    
    # Check for comments
    if token.startswith('--') or (token.startswith('/*') and token.endswith('*/')):
        return TokenType.COMMENT
    
    # Check for whitespace
    if token.isspace():
        if '\n' in token:
            return TokenType.NEWLINE
        return TokenType.WHITESPACE
    
    # Check for strings
    if (token.startswith("'") and token.endswith("'")) or \
       (token.startswith('"') and token.endswith('"')):
        return TokenType.STRING
    
    # Check for numbers
    if token.replace('.', '', 1).isdigit():
        return TokenType.NUMBER
    
    # Check for operators
    if token in ('<=', '>=', '<>', '!=', '<', '>', '=', '+', '-', '*', '/'):
        return TokenType.OPERATOR
    
    # Check for punctuation
    if token in ('(', ')', ',', '.', ';', '[', ']'):
        return TokenType.PUNCTUATION
    
    # Check for keywords (case-insensitive)
    if token.lower() in SQL_SERVER_KEYWORDS:
        return TokenType.KEYWORD
    
    # Check for identifiers (including variables and temp tables)
    if re.match(r'^[A-Za-z_@#][A-Za-z0-9_@#$]*$', token):
        return TokenType.IDENTIFIER
    
    return TokenType.UNKNOWN


def tokenize(sql: str) -> List[str]:
    """Tokenize SQL string into a list of token strings (backward compatible)"""
    tokens = []
    for groups in TOKEN_RE.findall(sql):
        # Find the first non-empty capturing group
        for t in groups:
            if t == "":
                continue
            # normalize whitespace
            if t.isspace():
                if "\n" in t:
                    tokens.append("\n")
                else:
                    tokens.append(" ")
            else:
                tokens.append(t)
            break

    return tokens


def tokenize_with_types(sql: str) -> List[Token]:
    """Tokenize SQL string into a list of Token objects with type information"""
    tokens = []
    for groups in TOKEN_RE.findall(sql):
        # Find the first non-empty capturing group
        for t in groups:
            if t == "":
                continue
            
            # Normalize whitespace
            if t.isspace():
                if "\n" in t:
                    tokens.append(Token("\n", TokenType.NEWLINE))
                else:
                    tokens.append(Token(" ", TokenType.WHITESPACE))
            else:
                token_type = get_token_type(t)
                tokens.append(Token(t, token_type))
            break

    return tokens


def is_keyword(token: str) -> bool:
    """Check if a token is a SQL Server keyword (case-insensitive)"""
    return token.lower() in SQL_SERVER_KEYWORDS


# ============================================================================
# Token Grouping Functions
# ============================================================================

def group_parentheses(tokens: List[Union[Token, TokenGroup]]) -> List[Union[Token, TokenGroup]]:
    """
    Group tokens within parentheses into TokenGroup objects.
    This handles nested parentheses recursively.
    """
    result = []
    i = 0
    
    while i < len(tokens):
        token = tokens[i]
        
        # Only process Token objects for parentheses
        if isinstance(token, Token) and token.value == '(':
            # Find matching closing parenthesis
            depth = 1
            j = i + 1
            while j < len(tokens) and depth > 0:
                if isinstance(tokens[j], Token):
                    if tokens[j].value == '(':
                        depth += 1
                    elif tokens[j].value == ')':
                        depth -= 1
                j += 1
            
            if depth == 0:
                # Found matching parenthesis
                inner_tokens = tokens[i+1:j-1]  # Exclude the parentheses themselves
                
                # Recursively group inner tokens
                grouped_inner = group_parentheses(inner_tokens)
                
                # Check if this is a function call
                # Look back to see if previous non-whitespace token is an identifier or keyword
                prev_token = None
                for k in range(len(result) - 1, -1, -1):
                    if isinstance(result[k], Token):
                        if result[k].type in (TokenType.IDENTIFIER, TokenType.KEYWORD):
                            prev_token = result[k]
                            break
                        elif result[k].type not in (TokenType.WHITESPACE, TokenType.NEWLINE):
                            break
                
                # SQL function keywords or identifiers followed by parentheses are functions
                if prev_token and (is_keyword(prev_token.value) or prev_token.type == TokenType.IDENTIFIER):
                    # Check if it looks like a function (not a keyword like IF, WHILE, etc.)
                    # Simple heuristic: if it's a common function keyword or an identifier
                    function_keywords = {
                        'cast', 'convert', 'coalesce', 'nullif', 'isnull',
                        'count', 'sum', 'avg', 'min', 'max', 'stdev', 'var',
                        'row_number', 'rank', 'dense_rank', 'ntile', 'lag', 'lead',
                        'first_value', 'last_value', 'string_agg',
                        'dateadd', 'datediff', 'getdate', 'year', 'month', 'day',
                        'upper', 'lower', 'substring', 'replace', 'trim', 'len',
                        'abs', 'ceiling', 'floor', 'round', 'power', 'sqrt',
                    }
                    
                    is_function = (prev_token.value.lower() in function_keywords or 
                                  prev_token.type == TokenType.IDENTIFIER)
                    
                    if is_function:
                        # Function call - include function name
                        # Remove the token from result
                        result = [r for r in result if r != prev_token]
                        # Remove whitespace between function and parenthesis
                        while result and isinstance(result[-1], Token) and \
                              result[-1].type in (TokenType.WHITESPACE, TokenType.NEWLINE):
                            result.pop()
                        
                        group = TokenGroup(
                            GroupType.FUNCTION,
                            [prev_token] + grouped_inner,
                            name=prev_token.value.upper()
                        )
                    else:
                        group = TokenGroup(GroupType.PARENTHESIS, grouped_inner)
                else:
                    group = TokenGroup(GroupType.PARENTHESIS, grouped_inner)
                
                result.append(group)
                i = j
            else:
                # Unmatched parenthesis
                result.append(token)
                i += 1
        else:
            result.append(token)
            i += 1
    
    return result


def group_by_statements(tokens: List[Union[Token, TokenGroup]]) -> List[TokenGroup]:
    """
    Group tokens into complete SQL statements (separated by semicolons).
    """
    statements = []
    current_statement = []
    
    for token in tokens:
        current_statement.append(token)
        
        # Check for statement terminator
        if isinstance(token, Token) and token.value == ';':
            if current_statement:
                statements.append(TokenGroup(GroupType.STATEMENT, current_statement))
                current_statement = []
    
    # Add remaining tokens as a statement (even without semicolon)
    if current_statement:
        # Skip if only whitespace/newlines
        non_ws = [t for t in current_statement if isinstance(t, Token) and 
                  t.type not in (TokenType.WHITESPACE, TokenType.NEWLINE, TokenType.COMMENT)]
        if non_ws:
            statements.append(TokenGroup(GroupType.STATEMENT, current_statement))
    
    return statements


def group_by_clauses(tokens: List[Union[Token, TokenGroup]]) -> List[TokenGroup]:
    """
    Group tokens by SQL clauses (SELECT, FROM, WHERE, etc.).
    """
    # Clause keywords that start a new clause
    clause_keywords = {
        'select', 'from', 'where', 'group', 'having', 'order', 'join',
        'inner', 'left', 'right', 'full', 'cross', 'on', 'with',
        'insert', 'update', 'delete', 'create', 'alter', 'drop',
        'union', 'intersect', 'except', 'into', 'values', 'set'
    }
    
    clauses = []
    current_clause = []
    current_clause_name = None
    
    for token in tokens:
        # Check if this token starts a new clause
        if isinstance(token, Token) and token.type == TokenType.KEYWORD:
            if token.value.lower() in clause_keywords:
                # Save previous clause
                if current_clause:
                    clauses.append(TokenGroup(
                        GroupType.CLAUSE,
                        current_clause,
                        name=current_clause_name
                    ))
                
                # Start new clause
                current_clause = [token]
                current_clause_name = token.value.upper()
                continue
        
        # Add to current clause
        current_clause.append(token)
    
    # Add final clause
    if current_clause:
        clauses.append(TokenGroup(
            GroupType.CLAUSE,
            current_clause,
            name=current_clause_name
        ))
    
    return clauses


def group_tokens(tokens: List[Token], 
                 group_parentheses_flag: bool = True,
                 group_statements_flag: bool = False,
                 group_clauses_flag: bool = False) -> Union[List[Union[Token, TokenGroup]], List[TokenGroup]]:
    """
    Group tokens into logical structures.
    
    Args:
        tokens: List of Token objects
        group_parentheses_flag: Group tokens within parentheses
        group_statements_flag: Group into complete statements (by semicolon)
        group_clauses_flag: Group by SQL clauses (SELECT, FROM, WHERE, etc.)
    
    Returns:
        List of tokens and/or TokenGroup objects
    """
    result = list(tokens)  # Start with copy of tokens
    
    # Apply groupings in order
    if group_parentheses_flag:
        result = group_parentheses(result)
    
    if group_statements_flag:
        result = group_by_statements(result)
    
    if group_clauses_flag:
        # If we have statements, group clauses within each statement
        if group_statements_flag and all(isinstance(r, TokenGroup) and 
                                         r.group_type == GroupType.STATEMENT for r in result):
            new_result = []
            for stmt in result:
                clauses = group_by_clauses(stmt.tokens)
                new_result.append(TokenGroup(GroupType.STATEMENT, clauses, name=stmt.name))
            result = new_result
        else:
            result = group_by_clauses(result)
    
    return result


def print_token_tree(items: List[Union[Token, TokenGroup]], indent: int = 0):
    """
    Print a hierarchical view of tokens and groups.
    Useful for debugging and visualization.
    """
    prefix = "  " * indent
    
    for item in items:
        if isinstance(item, Token):
            type_str = item.type.value
            value_str = repr(item.value) if len(item.value) <= 20 else repr(item.value[:20] + "...")
            print(f"{prefix}Token({type_str}: {value_str})")
        elif isinstance(item, TokenGroup):
            name_str = f" '{item.name}'" if item.name else ""
            print(f"{prefix}TokenGroup({item.group_type.value}{name_str}):")
            print_token_tree(item.tokens, indent + 1)

