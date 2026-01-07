"""
JOIN newline formatting rule using semantic tokenizer.

This rule ensures JOIN keywords appear on a new line with a blank line before them.
"""

from typing import List
from ..base import BaseRule, ConfigField, FormatterContext
from sqltidy.tokenizer import tokenize_with_types, Token, TokenType, SemanticLevel


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
    """
    rule_type = "tidy"
    order = 24  # Before on_newlines (26)
    
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
    
    def apply(self, tokens: List[str], ctx: FormatterContext) -> List[str]:
        """Apply JOIN newline formatting using semantic tokenizer."""
        enabled = getattr(ctx.config, "join_newlines", False)
        
        if not enabled:
            return tokens
        
        # Convert string tokens to typed Token objects
        sql = ''.join(tokens)
        typed_tokens = tokenize_with_types(sql, ctx.config.dialect, SemanticLevel.SEMANTIC)
        
        # Flatten to simple token list for processing
        flat_tokens = self._flatten_tokens(typed_tokens)
        
        # Process tokens
        result = []
        i = 0
        first_table_after_from = False
        
        while i < len(flat_tokens):
            token = flat_tokens[i]
            
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
                    while result and result[-1].type in (TokenType.WHITESPACE, TokenType.NEWLINE):
                        result.pop()
                    
                    # Add blank line before the JOIN and any preceding modifiers
                    # Look back to see if there's INNER, LEFT, RIGHT, FULL, CROSS, OUTER before this
                    modifier_start = len(result)
                    if result and result[-1].type == TokenType.KEYWORD:
                        last_keyword = result[-1].value.upper()
                        if last_keyword in ('INNER', 'LEFT', 'RIGHT', 'FULL', 'CROSS', 'OUTER'):
                            # Remove the modifier temporarily
                            modifier_start = len(result) - 1
                            modifiers = [result.pop()]
                            
                            # Remove whitespace before modifier
                            while result and result[-1].type in (TokenType.WHITESPACE, TokenType.NEWLINE):
                                result.pop()
                            
                            # Check for second modifier (e.g., LEFT OUTER)
                            if result and result[-1].type == TokenType.KEYWORD:
                                second_keyword = result[-1].value.upper()
                                if second_keyword in ('LEFT', 'RIGHT', 'FULL', 'OUTER'):
                                    modifiers.insert(0, result.pop())
                                    while result and result[-1].type in (TokenType.WHITESPACE, TokenType.NEWLINE):
                                        result.pop()
                            
                            # Add blank line, then modifiers
                            result.append(Token('\n', TokenType.NEWLINE))
                            result.append(Token('\n', TokenType.NEWLINE))
                            for mod in modifiers:
                                result.append(mod)
                                result.append(Token(' ', TokenType.WHITESPACE))
                    else:
                        # Just JOIN without modifiers
                        result.append(Token('\n', TokenType.NEWLINE))
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
        
        # Convert back to string tokens
        return [t.value for t in result]
    
    def _flatten_tokens(self, tokens: List) -> List[Token]:
        """Flatten token groups to simple token list, preserving parentheses."""
        from sqltidy.tokenizer import TokenGroup, GroupType
        
        result = []
        for item in tokens:
            if isinstance(item, Token):
                result.append(item)
            elif isinstance(item, TokenGroup):
                # For PARENTHESIS and SUBQUERY groups, add the parentheses that the tokenizer excluded
                if item.group_type in (GroupType.PARENTHESIS, GroupType.SUBQUERY):
                    result.append(Token('(', TokenType.PUNCTUATION))
                    result.extend(self._flatten_tokens(item.tokens))
                    result.append(Token(')', TokenType.PUNCTUATION))
                # For FUNCTION groups, first token is function name, rest is args
                elif item.group_type == GroupType.FUNCTION:
                    if item.tokens:
                        result.append(item.tokens[0])  # Function name
                        result.append(Token('(', TokenType.PUNCTUATION))
                        result.extend(self._flatten_tokens(item.tokens[1:]))
                        result.append(Token(')', TokenType.PUNCTUATION))
                else:
                    result.extend(self._flatten_tokens(item.tokens))
        return result
    
    def __repr__(self):
        return f"<NewlineJoinPatternRule(order={self.order})>"
