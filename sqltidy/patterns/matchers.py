"""
General-purpose pattern matchers for SQL tokens.

These matchers provide building blocks for creating complex pattern matching logic.
"""

import re
from typing import List, Union, Optional, Set, Callable
from .base import Pattern, Match, TokenListPattern, CompositePattern
from ..tokenizer import Token, TokenGroup, TokenType, get_token_type


class TokenMatcher(TokenListPattern):
    """
    Match a single token by value and/or type.
    
    Examples:
        TokenMatcher(value="SELECT")  # Match SELECT keyword
        TokenMatcher(type=TokenType.IDENTIFIER)  # Match any identifier
        TokenMatcher(value="COUNT", type=TokenType.KEYWORD)  # Match COUNT keyword
    """
    
    def __init__(self, value: Optional[str] = None, 
                 type: Optional[TokenType] = None,
                 case_sensitive: bool = False):
        """
        Initialize token matcher.
        
        Args:
            value: Specific token value to match (None = any value)
            type: Token type to match (None = any type)
            case_sensitive: Whether value matching is case-sensitive
        """
        self.value = value
        self.type = type
        self.case_sensitive = case_sensitive
    
    def match(self, tokens: List[Union[Token, TokenGroup]], start: int = 0) -> Optional[Match]:
        if start >= len(tokens):
            return None
        
        item = tokens[start]
        
        # Only match Token objects
        if not isinstance(item, Token):
            return None
        
        # Check type if specified
        if self.type is not None and item.type != self.type:
            return None
        
        # Check value if specified
        if self.value is not None:
            if self.case_sensitive:
                if item.value != self.value:
                    return None
            else:
                if item.value.upper() != self.value.upper():
                    return None
        
        return Match(
            tokens=[item],
            start_index=start,
            end_index=start + 1
        )


class KeywordMatcher(TokenMatcher):
    """
    Match a specific SQL keyword (case-insensitive by default).
    
    Examples:
        KeywordMatcher("SELECT")
        KeywordMatcher("JOIN")
    """
    
    def __init__(self, keyword: str):
        super().__init__(value=keyword, type=TokenType.KEYWORD, case_sensitive=False)
        self.keyword = keyword.upper()


class IdentifierMatcher(Pattern):
    """
    Match identifiers with optional pattern matching.
    
    Examples:
        IdentifierMatcher()  # Match any identifier
        IdentifierMatcher(pattern=r"tbl_.*")  # Match identifiers starting with tbl_
    """
    
    def __init__(self, pattern: Optional[str] = None, case_sensitive: bool = False):
        """
        Initialize identifier matcher.
        
        Args:
            pattern: Regex pattern for identifier name (None = any identifier)
            case_sensitive: Whether pattern matching is case-sensitive
        """
        self.pattern = pattern
        self.case_sensitive = case_sensitive
        self._regex = None
        
        if pattern:
            flags = 0 if case_sensitive else re.IGNORECASE
            self._regex = re.compile(pattern, flags)
    
    def match(self, tokens: List[Union[Token, TokenGroup]], start: int = 0) -> Optional[Match]:
        if start >= len(tokens):
            return None
        
        item = tokens[start]
        
        if not isinstance(item, Token) or item.type != TokenType.IDENTIFIER:
            return None
        
        if self._regex and not self._regex.match(item.value):
            return None
        
        return Match(
            tokens=[item],
            start_index=start,
            end_index=start + 1,
            metadata={"identifier": item.value}
        )


class WhitespaceMatcher(TokenMatcher):
    """
    Match whitespace tokens (space or newline).
    
    Examples:
        WhitespaceMatcher()  # Match any whitespace
        WhitespaceMatcher(include_newlines=False)  # Match spaces only
    """
    
    def __init__(self, include_newlines: bool = True):
        self.include_newlines = include_newlines
    
    def match(self, tokens: List[Union[Token, TokenGroup]], start: int = 0) -> Optional[Match]:
        if start >= len(tokens):
            return None
        
        item = tokens[start]
        
        if not isinstance(item, Token):
            return None
        
        if self.include_newlines:
            if item.type not in (TokenType.WHITESPACE, TokenType.NEWLINE):
                return None
        else:
            if item.type != TokenType.WHITESPACE:
                return None
        
        return Match(
            tokens=[item],
            start_index=start,
            end_index=start + 1
        )


class OperatorMatcher(TokenMatcher):
    """
    Match a specific operator.
    
    Examples:
        OperatorMatcher("=")
        OperatorMatcher(">=")
    """
    
    def __init__(self, operator: str):
        super().__init__(value=operator, type=TokenType.OPERATOR)


class AnyOfMatcher(Pattern):
    """
    Match any one of the given patterns.
    
    Examples:
        AnyOfMatcher(KeywordMatcher("LEFT"), KeywordMatcher("RIGHT"))
        AnyOfMatcher(*[TokenMatcher(value=op) for op in ["=", "<", ">"]])
    """
    
    def __init__(self, *patterns: Pattern):
        self.patterns = patterns
    
    def match(self, tokens: List[Union[Token, TokenGroup]], start: int = 0) -> Optional[Match]:
        for pattern in self.patterns:
            result = pattern.match(tokens, start)
            if result:
                return result
        return None


class SequenceMatcher(CompositePattern):
    """
    Match a sequence of patterns in order.
    
    Examples:
        # Match "LEFT JOIN"
        SequenceMatcher(KeywordMatcher("LEFT"), KeywordMatcher("JOIN"))
        
        # Match "table AS alias"
        SequenceMatcher(
            IdentifierMatcher(),
            KeywordMatcher("AS"),
            IdentifierMatcher()
        )
    """
    
    def __init__(self, *patterns: Pattern, skip_whitespace: bool = True):
        """
        Initialize sequence matcher.
        
        Args:
            patterns: Patterns to match in sequence
            skip_whitespace: Whether to automatically skip whitespace between patterns
        """
        super().__init__(*patterns)
        self.skip_whitespace = skip_whitespace
    
    def match(self, tokens: List[Union[Token, TokenGroup]], start: int = 0) -> Optional[Match]:
        matched_tokens = []
        current_pos = start
        metadata = {}
        
        for i, pattern in enumerate(self.patterns):
            # Skip whitespace if enabled
            if self.skip_whitespace:
                while current_pos < len(tokens):
                    if isinstance(tokens[current_pos], Token):
                        if tokens[current_pos].type in (TokenType.WHITESPACE, TokenType.NEWLINE):
                            matched_tokens.append(tokens[current_pos])
                            current_pos += 1
                            continue
                    break
            
            # Try to match the pattern
            result = pattern.match(tokens, current_pos)
            if not result:
                return None
            
            matched_tokens.extend(result.tokens)
            current_pos = result.end_index
            
            # Preserve metadata from sub-matches
            if result.metadata:
                metadata[f"match_{i}"] = result.metadata
        
        if not matched_tokens:
            return None
        
        return Match(
            tokens=matched_tokens,
            start_index=start,
            end_index=current_pos,
            metadata=metadata if metadata else None
        )


class OptionalMatcher(Pattern):
    """
    Match a pattern zero or one time.
    
    Examples:
        # Match optional "AS" keyword
        OptionalMatcher(KeywordMatcher("AS"))
    """
    
    def __init__(self, pattern: Pattern):
        self.pattern = pattern
    
    def match(self, tokens: List[Union[Token, TokenGroup]], start: int = 0) -> Optional[Match]:
        result = self.pattern.match(tokens, start)
        
        if result:
            return result
        else:
            # Return empty match at current position
            return Match(
                tokens=[],
                start_index=start,
                end_index=start
            )


class RepeatMatcher(Pattern):
    """
    Match a pattern multiple times.
    
    Examples:
        # Match one or more identifiers separated by commas
        RepeatMatcher(
            SequenceMatcher(IdentifierMatcher(), TokenMatcher(value=",")),
            min_count=1
        )
    """
    
    def __init__(self, pattern: Pattern, min_count: int = 0, max_count: Optional[int] = None):
        """
        Initialize repeat matcher.
        
        Args:
            pattern: Pattern to repeat
            min_count: Minimum number of matches required
            max_count: Maximum number of matches allowed (None = unlimited)
        """
        self.pattern = pattern
        self.min_count = min_count
        self.max_count = max_count
    
    def match(self, tokens: List[Union[Token, TokenGroup]], start: int = 0) -> Optional[Match]:
        matched_tokens = []
        current_pos = start
        count = 0
        
        while True:
            # Check if we've reached max count
            if self.max_count is not None and count >= self.max_count:
                break
            
            # Try to match pattern
            result = self.pattern.match(tokens, current_pos)
            if not result:
                break
            
            matched_tokens.extend(result.tokens)
            current_pos = result.end_index
            count += 1
        
        # Check minimum count requirement
        if count < self.min_count:
            return None
        
        return Match(
            tokens=matched_tokens,
            start_index=start,
            end_index=current_pos,
            metadata={"count": count}
        )


class BetweenMatcher(Pattern):
    """
    Match all tokens between two patterns (inclusive or exclusive).
    
    Examples:
        # Match everything between "(" and ")"
        BetweenMatcher(
            TokenMatcher(value="("),
            TokenMatcher(value=")"),
            inclusive=True
        )
    """
    
    def __init__(self, start_pattern: Pattern, end_pattern: Pattern, 
                 inclusive: bool = True, greedy: bool = False):
        """
        Initialize between matcher.
        
        Args:
            start_pattern: Pattern marking the start
            end_pattern: Pattern marking the end
            inclusive: Include the start and end tokens in the match
            greedy: Use greedy matching (match to last occurrence of end_pattern)
        """
        self.start_pattern = start_pattern
        self.end_pattern = end_pattern
        self.inclusive = inclusive
        self.greedy = greedy
    
    def match(self, tokens: List[Union[Token, TokenGroup]], start: int = 0) -> Optional[Match]:
        # Match start pattern
        start_match = self.start_pattern.match(tokens, start)
        if not start_match:
            return None
        
        # Find end pattern
        search_pos = start_match.end_index
        end_match = None
        last_end_match = None
        
        while search_pos < len(tokens):
            result = self.end_pattern.match(tokens, search_pos)
            if result:
                end_match = result
                if not self.greedy:
                    break
                last_end_match = result
                search_pos = result.end_index
            else:
                search_pos += 1
        
        if self.greedy and last_end_match:
            end_match = last_end_match
        
        if not end_match:
            return None
        
        # Determine which tokens to include
        if self.inclusive:
            matched_tokens = tokens[start:end_match.end_index]
            end_index = end_match.end_index
        else:
            matched_tokens = tokens[start_match.end_index:end_match.start_index]
            end_index = end_match.end_index
        
        return Match(
            tokens=matched_tokens,
            start_index=start,
            end_index=end_index
        )


class PredicateMatcher(Pattern):
    """
    Match tokens using a custom predicate function.
    
    Examples:
        # Match any keyword
        PredicateMatcher(lambda t: isinstance(t, Token) and t.type == TokenType.KEYWORD)
        
        # Match long identifiers
        PredicateMatcher(lambda t: isinstance(t, Token) and 
                                   t.type == TokenType.IDENTIFIER and 
                                   len(t.value) > 10)
    """
    
    def __init__(self, predicate: Callable[[Union[Token, TokenGroup]], bool]):
        """
        Initialize predicate matcher.
        
        Args:
            predicate: Function that returns True if token/group matches
        """
        self.predicate = predicate
    
    def match(self, tokens: List[Union[Token, TokenGroup]], start: int = 0) -> Optional[Match]:
        if start >= len(tokens):
            return None
        
        item = tokens[start]
        
        if self.predicate(item):
            return Match(
                tokens=[item],
                start_index=start,
                end_index=start + 1
            )
        
        return None
