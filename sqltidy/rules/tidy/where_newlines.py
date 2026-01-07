"""
WHERE clause formatting rule using semantic tokenizer.

This rule ensures WHERE conditions are formatted with proper newlines
for AND/OR operators, making complex WHERE clauses more readable.
"""

from typing import List
from ..base import BaseRule, ConfigField, FormatterContext
from sqltidy.tokenizer import tokenize_with_types, Token, TokenType, SemanticLevel


class WhereNewlinesRule(BaseRule):
    """
    Format WHERE clauses with newlines before AND/OR operators.
    
    This rule uses the semantic tokenizer to identify WHERE clauses
    and format them with proper line breaks for better readability.
    
    Example:
        Before:
            WHERE status = 'active' AND created_date >= '2024-01-01' OR user_id = 123
        
        After (where_newlines=True):
            WHERE status = 'active'
            AND created_date >= '2024-01-01'
            OR user_id = 123
    
    Configuration:
        where_newlines (bool): If True, add newlines before AND/OR in WHERE clauses
    """
    rule_type = "tidy"
    order = 30  # After JOIN formatting, before leading commas
    
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
    
    def apply(self, tokens: List[str], ctx: FormatterContext) -> List[str]:
        """Apply WHERE clause formatting using semantic tokenizer."""
        enabled = getattr(ctx.config, "where_newlines", False)
        
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
        in_where = False
        paren_depth = 0
        
        while i < len(flat_tokens):
            token = flat_tokens[i]
            
            # Detect WHERE keyword
            if token.type == TokenType.KEYWORD and token.value.upper() == 'WHERE':
                in_where = True
                
                # Add blank line before WHERE if not already present
                if result and result[-1].type not in (TokenType.NEWLINE,):
                    # Remove trailing whitespace
                    while result and result[-1].type == TokenType.WHITESPACE:
                        result.pop()
                    # Add blank line (two newlines)
                    result.append(Token('\n', TokenType.NEWLINE))
                    result.append(Token('\n', TokenType.NEWLINE))
                
                result.append(token)
                i += 1
                continue
            
            # Check for end of WHERE clause
            if in_where and paren_depth == 0 and token.type == TokenType.KEYWORD:
                keyword = token.value.upper()
                if keyword in self.CLAUSE_TERMINATORS:
                    in_where = False
                    # Ensure newline before clause terminator
                    if result and result[-1].type not in (TokenType.NEWLINE, TokenType.WHITESPACE):
                        result.append(Token('\n', TokenType.NEWLINE))
                    elif result and result[-1].type == TokenType.WHITESPACE:
                        result[-1] = Token('\n', TokenType.NEWLINE)
                    result.append(token)
                    i += 1
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
            
            # Format AND/OR operators in WHERE clause (but not inside parentheses)
            if in_where and paren_depth == 0 and token.type == TokenType.KEYWORD:
                keyword = token.value.upper()
                if keyword in self.LOGICAL_OPERATORS:
                    # Remove trailing whitespace before AND/OR
                    while result and result[-1].type in (TokenType.WHITESPACE, TokenType.NEWLINE):
                        result.pop()
                    
                    # Add newline before AND/OR
                    result.append(Token('\n', TokenType.NEWLINE))
                    result.append(token)
                    i += 1
                    
                    # Skip following whitespace and add single space
                    while i < len(flat_tokens) and flat_tokens[i].type in (TokenType.WHITESPACE, TokenType.NEWLINE):
                        i += 1
                    
                    if i < len(flat_tokens):
                        result.append(Token(' ', TokenType.WHITESPACE))
                    
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
