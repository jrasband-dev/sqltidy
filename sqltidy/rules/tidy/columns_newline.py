"""
Column newline formatting rule using semantic tokenizer.

This rule ensures each column in a SELECT statement appears on its own line
for better readability.
"""

from typing import List
from ..base import BaseRule, ConfigField, FormatterContext
from sqltidy.tokenizer import tokenize_with_types, Token, TokenType, SemanticLevel


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
    """
    rule_type = "tidy"
    order = 36  # After all other tokenizer-based rules to preserve column formatting
    
    config_fields = {
        "columns_newline": ConfigField(
            name="columns_newline",
            default=True,
            description="Place each SELECT column on its own line?",
            field_type=bool
        )
    }
    
    def apply(self, tokens: List[str], ctx: FormatterContext) -> List[str]:
        """Apply column newline formatting using semantic tokenizer."""
        enabled = getattr(ctx.config, "columns_newline", False)
        
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
        in_select = False
        paren_depth = 0
        first_column_seen = False
        
        while i < len(flat_tokens):
            token = flat_tokens[i]
            
            # Detect SELECT keyword
            if token.type == TokenType.KEYWORD and token.value.upper() == 'SELECT':
                in_select = True
                first_column_seen = False
                result.append(token)
                i += 1
                
                # Skip whitespace after SELECT
                while i < len(flat_tokens) and flat_tokens[i].type in (TokenType.WHITESPACE, TokenType.NEWLINE):
                    i += 1
                
                # Add newline after SELECT
                result.append(Token('\n', TokenType.NEWLINE))
                continue
            
            # Track parentheses depth
            if token.type == TokenType.PUNCTUATION:
                if token.value == '(':
                    paren_depth += 1
                    result.append(token)
                    i += 1
                    continue
                elif token.value == ')':
                    paren_depth -= 1
                    result.append(token)
                    i += 1
                    continue
            
            # Check for FROM keyword - ends SELECT column list
            if in_select and paren_depth == 0 and token.type == TokenType.KEYWORD:
                keyword = token.value.upper()
                if keyword in ('FROM', 'INTO', 'WHERE', 'GROUP', 'ORDER', 'HAVING', 'UNION', 'EXCEPT', 'INTERSECT'):
                    in_select = False
                    first_column_seen = False
                    
                    # Remove trailing whitespace
                    while result and result[-1].type in (TokenType.WHITESPACE, TokenType.NEWLINE):
                        result.pop()
                    
                    # Add newline before FROM
                    result.append(Token('\n', TokenType.NEWLINE))
                    result.append(token)
                    i += 1
                    continue
            
            # Handle commas in SELECT column list
            if in_select and paren_depth == 0 and token.type == TokenType.PUNCTUATION and token.value == ',':
                result.append(token)
                i += 1
                
                # Skip whitespace after comma
                while i < len(flat_tokens) and flat_tokens[i].type in (TokenType.WHITESPACE, TokenType.NEWLINE):
                    i += 1
                
                # Add newline and indentation after comma
                result.append(Token('\n', TokenType.NEWLINE))
                result.append(Token('    ', TokenType.WHITESPACE))
                
                # Mark that we've seen the first column (to prevent double indentation)
                first_column_seen = True
                continue
            
            # Handle first column in SELECT - add indentation
            if in_select and not first_column_seen and token.type not in (TokenType.WHITESPACE, TokenType.NEWLINE, TokenType.COMMENT):
                if paren_depth == 0:
                    # This is the first column
                    first_column_seen = True
                    result.append(Token('    ', TokenType.WHITESPACE))
                    result.append(token)
                    i += 1
                    continue
            
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
        return f"<ColumnsNewlineRule(order={self.order})>"
