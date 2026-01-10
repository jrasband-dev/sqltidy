"""
Declarative SQL pattern definitions.

These patterns compose the tiny matchers into meaningful SQL constructs
like CASE expressions, JOINs, CTEs, etc.
"""

from typing import Optional
from . import Pattern, MatchResult, MatchContext


class CTEPattern(Pattern):
    """
    Match Common Table Expressions (WITH clauses).

    Syntax:
        WITH cte_name [(column1, column2, ...)] AS (
            SELECT ...
        )
        [, cte_name2 AS (...)]
    """

    def __init__(self, name: Optional[str] = None):
        super().__init__(name=name or "CTE")

    def match(self, context: MatchContext) -> MatchResult:
        """Match a CTE definition."""
        from ..tokenizer import Token, TokenType, GroupType, TokenGroup

        # Must start with WITH keyword
        if context.at_end():
            return MatchResult(success=False)

        current = context.current()
        if not (
            isinstance(current, Token)
            and current.type == TokenType.KEYWORD
            and current.value.upper() == "WITH"
        ):
            return MatchResult(success=False)

        matched_tokens = [current]
        current_context = context.advance(1)

        # Skip whitespace
        while not current_context.at_end():
            curr = current_context.current()
            if isinstance(curr, Token) and curr.type in (
                TokenType.WHITESPACE,
                TokenType.NEWLINE,
            ):
                matched_tokens.append(curr)
                current_context = current_context.advance(1)
            else:
                break

        # Now expect identifier (CTE name)
        if current_context.at_end():
            return MatchResult(success=False)

        current = current_context.current()
        if not (isinstance(current, Token) and current.type == TokenType.IDENTIFIER):
            return MatchResult(success=False)

        cte_name = current.value
        matched_tokens.append(current)
        current_context = current_context.advance(1)

        columns = []

        # Optional column list
        if not current_context.at_end():
            curr = current_context.current()
            if isinstance(curr, Token) and curr.value == "(":
                # This might be a column list or the AS clause
                # Look ahead to distinguish
                peek_idx = 1
                is_column_list = False
                while current_context.peek(peek_idx) is not None:
                    peek = current_context.peek(peek_idx)
                    if isinstance(peek, Token):
                        if (
                            peek.type == TokenType.KEYWORD
                            and peek.value.upper() == "AS"
                        ):
                            is_column_list = True
                            break
                        elif (
                            peek.type == TokenType.KEYWORD
                            and peek.value.upper() == "SELECT"
                        ):
                            is_column_list = False
                            break
                    peek_idx += 1

                if is_column_list:
                    # Extract column list
                    matched_tokens.append(curr)
                    current_context = current_context.advance(1)

                    # Collect until closing paren
                    paren_depth = 1
                    while not current_context.at_end() and paren_depth > 0:
                        curr = current_context.current()
                        if isinstance(curr, Token):
                            if curr.value == "(":
                                paren_depth += 1
                            elif curr.value == ")":
                                paren_depth -= 1
                            elif curr.type == TokenType.IDENTIFIER:
                                columns.append(curr.value)

                        matched_tokens.append(curr)
                        current_context = current_context.advance(1)

                        if paren_depth == 0:
                            break

        # Must have AS keyword
        while not current_context.at_end():
            curr = current_context.current()
            if isinstance(curr, Token):
                if curr.type == TokenType.KEYWORD and curr.value.upper() == "AS":
                    matched_tokens.append(curr)
                    current_context = current_context.advance(1)
                    break
                elif curr.type in (TokenType.WHITESPACE, TokenType.NEWLINE):
                    matched_tokens.append(curr)
                    current_context = current_context.advance(1)
                else:
                    # No AS keyword found
                    return MatchResult(success=False)
            else:
                matched_tokens.append(curr)
                current_context = current_context.advance(1)

        # Must have opening parenthesis or PARENTHESIS group for subquery
        while not current_context.at_end():
            curr = current_context.current()

            # Check if it's already a PARENTHESIS group (from group_parentheses)
            if (
                isinstance(curr, TokenGroup)
                and curr.group_type == GroupType.PARENTHESIS
            ):
                matched_tokens.append(curr)
                current_context = current_context.advance(1)
                break
            # Or a raw opening paren (if parentheses grouping hasn't run yet)
            elif isinstance(curr, Token) and curr.value == "(":
                matched_tokens.append(curr)
                current_context = current_context.advance(1)

                # Collect subquery until matching closing paren
                paren_depth = 1
                while not current_context.at_end() and paren_depth > 0:
                    curr = current_context.current()
                    if isinstance(curr, Token):
                        if curr.value == "(":
                            paren_depth += 1
                        elif curr.value == ")":
                            paren_depth -= 1

                    matched_tokens.append(curr)
                    current_context = current_context.advance(1)

                    if paren_depth == 0:
                        break
                break
            elif isinstance(curr, Token) and curr.type in (
                TokenType.WHITESPACE,
                TokenType.NEWLINE,
            ):
                matched_tokens.append(curr)
                current_context = current_context.advance(1)
            else:
                return MatchResult(success=False)

        return MatchResult(
            success=True,
            matched_tokens=matched_tokens,
            end_index=current_context.start_index,
            metadata={"cte_name": cte_name, "columns": columns},
            group_type=GroupType.CTE,
            group_name=cte_name,
        )


class WindowFunctionPattern(Pattern):
    """
    Match window functions with OVER clause.

    Syntax:
        function_name(...) OVER ([PARTITION BY ...] [ORDER BY ...])
    """

    def __init__(self, name: Optional[str] = None):
        super().__init__(name=name or "WindowFunction")

    def match(self, context: MatchContext) -> MatchResult:
        """Match a window function."""
        from ..tokenizer import Token, TokenType, TokenGroup, GroupType

        # Must start with a function name followed by OVER
        if context.at_end():
            return MatchResult(success=False)

        current = context.current()

        # Check for function (identifier followed by parenthesis group)
        if not (isinstance(current, Token) and current.type == TokenType.IDENTIFIER):
            return MatchResult(success=False)

        function_name = current.value
        matched_tokens = [current]
        current_context = context.advance(1)

        # Must be followed by function arguments (parentheses)
        if current_context.at_end():
            return MatchResult(success=False)

        curr = current_context.current()

        # Check for function call pattern
        if isinstance(curr, TokenGroup) and curr.group_type == GroupType.FUNCTION:
            matched_tokens.append(curr)
            current_context = current_context.advance(1)
        elif isinstance(curr, Token) and curr.value == "(":
            # Collect function arguments
            matched_tokens.append(curr)
            current_context = current_context.advance(1)

            paren_depth = 1
            while not current_context.at_end() and paren_depth > 0:
                curr = current_context.current()
                if isinstance(curr, Token):
                    if curr.value == "(":
                        paren_depth += 1
                    elif curr.value == ")":
                        paren_depth -= 1

                matched_tokens.append(curr)
                current_context = current_context.advance(1)

                if paren_depth == 0:
                    break
        else:
            return MatchResult(success=False)

        # Skip whitespace
        while not current_context.at_end():
            curr = current_context.current()
            if isinstance(curr, Token) and curr.type in (
                TokenType.WHITESPACE,
                TokenType.NEWLINE,
            ):
                matched_tokens.append(curr)
                current_context = current_context.advance(1)
            else:
                break

        # Must be followed by OVER keyword
        if current_context.at_end():
            return MatchResult(success=False)

        curr = current_context.current()
        if not (
            isinstance(curr, Token)
            and curr.type == TokenType.KEYWORD
            and curr.value.upper() == "OVER"
        ):
            return MatchResult(success=False)

        matched_tokens.append(curr)
        current_context = current_context.advance(1)

        # Collect OVER clause content
        partition_by = []
        order_by = []

        # Skip whitespace
        while not current_context.at_end():
            curr = current_context.current()
            if isinstance(curr, Token) and curr.type in (
                TokenType.WHITESPACE,
                TokenType.NEWLINE,
            ):
                matched_tokens.append(curr)
                current_context = current_context.advance(1)
            else:
                break

        # Must have opening parenthesis
        if current_context.at_end():
            return MatchResult(success=False)

        curr = current_context.current()
        if not (isinstance(curr, Token) and curr.value == "("):
            return MatchResult(success=False)

        matched_tokens.append(curr)
        current_context = current_context.advance(1)

        # Collect OVER clause content until closing paren
        paren_depth = 1
        in_partition = False
        in_order = False

        while not current_context.at_end() and paren_depth > 0:
            curr = current_context.current()

            if isinstance(curr, Token):
                if curr.value == "(":
                    paren_depth += 1
                elif curr.value == ")":
                    paren_depth -= 1
                elif curr.type == TokenType.KEYWORD:
                    kw = curr.value.upper()
                    if kw == "PARTITION":
                        in_partition = True
                        in_order = False
                    elif kw == "ORDER":
                        in_partition = False
                        in_order = True
                elif curr.type == TokenType.IDENTIFIER:
                    if in_partition:
                        partition_by.append(curr.value)
                    elif in_order:
                        order_by.append(curr.value)

            matched_tokens.append(curr)
            current_context = current_context.advance(1)

            if paren_depth == 0:
                break

        return MatchResult(
            success=True,
            matched_tokens=matched_tokens,
            end_index=current_context.start_index,
            metadata={
                "function_name": function_name,
                "partition_by": partition_by,
                "order_by": order_by,
            },
            group_type=GroupType.WINDOW_FUNCTION,
            group_name=function_name,
        )


class SubqueryPattern(Pattern):
    """
    Match subqueries (SELECT within parentheses).

    Syntax:
        (SELECT ...) [AS alias]
    """

    def __init__(self, name: Optional[str] = None):
        super().__init__(name=name or "Subquery")

    def match(self, context: MatchContext) -> MatchResult:
        """Match a subquery."""
        from ..tokenizer import Token, TokenType, GroupType

        # Must start with opening parenthesis
        if context.at_end():
            return MatchResult(success=False)

        current = context.current()
        if not (isinstance(current, Token) and current.value == "("):
            return MatchResult(success=False)

        matched_tokens = [current]
        current_context = context.advance(1)

        # Skip whitespace
        while not current_context.at_end():
            curr = current_context.current()
            if isinstance(curr, Token) and curr.type in (
                TokenType.WHITESPACE,
                TokenType.NEWLINE,
            ):
                matched_tokens.append(curr)
                current_context = current_context.advance(1)
            else:
                break

        # Must contain SELECT keyword
        if current_context.at_end():
            return MatchResult(success=False)

        curr = current_context.current()
        if not (
            isinstance(curr, Token)
            and curr.type == TokenType.KEYWORD
            and curr.value.upper() == "SELECT"
        ):
            return MatchResult(success=False)

        # Collect subquery content
        paren_depth = 1
        while not current_context.at_end() and paren_depth > 0:
            curr = current_context.current()

            if isinstance(curr, Token):
                if curr.value == "(":
                    paren_depth += 1
                elif curr.value == ")":
                    paren_depth -= 1

            matched_tokens.append(curr)
            current_context = current_context.advance(1)

            if paren_depth == 0:
                break

        # Check for alias
        alias = ""
        while not current_context.at_end():
            curr = current_context.current()

            if isinstance(curr, Token):
                if curr.type in (TokenType.WHITESPACE, TokenType.NEWLINE):
                    matched_tokens.append(curr)
                    current_context = current_context.advance(1)
                elif curr.type == TokenType.KEYWORD and curr.value.upper() == "AS":
                    matched_tokens.append(curr)
                    current_context = current_context.advance(1)
                elif curr.type == TokenType.IDENTIFIER:
                    alias = curr.value
                    matched_tokens.append(curr)
                    current_context = current_context.advance(1)
                    break
                else:
                    break
            else:
                break

        return MatchResult(
            success=True,
            matched_tokens=matched_tokens,
            end_index=current_context.start_index,
            metadata={"has_alias": bool(alias), "alias": alias},
            group_type=GroupType.SUBQUERY,
            group_name=alias if alias else None,
        )


__all__ = [
    "CTEPattern",
    "WindowFunctionPattern",
    "SubqueryPattern",
]
