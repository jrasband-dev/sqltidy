"""
Pattern-based tokenizer integration.

This module provides functions to apply patterns during tokenization,
bridging the new pattern system with the existing tokenizer.
"""

from typing import List, Union, Optional
from .patterns import Pattern, MatchContext, MatchResult, register_pattern
from .patterns.general import CTEPattern, WindowFunctionPattern, SubqueryPattern
from .tokenizer import Token, TokenGroup, GroupType
from .dialects.base import SQLDialect


def initialize_default_patterns():
    """
    Initialize and register default SQL patterns.

    This should be called once at module load time to set up
    the global pattern registry with standard SQL patterns.
    """
    # Register standard SQL patterns (applicable to all dialects)
    register_pattern(CTEPattern())
    register_pattern(WindowFunctionPattern())
    register_pattern(SubqueryPattern())


def apply_patterns(
    tokens: List[Union[Token, TokenGroup]],
    dialect: SQLDialect,
    parent_group_type: Optional[GroupType] = None,
) -> List[Union[Token, TokenGroup]]:
    """
    Apply registered patterns to identify SQL constructs.

    This is the new pattern-based replacement for apply_semantic_patterns.

    Args:
        tokens: List of tokens and groups
        dialect: SQL dialect for dialect-specific patterns
        parent_group_type: Type of parent group (to avoid duplicate nesting)

    Returns:
        List with patterns identified and grouped
    """
    # First, recursively process any existing groups
    processed = []
    for item in tokens:
        if isinstance(item, TokenGroup):
            # Process tokens within this group
            new_tokens = apply_patterns(item.tokens, dialect, item.group_type)
            processed.append(
                TokenGroup(item.group_type, new_tokens, item.name, item.metadata)
            )
        else:
            processed.append(item)

    # Get all applicable patterns (global + dialect-specific)
    from .patterns import get_all_patterns

    global_patterns = get_all_patterns()
    dialect_patterns = dialect.get_patterns()
    all_patterns = global_patterns + dialect_patterns

    # Filter patterns by applicability to current dialect
    applicable_patterns = [p for p in all_patterns if p.is_applicable(dialect)]

    # Apply each pattern
    result = processed
    for pattern in applicable_patterns:
        result = _apply_single_pattern(result, pattern, dialect, parent_group_type)

    return result


def _apply_single_pattern(
    tokens: List[Union[Token, TokenGroup]],
    pattern: Pattern,
    dialect: SQLDialect,
    parent_group_type: Optional[GroupType],
) -> List[Union[Token, TokenGroup]]:
    """
    Apply a single pattern to the token list.

    Args:
        tokens: List of tokens to process
        pattern: Pattern to apply
        dialect: SQL dialect
        parent_group_type: Parent group type (to avoid duplicate nesting)

    Returns:
        List with pattern applied
    """
    result = []
    i = 0

    while i < len(tokens):
        # Create match context
        context = MatchContext(
            dialect=dialect,
            tokens=tokens,
            start_index=i,
            parent_group_type=parent_group_type,
        )

        # Try to match pattern
        match = pattern.match(context)

        if match.success and len(match.matched_tokens) > 0:
            # Pattern matched - create TokenGroup if needed
            if match.group_type:
                # Avoid duplicate nesting
                if match.group_type != parent_group_type:
                    group = TokenGroup(
                        group_type=match.group_type,
                        tokens=match.matched_tokens,
                        name=match.group_name,
                        metadata=match.metadata,
                    )
                    result.append(group)
                else:
                    # Don't nest same type - just add tokens
                    result.extend(match.matched_tokens)
            else:
                # No group type specified - just add matched tokens
                result.extend(match.matched_tokens)

            # Advance past matched tokens
            i = match.end_index
        else:
            # No match - add current token and advance
            result.append(tokens[i])
            i += 1

    return result


def create_pattern_from_match(match: MatchResult) -> Optional[TokenGroup]:
    """
    Create a TokenGroup from a MatchResult.

    Args:
        match: The match result to convert

    Returns:
        TokenGroup if match has group_type, None otherwise
    """
    if not match.success or not match.group_type:
        return None

    return TokenGroup(
        group_type=match.group_type,
        tokens=match.matched_tokens,
        name=match.group_name,
        metadata=match.metadata,
    )


# Initialize default patterns when module is imported
initialize_default_patterns()


__all__ = [
    "initialize_default_patterns",
    "apply_patterns",
    "create_pattern_from_match",
]
