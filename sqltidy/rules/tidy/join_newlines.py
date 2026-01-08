"""
JOIN newline formatting rule using Token objects.

This rule ensures JOIN keywords appear on a new line with a blank line before them.
"""

from typing import List, Union
from ..base import BaseRule, ConfigField, FormatterContext
from sqltidy.tokenizer import Token, TokenGroup, TokenType, GroupType


class NewlineJoinPatternRule(BaseRule):
    """
    Ensures JOIN keywords appear on a new line with a blank line before them.
    
    Example:
        Before:
            FROM Table1 INNER JOIN Table2 ON Table1.Id = Table2.ID LEFT JOIN Table3
        
        After:
            FROM Table1
            
            INNER JOIN Table2
            ON Table1.Id = Table2.ID
            
            LEFT JOIN Table3
    
    Configuration:
        join_newlines (bool): If True, adds blank line before JOIN keywords
        
    Works with Token objects for efficiency - no re-tokenization needed.
    """
    rule_type = "tidy"
    order = 24  # Before on_newlines (26)
    supports_token_objects = True
    
    config_fields = {
        "join_newlines": ConfigField(
            name="join_newlines",
            default=True,
            description="Add blank line before JOIN keywords?",
            field_type=bool
        )
    }
    
    # JOIN keywords to detect
    JOIN_KEYWORDS = {
        'INNER', 'LEFT', 'RIGHT', 'FULL', 'CROSS', 
        'OUTER', 'JOIN', 'APPLY'
    }
    
    def apply(self, tokens: List[Union[Token, TokenGroup]], ctx: FormatterContext) -> List[Union[Token, TokenGroup]]:
        """Apply JOIN newline formatting using Token objects."""
        enabled = getattr(ctx.config, "join_newlines", self.config_fields["join_newlines"].default)
        
        if not enabled:
            return tokens
        
        return self._process_tokens(tokens, first_table_after_from=False)
    
    def _process_tokens(self, tokens: List[Union[Token, TokenGroup]], first_table_after_from: bool = False) -> List[Union[Token, TokenGroup]]:
        """
        Recursively process tokens to add blank lines before JOIN keywords.
        
        Args:
            tokens: List of Token and TokenGroup objects to process
            first_table_after_from: Whether we're right after a FROM keyword
            
        Returns:
            Processed list of tokens with blank lines added before JOINs
        """
        result = []
        i = 0
        
        while i < len(tokens):
            token = tokens[i]
            
            if isinstance(token, TokenGroup):
                # Recursively process groups
                processed_tokens = self._process_tokens(token.tokens, first_table_after_from)
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
                # Track if we're right after FROM
                if token.type == TokenType.KEYWORD and token.value.upper() == 'FROM':
                    first_table_after_from = True
                    result.append(token)
                    i += 1
                    continue
                
                # Detect JOIN keyword
                if token.type == TokenType.KEYWORD and token.value.upper() == 'JOIN':
                    # This is the JOIN keyword - check if we should add blank line
                    if not first_table_after_from:
                        # Remove trailing whitespace
                        while result and isinstance(result[-1], Token) and result[-1].type in (TokenType.WHITESPACE, TokenType.NEWLINE):
                            result.pop()
                        
                        # Look back to see if there's INNER, LEFT, RIGHT, FULL, CROSS, OUTER before this
                        if result and isinstance(result[-1], Token) and result[-1].type == TokenType.KEYWORD:
                            last_keyword = result[-1].value.upper()
                            if last_keyword in ('INNER', 'LEFT', 'RIGHT', 'FULL', 'CROSS', 'OUTER'):
                                # Remove the modifier temporarily
                                modifiers = [result.pop()]
                                
                                # Remove whitespace before modifier
                                while result and isinstance(result[-1], Token) and result[-1].type in (TokenType.WHITESPACE, TokenType.NEWLINE):
                                    result.pop()
                                
                                # Check for second modifier (e.g., LEFT OUTER)
                                if result and isinstance(result[-1], Token) and result[-1].type == TokenType.KEYWORD:
                                    second_keyword = result[-1].value.upper()
                                    if second_keyword in ('LEFT', 'RIGHT', 'FULL', 'OUTER'):
                                        modifiers.insert(0, result.pop())
                                        while result and isinstance(result[-1], Token) and result[-1].type in (TokenType.WHITESPACE, TokenType.NEWLINE):
                                            result.pop()
                                
                                # Add a single newline, then modifiers
                                result.append(Token('\n', TokenType.NEWLINE))
                                for mod in modifiers:
                                    result.append(mod)
                                    result.append(Token(' ', TokenType.WHITESPACE))
                        else:
                            # Just JOIN without modifiers: add a single newline
                            result.append(Token('\n', TokenType.NEWLINE))
                    
                    result.append(token)
                    first_table_after_from = False
                    i += 1
                    continue
                
                # After seeing a non-whitespace, non-keyword token after FROM, we're past the first table
                if first_table_after_from and token.type not in (TokenType.WHITESPACE, TokenType.NEWLINE, TokenType.KEYWORD):
                    first_table_after_from = False
                
                result.append(token)
                i += 1
        
        return result
    
    def __repr__(self):
        return f"<NewlineJoinPatternRule(order={self.order})>"
