"""
Column newline formatting rule using Token objects.

This rule ensures each column in a SELECT statement appears on its own line
for better readability.
"""

from typing import List, Union
from ..base import BaseRule, ConfigField, FormatterContext
from sqltidy.tokenizer import Token, TokenGroup, TokenType, GroupType


class ColumnsNewlineRule(BaseRule):
    """
    Format SELECT columns with each column on its own line.
    
    Example:
        Before:
            SELECT Column1, Column2, Column3, Column4
        
        After (columns_newline=True):
            SELECT
                Column1,
                Column2,
                Column3,
                Column4
    
    Configuration:
        columns_newline (bool): If True, place each column on its own line
        
    Works with Token objects for efficiency - no re-tokenization needed.
    """
    rule_type = "tidy"
    order = 36  # After all other tokenizer-based rules to preserve column formatting
    supports_token_objects = True
    
    config_fields = {
        "columns_newline": ConfigField(
            name="columns_newline",
            default=True,
            description="Place each SELECT column on its own line?",
            field_type=bool
        )
    }
    
    def apply(self, tokens: List[Union[Token, TokenGroup]], ctx: FormatterContext) -> List[Union[Token, TokenGroup]]:
        """Apply column newline formatting using Token objects."""
        enabled = getattr(ctx.config, "columns_newline", self.config_fields["columns_newline"].default)
        
        if not enabled:
            return tokens
        
        return self._process_tokens(tokens, in_select=False, in_group=False, first_column_seen=False)
    
    def _process_tokens(self, tokens: List[Union[Token, TokenGroup]], in_select: bool = False, 
                       in_group: bool = False, first_column_seen: bool = False) -> List[Union[Token, TokenGroup]]:
        """
        Recursively process tokens to format SELECT columns with newlines.
        
        Args:
            tokens: List of Token and TokenGroup objects to process
            in_select: Whether we're currently inside a SELECT clause
            in_group: Whether we're inside a parenthesis group
            first_column_seen: Whether we've seen the first column
            
        Returns:
            Processed list of tokens with newlines added after commas
        """
        result = []
        i = 0
        
        while i < len(tokens):
            token = tokens[i]
            
            if isinstance(token, TokenGroup):
                # Check if this is a SELECT clause group
                if token.group_type == GroupType.SELECT_CLAUSE:
                    # Process SELECT clause with in_select=True
                    processed_tokens = self._process_tokens(token.tokens, in_select=True, 
                                                          in_group=in_group, first_column_seen=False)
                    # Ensure the SELECT clause ends with a newline so the next clause (e.g., FROM) starts on a new line
                    if processed_tokens and isinstance(processed_tokens[-1], Token) and processed_tokens[-1].type != TokenType.NEWLINE:
                        processed_tokens = processed_tokens + [Token('\n', TokenType.NEWLINE)]
                    result.append(TokenGroup(
                        token.group_type,
                        processed_tokens,
                        token.name,
                        token.metadata
                    ))
                elif token.group_type in (GroupType.PARENTHESIS, GroupType.SUBQUERY, GroupType.FUNCTION):
                    # Inside parentheses - recursively process but mark as in_group
                    processed_tokens = self._process_tokens(token.tokens, in_select=in_select, 
                                                          in_group=True, first_column_seen=first_column_seen)
                    result.append(TokenGroup(
                        token.group_type,
                        processed_tokens,
                        token.name,
                        token.metadata
                    ))
                else:
                    # Recursively process other groups
                    processed_tokens = self._process_tokens(token.tokens, in_select=in_select, 
                                                          in_group=in_group, first_column_seen=first_column_seen)
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
                # Detect SELECT keyword
                if token.type == TokenType.KEYWORD and token.value.upper() == 'SELECT':
                    in_select = True
                    first_column_seen = False
                    result.append(token)
                    i += 1
                    
                    # Skip whitespace after SELECT
                    while i < len(tokens) and isinstance(tokens[i], Token) and tokens[i].type in (TokenType.WHITESPACE, TokenType.NEWLINE):
                        i += 1
                    
                    # Add newline after SELECT
                    result.append(Token('\n', TokenType.NEWLINE))
                    continue
                
                # Check for FROM keyword - ends SELECT column list
                if in_select and not in_group and token.type == TokenType.KEYWORD:
                    keyword = token.value.upper()
                    if keyword in ('FROM', 'INTO', 'WHERE', 'GROUP', 'ORDER', 'HAVING', 'UNION', 'EXCEPT', 'INTERSECT'):
                        in_select = False
                        first_column_seen = False
                        
                        # Remove trailing whitespace
                        while result and isinstance(result[-1], Token) and result[-1].type in (TokenType.WHITESPACE, TokenType.NEWLINE):
                            result.pop()
                        
                        # Add newline before FROM
                        result.append(Token('\n', TokenType.NEWLINE))
                        result.append(token)
                        i += 1
                        continue
                
                # Handle commas in SELECT column list
                if in_select and not in_group and token.type == TokenType.PUNCTUATION and token.value == ',':
                    result.append(token)
                    i += 1
                    
                    # Skip whitespace after comma
                    while i < len(tokens) and isinstance(tokens[i], Token) and tokens[i].type in (TokenType.WHITESPACE, TokenType.NEWLINE):
                        i += 1
                    
                    # Add newline after comma (indentation will be added by indent_select_columns rule)
                    result.append(Token('\n', TokenType.NEWLINE))
                    
                    # Mark that we've seen the first column
                    first_column_seen = True
                    continue
                
                # Handle first column in SELECT - just mark as seen (indentation will be added by indent_select_columns rule)
                if in_select and not first_column_seen and not in_group and token.type not in (TokenType.WHITESPACE, TokenType.NEWLINE, TokenType.COMMENT):
                    # This is the first column
                    first_column_seen = True
                    # Don't add indentation here - let indent_select_columns handle it
                    result.append(token)
                    i += 1
                    continue
                
                result.append(token)
                i += 1
        
        return result
    
    def __repr__(self):
        return f"<ColumnsNewlineRule(order={self.order})>"
