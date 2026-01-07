"""
CASE WHEN newline and indent formatting rule.

This rule formats CASE expressions with proper newlines and indentation.
"""

from typing import List
from ..base import BaseRule, ConfigField, FormatterContext


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
    
    config_fields = {
        "case_when_newline_indent": ConfigField(
            name="case_when_newline_indent",
            default=True,
            description="Format CASE expressions with newlines and indentation?",
            field_type=bool
        )
    }
    
    def apply(self, tokens: List[str], ctx: FormatterContext) -> List[str]:
        """Apply CASE WHEN formatting working directly with string tokens."""
        enabled = getattr(ctx.config, "case_when_newline_indent", False)
        
        if not enabled:
            return tokens
        
        # Work directly with string tokens to preserve formatting from earlier rules
        result = []
        i = 0
        in_case = False
        case_depth = 0
        case_position_stack = []  # Track the column position of each CASE keyword
        
        while i < len(tokens):
            token = tokens[i]
            
            # Detect CASE keyword
            if token.upper() == 'CASE':
                case_depth += 1
                in_case = True
                
                # Calculate position of CASE on current line BEFORE adding newline
                case_position = 0
                for j in range(len(result) - 1, -1, -1):
                    if result[j] == '\n':
                        # Found newline, count from there
                        for k in range(j + 1, len(result)):
                            case_position += len(result[k])
                        break
                else:
                    # No newline found, we're on the first line
                    for token_str in result:
                        case_position += len(token_str)
                
                # Add length of CASE itself
                case_position += len(token)
                case_position_stack.append(case_position)
                
                result.append(token)
                i += 1
                
                # Skip whitespace after CASE
                while i < len(tokens) and tokens[i] in (' ', '\t', '\n'):
                    i += 1
                
                # Add newline after CASE
                result.append('\n')
                continue
            
            # Detect WHEN keyword in CASE expression
            if in_case and token.upper() == 'WHEN':
                # Remove trailing spaces/tabs (but keep newlines)
                while result and result[-1] in (' ', '\t'):
                    result.pop()
                
                # Calculate indentation: CASE position + 4 for relative indent
                # Subtract 4 because indent_select_columns (order 50) will add 4 spaces after newlines
                base_indent = case_position_stack[-1] + 4 if case_position_stack else 4
                indent_for_when = max(0, base_indent - 4)
                
                # Add newline and indentation before WHEN
                result.append('\n')
                result.append(' ' * indent_for_when)
                result.append(token)
                i += 1
                continue
            
            # Detect ELSE keyword in CASE expression
            if in_case and token.upper() == 'ELSE':
                # Remove trailing spaces/tabs (but keep newlines)
                while result and result[-1] in (' ', '\t'):
                    result.pop()
                
                # Calculate indentation: same as WHEN
                # Subtract 4 because indent_select_columns (order 50) will add 4 spaces after newlines
                base_indent = case_position_stack[-1] + 4 if case_position_stack else 4
                indent_for_else = max(0, base_indent - 4)
                
                # Add newline and indentation before ELSE
                result.append('\n')
                result.append(' ' * indent_for_else)
                result.append(token)
                i += 1
                continue
            
            # Detect END keyword
            if token.upper() == 'END':
                if case_depth > 0:
                    case_depth -= 1
                    if case_position_stack:
                        case_position_stack.pop()
                    if case_depth == 0:
                        in_case = False
                    
                    # Remove trailing whitespace before END
                    while result and result[-1] in (' ', '\t', '\n'):
                        result.pop()
                    
                    # Add space before END
                    result.append(' ')
                    result.append(token)
                    i += 1
                    continue
                else:
                    result.append(token)
                    i += 1
                    continue
            
            result.append(token)
            i += 1
        
        return result
    
    def __repr__(self):
        return f"<CaseWhenNewlineIndentRule(order={self.order})>"
