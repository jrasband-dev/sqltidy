"""
SELECT newline formatting rule using Token objects.

This rule ensures SELECT keywords appear on their own line with proper spacing.
"""

from typing import List, Union
from ..base import BaseRule, ConfigField, FormatterContext
from sqltidy.tokenizer import Token, TokenGroup, TokenType, GroupType


class SelectNewlineRule(BaseRule):
    """
    Ensure SELECT keywords appear on their own line.
    
    Example:
        Before:
            )SELECT Column1
        
        After (select_newline=True):
            )
            
            SELECT Column1
    
    Configuration:
        select_newline (bool): If True, add blank line before SELECT keywords
        
    Works with Token objects for efficiency - no re-tokenization needed.
    """
    rule_type = "tidy"
    order = 35  # After all other formatting rules to fix spacing around SELECT
    supports_token_objects = True
    
    config_fields = {
        "select_newline": ConfigField(
            name="select_newline",
            default=True,
            description="Add blank line before SELECT keywords?",
            field_type=bool
        )
    }
    
    def apply(self, tokens: List[Union[Token, TokenGroup]], ctx: FormatterContext) -> List[Union[Token, TokenGroup]]:
        """Apply SELECT newline formatting using Token objects."""
        enabled = getattr(ctx.config, "select_newline", self.config_fields["select_newline"].default)
        
        if not enabled:
            return tokens
        
        return self._process_tokens(tokens)
    
    def _process_tokens(self, tokens: List[Union[Token, TokenGroup]]) -> List[Union[Token, TokenGroup]]:
        """
        Process tokens to add blank lines before SELECT keywords.
        """
        result = []
        
        def first_token(g):
            """Recursively find the first token in a group."""
            for it in g.tokens:
                if isinstance(it, Token):
                    return it
                if isinstance(it, TokenGroup):
                    ft = first_token(it)
                    if ft:
                        return ft
            return None
        
        i = 0
        while i < len(tokens):
            token = tokens[i]
            
            if isinstance(token, TokenGroup):
                # Recursively process this group's contents  
                processed_tokens = self._process_tokens(token.tokens)
                
                # Now check: does the NEXT sibling (after this one) start with SELECT?
                # If so, we need to add blank lines to the END of this group's tokens
                next_token = tokens[i + 1] if i + 1 < len(tokens) else None
                
                # Check if next token starts with SELECT
                next_is_select = False
                if next_token:
                    if isinstance(next_token, Token) and next_token.type == TokenType.KEYWORD and next_token.value.upper() == 'SELECT':
                        next_is_select = True
                    elif isinstance(next_token, TokenGroup):
                        ft = first_token(next_token)
                        if ft and ft.type == TokenType.KEYWORD and ft.value.upper() == 'SELECT':
                            next_is_select = True
                
                # If next is SELECT and we have content, add blank lines at END of this group's tokens
                if next_is_select and result:
                    # Remove trailing whitespace from processed_tokens
                    while processed_tokens and isinstance(processed_tokens[-1], Token) and processed_tokens[-1].type in (TokenType.WHITESPACE, TokenType.NEWLINE):
                        processed_tokens.pop()
                    
                    # Add two newlines at the end
                    processed_tokens.append(Token('\n', TokenType.NEWLINE))
                    processed_tokens.append(Token('\n', TokenType.NEWLINE))
                
                group_out = TokenGroup(
                    token.group_type,
                    processed_tokens,
                    token.name,
                    token.metadata
                )
                result.append(group_out)
            else:
                result.append(token)
            
            i += 1
        
        return result
    
    def __repr__(self):
        return f"<SelectNewlineRule(order={self.order})>"
