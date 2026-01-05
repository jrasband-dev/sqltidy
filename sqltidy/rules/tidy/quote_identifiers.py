"""
Quote Identifiers Rule - Add quotes around identifiers based on dialect conventions.

This rule demonstrates dialect-specific behavior where different databases
use different quoting characters for identifiers.
"""

from ..base import BaseRule, ConfigField
from sqltidy.tokenizer import is_keyword


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
    
    def _is_identifier(self, token: str, dialect: str) -> bool:
        """
        Check if a token is an identifier that should be quoted.
        
        Simple heuristic:
        - Not a keyword
        - Not a number
        - Not already quoted
        - Not punctuation
        - Alphanumeric/underscore
        """
        if not token:
            return False
        
        # Already quoted?
        if token[0] in ('"', "'", '[', '`') and token[-1] in ('"', "'", ']', '`'):
            return False
        
        # Is it a keyword?
        if is_keyword(token, dialect):
            return False
        
        # Is it a number?
        try:
            float(token)
            return False
        except ValueError:
            pass
        
        # Is it punctuation?
        if token in (',', ';', '(', ')', '.', '+', '-', '*', '/', '=', '<', '>', '!'):
            return False
        
        # Is it alphanumeric with underscores?
        if token.replace('_', '').replace('.', '').isalnum():
            return True
        
        return False
    
    def apply(self, tokens, ctx):
        # Check if quoting is enabled in config
        if not getattr(ctx.config, "quote_identifiers", False):
            return tokens
        
        dialect = ctx.config.dialect
        open_quote, close_quote = self._get_quote_chars(dialect)
        
        result = []
        for token in tokens:
            if self._is_identifier(token, dialect):
                # Handle qualified identifiers like schema.table
                if '.' in token:
                    parts = token.split('.')
                    quoted_parts = [f"{open_quote}{part}{close_quote}" for part in parts]
                    result.append('.'.join(quoted_parts))
                else:
                    result.append(f"{open_quote}{token}{close_quote}")
            else:
                result.append(token)
        
        return result
