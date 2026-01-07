"""
SELECT newline formatting rule using semantic tokenizer.

This rule ensures SELECT keywords appear on their own line with proper spacing.
"""

from typing import List
from ..base import BaseRule, ConfigField, FormatterContext
from sqltidy.tokenizer import tokenize_with_types, Token, TokenType, SemanticLevel


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
    """
    rule_type = "tidy"
    order = 35  # After all other formatting rules to fix spacing around SELECT
    
    config_fields = {
        "select_newline": ConfigField(
            name="select_newline",
            default=True,
            description="Add blank line before SELECT keywords?",
            field_type=bool
        )
    }
    
    def apply(self, tokens: List[str], ctx: FormatterContext) -> List[str]:
        """Apply SELECT newline formatting using semantic tokenizer."""
        enabled = getattr(ctx.config, "select_newline", False)
        
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
        seen_meaningful_token = False  # Track if we've seen any meaningful token before SELECT
        
        while i < len(flat_tokens):
            token = flat_tokens[i]
            
            # Track if we've seen meaningful tokens (not just whitespace/newlines at start)
            if not seen_meaningful_token and token.type not in (TokenType.WHITESPACE, TokenType.NEWLINE):
                seen_meaningful_token = True
            
            # Detect SELECT keyword
            if token.type == TokenType.KEYWORD and token.value.upper() == 'SELECT':
                # Add blank line before SELECT if there's content before it
                if seen_meaningful_token and result:
                    # Check if previous token is not already a newline
                    has_content_before = False
                    for prev_token in reversed(result):
                        if prev_token.type not in (TokenType.WHITESPACE, TokenType.NEWLINE):
                            has_content_before = True
                            break
                    
                    if has_content_before:
                        # Remove trailing whitespace
                        while result and result[-1].type in (TokenType.WHITESPACE, TokenType.NEWLINE):
                            result.pop()
                        
                        # Add blank line (two newlines)
                        result.append(Token('\n', TokenType.NEWLINE))
                        result.append(Token('\n', TokenType.NEWLINE))
                
                # Reset for next SELECT
                seen_meaningful_token = False
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
        for i, item in enumerate(tokens):
            if isinstance(item, Token):
                result.append(item)
            elif isinstance(item, TokenGroup):
                # For PARENTHESIS and SUBQUERY groups, add the parentheses that the tokenizer excluded
                if item.group_type in (GroupType.PARENTHESIS, GroupType.SUBQUERY):
                    result.append(Token('(', TokenType.PUNCTUATION))
                    result.extend(self._flatten_tokens(item.tokens))
                    result.append(Token(')', TokenType.PUNCTUATION))
                    
                    # Add spacing after closing paren if next token is SELECT
                    if i + 1 < len(tokens):
                        next_item = tokens[i + 1]
                        if isinstance(next_item, Token) and next_item.type == TokenType.KEYWORD:
                            if next_item.value.upper() == 'SELECT':
                                # Add blank line after closing paren before SELECT
                                result.append(Token('\n', TokenType.NEWLINE))
                                result.append(Token('\n', TokenType.NEWLINE))
                        elif isinstance(next_item, TokenGroup):
                            # Check first token in the group
                            first_token = self._get_first_token(next_item)
                            if first_token and first_token.type == TokenType.KEYWORD and first_token.value.upper() == 'SELECT':
                                result.append(Token('\n', TokenType.NEWLINE))
                                result.append(Token('\n', TokenType.NEWLINE))
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
    
    def _get_first_token(self, group) -> Token:
        """Get the first Token from a TokenGroup recursively."""
        from sqltidy.tokenizer import TokenGroup
        
        for item in group.tokens:
            if isinstance(item, Token):
                return item
            elif isinstance(item, TokenGroup):
                first = self._get_first_token(item)
                if first:
                    return first
        return None
    
    def __repr__(self):
        return f"<SelectNewlineRule(order={self.order})>"
