# tokenizer/grouping.py
"""
Token grouping logic: parentheses, statements, clauses, and general grouping helpers.
"""
from typing import List, Union
from .base import Token, TokenType
from ..dialects import SQLDialect

class GroupType:
    STATEMENT = "statement"
    CLAUSE = "clause"
    PARENTHESIS = "parenthesis"
    FUNCTION = "function"
    # ... add other group types as needed ...

class TokenGroup:
    def __init__(self, group_type, tokens, name=None, metadata=None):
        self.group_type = group_type
        self.tokens = tokens
        self.name = name
        self.metadata = metadata or {}

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
