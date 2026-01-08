"""
ON keyword formatting rule using Token objects.

This rule ensures ON keywords in JOIN clauses appear on a new line
below the JOIN and table name for better readability.
"""

from typing import List, Union
from ..base import BaseRule, ConfigField, FormatterContext
from sqltidy.tokenizer import Token, TokenGroup, TokenType, GroupType


class OnNewlinesRule(BaseRule):
    """
    Format JOIN clauses with ON keyword on a new line.
    
    Example:
        Before:
            INNER JOIN table2 ON table1.id = table2.id
        
        After (on_newlines=True):
            INNER JOIN table2
            ON table1.id = table2.id
    
    Configuration:
        on_newlines (bool): If True, place ON keyword on new line after JOIN
        
    Works with Token objects for efficiency - no re-tokenization needed.
    """
    rule_type = "tidy"
    order = 26  # After newline_on_join (25), before where_newlines (30)
    supports_token_objects = True
    
    config_fields = {
        "on_newlines": ConfigField(
            name="on_newlines",
            default=True,
            description="Place ON keyword on new line after JOIN clauses?",
            field_type=bool
        )
    }
    
    # JOIN keywords to detect
    JOIN_KEYWORDS = {
        'INNER', 'LEFT', 'RIGHT', 'FULL', 'CROSS', 
        'OUTER', 'JOIN', 'APPLY'
    }
    
    def apply(self, tokens: List[Union[Token, TokenGroup]], ctx: FormatterContext) -> List[Union[Token, TokenGroup]]:
        """Apply ON newline formatting using Token objects."""
        enabled = getattr(ctx.config, "on_newlines", self.config_fields["on_newlines"].default)
        
        if not enabled:
            return tokens
        
        return self._process_tokens(tokens, in_join=False)
    
    def _process_tokens(self, tokens: List[Union[Token, TokenGroup]], in_join: bool = False) -> List[Union[Token, TokenGroup]]:
        """
        Recursively process tokens to add newlines before ON keywords.
        
        Args:
            tokens: List of Token and TokenGroup objects to process
            in_join: Whether we're currently inside a JOIN clause
            
        Returns:
            Processed list of tokens with newlines added before ON
        """
        result = []
        i = 0
        
        while i < len(tokens):
            token = tokens[i]
            
            if isinstance(token, TokenGroup):
                # Check if this is an ON_CONDITION group following a JOIN
                if token.group_type == GroupType.ON_CONDITION:
                    # Remove trailing whitespace before ON group
                    while result and isinstance(result[-1], Token) and result[-1].type in (TokenType.WHITESPACE, TokenType.NEWLINE):
                        result.pop()
                    
                    # Add newline before ON group
                    result.append(Token('\n', TokenType.NEWLINE))
                    
                    # Recursively process the ON group contents
                    processed_tokens = self._process_tokens(token.tokens, in_join)
                    result.append(TokenGroup(
                        token.group_type,
                        processed_tokens,
                        token.name,
                        token.metadata
                    ))
                    i += 1
                    continue
                    
                # Recursively process other groups
                processed_tokens = self._process_tokens(token.tokens, in_join)
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
                # Detect JOIN keywords
                if token.type == TokenType.KEYWORD and token.value.upper() in self.JOIN_KEYWORDS:
                    in_join = True
                    result.append(token)
                    i += 1
                    continue
                
                # When in JOIN, look for ON keyword
                if in_join and token.type == TokenType.KEYWORD and token.value.upper() == 'ON':
                    # Remove trailing whitespace before ON
                    while result and isinstance(result[-1], Token) and result[-1].type in (TokenType.WHITESPACE, TokenType.NEWLINE):
                        result.pop()
                    
                    # Add newline before ON
                    result.append(Token('\n', TokenType.NEWLINE))
                    result.append(token)
                    in_join = False
                    i += 1
                    
                    # Skip following whitespace and add single space
                    while i < len(tokens) and isinstance(tokens[i], Token) and tokens[i].type in (TokenType.WHITESPACE, TokenType.NEWLINE):
                        i += 1
                    
                    if i < len(tokens):
                        result.append(Token(' ', TokenType.WHITESPACE))
                    
                    continue
                
                # Exit JOIN context if we hit another major clause keyword without finding ON
                if in_join and token.type == TokenType.KEYWORD:
                    keyword = token.value.upper()
                    if keyword in ('WHERE', 'GROUP', 'HAVING', 'ORDER', 'UNION', 'EXCEPT', 'INTERSECT', 'SELECT', 'FROM'):
                        in_join = False
                
                result.append(token)
                i += 1
        
        return result
