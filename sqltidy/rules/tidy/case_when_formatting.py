"""
CASE WHEN formatting rule using semantic tokenizer.

This rule provides comprehensive formatting for CASE expressions,
ensuring consistent indentation and newline placement for WHEN, THEN, 
ELSE, and END keywords.
"""

from typing import List
from ..base import BaseRule, ConfigField, FormatterContext
from sqltidy.tokenizer import tokenize_with_types, Token, TokenType, TokenGroup, SemanticLevel, GroupType


class CaseWhenFormattingRule(BaseRule):
    """
    Format CASE expressions with proper indentation and newlines.
    
    This rule uses the semantic tokenizer to identify CASE expressions
    and format them according to configuration.
    
    Example:
        Before:
            SELECT CASE WHEN status='active' THEN 'A' WHEN status='pending' THEN 'P' ELSE 'X' END
        
        After (indent_case_when=True):
            SELECT CASE
                WHEN status='active' THEN 'A'
                WHEN status='pending' THEN 'P'
                ELSE 'X'
            END
    
    Configuration:
        indent_case_when (bool): If True, format CASE expressions with proper indentation
        case_indent_spaces (int): Number of spaces to indent WHEN/ELSE clauses (default: 4)
        newline_after_case (bool): Put CASE keyword on its own line (default: False)
        newline_before_end (bool): Put END keyword on its own line (default: True)
    """
    rule_type = "tidy"
    order = 50
    
    config_fields = {
        "indent_case_when": ConfigField(
            name="indent_case_when",
            default=False,
            description="Format CASE expressions with proper indentation?",
            field_type=bool
        ),
        "case_indent_spaces": ConfigField(
            name="case_indent_spaces",
            default=4,
            description="Number of spaces to indent WHEN/ELSE clauses",
            field_type=int
        ),
        "newline_after_case": ConfigField(
            name="newline_after_case",
            default=False,
            description="Put CASE keyword on its own line?",
            field_type=bool
        ),
        "newline_before_end": ConfigField(
            name="newline_before_end",
            default=True,
            description="Put END keyword on its own line?",
            field_type=bool
        ),
    }
    
    def apply(self, tokens: List[str], ctx: FormatterContext) -> List[str]:
        """Apply CASE WHEN formatting using semantic tokenizer."""
        enabled = getattr(ctx.config, "indent_case_when", False)
        
        if not enabled:
            return tokens
        
        # Get configuration
        indent_spaces = getattr(ctx.config, "case_indent_spaces", 4)
        newline_after_case = getattr(ctx.config, "newline_after_case", False)
        newline_before_end = getattr(ctx.config, "newline_before_end", True)
        
        # Convert string tokens to typed Token objects with semantic analysis
        sql = ''.join(tokens)
        typed_tokens = tokenize_with_types(sql, ctx.config.dialect, SemanticLevel.SEMANTIC)
        
        # Find all CASE expressions using semantic groups
        case_groups = self._find_case_expressions(typed_tokens)
        
        if not case_groups:
            return tokens
        
        # Flatten to simple token list for processing
        flat_tokens = self._flatten_tokens(typed_tokens)
        
        # Track positions of CASE expressions in flat list and format them
        result_tokens = []
        i = 0
        
        while i < len(flat_tokens):
            # Check if this token starts a CASE expression
            if isinstance(flat_tokens[i], Token) and \
               flat_tokens[i].type == TokenType.KEYWORD and \
               flat_tokens[i].value.upper() == 'CASE':
                # Find the matching END
                case_end_idx = self._find_case_end(flat_tokens, i)
                if case_end_idx > i:
                    # Format this CASE expression
                    case_tokens = flat_tokens[i:case_end_idx + 1]
                    formatted = self._format_case_expression(
                        case_tokens,
                        indent_spaces,
                        newline_after_case,
                        newline_before_end
                    )
                    result_tokens.extend(formatted)
                    i = case_end_idx + 1
                    continue
            
            result_tokens.append(flat_tokens[i])
            i += 1
        
        # Convert back to string tokens
        return [t.value for t in result_tokens]
    
    def _find_case_expressions(self, tokens: List) -> List[TokenGroup]:
        """Recursively find all CASE_EXPRESSION groups."""
        case_groups = []
        for item in tokens:
            if isinstance(item, TokenGroup):
                if item.group_type == GroupType.CASE_EXPRESSION:
                    case_groups.append(item)
                # Recursively search nested groups
                case_groups.extend(self._find_case_expressions(item.tokens))
        return case_groups
    
    def _flatten_tokens(self, tokens: List) -> List[Token]:
        """Flatten token groups to simple token list."""
        result = []
        for item in tokens:
            if isinstance(item, Token):
                result.append(item)
            elif isinstance(item, TokenGroup):
                result.extend(self._flatten_tokens(item.tokens))
        return result
    
    def _find_case_end(self, tokens: List[Token], start: int) -> int:
        """Find the matching END keyword for a CASE starting at index."""
        depth = 1
        i = start + 1
        while i < len(tokens) and depth > 0:
            if isinstance(tokens[i], Token) and tokens[i].type == TokenType.KEYWORD:
                keyword = tokens[i].value.upper()
                if keyword == 'CASE':
                    depth += 1
                elif keyword == 'END':
                    depth -= 1
                    if depth == 0:
                        return i
            i += 1
        return -1
    
    def _format_case_expression(
        self,
        tokens: List[Token],
        indent_spaces: int,
        newline_after_case: bool,
        newline_before_end: bool
    ) -> List[Token]:
        """
        Format a CASE expression with proper indentation.
        
        Args:
            tokens: Tokens comprising the CASE expression
            indent_spaces: Number of spaces for indentation
            newline_after_case: Whether to add newline after CASE
            newline_before_end: Whether to add newline before END
            
        Returns:
            Formatted list of tokens
        """
        result = []
        indent = ' ' * indent_spaces
        i = 0
        in_when_clause = False
        in_then_clause = False
        in_else_clause = False
        
        while i < len(tokens):
            token = tokens[i]
            
            # Handle CASE keyword
            if token.type == TokenType.KEYWORD and token.value.upper() == 'CASE':
                result.append(token)
                
                # Check if next non-whitespace is WHEN (simple case) or an expression (searched case)
                next_idx = i + 1
                while next_idx < len(tokens) and tokens[next_idx].type in (TokenType.WHITESPACE, TokenType.NEWLINE):
                    next_idx += 1
                
                if newline_after_case:
                    # Remove any following whitespace and add our own newline
                    while i + 1 < len(tokens) and tokens[i + 1].type in (TokenType.WHITESPACE, TokenType.NEWLINE):
                        i += 1
                    result.append(Token('\n', TokenType.NEWLINE))
                else:
                    # Keep single space
                    while i + 1 < len(tokens) and tokens[i + 1].type in (TokenType.WHITESPACE, TokenType.NEWLINE):
                        i += 1
                    result.append(Token(' ', TokenType.WHITESPACE))
                
                i += 1
                continue
            
            # Handle WHEN keyword
            elif token.type == TokenType.KEYWORD and token.value.upper() == 'WHEN':
                # Remove preceding whitespace
                while result and result[-1].type in (TokenType.WHITESPACE, TokenType.NEWLINE):
                    result.pop()
                
                # Add newline and indentation
                result.append(Token('\n', TokenType.NEWLINE))
                result.append(Token(indent, TokenType.WHITESPACE))
                result.append(token)
                result.append(Token(' ', TokenType.WHITESPACE))
                
                in_when_clause = True
                in_then_clause = False
                in_else_clause = False
                
                # Skip following whitespace
                while i + 1 < len(tokens) and tokens[i + 1].type in (TokenType.WHITESPACE, TokenType.NEWLINE):
                    i += 1
                
                i += 1
                continue
            
            # Handle THEN keyword
            elif token.type == TokenType.KEYWORD and token.value.upper() == 'THEN':
                # Clean up whitespace before THEN
                while result and result[-1].type in (TokenType.WHITESPACE, TokenType.NEWLINE):
                    result.pop()
                
                result.append(Token(' ', TokenType.WHITESPACE))
                result.append(token)
                result.append(Token(' ', TokenType.WHITESPACE))
                
                in_when_clause = False
                in_then_clause = True
                
                # Skip following whitespace
                while i + 1 < len(tokens) and tokens[i + 1].type in (TokenType.WHITESPACE, TokenType.NEWLINE):
                    i += 1
                
                i += 1
                continue
            
            # Handle ELSE keyword
            elif token.type == TokenType.KEYWORD and token.value.upper() == 'ELSE':
                # Remove preceding whitespace
                while result and result[-1].type in (TokenType.WHITESPACE, TokenType.NEWLINE):
                    result.pop()
                
                # Add newline and indentation
                result.append(Token('\n', TokenType.NEWLINE))
                result.append(Token(indent, TokenType.WHITESPACE))
                result.append(token)
                result.append(Token(' ', TokenType.WHITESPACE))
                
                in_when_clause = False
                in_then_clause = False
                in_else_clause = True
                
                # Skip following whitespace
                while i + 1 < len(tokens) and tokens[i + 1].type in (TokenType.WHITESPACE, TokenType.NEWLINE):
                    i += 1
                
                i += 1
                continue
            
            # Handle END keyword
            elif token.type == TokenType.KEYWORD and token.value.upper() == 'END':
                # Remove preceding whitespace
                while result and result[-1].type in (TokenType.WHITESPACE, TokenType.NEWLINE):
                    result.pop()
                
                if newline_before_end:
                    result.append(Token('\n', TokenType.NEWLINE))
                else:
                    result.append(Token(' ', TokenType.WHITESPACE))
                
                result.append(token)
                
                in_when_clause = False
                in_then_clause = False
                in_else_clause = False
                
                i += 1
                continue
            
            # Handle whitespace - normalize multiple whitespace/newlines
            elif token.type in (TokenType.WHITESPACE, TokenType.NEWLINE):
                # Skip consecutive whitespace tokens, keep only one space
                if result and result[-1].type not in (TokenType.WHITESPACE, TokenType.NEWLINE):
                    # Check if next non-whitespace is a keyword we'll handle specially
                    next_idx = i
                    while next_idx < len(tokens) and tokens[next_idx].type in (TokenType.WHITESPACE, TokenType.NEWLINE):
                        next_idx += 1
                    
                    if next_idx < len(tokens):
                        next_token = tokens[next_idx]
                        if next_token.type == TokenType.KEYWORD and next_token.value.upper() in ('WHEN', 'THEN', 'ELSE', 'END'):
                            # Skip this whitespace, we'll handle it when we hit the keyword
                            i += 1
                            continue
                    
                    # Otherwise keep a single space
                    result.append(Token(' ', TokenType.WHITESPACE))
                i += 1
                continue
            
            # All other tokens
            else:
                result.append(token)
                i += 1
        
        return result
    
    def __repr__(self):
        return f"<CaseWhenFormattingRule(order={self.order})>"
