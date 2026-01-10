"""
T-SQL (SQL Server) specific patterns.

These patterns handle SQL Server-specific syntax and constructs.
"""

from typing import Optional
from . import Pattern, MatchResult, MatchContext


class JoinClausePattern(Pattern):
    """
    Match JOIN clauses.
    """

    def __init__(self, name: Optional[str] = None):
        super().__init__(name=name or "JoinClause", supported_dialects=["sqlserver"])

        # Clause-ending keywords
        self.clause_end_keywords = {
            "WHERE",
            "GROUP",
            "HAVING",
            "ORDER",
            "UNION",
            "EXCEPT",
            "INTERSECT",
            "LIMIT",
            "OFFSET",
            "FETCH",
        }

    def match(self, context: MatchContext) -> MatchResult:
        """Match a JOIN clause."""
        from ..tokenizer import Token, TokenType, GroupType

        if context.at_end():
            return MatchResult(success=False)

        current = context.current()

        # Get join keywords from dialect
        join_type_keywords = {kw.upper() for kw in context.dialect.join_keywords}

        # Check if this starts a JOIN
        if not (
            isinstance(current, Token)
            and current.type == TokenType.KEYWORD
            and current.value.upper() in join_type_keywords
        ):
            return MatchResult(success=False)

        matched_tokens = []
        join_type_parts = []
        table_name = ""
        alias = ""
        has_on = False
        current_context = context

        # Collect JOIN type keywords (e.g., LEFT OUTER JOIN)
        while not current_context.at_end():
            curr = current_context.current()

            if isinstance(curr, Token) and curr.type == TokenType.KEYWORD:
                keyword = curr.value.upper()
                if keyword in join_type_keywords:
                    join_type_parts.append(keyword)
                    matched_tokens.append(curr)
                    current_context = current_context.advance(1)

                    if keyword == "JOIN":
                        break
                else:
                    break
            elif isinstance(curr, Token) and curr.type in (
                TokenType.WHITESPACE,
                TokenType.NEWLINE,
            ):
                matched_tokens.append(curr)
                current_context = current_context.advance(1)
            else:
                break

        if "JOIN" not in join_type_parts:
            # Not a valid JOIN clause
            return MatchResult(success=False)

        # Collect table name, alias, and ON condition
        paren_depth = 0
        while not current_context.at_end():
            curr = current_context.current()

            # Track parentheses for subqueries
            if isinstance(curr, Token) and curr.value == "(":
                paren_depth += 1
            elif isinstance(curr, Token) and curr.value == ")":
                paren_depth -= 1

            # Check for clause-ending keywords at depth 0
            if (
                isinstance(curr, Token)
                and curr.type == TokenType.KEYWORD
                and paren_depth == 0
            ):
                keyword = curr.value.upper()

                if keyword == "ON":
                    has_on = True
                    matched_tokens.append(curr)
                    current_context = current_context.advance(1)

                    # Continue until next major clause
                    while not current_context.at_end():
                        curr = current_context.current()

                        if isinstance(curr, Token) and curr.value == "(":
                            paren_depth += 1
                        elif isinstance(curr, Token) and curr.value == ")":
                            paren_depth -= 1

                        if (
                            isinstance(curr, Token)
                            and curr.type == TokenType.KEYWORD
                            and paren_depth == 0
                        ):
                            kw = curr.value.upper()
                            if (
                                kw in self.clause_end_keywords
                                or kw in join_type_keywords
                            ):
                                break

                        matched_tokens.append(curr)
                        current_context = current_context.advance(1)
                    break

                elif (
                    keyword in self.clause_end_keywords or keyword in join_type_keywords
                ):
                    break

            # Collect table name and alias
            if isinstance(curr, Token) and curr.type == TokenType.IDENTIFIER:
                if not table_name:
                    table_name = curr.value
                else:
                    alias = curr.value

            matched_tokens.append(curr)
            current_context = current_context.advance(1)

        join_type = " ".join(join_type_parts)

        return MatchResult(
            success=True,
            matched_tokens=matched_tokens,
            end_index=current_context.start_index,
            metadata={
                "join_type": join_type,
                "table": table_name,
                "alias": alias,
                "has_on": has_on,
            },
            group_type=GroupType.JOIN_CLAUSE,
            group_name=join_type,
        )


class CaseExpressionPattern(Pattern):
    """
    Match CASE...WHEN...THEN...ELSE...END expressions.
    """

    def __init__(self, name: Optional[str] = None):
        super().__init__(
            name=name or "CaseExpression", supported_dialects=["sqlserver"]
        )

    def match(self, context: MatchContext) -> MatchResult:
        """Match a CASE expression."""
        from ..tokenizer import Token, TokenType, GroupType

        # Must start with CASE keyword
        if context.at_end():
            return MatchResult(success=False)

        current = context.current()
        if not (
            isinstance(current, Token)
            and current.type == TokenType.KEYWORD
            and current.value.upper() == "CASE"
        ):
            return MatchResult(success=False)

        matched_tokens = [current]
        current_context = context.advance(1)

        # Track metadata
        has_else = False
        when_count = 0
        depth = 1  # Track nested CASE expressions

        # Match tokens until END
        while not current_context.at_end() and depth > 0:
            curr = current_context.current()

            if isinstance(curr, Token) and curr.type == TokenType.KEYWORD:
                keyword = curr.value.upper()

                if keyword == "CASE":
                    depth += 1
                elif keyword == "END":
                    depth -= 1
                    matched_tokens.append(curr)
                    current_context = current_context.advance(1)
                    if depth == 0:
                        break
                elif keyword == "WHEN" and depth == 1:
                    when_count += 1
                elif keyword == "ELSE" and depth == 1:
                    has_else = True

            matched_tokens.append(curr)
            current_context = current_context.advance(1)

        if depth != 0:
            # Unmatched CASE/END
            return MatchResult(success=False)

        return MatchResult(
            success=True,
            matched_tokens=matched_tokens,
            end_index=current_context.start_index,
            metadata={"has_else": has_else, "when_count": when_count},
            group_type=GroupType.CASE_EXPRESSION,
        )


class TrycatchPattern(Pattern):
    """
    Match TRY...CATCH blocks (T-SQL specific).

    Syntax:
        BEGIN TRY
            -- statements
        END TRY
        BEGIN CATCH
            -- error handling
        END CATCH
    """

    def __init__(self, name: Optional[str] = None):
        super().__init__(name=name or "TryCatch", supported_dialects=["sqlserver"])

    def match(self, context: MatchContext) -> MatchResult:
        """Match a TRY...CATCH block."""
        from ..tokenizer import Token, TokenType

        # Must start with BEGIN TRY
        if context.at_end():
            return MatchResult(success=False)

        current = context.current()
        if not (
            isinstance(current, Token)
            and current.type == TokenType.KEYWORD
            and current.value.upper() == "BEGIN"
        ):
            return MatchResult(success=False)

        matched_tokens = [current]
        current_context = context.advance(1)

        # Skip whitespace and check for TRY
        while not current_context.at_end():
            curr = current_context.current()
            if isinstance(curr, Token):
                if curr.type in (TokenType.WHITESPACE, TokenType.NEWLINE):
                    matched_tokens.append(curr)
                    current_context = current_context.advance(1)
                elif curr.type == TokenType.KEYWORD and curr.value.upper() == "TRY":
                    matched_tokens.append(curr)
                    current_context = current_context.advance(1)
                    break
                else:
                    return MatchResult(success=False)
            else:
                matched_tokens.append(curr)
                current_context = current_context.advance(1)

        # Collect TRY block content until END TRY
        depth = 1
        while not current_context.at_end() and depth > 0:
            curr = current_context.current()

            if isinstance(curr, Token) and curr.type == TokenType.KEYWORD:
                keyword = curr.value.upper()
                if keyword == "BEGIN":
                    depth += 1
                elif keyword == "END":
                    matched_tokens.append(curr)
                    current_context = current_context.advance(1)

                    # Check for TRY keyword after END
                    while not current_context.at_end():
                        curr = current_context.current()
                        if isinstance(curr, Token):
                            if curr.type in (TokenType.WHITESPACE, TokenType.NEWLINE):
                                matched_tokens.append(curr)
                                current_context = current_context.advance(1)
                            elif (
                                curr.type == TokenType.KEYWORD
                                and curr.value.upper() == "TRY"
                            ):
                                depth -= 1
                                matched_tokens.append(curr)
                                current_context = current_context.advance(1)
                                break
                            else:
                                break
                        else:
                            break

                    if depth == 0:
                        break
                    continue

            matched_tokens.append(curr)
            current_context = current_context.advance(1)

        # Must be followed by BEGIN CATCH
        while not current_context.at_end():
            curr = current_context.current()
            if isinstance(curr, Token):
                if curr.type in (TokenType.WHITESPACE, TokenType.NEWLINE):
                    matched_tokens.append(curr)
                    current_context = current_context.advance(1)
                elif curr.type == TokenType.KEYWORD and curr.value.upper() == "BEGIN":
                    matched_tokens.append(curr)
                    current_context = current_context.advance(1)
                    break
                else:
                    return MatchResult(success=False)
            else:
                matched_tokens.append(curr)
                current_context = current_context.advance(1)

        # Check for CATCH
        while not current_context.at_end():
            curr = current_context.current()
            if isinstance(curr, Token):
                if curr.type in (TokenType.WHITESPACE, TokenType.NEWLINE):
                    matched_tokens.append(curr)
                    current_context = current_context.advance(1)
                elif curr.type == TokenType.KEYWORD and curr.value.upper() == "CATCH":
                    matched_tokens.append(curr)
                    current_context = current_context.advance(1)
                    break
                else:
                    return MatchResult(success=False)
            else:
                matched_tokens.append(curr)
                current_context = current_context.advance(1)

        # Collect CATCH block content until END CATCH
        depth = 1
        while not current_context.at_end() and depth > 0:
            curr = current_context.current()

            if isinstance(curr, Token) and curr.type == TokenType.KEYWORD:
                keyword = curr.value.upper()
                if keyword == "BEGIN":
                    depth += 1
                elif keyword == "END":
                    matched_tokens.append(curr)
                    current_context = current_context.advance(1)

                    # Check for CATCH keyword after END
                    while not current_context.at_end():
                        curr = current_context.current()
                        if isinstance(curr, Token):
                            if curr.type in (TokenType.WHITESPACE, TokenType.NEWLINE):
                                matched_tokens.append(curr)
                                current_context = current_context.advance(1)
                            elif (
                                curr.type == TokenType.KEYWORD
                                and curr.value.upper() == "CATCH"
                            ):
                                depth -= 1
                                matched_tokens.append(curr)
                                current_context = current_context.advance(1)
                                break
                            else:
                                break
                        else:
                            break

                    if depth == 0:
                        break
                    continue

            matched_tokens.append(curr)
            current_context = current_context.advance(1)

        return MatchResult(
            success=True,
            matched_tokens=matched_tokens,
            end_index=current_context.start_index,
            metadata={"type": "TRY_CATCH"},
        )


class PivotUnpivotPattern(Pattern):
    """
    Match PIVOT/UNPIVOT operations (T-SQL specific).

    Syntax:
        PIVOT ( aggregate_function(column) FOR pivot_column IN (values) )
        UNPIVOT ( value_column FOR pivot_column IN (columns) )
    """

    def __init__(self, name: Optional[str] = None):
        super().__init__(name=name or "PivotUnpivot", supported_dialects=["sqlserver"])

    def match(self, context: MatchContext) -> MatchResult:
        """Match a PIVOT or UNPIVOT operation."""
        from ..tokenizer import Token, TokenType

        if context.at_end():
            return MatchResult(success=False)

        current = context.current()
        if not (
            isinstance(current, Token)
            and current.type == TokenType.KEYWORD
            and current.value.upper() in ("PIVOT", "UNPIVOT")
        ):
            return MatchResult(success=False)

        operation_type = current.value.upper()
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

        # Must have opening parenthesis
        if current_context.at_end():
            return MatchResult(success=False)

        curr = current_context.current()
        if not (isinstance(curr, Token) and curr.value == "("):
            return MatchResult(success=False)

        matched_tokens.append(curr)
        current_context = current_context.advance(1)

        # Collect content until matching closing paren
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

        return MatchResult(
            success=True,
            matched_tokens=matched_tokens,
            end_index=current_context.start_index,
            metadata={"operation": operation_type},
        )


class OutputClausePattern(Pattern):
    """
    Match OUTPUT clause (T-SQL specific).

    Used in INSERT, UPDATE, DELETE, MERGE statements.

    Syntax:
        OUTPUT inserted.*, deleted.* [INTO @table_variable]
    """

    def __init__(self, name: Optional[str] = None):
        super().__init__(name=name or "OutputClause", supported_dialects=["sqlserver"])

    def match(self, context: MatchContext) -> MatchResult:
        """Match an OUTPUT clause."""
        from ..tokenizer import Token, TokenType

        if context.at_end():
            return MatchResult(success=False)

        current = context.current()
        if not (
            isinstance(current, Token)
            and current.type == TokenType.KEYWORD
            and current.value.upper() == "OUTPUT"
        ):
            return MatchResult(success=False)

        matched_tokens = [current]
        current_context = context.advance(1)

        has_into = False
        clause_end_keywords = {
            "FROM",
            "WHERE",
            "GROUP",
            "HAVING",
            "ORDER",
            "INSERT",
            "UPDATE",
            "DELETE",
            "MERGE",
            "SELECT",
        }

        # Collect OUTPUT clause content
        while not current_context.at_end():
            curr = current_context.current()

            if isinstance(curr, Token) and curr.type == TokenType.KEYWORD:
                keyword = curr.value.upper()

                if keyword == "INTO":
                    has_into = True
                    matched_tokens.append(curr)
                    current_context = current_context.advance(1)
                    continue
                elif keyword in clause_end_keywords:
                    break

            matched_tokens.append(curr)
            current_context = current_context.advance(1)

        return MatchResult(
            success=True,
            matched_tokens=matched_tokens,
            end_index=current_context.start_index,
            metadata={"has_into": has_into},
        )


__all__ = [
    "TrycatchPattern",
    "PivotUnpivotPattern",
    "OutputClausePattern",
]
