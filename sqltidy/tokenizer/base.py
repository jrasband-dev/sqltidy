# tokenizer/base.py
"""
Core tokenization logic, types, and grouping functionality.
Consolidated module containing all tokenizer functionality.
"""

import re
from typing import Union, NamedTuple, Pattern, Literal, List, Dict, Optional
from enum import Enum
from dataclasses import dataclass
from ..dialects import get_dialect, SQLDialect


# ==============================================================================
# ENUMS AND TYPES
# ==============================================================================


class TokenType(Enum):
    """Token type classification."""

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


class GroupType:
    """Constants for different types of token groups."""

    STATEMENT = "statement"
    CLAUSE = "clause"
    PARENTHESIS = "parenthesis"
    FUNCTION = "function"
    # Semantic group types
    JOIN_CLAUSE = "join_clause"
    CASE_EXPRESSION = "case_expression"
    WINDOW_FUNCTION = "window_function"
    CTE = "cte"
    SUBQUERY = "subquery"
    SELECT_CLAUSE = "select_clause"
    FROM_CLAUSE = "from_clause"
    WHERE_CLAUSE = "where_clause"
    GROUP_BY_CLAUSE = "group_by_clause"
    HAVING_CLAUSE = "having_clause"
    ORDER_BY_CLAUSE = "order_by_clause"
    UNION_CLAUSE = "union_clause"
    LIMIT_CLAUSE = "limit_clause"


class SemanticLevel(Enum):
    """Semantic processing levels for tokenization."""

    BASIC = "basic"
    GROUPED = "grouped"
    STRUCTURED = "structured"
    SEMANTIC = "semantic"


# ==============================================================================
# TOKEN PATTERN DEFINITIONS
# ==============================================================================


@dataclass(frozen=True)
class TokenPattern:
    """Defines a pattern for matching tokens."""

    name: str
    pattern: Pattern

    @property
    def regex(self) -> Pattern:
        return self.pattern


# ==============================================================================
# TOKEN AND GROUP CLASSES
# ==============================================================================


class Token(NamedTuple):
    """Represents a single SQL token instance with its value and type."""

    value: str
    type: TokenType


class TokenGroup:
    """Represents a group of tokens (parentheses, functions, clauses, etc.)."""

    def __init__(self, group_type, tokens, name=None, metadata=None):
        self.group_type = group_type
        self.tokens = tokens
        self.name = name
        self.metadata = metadata or {}

    def get_text(self) -> str:
        """Recursively flatten this group to a SQL string."""
        result = []
        for item in self.tokens:
            if isinstance(item, Token):
                result.append(item.value)
            elif isinstance(item, TokenGroup):
                result.append(item.get_text())
        return "".join(result)

    def __repr__(self):
        return f"TokenGroup({self.group_type}, {len(self.tokens)} tokens)"


# ==============================================================================
# TOKENIZATION FUNCTIONS
# ==============================================================================


def get_token_type(
    token: str, dialect: Union[str, SQLDialect] = "sqlserver"
) -> TokenType:
    """Determine the type of a token based on its value and dialect."""
    if not token:
        return TokenType.UNKNOWN

    if isinstance(dialect, str):
        dialect_obj = get_dialect(dialect)
    else:
        dialect_obj = dialect

    # Check for comments
    # Multi-line: /* ... */
    # Single-line: -- ... or # ... (MySQL)
    # For # comments, require more than just the # character to avoid false positives
    if token.startswith("--") or (token.startswith("/*") and token.endswith("*/")):
        return TokenType.COMMENT
    if token.startswith("#") and len(token) > 1:
        return TokenType.COMMENT

    if token.isspace():
        if "\n" in token:
            return TokenType.NEWLINE
        return TokenType.WHITESPACE

    if (token.startswith("'") and token.endswith("'")) or (
        token.startswith('"') and token.endswith('"')
    ):
        return TokenType.STRING

    if token.replace(".", "", 1).isdigit():
        return TokenType.NUMBER

    if token in ("<=", ">=", "<>", "!=", "<", ">", "=", "+", "-", "*", "/"):
        return TokenType.OPERATOR

    if token in ("(", ")", ",", ".", ";", "[", "]"):
        return TokenType.PUNCTUATION

    if dialect_obj.is_keyword(token):
        return TokenType.KEYWORD

    id_chars = dialect_obj.identifier_chars
    if id_chars:
        pattern = f"^[A-Za-z_{id_chars}][A-Za-z0-9_{id_chars}]*$"
    else:
        pattern = r"^[A-Za-z_][A-Za-z0-9_]*$"

    if re.match(pattern, token):
        return TokenType.IDENTIFIER

    return TokenType.UNKNOWN


def tokenize(sql: str, dialect: str = "sqlserver") -> List[Token]:
    """
    Tokenize SQL string using TokenPattern definitions from dialect.

    Iterates through the input SQL and matches each position against
    token patterns from the dialect in order. The first matching pattern is used.

    Args:
        sql: SQL string to tokenize
        dialect: SQL dialect for keyword detection and token patterns

    Returns:
        List of Token instances
    """
    if isinstance(dialect, str):
        dialect_obj = get_dialect(dialect)
    else:
        dialect_obj = dialect

    tokens = []
    position = 0

    # Get token patterns from dialect
    token_patterns = dialect_obj.get_token_patterns()

    while position < len(sql):
        matched = False

        # Try each pattern in order
        for token_pattern in token_patterns:
            match = token_pattern.pattern.match(sql, position)
            if match:
                token_value = match.group(0)
                token_type = get_token_type(token_value, dialect_obj)
                tokens.append(Token(token_value, token_type))
                position = match.end()
                matched = True
                break

        if not matched:
            # Should never happen if FALLBACK pattern is properly defined
            position += 1

    return tokens


def tokenize_with_types(
    sql: str,
    dialect: Union[str, SQLDialect] = "sqlserver",
    level: Union[str, SemanticLevel] = SemanticLevel.BASIC,
) -> List[Union[Token, TokenGroup]]:
    """
    Tokenize SQL with type information.

    Args:
        sql: SQL string to tokenize
        dialect: SQL dialect for keyword detection
        level: Semantic processing level (currently delegates to tokenize)

    Returns:
        List of Token instances or TokenGroup instances
    """
    # Currently semantic level processing is done separately
    # This function maintains backward compatibility
    return tokenize(sql, dialect)


# ==============================================================================
# TOKEN GROUPING FUNCTIONS
# ==============================================================================


def group_parentheses(
    tokens: List[Union[Token, TokenGroup]], dialect: SQLDialect = None
) -> List[Union[Token, TokenGroup]]:
    """
    Group tokens within parentheses into TokenGroup objects.
    This handles nested parentheses recursively.

    Args:
        tokens: List of tokens to process
        dialect: SQL dialect for function and DDL keyword detection

    Returns:
        List with parentheses grouped into TokenGroup objects
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
                    is_ddl_object = False

                    # Find the position of prev_token in result
                    prev_token_found = False
                    for k in range(len(result) - 1, -1, -1):
                        if isinstance(result[k], Token):
                            if result[k] == prev_token:
                                prev_token_found = True
                                continue

                            if prev_token_found:
                                # Skip whitespace, newline, and punctuation
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
                                elif result[k].type == TokenType.IDENTIFIER:
                                    continue
                                elif (
                                    result[k].type == TokenType.KEYWORD
                                    and dialect
                                    and dialect.is_ddl_object_keyword(result[k].value)
                                ):
                                    is_ddl_object = True
                                    break
                                else:
                                    break

                    is_function = not is_ddl_object and (
                        (dialect and dialect.is_function(prev_token.value))
                        or prev_token.type == TokenType.IDENTIFIER
                    )

                    if is_function:
                        # Function call - include function name
                        result = [r for r in result if r != prev_token]
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

    Args:
        tokens: List of tokens to group

    Returns:
        List of TokenGroup objects with group_type STATEMENT
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


def group_by_clauses(tokens: List[Union[Token, TokenGroup]]) -> List[TokenGroup]:
    """
    Group tokens by SQL clauses (SELECT, FROM, WHERE, etc.).

    Args:
        tokens: List of tokens to group

    Returns:
        List of TokenGroup objects with group_type CLAUSE
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
    dialect: Union[str, SQLDialect] = None,
) -> Union[List[Union[Token, TokenGroup]], List[TokenGroup]]:
    """
    Group tokens into logical structures.

    Args:
        tokens: List of Token objects
        group_parentheses_flag: Group tokens within parentheses
        group_statements_flag: Group into complete statements (by semicolon)
        group_clauses_flag: Group by SQL clauses (SELECT, FROM, WHERE, etc.)
        dialect: SQL dialect for function detection

    Returns:
        List of tokens and/or TokenGroup objects
    """
    if isinstance(dialect, str):
        dialect_obj = get_dialect(dialect)
    else:
        dialect_obj = dialect

    result = list(tokens)  # Start with copy of tokens

    # Apply groupings in order
    if group_parentheses_flag:
        result = group_parentheses(result, dialect_obj)

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


# ==============================================================================
# UTILITY FUNCTIONS
# ==============================================================================


def print_token_tree(items: List[Union[Token, TokenGroup]], indent: int = 0):
    """
    Print a hierarchical view of tokens and groups.
    Useful for debugging and visualization.

    Args:
        items: List of tokens and groups to print
        indent: Current indentation level
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
            print(f"{prefix}TokenGroup({item.group_type}{name_str}):")
            print_token_tree(item.tokens, indent + 1)


def is_keyword(token: str, dialect: Union[str, SQLDialect] = "sqlserver") -> bool:
    """
    Check if a token is a keyword in the specified dialect (case-insensitive).

    Args:
        token: The token to check
        dialect: The SQL dialect to use (name or SQLDialect instance)

    Returns:
        True if the token is a keyword, False otherwise
    """
    if isinstance(dialect, str):
        dialect_obj = get_dialect(dialect)
    else:
        dialect_obj = dialect

    return dialect_obj.is_keyword(token)
