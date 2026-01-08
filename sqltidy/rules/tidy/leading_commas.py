from typing import List, Union
from ..base import BaseRule, ConfigField, FormatterContext
from sqltidy.tokenizer import tokenize_with_types, Token, TokenType, SemanticLevel, TokenGroup


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
    preserving whitespace and indentation. Now token-based to preserve
    formatting from previous rules.
    """
    rule_type = "tidy"
    order = 45
    supports_token_objects = True
    
    config_fields = {
        "leading_commas": ConfigField(
            name="leading_commas",
            default=True,
            description="Use leading commas in column lists (e.g., col1\\n  , col2\\n  , col3)?",
            field_type=bool
        )
    }

    def apply(self, tokens: Union[List[str], List[Union[Token, TokenGroup]]], ctx: FormatterContext) -> Union[List[str], List[Union[Token, TokenGroup]]]:
        leading = getattr(ctx.config, "leading_commas", False)
        
        if not leading:
            # Default behavior is trailing commas, which is what ClauseFormattingRule produces
            # Just return tokens as-is without re-tokenizing (which would destroy previous formatting)
            return tokens
        
        # If leading_commas is True, we need to move commas
        # For now, convert to string representation, apply logic, and return
        # (Token-based implementation of comma movement would be more complex)
        if not tokens or isinstance(tokens[0], str):
            # Already strings, process as before
            sql = ''.join(tokens)
            typed_tokens = tokenize_with_types(sql, ctx.config.dialect, SemanticLevel.BASIC)
            flat_tokens = self._flatten_tokens(typed_tokens)
        else:
            # Tokens/TokenGroups - flatten to get Token list
            flat_tokens = self._flatten_tokens(tokens)
        
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
                newline_count = 0
                
                # Collect any following whitespace/newline tokens
                while j < len(flat_tokens) and flat_tokens[j].type in (TokenType.WHITESPACE, TokenType.NEWLINE):
                    if flat_tokens[j].type == TokenType.NEWLINE:
                        has_newline = True
                        newline_count += 1
                        # Only keep the first newline, skip extras to avoid blank lines between columns
                        if newline_count == 1:
                            whitespace_tokens.append(flat_tokens[j])
                    else:
                        # Keep whitespace tokens (indentation)
                        whitespace_tokens.append(flat_tokens[j])
                    j += 1
                
                # If we have a newline, rearrange: whitespace first, then comma
                if has_newline and whitespace_tokens:
                    # Remove any trailing whitespace AND newlines from result before adding newline
                    # (this prevents blank lines when input has indented leading commas)
                    while result and result[-1].type in (TokenType.WHITESPACE, TokenType.NEWLINE):
                        result.pop()
                    
                    # Add the whitespace/newline tokens first (newline + indentation)
                    result.extend(whitespace_tokens)
                    # Then add the comma
                    result.append(token)
                    # Skip past the whitespace we already processed
                    i = j
                    continue
            
            result.append(token)
            i += 1
        
        # Return as Token objects
        return result
    
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
