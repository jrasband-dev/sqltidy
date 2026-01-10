"""
Tiny, reusable pattern matchers for SQL parsing.

These are the building blocks for complex SQL patterns. Each matcher
is focused on a single, simple matching operation.
"""

from typing import List, Optional, Callable, Set, TYPE_CHECKING
from . import Pattern, MatchResult, MatchContext

if TYPE_CHECKING:
    from sqltidy.tokenizer import TokenType, GroupType


class TokenPattern(Pattern):
    """Match a token by predicate function."""

    def __init__(self, predicate: Callable, name: Optional[str] = None):
        """
        Initialize a token pattern.

        Args:
            predicate: Function that takes (token, dialect) and returns bool
            name: Optional name for this pattern
        """
        super().__init__(name=name)
        self.predicate = predicate

    def match(self, context: MatchContext) -> MatchResult:
        """Match a single token using the predicate."""
        if context.at_end():
            return MatchResult(success=False)

        current = context.current()

        # Import here to avoid circular dependency
        from ..tokenizer import Token

        if isinstance(current, Token) and self.predicate(current, context.dialect):
            return MatchResult(
                success=True,
                matched_tokens=[current],
                end_index=context.start_index + 1,
            )

        return MatchResult(success=False)


class KeywordPattern(Pattern):
    """Match a specific SQL keyword (case-insensitive)."""

    def __init__(self, keyword: str, name: Optional[str] = None):
        """
        Initialize a keyword pattern.

        Args:
            keyword: The keyword to match (case-insensitive)
            name: Optional name for this pattern
        """
        super().__init__(name=name or f"Keyword({keyword})")
        self.keyword = keyword.upper()

    def match(self, context: MatchContext) -> MatchResult:
        """Match the specific keyword."""
        if context.at_end():
            return MatchResult(success=False)

        current = context.current()

        # Import here to avoid circular dependency
        from ..tokenizer import Token, TokenType

        if (
            isinstance(current, Token)
            and current.type == TokenType.KEYWORD
            and current.value.upper() == self.keyword
        ):
            return MatchResult(
                success=True,
                matched_tokens=[current],
                end_index=context.start_index + 1,
            )

        return MatchResult(success=False)


class KeywordSetPattern(Pattern):
    """Match any keyword from a set."""

    def __init__(self, keywords: Set[str], name: Optional[str] = None):
        """
        Initialize a keyword set pattern.

        Args:
            keywords: Set of keywords to match (case-insensitive)
            name: Optional name for this pattern
        """
        super().__init__(name=name or f"KeywordSet({len(keywords)})")
        self.keywords = {kw.upper() for kw in keywords}

    def match(self, context: MatchContext) -> MatchResult:
        """Match any keyword from the set."""
        if context.at_end():
            return MatchResult(success=False)

        current = context.current()

        # Import here to avoid circular dependency
        from ..tokenizer import Token, TokenType

        if (
            isinstance(current, Token)
            and current.type == TokenType.KEYWORD
            and current.value.upper() in self.keywords
        ):
            return MatchResult(
                success=True,
                matched_tokens=[current],
                end_index=context.start_index + 1,
                metadata={"matched_keyword": current.value.upper()},
            )

        return MatchResult(success=False)


class IdentifierPattern(Pattern):
    """Match an identifier token."""

    def match(self, context: MatchContext) -> MatchResult:
        """Match an identifier."""
        if context.at_end():
            return MatchResult(success=False)

        current = context.current()

        # Import here to avoid circular dependency
        from ..tokenizer import Token, TokenType

        if isinstance(current, Token) and current.type == TokenType.IDENTIFIER:
            return MatchResult(
                success=True,
                matched_tokens=[current],
                end_index=context.start_index + 1,
                metadata={"identifier": current.value},
            )

        return MatchResult(success=False)


class TokenTypePattern(Pattern):
    """Match a token of a specific type."""

    def __init__(self, token_type: "TokenType", name: Optional[str] = None):
        """
        Initialize a token type pattern.

        Args:
            token_type: The token type to match
            name: Optional name for this pattern
        """
        super().__init__(name=name or f"TokenType({token_type.value})")
        self.token_type = token_type

    def match(self, context: MatchContext) -> MatchResult:
        """Match a token of the specified type."""
        if context.at_end():
            return MatchResult(success=False)

        current = context.current()

        # Import here to avoid circular dependency
        from ..tokenizer import Token

        if isinstance(current, Token) and current.type == self.token_type:
            return MatchResult(
                success=True,
                matched_tokens=[current],
                end_index=context.start_index + 1,
            )

        return MatchResult(success=False)


class GroupTypePattern(Pattern):
    """Match a token group of a specific type."""

    def __init__(self, group_type: "GroupType", name: Optional[str] = None):
        """
        Initialize a group type pattern.

        Args:
            group_type: The group type to match
            name: Optional name for this pattern
        """
        super().__init__(name=name or f"GroupType({group_type.value})")
        self.group_type = group_type

    def match(self, context: MatchContext) -> MatchResult:
        """Match a group of the specified type."""
        if context.at_end():
            return MatchResult(success=False)

        current = context.current()

        # Import here to avoid circular dependency
        from ..tokenizer import TokenGroup

        if isinstance(current, TokenGroup) and current.group_type == self.group_type:
            return MatchResult(
                success=True,
                matched_tokens=[current],
                end_index=context.start_index + 1,
            )

        return MatchResult(success=False)


class SequencePattern(Pattern):
    """Match a sequence of patterns in order."""

    def __init__(self, patterns: List[Pattern], name: Optional[str] = None):
        """
        Initialize a sequence pattern.

        Args:
            patterns: List of patterns to match in sequence
            name: Optional name for this pattern
        """
        super().__init__(name=name or "Sequence")
        self.patterns = patterns

    def match(self, context: MatchContext) -> MatchResult:
        """Match all patterns in sequence."""
        matched_tokens = []
        current_context = context
        all_metadata = {}

        for i, pattern in enumerate(self.patterns):
            result = pattern.match(current_context)
            if not result.success:
                return MatchResult(success=False)

            matched_tokens.extend(result.matched_tokens)
            all_metadata[f"pattern_{i}"] = result.metadata
            current_context = current_context.advance(len(result.matched_tokens))

        return MatchResult(
            success=True,
            matched_tokens=matched_tokens,
            end_index=current_context.start_index,
            metadata=all_metadata,
        )


class OptionalPattern(Pattern):
    """Match a pattern optionally (always succeeds)."""

    def __init__(self, pattern: Pattern, name: Optional[str] = None):
        """
        Initialize an optional pattern.

        Args:
            pattern: Pattern to match optionally
            name: Optional name for this pattern
        """
        super().__init__(name=name or f"Optional({pattern.name})")
        self.pattern = pattern

    def match(self, context: MatchContext) -> MatchResult:
        """Try to match the pattern, succeed either way."""
        result = self.pattern.match(context)

        if result.success:
            return result

        # Still success, just no tokens matched
        return MatchResult(
            success=True,
            matched_tokens=[],
            end_index=context.start_index,
            metadata={"matched": False},
        )


class OneOrMorePattern(Pattern):
    """Match a pattern one or more times."""

    def __init__(
        self,
        pattern: Pattern,
        name: Optional[str] = None,
        max_matches: Optional[int] = None,
    ):
        """
        Initialize a one-or-more pattern.

        Args:
            pattern: Pattern to match one or more times
            name: Optional name for this pattern
            max_matches: Maximum number of matches (None = unlimited)
        """
        super().__init__(name=name or f"OneOrMore({pattern.name})")
        self.pattern = pattern
        self.max_matches = max_matches

    def match(self, context: MatchContext) -> MatchResult:
        """Match the pattern at least once."""
        matched_tokens = []
        current_context = context
        match_count = 0

        while not current_context.at_end():
            if self.max_matches and match_count >= self.max_matches:
                break

            result = self.pattern.match(current_context)
            if not result.success:
                break

            matched_tokens.extend(result.matched_tokens)
            current_context = current_context.advance(len(result.matched_tokens))
            match_count += 1

        if match_count == 0:
            return MatchResult(success=False)

        return MatchResult(
            success=True,
            matched_tokens=matched_tokens,
            end_index=current_context.start_index,
            metadata={"match_count": match_count},
        )


class ZeroOrMorePattern(Pattern):
    """Match a pattern zero or more times."""

    def __init__(
        self,
        pattern: Pattern,
        name: Optional[str] = None,
        max_matches: Optional[int] = None,
    ):
        """
        Initialize a zero-or-more pattern.

        Args:
            pattern: Pattern to match zero or more times
            name: Optional name for this pattern
            max_matches: Maximum number of matches (None = unlimited)
        """
        super().__init__(name=name or f"ZeroOrMore({pattern.name})")
        self.pattern = pattern
        self.max_matches = max_matches

    def match(self, context: MatchContext) -> MatchResult:
        """Match the pattern zero or more times."""
        matched_tokens = []
        current_context = context
        match_count = 0

        while not current_context.at_end():
            if self.max_matches and match_count >= self.max_matches:
                break

            result = self.pattern.match(current_context)
            if not result.success:
                break

            matched_tokens.extend(result.matched_tokens)
            current_context = current_context.advance(len(result.matched_tokens))
            match_count += 1

        return MatchResult(
            success=True,
            matched_tokens=matched_tokens,
            end_index=current_context.start_index,
            metadata={"match_count": match_count},
        )


class AlternativePattern(Pattern):
    """Match one of several alternative patterns."""

    def __init__(self, patterns: List[Pattern], name: Optional[str] = None):
        """
        Initialize an alternative pattern.

        Args:
            patterns: List of patterns to try (first match wins)
            name: Optional name for this pattern
        """
        super().__init__(name=name or "Alternative")
        self.patterns = patterns

    def match(self, context: MatchContext) -> MatchResult:
        """Try each pattern until one succeeds."""
        for i, pattern in enumerate(self.patterns):
            result = pattern.match(context)
            if result.success:
                result.metadata["alternative_index"] = i
                result.metadata["alternative_pattern"] = pattern.name
                return result

        return MatchResult(success=False)


class UntilPattern(Pattern):
    """Match tokens until a stop pattern is found."""

    def __init__(
        self,
        stop_pattern: Pattern,
        include_stop: bool = False,
        name: Optional[str] = None,
    ):
        """
        Initialize an until pattern.

        Args:
            stop_pattern: Pattern that stops the match
            include_stop: Whether to include the stop token in the match
            name: Optional name for this pattern
        """
        super().__init__(name=name or f"Until({stop_pattern.name})")
        self.stop_pattern = stop_pattern
        self.include_stop = include_stop

    def match(self, context: MatchContext) -> MatchResult:
        """Match tokens until stop pattern is found."""
        matched_tokens = []
        current_context = context

        while not current_context.at_end():
            result = self.stop_pattern.match(current_context)
            if result.success:
                if self.include_stop:
                    matched_tokens.extend(result.matched_tokens)
                    current_context = current_context.advance(
                        len(result.matched_tokens)
                    )
                break

            # Add current token and advance
            current = current_context.current()
            if current:
                matched_tokens.append(current)
                current_context = current_context.advance(1)

        return MatchResult(
            success=True,
            matched_tokens=matched_tokens,
            end_index=current_context.start_index,
        )


class BetweenPattern(Pattern):
    """Match tokens between start and end patterns."""

    def __init__(
        self,
        start_pattern: Pattern,
        end_pattern: Pattern,
        include_delimiters: bool = True,
        name: Optional[str] = None,
    ):
        """
        Initialize a between pattern.

        Args:
            start_pattern: Pattern that starts the match
            end_pattern: Pattern that ends the match
            include_delimiters: Whether to include start/end in the match
            name: Optional name for this pattern
        """
        super().__init__(
            name=name or f"Between({start_pattern.name},{end_pattern.name})"
        )
        self.start_pattern = start_pattern
        self.end_pattern = end_pattern
        self.include_delimiters = include_delimiters

    def match(self, context: MatchContext) -> MatchResult:
        """Match tokens between start and end patterns."""
        # First match the start pattern
        start_result = self.start_pattern.match(context)
        if not start_result.success:
            return MatchResult(success=False)

        matched_tokens = []
        if self.include_delimiters:
            matched_tokens.extend(start_result.matched_tokens)

        # Now match tokens until end pattern
        current_context = context.advance(len(start_result.matched_tokens))
        depth = 1  # Track nesting depth for nested constructs

        while not current_context.at_end() and depth > 0:
            # Check for end pattern
            end_result = self.end_pattern.match(current_context)
            if end_result.success:
                depth -= 1
                if depth == 0:
                    if self.include_delimiters:
                        matched_tokens.extend(end_result.matched_tokens)
                    current_context = current_context.advance(
                        len(end_result.matched_tokens)
                    )
                    break

            # Check for nested start pattern
            nested_start = self.start_pattern.match(current_context)
            if nested_start.success:
                depth += 1

            # Add current token
            current = current_context.current()
            if current:
                matched_tokens.append(current)
                current_context = current_context.advance(1)

        if depth != 0:
            # Unbalanced delimiters
            return MatchResult(success=False)

        return MatchResult(
            success=True,
            matched_tokens=matched_tokens,
            end_index=current_context.start_index,
        )


class WhitespacePattern(Pattern):
    """Match whitespace or newline tokens."""

    def __init__(self, optional: bool = True, name: Optional[str] = None):
        """
        Initialize a whitespace pattern.

        Args:
            optional: Whether whitespace is optional
            name: Optional name for this pattern
        """
        super().__init__(name=name or "Whitespace")
        self.optional = optional

    def match(self, context: MatchContext) -> MatchResult:
        """Match whitespace tokens."""
        from ..tokenizer import Token, TokenType

        if context.at_end():
            return MatchResult(success=self.optional)

        current = context.current()

        if isinstance(current, Token) and current.type in (
            TokenType.WHITESPACE,
            TokenType.NEWLINE,
        ):
            return MatchResult(
                success=True,
                matched_tokens=[current],
                end_index=context.start_index + 1,
            )

        return MatchResult(success=self.optional)


__all__ = [
    "TokenPattern",
    "KeywordPattern",
    "KeywordSetPattern",
    "IdentifierPattern",
    "TokenTypePattern",
    "GroupTypePattern",
    "SequencePattern",
    "OptionalPattern",
    "OneOrMorePattern",
    "ZeroOrMorePattern",
    "AlternativePattern",
    "UntilPattern",
    "BetweenPattern",
    "WhitespacePattern",
]
