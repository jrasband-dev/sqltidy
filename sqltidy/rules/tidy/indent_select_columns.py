from typing import List, Union
from ..base import BaseRule, ConfigField
from sqltidy.tokenizer import Token, TokenGroup, TokenType, GroupType


class IndentSelectColumnsRule(BaseRule):
    """
    Add 4 spaces of indentation to each selected column.
    This rule should run after ClauseFormattingRule and LeadingCommasRule.
    
    Works with Token objects for efficiency and robustness.
    """
    rule_type = "tidy"
    order = 50
    supports_token_objects = True
    
    config_fields = {
        "indent_select_columns": ConfigField(
            name="indent_select_columns",
            default=True,
            description="Add 4-space indentation to SELECT column lists?",
            field_type=bool
        )
    }

    def apply(self, tokens: List[Union[Token, TokenGroup]], ctx):
        if not getattr(ctx.config, "indent_select_columns", self.config_fields["indent_select_columns"].default):
            return tokens
        
        return self._process_tokens(tokens, in_select=False, indent_str=ctx.get_indent_string())
    
    def _process_tokens(self, tokens: List[Union[Token, TokenGroup]], in_select: bool = False, indent_str: str = "    ") -> List[Union[Token, TokenGroup]]:
        """
        Recursively process tokens to add indentation after newlines in SELECT clauses.
        
        Args:
            tokens: List of Token and TokenGroup objects to process
            in_select: Whether we're currently inside a SELECT column list
            indent_str: The indentation string to use (tab or spaces)
            
        Returns:
            Processed list of tokens with indentation added
        """
        result = []
        i = 0
        
        while i < len(tokens):
            token = tokens[i]
            
            if isinstance(token, TokenGroup):
                # Check if this is a SELECT clause
                if token.group_type == GroupType.SELECT_CLAUSE:
                    # Process SELECT clause contents with in_select=True
                    processed_tokens = self._process_tokens(token.tokens, in_select=True)
                    result.append(TokenGroup(
                        token.group_type,
                        processed_tokens,
                        token.name,
                        token.metadata
                    ))
                else:
                    # Recursively process other groups without changing in_select state
                    processed_tokens = self._process_tokens(token.tokens, in_select=in_select)
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
                # Detect SELECT keyword
                if token.type == TokenType.KEYWORD and token.value.upper() == "SELECT":
                    in_select = True
                    result.append(token)
                    i += 1
                    continue
                
                # Detect FROM keyword - end of column list
                if token.type == TokenType.KEYWORD and token.value.upper() == "FROM" and in_select:
                    in_select = False
                    # Remove trailing spaces before FROM
                    while result and isinstance(result[-1], Token) and result[-1].type == TokenType.WHITESPACE and result[-1].value == "    ":
                        result.pop()
                    result.append(token)
                    i += 1
                    continue
                
                # If we're in SELECT block and hit a newline, add 4 spaces after it
                # But only if the next non-whitespace token is not FROM/WHERE/etc
                if in_select and token.type == TokenType.NEWLINE:
                    result.append(token)
                    
                    # Look ahead to see if next meaningful token is a clause keyword
                    next_idx = i + 1
                    while next_idx < len(tokens) and isinstance(tokens[next_idx], Token) and tokens[next_idx].type in (TokenType.WHITESPACE, TokenType.NEWLINE):
                        next_idx += 1
                    
                    # Check if next token is a clause terminator
                    add_indent = True
                    if next_idx < len(tokens):
                        next_token = tokens[next_idx]
                        if isinstance(next_token, Token) and next_token.type == TokenType.KEYWORD:
                            if next_token.value.upper() in ('FROM', 'WHERE', 'GROUP', 'ORDER', 'HAVING', 'UNION', 'INTO'):
                                add_indent = False
                    
                    # Add indentation after the newline if appropriate
                    if add_indent:
                        result.append(Token(indent_str, TokenType.WHITESPACE))
                    i += 1
                    continue
                
                result.append(token)
                i += 1
        
        return result
