"""
PostgreSQL specific patterns.

These patterns handle PostgreSQL-specific syntax and constructs.
"""

from typing import Optional
from . import Pattern, MatchResult, MatchContext


class ArrayConstructorPattern(Pattern):
    """
    Match PostgreSQL ARRAY constructor.

    Syntax:
        ARRAY[1, 2, 3]
        ARRAY(SELECT ...)
    """

    def __init__(self, name: Optional[str] = None):
        super().__init__(
            name=name or "ArrayConstructor", supported_dialects=["postgresql"]
        )

    def match(self, context: MatchContext) -> MatchResult:
        """Match an ARRAY constructor."""
        from ..tokenizer import Token, TokenType

        if context.at_end():
            return MatchResult(success=False)

        current = context.current()
        if not (
            isinstance(current, Token)
            and current.type == TokenType.KEYWORD
            and current.value.upper() == "ARRAY"
        ):
            return MatchResult(success=False)

        matched_tokens = [current]
        current_context = context.advance(1)

        # Must be followed by [ or (
        if current_context.at_end():
            return MatchResult(success=False)

        curr = current_context.current()
        if not (isinstance(curr, Token) and curr.value in ("[", "(")):
            return MatchResult(success=False)

        bracket_type = curr.value
        closing_bracket = "]" if bracket_type == "[" else ")"

        matched_tokens.append(curr)
        current_context = current_context.advance(1)

        # Collect content until closing bracket
        depth = 1
        while not current_context.at_end() and depth > 0:
            curr = current_context.current()

            if isinstance(curr, Token):
                if curr.value in ("[", "("):
                    depth += 1
                elif curr.value in ("]", ")"):
                    if curr.value == closing_bracket:
                        depth -= 1

            matched_tokens.append(curr)
            current_context = current_context.advance(1)

            if depth == 0:
                break

        return MatchResult(
            success=True,
            matched_tokens=matched_tokens,
            end_index=current_context.start_index,
            metadata={"bracket_type": bracket_type},
        )


class ReturningClausePattern(Pattern):
    """
    Match RETURNING clause (PostgreSQL, also Oracle).

    Used in INSERT, UPDATE, DELETE statements.

    Syntax:
        RETURNING column1, column2, ...
    """

    def __init__(self, name: Optional[str] = None):
        super().__init__(
            name=name or "ReturningClause", supported_dialects=["postgresql", "oracle"]
        )

    def match(self, context: MatchContext) -> MatchResult:
        """Match a RETURNING clause."""
        from ..tokenizer import Token, TokenType

        if context.at_end():
            return MatchResult(success=False)

        current = context.current()
        if not (
            isinstance(current, Token)
            and current.type == TokenType.KEYWORD
            and current.value.upper() == "RETURNING"
        ):
            return MatchResult(success=False)

        matched_tokens = [current]
        current_context = context.advance(1)

        clause_end_keywords = {
            "INTO",
            "FROM",
            "WHERE",
            "GROUP",
            "HAVING",
            "ORDER",
            "LIMIT",
            "OFFSET",
            "FETCH",
            "INSERT",
            "UPDATE",
            "DELETE",
        }

        # Collect RETURNING clause content
        while not current_context.at_end():
            curr = current_context.current()

            if isinstance(curr, Token) and curr.type == TokenType.KEYWORD:
                keyword = curr.value.upper()
                if keyword in clause_end_keywords:
                    break

            matched_tokens.append(curr)
            current_context = current_context.advance(1)

        return MatchResult(
            success=True,
            matched_tokens=matched_tokens,
            end_index=current_context.start_index,
        )


class JsonOperatorPattern(Pattern):
    """
    Match PostgreSQL JSON operators.

    Operators: ->, ->>, #>, #>>, @>, <@, ?, ?|, ?&, ||

    Syntax:
        column -> 'key'
        column ->> 'key'
        column #> ARRAY['key1', 'key2']
    """

    def __init__(self, name: Optional[str] = None):
        super().__init__(name=name or "JsonOperator", supported_dialects=["postgresql"])

        self.json_operators = {
            "->",
            "->>",
            "#>",
            "#>>",
            "@>",
            "<@",
            "?",
            "?|",
            "?&",
            "||",
        }

    def match(self, context: MatchContext) -> MatchResult:
        """Match a JSON operator."""
        from ..tokenizer import Token

        if context.at_end():
            return MatchResult(success=False)

        current = context.current()

        # Check for multi-character operators
        if isinstance(current, Token):
            # Check for exact match
            if current.value in self.json_operators:
                return MatchResult(
                    success=True,
                    matched_tokens=[current],
                    end_index=context.start_index + 1,
                    metadata={"operator": current.value},
                )

            # Check for two-character operators that might be tokenized separately
            if current.value in ("-", "#", "?", "|", "<", "@"):
                next_token = context.peek(1)
                if isinstance(next_token, Token):
                    combined = current.value + next_token.value
                    if combined in self.json_operators:
                        return MatchResult(
                            success=True,
                            matched_tokens=[current, next_token],
                            end_index=context.start_index + 2,
                            metadata={"operator": combined},
                        )

        return MatchResult(success=False)


class OnConflictPattern(Pattern):
    """
    Match ON CONFLICT clause (PostgreSQL upsert).

    Syntax:
        ON CONFLICT (column) DO NOTHING
        ON CONFLICT (column) DO UPDATE SET ...
    """

    def __init__(self, name: Optional[str] = None):
        super().__init__(name=name or "OnConflict", supported_dialects=["postgresql"])

    def match(self, context: MatchContext) -> MatchResult:
        """Match an ON CONFLICT clause."""
        from ..tokenizer import Token, TokenType

        if context.at_end():
            return MatchResult(success=False)

        current = context.current()
        if not (
            isinstance(current, Token)
            and current.type == TokenType.KEYWORD
            and current.value.upper() == "ON"
        ):
            return MatchResult(success=False)

        matched_tokens = [current]
        current_context = context.advance(1)

        # Skip whitespace and check for CONFLICT
        while not current_context.at_end():
            curr = current_context.current()
            if isinstance(curr, Token):
                if curr.type in (TokenType.WHITESPACE, TokenType.NEWLINE):
                    matched_tokens.append(curr)
                    current_context = current_context.advance(1)
                elif (
                    curr.type == TokenType.KEYWORD and curr.value.upper() == "CONFLICT"
                ):
                    matched_tokens.append(curr)
                    current_context = current_context.advance(1)
                    break
                else:
                    return MatchResult(success=False)
            else:
                matched_tokens.append(curr)
                current_context = current_context.advance(1)

        # Collect conflict target (optional constraint name or columns)
        paren_depth = 0
        found_do = False

        while not current_context.at_end():
            curr = current_context.current()

            if isinstance(curr, Token):
                if curr.value == "(":
                    paren_depth += 1
                elif curr.value == ")":
                    paren_depth -= 1
                elif (
                    curr.type == TokenType.KEYWORD
                    and curr.value.upper() == "DO"
                    and paren_depth == 0
                ):
                    found_do = True
                    matched_tokens.append(curr)
                    current_context = current_context.advance(1)
                    break

            matched_tokens.append(curr)
            current_context = current_context.advance(1)

        if not found_do:
            return MatchResult(success=False)

        # Collect DO action (NOTHING or UPDATE SET ...)
        action_type = ""

        while not current_context.at_end():
            curr = current_context.current()

            if isinstance(curr, Token):
                if curr.type in (TokenType.WHITESPACE, TokenType.NEWLINE):
                    matched_tokens.append(curr)
                    current_context = current_context.advance(1)
                elif curr.type == TokenType.KEYWORD:
                    keyword = curr.value.upper()
                    if keyword == "NOTHING":
                        action_type = "NOTHING"
                        matched_tokens.append(curr)
                        current_context = current_context.advance(1)
                        break
                    elif keyword == "UPDATE":
                        action_type = "UPDATE"
                        matched_tokens.append(curr)
                        current_context = current_context.advance(1)

                        # Collect UPDATE SET clause
                        clause_end_keywords = {
                            "WHERE",
                            "RETURNING",
                            "INSERT",
                            "UPDATE",
                            "DELETE",
                            "SELECT",
                        }

                        while not current_context.at_end():
                            curr = current_context.current()

                            if (
                                isinstance(curr, Token)
                                and curr.type == TokenType.KEYWORD
                            ):
                                kw = curr.value.upper()
                                if kw in clause_end_keywords:
                                    break

                            matched_tokens.append(curr)
                            current_context = current_context.advance(1)
                        break
                else:
                    break
            else:
                matched_tokens.append(curr)
                current_context = current_context.advance(1)

        return MatchResult(
            success=True,
            matched_tokens=matched_tokens,
            end_index=current_context.start_index,
            metadata={"action": action_type},
        )


__all__ = [
    "ArrayConstructorPattern",
    "ReturningClausePattern",
    "JsonOperatorPattern",
    "OnConflictPattern",
]
