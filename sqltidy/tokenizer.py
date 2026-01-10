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

    STATEMENT = "statement"  # Complete SQL statement
    CLAUSE = "clause"  # SQL clause (SELECT, FROM, WHERE, etc.)
    PARENTHESIS = "parenthesis"  # Content within parentheses
    FUNCTION = "function"  # Function call with arguments
    EXPRESSION = "expression"  # Expression or value list
    IDENTIFIER_LIST = "identifier_list"  # Comma-separated identifiers
    CONDITION = "condition"  # Boolean condition
    COMMENT_BLOCK = "comment_block"  # Comment or block of comments

    # Semantic SQL patterns
    CASE_EXPRESSION = "case_expression"  # CASE...END expression
    WINDOW_FUNCTION = "window_function"  # Window function with OVER clause
    SUBQUERY = "subquery"  # SELECT within parentheses

    # Specific SQL clauses
    SELECT_CLAUSE = "select_clause"  # SELECT clause
    FROM_CLAUSE = "from_clause"  # FROM clause
    WHERE_CLAUSE = "where_clause"  # WHERE clause
    JOIN_CLAUSE = "join_clause"  # JOIN clause (any type)
    GROUP_BY_CLAUSE = "group_by_clause"  # GROUP BY clause
    HAVING_CLAUSE = "having_clause"  # HAVING clause
    ORDER_BY_CLAUSE = "order_by_clause"  # ORDER BY clause

    # Advanced SQL constructs
    CTE = "cte"  # Common Table Expression (WITH clause)
    UNION_CLAUSE = "union_clause"  # UNION/UNION ALL clause
    LIMIT_CLAUSE = "limit_clause"  # LIMIT/TOP/FETCH FIRST clause

    # Other groupings
    COLUMN_LIST = "column_list"  # List of columns
    ON_CONDITION = "on_condition"  # ON condition in JOIN


class SemanticLevel(Enum):
    """Levels of semantic analysis to apply during tokenization"""

    BASIC = "basic"  # Just Token objects, no grouping
    GROUPED = "grouped"  # + parentheses and function grouping
    STRUCTURED = "structured"  # + statements and basic clauses
    SEMANTIC = "semantic"  # + JOINs, CASE, CTEs, window functions, etc. (FULL)


class TokenGroup:
    """Represents a group of related tokens with optional metadata

    Metadata examples:
    - CASE_EXPRESSION: {'has_else': bool}
    - JOIN_CLAUSE: {'join_type': str, 'table': str, 'alias': str, 'has_on': bool}
    - WINDOW_FUNCTION: {'function_name': str, 'partition_by': List[str], 'order_by': List[str]}
    - CTE: {'cte_name': str, 'columns': List[str]}
    - SUBQUERY: {'has_alias': bool, 'alias': str}
    """

    def __init__(
        self,
        group_type: GroupType,
        tokens: List[Union[Token, "TokenGroup"]],
        name: Optional[str] = None,
        metadata: Optional[dict] = None,
    ):
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
        # Render inner content first
        inner_parts = []
        for item in self.tokens:
            if isinstance(item, Token):
                inner_parts.append(item.value)
            elif isinstance(item, TokenGroup):
                inner_parts.append(item.get_text())
        inner = "".join(inner_parts)

        # Wrap or augment based on group type
        if (
            self.group_type == GroupType.PARENTHESIS
            or self.group_type == GroupType.SUBQUERY
        ):
            return f"({inner})"

        if self.group_type == GroupType.FUNCTION:
            # Expect first token to be the function name
            func_name = ""
            args_text = inner
            if self.tokens and isinstance(self.tokens[0], Token):
                func_name = self.tokens[0].value
                # Re-render args without the first token
                arg_parts = []
                for item in self.tokens[1:]:
                    if isinstance(item, Token):
                        arg_parts.append(item.value)
                    elif isinstance(item, TokenGroup):
                        arg_parts.append(item.get_text())
                args_text = "".join(arg_parts)
            return f"{func_name}({args_text})"

        # Default: just return inner content for other group types
        return inner

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

    def find_groups(self, group_type: GroupType) -> List["TokenGroup"]:
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

    def get_clause_by_name(self, name: str) -> Optional["TokenGroup"]:
        """Get a clause by its name (case-insensitive)

        Args:
            name: The clause name to search for (e.g., 'SELECT', 'FROM')

        Returns:
            The first matching TokenGroup or None
        """
        name_upper = name.upper()
        for item in self.tokens:
            if (
                isinstance(item, TokenGroup)
                and item.name
                and item.name.upper() == name_upper
            ):
                return item
        return None


# Backward compatibility: Keep SQL_SERVER_KEYWORDS for existing code
# New code should use get_dialect('sqlserver').keywords instead
def _get_sql_server_keywords():
    """Lazy load SQL Server keywords from dialect"""
    return get_dialect("sqlserver").keywords


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


def get_token_type(
    token: str, dialect: Union[str, SQLDialect] = "sqlserver"
) -> TokenType:
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
    if token.startswith("--") or (token.startswith("/*") and token.endswith("*/")):
        return TokenType.COMMENT

    # Check for whitespace
    if token.isspace():
        if "\n" in token:
            return TokenType.NEWLINE
        return TokenType.WHITESPACE

    # Check for strings
    if (token.startswith("'") and token.endswith("'")) or (
        token.startswith('"') and token.endswith('"')
    ):
        return TokenType.STRING

    # Check for numbers
    if token.replace(".", "", 1).isdigit():
        return TokenType.NUMBER

    # Check for operators
    if token in ("<=", ">=", "<>", "!=", "<", ">", "=", "+", "-", "*", "/"):
        return TokenType.OPERATOR

    # Check for punctuation
    if token in ("(", ")", ",", ".", ";", "[", "]"):
        return TokenType.PUNCTUATION

    # Check for keywords (case-insensitive, dialect-aware)
    if dialect_obj.is_keyword(token):
        return TokenType.KEYWORD

    # Check for identifiers (including variables and temp tables)
    # Use dialect-specific identifier chars
    id_chars = dialect_obj.identifier_chars
    if id_chars:
        pattern = f"^[A-Za-z_{id_chars}][A-Za-z0-9_{id_chars}]*$"
    else:
        pattern = r"^[A-Za-z_][A-Za-z0-9_]*$"
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


def tokenize_with_types(
    sql: str,
    dialect: Union[str, SQLDialect] = "sqlserver",
    level: Union[str, SemanticLevel] = SemanticLevel.BASIC,
) -> Union[List[Token], List[Union[Token, TokenGroup]]]:
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
    if level in (
        SemanticLevel.GROUPED,
        SemanticLevel.STRUCTURED,
        SemanticLevel.SEMANTIC,
    ):
        result = group_parentheses(result, dialect_obj)

    # SEMANTIC level: apply advanced pattern recognition BEFORE clause grouping
    # This allows patterns to match constructs that span multiple clauses
    if level == SemanticLevel.SEMANTIC:
        from .pattern_tokenizer import apply_patterns

        result = apply_patterns(result, dialect_obj)

    # STRUCTURED level: add statements and clauses
    if level in (SemanticLevel.STRUCTURED, SemanticLevel.SEMANTIC):
        result = group_by_statements(result)
        # Group clauses within each statement
        new_result = []
        for item in result:
            if isinstance(item, TokenGroup) and item.group_type == GroupType.STATEMENT:
                clauses = group_by_clauses(item.tokens)
                new_result.append(
                    TokenGroup(GroupType.STATEMENT, clauses, name=item.name)
                )
            else:
                new_result.append(item)
        result = new_result

    return result


# ============================================================================
# Token Grouping Functions
# ============================================================================


def group_parentheses(
    tokens: List[Union[Token, TokenGroup]], dialect: SQLDialect = None
) -> List[Union[Token, TokenGroup]]:
    """
    Group tokens within parentheses into TokenGroup objects.
    This handles nested parentheses recursively.

    Args:
        tokens: List of tokens to process
        dialect: SQL dialect for function and DDL keyword detection
    """
    result = []
    i = 0

    while i < len(tokens):
        token = tokens[i]

        # Only process Token objects for parentheses
        if isinstance(token, Token) and token.value == "(":
            # Find matching closing parenthesis
            depth = 1
            j = i + 1
            while j < len(tokens) and depth > 0:
                if isinstance(tokens[j], Token):
                    if tokens[j].value == "(":
                        depth += 1
                    elif tokens[j].value == ")":
                        depth -= 1
                j += 1

            if depth == 0:
                # Found matching parenthesis
                inner_tokens = tokens[
                    i + 1 : j - 1
                ]  # Exclude the parentheses themselves

                # Recursively group inner tokens
                grouped_inner = group_parentheses(inner_tokens, dialect)

                # Check if this is a function call
                # Look back to see if previous non-whitespace token is an identifier or keyword
                prev_token = None
                for k in range(len(result) - 1, -1, -1):
                    if isinstance(result[k], Token):
                        if result[k].type in (TokenType.IDENTIFIER, TokenType.KEYWORD):
                            prev_token = result[k]
                            break
                        elif result[k].type not in (
                            TokenType.WHITESPACE,
                            TokenType.NEWLINE,
                        ):
                            break

                # SQL function keywords or identifiers followed by parentheses are functions
                if prev_token and (
                    prev_token.type == TokenType.IDENTIFIER
                    or prev_token.type == TokenType.KEYWORD
                ):
                    # Check if this is a DDL object definition (e.g., CREATE TABLE name (...))
                    # Look backwards to find the token before prev_token
                    is_ddl_object = False

                    # Find the position of prev_token in result
                    prev_token_found = False
                    for k in range(len(result) - 1, -1, -1):
                        if isinstance(result[k], Token):
                            if result[k] == prev_token:
                                prev_token_found = True
                                continue  # Skip prev_token itself

                            # After finding prev_token, look for DDL keywords
                            if prev_token_found:
                                # Skip whitespace, newline, and punctuation (like dots in schema.table)
                                if result[k].type in (
                                    TokenType.WHITESPACE,
                                    TokenType.NEWLINE,
                                ):
                                    continue
                                elif (
                                    result[k].type == TokenType.PUNCTUATION
                                    and result[k].value == "."
                                ):
                                    continue
                                # Skip identifiers (schema/database qualifiers like dbo, sys, etc.)
                                elif result[k].type == TokenType.IDENTIFIER:
                                    continue
                                # Check if this is a DDL object keyword using dialect
                                elif (
                                    result[k].type == TokenType.KEYWORD
                                    and dialect
                                    and dialect.is_ddl_object_keyword(result[k].value)
                                ):
                                    is_ddl_object = True
                                    break
                                else:
                                    # Found a different token (e.g., another keyword not in our list), stop looking
                                    break

                    # Use dialect to check if it's a function, or default to identifier heuristic
                    is_function = not is_ddl_object and (
                        (dialect and dialect.is_function(prev_token.value))
                        or prev_token.type == TokenType.IDENTIFIER
                    )

                    if is_function:
                        # Function call - include function name
                        # Remove the token from result
                        result = [r for r in result if r != prev_token]
                        # Remove whitespace between function and parenthesis
                        while (
                            result
                            and isinstance(result[-1], Token)
                            and result[-1].type
                            in (TokenType.WHITESPACE, TokenType.NEWLINE)
                        ):
                            result.pop()

                        group = TokenGroup(
                            GroupType.FUNCTION,
                            [prev_token] + grouped_inner,
                            name=prev_token.value.upper(),
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
        if isinstance(token, Token) and token.value == ";":
            if current_statement:
                statements.append(TokenGroup(GroupType.STATEMENT, current_statement))
                current_statement = []

    # Add remaining tokens as a statement (even without semicolon)
    if current_statement:
        # Skip if only whitespace/newlines (but keep TokenGroups)
        has_content = False
        for t in current_statement:
            if isinstance(t, TokenGroup):
                has_content = True
                break
            elif isinstance(t, Token) and t.type not in (
                TokenType.WHITESPACE,
                TokenType.NEWLINE,
                TokenType.COMMENT,
            ):
                has_content = True
                break

        if has_content:
            statements.append(TokenGroup(GroupType.STATEMENT, current_statement))

    return statements


# ============================================================================
# Backward Compatibility: Simple grouping helpers
# ============================================================================


def group_by_clauses(tokens: List[Union[Token, TokenGroup]]) -> List[TokenGroup]:
    """
    Group tokens by SQL clauses (SELECT, FROM, WHERE, etc.).
    """
    # Clause keywords that start a new clause
    clause_keywords = {
        "select",
        "from",
        "where",
        "group",
        "having",
        "order",
        "join",
        "inner",
        "left",
        "right",
        "full",
        "cross",
        "on",
        "with",
        "insert",
        "update",
        "delete",
        "create",
        "alter",
        "drop",
        "union",
        "intersect",
        "except",
        "into",
        "values",
        "set",
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
                    clauses.append(
                        TokenGroup(
                            GroupType.CLAUSE, current_clause, name=current_clause_name
                        )
                    )

                # Start new clause
                current_clause = [token]
                current_clause_name = token.value.upper()
                continue

        # Add to current clause
        current_clause.append(token)

    # Add final clause
    if current_clause:
        clauses.append(
            TokenGroup(GroupType.CLAUSE, current_clause, name=current_clause_name)
        )

    return clauses


def group_tokens(
    tokens: List[Token],
    group_parentheses_flag: bool = True,
    group_statements_flag: bool = False,
    group_clauses_flag: bool = False,
) -> Union[List[Union[Token, TokenGroup]], List[TokenGroup]]:
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
        if group_statements_flag and all(
            isinstance(r, TokenGroup) and r.group_type == GroupType.STATEMENT
            for r in result
        ):
            new_result = []
            for stmt in result:
                clauses = group_by_clauses(stmt.tokens)
                new_result.append(
                    TokenGroup(GroupType.STATEMENT, clauses, name=stmt.name)
                )
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
            value_str = (
                repr(item.value)
                if len(item.value) <= 20
                else repr(item.value[:20] + "...")
            )
            print(f"{prefix}Token({type_str}: {value_str})")
        elif isinstance(item, TokenGroup):
            name_str = f" '{item.name}'" if item.name else ""
            print(f"{prefix}TokenGroup({item.group_type.value}{name_str}):")
            print_token_tree(item.tokens, indent + 1)


def is_keyword(token: str, dialect: Union[str, SQLDialect] = "sqlserver") -> bool:
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
    if name == "SQL_SERVER_KEYWORDS":
        global SQL_SERVER_KEYWORDS
        if SQL_SERVER_KEYWORDS is None:
            SQL_SERVER_KEYWORDS = _get_sql_server_keywords()
        return SQL_SERVER_KEYWORDS
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")
