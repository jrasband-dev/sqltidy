"""
Quote Identifiers Rule - Add quotes around identifiers based on dialect conventions.

This rule demonstrates dialect-specific behavior where different databases
use different quoting characters for identifiers.
"""

from typing import List, Union
from ..base import BaseRule, ConfigField, FormatterContext
from sqltidy.tokenizer import Token, TokenGroup, TokenType, is_keyword


class QuoteIdentifiersRule(BaseRule):
    """
    Add or normalize quotes around SQL identifiers based on dialect.
    
    Quoting Styles by Dialect:
        - SQL Server: [identifier] or "identifier"
        - Oracle: "identifier"
        - PostgreSQL: "identifier"
        - MySQL: `identifier`
        - SQLite: "identifier", `identifier`, or [identifier]
    
    This rule is disabled by default. Enable via config.quote_identifiers = True.
    """
    rule_type = "tidy"
    order = 11
    supports_token_objects = True  # Use Token-based API
    
    config_fields = {
        "quote_identifiers": ConfigField(
            name="quote_identifiers",
            default=False,
            description="Add quotes around identifiers (table/column names)?",
            field_type=bool
        )
    }
    
    # Dialect-specific quote characters
    QUOTE_CHARS = {
        'sqlserver': ('[', ']'),    # SQL Server prefers brackets
        'oracle': ('"', '"'),       # Oracle uses double quotes
        'postgresql': ('"', '"'),   # PostgreSQL uses double quotes
        'mysql': ('`', '`'),        # MySQL uses backticks
        'sqlite': ('"', '"'),       # SQLite default to double quotes
    }
    
    def _get_quote_chars(self, dialect: str):
        """Get opening and closing quote characters for dialect."""
        return self.QUOTE_CHARS.get(dialect, ('"', '"'))
    
    def _is_already_quoted(self, value: str) -> bool:
        """Check if identifier is already quoted."""
        if not value or len(value) < 2:
            return False
        return (value[0] in ('"', "'", '[', '`') and 
                value[-1] in ('"', "'", ']', '`'))
    
    def _quote_identifier(self, value: str, open_quote: str, close_quote: str) -> str:
        """Quote an identifier, handling qualified names like schema.table."""
        if '.' in value:
            parts = value.split('.')
            quoted_parts = [f"{open_quote}{part}{close_quote}" for part in parts]
            return '.'.join(quoted_parts)
        else:
            return f"{open_quote}{value}{close_quote}"
    
    def apply(self, tokens: List[Union[Token, TokenGroup]], ctx: FormatterContext) -> List[Union[Token, TokenGroup]]:
        """Apply identifier quoting using Token objects."""
        # Check if quoting is enabled in config
        if not getattr(ctx.config, "quote_identifiers", False):
            return tokens
        
        dialect = ctx.config.dialect
        open_quote, close_quote = self._get_quote_chars(dialect)
        
        return self._process_tokens(tokens, dialect, open_quote, close_quote)
    
    def _process_tokens(self, tokens: List[Union[Token, TokenGroup]], dialect: str, 
                       open_quote: str, close_quote: str) -> List[Union[Token, TokenGroup]]:
        """Recursively process tokens to quote identifiers."""
        result = []
        
        for token in tokens:
            if isinstance(token, Token):
                if token.type == TokenType.IDENTIFIER and not self._is_already_quoted(token.value):
                    # Quote the identifier
                    quoted_value = self._quote_identifier(token.value, open_quote, close_quote)
                    result.append(Token(quoted_value, token.type))
                else:
                    result.append(token)
                    
            elif isinstance(token, TokenGroup):
                # Recursively process group contents
                processed_tokens = self._process_tokens(token.tokens, dialect, open_quote, close_quote)
                result.append(TokenGroup(token.group_type, processed_tokens, token.name, token.metadata))
            else:
                result.append(token)
        
        return result
