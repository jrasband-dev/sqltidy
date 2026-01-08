"""
WHERE clause formatting rule using Token objects.

This rule ensures WHERE conditions are formatted with proper newlines
for AND/OR operators, making complex WHERE clauses more readable.
"""

from typing import List, Union
from ..base import BaseRule, ConfigField, FormatterContext
from sqltidy.tokenizer import Token, TokenGroup, TokenType, GroupType


class WhereNewlinesRule(BaseRule):
    """
    Format WHERE clauses with newlines before AND/OR operators.
    
    Example:
        Before:
            WHERE status = 'active' AND created_date >= '2024-01-01' OR user_id = 123
        
        After (where_newlines=True):
            WHERE status = 'active'
            AND created_date >= '2024-01-01'
            OR user_id = 123
    
    Configuration:
        where_newlines (bool): If True, add newlines before AND/OR in WHERE clauses
        
    Works with Token objects for efficiency - no re-tokenization needed.
    """
    rule_type = "tidy"
    order = 30  # After JOIN formatting, before leading commas
    supports_token_objects = True
    
    config_fields = {
        "where_newlines": ConfigField(
            name="where_newlines",
            default=True,
            description="Add newlines before AND/OR operators in WHERE clauses?",
            field_type=bool
        )
    }
    
    # Logical operators to format
    LOGICAL_OPERATORS = {'AND', 'OR'}
    
    # WHERE clause terminators
    CLAUSE_TERMINATORS = {
        'GROUP', 'HAVING', 'ORDER', 'UNION', 'EXCEPT', 'INTERSECT',
        'LIMIT', 'OFFSET', 'FETCH', 'FOR', 'OPTION'
    }
    
    def apply(self, tokens: List[Union[Token, TokenGroup]], ctx: FormatterContext) -> List[Union[Token, TokenGroup]]:
        """Apply WHERE clause formatting using Token objects."""
        enabled = getattr(ctx.config, "where_newlines", self.config_fields["where_newlines"].default)
        
        if not enabled:
            return tokens
        
        return self._process_tokens(tokens, in_where=False, in_group=False)
    
    def _process_tokens(self, tokens: List[Union[Token, TokenGroup]], in_where: bool = False, in_group: bool = False) -> List[Union[Token, TokenGroup]]:
        """
        Recursively process tokens to format WHERE clauses.
        
        Args:
            tokens: List of Token and TokenGroup objects to process
            in_where: Whether we're currently inside a WHERE clause
            in_group: Whether we're inside a parenthesis group (don't format AND/OR)
            
        Returns:
            Processed list of tokens with newlines added before AND/OR
        """
        result = []
        i = 0
        
        while i < len(tokens):
            token = tokens[i]
            
            if isinstance(token, TokenGroup):
                # Check if this is a WHERE clause
                if token.group_type == GroupType.WHERE_CLAUSE:
                    # Process WHERE clause contents with in_where=True
                    processed_tokens = self._process_tokens(token.tokens, in_where=True, in_group=in_group)
                    result.append(TokenGroup(
                        token.group_type,
                        processed_tokens,
                        token.name,
                        token.metadata
                    ))
                elif token.group_type in (GroupType.PARENTHESIS, GroupType.SUBQUERY, GroupType.FUNCTION):
                    # Inside parentheses, don't format AND/OR - just recursively process
                    processed_tokens = self._process_tokens(token.tokens, in_where=in_where, in_group=True)
                    result.append(TokenGroup(
                        token.group_type,
                        processed_tokens,
                        token.name,
                        token.metadata
                    ))
                else:
                    # Recursively process other groups
                    processed_tokens = self._process_tokens(token.tokens, in_where=in_where, in_group=in_group)
                    result.append(TokenGroup(
                        token.group_type,
                        processed_tokens,
                        token.name,
                        token.metadata
                    ))
                i += 1
                continue
            
            # Handle Token objects
            if isinstance(token, Token):
                # Detect WHERE keyword
                if token.type == TokenType.KEYWORD and token.value.upper() == 'WHERE':
                    # Add blank line before WHERE if not already present
                    if result:
                        # Check last token
                        last_is_newline = False
                        if isinstance(result[-1], Token) and result[-1].type == TokenType.NEWLINE:
                            last_is_newline = True
                        
                        if not last_is_newline:
                            # Remove trailing whitespace
                            while result and isinstance(result[-1], Token) and result[-1].type == TokenType.WHITESPACE:
                                result.pop()
                            # Add blank line
                            result.append(Token('\n', TokenType.NEWLINE))
                            result.append(Token('\n', TokenType.NEWLINE))
                    
                    in_where = True
                    result.append(token)
                    i += 1
                    continue
                
                # Check for end of WHERE clause
                if in_where and not in_group and token.type == TokenType.KEYWORD:
                    keyword = token.value.upper()
                    if keyword in self.CLAUSE_TERMINATORS:
                        in_where = False
                
                # Format AND/OR operators in WHERE clause (but not inside groups)
                if in_where and not in_group and token.type == TokenType.KEYWORD:
                    keyword = token.value.upper()
                    if keyword in self.LOGICAL_OPERATORS:
                        # Remove trailing whitespace before AND/OR
                        while result and isinstance(result[-1], Token) and result[-1].type in (TokenType.WHITESPACE, TokenType.NEWLINE):
                            result.pop()
                        
                        # Add newline before AND/OR
                        result.append(Token('\n', TokenType.NEWLINE))
                        result.append(token)
                        i += 1
                        
                        # Skip following whitespace and add single space
                        while i < len(tokens) and isinstance(tokens[i], Token) and tokens[i].type in (TokenType.WHITESPACE, TokenType.NEWLINE):
                            i += 1
                        
                        if i < len(tokens):
                            result.append(Token(' ', TokenType.WHITESPACE))
                        
                        continue
                
                result.append(token)
                i += 1
        
        return result
