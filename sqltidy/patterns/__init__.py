"""
SQL pattern matching utilities.

This module provides building blocks for creating custom SQL formatting rules
by offering high-level pattern matchers for common SQL constructs.

Basic Usage:
    from sqltidy.patterns import JoinPattern, KeywordMatcher
    from sqltidy.plugins import sqltidy_rule
    
    @sqltidy_rule(rule_type="tidy", order=25)
    def format_joins(tokens, ctx):
        '''Ensure JOINs have ON clause on new line.'''
        from sqltidy.tokenizer import tokenize_with_types
        
        # Convert to typed tokens
        typed_tokens = tokenize_with_types(''.join(tokens), ctx.config.dialect)
        
        # Find all JOIN patterns
        join_pattern = JoinPattern(require_on=True)
        for match in join_pattern.find_all(typed_tokens):
            # Process match...
            print(f"Found {match.metadata['join_type']} on {match.metadata['table']}")
        
        return tokens

Pattern Types:
    - Token Matchers: Match individual tokens (KeywordMatcher, IdentifierMatcher, etc.)
    - Sequence Matchers: Match sequences of patterns (SequenceMatcher, RepeatMatcher, etc.)
    - SQL Patterns: Match SQL constructs (JoinPattern, SubqueryPattern, CTEPattern, etc.)
"""

from .base import Pattern, Match
from .matchers import (
    TokenMatcher,
    KeywordMatcher,
    IdentifierMatcher,
    WhitespaceMatcher,
    OperatorMatcher,
    AnyOfMatcher,
    SequenceMatcher,
    OptionalMatcher,
    RepeatMatcher,
    BetweenMatcher,
    PredicateMatcher
)
from .sql import (
    JoinPattern,
    SelectClausePattern,
    WhereClausePattern,
    SubqueryPattern,
    FunctionCallPattern,
    CaseExpressionPattern,
    CTEPattern,
    GroupByPattern,
    OrderByPattern,
    HavingPattern,
    UnionPattern,
    DistinctPattern,
    LimitPattern
)

__all__ = [
    # Base classes
    'Pattern',
    'Match',
    
    # Token matchers
    'TokenMatcher',
    'KeywordMatcher',
    'IdentifierMatcher',
    'WhitespaceMatcher',
    'OperatorMatcher',
    
    # Composite matchers
    'AnyOfMatcher',
    'SequenceMatcher',
    'OptionalMatcher',
    'RepeatMatcher',
    'BetweenMatcher',
    'PredicateMatcher',
    
    # SQL patterns
    'JoinPattern',
    'SelectClausePattern',
    'WhereClausePattern',
    'SubqueryPattern',
    'FunctionCallPattern',
    'CaseExpressionPattern',
    'CTEPattern',
    'GroupByPattern',
    'OrderByPattern',
    'HavingPattern',
    'UnionPattern',
    'DistinctPattern',
    'LimitPattern',
]
