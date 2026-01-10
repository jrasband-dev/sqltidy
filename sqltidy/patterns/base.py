"""
Base classes and infrastructure for the declarative SQL pattern system.

This module provides the core pattern matching framework that other patterns build upon.
"""

from typing import List, Optional, Union, Dict, Any
from dataclasses import dataclass, field
from abc import ABC, abstractmethod

# Import types from tokenizer
# Note: We avoid circular imports by using TYPE_CHECKING
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..tokenizer import Token, TokenGroup, GroupType
    from ..dialects.base import SQLDialect


class MatchResult:
    """Result of a pattern match operation."""

    def __init__(
        self,
        success: bool,
        matched_tokens: Optional[List[Union["Token", "TokenGroup"]]] = None,
        end_index: int = 0,
        metadata: Optional[Dict[str, Any]] = None,
        group_type: Optional["GroupType"] = None,
        group_name: Optional[str] = None,
    ):
        """
        Initialize a match result.

        Args:
            success: Whether the match succeeded
            matched_tokens: List of tokens that were matched
            end_index: Index after the last matched token
            metadata: Additional metadata about the match
            group_type: Optional GroupType for creating a TokenGroup
            group_name: Optional name for the TokenGroup
        """
        self.success = success
        self.matched_tokens = matched_tokens or []
        self.end_index = end_index
        self.metadata = metadata or {}
        self.group_type = group_type
        self.group_name = group_name

    def __bool__(self):
        """Allow using MatchResult in boolean context."""
        return self.success

    def __repr__(self):
        if self.success:
            return f"<MatchResult success=True tokens={len(self.matched_tokens)} end={self.end_index}>"
        return "<MatchResult success=False>"


@dataclass
class MatchContext:
    """Context for pattern matching operations."""

    dialect: "SQLDialect"
    """The SQL dialect being parsed."""

    tokens: List[Union["Token", "TokenGroup"]]
    """The full list of tokens being processed."""

    start_index: int = 0
    """Current position in the token list."""

    parent_group_type: Optional["GroupType"] = None
    """Type of the parent group (to avoid duplicate nesting)."""

    config: Dict[str, Any] = field(default_factory=dict)
    """Additional configuration options."""

    def advance(self, count: int = 1) -> "MatchContext":
        """Create a new context advanced by count positions."""
        return MatchContext(
            dialect=self.dialect,
            tokens=self.tokens,
            start_index=self.start_index + count,
            parent_group_type=self.parent_group_type,
            config=self.config,
        )

    def current(self) -> Optional[Union["Token", "TokenGroup"]]:
        """Get the current token."""
        if self.start_index < len(self.tokens):
            return self.tokens[self.start_index]
        return None

    def peek(self, offset: int = 1) -> Optional[Union["Token", "TokenGroup"]]:
        """Peek at a token ahead without advancing."""
        index = self.start_index + offset
        if index < len(self.tokens):
            return self.tokens[index]
        return None

    def at_end(self) -> bool:
        """Check if we're at the end of the token stream."""
        return self.start_index >= len(self.tokens)


class Pattern(ABC):
    """
    Base class for all SQL patterns.

    Patterns are composable, declarative matchers that can identify
    and group SQL constructs. Each pattern:

    - Is tiny and focused on one thing
    - Is reusable across different contexts
    - Can be dialect-aware
    - Returns structured MatchResult objects
    - Can be composed with other patterns
    """

    def __init__(
        self, name: Optional[str] = None, supported_dialects: Optional[List[str]] = None
    ):
        """
        Initialize a pattern.

        Args:
            name: Optional descriptive name for this pattern
            supported_dialects: List of dialect names this pattern supports (None = all)
        """
        self.name = name or self.__class__.__name__
        self.supported_dialects = supported_dialects

    @abstractmethod
    def match(self, context: MatchContext) -> MatchResult:
        """
        Attempt to match this pattern at the current position.

        Args:
            context: The current matching context

        Returns:
            MatchResult indicating success/failure and matched tokens
        """
        pass

    def is_applicable(self, dialect: "SQLDialect") -> bool:
        """
        Check if this pattern applies to the given dialect.

        Args:
            dialect: The SQL dialect to check

        Returns:
            True if pattern applies to this dialect
        """
        if self.supported_dialects is None:
            return True
        return dialect.name.lower() in [d.lower() for d in self.supported_dialects]

    def match_all(
        self, tokens: List[Union["Token", "TokenGroup"]], dialect: "SQLDialect"
    ) -> List[MatchResult]:
        """
        Find all matches of this pattern in a token list.

        Args:
            tokens: List of tokens to search
            dialect: The SQL dialect

        Returns:
            List of all MatchResults found
        """
        matches = []
        i = 0
        while i < len(tokens):
            context = MatchContext(dialect=dialect, tokens=tokens, start_index=i)
            result = self.match(context)
            if result.success:
                matches.append(result)
                i = result.end_index
            else:
                i += 1
        return matches

    def __repr__(self):
        return f"<{self.__class__.__name__} name={self.name}>"


class PatternRegistry:
    """
    Registry for SQL patterns.

    Patterns are registered by name and can be retrieved for use
    in tokenization and parsing. Patterns can be dialect-specific
    or apply to all dialects.
    """

    def __init__(self):
        self._patterns: Dict[str, Pattern] = {}
        self._dialect_patterns: Dict[str, List[Pattern]] = {}

    def register(self, pattern: Pattern, dialect: Optional[str] = None):
        """
        Register a pattern.

        Args:
            pattern: The pattern to register
            dialect: Optional dialect name (None = global pattern)
        """
        self._patterns[pattern.name] = pattern

        if dialect:
            if dialect not in self._dialect_patterns:
                self._dialect_patterns[dialect] = []
            self._dialect_patterns[dialect].append(pattern)

    def get(self, name: str) -> Optional[Pattern]:
        """Get a pattern by name."""
        return self._patterns.get(name)

    def get_all(self, dialect: Optional[str] = None) -> List[Pattern]:
        """
        Get all patterns, optionally filtered by dialect.

        Args:
            dialect: Optional dialect name to filter by

        Returns:
            List of patterns
        """
        if dialect is None:
            return list(self._patterns.values())
        return self._dialect_patterns.get(dialect, [])

    def get_by_type(
        self, pattern_class: type, dialect: Optional[str] = None
    ) -> List[Pattern]:
        """
        Get all patterns of a specific type.

        Args:
            pattern_class: The pattern class to filter by
            dialect: Optional dialect name

        Returns:
            List of matching patterns
        """
        patterns = self.get_all(dialect)
        return [p for p in patterns if isinstance(p, pattern_class)]

    def clear(self):
        """Clear all patterns from the registry."""
        self._patterns.clear()
        self._dialect_patterns.clear()


# Global pattern registry
_global_registry = PatternRegistry()


def register_pattern(pattern: Pattern, dialect: Optional[str] = None):
    """Register a pattern in the global registry."""
    _global_registry.register(pattern, dialect)


def get_pattern(name: str) -> Optional[Pattern]:
    """Get a pattern from the global registry by name."""
    return _global_registry.get(name)


def get_all_patterns(dialect: Optional[str] = None) -> List[Pattern]:
    """Get all patterns from the global registry."""
    return _global_registry.get_all(dialect)


def clear_patterns():
    """Clear the global pattern registry."""
    _global_registry.clear()


__all__ = [
    "Pattern",
    "MatchResult",
    "MatchContext",
    "PatternRegistry",
    "register_pattern",
    "get_pattern",
    "get_all_patterns",
    "clear_patterns",
]
