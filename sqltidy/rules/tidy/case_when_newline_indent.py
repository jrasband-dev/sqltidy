"""
CASE WHEN newline and indent formatting rule.

This rule formats CASE expressions with proper newlines and indentation.
Now uses Token-based API for better composability.
"""

from typing import List, Union
from ..base import BaseRule, ConfigField, FormatterContext
from sqltidy.tokenizer import Token, TokenGroup, TokenType, GroupType


class CaseWhenNewlineIndentRule(BaseRule):
    """
    Format CASE expressions with newlines and indentation.
    
    Example:
        Before:
            CASE WHEN x = 1 THEN 'a' WHEN x = 2 THEN 'b' ELSE 'c' END
        
        After (case_when_newline_indent=True):
            CASE
                WHEN x = 1 THEN 'a'
                WHEN x = 2 THEN 'b'
                ELSE 'c'
            END
    
    Configuration:
        case_when_newline_indent (bool): If True, format CASE expressions with newlines and indentation
    """
    rule_type = "tidy"
    order = 46  # After leading_commas (45) which re-tokenizes
    supports_token_objects = True  # Use new Token-based API
    
    config_fields = {
        "case_when_newline_indent": ConfigField(
            name="case_when_newline_indent",
            default=True,
            description="Format CASE expressions with newlines and indentation?",
            field_type=bool
        )
    }
    
    def apply(self, tokens: List[Union[Token, TokenGroup]], ctx: FormatterContext) -> List[Union[Token, TokenGroup]]:
        """Apply CASE WHEN formatting using Token objects."""
        enabled = getattr(ctx.config, "case_when_newline_indent", False)
        
        if not enabled:
            return tokens
        
        # Process tokens recursively to find and format CASE expressions
        return self._process_tokens(tokens)
    
    def _process_tokens(self, tokens: List[Union[Token, TokenGroup]], indent_str: str = "    ") -> List[Union[Token, TokenGroup]]:
        """Recursively process tokens to format CASE expressions."""
        result = []
        i = 0
        in_case = False
        case_depth = 0
        
        while i < len(tokens):
            token = tokens[i]
            
            # Handle TokenGroup - process recursively
            if isinstance(token, TokenGroup):
                # Process tokens within the group
                processed_group = TokenGroup(
                    token.group_type,
                    self._process_tokens(token.tokens),
                    token.name,
                    token.metadata
                )
                result.append(processed_group)
                i += 1
                continue
            
            # Detect CASE keyword
            if isinstance(token, Token) and token.type == TokenType.KEYWORD and token.value.upper() == 'CASE':
                case_depth += 1
                in_case = True
                
                result.append(token)
                i += 1
                
                # Add newline after CASE
                result.append(Token('\n', TokenType.NEWLINE))
                
                # Skip any existing whitespace/newlines after CASE
                while i < len(tokens) and isinstance(tokens[i], Token) and tokens[i].type in (TokenType.WHITESPACE, TokenType.NEWLINE):
                    i += 1
                continue
            
            # Detect WHEN keyword in CASE expression
            if in_case and isinstance(token, Token) and token.type == TokenType.KEYWORD and token.value.upper() == 'WHEN':
                # Remove trailing whitespace/newlines before WHEN
                while result and isinstance(result[-1], Token) and result[-1].type in (TokenType.WHITESPACE, TokenType.NEWLINE):
                    result.pop()
                
                # Add newline and indentation before WHEN
                result.append(Token('\n', TokenType.NEWLINE))
                result.append(Token(indent_str, TokenType.WHITESPACE))  # Base indent - indent_select_columns will add more
                result.append(token)
                i += 1
                continue
            
            # Detect ELSE keyword in CASE expression
            if in_case and isinstance(token, Token) and token.type == TokenType.KEYWORD and token.value.upper() == 'ELSE':
                # Remove trailing whitespace/newlines before ELSE
                while result and isinstance(result[-1], Token) and result[-1].type in (TokenType.WHITESPACE, TokenType.NEWLINE):
                    result.pop()
                
                # Add newline and indentation before ELSE
                result.append(Token('\n', TokenType.NEWLINE))
                result.append(Token(indent_str, TokenType.WHITESPACE))  # Same indentation as WHEN
                result.append(token)
                i += 1
                continue
            
            # Detect END keyword - could end CASE expression
            if isinstance(token, Token) and token.type == TokenType.KEYWORD and token.value.upper() == 'END':
                if case_depth > 0:
                    case_depth -= 1
                    if case_depth == 0:
                        in_case = False
                    
                    # Remove trailing whitespace/newlines before END
                    while result and isinstance(result[-1], Token) and result[-1].type in (TokenType.WHITESPACE, TokenType.NEWLINE):
                        result.pop()
                    
                    # Add space before END
                    result.append(Token(' ', TokenType.WHITESPACE))
                    result.append(token)
                    i += 1
                    continue
            
            result.append(token)
            i += 1
        
        return result
    
    def __repr__(self):
        return f"<CaseWhenNewlineIndentRule(order={self.order})>"
