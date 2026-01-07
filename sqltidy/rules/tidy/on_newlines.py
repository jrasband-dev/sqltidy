"""
ON keyword formatting rule using semantic tokenizer.

This rule ensures ON keywords in JOIN clauses appear on a new line
below the JOIN and table name for better readability.
"""

from typing import List
from ..base import BaseRule, ConfigField, FormatterContext
from sqltidy.tokenizer import tokenize_with_types, Token, TokenType, SemanticLevel


class OnNewlinesRule(BaseRule):
    """
    Format JOIN clauses with ON keyword on a new line.
    
    This rule uses the semantic tokenizer to identify JOIN clauses
    and format them with ON on a separate line.
    
    Example:
        Before:
            INNER JOIN table2 ON table1.id = table2.id
        
        After (on_newlines=True):
            INNER JOIN table2
            ON table1.id = table2.id
    
    Configuration:
        on_newlines (bool): If True, place ON keyword on new line after JOIN
    """
    rule_type = "tidy"
    order = 26  # After newline_on_join (25), before where_newlines (30)
    
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
    
    def apply(self, tokens: List[str], ctx: FormatterContext) -> List[str]:
        """Apply ON newline formatting using semantic tokenizer."""
        enabled = getattr(ctx.config, "on_newlines", False)
        
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
        in_join = False
        join_start = -1
        
        while i < len(flat_tokens):
            token = flat_tokens[i]
            
            # Detect JOIN keywords
            if token.type == TokenType.KEYWORD and token.value.upper() in self.JOIN_KEYWORDS:
                in_join = True
                join_start = len(result)
                result.append(token)
                i += 1
                continue
            
            # When in JOIN, look for ON keyword
            if in_join and token.type == TokenType.KEYWORD and token.value.upper() == 'ON':
                # Remove trailing whitespace before ON
                while result and result[-1].type in (TokenType.WHITESPACE, TokenType.NEWLINE):
                    result.pop()
                
                # Add newline before ON
                result.append(Token('\n', TokenType.NEWLINE))
                result.append(token)
                in_join = False
                i += 1
                
                # Skip following whitespace and add single space
                while i < len(flat_tokens) and flat_tokens[i].type in (TokenType.WHITESPACE, TokenType.NEWLINE):
                    i += 1
                
                if i < len(flat_tokens):
                    result.append(Token(' ', TokenType.WHITESPACE))
                
                continue
            
            # Exit JOIN context if we hit another major clause keyword without finding ON
            if in_join and token.type == TokenType.KEYWORD:
                keyword = token.value.upper()
                if keyword in ('WHERE', 'GROUP', 'HAVING', 'ORDER', 'UNION', 'EXCEPT', 'INTERSECT', 'SELECT', 'FROM'):
                    in_join = False
            
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
