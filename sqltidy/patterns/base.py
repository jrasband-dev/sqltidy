"""
Base pattern matching classes for SQL token analysis.

This module provides the foundation for building composable pattern matchers
that work with Token and TokenGroup objects from the tokenizer.
"""

from abc import ABC, abstractmethod
from typing import List, Union, Optional, Iterator, Tuple
from dataclasses import dataclass
from ..tokenizer import Token, TokenGroup, TokenType, GroupType


@dataclass
class Match:
    """
    Represents a successful pattern match.
    
    Attributes:
        tokens: The matched tokens/groups
        start_index: Starting position in the token list
        end_index: Ending position (exclusive) in the token list
        metadata: Additional match-specific data (e.g., captured groups)
    """
    tokens: List[Union[Token, TokenGroup]]
    start_index: int
    end_index: int
    metadata: Optional[dict] = None
    
    def get_text(self) -> str:
        """Get the text representation of matched tokens."""
        result = []
        for item in self.tokens:
            if isinstance(item, Token):
                result.append(item.value)
            elif isinstance(item, TokenGroup):
                result.append(item.get_text())
        return ''.join(result)
    
    def flatten(self) -> List[Token]:
        """Flatten matched tokens to a simple list."""
        result = []
        for item in self.tokens:
            if isinstance(item, Token):
                result.append(item)
            elif isinstance(item, TokenGroup):
                result.extend(item.flatten())
        return result


class Pattern(ABC):
    """
    Abstract base class for all pattern matchers.
    
    Patterns can match sequences of tokens and provide methods to find,
    replace, and transform matched sequences.
    """
    
    @abstractmethod
    def match(self, tokens: List[Union[Token, TokenGroup]], start: int = 0) -> Optional[Match]:
        """
        Try to match the pattern starting at the given position.
        
        Args:
            tokens: List of tokens/groups to match against
            start: Starting position in the token list
            
        Returns:
            Match object if successful, None otherwise
        """
        pass
    
    def find(self, tokens: List[Union[Token, TokenGroup]]) -> Optional[Match]:
        """
        Find the first occurrence of this pattern in the token list.
        
        Args:
            tokens: List of tokens/groups to search
            
        Returns:
            First Match object found, or None
        """
        for i in range(len(tokens)):
            match = self.match(tokens, i)
            if match:
                return match
        return None
    
    def find_all(self, tokens: List[Union[Token, TokenGroup]]) -> Iterator[Match]:
        """
        Find all non-overlapping occurrences of this pattern.
        
        Args:
            tokens: List of tokens/groups to search
            
        Yields:
            Match objects for each occurrence
        """
        i = 0
        while i < len(tokens):
            match = self.match(tokens, i)
            if match:
                yield match
                i = match.end_index
            else:
                i += 1
    
    def replace(self, tokens: List[Union[Token, TokenGroup]], 
                replacement: Union[List[Union[Token, TokenGroup]], callable]) -> List[Union[Token, TokenGroup]]:
        """
        Replace all occurrences of this pattern.
        
        Args:
            tokens: List of tokens/groups to process
            replacement: Either a list of replacement tokens or a callable
                        that takes a Match and returns replacement tokens
            
        Returns:
            New list with replacements applied
        """
        result = []
        i = 0
        
        while i < len(tokens):
            match = self.match(tokens, i)
            if match:
                # Apply replacement
                if callable(replacement):
                    result.extend(replacement(match))
                else:
                    result.extend(replacement)
                i = match.end_index
            else:
                result.append(tokens[i])
                i += 1
        
        return result
    
    def test(self, tokens: List[Union[Token, TokenGroup]]) -> bool:
        """
        Test if this pattern matches anywhere in the token list.
        
        Args:
            tokens: List of tokens/groups to test
            
        Returns:
            True if pattern matches, False otherwise
        """
        return self.find(tokens) is not None
    
    def count(self, tokens: List[Union[Token, TokenGroup]]) -> int:
        """
        Count the number of non-overlapping matches.
        
        Args:
            tokens: List of tokens/groups to search
            
        Returns:
            Number of matches found
        """
        return sum(1 for _ in self.find_all(tokens))


class TokenListPattern(Pattern):
    """
    Helper base class for patterns that work with flat token lists.
    
    Automatically handles flattening of TokenGroups if needed.
    """
    
    def _ensure_tokens(self, items: List[Union[Token, TokenGroup]]) -> List[Token]:
        """Convert mixed list to flat token list."""
        result = []
        for item in items:
            if isinstance(item, Token):
                result.append(item)
            elif isinstance(item, TokenGroup):
                result.extend(item.flatten())
        return result


class CompositePattern(Pattern):
    """
    Base class for patterns that combine other patterns.
    """
    
    def __init__(self, *patterns: Pattern):
        self.patterns = patterns
