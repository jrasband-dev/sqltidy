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
    
    # Semantic SQL patterns
    CASE_EXPRESSION = "case_expression"  # CASE...END expression
    WINDOW_FUNCTION = "window_function"  # Window function with OVER clause
    SUBQUERY = "subquery"             # SELECT within parentheses
    
    # Specific SQL clauses
    SELECT_CLAUSE = "select_clause"   # SELECT clause
    FROM_CLAUSE = "from_clause"       # FROM clause
    WHERE_CLAUSE = "where_clause"     # WHERE clause
    JOIN_CLAUSE = "join_clause"       # JOIN clause (any type)
    GROUP_BY_CLAUSE = "group_by_clause"  # GROUP BY clause
    HAVING_CLAUSE = "having_clause"   # HAVING clause
    ORDER_BY_CLAUSE = "order_by_clause"  # ORDER BY clause
    
    # Advanced SQL constructs
    CTE = "cte"                       # Common Table Expression (WITH clause)
    UNION_CLAUSE = "union_clause"     # UNION/UNION ALL clause
    LIMIT_CLAUSE = "limit_clause"     # LIMIT/TOP/FETCH FIRST clause
    
    # Other groupings
    COLUMN_LIST = "column_list"       # List of columns
    ON_CONDITION = "on_condition"     # ON condition in JOIN


class SemanticLevel(Enum):
    """Levels of semantic analysis to apply during tokenization"""
    BASIC = "basic"             # Just Token objects, no grouping
    GROUPED = "grouped"         # + parentheses and function grouping
    STRUCTURED = "structured"   # + statements and basic clauses
    SEMANTIC = "semantic"       # + JOINs, CASE, CTEs, window functions, etc. (FULL)


class TokenGroup:
    """Represents a group of related tokens with optional metadata
    
    Metadata examples:
    - CASE_EXPRESSION: {'has_else': bool}
    - JOIN_CLAUSE: {'join_type': str, 'table': str, 'alias': str, 'has_on': bool}
    - WINDOW_FUNCTION: {'function_name': str, 'partition_by': List[str], 'order_by': List[str]}
    - CTE: {'cte_name': str, 'columns': List[str]}
    - SUBQUERY: {'has_alias': bool, 'alias': str}
    """
    
    def __init__(self, group_type: GroupType, tokens: List[Union[Token, 'TokenGroup']], 
                 name: Optional[str] = None, metadata: Optional[dict] = None):
        self.group_type = group_type
        self.tokens = tokens
        self.name = name  # Optional name (e.g., clause name like "SELECT", "FROM")
        self.metadata = metadata or {}  # Additional semantic information
    
    def __repr__(self):
        token_count = len(self.tokens)
        name_str = f" '{self.name}'" if self.name else ""
        meta_str = f" {self.metadata}" if self.metadata else ""
        return f"<TokenGroup {self.group_type.value}{name_str} ({token_count} tokens){meta_str}>"
    
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
    
    def get_metadata(self, key: str, default=None):
        """Get a metadata value by key
        
        Args:
            key: The metadata key to retrieve
            default: Default value if key not found
            
        Returns:
            The metadata value or default
        """
        return self.metadata.get(key, default)
    
    def set_metadata(self, key: str, value):
        """Set a metadata value
        
        Args:
            key: The metadata key to set
            value: The value to set
        """
        self.metadata[key] = value
    
    def find_groups(self, group_type: GroupType) -> List['TokenGroup']:
        """Find all nested groups of a specific type (recursive)
        
        Args:
            group_type: The type of group to find
            
        Returns:
            List of matching TokenGroup objects
        """
        result = []
        for item in self.tokens:
            if isinstance(item, TokenGroup):
                if item.group_type == group_type:
                    result.append(item)
                # Recursively search nested groups
                result.extend(item.find_groups(group_type))
        return result
    
    def get_clause_by_name(self, name: str) -> Optional['TokenGroup']:
        """Get a clause by its name (case-insensitive)
        
        Args:
            name: The clause name to search for (e.g., 'SELECT', 'FROM')
            
        Returns:
            The first matching TokenGroup or None
        """
        name_upper = name.upper()
        for item in self.tokens:
            if isinstance(item, TokenGroup) and item.name and item.name.upper() == name_upper:
                return item
        return None
    

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


def tokenize_with_types(sql: str, dialect: Union[str, SQLDialect] = 'sqlserver',
                        level: Union[str, SemanticLevel] = SemanticLevel.BASIC) -> Union[List[Token], List[Union[Token, TokenGroup]]]:
    """
    Tokenize SQL string into a list of Token objects with optional semantic grouping.
    
    Args:
        sql: The SQL string to tokenize
        dialect: The SQL dialect to use (name or SQLDialect instance). Defaults to 'sqlserver'.
        level: Level of semantic analysis to apply. Can be:
            - SemanticLevel.BASIC or 'basic': Just Token objects (default, backward compatible)
            - SemanticLevel.GROUPED or 'grouped': + parentheses and function grouping
            - SemanticLevel.STRUCTURED or 'structured': + statements and basic clauses
            - SemanticLevel.SEMANTIC or 'semantic': + JOINs, CASE, CTEs, etc. (FULL)
        
    Returns:
        - If level is BASIC: List[Token]
        - Otherwise: List[Union[Token, TokenGroup]] with semantic groups
    """
    # Get dialect instance
    if isinstance(dialect, str):
        dialect_obj = get_dialect(dialect)
    else:
        dialect_obj = dialect
    
    # Parse level parameter
    if isinstance(level, str):
        try:
            level = SemanticLevel(level.lower())
        except ValueError:
            level = SemanticLevel.BASIC
    
    # Tokenize into basic tokens
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
    
    # Apply grouping based on level
    if level == SemanticLevel.BASIC:
        return tokens
    
    result = list(tokens)
    
    # GROUPED level: parentheses and functions
    if level in (SemanticLevel.GROUPED, SemanticLevel.STRUCTURED, SemanticLevel.SEMANTIC):
        result = group_parentheses(result)
    
    # STRUCTURED level: add statements and clauses
    if level in (SemanticLevel.STRUCTURED, SemanticLevel.SEMANTIC):
        result = group_by_statements(result)
        # Group clauses within each statement
        new_result = []
        for item in result:
            if isinstance(item, TokenGroup) and item.group_type == GroupType.STATEMENT:
                clauses = group_by_clauses_enhanced(item.tokens, dialect_obj)
                # Enrich JOIN_CLAUSE groups with metadata
                clauses = _enrich_join_metadata(clauses)
                new_result.append(TokenGroup(GroupType.STATEMENT, clauses, name=item.name))
            else:
                new_result.append(item)
        result = new_result
    
    # SEMANTIC level: apply advanced pattern recognition
    if level == SemanticLevel.SEMANTIC:
        result = apply_semantic_patterns(result, dialect_obj)
    
    return result


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


# ============================================================================
# Semantic Pattern Recognition Functions
# ============================================================================

def apply_semantic_patterns(tokens: List[Union[Token, TokenGroup]], dialect: SQLDialect) -> List[Union[Token, TokenGroup]]:
    """
    Apply semantic pattern recognition to identify SQL constructs.
    Patterns are applied in order from innermost to outermost:
    1. CASE expressions
    2. Window functions
    3. CTEs (WITH clauses)
    4. Subqueries
    5. JOINs
    6. Specific clauses (WHERE, GROUP BY, etc.)
    
    Args:
        tokens: List of tokens and groups
        dialect: SQL dialect for dialect-specific patterns
        
    Returns:
        List with semantic patterns identified and grouped
    """
    result = list(tokens)
    
    # Recursively process nested groups first
    result = _apply_patterns_recursive(result, dialect)
    
    return result


def _apply_patterns_recursive(tokens: List[Union[Token, TokenGroup]], dialect: SQLDialect, parent_group_type: Optional[GroupType] = None) -> List[Union[Token, TokenGroup]]:
    """
    Recursively apply patterns, processing nested groups first.
    
    Args:
        tokens: List of tokens and groups to process
        dialect: SQL dialect for dialect-specific patterns
        parent_group_type: Type of the parent group (to avoid re-applying patterns)
    """
    # First, recursively process any existing groups
    processed = []
    for item in tokens:
        if isinstance(item, TokenGroup):
            # Process tokens within this group, passing its type as parent
            new_tokens = _apply_patterns_recursive(item.tokens, dialect, item.group_type)
            processed.append(TokenGroup(item.group_type, new_tokens, item.name, item.metadata))
        else:
            processed.append(item)
    
    # Now apply patterns at this level (innermost to outermost)
    # Skip patterns that would create duplicate nesting
    result = processed
    
    # Only apply CASE patterns if not inside a CASE_EXPRESSION
    if parent_group_type != GroupType.CASE_EXPRESSION:
        result = identify_case_expressions(result)
    
    # Only apply window function patterns if not inside a WINDOW_FUNCTION
    if parent_group_type != GroupType.WINDOW_FUNCTION:
        result = identify_window_functions(result)
    
    # Only apply CTE patterns if not inside a CTE
    if parent_group_type != GroupType.CTE:
        result = identify_ctes(result)
    
    # Only apply subquery patterns if not inside a SUBQUERY
    if parent_group_type != GroupType.SUBQUERY:
        result = identify_subqueries(result)
    
    # Only apply JOIN patterns if not already inside a JOIN_CLAUSE
    # This allows JOINs to be detected inside FROM_CLAUSE but prevents nested JOIN detection
    if parent_group_type != GroupType.JOIN_CLAUSE:
        result = identify_joins(result)
    
    # Apply clause identification
    result = identify_specific_clauses(result, dialect)
    
    # Only apply UNION patterns if not inside a UNION_CLAUSE
    if parent_group_type != GroupType.UNION_CLAUSE:
        result = identify_union_clauses(result)
    
    # Only apply LIMIT patterns if not inside a LIMIT_CLAUSE
    if parent_group_type != GroupType.LIMIT_CLAUSE:
        result = identify_limit_clauses(result, dialect)
    
    return result


def identify_case_expressions(tokens: List[Union[Token, TokenGroup]]) -> List[Union[Token, TokenGroup]]:
    """
    Identify CASE...END expressions and group them.
    
    Creates TokenGroup with:
    - group_type: GroupType.CASE_EXPRESSION
    - metadata: {'has_else': bool}
    
    Args:
        tokens: List of tokens and groups
        
    Returns:
        List with CASE expressions grouped
    """
    result = []
    i = 0
    
    while i < len(tokens):
        # Skip if already a CASE_EXPRESSION group
        if isinstance(tokens[i], TokenGroup) and tokens[i].group_type == GroupType.CASE_EXPRESSION:
            result.append(tokens[i])
            i += 1
            continue
            
        if isinstance(tokens[i], Token) and tokens[i].type == TokenType.KEYWORD and \
           tokens[i].value.upper() == 'CASE':
            # Extract CASE expression
            case_tokens, end_idx, metadata = _extract_case_expression(tokens, i)
            if end_idx > i:
                result.append(TokenGroup(GroupType.CASE_EXPRESSION, case_tokens, metadata=metadata))
                i = end_idx
                continue
        
        result.append(tokens[i])
        i += 1
    
    return result


def _extract_case_expression(tokens: List[Union[Token, TokenGroup]], start: int) -> tuple:
    """
    Extract a CASE expression from tokens starting at index.
    
    Returns:
        (case_tokens, end_index, metadata)
    """
    case_tokens = [tokens[start]]  # Include CASE keyword
    i = start + 1
    has_else = False
    
    # Find matching END keyword
    depth = 1  # Track nested CASE expressions
    while i < len(tokens) and depth > 0:
        item = tokens[i]
        
        if isinstance(item, Token) and item.type == TokenType.KEYWORD:
            keyword = item.value.upper()
            if keyword == 'CASE':
                depth += 1
            elif keyword == 'END':
                depth -= 1
                if depth == 0:
                    case_tokens.append(item)
                    i += 1
                    break
            elif keyword == 'ELSE' and depth == 1:
                has_else = True
        
        case_tokens.append(item)
        i += 1
    
    metadata = {'has_else': has_else}
    return case_tokens, i, metadata


def identify_joins(tokens: List[Union[Token, TokenGroup]]) -> List[Union[Token, TokenGroup]]:
    """
    Identify JOIN clauses and group them.
    
    Creates TokenGroup with:
    - group_type: GroupType.JOIN_CLAUSE
    - name: Join type (e.g., 'INNER JOIN', 'LEFT JOIN')
    - metadata: {'join_type': str, 'table': str, 'alias': str, 'has_on': bool}
    
    Args:
        tokens: List of tokens and groups
        
    Returns:
        List with JOIN clauses grouped
    """
    result = []
    i = 0
    
    join_keywords = {'JOIN', 'INNER', 'LEFT', 'RIGHT', 'FULL', 'CROSS'}
    
    while i < len(tokens):
        # Skip if this is already a JOIN_CLAUSE group (avoid double-wrapping)
        if isinstance(tokens[i], TokenGroup) and tokens[i].group_type == GroupType.JOIN_CLAUSE:
            result.append(tokens[i])
            i += 1
            continue
            
        if isinstance(tokens[i], Token) and tokens[i].type == TokenType.KEYWORD and \
           tokens[i].value.upper() in join_keywords:
            # Extract JOIN clause
            join_tokens, end_idx, metadata = _extract_join_clause(tokens, i)
            if end_idx > i:
                join_name = metadata.get('join_type', 'JOIN')
                result.append(TokenGroup(GroupType.JOIN_CLAUSE, join_tokens, name=join_name, metadata=metadata))
                i = end_idx
                continue
        
        result.append(tokens[i])
        i += 1
    
    return result


def _extract_join_clause(tokens: List[Union[Token, TokenGroup]], start: int) -> tuple:
    """
    Extract a JOIN clause from tokens starting at index.
    
    Returns:
        (join_tokens, end_index, metadata)
    """
    join_tokens = []
    i = start
    join_type_parts = []
    table_name = ''
    alias = ''
    has_on = False
    
    # Collect join type (e.g., INNER JOIN, LEFT OUTER JOIN)
    while i < len(tokens):
        if isinstance(tokens[i], Token) and tokens[i].type == TokenType.KEYWORD:
            keyword = tokens[i].value.upper()
            if keyword in {'INNER', 'LEFT', 'RIGHT', 'FULL', 'OUTER', 'CROSS', 'JOIN'}:
                join_type_parts.append(keyword)
                join_tokens.append(tokens[i])
                i += 1
                if keyword == 'JOIN':
                    break
            else:
                break
        elif isinstance(tokens[i], Token) and tokens[i].type in (TokenType.WHITESPACE, TokenType.NEWLINE):
            join_tokens.append(tokens[i])
            i += 1
        else:
            break
    
    # Get table name and alias
    while i < len(tokens):
        item = tokens[i]
        
        # Check for clause-ending keywords
        if isinstance(item, Token) and item.type == TokenType.KEYWORD:
            keyword = item.value.upper()
            if keyword in {'ON', 'WHERE', 'GROUP', 'HAVING', 'ORDER', 'JOIN', 'INNER', 'LEFT', 'RIGHT', 'FULL', 'CROSS', 'UNION', 'EXCEPT', 'INTERSECT'}:
                if keyword == 'ON':
                    has_on = True
                    # Include ON condition in the join
                    join_tokens.append(item)
                    i += 1
                    # Include condition tokens until next major keyword
                    paren_depth = 0
                    while i < len(tokens):
                        curr = tokens[i]
                        if isinstance(curr, TokenGroup) and curr.group_type == GroupType.PARENTHESIS:
                            paren_depth += 1
                            join_tokens.append(curr)
                            i += 1
                            continue
                        elif isinstance(curr, Token):
                            if curr.value == '(':
                                paren_depth += 1
                            elif curr.value == ')':
                                paren_depth -= 1
                            
                            if curr.type == TokenType.KEYWORD and paren_depth == 0:
                                kw = curr.value.upper()
                                if kw in {'WHERE', 'GROUP', 'HAVING', 'ORDER', 'JOIN', 'INNER', 'LEFT', 'RIGHT', 'FULL', 'CROSS', 'UNION', 'EXCEPT', 'INTERSECT'}:
                                    break
                        
                        join_tokens.append(curr)
                        i += 1
                break
        
        # Collect table name and alias
        if isinstance(item, Token):
            if item.type == TokenType.IDENTIFIER:
                if not table_name:
                    table_name = item.value
                else:
                    alias = item.value
            elif item.value.upper() == 'AS' and item.type == TokenType.KEYWORD:
                pass  # Skip AS keyword
        
        join_tokens.append(item)
        i += 1
    
    join_type = ' '.join(join_type_parts) if join_type_parts else 'JOIN'
    metadata = {
        'join_type': join_type,
        'table': table_name,
        'alias': alias,
        'has_on': has_on
    }
    
    return join_tokens, i, metadata


def identify_ctes(tokens: List[Union[Token, TokenGroup]]) -> List[Union[Token, TokenGroup]]:
    """
    Identify CTEs (Common Table Expressions) with WITH keyword.
    
    Creates TokenGroup with:
    - group_type: GroupType.CTE
    - name: CTE name
    - metadata: {'cte_name': str, 'columns': List[str]}
    
    Args:
        tokens: List of tokens and groups
        
    Returns:
        List with CTEs grouped
    """
    result = []
    i = 0
    
    while i < len(tokens):
        # Skip if already a CTE group
        if isinstance(tokens[i], TokenGroup) and tokens[i].group_type == GroupType.CTE:
            result.append(tokens[i])
            i += 1
            continue
            
        if isinstance(tokens[i], Token) and tokens[i].type == TokenType.KEYWORD and \
           tokens[i].value.upper() == 'WITH':
            # Extract CTE
            cte_tokens, end_idx, metadata = _extract_cte(tokens, i)
            if end_idx > i:
                cte_name = metadata.get('cte_name', 'CTE')
                result.append(TokenGroup(GroupType.CTE, cte_tokens, name=cte_name, metadata=metadata))
                i = end_idx
                continue
        
        result.append(tokens[i])
        i += 1
    
    return result


def _extract_cte(tokens: List[Union[Token, TokenGroup]], start: int) -> tuple:
    """
    Extract a CTE from tokens starting at WITH keyword.
    
    Returns:
        (cte_tokens, end_index, metadata)
    """
    cte_tokens = [tokens[start]]  # Include WITH
    i = start + 1
    cte_name = ''
    columns = []
    
    # Get CTE name
    while i < len(tokens):
        if isinstance(tokens[i], Token):
            if tokens[i].type == TokenType.IDENTIFIER:
                cte_name = tokens[i].value
                cte_tokens.append(tokens[i])
                i += 1
                break
            elif tokens[i].type not in (TokenType.WHITESPACE, TokenType.NEWLINE, TokenType.COMMENT):
                break
        cte_tokens.append(tokens[i])
        i += 1
    
    # Get column list if present (in parentheses)
    while i < len(tokens):
        if isinstance(tokens[i], TokenGroup) and tokens[i].group_type == GroupType.PARENTHESIS:
            # Extract column names
            for item in tokens[i].tokens:
                if isinstance(item, Token) and item.type == TokenType.IDENTIFIER:
                    columns.append(item.value)
            cte_tokens.append(tokens[i])
            i += 1
            break
        elif isinstance(tokens[i], Token) and tokens[i].type == TokenType.KEYWORD and \
             tokens[i].value.upper() == 'AS':
            break
        cte_tokens.append(tokens[i])
        i += 1
    
    # Include AS and the subquery
    paren_depth = 0
    while i < len(tokens):
        item = tokens[i]
        cte_tokens.append(item)
        
        if isinstance(item, TokenGroup) and item.group_type == GroupType.PARENTHESIS:
            i += 1
            # Check if there's a comma (another CTE follows) or main SELECT
            while i < len(tokens):
                if isinstance(tokens[i], Token):
                    if tokens[i].type in (TokenType.WHITESPACE, TokenType.NEWLINE, TokenType.COMMENT):
                        i += 1
                        continue
                    elif tokens[i].value == ',':
                        # Another CTE follows, don't include it
                        break
                    else:
                        # Main query starts
                        break
                break
            break
        
        i += 1
        
        # Safety: stop at main SELECT
        if isinstance(item, Token) and item.type == TokenType.KEYWORD and \
           item.value.upper() == 'SELECT' and paren_depth == 0:
            break
    
    metadata = {
        'cte_name': cte_name,
        'columns': columns
    }
    
    return cte_tokens, i, metadata


def identify_subqueries(tokens: List[Union[Token, TokenGroup]]) -> List[Union[Token, TokenGroup]]:
    """
    Identify subqueries (SELECT within parentheses) and mark them.
    
    Creates TokenGroup with:
    - group_type: GroupType.SUBQUERY
    - metadata: {'has_alias': bool, 'alias': str}
    
    Args:
        tokens: List of tokens and groups
        
    Returns:
        List with subqueries marked
    """
    result = []
    
    for i, item in enumerate(tokens):
        # Skip if already a SUBQUERY group
        if isinstance(item, TokenGroup) and item.group_type == GroupType.SUBQUERY:
            result.append(item)
            continue
            
        if isinstance(item, TokenGroup) and item.group_type == GroupType.PARENTHESIS:
            # Check if this contains a SELECT statement
            has_select = False
            for token in item.tokens:
                if isinstance(token, Token) and token.type == TokenType.KEYWORD and \
                   token.value.upper() == 'SELECT':
                    has_select = True
                    break
            
            if has_select:
                # This is a subquery - check for alias
                alias = ''
                has_alias = False
                # Look ahead for alias
                j = i + 1
                while j < len(tokens):
                    if isinstance(tokens[j], Token):
                        if tokens[j].type in (TokenType.WHITESPACE, TokenType.NEWLINE):
                            j += 1
                            continue
                        elif tokens[j].type == TokenType.KEYWORD and tokens[j].value.upper() == 'AS':
                            has_alias = True
                            j += 1
                            continue
                        elif tokens[j].type == TokenType.IDENTIFIER:
                            alias = tokens[j].value
                            has_alias = True
                            break
                        else:
                            break
                    break
                
                metadata = {'has_alias': has_alias, 'alias': alias}
                result.append(TokenGroup(GroupType.SUBQUERY, item.tokens, metadata=metadata))
            else:
                result.append(item)
        else:
            result.append(item)
    
    return result


def identify_specific_clauses(tokens: List[Union[Token, TokenGroup]], dialect: SQLDialect) -> List[Union[Token, TokenGroup]]:
    """
    Identify specific clause types (WHERE, GROUP BY, ORDER BY, HAVING).
    Converts generic CLAUSE groups to specific clause types.
    
    Args:
        tokens: List of tokens and groups
        dialect: SQL dialect
        
    Returns:
        List with specific clause types
    """
    result = []
    
    for item in tokens:
        if isinstance(item, TokenGroup) and item.group_type == GroupType.CLAUSE and item.name:
            clause_name = item.name.upper()
            
            # Map clause names to specific types
            if clause_name == 'WHERE':
                result.append(TokenGroup(GroupType.WHERE_CLAUSE, item.tokens, name=item.name, metadata=item.metadata))
            elif clause_name in ('GROUP', 'GROUP BY'):
                result.append(TokenGroup(GroupType.GROUP_BY_CLAUSE, item.tokens, name='GROUP BY', metadata=item.metadata))
            elif clause_name == 'HAVING':
                result.append(TokenGroup(GroupType.HAVING_CLAUSE, item.tokens, name=item.name, metadata=item.metadata))
            elif clause_name in ('ORDER', 'ORDER BY'):
                result.append(TokenGroup(GroupType.ORDER_BY_CLAUSE, item.tokens, name='ORDER BY', metadata=item.metadata))
            elif clause_name == 'SELECT':
                result.append(TokenGroup(GroupType.SELECT_CLAUSE, item.tokens, name=item.name, metadata=item.metadata))
            elif clause_name == 'FROM':
                result.append(TokenGroup(GroupType.FROM_CLAUSE, item.tokens, name=item.name, metadata=item.metadata))
            else:
                result.append(item)
        else:
            result.append(item)
    
    return result


def identify_window_functions(tokens: List[Union[Token, TokenGroup]]) -> List[Union[Token, TokenGroup]]:
    """
    Identify window functions (functions with OVER clause).
    
    Creates TokenGroup with:
    - group_type: GroupType.WINDOW_FUNCTION
    - name: Function name
    - metadata: {'function_name': str, 'partition_by': List[str], 'order_by': List[str]}
    
    Args:
        tokens: List of tokens and groups
        
    Returns:
        List with window functions grouped
    """
    result = []
    i = 0
    
    while i < len(tokens):
        # Skip if already a WINDOW_FUNCTION group
        if isinstance(tokens[i], TokenGroup) and tokens[i].group_type == GroupType.WINDOW_FUNCTION:
            result.append(tokens[i])
            i += 1
            continue
            
        # Look for FUNCTION followed by OVER keyword
        if isinstance(tokens[i], TokenGroup) and tokens[i].group_type == GroupType.FUNCTION:
            # Check if followed by OVER
            j = i + 1
            has_over = False
            while j < len(tokens):
                if isinstance(tokens[j], Token):
                    if tokens[j].type in (TokenType.WHITESPACE, TokenType.NEWLINE):
                        j += 1
                        continue
                    elif tokens[j].type == TokenType.KEYWORD and tokens[j].value.upper() == 'OVER':
                        has_over = True
                        break
                    else:
                        break
                break
            
            if has_over:
                # Extract window function with OVER clause
                window_tokens, end_idx, metadata = _extract_window_function(tokens, i, j)
                result.append(TokenGroup(GroupType.WINDOW_FUNCTION, window_tokens, 
                                       name=tokens[i].name, metadata=metadata))
                i = end_idx
                continue
        
        result.append(tokens[i])
        i += 1
    
    return result


def _extract_window_function(tokens: List[Union[Token, TokenGroup]], func_idx: int, over_idx: int) -> tuple:
    """
    Extract a window function including the OVER clause.
    
    Returns:
        (window_tokens, end_index, metadata)
    """
    func_group = tokens[func_idx]
    window_tokens = [func_group]
    i = func_idx + 1
    partition_by = []
    order_by = []
    
    # Add whitespace before OVER
    while i < over_idx:
        window_tokens.append(tokens[i])
        i += 1
    
    # Add OVER keyword
    window_tokens.append(tokens[over_idx])
    i = over_idx + 1
    
    # Get OVER clause (usually in parentheses)
    while i < len(tokens):
        item = tokens[i]
        
        if isinstance(item, TokenGroup) and item.group_type == GroupType.PARENTHESIS:
            # Parse PARTITION BY and ORDER BY
            in_partition = False
            in_order = False
            for token in item.tokens:
                if isinstance(token, Token) and token.type == TokenType.KEYWORD:
                    kw = token.value.upper()
                    if kw == 'PARTITION':
                        in_partition = True
                        in_order = False
                    elif kw == 'ORDER':
                        in_order = True
                        in_partition = False
                    elif kw in ('BY',):
                        pass
                elif isinstance(token, Token) and token.type == TokenType.IDENTIFIER:
                    if in_partition:
                        partition_by.append(token.value)
                    elif in_order:
                        order_by.append(token.value)
            
            window_tokens.append(item)
            i += 1
            break
        elif isinstance(item, Token) and item.type in (TokenType.WHITESPACE, TokenType.NEWLINE):
            window_tokens.append(item)
            i += 1
        else:
            break
    
    metadata = {
        'function_name': func_group.name if func_group.name else '',
        'partition_by': partition_by,
        'order_by': order_by
    }
    
    return window_tokens, i, metadata


def identify_union_clauses(tokens: List[Union[Token, TokenGroup]]) -> List[Union[Token, TokenGroup]]:
    """
    Identify UNION/UNION ALL clauses.
    
    Creates TokenGroup with:
    - group_type: GroupType.UNION_CLAUSE
    - name: 'UNION' or 'UNION ALL'
    - metadata: {'union_type': 'UNION' or 'UNION ALL'}
    
    Args:
        tokens: List of tokens and groups
        
    Returns:
        List with UNION clauses grouped
    """
    result = []
    i = 0
    
    while i < len(tokens):
        # Skip if already a UNION_CLAUSE group
        if isinstance(tokens[i], TokenGroup) and tokens[i].group_type == GroupType.UNION_CLAUSE:
            result.append(tokens[i])
            i += 1
            continue
            
        if isinstance(tokens[i], Token) and tokens[i].type == TokenType.KEYWORD and \
           tokens[i].value.upper() == 'UNION':
            union_tokens = [tokens[i]]
            union_type = 'UNION'
            i += 1
            
            # Check for ALL
            while i < len(tokens):
                if isinstance(tokens[i], Token):
                    if tokens[i].type in (TokenType.WHITESPACE, TokenType.NEWLINE):
                        union_tokens.append(tokens[i])
                        i += 1
                        continue
                    elif tokens[i].type == TokenType.KEYWORD and tokens[i].value.upper() == 'ALL':
                        union_tokens.append(tokens[i])
                        union_type = 'UNION ALL'
                        i += 1
                        break
                    else:
                        break
                break
            
            metadata = {'union_type': union_type}
            result.append(TokenGroup(GroupType.UNION_CLAUSE, union_tokens, name=union_type, metadata=metadata))
        else:
            result.append(tokens[i])
            i += 1
    
    return result


def identify_limit_clauses(tokens: List[Union[Token, TokenGroup]], dialect: SQLDialect) -> List[Union[Token, TokenGroup]]:
    """
    Identify LIMIT/TOP/FETCH FIRST clauses (dialect-specific).
    
    Creates TokenGroup with:
    - group_type: GroupType.LIMIT_CLAUSE
    - name: 'LIMIT', 'TOP', or 'FETCH FIRST'
    - metadata: {'limit_type': str, 'limit_value': str}
    
    Args:
        tokens: List of tokens and groups
        dialect: SQL dialect
        
    Returns:
        List with LIMIT clauses grouped
    """
    result = []
    i = 0
    
    while i < len(tokens):
        # Skip if already a LIMIT_CLAUSE group
        if isinstance(tokens[i], TokenGroup) and tokens[i].group_type == GroupType.LIMIT_CLAUSE:
            result.append(tokens[i])
            i += 1
            continue
            
        if isinstance(tokens[i], Token) and tokens[i].type == TokenType.KEYWORD:
            keyword = tokens[i].value.upper()
            
            # LIMIT (MySQL, PostgreSQL)
            if keyword == 'LIMIT':
                limit_tokens = [tokens[i]]
                i += 1
                limit_value = ''
                
                # Get limit value
                while i < len(tokens):
                    if isinstance(tokens[i], Token):
                        if tokens[i].type in (TokenType.WHITESPACE, TokenType.NEWLINE):
                            limit_tokens.append(tokens[i])
                            i += 1
                            continue
                        elif tokens[i].type == TokenType.NUMBER:
                            limit_value = tokens[i].value
                            limit_tokens.append(tokens[i])
                            i += 1
                            break
                        else:
                            break
                    break
                
                metadata = {'limit_type': 'LIMIT', 'limit_value': limit_value}
                result.append(TokenGroup(GroupType.LIMIT_CLAUSE, limit_tokens, name='LIMIT', metadata=metadata))
            
            # TOP (SQL Server)
            elif keyword == 'TOP':
                limit_tokens = [tokens[i]]
                i += 1
                limit_value = ''
                
                # Get limit value
                while i < len(tokens):
                    if isinstance(tokens[i], Token):
                        if tokens[i].type in (TokenType.WHITESPACE, TokenType.NEWLINE):
                            limit_tokens.append(tokens[i])
                            i += 1
                            continue
                        elif tokens[i].type == TokenType.NUMBER:
                            limit_value = tokens[i].value
                            limit_tokens.append(tokens[i])
                            i += 1
                            break
                        elif tokens[i].value == '(':
                            # TOP (n)
                            limit_tokens.append(tokens[i])
                            i += 1
                            continue
                        elif tokens[i].value == ')':
                            limit_tokens.append(tokens[i])
                            i += 1
                            break
                        else:
                            break
                    break
                
                metadata = {'limit_type': 'TOP', 'limit_value': limit_value}
                result.append(TokenGroup(GroupType.LIMIT_CLAUSE, limit_tokens, name='TOP', metadata=metadata))
            
            # FETCH FIRST (Oracle, PostgreSQL)
            elif keyword == 'FETCH':
                limit_tokens = [tokens[i]]
                i += 1
                limit_value = ''
                
                # Get FIRST/NEXT and count
                while i < len(tokens):
                    if isinstance(tokens[i], Token):
                        if tokens[i].type in (TokenType.WHITESPACE, TokenType.NEWLINE):
                            limit_tokens.append(tokens[i])
                            i += 1
                            continue
                        elif tokens[i].type == TokenType.KEYWORD and tokens[i].value.upper() in ('FIRST', 'NEXT'):
                            limit_tokens.append(tokens[i])
                            i += 1
                            continue
                        elif tokens[i].type == TokenType.NUMBER:
                            limit_value = tokens[i].value
                            limit_tokens.append(tokens[i])
                            i += 1
                            continue
                        elif tokens[i].type == TokenType.KEYWORD and tokens[i].value.upper() in ('ROW', 'ROWS', 'ONLY'):
                            limit_tokens.append(tokens[i])
                            i += 1
                            if tokens[i-1].value.upper() == 'ONLY':
                                break
                            continue
                        else:
                            break
                    break
                
                metadata = {'limit_type': 'FETCH FIRST', 'limit_value': limit_value}
                result.append(TokenGroup(GroupType.LIMIT_CLAUSE, limit_tokens, name='FETCH FIRST', metadata=metadata))
            else:
                result.append(tokens[i])
                i += 1
        else:
            result.append(tokens[i])
            i += 1
    
    return result


def group_by_clauses_enhanced(tokens: List[Union[Token, TokenGroup]], dialect: SQLDialect) -> List[TokenGroup]:
    """
    Enhanced version of group_by_clauses that creates specific clause types.
    Instead of generic CLAUSE, creates SELECT_CLAUSE, FROM_CLAUSE, etc.
    
    Args:
        tokens: List of tokens and groups
        dialect: SQL dialect
        
    Returns:
        List of TokenGroup objects with specific clause types
    """
    # Clause keywords that start a new clause
    clause_keywords = {
        'select': GroupType.SELECT_CLAUSE,
        'from': GroupType.FROM_CLAUSE,
        'where': GroupType.WHERE_CLAUSE,
        'group': GroupType.GROUP_BY_CLAUSE,
        'having': GroupType.HAVING_CLAUSE,
        'order': GroupType.ORDER_BY_CLAUSE,
        'union': GroupType.UNION_CLAUSE,
        'on': GroupType.ON_CONDITION,
    }
    
    # JOIN modifier keywords (INNER, LEFT, etc.)
    join_modifiers = {'inner', 'left', 'right', 'full', 'cross', 'outer'}
    
    # Generic clause keywords (use CLAUSE type)
    generic_keywords = {'with', 'insert', 'update', 'delete', 'create', 'alter', 'drop', 'into', 'values', 'set', 'intersect', 'except'}
    
    clauses = []
    current_clause = []
    current_clause_name = None
    current_clause_type = GroupType.CLAUSE
    
    i = 0
    while i < len(tokens):
        token = tokens[i]
        
        # Check if this token starts a new clause
        if isinstance(token, Token) and token.type == TokenType.KEYWORD:
            keyword_lower = token.value.lower()
            
            # Special handling for JOIN keywords
            if keyword_lower in join_modifiers or keyword_lower == 'join':
                # Look ahead to see if this is a multi-word JOIN (e.g., INNER JOIN, LEFT OUTER JOIN)
                join_parts = []
                j = i
                
                # Collect join type keywords
                while j < len(tokens):
                    if isinstance(tokens[j], Token) and tokens[j].type == TokenType.KEYWORD:
                        kw = tokens[j].value.lower()
                        if kw in join_modifiers or kw == 'join':
                            join_parts.append(tokens[j].value.upper())
                            j += 1
                        else:
                            break
                    elif isinstance(tokens[j], Token) and tokens[j].type in (TokenType.WHITESPACE, TokenType.NEWLINE):
                        j += 1
                    else:
                        break
                
                # If we found a complete JOIN, save previous clause and start new one
                if 'JOIN' in join_parts or keyword_lower == 'join':
                    # Save previous clause
                    if current_clause:
                        clauses.append(TokenGroup(
                            current_clause_type,
                            current_clause,
                            name=current_clause_name
                        ))
                    
                    # Start new JOIN clause - collect all tokens up to j
                    current_clause = []
                    while i < j:
                        current_clause.append(tokens[i])
                        i += 1
                    current_clause_name = ' '.join(join_parts)
                    current_clause_type = GroupType.JOIN_CLAUSE
                    continue
            
            # Handle other clause keywords
            elif keyword_lower in clause_keywords or keyword_lower in generic_keywords:
                # Save previous clause
                if current_clause:
                    clauses.append(TokenGroup(
                        current_clause_type,
                        current_clause,
                        name=current_clause_name
                    ))
                
                # Start new clause
                current_clause = [token]
                current_clause_name = token.value.upper()
                current_clause_type = clause_keywords.get(keyword_lower, GroupType.CLAUSE)
                i += 1
                continue
        
        # Add to current clause
        current_clause.append(token)
        i += 1
    
    # Add final clause
    if current_clause:
        clauses.append(TokenGroup(
            current_clause_type,
            current_clause,
            name=current_clause_name
        ))
    
    return clauses


def _enrich_join_metadata(clauses: List[TokenGroup]) -> List[TokenGroup]:
    """
    Add metadata to JOIN_CLAUSE groups created by group_by_clauses_enhanced.
    
    Args:
        clauses: List of clause groups (may include JOIN_CLAUSE groups)
        
    Returns:
        List of clause groups with JOIN metadata enriched
    """
    result = []
    
    for i, clause in enumerate(clauses):
        if clause.group_type == GroupType.JOIN_CLAUSE:
            # Extract metadata from JOIN tokens
            table_name = ''
            alias = ''
            has_on = False
            
            # Find table name and alias
            for token in clause.tokens:
                if isinstance(token, Token):
                    if token.type == TokenType.IDENTIFIER:
                        if not table_name:
                            table_name = token.value
                        else:
                            # Second identifier is alias
                            alias = token.value
                    elif token.type == TokenType.KEYWORD and token.value.upper() == 'AS':
                        # Skip AS keyword, next identifier is alias
                        pass
            
            # Check if next clause is ON_CONDITION
            if i + 1 < len(clauses):
                next_clause = clauses[i + 1]
                if isinstance(next_clause, TokenGroup) and next_clause.group_type == GroupType.ON_CONDITION:
                    has_on = True
            
            metadata = {
                'join_type': clause.name if clause.name else 'JOIN',
                'table': table_name if table_name else '?',
                'alias': alias,
                'has_on': has_on
            }
            
            result.append(TokenGroup(clause.group_type, clause.tokens, clause.name, metadata))
        else:
            result.append(clause)
    
    return result


def group_by_clauses(tokens: List[Union[Token, TokenGroup]]) -> List[TokenGroup]:
    """
    Enhanced version of group_by_clauses that creates specific clause types.
    Instead of generic CLAUSE, creates SELECT_CLAUSE, FROM_CLAUSE, etc.
    
    Args:
        tokens: List of tokens and groups
        dialect: SQL dialect
        
    Returns:
        List of TokenGroup objects with specific clause types
    """
    # Clause keywords that start a new clause
    clause_keywords = {
        'select': GroupType.SELECT_CLAUSE,
        'from': GroupType.FROM_CLAUSE,
        'where': GroupType.WHERE_CLAUSE,
        'group': GroupType.GROUP_BY_CLAUSE,
        'having': GroupType.HAVING_CLAUSE,
        'order': GroupType.ORDER_BY_CLAUSE,
        'union': GroupType.UNION_CLAUSE,
        'on': GroupType.ON_CONDITION,
    }
    
    # JOIN modifier keywords (INNER, LEFT, etc.)
    join_modifiers = {'inner', 'left', 'right', 'full', 'cross', 'outer'}
    
    # Generic clause keywords (use CLAUSE type)
    generic_keywords = {'with', 'insert', 'update', 'delete', 'create', 'alter', 'drop', 'into', 'values', 'set', 'intersect', 'except'}
    
    clauses = []
    current_clause = []
    current_clause_name = None
    current_clause_type = GroupType.CLAUSE
    
    i = 0
    while i < len(tokens):
        token = tokens[i]
        
        # Check if this token starts a new clause
        if isinstance(token, Token) and token.type == TokenType.KEYWORD:
            keyword_lower = token.value.lower()
            
            # Special handling for JOIN keywords
            if keyword_lower in join_modifiers or keyword_lower == 'join':
                # Look ahead to see if this is a multi-word JOIN (e.g., INNER JOIN, LEFT OUTER JOIN)
                join_parts = []
                j = i
                
                # Collect join type keywords
                while j < len(tokens):
                    if isinstance(tokens[j], Token) and tokens[j].type == TokenType.KEYWORD:
                        kw = tokens[j].value.lower()
                        if kw in join_modifiers or kw == 'join':
                            join_parts.append(tokens[j].value.upper())
                            j += 1
                            if kw == 'join':
                                break
                        else:
                            break
                    elif isinstance(tokens[j], Token) and tokens[j].type in (TokenType.WHITESPACE, TokenType.NEWLINE):
                        j += 1
                    else:
                        break
                
                # If we found a complete JOIN, save previous clause and start new one
                if 'JOIN' in join_parts or keyword_lower == 'join':
                    # Save previous clause
                    if current_clause:
                        clauses.append(TokenGroup(
                            current_clause_type,
                            current_clause,
                            name=current_clause_name
                        ))
                    
                    # Start new JOIN clause - collect all tokens up to j
                    current_clause = []
                    while i < j:
                        current_clause.append(tokens[i])
                        i += 1
                    current_clause_name = ' '.join(join_parts)
                    current_clause_type = GroupType.JOIN_CLAUSE
                    continue
            
            # Handle other clause keywords
            elif keyword_lower in clause_keywords or keyword_lower in generic_keywords:
                # Save previous clause
                if current_clause:
                    clauses.append(TokenGroup(
                        current_clause_type,
                        current_clause,
                        name=current_clause_name
                    ))
                
                # Start new clause
                current_clause = [token]
                current_clause_name = token.value.upper()
                current_clause_type = clause_keywords.get(keyword_lower, GroupType.CLAUSE)
                i += 1
                continue
        
        # Add to current clause
        current_clause.append(token)
        i += 1
    
    # Add final clause
    if current_clause:
        clauses.append(TokenGroup(
            current_clause_type,
            current_clause,
            name=current_clause_name
        ))
    
    return clauses


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

