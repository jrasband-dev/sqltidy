from typing import List
from ..base import BaseRule, ConfigField, FormatterContext
from sqltidy.tokenizer import tokenize_with_types, Token, TokenType, SemanticLevel


class LeadingCommasRule(BaseRule):
    """
    If ctx.config.leading_commas is True → leading commas:
        SELECT
            a
            ,b
            ,c
    If False → trailing commas (default):
        SELECT
            a,
            b,
            c
    
    Uses the tokenizer to properly identify and move commas while
    preserving whitespace and indentation.
    """
    rule_type = "tidy"
    order = 45
    
    config_fields = {
        "leading_commas": ConfigField(
            name="leading_commas",
            default=True,
            description="Use leading commas in column lists (e.g., col1\\n  , col2\\n  , col3)?",
            field_type=bool
        )
    }

    def apply(self, tokens: List[str], ctx: FormatterContext) -> List[str]:
        leading = getattr(ctx.config, "leading_commas", False)
        
        if not leading:
            # Default behavior is trailing commas, which is what ClauseFormattingRule produces
            return tokens
        
        # Convert string tokens to typed Token objects
        sql = ''.join(tokens)
        typed_tokens = tokenize_with_types(sql, ctx.config.dialect, SemanticLevel.BASIC)
        
        # Flatten to simple token list
        flat_tokens = self._flatten_tokens(typed_tokens)
        
        # For leading commas, we need to move commas that are followed by newline+whitespace
        # to after the newline+whitespace (making them leading on the next line)
        result = []
        i = 0
        
        while i < len(flat_tokens):
            token = flat_tokens[i]
            
            # When we hit a comma followed by newline/whitespace
            if token.type == TokenType.PUNCTUATION and token.value == ",":
                # Look ahead to see if we have newline + whitespace pattern
                j = i + 1
                has_newline = False
                whitespace_tokens = []
                
                # Collect any following whitespace/newline tokens
                while j < len(flat_tokens) and flat_tokens[j].type in (TokenType.WHITESPACE, TokenType.NEWLINE):
                    if flat_tokens[j].type == TokenType.NEWLINE:
                        has_newline = True
                    whitespace_tokens.append(flat_tokens[j])
                    j += 1
                
                # If we have a newline, rearrange: whitespace first, then comma
                if has_newline and whitespace_tokens:
                    # Add the whitespace/newline tokens first
                    result.extend(whitespace_tokens)
                    # Then add the comma
                    result.append(token)
                    # Skip past the whitespace we already processed
                    i = j
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
