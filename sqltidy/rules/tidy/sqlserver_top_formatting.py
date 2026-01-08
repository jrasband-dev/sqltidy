"""
SQL Server TOP Keyword Formatting Rule.

This rule only applies to SQL Server dialect and formats the TOP keyword
according to T-SQL conventions.
"""

from typing import List, Union
from ..base import BaseRule, FormatterContext
from sqltidy.tokenizer import Token, TokenGroup, TokenType


class SQLServerTopFormattingRule(BaseRule):
    """
    Format SQL Server TOP keyword with proper spacing.
    
    Examples:
        SELECT TOP 10 * FROM users
        SELECT TOP(100) PERCENT * FROM orders
        SELECT TOP 1 WITH TIES * FROM ranked_items ORDER BY score
    
    This rule only applies to SQL Server dialect.
    """
    rule_type = "tidy"
    order = 25
    supported_dialects = {'sqlserver'}  # Only applies to SQL Server
    supports_token_objects = True  # Use Token-based API
    
    def apply(self, tokens: List[Union[Token, TokenGroup]], ctx: FormatterContext) -> List[Union[Token, TokenGroup]]:
        """Format TOP keyword with consistent spacing using Token objects."""
        return self._process_tokens(tokens)
    
    def _process_tokens(self, tokens: List[Union[Token, TokenGroup]]) -> List[Union[Token, TokenGroup]]:
        """Recursively process tokens to format TOP keyword."""
        result = []
        i = 0
        
        while i < len(tokens):
            token = tokens[i]
            
            if isinstance(token, Token):
                # Look for SELECT followed by TOP
                if token.type == TokenType.KEYWORD and token.value.upper() == 'SELECT':
                    result.append(token)
                    i += 1
                    
                    # Skip whitespace and track it
                    whitespace_tokens = []
                    while i < len(tokens) and isinstance(tokens[i], Token) and tokens[i].type in (TokenType.WHITESPACE, TokenType.NEWLINE):
                        whitespace_tokens.append(tokens[i])
                        i += 1
                    
                    # Check for TOP keyword
                    if i < len(tokens) and isinstance(tokens[i], Token) and tokens[i].type == TokenType.KEYWORD and tokens[i].value.upper() == 'TOP':
                        # Add newline before TOP
                        result.append(Token('\n', TokenType.NEWLINE))
                        result.append(tokens[i])  # TOP keyword
                        i += 1
                        
                        # Ensure space after TOP
                        if i < len(tokens) and isinstance(tokens[i], Token) and tokens[i].type not in (TokenType.WHITESPACE, TokenType.NEWLINE):
                            result.append(Token(' ', TokenType.WHITESPACE))
                        
                        continue
                    else:
                        # No TOP found, restore the whitespace we skipped
                        result.extend(whitespace_tokens)
                        continue
                else:
                    result.append(token)
                    i += 1
                    
            elif isinstance(token, TokenGroup):
                # Recursively process group contents
                processed_tokens = self._process_tokens(token.tokens)
                result.append(TokenGroup(token.group_type, processed_tokens, token.name, token.metadata))
                i += 1
            else:
                result.append(token)
                i += 1
        
        return result
