import re
from typing import List, NamedTuple, Optional, Union
from enum import Enum
from .dialects import get_dialect, SQLDialect


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
    

# Backward compatibility: Keep SQL_SERVER_KEYWORDS for existing code
# New code should use get_dialect('sqlserver').keywords instead
def _get_sql_server_keywords():
    """Lazy load SQL Server keywords from dialect"""
    return get_dialect('sqlserver').keywords

SQL_SERVER_KEYWORDS = None  # Will be lazily initialized


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


def get_token_type(token: str, dialect: Union[str, SQLDialect] = 'sqlserver') -> TokenType:
    """
    Determine the type of a token.
    
    Args:
        token: The token string to classify
        dialect: The SQL dialect to use (name or SQLDialect instance). Defaults to 'sqlserver'.
        
    Returns:
        TokenType enum value
    """
    if not token:
        return TokenType.UNKNOWN
    
    # Get dialect instance
    if isinstance(dialect, str):
        dialect_obj = get_dialect(dialect)
    else:
        dialect_obj = dialect
    
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
    
    # Check for keywords (case-insensitive, dialect-aware)
    if dialect_obj.is_keyword(token):
        return TokenType.KEYWORD
    
    # Check for identifiers (including variables and temp tables)
    # Use dialect-specific identifier chars
    id_chars = dialect_obj.identifier_chars
    if id_chars:
        pattern = f'^[A-Za-z_{id_chars}][A-Za-z0-9_{id_chars}]*$'
    else:
        pattern = r'^[A-Za-z_][A-Za-z0-9_]*$'
    if re.match(pattern, token):
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


def tokenize_with_types(sql: str, dialect: Union[str, SQLDialect] = 'sqlserver') -> List[Token]:
    """
    Tokenize SQL string into a list of Token objects with type information.
    
    Args:
        sql: The SQL string to tokenize
        dialect: The SQL dialect to use (name or SQLDialect instance). Defaults to 'sqlserver'.
        
    Returns:
        List of Token objects with type information
    """
    # Get dialect instance
    if isinstance(dialect, str):
        dialect_obj = get_dialect(dialect)
    else:
        dialect_obj = dialect
    
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
                token_type = get_token_type(t, dialect_obj)
                tokens.append(Token(t, token_type))
            break

    return tokens


def get_token_type(token: str, dialect: Union[str, SQLDialect] = 'sqlserver') -> TokenType:
    """
    Determine the type of a token.
    
    Args:
        token: The token string to classify
        dialect: The SQL dialect to use (name or SQLDialect instance). Defaults to 'sqlserver'.
        
    Returns:
        TokenType enum value
    """
    if not token:
        return TokenType.UNKNOWN
    
    # Get dialect instance
    if isinstance(dialect, str):
        dialect_obj = get_dialect(dialect)
    else:
        dialect_obj = dialect
    
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
    
    # Check for keywords (case-insensitive, dialect-aware)
    if dialect_obj.is_keyword(token):
        return TokenType.KEYWORD
    
    # Check for identifiers (including variables and temp tables)
    # Use dialect-specific identifier chars
    id_chars = dialect_obj.identifier_chars
    if id_chars:
        pattern = f'^[A-Za-z_{id_chars}][A-Za-z0-9_{id_chars}]*$'
    else:
        pattern = r'^[A-Za-z_][A-Za-z0-9_]*$'
    if re.match(pattern, token):
        return TokenType.IDENTIFIER
    
    return TokenType.UNKNOWN


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
                if prev_token and (prev_token.type == TokenType.IDENTIFIER or prev_token.type == TokenType.KEYWORD):
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


def is_keyword(token: str, dialect: Union[str, SQLDialect] = 'sqlserver') -> bool:
    """
    Check if a token is a keyword in the specified dialect (case-insensitive).
    
    Args:
        token: The token to check
        dialect: The SQL dialect to use (name or SQLDialect instance). Defaults to 'sqlserver'.
        
    Returns:
        True if the token is a keyword, False otherwise
    """
    # Get dialect instance
    if isinstance(dialect, str):
        dialect_obj = get_dialect(dialect)
    else:
        dialect_obj = dialect
    
    return dialect_obj.is_keyword(token)


# Backward compatibility: Initialize SQL_SERVER_KEYWORDS on first access
def __getattr__(name):
    """Module-level __getattr__ for lazy initialization of SQL_SERVER_KEYWORDS"""
    if name == 'SQL_SERVER_KEYWORDS':
        global SQL_SERVER_KEYWORDS
        if SQL_SERVER_KEYWORDS is None:
            SQL_SERVER_KEYWORDS = _get_sql_server_keywords()
        return SQL_SERVER_KEYWORDS
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")

